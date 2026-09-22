# Reconfigurable asynchronous FL experiment construction

> 文档定位：本文工作的实验构建稿。它回答三个问题：实验使用哪些开源组件，如何把动态成员和异步训练放入同一套运行流程，以及各个基线需要哪些适配。本稿用于实验执行，不是论文初稿。

## 1. Experimental objective

本文验证一个系统主张：

> 在客户端更新持续异步到达、委员会发生加入、退出、崩溃、恢复和节点滚动腐蚀时，活动训练窗口能够继续推进，已经完成的窗口保持同一结果，配置交接的状态开销随活动窗口规模增长。

实验把训练行为和更新保护分开观察。先回答动态成员是否影响训练连续性和模型推进，再测量安全聚合带来的通信与计算代价。密码学实现作为更新保护插件，实验主线保持在联邦学习服务行为。

## 2. Experiment architecture

```text
client workload
    -> asynchronous training event
    -> window service
    -> aggregate backend
    -> model snapshot and metrics
```

### 2.1 Client workload

客户端在本地模型版本上训练并提交更新。workload 产生：

```text
client_id
base_model_version
local_steps
training_finish_order
training_duration
update_delta
sample_weight
```

客户端训练代码、数据划分和模型评估由 FLSim 或 Catalyst 提供。客户端只提交更新，不判断委员会是否完成交接，也不决定窗口是否封存。

### 2.2 Event scheduler

调度器把客户端完成事件、网络延迟和成员事件合并为一条可重放轨迹。轨迹中的 `order` 是实验记录顺序，客户端完成时间来自异步训练 workload。

调度器注入：

```text
config_install
node_join
node_leave
node_crash
node_recover
node_corrupt
node_release
recover_state
message_deliver
```

滚动腐蚀事件只改变服务节点的控制和状态暴露记录。恶意客户端更新由 Catalyst 场景单独处理。

### 2.3 Window service

窗口服务是本文的主要实现对象，维护：

```text
window_id
base_model_version
owner_configuration
accepted_update_ids
window_status
record_version
aggregate_progress
sealed_result
```

窗口服务执行：

```text
open_window(model_version, configuration)
submit_update(client_update)
install_configuration(configuration_event)
handoff_live_window(window_id)
finalize_window(window_id)
recover_window(window_id, record_version)
```

活动窗口只有一个可写配置。配置转换时，活动窗口交给后继配置继续处理，已完成窗口只携带封存记录。四种策略只替换窗口交接规则，客户端 workload 和聚合接口保持一致。

### 2.4 Aggregate backend

聚合后端分为两个阶段：

```text
明文向量后端
    -> 验证窗口归属、客户端纳入和模型推进

protected-update backend
    -> 测量安全聚合实现的保护成本
```

第一阶段使用向量或不透明更新记录，让服务行为独立于具体密码学实现。第二阶段将同一 `ClientUpdate` 的 `payload` 替换为受保护更新。后端返回窗口服务需要的聚合结果，不改变窗口状态和配置规则。

第一版交接微基准使用 `experiments/abstract_threshold_backend.py`。它只记录按实例聚合状态的份额规模和状态转移：

```text
open_state -> admit_update -> export
           -> reshare -> confirm -> erase(source) -> activate(successor)
           -> admit_update -> authorize_open -> partial_open -> combine_open
           -> erase(current) -> seal
```

`AggregateShareState` 保存保护上下文、维度、已接受更新标识和阶段；`HandoffRecord` 绑定实例、模型版本、维度和接收截点。`reshare(record, successor_context)` 安装唯一后继并继承源维度；同一交接的重试返回同一状态。后继安装确认后，源状态完成清除，后继才恢复写入。

`authorize_open` 固定最终状态并进入 `opening`，`combine_open` 产生唯一结果并进入 `committed`。服务在此时发布 `Commit_sid`；清除完成后，`seal` 从结果生成 `SealedRecord`，再记录 `Seal_sid`。证书同时绑定实例、模型版本、配置、代数、维度、状态版本、更新集合、委员会成员和开启门槛。

抽象后端采用更新标识和符号规模表示聚合状态。真实 PVSS 或其他保护组件将提供认证、重分享与开启计算。当前实现和检验详见 `experiments/ABSTRACT_OPENING_TRACKER.md`；运行 `python3 experiments/check_abstract_protocol.py` 可复查交接与最终化约束。服务回放器目前独立运行，后端与 `window_finalize` 的连接属于下一阶段。

微基准入口为：

```bash
python3 experiments/handoff_microbench.py \
  --dimension 1024 \
  --old-members 4 \
  --new-members 4 \
  --threshold 3 \
  --active-windows 8 \
  --updates-per-window 16 \
  --output experiments/handoff_microbench.csv
```

输出区分源状态、后继状态、交接通信量和封存记录大小，用于绘制活动实例数量、模型维度和委员会规模对交接成本的影响。

抽象后端的估算关系为：

```text
encrypted_update_sum  = dimension * element_bytes
encrypted_key_sum     = dimension * element_bytes
aggregate_key_share   = members * key_share_bytes
source_state_bytes    = active_windows * (metadata + encrypted_update_sum + encrypted_key_sum + aggregate_key_share(old_members))
successor_state_bytes = active_windows * (metadata + encrypted_update_sum + encrypted_key_sum + aggregate_key_share(new_members))
handoff_bytes         = source_state_bytes + successor_state_bytes
sealed_record_bytes   = active_windows * fixed_sealed_record_bytes
```

该状态模型最初用于估计 Buffalo 兼容的 JL 聚合份额交接。组件审计后，首选后端改为系数域阈值保护：受保护模型保存一份，RLWE 密钥保存为 `m` 个可加曲线密文，委员会成员只保存一个窗口阈值密钥份额。单个活动实例的状态规模因此由 `d`、RLWE 维度 `m` 和曲线点编码共同决定；接受更新标识仍作为窗口元数据单独记录。

此前的三组扫描和 `526,336/526,848` bytes 结果使用旧的 JL 聚合份额状态模型，只保留为历史估算。阶段 D 按真实曲线点编码重新测量系数密文、窗口密钥份额和交接证明；论文结果不沿用这组旧数值。

## 3. Open-source components

### 3.1 Required components

| Component | Repository | Role in this work | Use |
|---|---|---|---|
| FLSim | `https://github.com/facebookresearch/FLSim` | 客户端本地训练、异步训练事件、陈旧度和 FedBuff 控制 | archived；用于 workload 和非安全异步控制 |
| Buffalo | `https://github.com/rtaiello/buffalo` | 主要异步安全聚合对照 | 使用公开实现和 Olympia/FLSim 运行路径 |
| Setup Once, Secure Always | `https://github.com/bytest02/scatesfl` | 动态用户安全聚合对照 | 记录用户动态和单次 setup；不改造成动态委员会基线 |
| Flower | `https://github.com/flwrlabs/flower` | SecAgg+ 同步安全聚合控制 | 使用 `flower-secure-aggregation` 示例 |
| Catalyst | `https://github.com/bacox/Catalyst` | 异步训练与 Byzantine 更新鲁棒性控制 | 使用原生异步训练脚本 |
| PyTorch | `https://pytorch.org` | 统一模型、本地训练和张量处理 | 由各框架按原生方式调用 |

### 3.2 Supporting components

| Component | Repository | Experimental role | Treatment |
|---|---|---|---|
| APSS | `https://github.com/ISTA-SPiDerS/apss` | 异步状态交接和恢复成本参考 | 只做状态迁移微基准 |
| DyCAPS | `https://github.com/DyCAPSTeam/DyCAPS` | 动态委员会 handoff 和 crash/cure 成本参考 | 只做原生协议成本记录 |
| LEAF | `https://github.com/TalwalkarLab/leaf` | FEMNIST 等自然客户端数据划分 | 第二阶段加入 |
| PPFA-BAA artifact | 论文提供的匿名仓库 | 异步 Byzantine FL 补充对照 | 仓库和运行脚本可复现后再加入 |

Turritopsis 用于动态异步成员模型的文献参照和事件设计，不作为 FL 端到端基线。它解决的是动态异步 BFT 共识，本文比较的是配置交接对 FL 窗口服务的影响。

### 3.3 Download list

实验设备准备以下仓库：

```bash
git clone https://github.com/facebookresearch/FLSim.git vendor/FLSim
git clone https://github.com/rtaiello/buffalo.git vendor/buffalo
git clone https://github.com/bytest02/scatesfl.git vendor/scatesfl
git clone https://github.com/flwrlabs/flower.git vendor/flower
git clone https://github.com/bacox/Catalyst.git vendor/Catalyst
git clone https://github.com/ISTA-SPiDerS/apss.git vendor/apss
git clone https://github.com/DyCAPSTeam/DyCAPS.git vendor/DyCAPS
```

