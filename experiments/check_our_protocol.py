#!/usr/bin/env python3
"""Check the paper's aggregation rules against exact numerical trajectories."""

import argparse
import json
from dataclasses import replace
from fractions import Fraction
from itertools import permutations
from pathlib import Path

from reconfigurable_async_fl import AggregationProtocol, Service


def protocol():
    return AggregationProtocol(
        services=(
            Service("A", ("p0", "p1", "p2", "p3"), 1, 2),
            Service("B", ("q0", "q1", "q2", "q3"), 1, 2),
            Service("C", ("r0", "r1", "r2", "r3"), 1, 2),
        ),
        initial_service="A", model=(0, 0), buffer_size=3, learning_rate=1,
    )


def event(system, operation, expected="accepted", **arguments):
    outcome = system.dispatch({"operation": operation, **arguments})
    assert outcome["status"] == expected, outcome
    return outcome


def update(system, sid, client, values=(1, -1), weight=1, service="A",
           expected="accepted", base_version=0, update_id=None):
    return event(system, "admit", expected, sid=sid, client=client,
                 update_id=update_id or f"{sid}:{client}", values=list(values),
                 weight=weight, service=service, base_version=base_version)


def ready(system, sid, service="A"):
    event(system, "start", sid=sid, base_version=0, service=service)
    for client in ("c0", "c1", "c2"):
        update(system, sid, client, service=service)


def opening(system, sid, members):
    for member in members:
        event(system, "contribute", sid=sid, member=member)
    event(system, "decode", sid=sid)


def dual_instance():
    system = protocol()
    event(system, "start", sid="active", base_version=0, service="A")
    update(system, "active", "c0", (1, 2), weight=1)
    update(system, "active", "c1", (4, -1), weight=2)
    ready(system, "opening")
    certificate = system.instances["opening"].certificate
    event(system, "change_service", service="B")
    assert system.instances["opening"].transfer is None
    assert system.instances["opening"].certificate == certificate
    update(system, "active", "late", (-2, -1), service="B", expected="pending")
    update(system, "active", "late", (-2, -1), expected="rejected")

    ready(system, "new", service="B")
    opening(system, "new", ("q0", "q1"))
    event(system, "commit", sid="new", service="B")
    event(system, "apply_result", sid="new")
    assert system.instances["active"].transfer is not None

    event(system, "activate", "pending", sid="active", generation=1)
    event(system, "retire", "pending", sid="active", generation=0)
    event(system, "set_online", member="q0", online=False)
    event(system, "set_online", member="q1", online=False)
    event(system, "install", "pending", sid="active", generation=1)
    event(system, "set_online", member="q1", online=True)
    event(system, "install", sid="active", generation=1)
    event(system, "install", "duplicate", sid="active", generation=1)
    update(system, "active", "late", (-2, -1), service="B", expected="pending")
    event(system, "retire", sid="active", generation=0)
    event(system, "activate", sid="active", generation=1)
    update(system, "active", "late", (-2, -1), service="B")
    update(system, "active", "late", (-2, -1), service="B", expected="duplicate")
    event(system, "contribute", "pending", sid="active", member="q0")
    event(system, "set_online", member="q0", online=True)
    event(system, "contribute", sid="active", member="q0")
    event(system, "contribute", "duplicate", sid="active", member="q0")
    event(system, "decode", "pending", sid="active")
    event(system, "contribute", sid="active", member="q1")
    event(system, "set_online", member="q0", online=False)
    event(system, "set_online", member="q1", online=False)
    event(system, "decode", sid="active")
    assert system.instances["active"].result == (Fraction(7, 4), Fraction(-1, 4))
    assert "active" not in system.commits
    event(system, "commit", "rejected", sid="active", service="A")
    event(system, "commit", "pending", sid="active", service="B")
    event(system, "set_online", member="q0", online=True)
    event(system, "commit", sid="active", service="B")

    event(system, "contribute", "rejected", sid="opening", member="q0")
    opening(system, "opening", ("p0", "p1"))
    event(system, "retire", sid="opening", generation=0)
    event(system, "commit", sid="opening", service="B")
    event(system, "apply_result", "pending", sid="opening")
    event(system, "apply_result", sid="active")
    event(system, "apply_result", sid="opening")
    assert system.model == (Fraction(53, 24), Fraction(-35, 24))
    event(system, "commit", "duplicate", sid="active", service="B")
    event(system, "apply_result", "duplicate", sid="active")
    event(system, "seal", "pending", sid="active")
    event(system, "retire", sid="active", generation=1)
    event(system, "seal", sid="active")
    event(system, "seal", sid="opening")
    fixed = system.commits["active"]
    event(system, "change_service", service="C")
    assert system.commits["active"] == fixed
    event(system, "commit", "duplicate", sid="active", service="C")
    update(system, "active", "extra", service="C", expected="rejected")
    event(system, "start", "rejected", sid="active", base_version=0, service="C")
    event(system, "start", sid="versioned", base_version=3, service="C")
    update(system, "versioned", "c0", base_version=3, service="C")
    return system


