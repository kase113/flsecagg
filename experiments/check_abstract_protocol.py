#!/usr/bin/env python3
"""Check abstract handoff and aggregate opening against protocol invariants."""

from dataclasses import replace
from itertools import permutations

from abstract_threshold_backend import (
    AbstractThresholdBackend,
    PartialOpening,
    ShareContext,
)


def rejects(operation, expected_message: str) -> None:
    try:
        operation()
    except ValueError as error:
        assert expected_message in str(error), str(error)
    else:
        raise AssertionError(f"expected rejection: {expected_message}")


def main() -> None:
    contexts = (
        ShareContext("C0", 0, ("p0", "p1", "p2", "p3"), 3),
        ShareContext("C1", 1, ("q0", "q1", "q2", "q3", "q4"), 3),
        ShareContext("C2", 2, ("r0", "r1", "r2", "r3"), 2),
    )
    backend = AbstractThresholdBackend()
    state = backend.open_state(contexts[0], 8, ("u0", "u1"), instance_id="sid", model_version="v0")
    assert not backend.admit_update(state, "u0")
    assert state.state_version == 2
    rejects(lambda: ShareContext("C0", 0, ("p0", "p0"), 2), "invalid threshold")
    rejects(lambda: backend.open_state(contexts[0], 8, instance_id="sid", model_version="v0"), "already exists")
    rejects(lambda: backend.erase(state), "requires confirmed handoff")

    for successor_context in contexts[1:]:
        source = state
        record = backend.export(source, successor_context.generation)
        prefix = record.accepted_update_ids
        assert not backend.admit_update(source, "late-source")
        rejects(lambda: backend.erase(source), "confirmed successor")
        rejects(lambda: backend.reshare(replace(record, dimension=16), successor_context), "current exported state")
        successor, _ = backend.reshare(record, successor_context)
        retry, _ = backend.reshare(record, successor_context)
        assert retry is successor
        assert successor.dimension == 8
        assert tuple(sorted(successor.accepted_update_ids)) == prefix
        assert successor.state_version == record.state_version
        rejects(lambda: backend.reshare(record, replace(successor_context, configuration="fork")), "different successor")
        rejects(lambda: backend.erase(source), "confirmed successor")
        rejects(lambda: backend.authorize_open(successor), "only writable state")
        backend.confirm(successor)
        rejects(lambda: backend.activate(successor, record), "must be erased")
        assert not backend.admit_update(successor, "premature")
        backend.erase(source)
        assert source.state_bytes == 0
        rejects(lambda: backend.activate(replace(successor), record), "installed successor")
        backend.activate(successor, record)
        rejects(lambda: backend.reshare(record, successor_context), "current exported state")
        rejects(lambda: backend.authorize_open(source), "only writable state")
        assert backend.admit_update(successor, f"u{successor_context.generation + 1}")
        assert set(prefix) < successor.accepted_update_ids
        state = successor

    certificate = backend.authorize_open(state)
    assert state.phase == "opening"
    assert certificate.instance_id == "sid" and certificate.model_version == "v0"
    assert certificate.accepted_update_ids == ("u0", "u1", "u2", "u3")
    assert not backend.admit_update(state, "after-authorize")
    rejects(lambda: backend.authorize_open(state), "only writable state")
    rejects(lambda: backend.export(state, 3), "only owned state")
    rejects(lambda: backend.erase(state), "requires confirmed handoff")
    rejects(lambda: backend.seal(state), "opened and erased")
    rejects(lambda: backend.partial_open(state, certificate, "outsider"), "not in the opening committee")
    partials = [backend.partial_open(state, certificate, member) for member in state.context.members[:state.context.threshold]]
    rejects(lambda: backend.combine_open(partials[:1], certificate), "insufficient partial")
    rejects(lambda: backend.combine_open([partials[0]] * state.context.threshold, certificate), "insufficient partial")
    rejects(lambda: backend.combine_open(partials + [PartialOpening(certificate, "r3")], certificate), "has not been produced")
    rejects(lambda: backend.combine_open(partials + [PartialOpening(certificate, "outsider")], certificate), "not authorized")
    for field_name, value in (
        ("instance_id", "unknown"), ("model_version", "v1"), ("generation", 3),
        ("configuration", "C3"), ("dimension", 16), ("state_version", 0),
        ("accepted_update_ids", ("u0",)), ("committee_members", ("outsider",)), ("threshold", 1),
    ):
        altered = replace(certificate, **{field_name: value})
        rejects(lambda: backend.partial_open(state, altered, "r0"), "does not authorize")
        rejects(lambda: backend.combine_open(partials, altered), "current opening state")

    other = backend.open_state(contexts[2], 8, ("other-u0",), instance_id="other", model_version="v1")
    other_certificate = backend.authorize_open(other)
    other_partials = [backend.partial_open(other, other_certificate, member) for member in contexts[2].members[:2]]
    backend.combine_open(other_partials, other_certificate)
    assert other.phase == "committed" and state.phase == "opening"
    rejects(lambda: backend.combine_open(partials + other_partials, certificate), "certificate mismatch")
    opening = backend.combine_open(partials, certificate)
    assert state.phase == "committed" and state.state_bytes > 0
    assert opening.certificate == certificate
    assert opening.accepted_update_ids == ("u0", "u1", "u2", "u3")
    rejects(lambda: backend.combine_open(partials, certificate), "current opening state")
    rejects(lambda: backend.seal(state), "opened and erased")
    backend.erase(state)
    assert state.state_bytes == 0 and not state.accepted_update_ids
    assert state.open_certificate is None and not state.partial_openings
    sealed = backend.seal(state)
    assert state.phase == "sealed" and state.state_bytes == 0
    assert (sealed.instance_id, sealed.model_version) == ("sid", "v0")
    assert sealed.accepted_update_ids == opening.accepted_update_ids
    assert not backend.admit_update(state, "after-seal")
    rejects(lambda: backend.partial_open(state, certificate, "r0"), "does not authorize")
    rejects(lambda: backend.combine_open(partials, certificate), "current opening state")
    rejects(lambda: backend.export(state, 3), "only owned state")
    rejects(lambda: backend.open_state(contexts[2], 8, instance_id="sid", model_version="v1"), "already exists")
    print("PASS: two handoffs preserve prefix and dimension; one writer and one opening per instance")
    print("PASS: certificate binding, distinct member threshold, instance isolation, erase before seal")

    successful_orders = []
    for order in permutations(("confirm", "erase", "activate")):
        backend = AbstractThresholdBackend()
        source = backend.open_state(contexts[0], 8, ("u0",), instance_id="order", model_version="v0")
        record = backend.export(source, 1)
        successor, _ = backend.reshare(record, contexts[1])
        operations = {
            "confirm": lambda: backend.confirm(successor),
            "erase": lambda: backend.erase(source),
            "activate": lambda: backend.activate(successor, record),
        }
        accepted = True
        for operation in order:
            try:
                operations[operation]()
            except ValueError:
                accepted = False
            assert not (source.phase == "owned" and successor.phase == "owned")
            if source.phase == "erased":
                assert successor.phase in {"confirmed", "owned"}
        if accepted:
            successful_orders.append(order)
    assert successful_orders == [("confirm", "erase", "activate")]
    print("PASS: all six handoff event orders checked; only confirm -> erase -> activate completes")


if __name__ == "__main__":
    main()