基础环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch torchvision
pip install -e vendor/FLSim
pip install -e vendor/Catalyst
```

Buffalo、Flower 和 APSS/DyCAPS 按各自仓库中的依赖文件安装。每个仓库单独记录版本、依赖和运行日志。

## 4. Baseline matrix

### 4.1 Primary system rows

| ID | Baseline | Source | Dynamic membership | Secure aggregation | Purpose |
|---|---|---|---|---|---|
| `P0` | Selective-finality | 本文实现 | 活动窗口交接，完成窗口只读封存 | 先用向量后端，再接保护插件 | 论文方案 |
| `A1` | Static | 本文同一服务实现 | 配置固定 | 与 `P0` 相同 | 固定成员性能参照 |
| `A2` | Full-transfer | 本文同一服务实现 | 所有窗口材料都迁移 | 与 `P0` 相同 | 全量迁移的状态和延迟代价 |
| `A3` | Periodic-rekey | 本文同一服务实现 | 活动窗口排空后接收新窗口 | 与 `P0` 相同 | 周期性重建状态的连续性代价 |
| `B1` | Buffalo-native | Buffalo | 固定 assistant 集合 | Buffalo 原生保护 | 最接近的开源异步安全聚合基线 |
| `B2` | Buffalo-reset | Buffalo 外部包装 | 每次配置变化关闭旧实例并启动新实例 | Buffalo 原生保护 | 普通动态部署的可行性和丢失代价 |
| `B3` | FedBuff/FLSim | FLSim | 固定成员 | 明文或框架原生后端 | 异步缓冲训练控制 |
| `B4` | Flower SecAgg+ | Flower 示例 | 固定同步轮次 | SecAgg+ | 常规安全聚合控制 |
| `B5` | Catalyst | Catalyst | 按原生脚本执行 | 明文 | 异步训练和 Byzantine 更新控制 |
| `B6` | Setup-Once-native | SCATESFL | 动态用户，聚合服务器固定在线 | 原生单次 setup 保护 | 动态用户与动态委员会的边界对照 |

`P0` 与 `A1-A3` 使用同一服务实现，只改变窗口策略。 `B1` 是主要外部端到端基线。 `B3-B6` 区分异步训练、保护开销、恶意更新处理和动态用户参与的影响。`B6` 不声称支持动态聚合委员会。

### 4.2 Optional baseline

| ID | Baseline | Inclusion condition | Reporting position |
|---|---|---|---|
| `B7` | PPFA-BAA | artifact 可访问，supplied run 可复现 | 异步 Byzantine FL 补充结果 |
| `C1` | APSS | 依赖和测试脚本可运行 | 状态迁移微基准 |
| `C2` | DyCAPS | 依赖和测试脚本可运行 | 动态委员会状态成本参考 |

如果 `B7` 的匿名 artifact 无法访问，论文主表不依赖它。APSS 和 DyCAPS 不产生统一 FL 模型质量结果，放在状态成本和假设对比中。

## 5. Modification policy

### 5.1 General rule

所有上游仓库保持原样。实验适配放在本文的 `experiments/adapters/` 或独立 checkout 中，记录：

```text
upstream repository
upstream version
adapter version
dataset and model configuration
command line
raw log location
```

适配只负责输入输出转换、事件注入和日志采集，不改变基线的聚合算法、保护参数或故障假设。

### 5.2 FLSim

FLSim 的 `AsyncClientDevice` 产生本地 `delta`、训练后模型和样本权重，`AsyncTrainingSimulator` 负责训练完成顺序。FLSim 的默认 `AsyncTrainer` 在客户端训练结束后直接调用异步聚合器并推进全局模型。

因此采用两种运行方式：

```text
B3 FedBuff/FLSim:
    使用 FLSim 原生 AsyncTrainer/FedBuff 路径

P0/A1-A3 workload:
    使用 FLSim 客户端和训练事件，交给外部窗口服务处理
```

第二种方式需要一个薄 runner 或 subclass，在 FLSim 默认全局更新之前截取客户端训练完成事件并创建 `ClientUpdate`。FLSim 源码保持不变。窗口服务自己维护模型快照，已接受窗口的聚合结果再交给 PyTorch 优化器。

### 5.3 Buffalo

Buffalo 原生实现用于 `B1`，保持其 buffer、assistant、更新保护和验证流程。适配器只负责：

```text
FLSim workload -> Buffalo client input
Buffalo output -> common result log
timing/counters -> experiment metrics
```

`B2 Buffalo-reset` 只在外部 launcher 层处理配置事件：当前配置结束后关闭 Buffalo 实例，保存已经完成的 buffer 结果，再为后继配置启动新实例。尚未完成的 buffer 内容单独记录为丢弃或重新提交，不把结果当作 Buffalo 原生动态能力。

### 5.4 Flower SecAgg+

Flower 只修改 `ClientApp`、`ServerApp` 和模型任务代码，用于接入统一模型、数据划分和日志。SecAgg+ workflow 保持原样。

Flower 的同步轮次映射为固定窗口，因此 `B4` 只回答安全聚合的基础代价和模型质量。加入异步窗口交接后，它应以新的实验名称出现，而不是继续标注为 Flower 原生基线。

### 5.5 Catalyst

Catalyst 使用其原生客户端速度分布、异步调度和 Byzantine 算法。适配内容限于模型、数据和结果读取。它不承担安全聚合，也不承担本文的窗口封存语义。

### 5.6 APSS and DyCAPS

APSS 和 DyCAPS 使用原生参数做状态迁移时间、通信量、恢复延迟和持久状态大小测量。实验报告保留其原始协议名称、门槛和故障条件。本文只把它们作为状态交接参考，不将其代码嵌入 P0。

### 5.7 Setup Once, Secure Always

`SCATESFL` 的公开实现是一个固定参与者原型。`src/config.json` 固定 `num_users`、`num_fognode` 和 `epochs`，`src/flapp.py` 按 epoch 依次训练客户端，再由固定的 fog nodes 和 aggregator 完成验证与聚合。代码没有委员会安装、成员交接或跨配置恢复路径，也没有把客户端训练事件放入真正的异步调度器。

因此 `B6 Setup Once native` 只作为论文协议的动态用户安全聚合对照。实验记录其原生用户参与、掉线处理和单次 setup 成本；不向代码中加入动态委员会逻辑，也不把外部包装后的版本称为 SCATESFL 原生能力。

## 6. Common workload

### 6.1 Primary workload

第一组端到端实验固定为：

```text
dataset:       CIFAR-10
model:         small CNN with a fixed parameter dimension
client split:  fixed non-IID partition shared by all primary rows
local train:   fixed optimizer, batch size, and local steps
evaluation:    test accuracy and loss on the same held-out set
```

客户端训练时间从 heterogeneous client speed 分布生成。每个客户端的训练结果携带基础模型版本和完成顺序，服务使用该信息计算陈旧度并决定纳入窗口。

第二组 workload 使用 FEMNIST 或 Buffalo 原生的 CelebA/Sent140 配置，用于检查不同数据规模和模型结构下的趋势。Buffalo 原生复现实验可以保留其论文 workload，但跨框架主表优先使用 CIFAR-10。

### 6.2 Fixed factors

所有主表固定：

```text
client population
data partition
model architecture
local optimizer and steps
client speed distribution
update dimension
evaluation schedule
configuration event trace
```

基线只改变窗口策略、是否使用安全聚合，以及对应的故障处理方式。性能实验使用至少 10 个随机种子；每个安全场景使用一条确定性攻击轨迹和若干延迟排列。

## 7. Dynamic-member trace

### 7.1 Trace format

沿用 `reconfigurable-async-fl-system-spec.md` 的 CSV 字段：

```text
order,kind,configuration,window,model_version,client,node,record_version,protection_context,source_window,delivered,update_id,source_update_id,source_generation,target_generation,handoff_attempt_id,retrained
```

滚动腐蚀事件为：

```text
node_corrupt       -> 读取节点当前服务状态并控制其后续行为
node_release       -> 释放该节点的主动控制
recover_state      -> 请求安装某个窗口的状态版本
handoff_confirm    -> 后继配置确认或拒绝活动状态安装
client_resubmit    -> 截点后的更新在后继实例重新提交
```

事件轨迹不保存客户端明文更新。模型质量由训练框架单独保存，服务日志保存窗口和配置事件。

### 7.2 Trace families

| Trace | Event pattern | Question |
|---|---|---|
| `T0` | 异步客户端完成，无成员变化 | 基础训练吞吐和模型质量 |
| `T1` | 活动窗口期间 config_install、join、leave | 活动窗口能否继续推进 |
| `T2` | 交接后旧节点退出或崩溃 | 已纳入更新能否保留 |
| `T3` | 封存前后交付同一迟到消息 | 封存结果是否稳定 |
| `T4` | 配置切换期间 corrupt、release、recover | 滚动腐蚀下的状态恢复行为 |
| `T5` | 两个或以上连续配置转换 | 窗口归属是否保持唯一 |
| `T6` | 高延迟客户端和高 churn 同时出现 | 训练质量与服务延迟的联合影响 |
| `T7` | 未满额实例在交接清除后继续收集更新 | 原实例是否跨配置达到聚合门槛 |

主要动态成员结果来自 `T1-T7`。 `T0` 建立各个 FL 框架的共同训练基线。

### 7.3 Existing trace commands

当前抽象回放器直接执行：

```bash
python3 experiments/generate_reconfigurable_trace.py \
  --transitions 2 \
  --windows-per-configuration 4 \
  --clients-per-window 2 \
  --nodes 6 \
  --output experiments/reconfigurable_trace.csv
```

带客户端和委员会成员事件的轨迹增加 `--include-membership-events`：

```bash
python3 experiments/generate_reconfigurable_trace.py \
  --transitions 2 \
  --windows-per-configuration 4 \
  --clients-per-window 2 \
  --nodes 6 \
  --include-membership-events \
  --output /tmp/reconfigurable_membership_trace.csv
```

```bash
python3 experiments/reconfigurable_fl_sim.py \
  --trace experiments/reconfigurable_trace.csv \
  --output experiments/reconfigurable_results.csv
```

该回放验证窗口、客户端资格、委员会成员事件和节点事件。回放器已经记录 `frontier`、`generation`、保护上下文和交接确认失败路径。真实 FL runner 把 FLSim/Catalyst 的训练完成事件映射到同一格式，再调用窗口服务。

## 8. Experimental phases

### Phase 0: trace semantics

使用当前抽象模拟器运行 `T0-T7`，检查：

```text
window ownership
accepted-client set
    committed/sealed result stability
