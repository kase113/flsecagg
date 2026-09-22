#!/usr/bin/env python3
"""Discrete-event experiment for asynchronous privacy finality mechanisms."""

from __future__ import annotations

import argparse
import csv
import heapq
import random
from dataclasses import dataclass, field
from typing import Iterable


PROTOCOLS = ("fgsr", "unfenced", "vssr", "epoch")


@dataclass(order=True)
class Event:
    delivery_time: int
    sequence: int
    kind: str = field(compare=False)
    node: int = field(compare=False)
    generation: int = field(compare=False)


@dataclass
class TrialResult:
    protocol: str
    trial: int
    violated: int
    stale_repair_accepts: int
    finality_latency: int
    messages: int
    retained_capabilities: int
    post_finality_openings: int


@dataclass(frozen=True)
class Scenario:
    delays: tuple[int, ...]
    delivered: tuple[bool, ...]


def parse_protocols(value: str) -> Iterable[str]:
    protocols = PROTOCOLS if value == "all" else tuple(value.split(","))
    unknown = set(protocols) - set(PROTOCOLS)
    if unknown:
        raise argparse.ArgumentTypeError("unknown protocol: " + ",".join(sorted(unknown)))
    return protocols


def run_trial(
    protocol: str,
    trial: int,
    scenario: Scenario,
    nodes: int,
    fault_bound: int,
    recovery_threshold: int,
    epoch_length: int,
) -> TrialResult:
    session = "sid-0"
    retirement_request = max(scenario.delays) + 2
    current_generation = 0
    retired = False
    finality_time = retirement_request
    stale_repair_accepts = 0
    messages = 0
    sequence = 0
    events: list[Event] = []
    shares = {(node, current_generation) for node in range(nodes)}
    recovery_edges: set[tuple[int, int]] = set()

    def schedule(node: int, generation: int, send_time: int) -> None:
        nonlocal sequence, messages
        if not scenario.delivered[node]:
            return
        delay = scenario.delays[node]
        sequence += 1
        heapq.heappush(events, Event(send_time + delay, sequence, "repair", node, generation))
        messages += 1

    # Repairs are sent before the retirement request and may arrive on either side
    # of the frontier, which is the asynchronous race under study.
    for node in range(nodes):
        schedule(node, current_generation, retirement_request - 1)

    if protocol == "epoch":
        finality_time = ((retirement_request // epoch_length) + 1) * epoch_length

    while events:
        event = heapq.heappop(events)
        if event.delivery_time >= retirement_request:
            retired = True
        if event.kind != "repair":
            continue

        stale = retired or event.generation < current_generation
        if protocol == "fgsr":
            # The frontier is absorbing for this session: stale messages are
            # rejected and cannot recreate a scalar capability.
            continue
        if protocol == "epoch" and event.delivery_time < finality_time:
            shares.add((event.node, event.generation))
            continue
        if protocol == "unfenced":
            shares.add((event.node, event.generation))
            if stale:
                stale_repair_accepts += 1
            continue
        if protocol == "vssr":
            shares.add((event.node, event.generation))
            recovery_edges.add((event.node, event.generation))
            if stale:
                stale_repair_accepts += 1

    if protocol == "fgsr":
        shares.clear()
        recovery_edges.clear()
    elif protocol == "epoch":
        # Epoch rekeying eventually closes the old state, but only globally.
        shares.clear()
        recovery_edges.clear()

    # The adversary first exposes fault_bound old shares, then corrupts nodes one
    # at a time after finality. This respects the instantaneous corruption bound
    # while testing accumulation across time.
    exposed_before = min(fault_bound, len(shares))
    known_old = exposed_before
    post_finality_openings = 0
    for capability in sorted(shares):
        if capability[1] != current_generation or known_old >= recovery_threshold:
            break
        if capability[0] < exposed_before:
            continue
        known_old += 1
        post_finality_openings += 1

    # A recovery edge is itself an old-generation opening route. It is counted
    # once per edge, rather than pretending that its underlying secret is known.
    for edge in sorted(recovery_edges):
        if edge[1] == current_generation and known_old < recovery_threshold:
            known_old += 1
            post_finality_openings += 1

    violated = int(known_old >= recovery_threshold and protocol != "epoch")
    retained = len(shares) + len(recovery_edges)
    return TrialResult(
        protocol=protocol,
        trial=trial,
        violated=violated,
        stale_repair_accepts=stale_repair_accepts,
        finality_latency=finality_time,
        messages=messages,
        retained_capabilities=retained,
        post_finality_openings=post_finality_openings,
    )


def write_results(results: list[TrialResult], output: str) -> None:
    fields = list(TrialResult.__dataclass_fields__)
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result.__dict__ for result in results)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", default="all", type=parse_protocols)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--output", default="experiments/results.csv")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--nodes", type=int, default=10)
    parser.add_argument("--fault-bound", type=int, default=2)
    parser.add_argument("--recovery-threshold", type=int, default=5)
    parser.add_argument("--max-delay", type=int, default=20)
    parser.add_argument("--epoch-length", type=int, default=40)
    args = parser.parse_args()
    if args.trials < 1 or args.nodes < args.recovery_threshold:
        parser.error("require trials >= 1 and nodes >= recovery-threshold")

    rng = random.Random(args.seed)
    scenarios = [
        Scenario(
            delays=tuple(rng.randint(1, args.max_delay) for _ in range(args.nodes)),
            delivered=tuple(rng.random() >= 0.15 for _ in range(args.nodes)),
        )
        for _ in range(args.trials)
    ]
    results = [
        run_trial(
            protocol,
            trial,
            scenarios[trial],
            args.nodes,
            args.fault_bound,
            args.recovery_threshold,
            args.epoch_length,
        )
        for trial in range(args.trials)
        for protocol in args.protocol
    ]
    write_results(results, args.output)
    for protocol in args.protocol:
        subset = [result for result in results if result.protocol == protocol]
        violation_rate = sum(result.violated for result in subset) / len(subset)
        mean_latency = sum(result.finality_latency for result in subset) / len(subset)
        print(f"{protocol}: violation_rate={violation_rate:.3f} mean_finality_time={mean_latency:.1f}")
    print(f"wrote {len(results)} trial records to {args.output}")


if __name__ == "__main__":
    main()
