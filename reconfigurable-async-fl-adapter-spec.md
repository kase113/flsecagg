# Reconfigurable asynchronous FL adapter specification

> 文档定位：动态异步 FL 系统接入真实训练框架的适配规格。它固定 FL 训练与窗口服务之间的边界，不规定具体密码学实现。

## 1. Purpose

适配层把真实 FL 训练产生的客户端更新交给窗口服务，把窗口完成后的聚合结果交回训练框架。所有主要基线使用同一组客户端、模型、到达轨迹和配置变化；基线之间只替换窗口处理策略和更新保护实现。

适配层需要保留真实训练中的三件事：客户端在某个模型版本上训练，更新可能延迟到达，服务按照完成窗口推进模型。委员会事件与客户端事件共用同一条逻辑轨迹，便于重放和比较。

## 2. Responsibility boundary

### FL training framework owns

- 客户端抽样和本地数据划分；
- 本地训练、优化器和模型序列化；
- 全局模型评估；
- 客户端计算时间和网络到达时间的生成。

### Window service owns

- 窗口创建、客户端更新纳入和重复判断；
- 模型版本与窗口归属；
- 配置安装、窗口转移和结果封存；
- 节点退出、崩溃、恢复和迟到消息处理；
- 聚合完成事件和统一指标记录。

### Protection plugin owns

- `protected_update` 的生成与传输；
- 聚合结果的释放；
- 活动聚合状态的份额累加、交接重分享、安装确认和清除；
- 保护开销的测量。

插件返回窗口服务需要的结果，不改变窗口状态转移规则。这样可以先验证系统路径，再替换不同的安全聚合实现。

### 2.1 Protection context contract

适配层把客户端更新保护和活动窗口密钥重分享分成两个接口：客户端保护后端负责 RLWE 向量保护和系数密文聚合；状态转移后端负责把活动实例的阈值解密密钥份额转换为后继委员会的新共享。转移过程不恢复窗口密钥或聚合明文，也不把已封存实例重新放入输入。首个真实后端采用系数域阈值保护，Buffalo 原生运行作为固定委员会性能基线。

```text
setup_context(configuration, generation, members, threshold)
protect_update(update, context) -> protected update and coefficient ciphertexts
accumulate(state, protected update) -> protected aggregate state
export_aggregate(state, frontier) -> handoff record
reshare_aggregate(record, successor context) -> installed state
authorize_open(state, finality_certificate) -> aggregate-open certificate
partial_open(state, aggregate-open certificate) -> partial aggregate openings
combine_open(state, partial openings, aggregate-open certificate) -> aggregate result
erase(state) -> cleared
```

`protect_update` 的输出可以由阈值 ElGamal 或其他安全聚合后端实现。窗口服务只使用验证结果、参与集合和状态阶段；它不读取客户端明文，也不要求后端暴露逐客户端开启接口。`authorize_open` 绑定实例标识、代数、最终参与集合和聚合状态摘要；成员只为对应证书生成部分开启结果。`combine_open` 完成后发布实例结果。交接时，`erase` 在后继安装确认后、后继恢复写入前执行；最终化时，`erase` 在结果发布后、封存记录生成前执行。

系数域后端把 Buffalo 绑定扩展限制为两个转换接口：

```text
export_coefficients(rlwe_key) -> a[0:m]
import_coefficients(a[0:m]) -> rlwe_key_ntt
```

`export_coefficients` 返回 NTT 之前的中心二项分布系数；`import_coefficients` 在 `q_LWE` 上执行 NTT，并返回 Buffalo 原生聚合接口使用的密钥表示。首个实现检查只验证

```text
import_coefficients(sum_u export_coefficients(s_u))
    == sum_u native_ntt_key(s_u) mod q_LWE
```

该等价性成立后，才接入曲线密文和份额重分享。

### 2.2 Preferred backend for the first implementation

首选真实后端沿用 Buffalo 的 RLWE 向量保护，并在 RLWE 密钥进入 NTT 表示之前保护其有界系数。每个活动实例持有独立的阈值 ElGamal 公钥 `PK_sid`；客户端用该公钥加密系数向量，委员会持有窗口解密秘密的份额。委员会交接只重分享这个均匀随机的曲线标量，受保护更新和系数密文保持不变。该构造直接使用 Optimistic DPSS 的标量域与动态委员会接口。