state recovery count
corruption and release schedule
handoff confirmation and protection-context transition
retained record bytes
```

### Phase 1: 明文模型训练

使用 FLSim 客户端完成真实本地训练，窗口服务先接收向量更新。验证：

```text
model snapshot continuity
accepted update set
model-version progress
accuracy/loss versus completed aggregates
```

该阶段隔离动态成员机制。

### Phase 2: 受保护更新的接入

将 `ClientUpdate.payload` 替换为 Buffalo 或其他选定的保护格式。窗口服务和四类策略保持相同，单独记录：

```text
client protection time
server/assistant processing time
upload and download bytes
handoff bytes
persistent state bytes
```

该阶段在 Phase 1 的窗口结果和模型推进稳定后开始。

### Phase 3: external baselines

依次执行：

```text
B1 Buffalo-native
B2 Buffalo-reset
B3 FedBuff/FLSim
B4 Flower SecAgg+
B5 Catalyst
```

每个基线先运行原生 README 或论文脚本，再接入统一模型和数据。原生结果和统一 workload 结果分开存储。

### Phase 4: dynamic fault evaluation

固定模型、客户端数据和训练预算，改变：

```text
transition frequency
active-window count
slow-client fraction
message delay and reordering
leave/crash rate
rolling corruption schedule
```

每次只改变一个主因素，再运行组合场景 `T6`，把训练退化、状态迁移成本和保护成本分别归因。

## 9. Parameter matrix

| Factor | Values |
|---|---|
| committee size | 8, 16, 32 |
| active windows | 1, 4, 8 |
| clients per window | 16, 32, 64 |
| transitions | 0, 1, 3, 5 |
| leave/crash events per transition | 0, 1, 2 |
| corruption schedule | before handoff, during handoff, after finalization |

每个配置记录瞬时受控节点数、离开节点数、配置重叠和活动窗口数。参数报告采用各基线的原生容错配置，动态服务额外报告本身的可用节点条件。

## 10. Metrics and plots

训练与服务指标：

```text
window completion rate
accepted-client rate
model-version progress
test accuracy and loss versus completed aggregates
update staleness
handoff latency
recovery latency
configuration transition delay
```

状态与通信指标：

```text
reopened or duplicated window count
accepted stale handoff count
client upload/download bytes
configuration handoff bytes
peak and persistent state bytes
fraction of windows blocked by unavailable nodes
```

核心图：

1. 窗口完成率和模型版本推进随委员会 churn 变化。
2. 模型准确率和损失随已完成聚合数变化。
3. p50/p95 交接和恢复延迟。
4. 持久记录大小随已完成窗口数和配置转换次数变化。
5. 活动窗口并发度与吞吐量。
6. `Selective-finality`、`Full-transfer` 和 `Periodic-rekey` 的连续性与状态成本。
7. Buffalo-native、Buffalo-reset 和 P0 的保护成本分解。
8. 滚动腐蚀轨迹下的窗口重开、迟到消息拒绝和模型推进。

## 11. Artifact layout

```text
vendor/<project>/                 upstream checkout
adapters/<baseline>/              external adapter and configuration
traces/<family>/<seed>.csv        immutable event traces
results/raw/<baseline>/<trace>/   raw logs
results/derived/                  tables and plots
configs/                          model, data, and service parameters
```

每条结果至少记录：

```text
baseline
upstream version
adapter version
dataset/model configuration
trace identifier
seed
host and accelerator
dependency versions
command line
```

原生基线结果与统一 workload 结果分开保存。跨框架比较只使用统一 workload 结果。

## 12. Interpretation rules

主表优先放：

```text
P0 Selective-finality
A1 Static
A2 Full-transfer
A3 Periodic-rekey
B1 Buffalo-native
B2 Buffalo-reset
B3 FedBuff/FLSim
B4 Flower SecAgg+
```

Catalyst 单独作为异步 Byzantine 更新控制。它的结果用于说明模型质量和恶意更新处理，不能直接与安全聚合行合并成同一保护排名。

向量后端结果支持窗口归属、训练连续性、结果稳定性和状态成本主张。受保护更新结果支持保护开销和同一窗口服务规则下的端到端表现。单次实验中没有发生窗口重开，只能说明测试轨迹没有触发该现象；系统结论仍依据窗口规则和实现检查。

论文中分别标注：

```text
native baseline
external logging adapter
external workload adapter
dynamic restart wrapper
derived policy baseline
```

对 Buffalo、Flower 或 FLSim 的行为改变都进入独立 baseline 名称，不以原项目名称代替。

## 13. Execution order

1. 在实验设备下载 required components，保存各自版本和原生运行日志。
2. 运行当前 trace replay，生成 `T0-T6` 的窗口服务结果。
3. 完成 CIFAR 10 的明文模型训练 runner。
4. 使用同一客户端和配置轨迹运行 `P0`、`A1`、`A2`、`A3`。
5. 运行 Buffalo-native 和 Buffalo-reset，记录活动 buffer 的完成、丢弃和重启行为。
6. 运行 FedBuff/FLSim、Flower SecAgg+ 和 Catalyst 控制。
7. 选定一个保护后端，重复动态成员场景并记录保护成本。
8. 运行连续配置转换和滚动腐蚀组合场景，生成主表和核心图。

## 14. Current decision

```text
primary external baseline:  Buffalo-native
primary async workload:     FLSim, with Catalyst as a secondary control
secure aggregation control: Flower SecAgg+
dynamic-user comparison:     Setup-Once-native (SCATESFL)
main derived ablations:     Static, Full-transfer, Periodic-rekey
dynamic Buffalo variant:    Buffalo-reset, clearly labeled as an adapter
first dataset:              CIFAR 10
first execution layer:      明文模型训练
cryptographic scope:        保护插件和成本测量
```

这套构建把论文主问题落到可测量的 FL 结果：窗口是否完成，模型是否持续推进，客户端是否被重复纳入，配置变化增加了多少延迟和状态。密码学组件提供真实保护路径和成本数据，研究叙事保持在动态异步 FL 系统。

## 15. Open decisions before live training

1. 选择 FLSim 客户端事件调度的具体桥接方式，是复用 `AsyncTrainingSimulator` 并替换 job scheduler，还是直接调用 `AsyncClientDevice` 并由本文调度器安排完成事件。
2. 第一版 P0 先使用抽象的聚合阈值共享状态验证窗口交接；随后接入 PVSS 保护插件。Buffalo 保持外部基线，不直接承担本文的委员会状态迁移。
3. 确定 CIFAR-10 的窗口大小和客户端速度分布，并将其写入固定配置文件。
4. 在 Buffalo-native 原生结果复现后，再决定 Buffalo-reset 是否进入主表还是放入敏感性分析。

## 16. 当前代码决策

第一步直接扩展 `experiments/reconfigurable_fl_sim.py`。其中的 `Simulator` 已经承担窗口服务职责，当前阶段保持这个结构，先补齐统一结果字段、接收截点、保护上下文版本和 epoch 事件。现在拆出独立服务包会增加接口数量，却不会增加实验信息。

第二步把 `experiments/generate_reconfigurable_trace.py` 作为唯一轨迹入口。每条轨迹同时包含客户端完成、配置变更、节点状态和迟到消息事件。四种策略读取同一份轨迹，结果写入同一组字段。轨迹生成器补充活动窗口跨 epoch、控制节点集合、交接上下文版本和接收截点之后到达的旧上下文更新。

第三步加入一个很薄的训练适配器，建议先放在 `experiments/adapters/`：

```text
common_records.py       ClientUpdate and AggregateResult
flsim_adapter.py        FLSim training events to ClientUpdate
buffalo_adapter.py      Buffalo protected payload and cost counters
```

适配器只转换事件和记录，不复制窗口状态机。窗口状态仍由 `Simulator` 或其后续的同一实现维护。这样明文训练和受保护训练共享窗口归属、交接和封存规则，实验结果可以逐层对照。

Phase 0 的完成条件是同一轨迹在四种策略下可重复运行，并输出有效更新序列、模型版本序列、封存后拒绝数、重开实例数、交接阶段、保护上下文版本、交接延迟和状态字节。Phase 1 的完成条件是 FLSim 产生的真实更新可以经过同一窗口服务，模型可以按已完成聚合继续推进。Phase 2 再接入 PVSS 保护插件和 Buffalo 外部基线，避免把训练事件、成员变化和密码学调试混在一个故障中。

暂时不加入网络 RPC、分布式进程和完整阈值密码学实现。当前论文问题首先需要可重放的成员变化和训练轨迹，事件模拟器足以验证这部分性质。端到端多进程实验在窗口规则稳定、基线适配完成后再投入。

## 17. Code construction blueprint

本节是实现前的代码构建方案，暂不新增代码。目标是让实现可以从当前回放器逐步扩展，同时保持协议状态、训练状态和密码学状态的边界清晰。

### 17.1 Planned modules

后续代码按职责组织为以下最小模块：

```text
experiments/
  records.py                 # unified event and result records
  trace_io.py                # deterministic trace loading and validation
  window_service.py          # window ownership, frontier, and finality
  reconfiguration_policy.py  # Static, Full-transfer, Periodic-rekey, P0
  protection_backend.py      # backend contract only
  abstract_backend.py        # state-size and transition model
  training_adapter.py        # training framework events to ClientUpdate
  metrics.py                 # derived training and handoff metrics
  run_replay.py              # one trace, one policy, one result bundle
adapters/
  flsim_adapter.py
  buffalo_adapter.py
```

这是一份目标结构，不要求一次性建立所有文件。当前 `reconfigurable_fl_sim.py` 继续作为回放器，直到 `records.py` 和 `window_service.py` 的职责可以从现有字段中直接抽取。保护后端不读取窗口服务的内部状态，窗口服务也不调用具体密码学库的内部函数。

### 17.2 Common records

四类记录是所有实验路径的共同输入输出：

```text
ClientUpdate(
    update_id, client_id, sid, source_sid,
    base_model_version, local_steps, sample_weight,
    protection_context, payload, arrival_order
)

LiveWindow(
    sid, base_model_version, owner_configuration, generation,
    accepted_update_ids, frontier, status,
    protected_state_ref, handoff_status
)

ConfigurationEvent(
    order, kind, configuration, predecessor,
    affected_clients, affected_nodes, effective_boundary,
    transition_certificate
)

