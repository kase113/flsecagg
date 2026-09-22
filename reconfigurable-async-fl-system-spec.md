# Dynamic Asynchronous FL Service Specification

> 文档定位：`Reconfiguration-Safe Privacy Finality for Asynchronous FL` 的系统规格稿。本文档固定服务语义、窗口转移规则、故障轨迹、基线和评估指标，不定义新的密码学原语，也不替代论文正文。

## 1. 系统目标

系统持续接收客户端更新，并在委员会成员变化、节点离开、节点崩溃和节点恢复期间推进异步联邦学习。系统以训练窗口为基本组织单位：一个窗口收集一组客户端更新，产生一个确定的模型版本，并记录该结果是否已经封存。

系统同时提供两种性质：

1. **训练连续性：** 委员会变化不会暂停新的客户端更新，未完成窗口可以由后继配置继续计算。
2. **结果终结性：** 已经确定模型结果的窗口不再接受新的更新，也不再向后继配置转移能够重新打开单客户端更新的材料。

这两个性质共同构成本文的系统目标。成员变化的价值在于它迫使服务对每个窗口作出明确的继续、转移或终结决定。

## 2. 参与者和对象

### 2.1 客户端

客户端在本地模型版本 `v` 上训练，提交带有窗口标识和版本信息的受保护更新。客户端不需要预先知道同一窗口中的其他客户端，也不需要等待委员会完成成员变更。

客户端资格与委员会成员资格分开记录。客户端加入只表示该客户端可以从指定的模型版本开始提交新更新；客户端退出只停止后续提交，不撤销已经进入 `accepted_update_ids` 的更新。客户端加入或退出不改变委员会的阈值上下文。

### 2.2 委员会配置

配置 `C_r` 包含成员集合、配置编号 `r`、用于验证配置转换的证明以及该配置能够处理的窗口范围。配置转换记录 `T_{r,r+1}` 确定后继配置，并允许新节点追赶公开的配置历史。

本文不规定配置证明由哪一种共识协议产生。实验使用一个可替换的配置服务接口，确保所有节点对配置编号和后继关系得到相同判断。

成员变更和可用性事件分开处理。加入和退出改变后继配置的成员集合；崩溃表示节点暂时不可用，不自动产生新的配置；恢复节点先读取当前配置和最新记录，只有被纳入后继配置时才重新获得服务职责。节点退出后再次出现也按照一次加入处理，不直接恢复旧配置中的写入权。

配置同时确定两类保护上下文：配置认证上下文 `Auth_r` 和活动聚合实例使用的阈值共享上下文 `Share_{r,sid}`。新配置安装后，新实例使用 `Auth_{r+1}` 和新的 `Share_{r+1,sid}`。已有活动实例通过可验证重分享从旧上下文迁移到新上下文；已封存实例不再迁移共享状态。

委员会成员事件采用配置生效语义：加入节点在 `C_{r+1}` 生效后获得新的阈值份额，退出节点在 `C_{r+1}` 生效后失去写入权。节点崩溃和恢复只改变可用性，不改变成员集合。恢复节点只有在后继配置中重新出现时才重新获得服务职责。

### 2.3 训练窗口

窗口 `sid` 绑定以下公开属性：

```text
W_sid = (sid, model_version, owner_configuration, admission_rule)
```

窗口记录还保存已纳入更新的客户端标识、累计聚合结果、当前计算进度、封存结果和状态版本。客户端更新的具体保护方式由安全聚合实现提供，窗口规则不依赖某个特定密码学构造。

### 2.4 服务记录

服务记录是跨节点恢复和配置转换的唯一依据。它分为两部分：

```text
live record:
    未完成窗口的当前计算进度和继续计算所需材料

sealed record:
    已确定模型版本、参与集合、聚合结果摘要、退役证明和拒绝边界
```

后继配置可以安装 `live record`，只能读取 `sealed record`。封存记录不包含能够重新开启单客户端更新的材料。