活动实例 `sid` 的保护状态写成：

```text
S_sid = (
    protected_update_sum,
    encrypted_lwe_coefficient_sum,
    threshold_key_shares_{r,sid},
    window_public_key,
    accepted_update_ids,
    frontier,
    generation
)
```

旧前缀的受保护模型和系数密文在交接时不变；份额持有者和 `generation` 改变。旧配置先确认每个已纳入更新的密文可用，再对窗口密钥份额执行可验证跨组重分享。后继配置在旧份额清除后继续填充同一实例，最终只为固定参与集合开启一次聚合结果。新提交继续使用 `PK_sid`，无需面向每名委员建立密钥份额渠道；旧上下文的迟到更新先经资格和模型版本检查，再以新代数提交。

该后端的完整操作顺序为：

```text
window: batched sharing creates fresh threshold key and PK_sid
client: fresh bounded LWE coefficient vector
    -> protect model vector; encrypt key coefficients under PK_sid
    -> verify payload and add to protected model and coefficient ciphertext sums
frontier:
    -> freeze accepted payloads and aggregate ciphertexts
    -> reshare only the window threshold key share
successor:
    -> verify transfer and install generation + 1
    -> confirm; clear old shares; admit eligible suffix to the same instance
finalization:
    -> threshold-decrypt bounded coefficient sums
    -> rebuild the aggregate LWE key, publish one result, erase window shares
```

旧客户端已纳入的更新无需重新保护；后继客户端使用同一窗口公钥向未完成的原实例提交。截点后的迟到更新更新代数和认证上下文，模型版本仍被接受时不需要重新训练。已封存实例仅传递结果记录。

Buffalo 的动态 assistant 扩展面对的是 NTT 表示或 JL 标量的大域离散对数。本文在 NTT 之前加密中心二项分布系数。若每个客户端系数满足 `|a_u,j| <= rho`，缓冲上限为 `B_max`，聚合系数位于 `[-B_max rho, B_max rho]`。Buffalo 参数 `rho=16`、`B_max=512` 对应 `16385` 个候选点，可用预计算表解码。阶段 D 需要测量客户端 `m` 个曲线密文、阈值部分解密、点表查询和窗口密钥批量生成的成本。

### 2.3 Phase D0 backend interfaces

第一版采用 BLS12-381 标量域。阈值 ElGamal 密文位于 G1，实验按 48 字节压缩点计量，并以 G1 中的 DDH 假设作为密文机密性基础。这个选择与 Optimistic DPSS 的公开实现保持同一标量域，避免在份额重分享时增加域转换。后端只暴露下列批量接口：

```text
create_window_keys(window_ids, committee, share_degree)
    -> {(PK_sid, threshold_shares_sid)}

encrypt_coefficients(PK_sid, coefficients[0:m])
    -> coefficient_ciphertexts[0:m]

add_coefficient_ciphertexts(aggregate[0:m], update[0:m])
    -> aggregate'[0:m]

partial_decrypt_coefficients(share_i, aggregate_digest, open_certificate)
    -> decryption_share_i[0:m]

combine_and_decode(decryption_shares, aggregate_digest, open_certificate,
                   B_max, rho)
    -> aggregate_coefficients[0:m]

reshare_window_key(sid, source_shares, successor_committee, share_degree)
    -> successor_shares, handoff_proof
```

窗口服务保存 `PK_sid`、聚合密文和份额版本，不读取 `z_sid`。曲线库可以在阶段 D 微基准后替换，替换实现必须保持 BLS12-381 标量域兼容或同时替换 DPSS 承诺层。

当前能力边界如下：

