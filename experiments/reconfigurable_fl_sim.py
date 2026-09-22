#!/usr/bin/env python3
"""Event-driven simulator for committee reconfiguration in asynchronous FL."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from typing import Iterable


PROTOCOLS = ("static", "full-transfer", "periodic-rekey", "selective-finality")
EVENT_KINDS = {
    "client_update",
    "config_install",
    "client_join",
    "client_leave",
    "committee_join",
    "committee_leave",
    "node_leave",
    "node_crash",
    "node_recover",
    "node_corrupt",
    "node_release",
    "recover_state",
    "message_deliver",
    "handoff_confirm",
    "handoff_abandon",
    "client_resubmit",
    "window_finalize",
    "erase_receipt",
}
REJECTION_REASONS = {
    "client_ineligible",
    "duplicate_update",
    "wrong_model_version",
    "old_configuration",
    "old_generation",
    "frontier_closed",
    "handoff_not_installed",
    "duplicate_handoff_confirmation",
    "sealed_window",
    "stale_record",
    "unavailable_owner",
    "invalid_transition",
}
LIVE_RECORD_BYTES = 256
SEALED_RECORD_BYTES = 96


@dataclass(frozen=True)
class TraceEvent:
    order: int
    kind: str
    configuration: str | None
    window: str | None
    model_version: str | None
    client: str | None
    node: str | None
    record_version: int | None
    protection_context: str | None
    source_window: str | None
    delivered: bool
    update_id: str | None
    source_update_id: str | None
    source_generation: int | None
    target_generation: int | None
    handoff_attempt_id: str | None
    retrained: bool


@dataclass
class Window:
    window: str
    model_version: str
    owner_configuration: str
    status: str = "accepted"
    accepted_clients: set[str] = field(default_factory=set)
    accepted_update_ids: set[str] = field(default_factory=set)
    accepted_update_log: list[str] = field(default_factory=list)
    frontier_update_ids: list[str] = field(default_factory=list)
    record_version: int = 0
    frontier_record_version: int = 0
    generation: int = 0
    protection_context: str = ""
    recoverable_owner: str | None = None
    handoff_target_configuration: str | None = None
    handoff_status: str = "owned"
    erase_status: str = "initial"
    handoff_attempt_id: str | None = None
    handoff_source_configuration: str | None = None
    handoff_order: int | None = None
    handoff_confirm_order: int | None = None
    handoff_count: int = 0
    handoff_bytes: int = 0
    resubmitted_updates: int = 0
    finalized_order: int | None = None
    rejected_messages: int = 0
    blocked_updates: int = 0
    unavailable_nodes_at_finalize: int = 0
    retained_record_bytes: int = LIVE_RECORD_BYTES
    state_recovery_count: int = 0


@dataclass
class SimulationResult:
    protocol: str
    window: str
    final_status: str
    final_model_version: str
    owner_configuration: str
    accepted_clients: str
    resubmitted_updates: int
    handoff_delay: int
    completion_order: int
    rejected_messages: int
    retained_record_bytes: int
    blocked_updates: int
    unavailable_nodes_at_finalize: int
    handoffs: int
    state_recoveries: int
    corruption_events: int
    peak_corrupted_nodes: int
    frontier_record_version: int
    generation: int
    protection_context: str
    handoff_status: str
    handoff_bytes: int
    erase_status: str
    frontier_update_ids: str
    accepted_update_ids: str


@dataclass(frozen=True)
class EventResult:
    protocol: str
    order: int
    kind: str
    event_result: str
    rejection_reason: str | None
    sid: str | None
    update_id: str | None
    source_update_id: str | None
    owner_configuration: str | None
    recoverable_owner: str | None
    generation: int
    handoff_status: str
    erase_status: str
    accepted_update_ids: str
    frontier_update_ids: str


def _optional(value: str) -> str | None:
    value = value.strip()
    return None if value in {"", "-"} else value


def _boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"invalid delivered value: {value}")
    return normalized == "true"


def load_trace(path: str) -> list[TraceEvent]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = [
            "order",
            "kind",
            "configuration",
            "window",
            "model_version",
            "client",
            "node",
            "record_version",
            "protection_context",
            "source_window",
            "delivered",
            "update_id",
            "source_update_id",
            "source_generation",
            "target_generation",
            "handoff_attempt_id",
            "retrained",
        ]
        if reader.fieldnames != expected:
            raise ValueError(
                "trace must use A0 columns in order; expected " + ",".join(expected)
            )

        events: list[TraceEvent] = []
        for row in reader:
            kind = row["kind"].strip()
            if kind not in EVENT_KINDS:
                raise ValueError(f"unknown event kind: {kind}")
            record_version = _optional(row["record_version"])
            source_generation = _optional(row["source_generation"])
            target_generation = _optional(row["target_generation"])
            events.append(
                TraceEvent(
                    order=int(row["order"]),
                    kind=kind,
                    configuration=_optional(row["configuration"]),
                    window=_optional(row["window"]),
                    model_version=_optional(row["model_version"]),
                    client=_optional(row["client"]),
                    node=_optional(row["node"]),
                    record_version=int(record_version) if record_version else None,
                    protection_context=_optional(row["protection_context"]),
                    source_window=_optional(row["source_window"]),
                    delivered=_boolean(row["delivered"]),
                    update_id=_optional(row["update_id"]),
                    source_update_id=_optional(row["source_update_id"]),
                    source_generation=(int(source_generation) if source_generation else None),
                    target_generation=(int(target_generation) if target_generation else None),
                    handoff_attempt_id=_optional(row["handoff_attempt_id"]),
                    retrained=_boolean(row["retrained"]),
                )
            )
    return sorted(events, key=lambda event: event.order)


class Simulator:
    def __init__(self, protocol: str, nodes: int, initial_configuration: str) -> None:
        self.protocol = protocol
        self.nodes = {f"p{node}" for node in range(nodes)}
        self.unavailable_nodes: set[str] = set()
        self.corrupted_nodes: set[str] = set()
        self.corruption_events = 0
        self.peak_corrupted_nodes = 0
        self.initial_configuration = initial_configuration
        self.active_configuration = initial_configuration
        self.pending_configuration: str | None = None
        self.windows: dict[str, Window] = {}
        self.client_status: dict[str, bool] = {}
        self.event_results: list[EventResult] = []
        self._current_result = "accepted"
        self._current_reason: str | None = None

    def _reject(self, window: Window | None = None, reason: str = "invalid_transition") -> None:
        self._current_result = "rejected"
        self._current_reason = reason
        if window is not None:
            window.rejected_messages += 1

    def _pending(self, window: Window | None = None, reason: str = "invalid_transition") -> None:
        self._current_result = "pending"
        self._current_reason = reason
        if window is not None:
            window.blocked_updates += 1

    def _duplicate(self, window: Window | None = None, reason: str = "duplicate_update") -> None:
        self._current_result = "duplicate"
        self._current_reason = reason
        if window is not None:
            window.rejected_messages += 1

    def _start_event(self) -> None:
        self._current_result = "accepted"
        self._current_reason = None

    def _finish_event(self, event: TraceEvent) -> None:
        window = self.windows.get(event.window or event.source_window or "")
        self.event_results.append(
            EventResult(
                protocol=self.protocol,
                order=event.order,
                kind=event.kind,
                event_result=self._current_result,
                rejection_reason=self._current_reason,
                sid=window.window if window is not None else event.window,
                update_id=event.update_id,
                source_update_id=event.source_update_id,
                owner_configuration=window.owner_configuration if window is not None else None,
                recoverable_owner=window.recoverable_owner if window is not None else None,
                generation=window.generation if window is not None else 0,
                handoff_status=window.handoff_status if window is not None else "owned",
                erase_status=window.erase_status if window is not None else "initial",
                accepted_update_ids="|".join(window.accepted_update_log) if window is not None else "",
                frontier_update_ids="|".join(window.frontier_update_ids) if window is not None else "",
            )
        )

    def _new_window(self, event: TraceEvent, configuration: str) -> Window:
        if event.window is None:
            raise ValueError("window is required")
        window = Window(
            window=event.window,
            model_version=event.model_version or "unknown",
            owner_configuration=configuration,
            recoverable_owner=configuration,
            protection_context=event.protection_context or f"ctx-{configuration}-0",
        )
        self.windows[event.window] = window
        return window

    def _admit_update(self, window: Window, event: TraceEvent) -> None:
        if event.update_id is None:
            raise ValueError("client update requires update_id")
        if window.status in {"committed", "sealed", "abandoned"}:
            self._reject(window, "sealed_window")
            return
        if event.model_version is not None and event.model_version != window.model_version:
            self._reject(window, "wrong_model_version")
            return
        if event.source_generation is not None and event.source_generation != window.generation:
            self._reject(window, "old_generation")
            return
        if event.record_version is not None and event.record_version < window.record_version:
            self._reject(window, "stale_record")
            return
        if window.handoff_status in {"handoff_pending", "installed"}:
            self._reject(window, "frontier_closed")
            return
        if window.handoff_status == "confirmed" and window.erase_status != "erased":
            self._pending(window, "invalid_transition")
            return
        if event.update_id in window.accepted_update_ids:
            self._duplicate(window)
            return
        if len(self.unavailable_nodes) == len(self.nodes):
            self._pending(window, "unavailable_owner")
            return
        window.accepted_update_ids.add(event.update_id)
        window.accepted_update_log.append(event.update_id)
        if event.client is not None:
            window.accepted_clients.add(event.client)
        window.record_version += 1

    def _export_active_windows(self, configuration: str, order: int) -> None:
        for window in self.windows.values():
            if window.status not in {"accepted", "transferred"}:
                continue
            if window.handoff_status not in {"owned", "confirmed"}:
                continue
            window.frontier_record_version = window.record_version
            window.frontier_update_ids = list(window.accepted_update_log)
            window.handoff_source_configuration = window.owner_configuration
            window.handoff_target_configuration = configuration
            window.handoff_status = "handoff_pending"
            window.erase_status = "pending"
            window.handoff_attempt_id = f"h-{configuration}-{window.window}"
            window.handoff_order = order
            window.handoff_count += 1
            window.handoff_bytes += LIVE_RECORD_BYTES

    def _transfer_all_windows(self, configuration: str, order: int) -> None:
        self._export_active_windows(configuration, order)
        for window in self.windows.values():
            if window.status not in {"committed", "sealed"}:
                continue
            window.handoff_order = order
            window.handoff_count += 1
            window.retained_record_bytes = LIVE_RECORD_BYTES
            window.handoff_bytes += LIVE_RECORD_BYTES

    def _finish_periodic_transition(self) -> None:
        if self.pending_configuration is None:
            return
        if any(window.status in {"accepted", "transferred"} for window in self.windows.values()):
            return
        self.active_configuration = self.pending_configuration
        self.pending_configuration = None

    def _handle_config_install(self, event: TraceEvent) -> None:
        if event.configuration is None:
            raise ValueError("config_install requires a configuration")
        if self.protocol == "static":
            return
        if self.protocol == "periodic-rekey":
            self.pending_configuration = event.configuration
            self._finish_periodic_transition()
            return
        self.active_configuration = event.configuration
        if self.protocol == "full-transfer":
            self._transfer_all_windows(event.configuration, event.order)
        else:
            self._export_active_windows(event.configuration, event.order)

    def _handle_client_update(self, event: TraceEvent) -> None:
        if event.window is None:
            raise ValueError("client_update requires a window")
        if event.client is None or not self.client_status.get(event.client, True):
            window = self.windows.get(event.window)
            if window is not None:
                self._reject(window, "client_ineligible")
            return
        target = event.configuration or self.active_configuration
        window = self.windows.get(event.window)
        if self.protocol == "static" and target != self.initial_configuration:
            self._reject(window, "old_configuration")
            return
        if self.protocol == "periodic-rekey" and self.pending_configuration is not None and window is None:
            self._pending(window, "old_configuration")
            return
        if target != self.active_configuration:
            self._reject(window, "old_configuration")
            return
        if window is None:
            if len(self.unavailable_nodes) == len(self.nodes):
                self._pending(window, "unavailable_owner")
                return
            window = self._new_window(event, target)
        else:
            if window.status in {"committed", "sealed", "abandoned", "rejected"}:
                self._reject(window, "sealed_window")
                return
            if target != window.owner_configuration:
                if target == window.handoff_target_configuration:
                    self._pending(window, "handoff_not_installed")
                else:
                    self._reject(window, "old_configuration")
                return
        self._admit_update(window, event)

    def _handle_finalize(self, event: TraceEvent) -> None:
        if event.window is None:
            raise ValueError("window_finalize requires a window")
        target = event.configuration or self.active_configuration
        window = self.windows.get(event.window)
        if window is None:
            self._reject(None, "invalid_transition")
            return
        if target != self.active_configuration:
            self._reject(window, "old_configuration")
            return
        if target != window.owner_configuration:
            self._reject(window, "old_configuration")
            return
        if window.status in {"committed", "sealed", "abandoned", "rejected"}:
            self._duplicate(window, "sealed_window")
            return
        if event.model_version is not None and event.model_version != window.model_version:
            self._reject(window, "wrong_model_version")
            return
        if window.handoff_status in {"handoff_pending", "installed"}:
            self._pending(window, "handoff_not_installed")
            return
        if window.handoff_status == "confirmed" and window.erase_status != "erased":
            self._pending(window, "invalid_transition")
            return
        window.status = "committed"
        window.handoff_status = "seal_pending"
        window.erase_status = "pending"
        window.finalized_order = event.order
        window.unavailable_nodes_at_finalize = len(self.unavailable_nodes)
        window.retained_record_bytes = SEALED_RECORD_BYTES
        self._finish_periodic_transition()

    def _handle_message(self, event: TraceEvent) -> None:
        if event.window is None or event.window not in self.windows:
            return
        window = self.windows[event.window]
        if not event.delivered or window.status in {"committed", "sealed", "abandoned"}:
            self._reject(window, "sealed_window")
            return
        if event.record_version is not None and event.record_version < window.record_version:
            self._reject(window)
            return
        if self.protocol == "static":
            self._reject(window, "old_configuration")
            return
        if event.configuration is None or event.configuration != self.active_configuration:
            self._reject(window, "old_configuration")
            return
        if self.protocol == "full-transfer" and window.handoff_status == "handoff_pending":
            window.handoff_status = "installed"
            window.handoff_target_configuration = event.configuration
            window.record_version = max(window.record_version, event.record_version or window.record_version)
            return
        self._reject(window, "invalid_transition")

    def _handle_recover_state(self, event: TraceEvent) -> None:
        if event.window is None or event.node is None:
            raise ValueError("recover_state requires a window and node")
        window = self.windows.get(event.window)
        if window is None or event.node in self.unavailable_nodes:
            if window is not None:
                self._reject(window, "unavailable_owner")
            return
        if not event.delivered or window.status in {"committed", "sealed", "abandoned", "rejected"}:
            self._reject(window, "sealed_window")
            return
        source_recovery = (
            self.protocol != "static"
            and event.configuration == window.handoff_source_configuration
            and event.configuration == window.owner_configuration
            and window.handoff_status in {"handoff_pending", "installed"}
        )
        if source_recovery:
            if event.handoff_attempt_id != window.handoff_attempt_id:
                self._reject(window, "stale_record")
                return
            if event.source_generation is not None and event.source_generation != window.generation:
                self._reject(window, "old_generation")
                return
            if event.record_version is not None and event.record_version < window.record_version:
                self._reject(window, "stale_record")
                return
            window.handoff_status = "handoff_pending"
            window.state_recovery_count += 1
            return
        if self.protocol == "static" or event.configuration != self.active_configuration:
            self._reject(window, "old_configuration")
            return
        if event.configuration != window.handoff_target_configuration or window.handoff_status != "handoff_pending":
            self._reject(window, "handoff_not_installed")
            return
        if event.handoff_attempt_id != window.handoff_attempt_id:
            self._reject(window, "stale_record")
            return
        if event.source_generation is not None and event.source_generation != window.generation:
            self._reject(window, "old_generation")
            return
        if event.target_generation is not None and event.target_generation != window.generation + 1:
            self._reject(window, "old_generation")
            return
        if event.record_version is not None and event.record_version < window.record_version:
            self._reject(window, "stale_record")
            return
        window.handoff_status = "installed"
        window.protection_context = event.protection_context or f"ctx-{event.configuration}-{window.generation + 1}"
        window.record_version = max(window.record_version, event.record_version or window.record_version)
        window.state_recovery_count += 1

    def _handle_handoff_confirm(self, event: TraceEvent) -> None:
        if event.window is None:
            raise ValueError("handoff_confirm requires a window")
        window = self.windows.get(event.window)
        if window is None or window.status in {"committed", "sealed", "abandoned", "rejected"}:
            if window is not None:
                self._reject(window, "sealed_window")
            return
        if not event.delivered or event.configuration != self.active_configuration:
            self._reject(window, "old_configuration")
            return
        if window.handoff_status == "confirmed":
            self._duplicate(window, "duplicate_handoff_confirmation")
            return
        if event.configuration != window.handoff_target_configuration or window.handoff_status != "installed":
            self._reject(window, "handoff_not_installed")
            return
        if event.handoff_attempt_id != window.handoff_attempt_id:
            self._reject(window, "stale_record")
            return
        if event.source_generation is not None and event.source_generation != window.generation:
            self._reject(window, "old_generation")
            return
        if event.target_generation is not None and event.target_generation != window.generation + 1:
            self._reject(window, "old_generation")
            return
        if event.record_version is not None and event.record_version < window.record_version:
            self._reject(window, "stale_record")
            return
        window.status = "transferred"
        window.protection_context = event.protection_context or f"ctx-{event.configuration}-{window.generation}"
        window.record_version = max(window.record_version, event.record_version or window.record_version)
        window.handoff_status = "confirmed"
        window.handoff_confirm_order = event.order

    def _handle_erase_receipt(self, event: TraceEvent) -> None:
        if event.window is None:
            self._reject(None, "invalid_transition")
            return
        window = self.windows.get(event.window)
        if window is None:
            self._reject(None, "invalid_transition")
            return
        if not event.delivered:
            self._reject(window, "invalid_transition")
            return
        if window.handoff_status == "sealed":
            self._duplicate(window, "sealed_window")
            return
        if window.status == "committed" and window.handoff_status == "seal_pending":
            if (
                event.configuration != window.owner_configuration
                or event.source_generation != window.generation
                or event.handoff_attempt_id is not None
            ):
                self._reject(window, "stale_record")
                return
            window.erase_status = "erased"
            window.status = "sealed"
            window.handoff_status = "sealed"
            return
        if window.handoff_status != "confirmed":
            self._reject(window, "handoff_not_installed")
            return
        if (
            event.configuration != window.handoff_source_configuration
            or event.source_generation != window.generation
            or event.handoff_attempt_id != window.handoff_attempt_id
        ):
            self._reject(window, "stale_record")
            return
        if window.erase_status == "erased":
            self._duplicate(window, "invalid_transition")
            return
        window.erase_status = "erased"
        window.owner_configuration = window.handoff_target_configuration or window.owner_configuration
        window.recoverable_owner = window.owner_configuration
        window.generation += 1
        window.status = "transferred"

    def _handle_handoff_abandon(self, event: TraceEvent) -> None:
        if event.window is None:
            self._reject(None, "invalid_transition")
            return
        window = self.windows.get(event.window)
        if window is None:
            self._reject(None, "invalid_transition")
            return
        if window.status in {"committed", "sealed", "abandoned", "rejected"}:
            self._reject(window, "sealed_window")
            return
        if not event.delivered or event.configuration != self.active_configuration:
            self._reject(window, "old_configuration")
            return
        if window.handoff_status not in {"handoff_pending", "installed", "confirmed"}:
            self._reject(window, "handoff_not_installed")
            return
        window.status = "abandoned"
        window.handoff_status = "abandoned"
        window.recoverable_owner = None

    def _handle_client_resubmit(self, event: TraceEvent) -> None:
        if event.window is None or event.client is None or event.source_window is None:
            raise ValueError("client_resubmit requires source_window, window, and client")
        source = self.windows.get(event.source_window)
        if source is None or source.handoff_status not in {"confirmed", "sealed", "abandoned"}:
            if source is not None:
                self._reject(source, "handoff_not_installed")
            return
        if not self.client_status.get(event.client, True):
            self._reject(source, "client_ineligible")
            return
        if event.configuration != self.active_configuration:
            self._reject(source, "old_configuration")
            return
        if event.model_version is not None and event.model_version != source.model_version:
            self._reject(source, "wrong_model_version")
            return
        target = self.windows.get(event.window)
        if target is None:
            target = self._new_window(event, event.configuration)
        before = len(target.accepted_update_ids)
        self._admit_update(target, event)
        if len(target.accepted_update_ids) != before:
            target.resubmitted_updates += 1

    def _handle_client_join(self, event: TraceEvent) -> None:
        if event.client is None:
            raise ValueError("client_join requires a client")
        self.client_status[event.client] = True

    def _handle_client_leave(self, event: TraceEvent) -> None:
        if event.client is None:
            raise ValueError("client_leave requires a client")
        self.client_status[event.client] = False

    def _handle_committee_join(self, event: TraceEvent) -> None:
        if event.node is None:
            raise ValueError("committee_join requires a node")
        self.nodes.add(event.node)
        self.unavailable_nodes.discard(event.node)

    def _handle_node_corrupt(self, event: TraceEvent) -> None:
        if event.node is None:
            raise ValueError("node_corrupt requires a node")
        self.corrupted_nodes.add(event.node)
        self.corruption_events += 1
        self.peak_corrupted_nodes = max(self.peak_corrupted_nodes, len(self.corrupted_nodes))

    def _handle_node_release(self, event: TraceEvent) -> None:
        if event.node is None:
            raise ValueError("node_release requires a node")
        self.corrupted_nodes.discard(event.node)

    def apply(self, event: TraceEvent) -> None:
        self._start_event()
        if event.kind == "config_install":
            self._handle_config_install(event)
        elif event.kind == "client_join":
            self._handle_client_join(event)
        elif event.kind == "client_leave":
            self._handle_client_leave(event)
        elif event.kind == "committee_join":
            self._handle_committee_join(event)
        elif event.kind == "client_update":
            self._handle_client_update(event)
        elif event.kind == "window_finalize":
            self._handle_finalize(event)
        elif event.kind == "message_deliver":
            self._handle_message(event)
        elif event.kind == "recover_state":
            self._handle_recover_state(event)
        elif event.kind == "handoff_confirm":
            self._handle_handoff_confirm(event)
        elif event.kind == "handoff_abandon":
            self._handle_handoff_abandon(event)
        elif event.kind == "client_resubmit":
            self._handle_client_resubmit(event)
        elif event.kind == "erase_receipt":
            self._handle_erase_receipt(event)
        elif event.kind in {"node_leave", "committee_leave", "node_crash"}:
            if event.node is not None:
                self.unavailable_nodes.add(event.node)
        elif event.kind == "node_recover":
            if event.node is not None:
                self.unavailable_nodes.discard(event.node)
        elif event.kind == "node_corrupt":
            self._handle_node_corrupt(event)
        elif event.kind == "node_release":
            self._handle_node_release(event)
        self._finish_event(event)

    def results(self) -> list[SimulationResult]:
        output: list[SimulationResult] = []
        for window in self.windows.values():
            finalized = window.finalized_order or 0
            handoff_delay = 0
            if window.handoff_order is not None and window.finalized_order is not None:
                handoff_delay = max(0, window.finalized_order - window.handoff_order)
            output.append(
                SimulationResult(
                    protocol=self.protocol,
                    window=window.window,
                    final_status=window.status,
                    final_model_version=window.model_version,
                    owner_configuration=window.owner_configuration,
                    accepted_clients="|".join(sorted(window.accepted_clients)),
                    resubmitted_updates=window.resubmitted_updates,
                    handoff_delay=handoff_delay,
                    completion_order=finalized,
                    rejected_messages=window.rejected_messages,
                    retained_record_bytes=window.retained_record_bytes,
                    blocked_updates=window.blocked_updates,
                    unavailable_nodes_at_finalize=window.unavailable_nodes_at_finalize,
                    handoffs=window.handoff_count,
                    state_recoveries=window.state_recovery_count,
                    corruption_events=self.corruption_events,
                    peak_corrupted_nodes=self.peak_corrupted_nodes,
                    frontier_record_version=window.frontier_record_version,
                    generation=window.generation,
                    protection_context=window.protection_context,
                    handoff_status=window.handoff_status,
                    handoff_bytes=window.handoff_bytes,
                    erase_status=window.erase_status,
                    frontier_update_ids="|".join(window.frontier_update_ids),
                    accepted_update_ids="|".join(window.accepted_update_log),
                )
            )
        return sorted(output, key=lambda result: result.window)

    def event_log(self) -> list[EventResult]:
        return list(self.event_results)


def parse_protocols(value: str) -> Iterable[str]:
    protocols = PROTOCOLS if value == "all" else tuple(value.split(","))
    unknown = set(protocols) - set(PROTOCOLS)
    if unknown:
        raise argparse.ArgumentTypeError("unknown protocol: " + ",".join(sorted(unknown)))
    return protocols


def write_results(results: list[SimulationResult], output: str) -> None:
    fields = list(SimulationResult.__dataclass_fields__)
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result.__dict__ for result in results)


def write_event_results(results: list[EventResult], output: str) -> None:
    fields = list(EventResult.__dataclass_fields__)
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result.__dict__ for result in results)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--protocol", default="all", type=parse_protocols)
    parser.add_argument("--output", default="experiments/reconfigurable_results.csv")
    parser.add_argument("--event-output", default="experiments/reconfigurable_event_results.csv")
    parser.add_argument("--nodes", type=int, default=6)
    parser.add_argument("--initial-configuration", default="C0")
    args = parser.parse_args()
    if args.nodes < 1:
        parser.error("nodes must be positive")

    events = load_trace(args.trace)
    results: list[SimulationResult] = []
    event_results: list[EventResult] = []
    for protocol in args.protocol:
        simulator = Simulator(protocol, args.nodes, args.initial_configuration)
        for event in events:
            simulator.apply(event)
        results.extend(simulator.results())
        event_results.extend(
            simulator.event_log()
        )
    write_results(results, args.output)
    write_event_results(event_results, args.event_output)
    print(f"wrote {len(results)} window records to {args.output}")
    print(f"wrote {len(event_results)} event records to {args.event_output}")


if __name__ == "__main__":
    main()
