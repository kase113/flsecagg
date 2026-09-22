# Dynamic Membership and Epoch-Bounded Mobile Adversary

> 文档定位：`Reconfiguration-Safe Privacy Finality for Asynchronous FL` 的动态成员模型稿。本文档把动态配置、异步训练窗口和受限 epoch-mobile adversary 放入同一个可复现实验对象，服务于系统设计、故障轨迹和论文叙事。密码学组件只提供更新保护接口。

> 2026-09-20 当前依据：以下保留早期模型和实验轨迹的推导。当前论文采用 [论文结构稿](reconfigurable-async-fl-manuscript-structure.md) 第 3.1、3.2 节及 [研究追踪 P144](reconfigurable-async-fl-privacy-finality-tracker.md) 的模型与推进条件。累计暴露按每个实例的份额代数统计，直到旧材料满足清除条件；服务更替期间同时核对新旧代暴露与重分享转录。活性分别依赖载荷可用性、源服务和后继服务完成相应职责、开启及提交条件。$\ell_r$ 作为额外不可用节点数用于参数实验。下文以配置周期计数、单一恢复门槛概括交接、或在失联后直接放弃实例的早期表述，由当前结构稿的实例规则替代。

## 1. Research question

持续运行的异步联邦学习服务同时面对两类变化：客户端更新按照不可预测的顺序到达，服务委员会随着节点加入、退出、崩溃和恢复持续变化。窗口可能在配置切换前接收部分更新，也可能在切换后等待恢复或继续聚合。

本文研究的问题是：

> 在完全异步的动态成员环境中，如何让正在形成的联邦聚合跨配置继续产生模型更新，并让已经确定的聚合结果成为后继配置不可重新开启的隐私边界？

问题的关键对象是窗口状态的归属。配置交接会改变状态的持有者、恢复路径和消息可达性；这些变化直接决定客户端更新能否进入模型、已完成结果能否保持唯一，以及历史状态需要保存多久。

## 2. Main thesis

动态成员是异步 FL 的训练语义问题。委员会变化把一个连续训练服务切分成相邻的配置视图，而客户端窗口可能跨越这些视图。系统需要同时维护两条关系：

```text
live instance    -> ownership can move to a successor configuration
committed result -> result remains fixed; only a retired record is carried forward
```

这条区分形成本文的核心设计原则：**交接对象由窗口状态决定，配置变更本身不决定所有历史状态的处理方式。**

本文要观察三个系统结果：

1. 在节点变化和异步延迟下，活动窗口仍然能够产生后续模型版本；
2. 每个已完成窗口只产生一个参与集合和一个模型结果；
3. 配置交接和长期状态规模随活动窗口变化，而不是随历史窗口无限增长。

## 3. System model

### 3.1 Universe and configurations

令 `U` 为潜在服务节点集合。配置 `C_r` 包含：

```text
C_r = (M_r, version_r, predecessor_r, transition_record_r)
```

其中 `M_r` 是当前参与节点，`version_r` 是单调递增的配置编号，`predecessor_r` 指向前一配置，`transition_record_r` 记录该配置的安装依据和成员变化。

配置从节点的本地视图推进。系统不使用全局墙上时钟判断配置是否生效；节点通过已经认证的配置记录和服务事件更新本地视图。短时间内，旧配置和新配置可以同时存在于网络中，但每个窗口在任意本地视图中只有一个服务归属。

配置事件包括：

```text
install(C_r -> C_{r+1})
join(p, C_{r+1})
leave(p, C_r)
crash(p, C_r)
recover(p, C_r or C_{r+1})
```

加入节点从已认证的配置记录和必要的当前窗口状态开始服务。退出请求形成后继配置后，退出节点不再拥有旧配置的写入权；与其有关的尚未交付消息可以被调度器丢弃。崩溃节点暂时停止服务，恢复后按照当前配置记录恢复可服务状态。恢复节点若未被纳入后继配置，只能提交材料供当前配置验证，不能直接恢复旧写入权。

### 3.2 Asynchronous network

节点之间使用认证异步通道。消息可以任意延迟、重排和重复；诚实节点发送的消息在节点持续服务时最终可以交付。节点退出后，调度器可以丢弃该节点尚未完成的发送和重传。

成员事件通过服务已有的成员管理路径传播。配置记录的顺序由认证的转换记录确定，消息抵达顺序保持异步。模型将网络延迟和成员变化作为同一事件轨迹的两个维度，避免用同步轮次掩盖配置交接期间的真实竞争。

### 3.3 Training windows

每个训练窗口定义为：