活动记录的保护状态是聚合值的阈值共享，而不是客户端明文或逐客户端开启材料。委员会节点在本地累加自己持有的更新份额，交接时对该聚合值执行可验证重分享。记录因此可以在保留客户端参与集合的同时，把交接规模从逐客户端保护记录降为一个聚合状态和必要的元数据。

每条活动记录还保存以下字段：

```text
frontier:
    已被旧配置接受的最后记录版本和对应的客户端更新集合
generation:
    保护上下文版本，每次活动实例成功交接后递增
share_context:
    当前委员会的阈值共享上下文标识
handoff_status:
    owned, handoff_pending, installed, confirmed, committed, seal_pending,
    sealed 或 abandoned
```

`frontier` 是旧配置接收前缀的逻辑边界，不表示全局物理时间。边界后抵达的旧代数消息不能写入原实例；交接及旧份额清除完成后，仍具资格的客户端可使用后继代数向**同一未完成实例**重新提交。实例已经封存或明确放弃时，合格更新才转向新实例。这使未满额的缓冲区有机会继续达到最低参与数。

## 3. 窗口状态和转移

每个窗口使用以下服务状态：

| 状态 | 含义 | 后继配置可执行的操作 |
|---|---|---|
| `accepted` | 窗口正在收集并聚合更新 | 继续接收满足版本和纳入条件的更新 |
| `transferred` | 未完成窗口已安装到后继配置，等待旧状态退役 | 读取交接状态，不能写入 |
| `confirmed` | 后继配置成为唯一服务者，旧状态已形成退役记录 | 继续接收满足条件的更新 |
| `committed` | 模型结果和参与集合已经确定 | 读取结果，不能写入或恢复 |
| `sealed` | 可写状态已经退役，只保留封存记录 | 读取封存结果 |
| `abandoned` | 交接条件未满足，实例停止提供可写后继状态 | 重新提交到新实例 |
| `rejected` | 消息与窗口记录不匹配或已过期 | 记录拒绝原因 |

实现内部还记录两个过渡状态：`handoff_pending` 表示活动状态已经冻结但后继所有者尚未确认，`seal_pending` 表示结果已经发布但活动保护材料尚未收到退役回执。它们不属于可供客户端写入的服务状态：`handoff_pending` 只允许交接恢复操作，`seal_pending` 只允许退役重试。

允许的状态转移为：

```text
accepted    -> accepted
accepted    -> handoff_pending
accepted    -> transferred
accepted    -> committed
accepted    -> abandoned
accepted    -> rejected       (仅针对单条消息)
transferred -> transferred
transferred -> confirmed       (仅在旧状态退役后)
transferred -> abandoned
transferred -> rejected       (仅针对单条消息)
confirmed   -> confirmed
confirmed   -> committed
confirmed   -> abandoned
committed   -> seal_pending
seal_pending -> seal_pending  (仅重试退役)
seal_pending -> sealed        (仅在退役回执记录后)
committed   -> committed
sealed      -> sealed
abandoned   -> abandoned
rejected    -> rejected
```

`committed`、`sealed`、`abandoned` 和 `rejected` 对同一窗口的结果具有单调性。一个窗口的模型结果和参与集合一经 `Commit` 确定，后续事件只能读取、完成退役、放弃或拒绝，不能重新计算出另一份结果。

活动记录的唯一写入权随配置转换移动。旧配置确定 `frontier` 后暂停纳入；新配置完成重分享、暂存安装，并且源配置形成退役记录后，才成为唯一所有者并恢复同一实例的纳入。确认之前，旧配置是唯一可恢复来源，但冻结的旧实例不可写；确认后若退役条件未满足，原实例继续冻结，新配置仍可处理其他实例。达到配置服务规定的放弃条件后，实例进入 `abandoned`，合格客户端改用新实例提交。失败确认只允许重试交接；恢复旧配置写入需要有明确的撤销转换记录，不能由超时触发。