AggregateResult(
    sid, model_version, accepted_update_ids,
    accepted_client_ids, aggregate_payload,
    owner_configuration, generation, final_status
)
```

`payload` 可以是明文向量、抽象状态引用或受保护载荷。窗口服务只读取后端返回的验证结果和聚合结果，不读取客户端明文。`source_sid` 只用于记录迟到更新的重新提交来源，不能让旧实例恢复写入权。

### 17.3 Backend contract

保护后端先用文档和抽象测试固定接口，再实现具体算法：

```text
setup_context(configuration, sid, generation, members, threshold)
protect_update(update, context)
accumulate(state, protected_update)
export_live_state(state, frontier)
reshare_live_state(record, successor_context)
install_live_state(record, successor_context)
authorize_open(state)
partial_open(state, aggregate_open_certificate, member)
combine_open(partial_openings, aggregate_open_certificate)
seal(state)
erase(state)
```

接口约束如下：

| 操作 | 必须保持的语义 | 不负责的内容 |
|---|---|---|
| `protect_update` | 生成绑定 `sid`、代数和保护上下文的载荷 | 客户端是否有资格提交 |
| `accumulate` | 每个 `update_id` 至多累加一次 | 决定 frontier |
| `export_live_state` | 输出当前聚合状态和已接受更新摘要 | 生成后继配置 |
| `reshare_live_state` | 逻辑聚合值不变，份额上下文改变 | 接受新客户端更新 |
| `install_live_state` | 只安装更高代数且有效的状态 | 删除旧状态 |
| `authorize_open` / `partial_open` / `combine_open` | 只释放绑定最终状态的聚合结果 | 释放单客户端更新或接受未授权的密文集合 |
| `erase` | 清除可写份额和恢复材料 | 发布模型结果 |

抽象后端先返回状态大小、状态版本和结果摘要，不声称提供密码学安全。真实后端接入时，必须用同一组接口测试 `sid`、配置编号、代数和封存边界。

### 17.4 Window service contract

窗口服务保留唯一的训练语义：

```text
open_window(model_version, configuration)
admit_update(update)
freeze_window(sid, frontier)
handoff_window(sid, successor_configuration)
confirm_handoff(sid, installation_certificate)
finalize_window(sid)
route_late_update(update)
recover_window(record)
```

服务必须能够回答四个问题：更新是否已经进入 `frontier`，当前唯一写入配置是谁，更新是否需要重新提交，窗口是否已经封存。保护后端只提供对应操作，不改变这些答案。

### 17.5 Build phases and gates

代码按以下顺序构建，每一阶段都有独立的停止条件：

| 阶段 | 实现内容 | 进入下一阶段的条件 |
|---|---|---|
| A | 当前回放器验证四类策略和成员轨迹 | 同一轨迹得到稳定的状态路径和统一结果字段 |
| B | 从 FLSim 接收真实训练完成事件 | 模型版本、陈旧度和已接受更新集合可重放 |
| C | 抽象后端接入窗口服务 | 交接前后聚合状态摘要一致，封存后无可写状态 |
| D | 系数域阈值保护适配 | 系数加密、密文聚合、窗口密钥重分享和有界开启可分开计量 |
| E | 外部基线和故障组合 | 所有主表结果使用同一 workload 和事件轨迹 |

阶段 C 是本文方案的最小可复现实验闭环。阶段 D 才引入真实密码学，避免在状态语义仍变化时调试底层保护实现。

### 17.6 Baseline modification boundary

基线改动保持在适配层：

| 基线 | 允许的适配 | 不允许的改动 |
|---|---|---|
| Buffalo native | 记录提交、缓冲完成和保护开销 | 修改原生 assistant 或声称支持本文交接 |
| Buffalo reset | 在配置变化时重启外部运行实例 | 将重启包装描述为原生能力 |
| FedBuff/FLSim | 转换训练事件和模型结果 | 修改异步聚合算法 |
| Flower SecAgg+ | 统一数据、模型和结果日志 | 把同步轮次改成异步委员会方案 |
| Catalyst | 记录 Byzantine 更新筛选和模型质量 | 把鲁棒聚合结果当作隐私终结结果 |
| Setup Once native | 记录动态客户端参与和 setup 成本 | 添加动态委员会逻辑后仍使用原项目名称 |

本文的 `P0`、`Static`、`Full-transfer` 和 `Periodic-rekey` 使用同一窗口服务，只切换交接策略；它们是内部策略对照，不是四份独立系统实现。

### 17.7 Required checks before live training

在接入真实训练前，只检查与论文主张直接相关的状态性质：

```text
same update_id is accepted at most once
frontier is monotone
generation never decreases
only the current owner accepts writes
old-context updates are rejected after freeze
handoff failure preserves one recoverable owner
sealed windows accept no state-changing message
sealed records contain no writable protection state
```

这些检查可以由确定性轨迹和结果日志完成，不需要先构建多进程网络。真实训练接入后再增加模型质量、陈旧度和吞吐指标；密码学后端接入后再增加保护时间、开启时间和清除时间。

### 17.8 Reproducible result bundle

每次运行只产生一个自包含结果目录：

```text
results/<baseline>/<trace_id>/<seed>/
  manifest.json
  events.csv
  window_results.csv
  configuration_results.csv
  training_metrics.csv
  protection_metrics.csv
  stdout.log
```

`manifest.json` 记录代码版本、上游基线版本、数据集、模型、轨迹、随机种子和命令行。原始日志与派生图表分开保存。这样可以在不重新运行密码学后端的情况下复算窗口完成率、交接代价和模型陈旧度。

### 17.9 Current implementation decision

本轮只冻结接口和构建顺序，不实现新的 Python 模块，不引入 RPC、进程编排或密码学依赖。下一次代码工作从阶段 A 的结果字段审计开始；阶段 A 通过后，才抽取窗口服务和训练适配器。真实保护后端采用 RLWE 系数域阈值 ElGamal 和活动窗口密钥重分享，Buffalo 原生运行作为固定委员会性能基线。

## 18. Phase A audit of the current replayer

本轮使用带成员事件的轨迹运行现有回放器：输入包含 90 条事件，输出 44 个窗口记录，四类窗口策略均能生成结果文件。这证明当前入口、轨迹格式和基本交接路径可以运行，但还不足以支撑论文中的全部不变量。

| 需要验证的性质 | 当前已有证据 | 当前缺口 | 实现前必须冻结的字段 |
|---|---|---|---|
| 更新至多纳入一次 | `accepted_clients` 能发现同一客户端的重复纳入 | 没有独立 `update_id`，同一客户端的两次合法更新无法区分 | `update_id`、`accepted_update_ids`、逐事件 admission log |
| `frontier` 单调 | 记录了 `frontier_record_version` | 当前 `record_version` 不随更新纳入递增，所有更新可能共享版本 `1` | `record_version`、`frontier_update_ids`、frontier 形成事件 |
| 唯一写入者 | 输出 `owner_configuration` 和 `handoff_status` | 没有记录每次写入尝试及旧配置被拒绝的原因 | `writer_configuration`、`owner_history`、`write_rejection_reason` |
| 代数不回退 | 输出 `generation` 和保护上下文 | 缺少旧代数确认、恢复和重复安装的专门事件 | `source_generation`、`target_generation`、安装拒绝原因 |
| 交接失败可恢复 | 交接状态可以停留在 `exported` 或 `installed` | 没有明确的失败确认事件和旧状态保留证明 | `handoff_attempt_id`、`handoff_failure_reason`、`recoverable_owner` |
| 旧状态已擦除 | 抽象后端内部将阶段置为 `erased` | 回放结果看不到擦除收据，无法区分 sealed bytes 与 writable bytes | `erase_status`、`erase_order`、`writable_state_bytes`、`erase_receipt` |
| 封存后不可变 | `final_status`、拒绝计数和封存记录大小可见 | 拒绝计数没有区分迟到更新、恢复请求和旧交接 | `rejection_reason`、`sealed_state_bytes`、`state_change_after_seal` |
| 重新提交可追踪 | `resubmitted_updates` 和 `source_window` 可见 | 没有原始更新标识、是否复用训练结果以及模型版本兼容结果 | `source_update_id`、`resubmission_mode`、`retrained`、`base_model_version` |

当前抽象后端也有两个需要在真实实现前固定的语义：`HandoffRecord` 必须只能被一个后继配置安装，不能被重复重分享；`seal` 之后的活动状态大小应当归零或明确标记为不可写，不能继续用活动状态大小表示封存记录。微基准输出应分别报告 `live_state_bytes_before_seal`、`sealed_record_bytes` 和 `erased_state_bytes`。

## 19. Phase A data contract and build gate

阶段 A 先冻结记录格式，再修改回放逻辑。下一轮允许新增字段和校验，不引入真实密码学、RPC 或训练框架依赖。

### 19.1 Trace fields

轨迹事件在现有字段之外增加：

```text
update_id
source_update_id
source_generation
target_generation
handoff_attempt_id
retrained
```

`update_id` 唯一标识一次提交；重新保护同一训练结果时产生新的目标提交标识，通过 `source_update_id` 关联未纳入的源提交。`retrained=true` 表示客户端重新下载模型后产生了新的训练结果，与简单的重新保护分开。拒绝原因由窗口服务输出，不由轨迹输入决定；最终 CSV 列序和默认值见第 24.1 节。

### 19.2 Window result fields

每个窗口结果增加：

```text
accepted_update_ids
frontier_update_ids
owner_history
write_attempts
write_rejections
handoff_attempts
handoff_failures
recoverable_owner
erase_status
erase_order
sealed_state_bytes
state_change_after_seal
```

这些字段服务于论文中的状态性质，不是密码学实现的内部调试信息。保护后端只需要返回状态阶段、状态大小和擦除回执；窗口服务负责把它们与事件序列对应起来。

### 19.3 Replay assertions

阶段 A 的回放验收固定为以下断言：

```text
each update_id enters at most one accepted set
frontier_update_ids equals the accepted-update snapshot at freeze
accepted_update_log has frontier as an order-preserving prefix
writer_configuration changes only after a valid retirement receipt
generation strictly increases on every successful handoff
failed handoff leaves exactly one recoverable owner
old-generation writes are rejected after installation
sealed windows have zero state-changing admissions
erase_receipt exists before successor admission or opening resumes
resubmission records preserve source_update_id and model compatibility
```

断言失败时先修正记录和状态语义，不进入 FLSim 或 Buffalo 适配。阶段 A 通过的证据是一组可重放轨迹及其逐事件日志，而不是单个最终 CSV 中没有明显异常。

### 19.4 Next implementation order

下一轮代码工作的最小顺序为：

1. 给轨迹和结果记录补上 `update_id`、状态版本和拒绝原因；
2. 将每次状态变化写入逐事件日志，并从日志派生最终结果；
3. 回放 `phase-a-traces/` 中的四条确定性轨迹；
4. 用抽象后端验证安装唯一性、擦除收据和封存状态大小；
5. 通过阶段 A 后再抽取 `window_service.py` 和 `training_adapter.py`。

这一步完成前不接入真实训练。否则模型质量结果会掩盖窗口归属和状态清除语义中的缺口。

## 21. Interface call graph and failure semantics

阶段 A 通过后，阶段 C 的实现必须按以下调用图组织。它把窗口服务作为唯一状态裁决点，保护后端只处理受保护状态。

```text
client/training adapter
    -> ClientUpdate
    -> WindowService.preflight
       -> ProtectionBackend.verify
       -> ProtectionBackend.accumulate
    -> WindowService.commit_admission
    -> EventLog

