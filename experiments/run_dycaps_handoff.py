#!/usr/bin/env python3
"""Run upstream DyCAPS across two processes using a Go test overlay."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("experiments/results/dycaps-handoff"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    upstream = root / "upstream/dycaps"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stages = ("sender", "persist", "replicate", "retire", "successor", "quorum", "recover")
    for stage in stages:
        (output / f"{stage}.json").unlink(missing_ok=True)
        (output / f"{stage}.log").unlink(missing_ok=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    version = subprocess.check_output(["go", "version"], text=True).strip()
    (output / "environment.json").write_text(json.dumps({
        "upstream": "https://github.com/DyCAPSTeam/DyCAPS", "revision": revision,
        "go": version, "transport": "two independent saver stores; recipient-scoped encrypted serialized packets with signatures",
        "setup": "upstream trusted dealer and public testing KZG setup",
    }, indent=2) + "\n")
    with tempfile.TemporaryDirectory(prefix="fl-dycaps-") as temporary:
        temporary = Path(temporary)
        overlay = temporary / "overlay.json"
        overlay.write_text(json.dumps({"Replace": {
            str(upstream / "internal/party/fl_handoff_test.go"): str(root / "dycaps_handoff_test.go"),
        }}))
        binary = temporary / "handoff.test"
        subprocess.run([
            "go", "test", "-overlay", str(overlay), "-c", "-o", str(binary), "./internal/party",
        ], cwd=upstream, check=True, timeout=120)
        fixture = temporary / "handoff.json"
        store_a = temporary / "handoff-store-a.json"
        store_b = temporary / "handoff-store-b.json"
        keys = temporary / "recipient-keys.json"
        for stage in stages:
            environment = dict(os.environ, FL_HANDOFF_STAGE=stage,
                               FL_HANDOFF_FIXTURE=str(fixture), FL_HANDOFF_STORE_A=str(store_a),
                               FL_HANDOFF_STORE_B=str(store_b), FL_HANDOFF_STORE=str(store_b),
                               FL_HANDOFF_KEYS=str(keys), FL_HANDOFF_OUTPUT=str(output))
            result = subprocess.run([
                str(binary), "-test.run=^TestFLHandoff$", "-test.v", "-test.timeout=30s",
            ], cwd=upstream, env=environment, capture_output=True, text=True, timeout=35)
            (output / f"{stage}.log").write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f"{stage} failed; see {output / (stage + '.log')}")
            print(f"PASS: {stage}", flush=True)
        print(f"Results: {output}")


if __name__ == "__main__":
    run()