## 4. 配置变化期间的服务行为

配置转换发生时，服务按照窗口记录作出决定：

```text
for each window sid known to C_r:
    if sid is committed or sealed:
        publish sealed record to C_{r+1}
    else if sid has a verifiable live record and SC6 holds:
        transfer live record to C_{r+1}
    else:
        retain sid at C_r until completion, retry handoff, or mark abandoned

route new client updates to C_{r+1}
```

这条规则允许旧配置和新配置在短时间内并行服务，但每个窗口只有一个能够接受新更新的当前配置。窗口归属由记录中的配置编号和 `frontier` 决定，消息到达顺序不会改变已接受更新的归属。新配置可以立即创建新的聚合实例，因此交接不会暂停整个训练服务。

成员事件的处理顺序固定为：身份或配置请求先获得确认，随后写入后继配置记录，最后在配置生效点改变服务资格。请求到达本身不改变活动窗口的写入权，也不改变已经发布的模型结果。

### 4.1 新成员加入

新客户端先完成身份认证，获取当前实例的模型版本和保护上下文，再提交更新。它不需要参与旧实例的密钥协商，也不获得旧实例的恢复材料。

新委员会节点先获取配置历史和 `Auth_{r+1}`，再从后继配置得到阈值份额。对于跨配置的活动窗口，新节点只安装经过验证的 `live record` 和 `Share_{r+1,sid}`；已封存窗口只提供模型结果、参与集合和封存边界。

### 4.2 成员退出

客户端退出只停止后续更新提交。已经由旧配置接受的更新仍然进入原实例。尚未接受的更新在退出生效后不得重新提交；重新加入并重新取得资格的客户端根据当前模型版本和实例状态决定是否重新训练、重提到原实例或进入新实例。

委员会退出请求由配置服务确认后形成后继配置。退出节点在新配置生效后停止接收新实例和活动实例的新写入；已经由旧配置接受的聚合份额通过交接转移给后继配置。交接确认前，旧配置保留满足恢复门槛的唯一活动状态；交接确认后，退出节点删除活动份额和旧写入状态，只保留交接回执。若该条件无法满足，实例保持冻结或进入 `abandoned`。

### 4.3 节点崩溃和恢复

崩溃不会自动改变配置。只要剩余节点满足当前恢复门槛，活动窗口继续处理；否则窗口保持可恢复状态，等待旧配置或后继配置完成交接。恢复节点先读取最新配置记录和窗口记录，再处理消息。若恢复节点已经属于后继配置，它只安装不低于当前 `generation` 的记录；旧配置的重复恢复材料不能覆盖更高版本的窗口记录。已提交或已封存窗口的恢复请求只产生拒绝结果。

恢复节点若未被纳入后继配置，不重新获得旧写入权。它可以提交已经保存的交接材料，由当前配置按记录版本判断是否可用；该行为属于恢复事件，不属于一次新的委员会配置。

### 4.4 迟到和重复消息

每条消息携带窗口标识、模型版本、配置编号、记录版本和保护上下文版本。服务根据窗口记录和 `frontier` 判断其是否仍属于当前计算。迟到消息可以被保存为诊断信息，但不能改变已提交结果、重新纳入客户端更新或触发旧窗口恢复。旧上下文的消息不会被转换成新上下文的可写状态。

### 4.5 活动状态交接

一次活动实例交接包含以下记录：

```text
H_sid = (
    sid, model_version, owner_configuration,
    successor_configuration, frontier, generation,
    accepted_update_ids, transition_record
)
```

旧配置先固定 `frontier`，暂停该实例的接收，再导出受保护聚合状态和 `H_sid`。后继配置验证配置转换记录、活动记录版本、已接受更新集合和共享重分享结果，暂存 `generation + 1` 的保护上下文并返回安装确认。安装确认只证明后继状态已暂存，不改变写入权；旧状态仍是唯一恢复来源。旧配置形成退役回执后，实例进入 `confirmed`，后继配置才恢复纳入和开启。无法形成退役回执时，实例保持冻结或进入 `abandoned`。