def handoff_orders():
    successes = []
    for order in permutations(("install", "retire", "activate")):
        system = protocol()
        event(system, "start", sid="sid", base_version=0, service="A")
        update(system, "sid", "c0")
        event(system, "change_service", service="B")
        statuses = []
        for operation in order:
            statuses.append(system.dispatch({"operation": operation, "sid": "sid",
                                            "generation": 0 if operation == "retire" else 1})["status"])
        if statuses == ["accepted"] * 3:
            successes.append(order)
    assert successes == [("install", "retire", "activate")]


def cumulative_exposure():
    system = protocol()
    event(system, "start", sid="sid", base_version=0, service="A")
    update(system, "sid", "c0")
    event(system, "corrupt", member="p0")
    event(system, "release", member="p0")
    event(system, "corrupt", member="p1")
    assert system.exposures[("sid", 0)].exposed == {"p0", "p1"}
    assert system.exposure_violations == {("sid", 0)}

    system = protocol()
    event(system, "start", sid="sid", base_version=0, service="A")
    event(system, "corrupt", member="p0")
    event(system, "release", member="p0")
    for service, generation, member in (("B", 1, "q0"), ("C", 2, "r0")):
        event(system, "change_service", service=service)
        event(system, "install", sid="sid", generation=generation)
        event(system, "retire", sid="sid", generation=generation - 1)
        event(system, "activate", sid="sid", generation=generation)
        event(system, "retire", "rejected", sid="sid", generation=generation - 1)
        event(system, "corrupt", member=member)
        event(system, "release", member=member)
    event(system, "corrupt", member="p1")
    assert system.exposures[("sid", 0)].exposed == {"p0"}
    assert not system.exposure_violations

    system = protocol()
    system.services["B"] = replace(system.services["B"], members=("p0", "q1", "q2", "q3"))
    event(system, "start", sid="overlap", base_version=0, service="A")
    event(system, "change_service", service="B")
    event(system, "install", sid="overlap", generation=1)
    event(system, "corrupt", member="p0")
    assert all(period.exposed == {"p0"} for period in system.exposures.values())


def admission_binding():
    system = protocol()
    event(system, "start", sid="sid", base_version=0, service="A")
    update(system, "sid", "c0")
    update(system, "sid", "c0", weight=2, expected="rejected")
    update(system, "sid", "c0", update_id="another", expected="rejected")
    update(system, "sid", "c1", (1,), expected="rejected")
    update(system, "sid", "c1", weight=0, expected="rejected")
    update(system, "sid", "c1", base_version=1, expected="rejected")
    event(system, "start", sid="other", base_version=0, service="A")
    update(system, "other", "c0", update_id="sid:c0", expected="rejected")
    assert len(system.instances["sid"].updates) == 1
    event(system, "change_service", service="B")
    event(system, "change_service", "pending", service="C")
    assert system.current_service == "B"


def corrupted_installation():
    system = protocol()
    event(system, "corrupt", member="p0")
    event(system, "start", sid="sid", base_version=0, service="A")
    assert system.exposures[("sid", 0)].exposed == {"p0"}
    event(system, "change_service", service="B")
    event(system, "corrupt", member="q0")
    event(system, "install", sid="sid", generation=1)
    assert system.exposures[("sid", 1)].exposed == {"q0"}
    event(system, "release", member="p0")
    event(system, "corrupt", member="p1")
    assert system.exposure_violations == {("sid", 0)}
    assert not system.exposures[("sid", 0)].retired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("experiments/results/our-protocol"))
    args = parser.parse_args()
    system = dual_instance()
    handoff_orders()
    cumulative_exposure()
    admission_binding()
    corrupted_installation()
    replayed = protocol()
    for record in json.loads(json.dumps(system.events)):
        assert replayed.dispatch(record["event"]) == record
    assert replayed.model == system.model
    assert replayed.commits == system.commits
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "implementation": "ordered-event numerical protocol; abstract threshold backend",
        "checks": ["dual instance continuity", "independent new training", "weighted aggregate",
                   "commit and apply separation", "six handoff orders", "cumulative exposure",
                   "repeated disjoint and overlapping membership", "admission binding", "event replay"],
        "active_aggregate": [str(value) for value in system.instances["active"].result],
        "final_model": [str(value) for value in system.model],
        "application_order": system.applied,
        "events_checked": len(system.events),
    }
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "events.json").write_text(json.dumps(system.events, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
