#!/usr/bin/env python3
"""Abstract per-instance threshold state for handoff microbenchmarks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


ELEMENT_BYTES = 32
KEY_SHARE_BYTES = 32
RECORD_METADATA_BYTES = 128
SEALED_RECORD_BYTES = 96


@dataclass(frozen=True)
class ShareContext:
    configuration: str
    generation: int
    members: tuple[str, ...]
    threshold: int

    def __post_init__(self) -> None:
        if not self.members or len(set(self.members)) != len(self.members) or not 1 <= self.threshold <= len(self.members):
            raise ValueError("invalid threshold context")


@dataclass
class AggregateShareState:
    context: ShareContext
    dimension: int
    instance_id: str = ""
    model_version: str = ""
    accepted_update_ids: set[str] = field(default_factory=set)
    phase: str = "owned"
    state_version: int = 0
    open_certificate: AggregateOpenCertificate | None = None
    handoff_record: HandoffRecord | None = None
    partial_openings: set[PartialOpening] = field(default_factory=set)

    @property
    def state_bytes(self) -> int:
        if self.phase in {"erased", "sealed"}:
            return 0
        return (
            RECORD_METADATA_BYTES
            + self.encrypted_update_sum_bytes
            + self.encrypted_key_sum_bytes
            + self.aggregate_key_share_bytes
        )

    @property
    def encrypted_update_sum_bytes(self) -> int:
        return self.dimension * ELEMENT_BYTES

    @property
    def encrypted_key_sum_bytes(self) -> int:
        return self.dimension * ELEMENT_BYTES

    @property
    def aggregate_key_share_bytes(self) -> int:
        return len(self.context.members) * KEY_SHARE_BYTES


@dataclass(frozen=True)
class HandoffRecord:
    source_context: ShareContext
    frontier_version: int
    accepted_update_ids: tuple[str, ...]
    source_state_bytes: int
    instance_id: str
    model_version: str
    state_version: int
    dimension: int


@dataclass(frozen=True)
class SealedRecord:
    instance_id: str
    model_version: str
    configuration: str
    generation: int
    accepted_update_ids: tuple[str, ...]
    record_bytes: int = SEALED_RECORD_BYTES


@dataclass(frozen=True)
class AggregateOpenCertificate:
    instance_id: str
    model_version: str
    configuration: str
    generation: int
    dimension: int
    state_version: int
    accepted_update_ids: tuple[str, ...]
    committee_members: tuple[str, ...]
    threshold: int


@dataclass(frozen=True)
class PartialOpening:
    certificate: AggregateOpenCertificate
    member: str


@dataclass(frozen=True)
class AggregateOpening:
    certificate: AggregateOpenCertificate
    members: tuple[str, ...]

    @property
    def accepted_update_ids(self) -> tuple[str, ...]:
        return self.certificate.accepted_update_ids


class AbstractThresholdBackend:
    """Models share movement without implementing a cryptographic primitive."""

    def __init__(self) -> None:
        self._states: dict[str, AggregateShareState] = {}
        self._successors: dict[HandoffRecord, AggregateShareState] = {}
        self._openings: dict[str, AggregateOpening] = {}

    def open_state(
        self,
        context: ShareContext,
        dimension: int,
        update_ids: Iterable[str] = (),
        *,
        instance_id: str,
        model_version: str,
    ) -> AggregateShareState:
        if dimension < 1:
            raise ValueError("dimension must be positive")
        if not instance_id or not model_version:
            raise ValueError("instance and model version are required")
        if instance_id in self._states:
            raise ValueError("instance already exists")
        state = AggregateShareState(
            context=context,
            dimension=dimension,
            instance_id=instance_id,
            model_version=model_version,
        )
        for update_id in update_ids:
            self.admit_update(state, update_id)
        self._states[instance_id] = state
        return state

    def admit_update(self, state: AggregateShareState, update_id: str) -> bool:
        if state.phase != "owned":
            return False
        if update_id in state.accepted_update_ids:
            return False
        state.accepted_update_ids.add(update_id)
        state.state_version += 1
        return True

    def export(self, state: AggregateShareState, frontier_version: int) -> HandoffRecord:
        if state.phase != "owned":
            raise ValueError("only owned state can be exported")
        state.phase = "exported"
        record = HandoffRecord(
            source_context=state.context,
            frontier_version=frontier_version,
            accepted_update_ids=tuple(sorted(state.accepted_update_ids)),
            source_state_bytes=state.state_bytes,
            instance_id=state.instance_id,
            model_version=state.model_version,
            state_version=state.state_version,
            dimension=state.dimension,
        )
        state.handoff_record = record
        return record

    def reshare(
        self,
        record: HandoffRecord,
        successor_context: ShareContext,
    ) -> tuple[AggregateShareState, int]:
        source = self._states.get(record.instance_id)
        if source is None or source.handoff_record != record or source.phase not in {"exported", "erased"}:
            raise ValueError("handoff must reference the current exported state")
        if successor_context.generation != record.source_context.generation + 1:
            raise ValueError("successor generation must advance by one")
        if successor_context.configuration == record.source_context.configuration:
            raise ValueError("resharing requires a successor configuration")
        if record in self._successors:
            state = self._successors[record]
            if state.context != successor_context:
                raise ValueError("handoff already has a different successor")
            return state, record.source_state_bytes + state.state_bytes
        state = AggregateShareState(
            context=successor_context,
            dimension=record.dimension,
            instance_id=record.instance_id,
            model_version=record.model_version,
            accepted_update_ids=set(record.accepted_update_ids),
            state_version=record.state_version,
            phase="installed",
            handoff_record=record,
        )
        self._successors[record] = state
        return state, record.source_state_bytes + state.state_bytes

    def confirm(self, state: AggregateShareState) -> None:
        if state.phase != "installed":
            raise ValueError("only installed state can be confirmed")
        state.phase = "confirmed"

    def activate(
        self,
        state: AggregateShareState,
        record: HandoffRecord,
    ) -> None:
        if state.phase != "confirmed":
            raise ValueError("only confirmed state can be activated")
        if self._successors.get(record) is not state:
            raise ValueError("activation must use the installed successor")
        source = self._states[record.instance_id]
        if source.phase != "erased" or source.handoff_record != record:
            raise ValueError("source state must be erased before activation")
        if state.context.generation != record.source_context.generation + 1:
            raise ValueError("successor generation must advance by one")
        if state.instance_id != record.instance_id:
            raise ValueError("successor instance must match source instance")
        if state.model_version != record.model_version:
            raise ValueError("successor model version must match source state")
        if tuple(sorted(state.accepted_update_ids)) != record.accepted_update_ids:
            raise ValueError("successor accepted set must match source state")
        if state.state_version != record.state_version:
            raise ValueError("successor state version must match source state")
        if state.dimension != record.dimension:
            raise ValueError("successor dimension must match source state")
        state.phase = "owned"
        self._states[state.instance_id] = state
        del self._successors[record]

    def authorize_open(
        self,
        state: AggregateShareState,
    ) -> AggregateOpenCertificate:
        if state.phase != "owned" or self._states.get(state.instance_id) is not state:
            raise ValueError("only writable state can authorize opening")
        if state.open_certificate is not None:
            raise ValueError("opening is already authorized")
        certificate = AggregateOpenCertificate(
            instance_id=state.instance_id,
            model_version=state.model_version,
            configuration=state.context.configuration,
            generation=state.context.generation,
            dimension=state.dimension,
            state_version=state.state_version,
            accepted_update_ids=tuple(sorted(state.accepted_update_ids)),
            committee_members=state.context.members,
            threshold=state.context.threshold,
        )
        state.open_certificate = certificate
        state.phase = "opening"
        return certificate

    def partial_open(
        self,
        state: AggregateShareState,
        certificate: AggregateOpenCertificate,
        member: str,
    ) -> PartialOpening:
        if state.phase != "opening" or state.open_certificate != certificate:
            raise ValueError("certificate does not authorize this state")
        if member not in state.context.members:
            raise ValueError("member is not in the opening committee")
        partial = PartialOpening(certificate=certificate, member=member)
        state.partial_openings.add(partial)
        return partial

    def combine_open(
        self,
        partials: Iterable[PartialOpening],
        certificate: AggregateOpenCertificate,
    ) -> AggregateOpening:
        state = self._states.get(certificate.instance_id)
        if state is None or state.phase != "opening" or state.open_certificate != certificate:
            raise ValueError("certificate must authorize the current opening state")
        partials = tuple(partials)
        members = tuple(sorted({partial.member for partial in partials}))
        if any(partial.certificate != certificate for partial in partials):
            raise ValueError("partial opening certificate mismatch")
        if any(member not in certificate.committee_members for member in members):
            raise ValueError("partial opening member is not authorized")
        if any(partial not in state.partial_openings for partial in partials):
            raise ValueError("partial opening has not been produced for this state")
        if len(members) < certificate.threshold:
            raise ValueError("insufficient partial openings")
        opening = AggregateOpening(certificate=certificate, members=members)
        self._openings[state.instance_id] = opening
        state.phase = "committed"
        return opening

    def seal(self, state: AggregateShareState) -> SealedRecord:
        if state.phase != "erased" or self._states.get(state.instance_id) is not state or state.instance_id not in self._openings:
            raise ValueError("state must be opened and erased before sealing")
        certificate = self._openings[state.instance_id].certificate
        state.phase = "sealed"
        return SealedRecord(
            instance_id=certificate.instance_id,
            model_version=certificate.model_version,
            configuration=certificate.configuration,
            generation=certificate.generation,
            accepted_update_ids=certificate.accepted_update_ids,
        )

    def erase(self, state: AggregateShareState) -> None:
        if state.phase == "exported":
            successor = self._successors.get(state.handoff_record)
            if successor is None or successor.phase != "confirmed":
                raise ValueError("source erasure requires confirmed successor installation")
        elif state.phase != "committed":
            raise ValueError("erasure requires confirmed handoff or completed opening")
        state.accepted_update_ids.clear()
        state.open_certificate = None
        state.partial_openings.clear()
        state.phase = "erased"
