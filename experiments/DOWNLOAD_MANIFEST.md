# Download Manifest

This is the external-device acquisition list for the first experimental round.
Download into `experiments/upstream/` for protocol components and `datasets/` for
workload data.

Local status (2026-09-20): DyCAPS, Optimistic DPSS and Buffalo are cloned under
`experiments/upstream/`. Buffalo includes its FLSim copy. Current execution and
dependency status are in `REAL_COMPONENT_BRINGUP.md`; earlier experiment plans are
preserved in `archive/legacy-design/`.

Keep each upstream checkout immutable and record its commit in the result metadata.
Do not modify upstream repositories in place.

## Required projects

| Priority | Project | URL | Role |
|---|---|---|---|
| 1 | Buffalo | https://github.com/rtaiello/buffalo | Main buffered asynchronous secure-aggregation baseline |
| 1 | Flower secure-aggregation example | https://github.com/flwrlabs/flower/tree/main/examples/flower-secure-aggregation | SecAgg+ secure-aggregation control on CIFAR-10 |
| 1 | FLSim | https://github.com/facebookresearch/FLSim | FedBuff/asynchronous scheduling control; archived upstream |
| 1 | APSS | https://github.com/ISTA-SPiDerS/apss | Asynchronous proactive secret-sharing component benchmark |
| 1 | DyCAPS | https://github.com/DyCAPSTeam/DyCAPS | Dynamic committee and crash/cure component comparison |
| 1 | Optimistic DPSS | https://github.com/opDPSSTeam/Implementation | Verifiable sharing and successor recovery reference |
| 1 | NFSA with TLSS | https://github.com/pahjastia/NFSA-with-TLSS | State, masking, and communication-cost reference |
| 2 | Catalyst | https://github.com/bacox/Catalyst | Byzantine-robust FL control without secure aggregation |

## Theory candidates

These are cryptographic construction candidates, not additional primary FL baselines.
Download them only for protocol and proof-interface auditing:

| Priority | Project | URL | Role |
|---|---|---|---|
| 1 | hbACSS | https://github.com/tyurek/hbACSS | Univariate ACSS and transcript-simulation candidate |
| 2 | Haven++ / AMPC | https://github.com/nicolas3355/AMPC | Packed/bivariate ACSS reference; deferred from the first FGSR theorem |

Suggested checkout commands:

```bash
git clone https://github.com/rtaiello/buffalo experiments/upstream/buffalo
git clone https://github.com/flwrlabs/flower experiments/upstream/flower
git clone https://github.com/facebookresearch/FLSim experiments/upstream/flsim
git clone https://github.com/ISTA-SPiDerS/apss experiments/upstream/apss
git clone https://github.com/DyCAPSTeam/DyCAPS experiments/upstream/dycaps
git clone https://github.com/pahjastia/NFSA-with-TLSS experiments/upstream/nfsa-with-tlss
git clone https://github.com/bacox/Catalyst experiments/upstream/catalyst
git clone https://github.com/opDPSSTeam/Implementation experiments/upstream/optimistic-dpss
```

The PPFA-BAA artifact is optional and conditional:

```text
https://anonymous.4open.science/r/privacy-preserving-federated-averaging-with-byzantine-aggregators-in-asynchronous-networks-4E25/
```

It returned `401` during the local audit. Download it only if the artifact becomes
accessible and preserve its supplied scripts and commit separately.

## Required datasets

| Priority | Dataset | URL or source | Role |
|---|---|---|---|
| 1 | CIFAR-10 | https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz | Common first-round FL workload |
| 1 | FEMNIST | https://github.com/TalwalkarLab/leaf | Non-IID and client-heterogeneity workload; use `data/femnist` |
| 1 | MNIST | `torchvision.datasets.MNIST(download=True)` | Small-scale Catalyst/control workload |
| 2 | WikiText-2 | https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip | Optional text FL workload for Catalyst |
| 2 | LEAF CelebA | https://github.com/TalwalkarLab/leaf | Buffalo-native reproduction only |
| 2 | LEAF Sent140 | https://github.com/TalwalkarLab/leaf | Buffalo-native reproduction only |

Do not download `REPLACE-BG` yet. Its access and license need to be verified before
use; it is not required for the first common workload.

## Models and checkpoints

No pretrained model or checkpoint is required. Use identical random initialization
and training configuration across primary rows:

- CIFAR-10: a small CNN with a fixed parameter count.
- FEMNIST: LeNet-style CNN.
- MNIST: the two-convolution/two-fully-connected CNN used by Catalyst where useful.
- WikiText-2: embedding plus LSTM plus fully connected output, only for the optional
  text workload.

The Buffalo CelebA/Sent140/REPLACE-BG architectures are needed only for exact native
reproduction, not for the first FGSR comparison.

## Deferred downloads

Do not spend time on these in the first round:

- pretrained weights;
- `REPLACE-BG`;
- PPFA-BAA until its artifact access is confirmed;
- additional datasets beyond CIFAR-10, FEMNIST, and MNIST.
