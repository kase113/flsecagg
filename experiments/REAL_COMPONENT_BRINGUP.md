# 真实组件接入记录

更新日期：2026-09-20。

## 当前目标

已接通活动聚合实例的第一条真实组件路径：

```text
两个客户端的系数密文 -> 旧组生成 Prepare 与 ShareReduce
    -> 保存真实消息 -> 旧组进程结束
    -> 独立后继进程验证输入 -> ProactivizeAndShareDist
    -> 第三个客户端的系数密文 -> 用新份额开启原实例聚合
```

本轮复用原版 VSS、KZG、Prepare、ShareReduce、刷新、MVBA 和份额分发，使用 BLS12-381 G1 系数密文检查交接前后同一个聚合。每组四个节点在同一进程内用通道通信；旧组与新组分别运行，跨组传递按后继加密并由源签名绑定的序列化消息。训练模型、RLWE 向量保护与可验证部分开启随后接入。

## 已拉取组件

| 组件 | 本地路径 | 上游提交 | 当前用途 |
|---|---|---|---|
| DyCAPS | `experiments/upstream/dycaps` | `09d2262` | 参考 `ShareReduce`、KZG 证明和委员会交接 |
| Optimistic DPSS | `experiments/upstream/optimistic-dpss` | `e86b348` | 参考可验证分享、后继恢复和乐观路径 |
| Buffalo | `experiments/upstream/buffalo` | `3a8dfbf` | RLWE 保护、训练代码与主要 FL 基线；仓库自带 FLSim 副本 |

三个上游仓库保持原样。`dycaps_handoff_test.go` 保存在本项目实验目录，`run_dycaps_handoff.py` 通过 Go overlay 将它加入上游测试包，只在编译视图中访问原实现。测试二进制、交接输入放入临时目录，运行完成自动移除；结果目录只保存日志、公开指标和版本记录。

## 已确认的接口事实

DyCAPS 的 `ShareReduceSend` 会为每个后继生成求值、承诺和见证，并在发送后记录旧节点的结束时间。后继通过 KZG 检查求值和见证，再按相同承诺收集足够输入。因此，旧节点提前退出的最小条件是：

1. 它已经生成本次交接所需的全部后继输入；
2. 输入已经由可继续提供的节点保存，或底层通信协议已经给出等价的可取得性保证；
3. 后继仍可完成原协议要求的验证、刷新和份额安装。

仅有“发送函数返回”无法推出第二项。本文的保存确认必须对应真实字节批次，而不是发送事件。

Optimistic DPSS 的仓库提供 Merkle 版和 Pointproofs 版路径。Pointproofs 需要额外的本地原生库；首轮接入先使用可编译的 Merkle 版，记录其通信和恢复路径，再单独评估 Pointproofs 的依赖。

## 当前运行结果

### 跨进程真实交接

从项目根目录运行：

```bash
python3 experiments/run_dycaps_handoff.py
```

本机 Go 1.26.2，脚本构建的包沿用上游 Go 1.18 语言版本。结果在 `experiments/results/dycaps-handoff/`，其中 `environment.json` 记录上游完整提交和编译环境。每次运行覆盖本次四个阶段的结果；任一阶段失败，脚本返回非零状态。

| 阶段 | 检查 | 实际结果 |
|---|---|---|
| sender | 原版 VSS 后生成并保存四对四的 Prepare、Reduce 消息 | 32 条序列化消息，生成进程结束 |
| successor | 后继独立完成真实刷新和分发 | 四份新份额均改变，实例公钥保持 |
| quorum | 每个接收者只获得两个不同旧节点的输入 | 完成真实交接；八份 Reduce 证明通过 |
| recover | 一个接收者先仅有一份 Reduce 输入，100 ms 后补齐保存的消息 | 等待期间未完成，补齐后完成交接 |