configuration service
    -> WindowService.freeze
    -> ProtectionBackend.export
    -> ProtectionBackend.reshare
    -> ProtectionBackend.install(staged)
    -> WindowService.confirm
    -> ProtectionBackend.erase(source)
    -> EventLog

WindowService.finalize
    -> ProtectionBackend.authorize_open
    -> ProtectionBackend.partial_open
    -> ProtectionBackend.combine_open
    -> sealed record publication
    -> ProtectionBackend.seal
    -> ProtectionBackend.erase
    -> EventLog
```

封存发布和后端清除之间记录 `seal_pending`。此状态表示聚合结果已经固定，窗口不再接受任何更新、恢复或交接，但活动保护材料尚未得到擦除回执。只有 `erase_receipt` 写入日志后，摘要才变为 `sealed`；擦除失败不允许回退为活动窗口，也不允许后继配置恢复该实例。

### 21.1 Ownership of decisions

| 决定 | 唯一负责模块 | 后端可见输入 | 后端不能改变 |
|---|---|---|---|
| 客户端是否有资格提交 | 窗口服务 | 更新元数据 | 资格、模型版本和配置归属 |
| 更新是否进入窗口 | 窗口服务与后端原子协作 | `update_id`、保护载荷 | frontier 和所有者 |
| 是否冻结窗口 | 窗口服务 | 当前记录版本 | 冻结边界 |
| 是否安装后继状态 | 窗口服务验证后端证明 | 交接记录、代数、摘要 | `owner_configuration` |
| 何时切换所有者 | 窗口服务 | 安装确认及源状态退役回执 | 旧状态清除顺序 |
| 是否封存窗口 | 窗口服务 | 聚合结果和完成条件 | 封存边界 |
| 何时清除状态 | 后端执行，服务确认 | `erase_token` | 封存结果和所有者历史 |

### 21.2 Idempotency tokens

所有可能重试的操作都绑定唯一标识：

```text
admission_token = (sid, update_id, generation)
handoff_token   = (sid, source_generation, target_generation,
                   successor_configuration, handoff_attempt_id)
install_token   = handoff_token
erase_token     = (sid, generation, owner_configuration, erase_order)
seal_token      = (sid, generation, result_id)
```

重复请求必须返回第一次请求的结果，不得再次累加、再次安装、再次切换 owner 或生成第二份封存记录。阶段 A 日志应把 token 和结果同时保存，以便区分合法重试与重复状态改变。

### 21.3 Failure semantics for the implementation plan

实现计划采用以下状态原则：

```text
preflight failure      -> no backend mutation
accumulate failure     -> no admission commit
handoff export failure -> source remains recoverable
reshare failure        -> no successor install
install failure        -> owner remains unchanged
confirm failure        -> staged successor is unusable
handoff erase failure  -> source remains recovery owner; successor waits
final erase failure    -> committed result remains fixed; seal_pending is recorded
open wait              -> opening uses the same certificate until sufficient partials arrive
seal publication fail  -> result is retryable; no new update is admitted
```

其中 `erase_pending` 必须成为显式结果，而不是把安装确认直接解释为隐私终结。移动敌手实验需要单独注入“安装成功、旧状态暂未擦除”的窗口，测量该状态的持续时间，并验证服务不会把它误报为已完成清除。

### 21.4 Phase C test matrix

阶段 C 的抽象后端测试按模块边界组织：

| 测试组 | 输入 | 观察量 | 通过条件 |
|---|---|---|---|
| admission | 重复 `update_id`、旧代数、错误模型 | backend mutation、accepted log | 拒绝请求不改变后端状态 |
| handoff | 同一 token 重试、不同目标代数、重复安装 | owner、generation、staged state | 只产生一个可安装后继状态 |
| confirmation | 确认失败、确认重复、确认后旧写入 | owner history、rejection reason | 确认保留源 owner，退役回执触发唯一一次转移 |
| erasure | 安装后擦除成功或延迟 | writable bytes、erase receipt | `erase_pending` 可见，最终旧状态归零 |
| finality | 封存后更新、恢复、交接 | sealed bytes、state changes | 所有改变状态的消息被拒绝 |
| resubmission | 同一训练结果重新保护、重新训练 | source id、retrained、model version | 来源关系清晰，不在旧 sid 重复纳入 |

阶段 C 只使用抽象状态和固定 token。通过后，真实保护后端只需满足同一调用图和结果字段，不得通过改变接口语义降低测试要求。

### 21.5 Transition to live training

FLSim 接入时只实现以下转换：

```text
training_started(model_version)
    -> local training
training_finished(delta, weight, client_model_version)
    -> ClientUpdate(update_id, base_model_version, payload=delta)
WindowService result
    -> accepted / reroute / rejected / committed
committed AggregateResult
    -> global model update and next model snapshot
```

FLSim 提供客户端训练和陈旧度计算，窗口服务决定更新纳入与聚合结果发布。首次 `Commit_sid` 触发一次模型更新；随后 `Seal_sid` 只记录状态清除。读取已封存结果时，按实例标识检查该结果是否已经用于模型更新。`abandoned` 实例没有可发布的聚合结果。

### 21.6 Stop conditions

阶段 C 出现以下任一情况时停止接入真实保护后端：

```text
event log cannot reconstruct owner history
backend mutates on a rejected preflight
same token changes state twice
failed confirmation loses the source state
erase_pending is reported as erased
sealed state accepts a mutation
```

这些停止条件优先于性能优化。只有调用顺序和状态摘要稳定后，实验才有意义地比较 Buffalo、PVSS 或其他后端的开销。

## 22. Final build checklist for phases A-C

本节是当前代码工作的唯一执行清单。它保持“先验证窗口服务语义，再接入真实训练，最后接入保护后端”的顺序。阶段之间不共享未通过验收的状态假设。

### 22.1 Phase A: trace and service semantics

**输入**

```text
 A1-handoff-failure.csv
 A2-stale-generation.csv
 A3-sealed-rejection.csv
 A4-handoff-abandon.csv
四类窗口策略的同一轨迹副本
```

**需要构建的部分**

```text
TraceEvent fields
Window ownership and generation fields
per-event EventResult
window summary derivation
rejection reason mapping
```

**必须产生的结果**

```text
results/phase-a/<trace_id>/events.csv
results/phase-a/<trace_id>/window_results.csv
results/phase-a/<trace_id>/manifest.json
```

**验收证据**

```text
accepted_update_log can be replayed exactly
frontier_update_ids equals the freeze snapshot
owner_history has no overlapping writers
generation increases only after valid confirmation
failed confirmation preserves recoverable_owner
seal_pending and sealed reject every state-changing event
```

**停止条件**

```text
summary cannot be derived from event log
old and new owners both accept writes
same update_id or token mutates state twice
failed handoff loses the source state
sealed state changes without a rejection event
```

Phase A 的输出只验证服务语义，不包含模型训练和密码学性能。它通过后，事件记录格式才可作为后续阶段的输入契约。

### 22.2 Phase B: live training bridge

**输入**

```text
Phase A event and result schema
FLSim AsyncClientDevice training events
fixed model, data split, optimizer, and client speed trace
```

**适配器职责**

```text
training_started -> local model snapshot
training_finished -> ClientUpdate
    WindowService result -> accepted / reroute / rejected / committed
committed AggregateResult -> global model update
```

FLSim 只产生本地训练结果、样本权重、模型版本和完成顺序。窗口服务继续拥有窗口纳入、frontier、交接和封存决定权。适配器不调用保护后端的交接或擦除操作。

**必须产生的结果**

```text
results/phase-b/<trace_id>/training_metrics.csv
results/phase-b/<trace_id>/events.csv
results/phase-b/<trace_id>/window_results.csv
```

**验收证据**

```text
same ClientUpdate trace can be replayed from recorded events
accepted model updates match accepted_update_log
model version never rolls back across handoff
reroute distinguishes re-protection from retraining
    committed AggregateResult is the only model-update input