| 组件 | 客户端更新保护 | 聚合状态累加 | 跨配置重分享 | 聚合结果开启 | 作为首个后端 |
|---|---|---|---|---|---|
| 系数域阈值 ElGamal 加 Optimistic DPSS | 支持 | 支持密文加法 | 支持曲线标量重分享 | 支持有界系数开启 | 首选 |
| Buffalo 原生 JL 两层保护 | 支持 | 支持 | 固定 assistant | 支持 | 性能基线 |
| PVSS 或 KZG VSS | 支持可验证份额分发 | 支持加法份额累加 | 需要额外异步重分享 | 支持 | 能力对照 |
| VSSR | 支持同一配置内份额恢复 | 取决于底层 VSS | 原文未提供动态委员会重分享 | 支持 | 不直接采用 |
| Silent Threshold Encryption | 支持动态 universe 的阈值开启 | 原语本身不提供 FL 向量聚合 | 不迁移旧 universe 的活动密文 | 支持 | 不直接采用 |

## 3. Canonical records

### Client update

```text
ClientUpdate = (
    update_id,
    client_id,
    window_id,
    source_window_id,
    base_model_version,
    local_steps,
    protection_context,
    payload,
    arrival_order
)
```

`payload` 可以是明文向量、抽象记录或受保护更新。`update_id` 在同一窗口内唯一，`base_model_version` 决定更新是否能够进入该窗口。

### Configuration event

```text
ConfigurationEvent = (
    order,
    event_kind,
    configuration,
    predecessor,
    affected_nodes,
    generation,
    handoff_status
)
```

`event_kind` 包括配置登记、节点离开、节点崩溃和节点恢复。适配层把成员变化交给窗口服务，不修改客户端本地训练。

### Aggregate result

```text
AggregateResult = (
    window_id,
    model_version,
    accepted_update_ids,
    accepted_client_ids,
    resubmitted_update_count,
    aggregate_payload,
    owner_configuration,
    generation,
    handoff_status,
    final_status,
    completion_order
)
```

`final_status` 为 `transferred`、`finalized` 或 `rejected`。只有 `finalized` 结果能够推进全局模型；`transferred` 结果表示窗口仍在处理。

## 4. Adapter operations

```text
open_window(model_version, configuration) -> window_id
submit_update(ClientUpdate) -> admission_result
install_configuration(ConfigurationEvent) -> transition_result
finalize_window(window_id) -> AggregateResult
recover(configuration, record_version) -> recovery_result
poll_result(window_id) -> AggregateResult | pending
```

这些操作对应系统规格中的窗口状态，不要求框架暴露委员会内部记录。适配层把每个操作和事件序号写入统一日志，日志可以重放同一训练轨迹。

### 4.1 `open_window`

服务为指定模型版本创建窗口，并记录当前配置。窗口拥有唯一的接收配置。后续配置转换不会改变已经纳入的客户端集合。

### 4.2 `submit_update`

服务检查窗口是否仍可接收、模型版本是否匹配、更新是否重复。通过检查的更新进入聚合；其他更新得到明确的拒绝原因。客户端不需要知道窗口中的其他客户端。

### 4.3 `install_configuration`

服务根据策略处理活动窗口：`Full-transfer` 转移全部窗口记录，`Periodic-rekey` 排空活动窗口后接收新窗口，`Selective-finality` 只转移未完成窗口并为已完成窗口发布封存记录。本文方案的活动记录还包含 `frontier`、`generation` 和聚合状态保护上下文；接收截点之后到达的旧上下文更新由客户端重新提交到新实例。

### 4.4 `finalize_window`

服务固定参与集合和模型版本，输出 `AggregateResult`，然后拒绝后续会改变该结果的更新和恢复材料。训练框架只把 `finalized` 结果交给全局模型更新器。交接确认失败时，服务保留旧配置的唯一写入权并返回暂缓状态，不创建第二个活动副本。

## 5. Framework mapping

### 5.1 FLSim

按 2026-09-13 对公开仓库 `facebookresearch/FLSim` 主分支的核对，FLSim 提供客户端训练、异步事件调度和异步聚合器，但动态配置、窗口归属、配置交接和结果封存由本文的外部窗口服务承载。核对版本为 `7311f2db471f89f14a0c8c9ea1c9584171677f5a`。

与适配层直接相关的公开接口为：

```text
AsyncClientDevice.training_started(model_seqnum, init_model)
AsyncClientDevice.train_local_model() -> (delta, final_local_model, weight)
AsyncTrainer.train_and_update_global_model(client)
AsyncAggregator.model_staleness(model_seqnum)
AsyncAggregator.on_client_training_end(delta, final_local_model, weight)
```