正常与延迟路径各验证 16 份真实 Reduce 证明，并对每份求值加一，检查原 KZG 验证器拒绝该篡改。四个新成员的全部六种两人组合均保持原公钥，并恢复同一系数和 $[3,0,-4]$。开启门槛为原组件的 $f+1=2$；原一致及签名流程采用 $2f+1=3$。FL 缓冲人数另取三，这三种人数分别记录。

加密交接路径运行 `python3 experiments/run_dycaps_handoff.py --output experiments/results/dycaps-handoff-saver`。发送者为四个后继各保存八个真实 Prepare/ShareReduce 封装，共 32 个按后继区分的密文；保存者 A 写入密文和公开元数据，保存者 B 复制同一批次，A 随后退出并删除自己的保存库。后继私钥始终由后继侧单独持有。后继先验证源签名，再用自己的接收私钥解密并交给原版接收函数。正常路径打开 32 个封装，quorum 路径打开 16 个，recover 路径在延迟 100 ms 后从 B 补开剩余封装，最终仍打开 32 个，三条路径均恢复 $[3,0,-4]$。

前两个客户端的系数为 $(1,2,-3)$ 与 $(4,-1,1)$，旧组退出前保存它们的密文和；后继刷新完成后才保护并加入第三个向量 $(-2,-1,-2)$。检查在 $[-48,48]$ 中实际解码聚合系数。首次接入发现原库字符串解析按绝对值导入负数，适配代码现用有限域减法编码负数，正、负及零聚合均纳入检查。

阶段时间用于定位本地计算与等待，包含检查代码开销，尚不用于论文性能对比。100 ms 是注入的有限观察区间；异步活性仍由协议条件分析。

### DyCAPS

运行：

```bash
cd experiments/upstream/dycaps
go test ./internal/bls ./internal/polycommit ./internal/polyring
```

这些基础密码学和多项式组件通过。完整 `go test ./...` 中，`cmd/DyCAPs/main.go` 的四个格式化调用缺少参数，触发 `go vet` 错误；原生网络测试还共用固定端口。第一次全包执行未完成，已停止该次运行。本文新增检查单独编译目标包并使用进程内通信，实际执行完整密码学交接；上游全包测试继续单独记录。

P149 已进一步验证原生 TCP 路径：四个旧成员、四个新成员分别运行独立进程，全部后继完成交接；十节点原生完整测试的 reducedShares、fullShares 两条重构路径均恢复原秘密。复现命令为 `python3 experiments/verification/dycaps_native.py`，详细结果见 `verification/dycaps-report.md`。

发布的 `test_multiCommittee.sh` 把角色写作 `currentCommitee`、`newCommitee`，实际命令程序接受 `oldCommittee`、`newCommittee`。运行器使用正确参数和本次分配的端口，协议源文件保持原样。十节点测试仅用 overlay 替换固定端口。成员退出和消息保存的真实网络实验随后在这一入口上扩展。

### Optimistic DPSS

运行：

```bash
cd experiments/upstream/optimistic-dpss
go test ./...
```

完整测试失败：Pointproofs 测试缺少 `pkg/pointproofs_target/release/libvc_api`；若干网络测试复用固定端口，并行执行时发生端口占用。基础组件包 `bls、dprf、party、polycommit、polyring、vss、reedsolomon、vectorcommitment` 的分组测试通过。

随后单独运行 `go test -count=1 -timeout=45s -run '^TestDpssNew$' ./internal/DPSS`，在测试限时内未完成。完整日志及 goroutine 栈保存于 `results/optimistic-dpss-test.log`；此观察用于定位实现，不能据此判定协议不具备异步活性。当前首条接入路径使用已跑通的 DyCAPS，Optimistic DPSS 保留为后续优化候选，继续分别核对原论文敌手条件。

