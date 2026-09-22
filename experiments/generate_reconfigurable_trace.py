#!/usr/bin/env python3
"""Generate deterministic multi-window traces for reconfigurable FL."""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TraceEvent:
    order: int
    kind: str
    configuration: str
    window: str
    model_version: str
    client: str
    node: str
    record_version: str
    protection_context: str
    source_window: str
    delivered: str
    update_id: str
    source_update_id: str
    source_generation: str
    target_generation: str
    handoff_attempt_id: str
    retrained: str


def generate_trace(
    transitions: int,
    windows_per_configuration: int,
    clients_per_window: int,
    nodes: int,
    seed: int,
    include_membership_events: bool = False,
    include_handoff_abandonment: bool = False,
) -> list[TraceEvent]:
    rng = random.Random(seed)
    events: list[TraceEvent] = []
    order = 1
    window_number = 0

    def add(
        kind: str,
        configuration: str = "-",
        window: str = "-",
        model_version: str = "-",
        client: str = "-",
        node: str = "-",
        record_version: str = "-",
        protection_context: str = "-",
        source_window: str = "-",
        update_id: str = "-",
        source_update_id: str = "-",
        source_generation: str = "-",
        target_generation: str = "-",
        handoff_attempt_id: str = "-",
        retrained: str = "false",
    ) -> None:
        nonlocal order
        if kind == "client_update" and update_id == "-":
            update_id = f"upd-{window}-{client}"
        events.append(
            TraceEvent(
                order=order,
                kind=kind,
                configuration=configuration,
                window=window,
                model_version=model_version,
                client=client,
                node=node,
                record_version=record_version,
                protection_context=protection_context,
                source_window=source_window,
                delivered="true",
                update_id=update_id,
                source_update_id=source_update_id,
                source_generation=source_generation,
                target_generation=target_generation,
                handoff_attempt_id=handoff_attempt_id,
                retrained=retrained,
            )
        )
        order += 1

    for configuration_number in range(transitions + 1):
        configuration = f"C{configuration_number}"
        model_version = f"v{configuration_number}"
        active_windows: list[str] = []
        sealed_window: str | None = None
        first_client: str | None = None

        for local_window in range(windows_per_configuration):
            window = f"sid-{window_number}"
            window_number += 1
            if first_client is None:
                first_client = f"u-{window}-0"
            for client_number in range(clients_per_window):
                add(
                    "client_update",
                    configuration=configuration,
                    window=window,
                    model_version=model_version,
                    client=f"u-{window}-{client_number}",
                    record_version="1",
                    protection_context=f"ctx-{configuration}-0",
                )
            if local_window == 0:
                add("window_finalize", window=window, model_version=model_version, record_version="1")
                add(
                    "erase_receipt",
                    configuration=configuration,
                    window=window,
                    source_generation="0",
                )
                sealed_window = window
            else:
                active_windows.append(window)

        if configuration_number == transitions:
            for window in active_windows:
                add("window_finalize", window=window, model_version=model_version, record_version="1")
                add(
                    "erase_receipt",
                    configuration=configuration,
                    window=window,
                    source_generation="0",
                )
            continue

        next_configuration = f"C{configuration_number + 1}"
        if include_membership_events:
            add(
                "client_leave",
                configuration=configuration,
                client=first_client or "-",
            )
            add(
                "client_update",
                configuration=configuration,
                window=active_windows[0] if active_windows else sealed_window or "-",
                model_version=model_version,
                client=first_client or "-",
                record_version="1",
                protection_context=f"ctx-{configuration}-0",
            )
            add(
                "client_join",
                configuration=next_configuration,
                model_version=f"v{configuration_number + 1}",
                client=f"u-sid-{window_number}-0",
            )
            add(
                "committee_join",
                configuration=next_configuration,
                node=f"p-new-{configuration_number + 1}",
            )
        leaving_node_index = rng.randrange(nodes)
        leaving_node = f"p{leaving_node_index}"
        add("node_corrupt", configuration=configuration, node=leaving_node)
        add("config_install", configuration=next_configuration)
        add(
            "node_crash" if configuration_number % 2 and not include_membership_events else "committee_leave",
            configuration=configuration,
            node=leaving_node,
        )
        add("node_release", configuration=configuration, node=leaving_node)
        successor_node = f"p{(leaving_node_index + 1) % nodes}"
        add("node_corrupt", configuration=next_configuration, node=successor_node)
        abandoned_window = active_windows[0] if include_handoff_abandonment and active_windows else None
        if abandoned_window is not None:
            add(
                "handoff_abandon",
                configuration=next_configuration,
                window=abandoned_window,
                model_version=model_version,
            )
        for window in active_windows:
            if window == abandoned_window:
                rerouted_window = f"{window}-abandoned-reroute"
                add(
                    "client_resubmit",
                    configuration=next_configuration,
                    window=rerouted_window,
                    model_version=model_version,
                    client=f"late-{window}",
                    record_version="1",
                    protection_context=f"ctx-{next_configuration}-1",
                    source_window=window,
                    update_id=f"upd-abandoned-reroute-{window}",
                    source_update_id=f"upd-late-{window}",
                )
                add(
                    "window_finalize",
                    configuration=next_configuration,
                    window=rerouted_window,
                    model_version=model_version,
                    record_version="1",
                    protection_context=f"ctx-{next_configuration}-1",
                )
                add(
                    "erase_receipt",
                    configuration=next_configuration,
                    window=rerouted_window,
                    source_generation="0",
                )
                continue
            add(
                "client_update",
                configuration=configuration,
                window=window,
                model_version=model_version,
                client=f"late-{window}",
                record_version="1",
                protection_context=f"ctx-{configuration}-0",
            )
        if active_windows:
            add(
                "recover_state",
                configuration=next_configuration,
                window=active_windows[0],
                model_version=model_version,
                node=successor_node,
                record_version="2",
                protection_context=f"ctx-{next_configuration}-1",
                source_generation="0",
                target_generation="1",
                handoff_attempt_id=f"h-{next_configuration}-{active_windows[0]}",
            )
        for window in active_windows:
            if window != active_windows[0]:
                add(
                    "recover_state",
                    configuration=next_configuration,
                    window=window,
                    model_version=model_version,
                    node=successor_node,
                    record_version="2",
                    protection_context=f"ctx-{next_configuration}-1",
                    source_generation="0",
                    target_generation="1",
                    handoff_attempt_id=f"h-{next_configuration}-{window}",
                )
            add(
                "handoff_confirm",
                configuration=next_configuration,
                window=window,
                model_version=model_version,
                record_version="2",
                protection_context=f"ctx-{next_configuration}-1",
                source_generation="0",
                target_generation="1",
                handoff_attempt_id=f"h-{next_configuration}-{window}",
            )
            add(
                "client_update",
                configuration=next_configuration,
                window=window,
                model_version=model_version,
                client=f"late-{window}",
                record_version="2",
                protection_context=f"ctx-{next_configuration}-1",
                update_id=f"upd-late-{window}",
                source_generation="1",
            )
            add(
                "erase_receipt",
                configuration=configuration,
                window=window,
                source_generation="0",
                handoff_attempt_id=f"h-{next_configuration}-{window}",
            )
            add(
                "client_update",
                configuration=next_configuration,
                window=window,
                model_version=model_version,
                client=f"late-{window}",
                record_version="3",
                protection_context=f"ctx-{next_configuration}-1",
                update_id=f"upd-late-{window}",
                source_generation="1",
            )
            rerouted_window = f"{window}-reroute"
            add(
                "client_resubmit",
                configuration=next_configuration,
                window=rerouted_window,
                model_version=model_version,
                client=f"late-{window}",
                record_version="1",
                protection_context=f"ctx-{next_configuration}-1",
                source_window=window,
                update_id=f"upd-reroute-{window}",
                source_update_id=f"upd-late-{window}",
            )
            add("window_finalize", configuration=next_configuration, window=window, model_version=model_version, record_version="2", protection_context=f"ctx-{next_configuration}-1")
            add(
                "erase_receipt",
                configuration=next_configuration,
                window=window,
                source_generation="1",
            )
            add("window_finalize", configuration=next_configuration, window=rerouted_window, model_version=model_version, record_version="1", protection_context=f"ctx-{next_configuration}-1")
            add(
                "erase_receipt",
                configuration=next_configuration,
                window=rerouted_window,
                source_generation="0",
            )
        if sealed_window is not None:
            add(
                "message_deliver",
                configuration=next_configuration,
                window=sealed_window,
                model_version=model_version,
                record_version="1",
            )
        add("node_recover", configuration=next_configuration, node=leaving_node, record_version="2")
        add("node_release", configuration=next_configuration, node=successor_node)

    return events


def write_trace(events: list[TraceEvent], output: str) -> None:
    fields = list(TraceEvent.__dataclass_fields__)
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(event) for event in events)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transitions", type=int, default=2)
    parser.add_argument("--windows-per-configuration", type=int, default=4)
    parser.add_argument("--clients-per-window", type=int, default=2)
    parser.add_argument("--nodes", type=int, default=6)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--include-membership-events", action="store_true")
    parser.add_argument("--include-handoff-abandonment", action="store_true")
    parser.add_argument("--output", default="experiments/reconfigurable_trace.csv")
    args = parser.parse_args()
    if args.transitions < 0 or args.windows_per_configuration < 1 or args.clients_per_window < 1:
        parser.error("transitions must be non-negative and window/client counts must be positive")
    if args.nodes < 1:
        parser.error("nodes must be positive")

    events = generate_trace(
        args.transitions,
        args.windows_per_configuration,
        args.clients_per_window,
        args.nodes,
        args.seed,
        args.include_membership_events,
        args.include_handoff_abandonment,
    )
    write_trace(events, args.output)
    print(f"wrote {len(events)} events to {args.output}")


if __name__ == "__main__":
    main()