`AsyncTrainer` 使用 `AsyncTrainingSimulator` 和可配置的 event generator 安排客户端训练。客户端完成训练后，内置路径按照模型序号计算陈旧度，再直接调用 `AsyncAggregator.on_client_training_end`。`AsyncAggregator` 会推进全局模型；`FedBuffAggregator` 在达到 buffer size 后推进全局模型。

因此，真实 FL 适配采用两层职责：FLSim 产生客户端训练结果、训练完成顺序和陈旧度，窗口服务决定更新进入哪个窗口、何时完成聚合以及何时推进模型。桥接层从 `AsyncClientDevice` 读取 `delta` 和 `weight`，将客户端模型序号映射为 `base_model_version`，再创建 `ClientUpdate`。窗口服务返回接受、转移、封存或拒绝结果，并向后续客户端提供新的模型快照。

FLSim 内置 `AsyncTrainer` 的即时全局更新路径不承担本文的窗口裁决。第一版适配使用 FLSim 的客户端与事件调度组件，窗口服务独立维护模型版本；需要复用 FLSim 优化器时，再将已接受窗口的聚合结果交给对应优化器。这样可以在同一训练 workload 下替换四类窗口策略。

### 5.2 Buffalo

Buffalo 的缓冲异步 FL 流程作为主要安全聚合对照。适配器把其缓冲聚合结果映射为 `AggregateResult`，把客户端提交映射为 `ClientUpdate`，保留其本来的客户端训练流程和保护开销。动态配置事件先通过窗口服务记录，再在适配层交给对应的 Buffalo 运行实例。

第一阶段保持 Buffalo 原有运行方式，测量异步缓冲和客户端保护成本。第二阶段加入统一窗口事件日志，用于比较成员变化期间的完成率和模型推进。上游代码保持独立，适配修改以单独补丁保存。

### 5.3 Flower SecAgg+

Flower SecAgg+ 作为常规安全聚合控制。其同步轮次映射为固定窗口，主要用于测量安全聚合加入真实模型训练后的基础代价。它不承担动态委员会主张，成员变化场景使用统一窗口服务和动态轨迹。

### 5.4 Catalyst

Catalyst 作为异步 Byzantine 鲁棒性控制，保留其更新筛选和模型质量评价。它用于区分异步训练与更新鲁棒性的影响，不作为隐私终结的直接对照。

## 6. Replay modes

适配器提供两种执行方式：

```text
trace replay:
    读取预先生成的客户端、网络和配置事件，保证基线逐事件一致

live training:
    由训练框架产生客户端更新，窗口服务实时处理并记录事件
```

第一阶段使用 `trace replay` 验证四类策略的窗口结果和服务开销。第二阶段使用 FLSim 的客户端训练与事件调度产生 `live training` 更新，再由外部窗口服务裁决。两种方式共享 `ClientUpdate`、`ConfigurationEvent` 和 `AggregateResult`。

## 7. Unified logging

每个窗口记录：

```text
window_id, model_version, owner_configuration,
accepted_update_ids, accepted_client_ids,
first_arrival_order, finalization_order,
transfer_count, rejected_message_count,
model_update_time, retained_record_bytes
```

每个配置记录：

```text
configuration, predecessor, install_order,
join_count, leave_count, crash_count, recovery_count,
active_window_count, transferred_window_count,
configuration_transition_delay
```

这些日志足以重建窗口状态路径、客户端纳入集合、模型版本推进和配置转换代价。日志不保存客户端明文更新，模型质量由训练框架单独记录。

## 8. Integration order

1. 使用合成向量和 `trace replay` 验证窗口状态、配置转换和统一日志；
2. 使用 FLSim 的 `AsyncClientDevice` 和 `AsyncTrainingSimulator` 产生真实客户端更新，由外部窗口服务维护模型版本并比较四类窗口策略；
3. 接入 Buffalo，保持同一客户端与配置轨迹，测量保护和交接的共同代价；
4. 接入 Flower SecAgg+ 和 Catalyst，分别提供安全聚合与 Byzantine 鲁棒性控制；
5. 固定模型、客户端数据划分和成员变化轨迹后，运行完整 FL 评价。

