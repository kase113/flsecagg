# Privacy Finality Manuscript Structure

## Editorial Decision

The paper is an OSDI-oriented asynchronous federated learning systems paper.
Its central object is a long-running asynchronous FL service that keeps making
progress through delayed clients, committee failures, and node recovery while
preserving the privacy of updates that have already contributed to training.
The security guarantee is an important service requirement, rather than the
paper's entire organizing principle. The main question is:

> After an asynchronous FL aggregate is released, when is every constituent
> client update permanently protected against future mobile corruption and
> recovery?

The paper should be written around this FL service question. The design and
implementation explain how the service admits updates, releases aggregates,
seals completed windows, and repairs committee state. The security model and
proof establish the guarantee under the stated failure and corruption model.
Cryptographic interfaces remain subordinate implementation choices.

The full main-paper draft is intentionally deferred. The current writing artifact
is the revised introduction-and-solution plan at the beginning of
`privacy-finality-paper-idea-draft.md`; this file is the structural authority,
while the longer theorem document remains the proof archive.

The security results retain a clear mapping to the technical archive: the
closure-aware retirement criterion corresponds to Theorem 44, the
recovery-state localization separation to Proposition 22, and the conditional
protocol realization to Theorem 42. In the main paper these results support one
end-to-end FL guarantee; they are not presented as three independent
cryptographic contributions.

## OSDI Positioning

The paper presents a long-running asynchronous FL service and evaluates the
cost of adding privacy finality to its normal training path. The system section
must show how the model server, clients, aggregation committee, buffer, and
recovery path cooperate in one training workflow. The implementation story
should use an existing asynchronous SA/ACS building block wherever possible;
the new design contribution is the way an FL window is admitted, released,
sealed, and repaired without reopening an earlier update.

The evaluation must connect security actions to FL behavior. It should report
client inclusion and staleness, model-update and sealing latency, recovery
latency after crash/cure, communication and persistent-state cost, and model
quality. A fault schedule with delayed repair messages and later committee
exposure is the central systems experiment because it exercises the same path
captured by the theory.

## Main Claims

The main text has a strict three-claim budget.

### Claim 1: A complete asynchronous FL service path

The design connects buffered client admission, descriptor agreement, aggregate
release, model-version advancement, window sealing, and committee repair. It
defines what happens to late updates, duplicate submissions, crashes during
sealing, and repair messages that cross a sealing boundary.

### Claim 2: Privacy finality as an operational service guarantee

The service exposes a released model update only after fixing its contributing
clients and weights. It then seals the window before recovery can reuse its
private state. The security section defines the recovery-closure condition and
proves that future mobile corruption and repair preserve this guarantee.

### Claim 3: Practical cost and training behavior

The evaluation measures client inclusion, update staleness, model-update
latency, sealing delay, crash recovery, communication, persistent state, and
model quality. It compares the privacy-finality design with asynchronous secure
aggregation paths that lack sealing closure or use ordinary recovery.

## Main-Text Order

1. **Introduction.** Start with a buffered asynchronous FL service in which
   clients arrive at different times, aggregates advance the model, and
   committee failures occur during continued training. Use delayed repair as
   the motivating failure scenario.
2. **Service requirements and model.** Define client submissions, buffering,
   accepted descriptors, weights, dropped clients, model versions, committee
   state, crashes, recovery, and the privacy boundary of a completed window.
3. **System design.** Describe the end-to-end workflow: admission, agreement,
   aggregate release, sealing, late-message handling, and current-state repair.
   Explain the data structures and persistent records needed for restart.
4. **Implementation.** Describe the integration with the asynchronous SA/ACS
   substrate, the model-server interface, committee communication, storage,
   failure handling, and tunable parameters. Keep cryptographic details at the
   level needed to reproduce the service.
5. **Security model and guarantee.** Define privacy finality and recovery
   closure, present the delayed-repair attack, and state one conditional
   theorem covering correctness, liveness, and privacy. Move detailed hybrids
   and primitive-specific obligations to the appendix.
6. **FL evaluation.** Measure inclusion, staleness, model-update latency,
   sealing delay, recovery delay, communication, persistent state, and model
   quality under realistic arrival and failure schedules.
7. **Related work and scope.** Compare asynchronous SA, buffered FL, VSS/DPSS,
   threshold encryption, and forward security using the same service model.
   State the fixed-committee result and the boundary for dynamic membership.

The system model uses one canonical trace throughout the paper: a repair message
is sent before model output, arrives after sealing, and is followed by mobile
exposure of committee state. The baseline installs the delayed repair result;
the proposed path absorbs the frontier before repair and produces only current
live state. This trace is the common input to the recovery-closure theorem, the
implementation conditions, and the fault-schedule evaluation.

The first parameter point is deliberately tight. With `n=3f+2`,
`q_dec=q_rec=2f+1`, and a per-window pre-sealing exposure budget `b=f`, privacy
finality requires `|A_sid|>=n-f=2f+2`; target-excluded repair separately needs
`2f+1` correct helpers. The paper must keep these two quorum roles distinct.
The adversary may move across windows; `b` bounds retained old capabilities for the
target window and is not a global corruption or decryption-query bound.

## What Moves Out of the Main Narrative

The following material is technical support, not independent top-level
contribution:

- `AOR-1`--`AOR-5` become one recovery-closure definition plus supporting
  lemmas.
- `Joint-AO^mob` becomes the aggregate-only security assumption used by the
  end-to-end theorem.
- `F_PF^mob` becomes the ideal functionality used to state the composition
  result, not a second paper narrative.
- `PVOD`, `CSO-VE`, `KeyOrigin`, `PECC`, and the YLH20 hybrid become one
  cryptographic-instantiation section and an appendix. They are introduced
  only after the FL theorem explains why opaque delivery and late exposure are
  needed.
- Individual hybrid transitions, proof metadata, and advantage bookkeeping
  move to the appendix unless a transition exposes a new FL-specific boundary.
- Dynamic committee handoff remains a closure-preserving extension, not a
  second protocol in the first paper.

## Required FL-Specific Evidence

The paper cannot rely on cryptographic notation alone. The protocol section
must answer these questions directly:

- Which clients are in the accepted asynchronous buffer and which are dropped?
- When does an update become individually unrecoverable?
- How does a late update or late recovery message affect the training state?
- What work is lost when a crash occurs during retirement or repair?
- What is the effect of privacy-finality barriers on staleness and model
  utility?

The baseline comparison should include a conventional asynchronous secure
aggregation design, a buffered asynchronous design, and a refresh/recovery
design without retirement closure. The decisive comparison is not only model
accuracy; it is whether each design survives the same delayed-message and
future-corruption schedule.

## Proof Budget

The main text should contain at most:

1. one concise definition of privacy finality and its recovery-closure test;
2. one delayed-repair separation result explaining the design requirement; and
3. one conditional end-to-end theorem with correctness, liveness, and privacy.

The system design and implementation sections carry the main paper narrative.
All other lemmas should be visibly subordinate to the end-to-end guarantee. A
proof that does not establish a new FL service consequence belongs in the
appendix.

## Positioning Test

The paper is ready for security/FL venues only when a reader can understand
the problem, attack, and practical consequence before seeing `PVOD` or
`CSO-VE`. If the main contribution can be summarized as a new late-key-opening
construction after removing the FL section, the paper has reverted to a
cryptography-paper framing and requires another restructure.