按上游 `cmd/test_main.sh` 使用 $n=4,f=1$ 的正确参数重新运行了原生八进程入口。第一次运行中四个新成员完成，两个旧成员完成，另外两个旧成员停在 `wpACSS` 交互；第二次运行在新成员处理承诺时出现 `input string length must be equal to 48 bytes`，其余进程随后等待。两次运行均在 30 秒限时内未形成完整端到端通过。结果保存在 `results/upstream-verification/optimistic-dpss/main-baseline/` 和 `main-baseline-rerun/`，因此 DPSS 当前只作为已通过组件测试和待定位的交接基线记录。

### Buffalo

Bazel 6.5.0 已完成 RLWE 扩展构建；上游 C++ API 测试和 Python 原生测试均通过。修正核验脚本后，以下三项检查通过：

```bash
python3 experiments/verification/buffalo-run.py buffalo-native \
  /home/yzc/flsecagg/experiments python3 verification/buffalo-native.py
python3 experiments/verification/buffalo-run.py buffalo-roundtrip \
  /home/yzc/flsecagg/experiments python3 verification/buffalo-native.py roundtrip
python3 experiments/verification/buffalo-run.py buffalo-seeded-roundtrip \
  /home/yzc/flsecagg/experiments python3 verification/buffalo-native.py seeded-roundtrip
```

检查覆盖 $2^{11}$ 维 RLWE 加解密、五个独立密钥的模加聚合、密钥向量求和、共享矩阵种子下的单实例复现以及 Buffalo Python 包装器。原生实现要求聚合参与者使用同一 RLWE 上下文；探索性地让多个独立 Python 对象共享 seed 时，五客户端聚合出现不稳定解密结果，因此没有把该路径记为通过，也没有修改上游实现。FLSim 的两个 FedBuff 一致性检查仍失败，一个指标隔离检查通过，详见 `results/upstream-verification/buffalo/`。

## 接入顺序

### A. 已完成的组件交接

已使用 $n=4,f=1$ 检验真实交接、新份额变化、公钥保持及交接前后系数密文相加。旧节点进程结束后，后继仅从保存的 Prepare 和 Reduce 输入继续执行。

保存者路径也已扩展为 A、B 两个独立保存库。B 完成副本复制后，A 删除保存库；后继和延迟恢复路径只读取 B，验证保存者退出不会让已交付的交接输入重新依赖发送者。

### B. 加入发送后消息丢失

以实际有效输入门槛安排故障。当前接收者至少需要两个不同旧节点的有效 Reduce 输入，丢一条消息仍可能完成。已有检查覆盖低于门槛时等待、补齐后恢复；下一步将这些真实消息接到按接收者加密的副本保存机制，检验保存者退出及接收私钥丢失。

### C. 接入聚合实例

当前检查使用固定的实例身份、代数和三系数输入。后续把输出绑定到真实模型版本、权重和已接受更新前缀，并接入带证明的部分开启；最终开启、结果提交和模型应用仍分开记录。

### D. 最后接入 FL workload

先使用现有回放器产生客户端到达和模型版本，再接 Buffalo 或 FLSim 的小模型训练。相同客户端轨迹下比较“安装完成后退出”和“保存完成后退出”，报告旧节点在线时长、后继就绪时间、完成实例数和通信量。

## 当前边界

本轮执行原版 DPSS 交接代码。测试沿用上游可信初始化方和公开测试 KZG 设置，跨组临时文件包含私密求值和接收私钥，权限为 0600；实验封装使用 Curve25519 匿名盒与 Ed25519 签名，属于组件接入检查，不等同于论文最终密码学构造。多保存者流程当前验证诚实保存者 B 在 A 退出后继续提供完整副本；恶意节点、安全清除、可信设置及受限移动敌手下的组合保证，仍需各自实现与分析。

系数开启检查直接使用诚实成员的部分开启点；Reduce 的 KZG 证明已检验，部分开启的等离散对数证明尚未接入。Buffalo 的 RLWE 扩展已经构建并完成原生小规模核验，但多进程 FL 适配和训练一致性仍未通过。下一项实现优先复用可验证开启组件，并把真实 Reduce 输入接到保存与恢复流程，再接 RLWE 及小规模训练。