客户端已经被旧配置接受的更新组成不可回退的前缀。处于传输中的更新若尚未进入 `accepted_update_ids`，需要在清除完成后重新按资格、模型版本和后继代数核验，并进入同一未完成实例的后缀；封存或放弃的实例把合格更新导向新实例。保护后端须让旧前缀和新后缀沿用同一 LWE 公共参数和窗口阈值公钥，把窗口解密秘密的份额重分享给后继委员，并继续累加后继提交的系数密文。客户端提交使用公开窗口密钥，不依赖委员会成员名单。

交接过程中的密钥变化遵循以下规则：身份认证密钥可以保持有效，配置级阈值上下文必须刷新，活动实例的逻辑聚合值保持不变但共享份额必须重分享。已封存实例不执行密钥交接；后继配置只安装封存记录。前向安全或后向安全只能保护密钥泄露影响范围，不能决定更新归属和封存边界。

## 5. 服务不变量

实验和论文实现共同检查以下不变量：

### I1. 窗口归属唯一

对任意 `sid`，在任意时刻至多存在一个配置可以接受新的客户端更新。

### I2. 客户端纳入单调

已纳入集合只增加到窗口封存为止；同一 `(sid, client_id, update_version)` 至多贡献一次。

### I3. 模型版本单调

服务发布的模型版本按照窗口记录推进，不因配置转换或节点恢复回退。

### I4. 交接可继续

后继配置只有在有效 `live record`、新的阈值共享上下文和实例级交接可用性条件同时成立后，才能从 `generation + 1` 继续未完成窗口的计算，并保留已纳入更新的决定。

### I5. 封存不可改

`committed` 窗口的模型结果和参与集合在任何后续配置中保持不变；`sealed` 状态进一步表明旧可写状态已经退役。

### I6. 迟到消息不产生训练效果

属于旧配置、旧模型版本、旧记录版本、旧保护上下文或已提交窗口的消息不会改变模型结果和参与集合。

### I7. 客户端资格单调

客户端退出后产生的更新不能进入退出生效前已经封存的实例；客户端重新加入后使用新的提交资格和当前保护上下文，不恢复旧实例的写入权。

### I8. 配置上下文隔离

不同委员会配置使用不同的阈值共享上下文。后继配置可以验证并安装活动实例的重分享结果，但不能使用旧配置的份额直接写入或恢复已经封存的实例。

## 6. 故障轨迹

每条故障轨迹由客户端到达序列、配置转换序列和节点事件序列组成。评估至少覆盖以下轨迹：

| 轨迹 | 事件顺序 | 观察重点 |
|---|---|---|
| `T1` | 聚合期间发生配置转换 | 新窗口推进，旧窗口是否完成或顺利转移 |
| `T2` | 未完成窗口交接后旧节点离开 | 已纳入更新是否保留，窗口是否继续完成 |
| `T3` | 封存前后分别到达同一迟到消息 | 结果是否保持一致，消息是否正确拒绝 |
| `T4` | 客户端加入后提交，随后退出 | 加入前消息是否拒绝，退出后的更新是否进入新实例 |
| `T5` | 委员会节点加入并参与活动状态交接 | 新份额是否安装，旧上下文是否失去写入权 |
| `T6` | 委员会节点退出后尝试恢复旧状态 | 旧节点是否只能提供交接材料，不能恢复写入权 |
| `T4` | 配置转换期间节点崩溃并恢复 | 恢复后的记录版本和模型版本是否单调 |
| `T5` | 连续两次配置转换 | 多个窗口是否按各自归属推进 |
| `T6` | 客户端高延迟和委员会高 churn 同时出现 | 训练质量、窗口完成率和服务延迟 |

这些轨迹描述真实服务事件。它们既可用于仿真，也可用于后续真实联邦学习部署的故障注入。