```text
W_sid = (
    sid,
    base_model_version,
    owner_configuration,
    accepted_updates,
    frontier,
    generation,
    share_context,
    status,
    result_record
)
```

客户端更新携带 `sid`、基础模型版本、客户端身份、本地训练结果和保护上下文。服务按照窗口归属、模型版本和 `frontier` 接收更新。`accepted_updates` 只增不减，窗口结果由该集合确定。`frontier` 是旧配置已经接受的更新集合及其记录版本，不是消息发送时间。

实例状态采用具有明确服务含义的值：

```text
    accepted    -> 当前配置继续接收和聚合更新
    transferred -> 未完成实例已安装到后继配置，等待退役确认
    committed   -> 参与集合、聚合值和模型结果已经确定
    sealed      -> 可写状态已退役，只保留封存记录
    abandoned   -> 交接条件未满足，实例不再拥有可写后继状态
    rejected    -> 更新不改变实例结果
```

`transferred` 表示实例已经由后继配置安装但仍处于冻结阶段；退役确认后才恢复纳入。`committed` 是结果级吸收状态：后继配置可以读取记录，却不能重新打开实例或改变其参与集合。`sealed` 进一步表示旧可写状态已经退役。

### 3.4 Configuration transitions

一次配置转换包含三个逻辑事实：

```text
predecessor view   -> old configuration has accepted state
successor view     -> new configuration is authorized to serve
    instance decision  -> each instance is transferred, committed, sealed, or abandoned
```

配置转换允许旧配置继续处理已经接收的活动窗口，同时让新配置接收后续窗口。对于跨越转换点的活动窗口，交接记录至少绑定：

```text
(sid, base_model_version, source_configuration,
 target_configuration, frontier, generation,
 current_record_version, transition_record)
```

交接记录描述当前活动状态的版本和来源。旧配置对聚合值执行阈值共享重分享，后继配置验证交接记录和新 `share_context` 后安装活动状态；安装确认前旧配置仍是唯一可恢复来源。已完成窗口只携带 `result_record` 和封存所需的元数据。

## 4. Epoch-bounded mobile adversary

### 4.1 Adversary capabilities

本文采用 **epoch-bounded mobile adversary** 模型。一个 epoch 对应一个配置周期 `C_r`。敌手观察公开的配置记录、窗口状态事件、消息交付结果和模型版本推进，并根据这些观察选择下一步操作。敌手可以：

```text
delay/reorder/drop allowed messages
corrupt a currently active node
read the corrupted node's current service state
release a corrupted node after it leaves or is cured
select a later node for corruption
trigger legal recovery and membership events
```

敌手遵守节点认证和配置安装规则，不能伪造诚实节点的认证事件。敌手对客户端更新的影响通过服务允许的提交和调度路径产生；模型把恶意梯度筛选交给 Catalyst 等独立对照。

### 4.2 Epoch bound

对每个配置周期 `C_r`，`f_r` 表示该 epoch 内敌手可控制和读取的委员会节点上限，`\tau_r` 是该配置对活动实例的恢复门槛。基本条件是 `f_r < \tau_r`，并且后端的刷新协议保证不同 generation 的已读份额不能直接组合成一次有效恢复。敌手可以在相邻 epoch 之间释放旧节点并选择新节点，因此长期执行中的累计暴露量可以超过单个 epoch 的 `f_r`。这刻画了持续运行中的自适应节点替换。

该模型刻画真实的持续服务：节点可能在参加若干窗口后被腐蚀，随后离开或恢复；新成员接替其服务位置，敌手继续根据新的配置和窗口状态选择目标。模型将累计暴露作为系统状态记录，而不是把它压缩成一次性的静态故障集合。

该模型具有五个边界：

1. 每个配置周期的控制规模满足该配置的服务容错条件；
2. 节点释放结束当前主动控制，敌手已经读取的状态继续属于其视图；
3. 活动窗口跨越 epoch 时使用后继配置的新保护上下文，交接期间旧、新份额的联合暴露仍须满足后端的移动安全条件；
4. 交接只有在源配置产生前缀证明、后继配置安装新份额并形成旧状态退役记录后才成为可继续的交接；该条件由恢复门槛决定，不要求源配置所有节点在线；
5. 退出、崩溃和恢复改变消息可达性与本地记录，但不改变已经确定的窗口结果；恢复节点只有在当前配置中重新获得成员资格时才拥有写入权。

本文把 `f_r`、`\tau_r`、配置重叠和交接延迟作为实验参数，并分别报告交接成功、交接暂缓和实例放弃。论文不把某个动态共识协议的容错不等式直接套用于 FL 服务；它只要求成员服务提供可验证的后继配置证明，本文分析该证明驱动的活动聚合交接。