## 9. Acceptance criteria

适配层进入完整实验前需要满足：

- 相同轨迹能够在四类策略下重放；
- `accepted_client_ids` 与窗口记录逐事件一致；
- `finalized` 窗口的模型结果和参与集合保持不变；
- 配置变化期间新窗口和旧窗口按照策略得到不同且可解释的处理结果；
- 日志可以计算窗口完成率、客户端纳入率、模型推进、陈旧度、交接延迟、通信量和持久记录大小；
- 替换保护插件不会改变窗口状态和模型版本规则。

## 10. Current decision

动态系统的第一真实 FL 入口采用 FLSim 客户端训练与事件调度，外部窗口服务维护动态配置和窗口结果；Buffalo 作为主要异步安全聚合对照，Flower SecAgg+ 作为常规安全聚合控制。适配层先完成训练路径和窗口指标，安全聚合组件在同一接口下逐步替换。

## 11. Implementation data contract

本节冻结后续代码实现使用的唯一记录契约。它补充当前回放器字段，暂不要求立即建立对应的 Python 文件。

### 11.1 Ownership fields

全局当前配置和窗口所有者必须分开记录：

```text
active_configuration
    可以创建新聚合实例的配置

owner_configuration
    当前 sid 唯一可以接受写入的配置

recoverable_owner
    交接确认失败时仍然可以恢复 sid 活动状态的配置

handoff_status
    owned, handoff_pending, installed, confirmed, seal_pending, sealed
```

配置安装后，`active_configuration` 可以立即变为后继配置；活动窗口在 `handoff_confirm` 成功前仍保持原来的 `owner_configuration` 和 `recoverable_owner`。旧配置在冻结后不能接受新的客户端更新，但可以恢复已经接受的状态并完成交接。确认后，后继配置持有唯一所有权；旧份额擦除回执到达前该窗口继续暂停纳入和开启，其他新窗口照常训练。

### 11.2 Canonical records

```text
ClientUpdate(
    update_id,
    client_id,
    sid,
    source_sid,
    source_update_id,
    base_model_version,
    local_steps,
    sample_weight,
    generation,
    protection_context,
    payload,
    arrival_order,
    retrained
)

LiveWindow(
    sid,
    base_model_version,
    active_configuration,
    owner_configuration,
    recoverable_owner,
    generation,
    accepted_update_log,
    frontier_update_ids,
    status,
    handoff_attempt_id,
    handoff_status,
    writable_state_bytes
)

ConfigurationEvent(
    order,
    kind,
    configuration,
    predecessor,
    effective_boundary,
    source_generation,
    target_generation,
    handoff_attempt_id,
    delivered,
    rejection_reason
)

AggregateResult(
    sid,
    model_version,
    accepted_update_ids,
    accepted_client_ids,
    source_update_ids,
    owner_configuration,
    generation,
    sealed_state_bytes,
    state_change_after_seal,
    final_status
)
```

`accepted_update_log` 按服务接受顺序保存更新标识；`frontier_update_ids` 是冻结时的接受快照。`source_update_id` 建立重新提交关系：同一训练结果产生新目标提交标识，源标识必须标记为未纳入，不能让同一训练结果同时进入两个实例。原实例未完成时，合格的重提优先进入原实例的后继代数；原实例已封存或放弃时进入新实例。退出客户端必须重新取得资格。`retrained` 区分重新保护同一训练结果和基于新模型重新训练。

### 11.3 Event processing order

窗口服务按以下顺序处理影响同一 `sid` 的事件：

```text
1. validate configuration and transition generation
2. validate window status and owner configuration
3. validate client eligibility and model version
4. validate update_id or handoff_attempt_id uniqueness
5. call protection backend operation
6. update accepted log, frontier, owner, or sealed record
7. append event result and rejection reason
```

配置安装不会直接覆盖窗口所有者。`handoff_confirm` 只有在 `installed`、代数严格递增、交接尝试标识匹配且后继状态验证通过时，才改变 `owner_configuration`。`erase` 的回执必须先进入事件日志，再将旧所有者从可恢复集合中移除。