## 7. 基线对照

所有基线使用相同的客户端到达、模型、网络延迟和配置转换轨迹。

| 基线 | 窗口处理方式 | 预期比较问题 |
|---|---|---|
| `Static` | 委员会固定，配置转换期间停止成员变化 | 固定成员的性能上限 |
| `Full-transfer` | 配置变化时迁移所有窗口材料，包括已封存窗口的完整记录 | 全量迁移对延迟和历史记录的影响 |
| `Periodic-rekey` | 以固定周期重建聚合相关状态 | 已有窗口继续由旧配置完成，新窗口等待转换完成 |
| `Selective-finality` | 仅转移未完成窗口，封存窗口只传封存记录 | 本文连续性和结果终结性的综合代价 |

`Full-transfer` 是普通动态交接基线，`Periodic-rekey` 是常见的密钥更新型基线，`Static` 用于隔离成员变化本身的代价。基线先比较服务行为，再比较密码学实现成本。

## 8. 评估指标

### 8.1 训练效果

- 窗口完成率和客户端纳入率；
- 模型版本推进速度；
- 客户端更新陈旧度；
- 固定训练时间或固定客户端预算下的模型质量。

### 8.2 服务开销

- 配置转换延迟；
- 未完成窗口交接延迟；
- 节点恢复延迟；
- 每个客户端和每个配置的通信量；
- 持久窗口记录大小。

### 8.3 结果一致性

- 重复纳入次数；
- 被拒绝的迟到消息数量；
- 模型版本回退次数；
- 在相同故障轨迹下不同执行得到的最终参与集合和模型结果是否一致。

安全性只报告与系统行为直接相关的结果：封存窗口是否出现重新纳入、旧记录是否被后继配置接受、以及单客户端开启接口是否在封存后仍可达。详细原语证明保留在安全性小节，不作为系统实验主体。

## 9. 最小实现接口

系统实现只需要以下接口：

```text
submit_update(sid, model_version, client_id, protected_update)
accept_update(sid, update_version)
finalize_window(sid)
export_live_record(sid, configuration)
install_live_record(record, transition_certificate)
publish_sealed_record(sid)
handle_late_message(message)
recover(configuration_record, window_records)
```

接口的具体消息格式可以随实现调整，但必须保留窗口标识、模型版本、配置编号和记录版本。密码学实现通过 `protected_update`、聚合结果释放和记录清除接口接入，不改变窗口状态规则。

## 10. 论文实验的最小闭环

第一步使用确定性事件驱动模拟器验证 I1-I8 和 T1-T6。第二步把同一窗口调度规则接入已有异步 FL 框架，测量真实模型训练中的客户端纳入率、陈旧度和模型质量。第三步替换不同安全聚合实现，比较保护开销与交接开销的相对大小。

论文的主要实验图应围绕以下关系组织：

```text
committee churn
    -> window transfer and finalization behavior
    -> training continuity and model quality
    -> communication, recovery, and persistent-record cost
```

这条闭环将动态成员、异步训练和隐私终结放在同一个可复现实验对象中。密码学组件用于支撑该对象，系统行为决定论文的主要评价。

## 11. 当前决策

首个实现版本固定四类窗口状态、一个后继配置、一个未完成窗口交接路径和一个已封存窗口拒绝路径。成员变化先覆盖加入、退出和崩溃恢复，再扩展连续多次转换。该范围足以验证论文主张，并为后续完整联邦学习实验提供稳定接口。

成员事件回放已经显式记录 `frontier`、`generation`、保护上下文版本、交接阶段和确认失败路径。下一项工作是先完成系数域阈值保护的阶段 D 微基准，核对系数导出、曲线密文聚合、有界点表解码和活动窗口密钥重分享；Buffalo 原生运行保持为固定委员会性能基线。

## 12. 事件轨迹输入

