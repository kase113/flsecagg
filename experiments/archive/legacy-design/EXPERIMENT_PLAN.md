# Reconfigurable Asynchronous FL Experiment Plan

Detailed component, baseline, adapter, and execution construction is tracked in
`experiments/EXPERIMENT_BUILD.md`.

## 1. Experimental Claim

The experiment tests one system claim:

> Under asynchronous client arrivals and committee churn, training continues
> through configuration changes while finalized windows retain the same result
> and later rolling corruption cannot reopen them through state transfer.

The FL run measures continuity, utility, and systems cost. The attack harness
provides a focused check for stale-state acceptance and duplicate window
ownership. It is a systems trace, not a cryptographic security proof.

## 2. Baseline Matrix

### Primary end-to-end baselines

| ID | Work and open artifact | Role | Comparable dimensions | Excluded claims |
|---|---|---|---|---|
| `P0` | **Selective-finality** (this work) | Proposed dynamic protocol | async aggregation, per-window finalization, selective handoff, committee churn | cryptographic details are evaluated through the same aggregation interface |
| `B1` | [Buffalo](https://github.com/rtaiello/buffalo) | Closest buffered asynchronous secure-aggregation baseline | asynchronous buffering, client update protection, aggregate service cost | no `PF_sid` or long-lived repair-closure claim |
| `B1a` | [Setup Once, Secure Always](https://github.com/bytest02/scatesfl) | Dynamic-user secure-aggregation baseline | dynamic users, single setup, user dropout | intermediate servers remain stable; no dynamic committee or `PF_sid` claim |
| `B2` | [Privacy-Preserving Federated Averaging with Byzantine Aggregators in Asynchronous Networks](https://anonymous.4open.science/r/privacy-preserving-federated-averaging-with-byzantine-aggregators-in-asynchronous-networks-4E25/) | Closest asynchronous Byzantine-FL artifact | asynchronous FL, malicious aggregators, aggregate/privacy evaluation | paper-listed open artifact; access returned `401` during this audit, so verify availability before scheduling; no `PF_sid` claim |
| `B3` | [Flower SecAgg+ example](https://github.com/flwrlabs/flower/tree/main/examples/flower-secure-aggregation) | Standard secure-aggregation FL control | real FL workload, secure aggregation, model accuracy | SecAgg+ is not an asynchronous mobile-corruption baseline |
| `B4` | [FLSim](https://github.com/facebookresearch/FLSim) FedBuff/async components | Scheduling and non-cryptographic throughput control | client heterogeneity, buffering, asynchronous optimizer behavior | repository is archived; no security comparison |
| `B5` | [Catalyst](https://github.com/bacox/Catalyst) | Byzantine-robust FL control without secure aggregation | asynchronous training, malicious updates, model utility | no secure-aggregation or privacy-finality claim |
| `B6` | `Full-transfer` | Dynamic handoff control | committee churn, migration of every active window | derived baseline implemented on the common framework |
| `B7` | `Periodic-rekey` | Periodic transition control | committee churn, global re-establishment before new windows | derived baseline implemented on the common framework |

`B1` is the unconditional main protocol comparison. `B1a` is the dynamic-user
comparison and does not count as a dynamic-committee implementation. `B2` joins the main comparison
only after its artifact is accessible and its supplied run is reproduced; otherwise
the first end-to-end table uses `B1`, `B3`, and `B4`, with the PPFA-BAA result reported
separately when recovered. `B3` controls for the cost of secure aggregation in a
conventional FL workflow. `B4` controls for the cost of asynchrony without
cryptographic state protection. `B5` controls for Byzantine-update robustness when
privacy is removed. Results may share an end-to-end table only when the same client
workload and update encoding are used.

### Component and state baselines

| ID | Open artifact | Use | Why it is not a primary FL row |
|---|---|---|---|
| `C1` | [APSS](https://github.com/ISTA-SPiDerS/apss) | asynchronous state-transfer latency | no FL aggregation API; service and failure assumptions differ from this work |
| `C2` | [DyCAPS](https://github.com/DyCAPSTeam/DyCAPS) | dynamic-committee handoff and crash/cure systems comparison | handoff and epoch semantics differ from per-window ownership and finalization |
| `C3` | [NFSA with TLSS](https://github.com/pahjastia/NFSA-with-TLSS) | two-layer sharing, masking, vector and state-cost comparison | single-threaded simulation and different server/corruption assumptions |
| `C4` | [Google Federated Compute](https://github.com/google-parfait/federated-compute) secure aggregation code | production-oriented secure-aggregation implementation reference | not a drop-in research baseline for this asynchronous committee model |

`C1`--`C4` belong in component microbenchmarks and an assumption matrix, not in
the primary FL accuracy and systems comparison. VSSR remains an algorithmic recovery
baseline in the paper and may be implemented in the attack harness; no verified
official repository is required for the first end-to-end round.

## 3. Execution Layers

### Layer A: protocol attack harness

Use `privacy_finality_sim.py` to validate the fixed-window boundary, then use
`reconfigurable_fl_sim.py` with the event-trace format in
`reconfigurable-async-fl-system-spec.md` for committee churn and multiple windows.
Both simulators use abstract records rather than model plaintexts. Run all mechanisms
on the same trace. Record:

- reopened or duplicated windows;
- stale handoff acceptance;
- accepted-client-set agreement;
- window completion and model-version progress;
- handoff, recovery, and retained-record cost.

This layer answers whether stale messages and old window records can change a
finalized result, and whether active windows continue across configuration changes
under rolling corruption. It must not be reported as a cryptographic implementation
benchmark.

### Layer B: cryptographic component benchmark

Measure `C1` APSS and `C2` DyCAPS on their native protocol APIs when their code is
available. Measure the proposed window service on the same host. Report separately:

- setup and resharing time;
- per-recipient and aggregate communication;
- verification time;
- repair or handoff latency;
- live-state and retired-state bytes;
- completion rate under withholding and crash/restart.

Use native parameters first. Record committee size, fault threshold, implementation
version, commit, and branch in every result file.

### Layer C: end-to-end federated learning

Use one model workload and one canonical adapter contract for every primary row. The
first dynamic-system port is FLSim because its asynchronous trainer produces client
training events and staleness without forcing the dynamic service into a synchronous
round interface. Buffalo is the
primary asynchronous secure-aggregation comparison. Flower SecAgg+ supplies the
conventional secure-aggregation control, and the PPFA-BAA artifact should be run using
its supplied scripts before adapting its interface. The adapter boundary is the
aggregation service, not the local optimizer. See
`reconfigurable-async-fl-adapter-spec.md`.

For each window, log the client update identifier, session identifier, accepted set,
owner configuration, window status, handoff count, aggregation completion time, and
model version. The server must retain an audit record sufficient to replay the attack
schedule without retaining client plaintexts.

## 4. Workloads and Parameters

### Common workload

- CIFAR-10 first; FEMNIST or another naturally heterogeneous workload second;
- fixed model, local epochs, batch size, optimizer, quantization, and client data split;
- same client population and update dimension across primary rows;
- 10 independent seeds for performance measurements, one deterministic adversarial
  schedule per security scenario;
- report host CPU, RAM, GPU, Python/Rust/Go versions, dependency lockfiles, and commit
  hashes.

### Configuration settings

Use several configuration sequences with explicit service availability conditions:

| sequence | initial nodes | transition pattern | active nodes after transition |
|---|---:|---|---:|
| `C1` | 8 | one join and one leave | 8 |
| `C2` | 8 | one crash and recovery | 8 |
| `C3` | 8 | two consecutive replacements | 8 |

Record the native settings for Buffalo, APSS, and DyCAPS separately. The dynamic
service report states the instantaneous corruption bound, leaving quota, configuration
overlap, and number of active windows for every sequence.

### Network and failure scenarios

| Scenario | Description | Purpose |
|---|---|---|
| `S0` | no failures, bounded heterogeneous delay | baseline utility and cost |
| `S1` | slow-tail delay and out-of-order delivery | asynchronous finality latency |
| `S2` | client dropout and committee withholding | liveness/completion |
| `S3` | crash, restart, and sequential cure/corruption | state persistence and exposure |
| `S4` | repair message delivered after `PF_sid` | stale transcript/no-resurrection |
| `S5` | concurrent sessions retire in different orders | per-session frontier isolation |
| `S6` | rolling corruption before and during handoff | state exposure and ownership continuity |
| `S7` | join/leave and committee handoff during active windows | primary dynamic-member scenario |
| `S8` | two or more configuration changes with concurrent windows | per-window ownership and recovery |
| `S9` | rolling corruption after finalization with delayed old messages | finalized-result stability |

`S4`--`S9` are the paper's core scenarios. `S0`--`S3` establish the common
training and failure behavior used to interpret them.

## 5. Metrics

### Window and training correctness

- reopened or duplicated window rate under `S4`--`S9`;
- number of accepted stale handoff messages;
- accepted-client-set and model-version agreement;
- window completion rate and explicit abandonment rate;
- model-version progress and ownership monotonicity.

An empirical zero failure rate means that the tested schedules produced no failure. It
does not replace the system argument or the assumptions of the selected protection
plugin.

### Systems cost

- p50/p95 aggregation and retirement latency;
- successful aggregates per unit time;
- client upload/download and committee-to-committee bytes;
- CPU time for sharing, verification, repair, and aggregation;
- peak and persistent state bytes per committee member;
- fraction of delayed sessions that block completion.

### ML utility

- test accuracy/loss versus completed aggregates, not wall-clock rounds alone;
- staleness distribution of accepted updates;
- client inclusion fairness and dropout rate;
- final model quality under the same Byzantine/update attack.

## 6. Required Plots

1. reopened-window rate versus delayed-message fraction and corruption schedule;
2. p50/p95 finality latency versus slow-client fraction;
3. persistent state bytes versus number of completed windows and transitions;
4. handoff communication versus committee size and active-window count;
5. accuracy/loss versus completed aggregates for `P0`, `B1`, `B2`, `B3`, and `B4`;
6. throughput versus concurrent windows;
7. a continuity/cost plot separating periodic transition from selective handoff;
8. window completion and model progress versus committee churn;
9. rejected late messages and retained records versus the number of transitions.

## 7. Execution Order on the Other Device

1. Clone and record commits for `B1`, `B1a`--`B5`, `C1`--`C4`; do not modify upstream code.
2. Reproduce each upstream README example or supplied benchmark and save raw logs.
3. Run Layer A with both simulators and verify paired schedules.
   Generate a multi-window trace with:
   `python3 experiments/generate_reconfigurable_trace.py --transitions 2 --windows-per-configuration 4 --output experiments/reconfigurable_trace.csv`.
   The dynamic runner reads a trace with:
   `python3 experiments/reconfigurable_fl_sim.py --trace experiments/reconfigurable_trace.csv --output experiments/reconfigurable_results.csv`.
4. Replay the generated `corrupt`, `release`, and `recover_state` events, keeping the
   node-level action separate from cryptographic opening operations.
5. Port only the aggregation-service interface into the chosen FL framework.
6. Run `S0`--`S3` for common utility and cost; then run `S4`--`S6` with the attack harness.
7. Run `S7`--`S9` as primary dynamic-member scenarios after the common event trace is validated.
8. Replace abstract update records with the chosen secure-aggregation implementation only after the window behavior and failure measurements are stable.

Use this artifact layout on the execution device:

```text
artifacts/<baseline>/<commit>/       immutable upstream checkout
results/raw/<baseline>/<scenario>/<seed>/
results/derived/                     tables and plots made from raw logs
```

Every record must include the upstream commit, local patch identifier (if an adapter
is needed), dataset/model configuration, host, dependency versions, and random seed.
Adapters belong in a separate checkout or patch file; upstream results remain
reproducible without them.

The first publishable comparison is Selective-finality versus Buffalo under the same
asynchronous FL workload and committee-change trace, with Flower SecAgg+ and FLSim
as controls. Catalyst is a separate Byzantine-utility control, not a privacy
competitor. `Full-transfer` and `Periodic-rekey` isolate the cost of the two main
alternative transition policies. PPFA-BAA joins when its
artifact is reproducible. APSS and DyCAPS support the component-cost and
state-transition analysis; they are not presented as direct FL competitors.

## 8. Artifact Status

Repository locations checked through the public GitHub API as of 2026-09-11:

- Buffalo: `https://github.com/rtaiello/buffalo`;
- APSS: `https://github.com/ISTA-SPiDerS/apss`;
- DyCAPS: `https://github.com/DyCAPSTeam/DyCAPS`;
- NFSA: `https://github.com/pahjastia/NFSA-with-TLSS`;
- Flower: `https://github.com/flwrlabs/flower/tree/main/examples/flower-secure-aggregation`;
- Google Federated Compute: `https://github.com/google-parfait/federated-compute`;
- PPFA-BAA artifact: the anonymous 4open.science URL listed in `B2`; the URL is
  taken from the paper's artifact section and requires a manual access check before
  execution.

Repository availability does not imply identical license, threat model, or reproducible
hardware. Those fields must be checked and recorded before using a result in a paper.