### 4.2.1 Model interpretation

该模型沿用 proactive secret sharing 和动态委员会研究中的周期性暴露边界、状态刷新与安全擦除。相关工作通过刷新 share 控制每个服务周期内的状态暴露；DyCAPS 进一步处理周期之间的节点替换、handoff 和 secure erasure。本文把这些条件用于异步 FL 的训练窗口。

这些工作保护的对象是长期秘密或新的阈值份额。本文把实例、模型版本和配置转换纳入成功事件。敌手读取受控制节点的服务状态，并检验这些状态是否能够在 `Seal_sid` 之后形成某个历史实例的合法开启路径。

本文不提出新的通用敌手理论。epoch-bounded mobile adversary 是面向异步 FL 配置交接的模型实例，边界由五点组成：

1. 控制上限按当前 epoch 计算，跨 epoch 的累计状态暴露单独记录，且 `f_r < \tau_r`；
2. `release` 结束当前控制，但敌手已经读取的状态仍保留在敌手视图中；
3. 节点的安全擦除和状态交接属于协议条件，节点离开记录不能替代这两个条件；
4. 敌手只能根据公开事件、合法恢复和消息调度选择下一步操作，不获得任意历史查询接口；
5. 对一个活动实例，协议在每次交接时安装新的保护上下文；交接无法完成时，实例保持冻结，服务重试同一交接或明确报告 `abandoned`，不创建第二个可写副本。

对实例 `sid`，令 `X_A(sid,t)` 表示敌手截至事件前缀 `t` 取得的状态、消息和恢复转录。该模型下的 FL 安全目标是：在 `Seal_sid` 之后，`X_A(sid,t)` 与合法后继配置状态的闭包不能形成 `sid` 的单客户端开启集合。对 `Seal_sid` 之前的活动实例，协议通过 epoch 状态刷新、交接期间的联合暴露条件和旧状态退役限制跨 epoch 状态的可组合性。

### 4.3 What the adversary is testing

敌手检验的是窗口状态在配置边界上的一致性：

```text
old live state + new live state
old delayed message + new admission rule
committed record + later recovery request
```

攻击成功表现为系统级事件，而非密码学破译：

```text
duplicate inclusion       -> 同一更新影响两个配置的结果
window resurrection        -> 已完成窗口重新进入聚合
result divergence          -> 不同节点记录不同参与集合或模型结果
progress loss              -> 活动窗口因交接等待而长期无法完成
history growth             -> 已完成窗口仍保存完整活动状态
```

## 5. Adaptive cross-configuration trace

### 5.1 Two-configuration trace

固定两个相邻配置 `C_0` 和 `C_1`，选择一个正在接收更新的窗口 `W_sid`：

```text
t0  C_0 accepts updates for W_sid.
t1  The service installs C_1 while W_sid remains active.
t2  A_0 observes the transition record and delays one C_0 handoff message.
t3  A_0 corrupts selected C_0 nodes and reads their current W_sid state.
t4  A_0 selects C_1 nodes after observing the new membership.
t5  C_1 receives the delayed message or a recovery request.
t6  C_1 either installs W_sid state, rejects it, or creates a second copy.
t7  The service finalizes W_sid or processes a late update.
```

该轨迹同时测试训练连续性和结果终结性。`t2` 测试离开或异步延迟导致的状态遗漏，`t3-t4` 测试跨周期的有限状态暴露，`t5-t7` 测试配置交接与窗口封存的先后关系。

### 5.2 Failure modes

**Late handoff admission.** `C_1` 接受一个在 `Commit_sid` 之后抵达的旧活动状态，实例重新进入聚合，或者旧更新再次参与模型推进。

**Split ownership.** `C_0` 和 `C_1` 都保留可写的 `W_sid` 状态，两个配置分别接受更新，最终形成不同的参与集合和模型结果。

**Recovery amplification.** `C_1` 为恢复 `W_sid` 反复请求 `C_0` 的旧状态，节点退出和消息遗漏使恢复路径持续占用服务资源，后续窗口受到阻塞。

**Historical state retention.** `W_sid` 已经完成，系统仍然携带完整聚合材料和恢复材料跨越多个配置，交接成本随历史窗口数量增长。

这些失败模式都能通过事件日志观察：窗口状态、配置归属、接受集合、交接次数、拒绝消息、恢复延迟和保留记录大小足以重建攻击结果。

## 6. Design response

本文方案采用窗口级交接规则，包含三个相互配合的机制。

### 6.1 Ownership transfer for live windows