为保证基线比较只改变窗口处理规则，所有执行使用同一组事件轨迹。轨迹中的 `order` 是模拟器用于确定事件顺序的逻辑序号，不代表协议拥有全局时钟；真实实现仍按异步消息到达处理。

每条事件至少包含：

```text
order, kind, configuration, window, model_version,
client, node, record_version, protection_context, source_window, delivered
```

阶段 A 的实现还需要以下扩展字段：

```text
update_id
source_update_id
source_generation
target_generation
handoff_attempt_id
rejection_reason
retrained
```

窗口摘要同时保存：

```text
accepted_update_ids
accepted_update_log
frontier_update_ids
active_configuration
owner_configuration
recoverable_owner
generation
handoff_status
erase_status
sealed_state_bytes
state_change_after_seal
```

`accepted_update_log` 按接受顺序记录更新；`frontier_update_ids` 是冻结时的接受快照。`active_configuration` 可以先于活动窗口所有者变化，`handoff_confirm` 只确认后继状态已经安装，`owner_configuration` 和 `generation` 在旧配置返回退役回执后变化，`recoverable_owner` 在此之前保留旧配置。事件日志是摘要的来源，摘要不能替代逐事件记录。

事件类型为：

| `kind` | 必要字段 | 作用 |
|---|---|---|
| `client_update` | `window`, `client`, `model_version` | 客户端提交一个受保护更新 |
| `client_resubmit` | `source_window`, `window`, `client`, `model_version`, `protection_context` | 接收截点后的更新在后继实例重新提交 |
| `client_join` | `configuration`, `client`, `model_version` | 客户端从指定模型版本起获得提交资格 |
| `client_leave` | `configuration`, `client` | 客户端停止后续提交，不撤销已接受更新 |
| `config_install` | `configuration` | 登记后继配置并开始配置转换 |
| `committee_join` | `configuration`, `node` | 节点加入指定后继委员会并获得新阈值份额 |
| `committee_leave` | `configuration`, `node` | 节点从后继委员会中退出并失去写入权 |
| `node_leave` | `configuration`, `node` | 节点停止提供服务 |
| `node_crash` | `configuration`, `node` | 节点暂时停止响应 |
| `node_recover` | `configuration`, `node`, `record_version` | 节点按记录恢复 |
| `message_deliver` | `configuration`, `window`, `record_version`, `delivered` | 交付或丢弃一条交接/恢复消息 |
| `handoff_confirm` | `configuration`, `window`, `record_version`, `protection_context`, `delivered` | 后继配置确认或拒绝安装活动状态 |
| `handoff_abandon` | `configuration`, `window`, `delivered` | 交接条件无法满足时终止该实例的可写后继状态 |
| `window_finalize` | `configuration`, `window`, `model_version` | 生成 `Commit_sid` 并进入只读阶段 |

epoch-bounded mobile adversary 场景在同一轨迹中使用以下扩展事件：

| `kind` | 必要字段 | 作用 |
|---|---|---|
| `node_corrupt` | `configuration`, `node` | 敌手取得节点当前服务状态并控制其后续行为 |
| `node_release` | `configuration`, `node` | 敌手释放节点，节点回到协议规定的服务状态 |
| `recover_state` | `configuration`, `window`, `node`, `record_version` | 恢复节点请求安装指定版本的窗口状态 |

扩展事件只描述节点控制、释放和状态恢复，不表示任何密码学开启操作。回放器根据窗口记录判断恢复请求是否属于活动窗口、已交接窗口、已放弃实例或已封存窗口，并记录对应的接受、转移或拒绝结果。当前 `experiments/reconfigurable_fl_sim.py` 已支持客户端加入、客户端退出、委员会加入、节点可用性、恢复、`handoff_confirm` 和 `handoff_abandon` 事件；确认失败时保留旧配置的活动状态，达到放弃条件时停止该实例的可写后继状态。每个 epoch 的控制节点数量应满足 `f_r` 上限，活动窗口交接后安装新的保护上下文并清除旧可写状态。