```

**停止条件**

```text
FLSim bypasses WindowService for model updates
model quality depends on an unrecorded admission decision
client model version cannot be reconstructed
rerouted update loses source_update_id or retrained flag
```

Phase B 只证明本文窗口服务可以承接真实异步训练，不声称已经完成安全聚合。

### 22.3 Phase C: abstract protected-state backend

**输入**

```text
Phase A service calls
ClientUpdate payloads from Phase B or synthetic vectors
AbstractThresholdBackend state model
fixed admission, handoff, install, erase, and seal tokens
```

**需要验证的调用顺序**

```text
preflight -> verify -> accumulate -> admission commit
freeze -> export -> reshare -> staged install -> confirm -> erase
open -> result validation -> publish -> seal_pending -> erase -> sealed
```

**必须产生的结果**

```text
results/phase-c/<trace_id>/backend_events.csv
results/phase-c/<trace_id>/state_metrics.csv
results/phase-c/<trace_id>/window_results.csv
```

**验收证据**

```text
rejected preflight causes no backend mutation
same admission or handoff token is idempotent
staged successor is unusable before confirmation
source owner remains recoverable after failed confirmation
erase_pending is visible and not reported as erased
sealed_state_bytes excludes writable state after erase receipt
```

**停止条件**

```text
backend decides eligibility or frontier
backend accepts a state-changing call after seal_pending
install changes owner before service confirmation
erase receipt is missing but state is reported sealed
abstract state summary differs before and after a value-preserving reshare
```

Phase C 是本文方案的最小系统闭环。只有它通过后，才进入阶段 D 的系数域阈值保护实现；阶段 D 不得改变阶段 A-C 的窗口、事件和结果语义。

### 22.4 Phase transition record

每个阶段结束时生成一份简短的 `phase_gate.json`：

```text
phase
input_manifest
output_manifest
passed_assertions
failed_assertions
stop_conditions_triggered
next_phase_approved
```

`next_phase_approved=true` 只能由当前阶段的逐事件日志和结果摘要共同支持。没有该文件，后续阶段只能继续当前阶段的诊断，不能用新的训练或密码学结果掩盖未解决的状态问题。

### 22.5 Planned file ownership

阶段 A 至 C 的目标文件边界固定为：

```text
experiments/records.py                 A: canonical records
experiments/trace_io.py                A: trace validation and replay input
experiments/window_service.py          A/C: service state transitions
experiments/reconfiguration_policy.py A: policy-specific handoff behavior
experiments/protection_backend.py      C: backend contract
experiments/abstract_backend.py        C: abstract state implementation
experiments/metrics.py                 A/B/C: derived metrics
experiments/run_replay.py              A/B/C: reproducible runner
adapters/flsim_adapter.py              B: live training bridge
```

现有 `reconfigurable_fl_sim.py` 在阶段 A 完成前继续作为参考回放器，不同时承担新的记录定义和最终窗口服务。抽取新文件时必须保持旧轨迹可重放，避免一次重构同时改变状态语义和文件结构。

## 23. Phase A work packages

阶段 A 的实现按依赖顺序拆成五个工作包。每个工作包只拥有一类状态，完成后保存独立证据；工作包之间不共享隐藏的可变状态。当前 A0 已由冻结 schema、轨迹生成器和回放器覆盖，后续检查以这套实现为准。

### 23.1 A0: schema freeze

**目标**：把阶段 A 需要的字段定义为不可变记录。

```text
records.py
  TraceEvent
  ClientUpdate
  EventResult
  LiveWindow
  AggregateResult
```

**输入**：`phase-a-traces/` 中四条确定性轨迹、适配规格第 11 节的记录定义。

**输出**：字段列表、默认值规则、枚举值、CSV 列顺序和已冻结的 `phase-a-schema.json`。

**决定项**：以第 24 节的字段及事件约束为 A0 的具体输入。`frontier_update_ids` 固定旧配置前缀，后继配置在同一 `sid` 的新代数下追加后缀；`handoff_confirm` 与旧份额 `erase_receipt` 分开记录。当前轨迹生成器和回放器已经实现这些字段及状态顺序。

**通过条件**：`phase-a-schema.json` 与本节字段、默认值和枚举一致；事件日志和窗口摘要能够引用同一 `update_id`、`handoff_attempt_id`、代数和所有者字段；未定义字段不能静默丢弃。

### 23.2 A1: trace validation

**目标**：验证轨迹本身满足可重放条件。

```text
trace_io.py
  load_trace(path)
  validate_trace(events)
  write_event_log(events)
```

**必须检查**：事件序号严格递增、同一 token 的字段不漂移、目标代数高于源代数、封存后事件携带原因所需字段、`source_update_id` 指向已存在或明确被拒绝的来源。

**停止条件**：轨迹无法唯一确定事件顺序，或同一 token 对应多个目标配置。此时修改轨迹规格，不在服务层猜测。

### 23.3 A2: window service state

**目标**：实现窗口服务的状态转移，不调用真实后端。

```text
window_service.py
  preflight(update)
  freeze_window(sid, handoff_token)
  validate_installation(record)
  confirm_handoff(token)
  finalize_result(result)
  route_late_update(update)
```

服务内部至少分开保存 `active_configuration`、`owner_configuration`、`recoverable_owner`、`generation`、`handoff_status` 和 `erase_status`。服务可以返回后端操作所需的意图，但不直接修改后端状态。成功交接后的未完成窗口须在收到旧份额擦除回执后重新纳入客户端更新。

**通过条件**：A1 至 A4 的逐事件结果与预期状态表一致；旧配置仅能恢复冻结状态，不能继续接受新写入；放弃实例拒绝后续写入和恢复。

### 23.4 A3: policy isolation

**目标**：把四类窗口策略限制为同一服务上的策略差异。

```text
reconfiguration_policy.py
  Static
  FullTransfer
  PeriodicRekey
  SelectiveFinality
```

策略只决定配置变化时哪些窗口进入冻结、转移或等待；不重新实现客户端资格、代数验证、封存拒绝和日志记录。四类策略必须读取相同的事件日志输入。

**通过条件**：在相同轨迹下，四类策略的差异只出现在定义好的交接行为和对应指标中；拒绝原因枚举和记录字段保持相同。

### 23.5 A4: summary and gate

**目标**：从事件日志派生窗口摘要并生成阶段门禁文件。

```text
metrics.py
  derive_window_results(event_log)
  derive_configuration_results(event_log)
  check_phase_a_assertions(event_log, summaries)

run_replay.py
  run_phase_a(trace, policy)
  write_phase_gate(...)
```

`window_results.csv` 不允许由服务状态直接单独写出；它必须由 `events.csv` 重放得到。`phase_gate.json` 必须包含 `passed_assertions`、`failed_assertions` 和 `next_phase_approved`，否则阶段 B 不得读取该结果目录。

### 23.6 A work-package order

```text
A0 schema freeze
    -> A1 trace validation
    -> A2 window service state
    -> A3 policy isolation
    -> A4 summary and gate
```

A0 和 A1 不依赖保护后端；A2 只依赖记录和事件；A3 依赖 A2；A4 依赖前三者。任何工作包失败都回到其直接前置包处理，不跨阶段修补结果文件。

### 23.7 Phase A handoff to Phase B

阶段 A 向阶段 B 只交付以下内容：

```text
phase-a-schema.json
trace manifest
event/result column definitions
passed phase_gate.json
window service admission and finality contract
```

阶段 B 不继承阶段 A 的 Python 对象或内存状态，只读取记录契约和服务接口。这样真实训练适配器不能通过复用旧模拟器内部字段绕过阶段 A 的验收。

## 20. Deterministic Phase A traces

阶段 A 固定四条最小轨迹，验证配置代数、唯一写入权、结果固定和实例放弃。前三条以一个活动实例 `sid-0` 为主，第四条增加重提实例和独立实例。CSV 位于 `experiments/phase-a-traces/`，逐事件结果由回放器生成。

### 20.1 Handoff confirmation failure and recovery

这条轨迹检验安装确认失败时系统是否保留旧配置的唯一恢复来源。失败确认不能产生后继可写副本；旧配置恢复成功后可以重试同一个交接。

```text
1  client_update   C0 sid-0 u0 gen=0 update=u0
2  client_update   C0 sid-0 u1 gen=0 update=u1
3  config_install  C1                  transition=h1
4  recover_state   C1 sid-0 p1 target_gen=1 attempt=h1 delivered=true
5  handoff_confirm C1 sid-0 delivered=false attempt=h1
6  client_update   C0 sid-0 u2 gen=0 update=u2
7  recover_state   C0 sid-0 p0 gen=0 attempt=h1 delivered=true
8  recover_state   C1 sid-0 p1 target_gen=1 attempt=h1 delivered=true
9  handoff_confirm C1 sid-0 delivered=true attempt=h1 target_gen=1
10 erase_receipt   C0 sid-0 attempt=h1 source_gen=0
11 client_update   C1 sid-0 u3 gen=1 update=u3
12 window_finalize C1 sid-0
13 erase_receipt   C1 sid-0 source_gen=1
```

预期状态如下：

```text
after 3:  owner=C0, frontier={u0,u1}, handoff_status=handoff_pending
after 4:  C1 has only staged state; owner=C0
after 5:  owner=C0, recoverable_owner=C0, generation=0
after 6:  u2 is rejected as an old-context write after freeze
after 7:  C0 remains the only recoverable owner
after 8:  C1 restages the same attempt; owner=C0
after 9:  handoff confirmed; owner=C0, generation=0, admission remains paused
after 10: old shares cleared; owner=C1, generation=1, C1 may admit to sid-0
after 11: u3 is accepted only under C1 and generation=1
after 12: sid-0 becomes seal_pending
after 13: sid-0 becomes sealed
```

验收重点是：失败确认不改变 `owner_configuration`；恢复请求不能创建第二个副本；同一个 `handoff_attempt_id` 可以重试，但成功确认只发生一次；旧份额擦除晚于安装确认、早于 `sid-0` 恢复接收。例中最低参与数设为 3，旧前缀只有 2 个更新，后继更新 `u3` 必须进入同一个实例才能完成聚合。

### 20.2 Stale-generation installation rejection

这条轨迹检验后继配置安装后，旧代数的恢复材料、重复安装和旧配置写入是否全部失效。`handoff_confirm` 只完成后继状态安装确认；在旧份额清除前，`C0` 仍是恢复来源，`C1` 不能写入。

```text
1  client_update   C0 sid-0 u0 gen=0 update=u0
2  config_install  C1                  transition=h1
3  recover_state   C1 sid-0 p1 gen=0 attempt=h1 target_gen=1 (stale record)
4  handoff_confirm C1 sid-0 gen=0 delivered=true attempt=h1
5  recover_state   C1 sid-0 p1 source_gen=0 attempt=h1 target_gen=1 (valid record)
6  handoff_confirm C1 sid-0 gen=1 delivered=true attempt=h1
7  erase_receipt   C0 sid-0 attempt=h1 source_gen=0
8  client_update   C0 sid-0 u1 gen=0 update=u1
9  client_update   C1 sid-0 u2 gen=1 update=u2
10 client_update   C1 sid-0 u3 gen=1 update=u3
11 window_finalize C1 sid-0
12 erase_receipt   C1 sid-0 source_gen=1
```

预期状态如下：

```text
after 3:  stale recovery is rejected; owner remains C0
after 4:  stale confirmation is rejected; generation remains 0
after 6:  one valid confirmation installs the successor state; owner remains C0 and generation remains 0
after 7:  old shares are cleared, then generation=1 and owner=C1 become writable
after 8:  old-generation write is rejected
after 9-10: u2 and u3 enter the C1 accepted-update log
after 11: fixed result contains u0,u2,u3, never u1; status=seal_pending
after 12: status=sealed
```

验收重点是：代数严格递增；同一安装尝试不能被重复确认；旧代数恢复和写入分别产生拒绝原因；`owner_history` 不出现重叠的可写配置；`accepted_update_log` 不包含被拒绝的 `u1`。

### 20.3 Sealed-window late message and recovery rejection

这条轨迹检验封存记录的吸收性。封存之后同时到达旧上下文更新、迟到交接消息和恢复请求，三者都只能产生拒绝记录。

```text
1  client_update   C0 sid-0 u0 gen=0 update=u0
2  client_update   C0 sid-0 u2 gen=0 update=u2
3  config_install  C1                  transition=h1
4  recover_state   C1 sid-0 p1 source_gen=0 attempt=h1 target_gen=1
5  handoff_confirm C1 sid-0 gen=1 delivered=true attempt=h1
6  erase_receipt   C0 sid-0 attempt=h1 source_gen=0
7  window_finalize C1 sid-0
8  erase_receipt   C1 sid-0 source_gen=1
9  client_update   C0 sid-0 u1 gen=0 update=u1
10 message_deliver C1 sid-0 gen=0 attempt=h1 delivered=true
11 recover_state   C1 sid-0 p1 gen=1 attempt=h1 delivered=true
12 client_resubmit C1 sid-1 source=sid-0 source_update=u1
```

预期状态如下：

```text
after 7:  sid-0 is seal_pending and its result is fixed
after 8:  sid-0 is sealed; sealed_state_bytes is fixed
after 9:  old-context update is rejected
after 10: stale handoff is rejected
after 11: recovery of sealed sid-0 is rejected
after 12: only a separately valid sid-1 may accept a resubmission
```

如果 `sid-1` 没有当前模型版本或客户端资格，事件 12 也必须被拒绝；无论事件 9 至 12 的顺序如何，`sid-0` 的参与集合、结果版本、`sealed_state_bytes` 和 `state_change_after_seal` 都保持不变。该轨迹直接对应封存不可变和封存后状态排除两个验收条件。

### 20.4 Trace outputs

四条轨迹都输出逐事件日志和窗口摘要。摘要至少包含：

```text
trace_id
event_order
sid
update_id
source_update_id
event_result
rejection_reason
owner_configuration
generation
handoff_status
recoverable_owner
erase_status
state_bytes
state_change_after_seal
```

阶段 A 只接受同时满足以下条件的实现：

1. 第一条轨迹中确认失败不丢失旧状态，成功重试后只有 `C1` 可写；
2. 第二条轨迹中任何旧代数操作都不能改变 `C1` 的状态；
3. 第三条轨迹中封存后的状态摘要逐事件保持不变；
4. 四条轨迹的拒绝原因足以区分旧配置写入、旧代数恢复、重复确认、封存后恢复和放弃实例写入；
5. 每个 `update_id`、`source_update_id` 和 `handoff_attempt_id` 可以从最终摘要追溯到原始事件。

这四条轨迹通过后，再把同样的事件序列映射到 FLSim 的训练完成事件。真实训练只替换 `ClientUpdate.payload` 和模型更新，不改变轨迹的状态断言。

### 20.5 Current replayer versus target semantics

当前回放器已把全局当前配置和活动实例恢复所有者分开处理。配置安装后新配置可以创建新实例；在 `handoff_confirm` 失败时，旧配置仍可恢复同一交接尝试，且不会获得新的客户端写入资格。

实现时将“全局当前配置”和“窗口写入所有者”分开保存：

```text
active_configuration:      新配置可以创建的新实例配置
window.owner_configuration: 当前 sid 的唯一可写或可恢复配置
handoff_status:            owned, handoff_pending, installed, confirmed,
                           seal_pending, sealed