活动窗口拥有唯一服务归属。配置转换产生交接记录后，旧配置固定 `frontier` 并对聚合值的阈值共享执行重分享；后继配置验证交接记录和新保护上下文后取得写入权。旧配置继续处理已经在本地确认的事件，直到交接记录生效；新配置从该记录继续处理。截点之后到达的旧上下文更新进入新的聚合实例。

交接只针对仍然需要训练推进的窗口。窗口在交接期间保持 `transferred`，因此客户端不会被默默丢弃，也不会被两个配置同时计入。

### 6.2 Finality barrier for completed windows

实例达到聚合条件时，服务先生成 `Commit_sid`，确定：

```text
sid, base_model_version, accepted_client_ids, aggregate result
```

该记录成为后继配置读取的唯一历史对象。后继配置收到旧更新、旧恢复请求或旧交接材料时，按照窗口记录产生拒绝事件；这些事件不改变模型版本和参与集合。

之后只有在旧可写状态完成退役后才生成 `Seal_sid`。封存记录保留结果重放和审计所需的信息，完整活动状态只在实例仍需推进时保留。该规则把历史数据规模从“所有曾经处理的实例”降到“当前活动实例加上固定大小的结果记录”。

### 6.3 Recovery follows the current view

恢复节点先安装自己能够验证的最新配置记录，再恢复该配置仍然拥有服务归属的活动窗口。恢复路径按照窗口状态分类：

```text
live window       -> restore current version and continue
transferred       -> restore from successor handoff record
   committed         -> restore result record only
   sealed            -> restore result record only
   abandoned         -> restore no writable state
rejected          -> restore no writable state
```

节点恢复过程不会把旧配置的完整活动记录重新加入已提交实例。交接记录与窗口记录共同决定恢复对象，消息到达顺序只影响恢复时间，不改变实例归属和最终结果。

## 7. System properties

下面的性质是系统设计目标和实验检查条件。它们描述训练服务行为，安全聚合组件只需实现相应的更新保护接口。

### P1. Single ownership

每个窗口在任意事件前缀中至多拥有一个可写配置。配置交接完成后，旧配置产生的写入只作为交接输入或拒绝事件处理。

### P2. Monotone admission

窗口的接受集合随事件推进单调增加。配置交接复制已有状态，不删除已经接受的更新，也不重复计入同一更新。

### P3. Committed-result stability

实例生成 `Commit_sid` 后，参与集合、聚合结果和模型版本保持不变。任意后继配置的恢复和迟到消息处理都保持该记录；`Seal_sid` 进一步表示旧可写状态已经退役。

### P4. Transfer continuity

在实例级交接可用性条件成立、交接记录能够交付或恢复的执行中，活动实例继续产生结果。交接延迟影响完成时间，但不改变已接受前缀；无法满足条件的实例进入 `abandoned`，不产生后继配置伪造的结果。

### P5. Explicit handoff failure

当服务条件暂时无法支持活动实例交接时，系统保留旧配置的唯一恢复来源，并输出明确的重试或暂缓记录。确认失败不会产生第二个活动副本；达到放弃条件时输出 `abandoned` 记录，合格客户端改用新实例提交。

### P6. Bounded retained state

完成窗口只保留封存记录；配置转换的迁移量由活动窗口状态和转换记录决定。历史完成窗口数量增加时，迁移量保持有界增长。

## 8. Necessary conditions and falsifiable claims

### 8.1 Candidate sufficiency conditions

以下条件组成候选系统条件，后续通过轨迹模拟和真实 FL 运行验证：

```text
SC1  Configuration records have a single successor order.
SC2  Every writable window has one owner at each event prefix.
SC3  A live-window handoff carries a complete current record.
SC4  Commit changes the instance's admission class to read-only.
SC5  Recovery uses the latest record in the installed configuration view.
SC6  The source and successor jointly meet the threshold needed for a certified handoff and retirement record.
```

`SC1-SC5` 是服务语义条件，`SC6` 是由源配置恢复门槛、后继配置安装门槛和退役记录共同决定的可用性条件。它不要求所有旧节点在线，只要求足够的诚实服务节点完成一次可验证交接。它们共同支持 P1-P6；本文先将其作为候选条件，不提前写成密码学安全定理。

### 8.2 Candidate necessity traces

去掉 `SC2` 会产生 split ownership；去掉 `SC3` 会产生 silent loss 或 recovery amplification；去掉 `SC4` 会产生 window resurrection；去掉 `SC5` 会让恢复节点重新加载旧配置状态；去掉 `SC6` 会使活动实例冻结或错误地被后继配置重新打开。

这些反例把方案价值转化为可证伪主张：每条条件都对应一个事件轨迹和至少一个可测量指标。实验可以改变配置转换频率、并发窗口数、网络延迟、离开额度和 epoch 控制顺序，观察条件变化时的具体代价。

