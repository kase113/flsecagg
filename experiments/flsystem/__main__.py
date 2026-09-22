"""Run local SGD, protected aggregation and service replacement in one project."""

import argparse
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from contextlib import ExitStack
from fractions import Fraction
import json
import multiprocessing
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))
from reconfigurable_async_fl import AggregationProtocol, Service
from .training import dataset, train_client


class Worker:
    def __init__(self, binary, log):
        self.log = log.open("w")
        self.process = subprocess.Popen([str(binary)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.log, text=True)

    def call(self, operation, **arguments):
        self.process.stdin.write(json.dumps({"Operation": operation, **arguments}) + "\n")
        self.process.stdin.flush()
        if not select.select([self.process.stdout], [], [], 120)[0]:
            raise TimeoutError(f"crypto worker timed out: {operation}")
        response = self.process.stdout.readline()
        if not response:
            raise RuntimeError(f"crypto worker exited during {operation}; see {self.log.name}")
        return json.loads(response)

    def close(self):
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()
        self.log.close()


def build_worker(directory):
    upstream = ROOT / "experiments/upstream/dycaps"
    source = Path(__file__).resolve().parent
    checkout = directory / "dycaps"
    shutil.copytree(upstream, checkout, ignore=shutil.ignore_patterns(".git", ".idea"))
    shutil.copy(source / "crypto_worker.go", checkout / "internal/party/fl_runtime.go")
    shutil.copy(source / "worker_main.go", checkout / "cmd/DyCAPs/main.go")
    binary = directory / "fl-crypto"
    subprocess.run(["go", "build", "-o", str(binary), "./cmd/DyCAPs"],
                   cwd=checkout, check=True, timeout=120)
    return binary


def persist_json(path, value):
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def load_handoff(path):
    return json.loads(path.read_text())["transfer"]


def evaluate(model):
    import torch
    features, labels = dataset(90001, 512)
    weights = torch.tensor([float(value) for value in model])
    logits = features @ weights[:5] + weights[5]
    return {"loss": float(torch.nn.functional.binary_cross_entropy_with_logits(logits, labels)),
            "accuracy": float(((logits >= 0) == labels.bool()).float().mean())}


def run(args):
    import torch
    torch.set_num_threads(1)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    protocol = AggregationProtocol(
        (Service("A", ("p0", "p1", "p2", "p3"), 1, 2),
         Service("B", ("q0", "q1", "q2", "q3"), 1, 2)),
        "A", (0,) * 6, args.clients, Fraction(1, args.scale))

    def act(operation, **arguments):
        outcome = protocol.dispatch({"operation": operation, **arguments})
        if outcome["status"] != "accepted":
            raise RuntimeError(outcome)

    initial = evaluate(protocol.model)
    rounds, transfers = [], []
    accepted = 0
    changed = False
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="fl-system-") as temporary, ExitStack() as resources:
        directory = Path(temporary)
        binary = build_worker(directory)
        workers = {"A": Worker(binary, output / "service-A.log")}
        resources.callback(workers["A"].close)
        executor = resources.enter_context(ProcessPoolExecutor(
            max_workers=args.clients, mp_context=multiprocessing.get_context("spawn")))
        pending = {}
        references = {}
        next_instance = 0

        def launch():
            nonlocal next_instance
            sid = f"aggregation-{next_instance}"
            next_instance += 1
            service = protocol.current_service
            version = len(protocol.applied)
            act("start", sid=sid, service=service, base_version=version)
            response = workers[service].call("init", SID=sid, Dimension=6, Limit=args.clients,
                                             Bound=args.clients * args.scale // 4)
            references[sid] = []
            for client_index in range(args.clients):
                update_id = f"{sid}:{client_index}"
                reference = directory / f"{sid}-{client_index}.json"
                references[sid].append(reference)
                task = {"sid": sid, "base_version": version, "update_id": update_id,
                        "client_index": client_index, "model": [float(value) for value in protocol.model],
                        "public": response["public"], "seed": args.seed, "steps": args.local_steps,
                        "scale": args.scale, "binary": str(binary), "reference": str(reference)}
                pending[executor.submit(train_client, task)] = update_id

        for _ in range(min(2, args.rounds)):
            launch()
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in sorted(completed, key=lambda item: pending[item]):
                pending.pop(future)
                submission = future.result()
                sid = submission["sid"]
                service = protocol.current_service
                workers[service].call("add", SID=sid, Update=submission["update_id"],
                                      Ciphertext=submission["ciphertext"])
                act("admit", sid=sid, client=submission["client"], update_id=submission["update_id"],
                    base_version=submission["base_version"], service=service, weight=1,
                    values=[], ciphertext=submission["ciphertext"])
                accepted += 1
                instance = protocol.instances[sid]
                if instance.phase == "opening":
                    summed = workers[service].call("open", SID=sid)
                    for member in instance.certificate.committee_members[:2]:
                        act("contribute", sid=sid, member=member)
                    act("decode", sid=sid, decoded_sum=summed)
                    act("commit", sid=sid, service=service)
                    act("apply_result", sid=sid)
                    workers[service].call("retire", SID=sid)
                    act("retire", sid=sid, generation=instance.state.context.generation)
                    act("seal", sid=sid)
                    expected = [sum(column) for column in zip(*(json.loads(path.read_text()) for path in references[sid]))]
                    if summed != expected:
                        raise RuntimeError("cryptographic aggregate differs from independent client reference")
                    metrics = {"sid": sid, "service": service, "base_version": instance.base_version,
                               "application_position": protocol.commits[sid].position, "aggregate": summed,
                               "model": [float(value) for value in protocol.model], **evaluate(protocol.model)}
                    rounds.append(metrics)
                    checkpoint = output / "checkpoint.tmp"
                    checkpoint.write_text(json.dumps({"rounds": rounds, "applied": protocol.applied,
                                                       "model": metrics["model"]}, indent=2) + "\n")
                    checkpoint.replace(output / "checkpoint.json")
                    print(f"{sid}: {service}, loss={metrics['loss']:.4f}, accuracy={metrics['accuracy']:.3f}", flush=True)
                    if next_instance < args.rounds:
                        launch()
                active = [sid for sid, instance in protocol.instances.items() if instance.phase == "gathering"]
                partial = [sid for sid in active if protocol.instances[sid].updates]
                if args.handoff_after and accepted >= args.handoff_after and not changed and partial:
                    transition_started = time.perf_counter()
                    workers["B"] = Worker(binary, output / "service-B.log")
                    resources.callback(workers["B"].close)
                    recipients = workers["B"].call("receivers")
                    act("change_service", service="B")
                    for active_sid in active:
                        bundle = workers["A"].call("export", SID=active_sid, Recipients=recipients)
                        handoff_path = output / f"handoff-{active_sid}.json"
                        persist_json(handoff_path, {"sid": active_sid, "source": "A",
                                                    "target": "B", "transfer": bundle})
                        installed = workers["B"].call("receive", SID=active_sid,
                                                        Transfer=load_handoff(handoff_path))
                        ack_path = output / f"handoff-{active_sid}.ack.json"
                        persist_json(ack_path, {"sid": active_sid, "status": "installed",
                                               **installed})
                        act("install", sid=active_sid, generation=1)
                        workers["A"].call("retire", SID=active_sid)
                        act("retire", sid=active_sid, generation=0)
                        act("activate", sid=active_sid, generation=1)
                        transfers.append({"sid": active_sid, **installed,
                                          "serialized_transfer_bytes": len(handoff_path.read_bytes()),
                                          "handoff_file": handoff_path.name,
                                          "ack_file": ack_path.name})
                    workers["A"].close()
                    changed = True
                    print(f"A -> B: {len(active)} instances, {time.perf_counter() - transition_started:.3f}s; A exited", flush=True)

    if args.handoff_after and not changed:
        raise RuntimeError("requested handoff did not occur while an instance was in flight")
    replayed = AggregationProtocol(tuple(protocol.services.values()), "A", (0,) * 6,
                                   args.clients, Fraction(1, args.scale))
    for record in protocol.events:
        if replayed.dispatch(record["event"]) != record:
            raise RuntimeError("protocol replay mismatch")
    if replayed.model != protocol.model:
        raise RuntimeError("model replay mismatch")
    summary = {"mode": "local multiprocess training with real BLS encryption and DyCAPS handoff",
               "seed": args.seed, "clients_per_instance": args.clients, "local_steps": args.local_steps,
               "scale": args.scale, "initial": initial, "final": evaluate(protocol.model),
               "completed_instances": len(rounds), "accepted_updates": accepted,
               "handoff": changed, "transfers": transfers, "application_order": protocol.applied,
               "aggregate_reference_match": True, "model_replay_match": True,
               "durable_handoff_match": all(
                   (output / transfer["handoff_file"]).exists()
                   and (output / transfer["ack_file"]).exists() for transfer in transfers),
               "elapsed_seconds_including_build": time.perf_counter() - started,
               "limits": ["synthetic logistic regression data", "one process per committee, in-process member channels",
                          "trusted initialization and upstream testing KZG parameters",
                          "ideal agreement and trusted coordinator", "honest partial opening without proof",
                          "checkpoint stores completed models; live-state crash resume pending",
                          "no claim of mobile-adversary privacy or production isolation"]}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "events.json").write_text(json.dumps(protocol.events, indent=2) + "\n")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=ROOT / "experiments/upstream/dycaps", text=True).strip()
    (output / "environment.json").write_text(json.dumps({"python": sys.version, "torch": torch.__version__,
        "go": subprocess.check_output(["go", "version"], text=True).strip(), "dycaps_revision": revision,
        "arguments": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}}, indent=2) + "\n")
    print(f"Completed: {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("experiments/results/fl-system"))
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument("--local-steps", type=int, default=8)
    parser.add_argument("--scale", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--handoff-after", type=int, default=5, help="accepted updates before handoff; 0 keeps membership fixed")
    args = parser.parse_args()
    if (args.rounds < 1 or args.clients < 2 or args.local_steps < 1 or args.scale < 4
            or args.scale % 4 or args.handoff_after < 0
            or args.handoff_after >= args.rounds * args.clients):
        parser.error("invalid training count, quantization scale or handoff position")
    run(args)


if __name__ == "__main__":
    main()