recoverable_owner:         失败交接时仍可使用的配置
```

因此 `C1` 可以在 A1 中创建新的实例，而 `sid-0` 在确认失败时仍由 `C0` 恢复。`handoff_confirm` 到达后仍由 `C0` 保留恢复权；只有 `C0` 返回有效退役回执后，`sid-0.owner_configuration` 才改变为 `C1`。这一区分是动态异步训练连续性和单写入权同时成立的必要条件。

### 20.6 Rejection reason vocabulary

拒绝原因使用固定枚举，避免不同基线用不同文字掩盖同一状态：

```text
client_ineligible
duplicate_update
wrong_model_version
old_configuration
old_generation
frontier_closed
handoff_not_installed
duplicate_handoff_confirmation
sealed_window
stale_record
unavailable_owner
invalid_transition
```

`old_configuration` 表示消息的配置不是该窗口当前允许的配置；`old_generation` 表示配置正确但保护状态代数过旧；`frontier_closed` 表示消息属于接收截点之后的旧上下文；`sealed_window` 表示消息试图改变已封存实例。实现和论文表格都使用这组含义。

### 20.7 Expected state table for A1

| 事件范围 | `sid-0.owner` | `sid-0.recoverable_owner` | `generation` | `sid-0` 是否可写 |
|---|---|---|---:|---|
| 事件 1 至 2 | `C0` | `C0` | 0 | `C0` |
| 事件 3 至 8 | `C0` | `C0` | 0 | 冻结；只有 `C0` 可恢复，不接收新写入 |
| 事件 9 | `C0` | `C0` | 0 | 等待旧份额清除 |
| 事件 10 至 11 | `C1` | `C1` | 1 | `C1` 可继续填充 `sid-0` |
| 事件 12 | `C1` | 无活动状态 | 1 | `seal_pending` |
| 事件 13 | `C1` | 无活动状态 | 1 | `sealed` |

表中“仅可恢复”表示旧状态可以用于完成交接或恢复已接受聚合，不表示旧配置可以继续接受新客户端更新。这样 `recoverable_owner` 和 `writer_configuration` 的含义不会混淆。

## 24. A0 字段契约与活动实例续收

此前阶段 A 轨迹主要检验封存和配置权属。论文的训练连续性还需要直接检验**未满额活动实例在换委员会后继续填充**。以下为记录契约，当前实现范围见第 24.7 节。

### 24.1 最小记录与 CSV 顺序

| 记录 | 字段顺序（从左到右） | 缺省与作用 |
|---|---|---|
| `TraceEvent` | `order,kind,configuration,window,model_version,client,node,record_version,protection_context,source_window,delivered,update_id,source_update_id,source_generation,target_generation,handoff_attempt_id,retrained` | 保留原有 11 列；后 6 列为空表示不适用，`retrained` 缺省 `false`；`delivered` 缺省 `true`，均只接受布尔字面值。原有标识列为空按缺失处理。`rejection_reason` 是输出，不作为输入。 |
| `ClientUpdate` | `update_id,client_id,sid,source_sid,source_update_id,base_model_version,generation,protection_context,payload,arrival_order,retrained` | `source_*` 在新训练结果首次提交时为空；`payload` 在阶段 A 是不含明文模型的标记。 |
| `EventResult` | `order,kind,sid,event_result,rejection_reason,update_id,source_update_id,owner_configuration,recoverable_owner,generation,handoff_status,erase_status,accepted_update_ids,frontier_update_ids` | 一条输入对应一条结果，拒绝时填固定枚举，接受时原因留空；集合保留服务接收顺序。 |
| `LiveWindow` | `sid,base_model_version,owner_configuration,recoverable_owner,generation,record_version,accepted_update_log,frontier_update_ids,handoff_attempt_id,handoff_status,erase_status` | `active_configuration` 属于服务全局配置，不复制进每个窗口；新窗口 `generation=0`、`record_version=0`、两条更新序列为空、`handoff_status=owned`、`erase_status=initial`。 |
| `AggregateResult` | `sid,model_version,accepted_update_ids,owner_configuration,generation,final_status,completion_order,sealed_state_bytes` | `final_status=committed` 表示结果已固定，`sealed` 表示可写状态已退役；`abandoned` 不进入全局模型推进。 |

`record_version` 每次成功纳入递增，冻结只保存当时的快照；交接成功递增 `generation`，不改变冻结快照。`update_id` 是一次训练结果的稳定标识：重新保护同一结果时保留一个 `training_result_id`（阶段 A 可用最初 `update_id` 表示），生成新的提交标识并通过 `source_update_id` 关联。被接受的提交及其重提后代只能有一个进入任一实例；重新训练得到新训练结果。日志读取旧轨迹时缺少新列应当显式标记为旧版本，不能默默产生“通过 A0”结论。

阶段 A 的 `erase_receipt` 由交接旧配置或封存配置产生，绑定 `window, configuration, source_generation, handoff_attempt_id`（封存时交接标识为空）。它模拟诚实节点按协议完成清除的回执；真实隐私结论仍依赖腐蚀上限和清除假设。`erase_status` 取 `initial, pending, erased`；`event_result` 取 `accepted, rejected, pending, duplicate`；`handoff_status` 取 `owned, handoff_pending, installed, confirmed, seal_pending, sealed, abandoned`。`handoff_abandon` 终止该实例的写入和恢复，合格更新可请求在新实例重新提交。确认后、退役前，后继配置提交返回 `pending / handoff_not_installed`，接受集合保持不变；此处的原因枚举同时表示写入资格尚未转移。

### 24.2 T7 轨迹：未满缓冲区跨配置继续填充

设最低聚合参与数为 3，事件顺序如下。前两次更新已经由 `C0` 接受；`C1` 在配置安装后能打开其他新窗口，但 `sid-0` 在旧份额擦除前暂不接收更新。

```text
1 client_update   C0 sid-0 u0 update=m0 gen=0                 -> accepted
2 client_update   C0 sid-0 u1 update=m1 gen=0                 -> accepted
3 config_install  C1                                          -> frontier=[m0,m1]
4 recover_state   C1 sid-0 attempt=h1 target_gen=1             -> accepted (staged)
5 handoff_confirm C1 sid-0 attempt=h1 target_gen=1            -> accepted
6 client_update   C1 sid-0 u2 update=m2 gen=1                 -> pending
7 erase_receipt   C0 sid-0 attempt=h1 source_gen=0             -> accepted
8 client_update   C1 sid-0 u2 update=m2 gen=1                 -> accepted
9 window_finalize C1 sid-0                                    -> result=[m0,m1,m2]
10 erase_receipt  C1 sid-0 source_gen=1                        -> sealed
```

事件 6 的原更新标识在事件 8 重试，必须累加一次；事件 8 保留 `frontier=[m0,m1]`，接受日志变为 `[m0,m1,m2]`。事件 9 发布的结果必须有至少 3 名参与者，进入 `seal_pending`；事件 10 才进入 `sealed`。成功轨迹证明服务续收语义；真实密文兼容和擦除成本留待阶段 D 验证。另跑同一轨迹但删除事件 7，预期 `sid-0` 始终不能接收事件 8 或最终发布，这一对照单独报告交接等待对吞吐和陈旧度的影响。

### 24.3 保护后端能力门槛

阶段 C 的抽象后端检查 `frontier` 前缀保持、代数递增、回执前暂停接收、回执后续收和唯一发布，不能据此宣称真实密码学安全。阶段 D 沿用 Buffalo 的 RLWE 向量保护，在 NTT 之前导出有界密钥系数，并用活动窗口的阈值 ElGamal 公钥逐项加密。委员会只重分享窗口解密秘密的曲线标量份额；旧前缀密文和后继提交密文在同一 `PK_sid` 下相加。

阶段 D 的组件验证矩阵如下：

| 组件 | 真实输入 | 正确性检查 | 主要测量 | 通过条件 |
|---|---|---|---|---|
| RLWE 系数导出与导入 | Buffalo 方差 `8` 的密钥和真实模型维度 | `NTT(sum a_u)` 与原生密钥求和解密结果一致 | 转换时间、系数范围 | 所有系数满足配置上界，聚合解密逐项一致 |
| 阈值 ElGamal 系数保护 | `m` 个系数，缓冲上限 `B_max` | 密文相加后得到 `sum a_u,j * G` | 客户端时间、字节数、部分解密时间 | 异步到达顺序不改变结果 |
| 有界点表解码 | 区间 `[-B_max rho,B_max rho]` | 解码值等于明文系数和 | 建表时间、内存、单点查询时间 | 全区间无冲突，超界输入被拒绝 |
| Optimistic DPSS handoff | 两套成员集合、不同门槛、零重叠 | `PK_sid` 保持，旧新份额不能跨代数组合 | 乐观与异步故障路径的延迟、通信 | 新委员会完成阈值开启，旧份额清除后失效 |
| 窗口封存 | 固定参与集合和重复开启请求 | 只发布一次聚合结果 | 擦除等待、拒绝数 | 封存记录不含阈值份额或部分解密材料 |

阶段 D 按以下顺序执行：

1. 给 Buffalo RLWE 绑定增加系数域导出和导入，先验证单客户端及多客户端密钥求和。
2. 用与 DPSS 相同的曲线标量域实现阈值 ElGamal，验证 `rho=16`、`B_max=512` 时的 `16385` 项点表。
3. 批量生成窗口密钥，并在成员重叠率 `0%、50%、100%` 下运行 handoff；交接过程不得恢复 `z_sid`。
4. 在 `T7` 上组合旧前缀、后继后缀和单次开启，再接入真实模型训练。
5. 与 Buffalo 原生 JL 路径分别报告客户端保护、通信和聚合开启开销；Buffalo 不承担动态委员会交接主张。

若系数密文的客户端开销超过目标设备预算，使用旧委员会完成或放弃窗口作为能力对照，并把优化范围限定为曲线运算并行化和批量验证。阶段 D 通过之前，论文不声称真实密码后端已经实现活动窗口交接。

### 24.4 阶段 D0 参数

阶段 D0 固定一组可运行参数，避免在首个组件检查中同时改变 RLWE、曲线和委员会设置：

| 参数 | D0 取值 | 依据与测量口径 |
|---|---:|---|
| RLWE 环维度 `m` | `2048` | Buffalo 论文与开源默认实验参数 |
| RLWE 系数模数 `q_LWE` | `332366567264636929` | Buffalo `kModulus59` 的当前绑定值 |
| 中心二项分布参数 | `8` | Buffalo 采样器使用 16 对随机比特 |
| 系数上界 `rho` | `16` | 16 个比特差之和的严格取值范围 |
| 窗口客户端上限 `B_max` | `512` | 主实验的最大缓冲规模 |
| 有界点表 | `[-8192,8192]` | 共 `16385` 个候选点 |
| 曲线 | BLS12-381 G1 | 与 Optimistic DPSS 实现共享标量域；ElGamal 依赖 G1 中的 DDH 假设 |
| 点编码 | 48 字节压缩 G1 | 客户端与交接通信均按实际编码计量 |
| 委员会规模 `n` | `8,16,32` | 覆盖小型到中型聚合委员会 |
| Byzantine 上限 `f` | `floor((n-1)/3)` | 与异步委员会容错设置一致 |
| 共享多项式次数 | `f` | 与 Optimistic DPSS 的腐蚀上限一致 |
| 阈值解密份额数 `tau_dec` | `f+1` | 少于该数量不能开启窗口密钥 |
| 配置确认票数 `q_cfg` | `n-f` | 在 `n=3f+1` 时等于 `2f+1` |
| 相邻委员会重叠率 | `0%,50%,100%` | 区分完全更换、部分变化和份额刷新 |
| 活动窗口数 | `1,4,8` | 测量批量密钥生成和交接摊销 |

BLS12-381 是 D0 的实现选择。论文主张依赖同一素数阶标量域中的阈值加密和可验证重分享，不依赖某个库的对象布局。若 Optimistic DPSS 上游 API 无法复用同一 G1 类型，阶段 D 使用同一曲线库重写薄适配层，并分别报告原生 DPSS 和组合后端的成本。

由 `m=2048` 和 48 字节压缩点可以直接得到三项格式检查：一个 ElGamal 系数向量包含 `2m` 个 G1 点，原始编码为 `196608` 字节；一个委员对全部系数的部分解密包含 `m` 个 G1 点，原始编码为 `98304` 字节；一个活动窗口的聚合系数密文仍为 `196608` 字节。实现日志必须分别报告原始点编码、协议元数据和证明字节，避免序列化开销混入密码学载荷。

### 24.5 阶段 D0 接口改动

Buffalo 侧只增加两个入口：

```text
export_coefficients(rlwe_key) -> int[m]
import_coefficients(coefficients) -> native_ntt_key
```

阈值保护侧实现五个批量操作：

```text
create_window_keys(window_ids, committee, share_degree)
encrypt_coefficients(PK_sid, coefficients)
add_coefficient_ciphertexts(aggregate, update)
partial_decrypt_coefficients(share_i, aggregate_digest, open_certificate)
combine_and_decode(decryption_shares, aggregate_digest, open_certificate,
                   B_max, rho)