### 8.3 Main system claim

在满足 `SC1-SC6` 的执行中，`Selective-finality` 同时提供：

```text
    continuous progress for live instances that meet SC6
    single committed result per instance
bounded handoff state tied to active windows
```

与之相比，`Full-transfer` 继续迁移历史活动材料，`Periodic-rekey` 通过暂停后续窗口换取较简单的配置转换，`Static` 避免成员变化但无法反映长期运行中的节点替换。四类策略使用相同客户端更新和网络轨迹，差异集中在窗口处理规则。

## 9. Relation to existing dynamic asynchronous work

Turritopsis 将动态异步 BFT 组织为连续配置，并明确指出：节点离开会导致未交付消息遗漏，配置推进依赖本地状态，离开额度和配置间可用成员关系决定活性。本文借鉴这些系统事实，重新定义研究对象为 FL 窗口而非共识交易。

Turritopsis 的配置证明链适合证明新成员应当追赶哪个配置；本文还需要回答该配置是否有权修改某个具体训练窗口。一个配置记录可以授权后续训练，也可以只授权读取已经完成的结果，两类权限由窗口状态分别决定。

动态 proactive secret sharing 和阈值刷新方案适合维持连续使用的委员会状态。FL 服务需要为每个窗口划出结果边界：活动窗口可以继续使用当前服务状态，完成窗口进入只读记录。持久状态刷新因此成为本文的对照机制，窗口级封存成为主要设计差异。

本文不把 Turritopsis 的共识安全性质作为攻击对象，也不把动态 BFT 的成员容错公式直接移植到 FL。比较对象是配置交接机制与 FL 窗口服务语义的组合结果。

## 10. Evaluation plan

### 10.1 Workload factors

```text
configuration transitions: 1, 3, 5, ...
active windows:            1, 4, 8, ...
client arrivals:           low, bursty, delayed
membership events:         join, leave, crash, recover
message schedule:          reordered, delayed, omitted after leave
epoch-bounded exposure:   before handoff, during handoff, after finality
```

训练框架提供客户端本地训练、到达顺序、陈旧度和模型评估；窗口服务提供配置变化、交接和封存；保护插件提供更新保护开销。三者使用统一事件记录，保证基线只改变服务策略。

### 10.2 Metrics

主要指标为：

```text
window completion rate
accepted-client rate
model-version progress
update staleness
handoff and recovery latency
duplicate or reopened windows
rejected late-message count
retained record bytes
communication volume
model quality under equal training budget
```

### 10.3 Falsification criteria

本文方案需要同时面对两类结果：

1. 如果 `Selective-finality` 在 epoch-bounded exposure 和高延迟轨迹中仍能保持 P1-P6，同时完成率和模型推进优于 `Periodic-rekey`，主张得到支持；
2. 如果交接记录或恢复路径仍然产生重复窗口、旧状态复活、结果分歧或持续阻塞，模型和机制需要收紧。

结果报告以事件轨迹和窗口日志为依据。安全聚合实现的密码学开销作为独立维度记录，不承担动态成员主张。

## 11. Scope boundary

本文当前聚焦：

```text
fully asynchronous delivery
dynamic service membership
epoch-bounded mobile exposure of service nodes
window-scoped handoff and finality
continuous asynchronous FL training
```

本文暂不引入：

```text
adaptive query histories
new threshold cryptosystem construction
direct attacks on Turritopsis consensus safety
Byzantine gradient robustness as the main contribution
```

这些边界保持论文成为一篇 FL 系统论文：动态成员机制决定训练连续性、结果稳定性和系统代价；安全模型和保护接口为这些性质提供约束。

## 12. Immediate research tasks

1. 将 `SC1-SC6` 映射到 `reconfigurable-async-fl-system-spec.md` 的窗口不变量和事件类型。
2. 使用回放器验证 `corrupt`、`release` 和 `recover_state` 事件能区分四类失败模式。
3. 核对 FLSim 的客户端训练和异步到达接口，把训练时间与窗口事件分开注入。
4. 用相同轨迹比较 `Static`、`Full-transfer`、`Periodic-rekey` 和 `Selective-finality`，再决定真实 FL 适配的最小实现。
5. 依据稳定的系统指标选择更新保护组件。

## 13. Current status

```text
research question:      fixed
dynamic model:          drafted here
rolling attack:         defined as system trace
candidate conditions:   SC1-SC6
protocol mechanism:     window ownership + finality barrier + view-based recovery
cryptographic claim:    intentionally abstract
next gate:              FLSim API mapping and live-training replay
```
