# 抽象聚合流程与检验追踪

更新日期：2026-09-20。本稿记录聚合实例从更新纳入、委员会交接到整体开启和清除封存的可执行流程，以及检查中发现的问题。

## 1. 实现范围与模块

| 文件 | 当前职责 |
|---|---|
| `abstract_threshold_backend.py` | 实例身份、活动状态、唯一后继、开启证书、部分开启记录和清除封存 |
| `handoff_microbench.py` | 多实例成功路径及符号状态规模估算 |
| `check_abstract_protocol.py` | 两次连续交接、拒绝路径与交接事件排列检查 |
| `check_departure_recovery.py` | 发送进程结束后，从加密副本恢复交接载荷、从公开贡献恢复系数和 |
| `run_dycaps_handoff.py`、`dycaps_handoff_test.go` | 在独立后继进程执行原版 DPSS 交接并继续 BLS12-381 系数聚合 |
| `reconfigurable_fl_sim.py` | 异步到达、配置变化、失败恢复、放弃与重提的服务事件回放 |

前三个文件使用同一抽象后端。回放器目前独立运行；其 `window_finalize` 仍直接模拟结果确定。当前真实组件进展见 `REAL_COMPONENT_BRINGUP.md`，组件输出与回放器的接通随后进行。

## 2. 整体流程

```text
open_state -> admit_update -> export
                              |
                              v
                 reshare -> confirm
                              |
                        erase(source)
                              |
                     activate(successor)
                              |
                 admit_update on the same sid
                              |
              authorize_open -> partial_open
                              |
                         combine_open
                              |
                        erase(current)
                              |
                             seal
```

源状态遵循 `owned -> exported -> erased`。后继状态遵循 `installed -> confirmed -> owned`；激活以源状态已清除为前提。实例在交接前后保留同一标识、模型版本、维度和已接受更新集合，随后追加新更新。每次交接的实例代数增加一。

最终化遵循 `owned -> opening -> committed -> erased -> sealed`。`authorize_open` 固定最终状态并进入 `opening`，等待足够的部分开启；`combine_open` 成功时才产生可供服务发布的唯一结果。服务应在此时记录 `Commit_sid`，执行清除后再记录 `Seal_sid`。等待开启期间，其他实例可以继续推进。

## 3. 接口与绑定

```text
open_state(context, dimension, update_ids, *, instance_id, model_version)
export(state, frontier_version) -> HandoffRecord
reshare(record, successor_context) -> (successor, estimated_bytes)
confirm(successor)
erase(source)
activate(successor, record)
authorize_open(state) -> AggregateOpenCertificate
partial_open(state, certificate, member) -> PartialOpening
combine_open(partials, certificate) -> AggregateOpening
erase(state)
seal(state) -> SealedRecord
```

`HandoffRecord` 绑定源上下文、接收截点版本、更新集合、实例标识、模型版本、状态版本和维度。后继维度直接继承记录。对同一记录重试重分享会返回已安装的同一状态；改变后继上下文会被拒绝。源状态清除要求后继安装已经确认。

开启证书绑定 `instance_id, model_version, configuration, generation, dimension, state_version, accepted_update_ids, committee_members, threshold`。合并使用当前实例实际授权的证书，并核对部分开启曾由该后端产生。门槛按不同成员计数；同一成员的重复记录计一次。实例标识在本后端中保持唯一，封存后继续保留结果身份。

更新集合按标识排序后保存，用于检查纳入集合的一致性。该表示保留集合成员关系，接收次序由服务回放日志另行记录。封存记录从已完成的开启结果生成，因此活动状态清除后仍保留实例、模型版本和最终参与集合。

## 4. 本轮发现与修复

| 复现的问题 | 原因 | 当前处理 |
|---|---|---|
| 同一交接激活两个可写后继 | 重分享每次创建副本，激活只检查源状态已清除 | 每个交接保存唯一后继；激活后更新当前实例并消费待激活记录 |
| 维度从 8 变为 16 仍可交接 | 后继维度由调用者另行传入 | 维度纳入源记录并直接继承 |
| 后继尚未安装或确认，源状态即可清除 | `exported` 被直接视作可清除 | 清除以该后继的安装确认为前提 |
| `sealed` 状态仍计有 768 字节活动材料 | 原成功路径先 `seal` 再 `erase` | 开启成功、清除、封存依次执行；封存状态的活动字节数为零 |
| 开启授权被记作结果完成 | 授权时直接进入 `committed` | 增加 `opening` 阶段，合并成功才进入 `committed` |

此前临时检查还把 `admit_update` 返回 `False` 误判成接受。现有检查分别判断布尔拒绝和异常拒绝，并核对异常原因。重复合并直接重用已生成的部分开启调用 `combine_open`，使检查落在合并操作本身。

## 5. 可重复运行的检验

