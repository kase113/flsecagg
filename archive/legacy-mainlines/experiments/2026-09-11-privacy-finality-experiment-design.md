# Privacy Finality Experiment Design

## Scope

The first experiment isolates the protocol claim rather than training accuracy:
whether an asynchronous secure-aggregation service prevents a retired coordinate
from becoming recoverable after long-lived mobile corruption and delayed messages.
The simulator uses abstract capability tokens. It does not implement group
operations, encryption, ACSS, or a federated-learning optimizer.

## Research Questions

1. Does a frontier-bound retirement barrier eliminate post-retirement opening paths?
2. What latency and communication cost is paid for that closure under delay,
   withholding, crash/recovery, and concurrent sessions?
3. How do unfenced repair, recovery-oriented VSS, and global epoch rekeying compare
   when sessions retire out of order?

## Simulator

`experiments/privacy_finality_sim.py` is a deterministic discrete-event simulator.
Each node holds typed abstract share capabilities. A message carries only a session,
generation, and frontier label; no secret value is represented. The scheduler samples
asynchronous delays and Byzantine withholding from a seeded pseudorandom generator.
The adversary corrupts one node at a time, so the measured attack is within any
instantaneous `f` bound while still accumulating state over time.
Each trial samples one delay/withholding scenario and reuses it across all baselines,
so protocol comparisons are paired by network schedule.

The simulator compares four abstract mechanisms:

- `fgsr`: rejects stale repair after the frontier and atomically erases retired
  share, helper, and endpoint capabilities;
- `unfenced`: accepts delayed repair against the old generation and retains old
  shares after the application declares retirement;
- `vssr`: models a recovery response as a durable old-generation opening edge;
- `epoch`: retains old state until a global epoch boundary, preserving finality but
  delaying out-of-order session completion.

These labels are mechanism baselines, not claims that the corresponding papers are
implemented line-for-line.

## Measurements

Each trial records privacy-finality violation, stale repair acceptance, finality
latency, messages, retained state, and the number of post-finality openings. The
attacker's pre-frontier exposure is `f` nodes and its post-frontier corruption is
sequential; a violation requires `q_rec` old-generation capabilities. Results are
written as CSV so plots and statistical aggregation remain separate from the
protocol model.

## Reproducibility

The command below runs all mechanisms with a fixed seed:

```text
python3 experiments/privacy_finality_sim.py --trials 200 --output experiments/results.csv --seed 7
```

The first artifact is a mechanism-level sanity check for the paper's attack and
latency claims. A later artifact may replace abstract tokens with measured ACSS and
private-channel implementations after the three conditional interfaces in 19.31
are proved.

The complete cross-device FL plan and open-source baseline matrix are maintained in
`experiments/EXPERIMENT_PLAN.md`. The simulator is an auxiliary attack harness, not
the primary end-to-end FL baseline.
