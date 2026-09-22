#!/usr/bin/env python3
"""Measure abstract aggregate-state handoff cost for active FL instances."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass

from abstract_threshold_backend import AbstractThresholdBackend, ShareContext


@dataclass(frozen=True)
class HandoffMeasurement:
    dimension: int
    old_members: int
    new_members: int
    threshold: int
    active_windows: int
    updates_per_window: int
    source_state_bytes: int
    successor_state_bytes: int
    handoff_bytes: int
    sealed_record_bytes: int


def measure(
    dimension: int,
    old_members: int,
    new_members: int,
    threshold: int,
    active_windows: int,
    updates_per_window: int,
) -> HandoffMeasurement:
    backend = AbstractThresholdBackend()
    old_context = ShareContext(
        configuration="C0",
        generation=0,
        members=tuple(f"p{index}" for index in range(old_members)),
        threshold=threshold,
    )
    new_context = ShareContext(
        configuration="C1",
        generation=1,
        members=tuple(f"q{index}" for index in range(new_members)),
        threshold=threshold,
    )
    source_state_bytes = 0
    successor_state_bytes = 0
    handoff_bytes = 0
    sealed_record_bytes = 0

    for window_index in range(active_windows):
        instance_id = f"sid-{window_index}"
        state = backend.open_state(
            old_context,
            dimension,
            instance_id=instance_id,
            model_version="v0",
        )
        for update_index in range(updates_per_window):
            backend.admit_update(state, f"u-{window_index}-{update_index}")
        record = backend.export(state, frontier_version=1)
        successor, transfer_bytes = backend.reshare(record, new_context)
        backend.confirm(successor)
        backend.erase(state)
        backend.activate(successor, record)
        certificate = backend.authorize_open(successor)
        partials = [
            backend.partial_open(successor, certificate, member)
            for member in new_context.members[: new_context.threshold]
        ]
        backend.combine_open(partials, certificate)
        successor_state_size = successor.state_bytes
        backend.erase(successor)
        sealed = backend.seal(successor)
        source_state_bytes += record.source_state_bytes
        successor_state_bytes += successor_state_size
        handoff_bytes += transfer_bytes
        sealed_record_bytes += sealed.record_bytes

    return HandoffMeasurement(
        dimension=dimension,
        old_members=old_members,
        new_members=new_members,
        threshold=threshold,
        active_windows=active_windows,
        updates_per_window=updates_per_window,
        source_state_bytes=source_state_bytes,
        successor_state_bytes=successor_state_bytes,
        handoff_bytes=handoff_bytes,
        sealed_record_bytes=sealed_record_bytes,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dimension", type=int, default=1024)
    parser.add_argument("--old-members", type=int, default=4)
    parser.add_argument("--new-members", type=int, default=4)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--active-windows", type=int, default=8)
    parser.add_argument("--updates-per-window", type=int, default=16)
    parser.add_argument("--output", default="experiments/handoff_microbench.csv")
    args = parser.parse_args()
    if min(args.dimension, args.old_members, args.new_members, args.threshold, args.active_windows, args.updates_per_window) < 1:
        parser.error("all parameters must be positive")
    if args.threshold > min(args.old_members, args.new_members):
        parser.error("threshold cannot exceed either committee size")

    measurement = measure(
        dimension=args.dimension,
        old_members=args.old_members,
        new_members=args.new_members,
        threshold=args.threshold,
        active_windows=args.active_windows,
        updates_per_window=args.updates_per_window,
    )
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(HandoffMeasurement.__dataclass_fields__))
        writer.writeheader()
        writer.writerow(asdict(measurement))
    print(f"wrote handoff measurement to {args.output}")


if __name__ == "__main__":
    main()