```bash
python3 experiments/check_abstract_protocol.py
python3 experiments/handoff_microbench.py \
  --dimension 32 --old-members 4 --new-members 5 --threshold 3 \
  --active-windows 2 --updates-per-window 3 \
  --output /tmp/handoff-opening.csv
```

2026-09-19，以上命令均通过。检查覆盖：

1. 三个互不相交委员会之间的两次交接，委员会规模和门槛变化，同一实例持续追加更新。
2. 交接重试、后继冲突、旧记录复用、提前清除、提前激活及旧状态再次开启。
3. 证书九个字段的分别替换、跨实例组合、非成员、未产生的部分开启、人数不足和重复成员。
4. 一个实例等待开启时另一个实例完成；结果唯一；清除后封存；封存后写入、开启和交接均拒绝。
5. `confirm, erase, activate` 的全部六种排列，只有规定顺序全部成功。

微基准输出源状态 `4608`、后继状态 `4672`、交接估算 `9280`、封存记录估算 `192` 字节。这些数值采用原有 `32` 字节元素和固定元数据模型，用于核验公式和流程。真实编码、证明、重传、更新标识存储及清除代价需要由具体后端测量；它们尚未计入这组估算。编译检查与 A0 schema 的 JSON 语法检查也已通过。

## 6. 结论适用范围与下一步

当前检验支持单个抽象后端内的状态顺序、更新集合保持、唯一后继和唯一结果。证书和部分开启都是进程内记录；密码学认证、共享刷新、物理清除以及受限移动敌手下的隐私结论，需要具体组件和相应安全分析。记录中的更新标识用于替代受保护聚合状态，尚未计算训练向量或模型精度。

接入服务回放器前，需要把已保存材料的恢复与原持有者的进程内状态分开，并将开启合并与模型结果提交分别表示。当前 `combine_open` 读取原后端中的贡献记录且直接标记 `committed`，适用于早期状态顺序检查。P145 至 P147 的方案允许公开开启材料先保存、原秘密持有者先退出，随后由当前服务提交结果。回放器接入应沿此方案推进。

## 7. P147：退出后的材料恢复检查

运行 `python3 experiments/check_departure_recovery.py`。依赖本机已有 PyNaCl 1.5.0；2026-09-20 实际运行通过。

产生材料的子进程先结束；检查进程只收到交接接收者自己的私钥、源签名公钥、加密消息和公开开启材料。源签名私钥、实例秘密、多项式系数及成员份额均留在已结束的生成进程。每次系数恢复又启动一个独立进程，只向其传入公开开启材料。

| 检查 | 实际结果及范围 |
|---|---|
| 完整加密批次有三个副本，其中一个不可用 | 接收者从另一副本取得消息，以自己的私钥解密并验证源签名 |
| 副本缺失、接收私钥丢失后换钥、错误源公钥、密文篡改、取错接收者消息 | 按对应的取回、解密或认证错误拒绝 |
| 三个客户端、三个系数、四个持有者、门限为三 | 四种三人子集以及四人集合均在独立进程恢复 `[3, 0, -4]` |
| 贡献不足、重复成员、跨代、跨实例、向量缺项 | 检查拒绝合并 |
| 所有成员的第一个贡献点都加同一个基点 | 恢复值变为 `[2, 0, -4]`；此对照显示正式组件需要验证贡献证明 |

交接实验采用 PyNaCl 的 SealedBox 和独立 Ed25519 签名，消息绑定实例、代数及指定接收者。载荷是代替 Reduce 输入的固定字节串，复制与副本故障在本地模拟。开启实验采用 Ed25519 素数阶子群的门限 ElGamal 代数；候选论文方案仍采用 P146 的 BLS12-381，字节预算沿用其参数。上下文由检查预置；证明验证、共识授权、DPSS 刷新、RLWE 解码、网络传输和物理安全清除尚需具体实现。进程结束用于检验后续计算的数据依赖。

这一结果支持两条不同的恢复条件：交接输入需要指定接收者的有效私钥，已经产生的完整开启贡献支持公开合并。下一步复用选定组件，核验交接输入验证及缺份额恢复，并接入带证明的部分开启；测量沿用同一到达轨迹下的旧节点在线时长、后继就绪时间和完整通信量。

## 8. P148：原版 DPSS 交接接入

`python3 experiments/run_dycaps_handoff.py` 已通过 sender、successor、quorum、recover 四阶段。旧组进程结束后，后继从真实 Prepare、Reduce 消息继续原版刷新和份额分发。16 份有效 KZG 求值证明通过，16 个被篡改的求值被拒绝；只保留两个旧发送者的路径也完成。后继收到低于门槛的输入时，在注入的 100 ms 区间保持等待，补齐后完成。

四份新份额均变化，所有六种两人组合都保持实例公钥，并恢复跨交接的三客户端系数和 $[3,0,-4]$。测试复用上游的公开测试设置，节点在每组进程内部通信，提供功能接合证据。具体范围、版本、原始日志和后续工作见 `REAL_COMPONENT_BRINGUP.md`。