```

交接层只增加一个窗口密钥入口：

```text
reshare_window_key(sid, source_shares, successor_committee, share_degree)
    -> successor_shares, handoff_proof
```

窗口服务继续调用第 17.3 节的通用后端契约。它不调用 NTT、曲线点运算或 DPSS 内部函数。

### 24.7 六个算法与回放事件的对应

A0 回放只模拟协议边界，不模拟密码学内部计算。每个事件对应一个算法入口或其可观察结果；一个算法可能跨越多个事件，尤其是交接和最终状态清除。

| 算法 | 当前回放事件 | 需要记录的关键结果 | 当前实现状态 |
|---|---|---|---|
| `CreateInstance` | 首个 `client_update` 或显式实例创建事件 | `sid`、模型版本、初始配置、代数和保护上下文 | 已由首次更新隐式创建并记录 |
| `AdmitUpdate` | `client_update`、`client_resubmit` | 更新标识、源标识、接受日志、拒绝原因和记录版本 | 已实现 |
| `FreezePrefix` | `config_install` | 旧配置、接受前缀、`frontier_update_ids` 和聚合状态版本 | 已实现 |
| `HandoffActiveState` | `recover_state`、`handoff_confirm`、`erase_receipt` | 交接尝试、源与目标代数、安装结果、所有者和清除状态 | 已实现；确认、源配置恢复与退役分离 |
| `FinalizeAggregate` | `window_finalize` | 最终参与集合、聚合摘要、整体开启授权结果和结果版本 | 当前只模拟结果确定，未模拟开启授权 |
| `EraseAndSeal` | `erase_receipt` 或封存清除事件 | 封存记录、擦除回执、`seal_pending` 到 `sealed` 的转换 | 已实现 |

因此，阶段 A 的通过条件不是“所有事件都返回 accepted”，而是六个算法的状态前置条件在同一轨迹中成立。特别是 `window_finalize` 不能绕过 `FinalizeAggregate` 的最终集合确认，`handoff_confirm` 不能绕过 `HandoffActiveState` 的安装和清除顺序，`erase_receipt` 之前的活动实例不能恢复纳入或开启。A0 完成后，阶段 C 的抽象后端再为整体开启证书提供不含明文的记录语义。

当前完成的是 A0 输入格式、主要状态转移和四条固定轨迹的服务语义检查。最低聚合人数、最终状态授权和真实密文聚合仍属于后续阶段；T7 当前验证续收顺序。`recoverable_owner` 在完成实例的日志中仍保留最后所属配置，操作许可由实例状态决定。A0 回放尚未计算模型或密文聚合值。

### 24.6 首个可运行检查

第一项代码工作只验证系数转换等价性。对 `k in {1,16,64,512}` 个 Buffalo 原生密钥，分别计算

```text
lhs = import_coefficients(sum_u export_coefficients(s_u))
rhs = sum_u native_ntt_key(s_u) mod q_LWE
```

通过条件是 `lhs` 与 `rhs` 的 `m=2048` 个系数逐项相等，并且每个导出系数满足 `|a_u,j| <= rho`。该检查通过后进入阈值 ElGamal；此时先测单窗口的加密、密文加法和有界解码，再连接 DPSS handoff。这样可以把 RLWE 表示错误与曲线协议错误分开定位。