一个最小轨迹可以写成（仓库中的样例为 `experiments/reconfigurable_trace.csv`）：

```text
order, kind, configuration, window, model_version, client, node,
record_version, protection_context, source_window, delivered
1, client_update, C0, sid-0, v0, u0, -, 1, true
2, client_update, C0, sid-0, v0, u1, -, 1, true
3, window_finalize, C0, sid-0, v0, -, -, 1, true
4, config_install, C1, -, -, -, -, -, true
5, node_leave, C0, -, -, -, p0, -, true
6, message_deliver, C1, sid-0, v0, -, -, 1, true
7, client_update, C1, sid-1, v1, u2, -, 1, true
8, node_recover, C1, sid-0, v0, -, p1, 2, true
```

基线执行器对同一轨迹只替换以下决策：是否迁移活动窗口、是否接受迟到记录、何时确定窗口结果，以及配置变化期间是否暂停新窗口。执行器输出统一字段：

```text
window, final_status, final_model_version, owner_configuration, accepted_clients,
resubmitted_updates,
handoff_delay, completion_order, rejected_messages, retained_record_bytes
```

这样可以分别观察训练结果、服务连续性和记录开销。轨迹生成器 `experiments/generate_reconfigurable_trace.py` 提供固定种子、窗口并发度、客户端数量、成员变化序列和节点故障序列；epoch-bounded mobile adversary 事件沿用同一轨迹格式。基线只读取生成后的轨迹文件。消息延迟和交付顺序可以在同一格式上由其他调度器替换。

事件轨迹通过以下三项校验后进入真实 FL 运行：

1. 同一轨迹在 `Static`、`Full-transfer`、`Periodic-rekey` 和 `Selective-finality` 下都能结束或明确报告未完成窗口；
2. 同一窗口的客户端更新顺序和成员事件顺序在所有基线中保持一致；
3. 输出能够重建每个窗口从 `accepted` 到 `transferred`、`confirmed`、`committed`、`sealed` 或 `abandoned` 的路径。

`window_finalize` 必须来自窗口当前所属的可服务配置，且该窗口已经被接受。周期重建策略在旧窗口全部完成前保留旧配置作为当前配置，因此配置转换期间到达的新窗口更新会被等待或拒绝；已有窗口仍可继续收集更新并完成。

## 13. 阶段 A 的确定性轨迹

阶段 A 在接入真实训练前计划固定四条轨迹：

| 轨迹 | 关键执行 | 必须证明的语义 |
|---|---|---|
| `A1-handoff-failure` | 确认失败、旧配置恢复、同一交接重试 | 失败确认不产生第二个写入副本，旧配置保持唯一恢复来源 |
| `A2-stale-generation` | 后继配置安装后发送旧代数恢复、确认和写入 | 代数递增，旧代数消息全部失效 |
| `A3-sealed-rejection` | `Commit` 或 `Seal` 后同时交付迟到更新、旧交接和恢复请求 | 结果记录吸收后续消息，状态和结果不再改变 |
| `A4-handoff-abandon` | 交接条件不足，实例放弃并重新提交到新实例 | 原实例不可写，重提实例可以独立完成，其他实例继续推进 |

四条轨迹的事件字段使用 `update_id`、`source_update_id`、`source_generation`、`target_generation` 和 `handoff_attempt_id`。实现必须同时输出逐事件结果和窗口摘要，摘要能够定位所有被接受的更新、frontier 快照、所有者历史、擦除收据和封存后状态变化。

阶段 A 的验收依据是逐事件日志：确认失败时保留旧配置恢复来源；退役回执后由后继配置接收更新；结果确定后保持参与集合；放弃实例停止写入，重提请求按新实例规则处理。安装确认和退役之间允许旧配置为完成交接保留状态。四条固定轨迹保存在 `experiments/phase-a-traces/`，由回放器逐事件核验。