### 11.4 Trace and result files

每个阶段 A 轨迹输出：

```text
events.csv
  order, kind, sid, update_id, source_update_id,
  configuration, source_generation, target_generation,
  handoff_attempt_id, delivered, event_result, rejection_reason

window_results.csv
  sid, accepted_update_ids, frontier_update_ids,
  owner_configuration, recoverable_owner, generation,
  handoff_status, erase_status, writable_state_bytes,
  sealed_state_bytes, state_change_after_seal
```

`events.csv` 是状态判断的依据，`window_results.csv` 是从事件日志派生的摘要。适配器不得只写最终摘要而丢弃逐事件结果。

### 11.5 Build gate

适配器进入 FLSim 前必须通过：

```text
A1: failed confirmation preserves C0 as the only recoverable owner
A2: stale generation cannot install, confirm, recover, or write
A3: sealed sid rejects every state-changing event
```

每个条件都需要对应的逐事件日志和窗口摘要。通过后，FLSim 只负责提供真实 `ClientUpdate` 的 `payload`、模型版本和到达顺序；窗口服务和保护后端的状态规则保持不变。

## 12. Service and backend call boundaries

本节冻结两个模块之间的调用方向。窗口服务拥有状态转移决定权，保护后端拥有保护状态的操作权；后端不能自行改变窗口所有者、frontier 或封存状态。

### 12.1 Client update path

客户端保护发生在提交前，窗口服务的纳入判断发生在保护载荷到达后：

```text
ClientUpdate
    -> client-side protect_update(update, context)
    -> WindowService.preflight(update)
       [configuration, eligibility, model, generation, update_id]
    -> ProtectionBackend.verify_protected_update(update)
    -> ProtectionBackend.accumulate(state, update)
    -> WindowService.commit_admission(update_id)
    -> EventLog.append(accepted)
```

`preflight` 只读状态，不改变接受日志或保护状态。服务先检查 `update_id`、配置、代数和窗口状态，再调用 `accumulate`。`accumulate` 必须是原子操作：成功时聚合状态和接受结果同时可提交，失败时保护状态保持不变。服务只有在后端成功返回后才把更新写入 `accepted_update_log`。

重复提交在 `preflight` 阶段被拒绝，不调用 `accumulate`。如果事件日志写入失败，窗口服务必须保留未提交的后端状态并返回可重试结果，不能出现“密文已经累加但接受日志没有记录”的状态。真实后端可以用事务、临时版本或等价的提交标识实现这一点。

### 12.2 Reconfiguration path

活动实例交接使用暂存状态和单一提交点：

```text
WindowService.freeze(sid)
    -> record frontier_update_ids and source_generation
    -> ProtectionBackend.export_live_state(state, frontier)
    -> ProtectionBackend.reshare_live_state(record, successor_context)
    -> ProtectionBackend.install_live_state(staged_record, successor_context)
    -> WindowService.validate_installation(sid, attempt_id)
    -> WindowService.confirm_handoff(sid, attempt_id)
    -> ProtectionBackend.erase(source_state, erase_token)
    -> EventLog.append(confirmed, erased)
```

`freeze` 是窗口服务的状态操作，先于后端导出发生。冻结后旧上下文更新都得到 `frontier_closed`，即使后端尚未完成重分享。`export_live_state` 和 `reshare_live_state` 可以重试，但必须绑定 `sid`、源代数、目标代数和 `handoff_attempt_id`；同一尝试重复执行不能生成两个可安装状态。

`install_live_state` 只产生后继配置的暂存状态，不改变窗口的 `owner_configuration`。只有 `validate_installation` 和 `confirm_handoff` 成功后，窗口所有者才切换。确认失败时销毁或标记无效的暂存状态，保留源状态和 `recoverable_owner`。确认成功后先写入安装确认，再执行源状态擦除；擦除收据写入事件日志后，该实例才可在新代数下恢复纳入或开启。旧配置的服务资格在确认时停止；旧物理份额在擦除成功前仍被记录为待清除，不能被当作已证明删除。

### 12.3 Finalization path

封存是独立于交接的单向提交：

