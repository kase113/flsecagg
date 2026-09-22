#!/usr/bin/env python3
"""Numerical protocol core driven by ordered, already authenticated events."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction

from abstract_threshold_backend import (
    AbstractThresholdBackend,
    AggregateOpenCertificate,
    AggregateShareState,
    HandoffRecord,
    PartialOpening,
    ShareContext,
)


@dataclass(frozen=True)
class Service:
    name: str
    members: tuple[str, ...]
    fault_bound: int
    threshold: int

    def __post_init__(self):
        if (not self.name or len(set(self.members)) != len(self.members)
                or self.fault_bound < 0 or len(self.members) < 3 * self.fault_bound + 1
                or not self.fault_bound < self.threshold <= len(self.members) - self.fault_bound):
            raise ValueError("invalid service parameters")

    def context(self, generation):
        return ShareContext(self.name, generation, self.members, self.threshold)


@dataclass(frozen=True)
class Update:
    sid: str
    client: str
    update_id: str
    base_version: int
    values: tuple[Fraction, ...]
    weight: Fraction
    ciphertext: tuple[tuple[str, str], ...] | None = None


@dataclass
class Exposure:
    members: tuple[str, ...]
    bound: int
    exposed: set[str] = field(default_factory=set)
    retired: bool = False


@dataclass
class Transfer:
    record: HandoffRecord
    target: str
    successor: AggregateShareState | None = None


@dataclass
class Instance:
    state: AggregateShareState
    base_version: int
    weighted_sum: tuple[Fraction, ...]
    weight: Fraction = Fraction(0)
    updates: dict[str, Update] = field(default_factory=dict)
    phase: str = "gathering"
    transfer: Transfer | None = None
    certificate: AggregateOpenCertificate | None = None
    contributions: dict[str, PartialOpening] = field(default_factory=dict)
    result: tuple[Fraction, ...] | None = None


@dataclass(frozen=True)
class Commit:
    sid: str
    position: int
    base_version: int
    updates: tuple[str, ...]
    result: tuple[Fraction, ...]


class Pending(Exception):
    pass


class AggregationProtocol:
    """Implements instance rules; agreement, encryption and erasure are idealized."""

    def __init__(self, services, initial_service, model, buffer_size, learning_rate):
        self.services = {service.name: service for service in services}
        if len(self.services) != len(services) or initial_service not in self.services:
            raise ValueError("services require distinct names and an initial service")
        self.model = tuple(Fraction(str(value)) for value in model)
        self.learning_rate = Fraction(str(learning_rate))
        if not self.model or type(buffer_size) is not int or buffer_size < 1 or self.learning_rate <= 0:
            raise ValueError("invalid training parameters")
        self.buffer_size = buffer_size
        self.current_service = initial_service
        self.service_history = [initial_service]
        self.online = {member for service in services for member in service.members}
        self.corrupted: set[str] = set()
        self.backend = AbstractThresholdBackend()
        self.instances: dict[str, Instance] = {}
        self.accepted: dict[str, Update] = {}
        self.commits: dict[str, Commit] = {}
        self.applied: list[str] = []
        self.exposures: dict[tuple[str, int], Exposure] = {}
        self.exposure_violations: set[tuple[str, int]] = set()
        self.events: list[dict] = []

    def dispatch(self, event):
        handlers = {
            "start": self.start, "admit": self.admit, "change_service": self.change_service,
            "install": self.install, "retire": self.retire, "activate": self.activate,
            "contribute": self.contribute, "decode": self.decode, "commit": self.commit,
            "apply_result": self.apply_result, "seal": self.seal,
            "set_online": self.set_online, "corrupt": self.corrupt, "release": self.release,
        }
        arguments = deepcopy(event)
        operation = arguments.pop("operation")
        reason = ""
        try:
            if operation not in handlers:
                raise ValueError("unknown operation")
            status = handlers[operation](**arguments) or "accepted"
        except Pending as error:
            status, reason = "pending", str(error)
        except ValueError as error:
            status, reason = "rejected", str(error)
        record = {"event": deepcopy(event), "status": status, "reason": reason}
        self.events.append(deepcopy(record))
        return record

    def _instance(self, sid):
        if sid not in self.instances:
            raise ValueError("unknown instance")
        return self.instances[sid]

    def _available(self, service):
        group = self.services[service]
        if len(set(group.members) & self.online) < len(group.members) - group.fault_bound:
            raise Pending("waiting for service participants")

    def _current(self, service):
        if service != self.current_service:
            raise ValueError("operation requires current service authority")

    def _observe(self):
        for key, period in self.exposures.items():
            if not period.retired:
                period.exposed.update(self.corrupted.intersection(period.members))
            if len(period.exposed) > period.bound:
                self.exposure_violations.add(key)

    def _register(self, sid, state):
        group = self.services[state.context.configuration]
        self.exposures[(sid, state.context.generation)] = Exposure(group.members, group.fault_bound)
        self._observe()

    def start(self, sid, base_version, service):
        self._current(service)
        if not sid or sid in self.instances:
            raise ValueError("instance identifier must be new")
        if type(base_version) is not int or not 0 <= base_version <= len(self.applied):
            raise ValueError("unknown base model version")
        self._available(service)
        state = self.backend.open_state(self.services[service].context(0), len(self.model),
                                        instance_id=sid, model_version=f"v{base_version}")
        self.instances[sid] = Instance(state, base_version, (Fraction(0),) * len(self.model))
        self._register(sid, state)

    def admit(self, sid, client, update_id, values, weight, service, base_version, ciphertext=None):
        self._current(service)
        instance = self._instance(sid)
        protected = None if ciphertext is None else tuple(tuple(pair) for pair in ciphertext)
        if protected is not None and (values or any(len(pair) != 2 for pair in protected)):
            raise ValueError("protected updates require ciphertext pairs and no plaintext")
        update = Update(sid, client, update_id, base_version,
                        tuple(Fraction(str(value)) for value in values), Fraction(str(weight)), protected)
        if (not client or not update_id or update.weight <= 0
                or len(update.values if protected is None else protected) != len(self.model)
                or type(base_version) is not int or base_version != instance.base_version):
            raise ValueError("invalid update metadata or dimensions")
        if instance.updates and any((previous.ciphertext is None) != (protected is None)
                                    for previous in instance.updates.values()):
            raise ValueError("instance requires a single update representation")
        if update_id in self.accepted:
            if self.accepted[update_id] != update:
                raise ValueError("update identifier bound to different input")
            return "duplicate"
        if any(previous.client == client for previous in instance.updates.values()):
            raise ValueError("client already contributed to this instance")
        if instance.phase != "gathering":
            raise ValueError("instance participation is fixed")
        if instance.transfer is not None:
            raise Pending("instance awaiting successor activation")
        if instance.state.context.configuration != service:
            raise ValueError("service does not own this instance")
        self._available(service)
        if not self.backend.admit_update(instance.state, update_id):
            raise ValueError("threshold state refused admission")
        instance.updates[update_id] = update
        self.accepted[update_id] = update
        instance.weight += update.weight
        if protected is None:
            instance.weighted_sum = tuple(total + update.weight * value
                                          for total, value in zip(instance.weighted_sum, update.values))
        if len(instance.updates) == self.buffer_size:
            instance.certificate = self.backend.authorize_open(instance.state)
            instance.phase = "opening"

    def change_service(self, service):
        if service == self.current_service:
            return "duplicate"
        if service not in self.services or service in self.service_history:
            raise ValueError("successor requires a fresh service identifier")
        if any(instance.transfer is not None for instance in self.instances.values()):
            raise Pending("finish current instance transfers before the next service change")
        self._available(self.current_service)
        self._available(service)
        for instance in self.instances.values():
            if instance.phase == "gathering":
                record = self.backend.export(instance.state, instance.state.state_version)
                instance.transfer = Transfer(record, service)
        self.current_service = service
        self.service_history.append(service)

    def install(self, sid, generation):
        instance = self._instance(sid)
        transfer = instance.transfer
        if transfer is None or generation != transfer.record.source_context.generation + 1:
            raise ValueError("installation requires the pending successor generation")
        if transfer.successor is not None:
            return "duplicate"
        self._available(transfer.record.source_context.configuration)
        self._available(transfer.target)
        successor, _ = self.backend.reshare(transfer.record, self.services[transfer.target].context(generation))
        self.backend.confirm(successor)
        transfer.successor = successor
        self._register(sid, successor)

    def retire(self, sid, generation):
        instance = self._instance(sid)
        if instance.state.context.generation != generation:
            raise ValueError("retirement generation mismatch")
        if instance.state.phase in {"erased", "sealed"}:
            return "duplicate"
        if instance.transfer is not None:
            if instance.transfer.successor is None:
                raise Pending("retirement awaits successor installation")
        elif instance.result is None:
            raise Pending("retirement awaits recoverable aggregate")
        self.backend.erase(instance.state)
        self.exposures[(sid, generation)].retired = True

    def activate(self, sid, generation):
        instance = self._instance(sid)
        transfer = instance.transfer
        if transfer is None:
            if generation == instance.state.context.generation and instance.state.phase == "owned":
                return "duplicate"
            raise ValueError("activation requires a pending transfer")
        if generation != transfer.record.source_context.generation + 1:
            raise ValueError("activation generation mismatch")
        if transfer.successor is None or instance.state.phase != "erased":
            raise Pending("activation awaits installation and source retirement")
        self._available(transfer.target)
        self.backend.activate(transfer.successor, transfer.record)
        instance.state = transfer.successor
        instance.transfer = None

    def contribute(self, sid, member):
        instance = self._instance(sid)
        if instance.phase != "opening" or instance.certificate is None:
            raise ValueError("contribution requires an opening instance")
        if member not in instance.certificate.committee_members:
            raise ValueError("member outside the original opening authority")
        if member in instance.contributions:
            return "duplicate"
        if member not in self.online:
            raise Pending("contributor is offline")
        instance.contributions[member] = self.backend.partial_open(instance.state, instance.certificate, member)

    def decode(self, sid, decoded_sum=None):
        instance = self._instance(sid)
        if instance.result is not None:
            return "duplicate"
        if instance.certificate is None:
            raise ValueError("decode requires a fixed participation set")
        if len(instance.contributions) < instance.certificate.threshold:
            raise Pending("waiting for distinct opening contributions")
        protected = all(update.ciphertext is not None for update in instance.updates.values())
        if protected:
            if decoded_sum is None:
                raise Pending("waiting for cryptographic aggregate recovery")
            if len(decoded_sum) != len(self.model) or any(type(value) is not int for value in decoded_sum):
                raise ValueError("decoded aggregate requires an integer vector of model dimension")
            total = tuple(Fraction(value) for value in decoded_sum)
        else:
            if decoded_sum is not None:
                raise ValueError("numerical reference derives its own aggregate")
            total = instance.weighted_sum
        self.backend.combine_open(instance.contributions.values(), instance.certificate)
        instance.result = tuple(value / instance.weight for value in total)
        instance.phase = "decoded"

    def commit(self, sid, service):
        self._current(service)
        instance = self._instance(sid)
        if sid in self.commits:
            return "duplicate"
        if instance.result is None:
            raise Pending("result is awaiting aggregate recovery")
        self._available(service)
        self.commits[sid] = Commit(sid, len(self.commits), instance.base_version,
                                   tuple(instance.updates), instance.result)
        instance.phase = "committed"

    def apply_result(self, sid):
        if sid not in self.commits:
            raise Pending("model application awaits committed result")
        if sid in self.applied:
            return "duplicate"
        record = self.commits[sid]
        if record.position != len(self.applied):
            raise Pending("waiting for preceding model application")
        multiplier = self.learning_rate / (1 + len(self.applied) - record.base_version)
        self.model = tuple(value + multiplier * delta for value, delta in zip(self.model, record.result))
        self.applied.append(sid)

    def seal(self, sid):
        instance = self._instance(sid)
        if instance.phase == "sealed":
            return "duplicate"
        if sid not in self.commits or instance.state.phase != "erased":
            raise Pending("sealing awaits commitment and retirement")
        self.backend.seal(instance.state)
        instance.phase = "sealed"

    def _member(self, member):
        if not any(member in service.members for service in self.services.values()):
            raise ValueError("unknown service member")

    def set_online(self, member, online):
        self._member(member)
        if type(online) is not bool:
            raise ValueError("online must be boolean")
        if online:
            self.online.add(member)
        else:
            self.online.discard(member)

    def corrupt(self, member):
        self._member(member)
        self.corrupted.add(member)
        self._observe()

    def release(self, member):
        self._member(member)
        self.corrupted.discard(member)