```text
WindowService.check_finalize(sid)
    -> ProtectionBackend.authorize_open(live_state, finality_certificate)
    -> ProtectionBackend.partial_open(live_state, aggregate_open_certificate)
    -> ProtectionBackend.combine_open(live_state, partial_openings,
                                      aggregate_open_certificate)
    -> WindowService.validate_result(result, sid, generation)
    -> EventLog.append(result_ready)
    -> WindowService.publish_sealed_record(result)
    -> ProtectionBackend.seal(live_state)
    -> ProtectionBackend.erase(live_state, erase_token)
    -> EventLog.append(sealed, erased)
```

如果整体开启授权、部分开启或结果合并失败，窗口保持活动状态；如果结果校验或封存记录发布失败，服务保留可恢复的活动状态并使用同一结果标识重试。`publish_sealed_record` 成功后，任何改变窗口状态的消息都只能得到 `sealed_window`。后端不能在封存记录发布后重新提供可写份额或重新授权该实例开启。

封存记录发布和活动状态擦除之间使用显式的 `seal_pending` 状态：结果已经固定，窗口不再接受任何状态改变，但后端仍可能保留待清除的活动材料。只有擦除回执写入事件日志后，状态才变为 `sealed`。如果擦除失败，服务继续报告已固定的结果，同时记录 `erase_pending`，不允许恢复或重新开启该实例。

### 12.4 Failure and retry matrix

| 阶段 | 失败事件 | 保留状态 | 可重试操作 | 禁止结果 |
|---|---|---|---|---|
| 提交预检 | 配置、资格、代数或模型不匹配 | 原活动状态 | 客户端使用新上下文重新提交 | 不得调用 `accumulate` |
| 聚合累加 | 后端验证或累加失败 | 原接受日志和聚合状态 | 使用同一 `update_id` 重试 | 不得部分累加 |
| `freeze` 后导出 | 节点不可用或状态读取失败 | 已冻结的源状态 | 同一 `handoff_attempt_id` 重试 | 不得重新开放 frontier |
| 重分享 | 份额转移失败 | 源状态和 `recoverable_owner` | 重试同一交接尝试 | 不得安装半成品状态 |
| 安装确认 | 证书、代数或摘要不匹配 | 源状态唯一可恢复 | 修复后重试同一尝试 | 不得切换 owner |
| 擦除 | 安装已确认但擦除暂时失败 | 新 owner 已确认，旧状态标记待擦除，该实例暂停纳入及开启 | 按 `erase_token` 重试 | 不得把旧状态当作可恢复副本或报告训练已恢复 |
| 开启结果 | 整体开启授权、部分开启或结果合并失败 | 活动状态 | 使用同一最终状态证书重试 | 不得生成 sealed record |
| 封存发布 | 记录写入失败 | 活动状态和结果标识 | 重试同一结果发布 | 不得接受新的聚合输入 |
| 封存清除 | 记录已发布但擦除失败 | `seal_pending` 和固定结果 | 使用同一 `erase_token` 重试 | 不得恢复或重新开启 |

擦除失败是安全状态而不是普通网络失败：系统可以继续报告后继配置已安装，但不能报告旧状态已经清除。实验结果必须分别记录 `installed`、`erase_pending` 和 `erased`。

### 12.5 Adapter responsibilities

适配器只做记录转换和计时：

```text
FLSim/Catalyst -> ClientUpdate
Buffalo/Flower -> protected payload and backend counters
WindowService -> admission, handoff, finality records
Metrics        -> event log and derived tables
```

适配器不能直接调用 `reshare_live_state`、`erase` 或 `publish_sealed_record` 绕过窗口服务。基线若没有对应能力，适配器返回 `unsupported`，实验把它记录为能力差异；不通过隐藏的重启或状态复制模拟成功交接。

### 12.6 Interface-level acceptance checks

实现接口进入阶段 C 前，必须能从调用日志检查：

```text
preflight rejection has no backend mutation
successful accumulation precedes admission commit
freeze precedes every handoff export
install precedes confirm, confirm precedes erase
failed confirm leaves source recoverable
sealed publication precedes sealed-window rejection
every retry carries the same idempotency token
```

这些检查只验证模块边界和调用顺序，不替代底层密码学安全证明。
