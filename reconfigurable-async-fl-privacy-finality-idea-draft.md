# Privacy Finality under Committee Reconfiguration in Asynchronous FL

> 文档定位：动态委员会版本的论文思路稿，不是论文初稿。本文档先固定问题、系统模型、攻击轨迹和方案方向，暂不把尚未完成的密码学实例化写成既成结果。

## 1. 一句话叙事

异步联邦学习需要在客户端到达不齐、委员会节点退出和节点恢复的情况下持续推进模型。委员会变更能够维持服务，却也会把历史恢复状态交给新的成员。本文研究一种配置交接规则：**live state 可以随委员会迁移，已经完成训练的窗口只能留下封存事实，不能把单客户端更新的开启能力带到下一届委员会。**

## 2. 研究背景

跨设备、跨机构和边缘 FL 的客户端具有不同的计算速度、在线时间和网络条件。异步 FL 不等待一个同步轮次的所有客户端，而是根据持续到达的更新形成训练窗口，及时推进模型版本。Secure aggregation 保护聚合期间的单客户端更新，但长期服务还要处理委员会崩溃、节点修复、成员加入退出和配置交接。

动态异步 BFT 已经研究了纯异步网络中的配置变更。相关工作使用配置证明、节点追赶和阈值密钥刷新，让共识跨越委员会变化继续运行。它们的阈值密钥交接目标是让新配置继续获得共识所需的密码学能力。

异步 FL 的目标有一处不同：训练窗口已经输出后，单客户端更新的开启能力应当退出后续恢复路径。若新委员会接收旧窗口的阈值份额、修复材料或待处理转录，动态配置就可能成为历史更新的重新开启通道。于是委员会交接不只是可用性问题，也是 secure aggregation 的隐私边界。

### 2.1 文献定位

现有工作已经分别覆盖了动态客户端、异步缓冲聚合和动态委员会密码学。`Setup Once, Secure Always` 允许用户动态参与并处理用户掉线，但其聚合服务器在整个训练期间保持在线。`Buffalo` 将 secure aggregation 带入 buffered asynchronous FL，并讨论 assistant 掉线；当 assistant 集合变化时，现有 pairwise key 关系需要重建，share transfer 也会改变成本和协议路径。异步 Byzantine 聚合工作则采用固定的多聚合器集合，重点是网络延迟、聚合器故障和客户端纳入。

这些工作留下一个不同的问题：**聚合权威变化时，已经进入异步训练过程的客户端更新由谁继续处理，已经形成的模型结果又如何跨越配置变化保持稳定？** 动态客户端参加训练，不等于聚合委员会能够安全交接；动态拓扑，也不等于在途安全聚合状态能够转移。

## 3. 核心研究问题

> **在完全异步的委员会变更下，如何让正在形成的联邦聚合跨配置继续产生模型更新，并使已经确定的聚合结果成为不可重新开启的隐私边界？**

这个问题包含三个服务目标：

1. 新配置能够接收新训练窗口，旧配置能够处理正在完成的窗口；
2. 未完成的窗口可以在必要时交接当前可用状态，不因一次成员变更丢失全部训练工作；
3. 已经确定结果并完成 `Seal_sid` 的实例不会因未来配置交接和状态暴露重新打开单客户端更新。

## 4. 为什么委员会重配置改变了研究问题

动态成员不是把固定委员会中的 `P` 改成 `P_r`。配置交接会改变谁持有恢复状态、哪些消息仍然有效以及未来能够运行哪些恢复操作。它因此引入了固定委员会不存在的路径：

```text
old committee state
    -> configuration transition
    -> state handoff
    -> new committee state
    -> future recovery
```

如果交接规则只保证阈值秘密连续可用，历史 `sid` 的能力也可能连续可用。本文的贡献应当落在委员会重配置下的隐私终结：委员会变化时，活动窗口继续训练，已完成窗口的单客户端保护边界随结果一起终结。

## 5. 动态异步 FL 系统模型

### 5.1 训练窗口与委员会配置

客户端更新按异步到达顺序进入候选窗口 `sid`。委员会配置写为：

```text
C_0, C_1, C_2, ...
```

每个配置包含成员集合、签名验证信息、聚合门槛、恢复门槛和配置编号。窗口描述符绑定配置：

```text
D_sid = (sid, model_version, S_sid, w_sid, C_sid, H_ct, H_out).
```

`CC_sid` 固定窗口的客户端集合、权重、模型版本和配置上下文。配置切换不依赖全局时钟，而由节点根据已经认证的配置转换记录推进本地状态。

### 5.2 配置变更

加入和退出请求通过异步成员变更协议处理。一次配置变更产生认证的 transition certificate，证明新配置 `C_{r+1}` 是由旧配置 `C_r` 接受的后继配置。新旧配置可以在短时间内并存：旧配置排空已经接收的窗口，新配置负责后续窗口。

完全异步环境中，配置证书不能只依赖沉默判断。系统需要使用异步一致机制、可验证配置证明，或明确的成员管理权威。若节点离开后停止发送，未交付消息可以被调度器丢弃；协议不能等待离开节点完成后续重传。

每个配置需要单独满足成员规模与故障条件。动态异步 BFT 工作中的成员规模条件通常同时考虑 Byzantine 节点和诚实离开造成的消息遗漏。本文不能直接采用某个共识不等式，因为还要分别满足窗口聚合、隐私封存、状态交接和恢复活性。

### 5.3 状态分类

对每个 `sid`，委员会状态分为两类：

```text
live state:
    未封存窗口继续训练或恢复所需的当前份额和恢复材料

sealed record:
    sid、模型版本、参与集合、frontier、配置历史和封存证明
```

配置交接只允许传递未封存窗口的 live state。已封存窗口向新配置传递 sealed record，不传递 direct share、repair share、pending plaintext、endpoint key 或旧恢复转录。

### 5.4 故障与受 epoch 约束的移动敌手

网络允许消息任意延迟、重排和重复；离开节点相关的未交付消息可以因节点停止执行而遗漏。本文采用每个 epoch 具有控制上限的移动敌手模型。一个 epoch 对应一个配置周期 `C_r`，敌手在该 epoch 内最多控制并读取 `f_r` 个委员会节点。相邻 epoch 可以选择新的节点，已经读取的内容继续保留在敌手视图中。活动窗口跨越 epoch 时使用后继配置的新保护上下文，交接完成后旧状态必须擦除。

敌手不获得任意历史数据库查询接口。它只能观察公开配置记录、异步消息和模型版本，并执行协议允许的节点控制、释放、恢复、成员变更和状态暴露操作。敌手根据已经观察到的配置和消息自适应选择下一步操作。这个模型描述长期自适应服务环境，同时保留每个配置周期和每个活动窗口的可分析边界。

## 6. 跨配置状态复活攻击

攻击名称暂定为 **State Resurrection across Configurations**。

### 6.1 攻击目标

目标是一个已经进入模型输出、但其状态仍可能被旧委员会或新委员会引用的训练窗口 `sid`。攻击者不篡改模型输出，也不破解底层加密，而是利用合法的配置交接和恢复路径积累开启能力。

### 6.2 攻击轨迹

```text
1. 选择目标窗口 sid，并等待 CC_sid 和模型输出 Y_sid 发布。
2. 观察旧配置中尚未完成的封存、修复请求和成员退出请求。
3. 延迟旧配置发送的 repair/handoff 消息，使其跨过 `Commit_sid` 或配置切换边界。
4. 在旧配置中读取部分状态，释放节点，再根据公开 transition certificate
   选择新配置中的腐化节点。
5. 让新配置按照普通 recovery/handoff 规则安装旧 generation 或其等价状态。
6. 继续移动读取不同配置的当前状态、缓冲区和恢复转录。
7. 若这些对象共同形成 sid 的授权开启集合，则打开一个客户端更新，或区分
   两组具有相同授权聚合的客户端更新。
```

该攻击的适应性来自时序选择：下一次腐化对象、交接时机和恢复目标由已经公开的配置状态与消息延迟决定。它不是自适应查询模型，因为每一步都是真实协议中的配置、网络、恢复或腐化操作。

### 6.3 两个具体攻击分支

**分支 A：封存后的迟到交接。** 旧委员会在 `Commit_sid` 前生成恢复材料，网络将其延迟到结果确定后；新委员会仍接受该材料并安装旧状态。此时结果确定没有支配迟到消息，`sid` 的旧能力跨配置复活。

**分支 B：活动状态交接残留。** `sid` 尚未完成 `Seal_sid` 时，旧委员会将状态交给新委员会，但旧委员会未能形成退役记录。敌手先后读取旧、新配置的份额，形成跨配置的旧开启集合。因此 `Seal_sid` 必须覆盖所有曾经持有该状态的配置。

### 6.4 攻击成立的条件

攻击需要至少一个以下条件：

- handoff payload 没有绑定 `sid`、generation、configuration 和 frontier；
- 新配置只验证状态来源，不验证该窗口是否已经封存；
- sealed window 的旧 share 或 recovery state 被当作普通 handoff state 传递；
- 旧配置在交接确认前没有完成擦除，且新配置已经可以恢复；
- 已发出的旧消息在新配置中仍然可以产生有效安装结果。

这些条件构成针对动态异步 BFT/DPSS/普通阈值刷新方案的统一审计入口。具体方案是否满足某个条件，需要逐篇核对其状态和消息语义，不能根据论文标题判断。

### 6.5 最小两配置攻击实例

为了避免把攻击写成抽象的“长期暴露”，先固定两个配置 `C_0` 和 `C_1`，以及一个已经生成 `CC_sid` 和 `Y_sid` 的窗口。设 `C_0` 中的旧状态通过合法 handoff 规则产生 `C_1` 可安装的 `sid` 状态。令 `H_0` 和 `H_1` 分别表示两个配置中能够参与该窗口恢复的正确节点集合。

攻击者按下面的自适应轨迹行动：

```text
t0: 观察 sid 已经输出 Y_sid，但没有看到完整 Commit_sid。
t1: 读取 C_0 中一部分 sid 状态，保留为 X_hist；延迟 C_0 的 handoff 消息。
t2: 观察到 C_0 -> C_1 的有效配置证明后，选择 C_1 中的恢复目标。
t3: 让 C_1 接收迟到 handoff，或让 C_1 按普通规则请求 sid 的恢复状态。
t4: 读取 C_1 的当前状态，并释放 t1 时控制的节点。
t5: 触发合法的 repair/recovery；若旧 frontier 没有支配 handoff，得到旧 sid 状态。
t6: 检查 C_0 与 C_1 的已读状态是否共同满足 sid 的解密门槛。
```

攻击的成功条件可以写成：

```text
H_old = Cl_rec(X_hist union X_current union HandoffEdges)
H_old contains D,
for some D in Gamma_dec^cap(sid).
```

这条轨迹保持每个配置周期的暴露上限和窗口暴露额度。适应性只用于根据 `CC_sid`、配置证明、消息到达和本次状态读取结果选择下一步操作。若 `C_1` 只收到 sealed record，旧配置的 `sid` 状态已完成退役，且旧 handoff 在 frontier 检查中无法安装，则该攻击分支无法形成有效开启集合；这正是方案需要实现和实验验证的边界。

### 6.6 攻击对象的边界

本文审计的是动态异步 BFT 或动态状态共享机制与 FL 安全聚合的组合接口。动态共识协议通常保证后继配置继续获得共识能力，动态状态共享通常保证后继委员会继续恢复一个长期秘密；本文进一步检查这些能力是否被错误地用于恢复已经封存的 FL 聚合实例。

如果候选机制没有定义客户端密文、聚合实例标识和封存事件，论文结论应写成“组合接口未覆盖该应用状态”。如果候选机制把历史聚合实例的保护状态直接放入配置交接，本文的两配置轨迹可以检验该状态是否能够跨配置重新进入恢复路径。

## 7. 方案方向：以状态交接封闭隐私终结

### 7.1 按窗口绑定配置

每个窗口由 `CC_sid` 绑定到形成该窗口的配置。配置变更只改变后续窗口的服务归属，不自动改变历史窗口的客户端集合、权重或隐私状态。

### 7.2 新旧配置并行推进

配置变更期间，旧配置处理已接收的实例，新配置处理新的客户端更新。这样委员会变更不会要求模型服务器暂停全部训练。对于尚未确定结果的实例，服务可以取消并重新提交；对于已经生成 `CC_sid` 但尚未 `Commit_sid` 的实例，系统需要使用活动状态交接完成转换。

这里的“已接收”指旧配置已经把更新写入实例记录，而不是客户端已经发送了消息。异步网络无法提供一个所有节点共享的发送时间，因此协议以实例记录中的接收截点决定归属。截点之后到达的旧上下文更新进入后继配置创建的新实例。

### 7.3 只交接活动状态

未封存窗口可以交接当前 generation 的状态。交接记录绑定：

```text
(sid, model_version, generation, C_old, C_new, frontier, transition_certificate)
```

`frontier` 由旧配置的成员管理协议确认，并记录旧配置已经接受的更新集合及其记录版本；它不能由单个节点声明。一次交接满足以下实例级可用性条件时，后继配置才能继续该实例：旧配置中足够的诚实服务节点完成可验证的前缀导出，后继配置安装通过验证，且旧状态产生可验证的退役记录。这里的“足够”由旧配置的恢复门槛决定，不要求所有旧节点在线。若条件暂时不满足，实例保持冻结；若旧配置在最终离开前无法满足条件，实例转入 `abandoned`，已接受前缀不被后继配置伪造为可写状态，合格客户端改用新实例继续训练。新实例和其他活动实例不受该单个实例的交接结果影响。

### 7.3.1 交接协议的具体步骤

交接采用单写者规则。配置转换开始后，一个活动实例先由旧配置固定当前接收边界，随后由新配置取得唯一的写入权。旧配置和新配置可以同时存在于网络中，但它们不能同时修改同一个 `sid`。

```text
1. Freeze:
   old configuration fixes frontier_sid and stops new admissions for sid.

2. Export:
   old configuration exports the threshold shares of the aggregate state,
   the accepted update identifiers, model version, generation, and frontier.

3. Certify:
   old configuration certifies H_sid with the configuration transition record.

4. Install:
   new configuration verifies H_sid and installs the live state under
   generation + 1, using the same window public key and the successor
   configuration's refreshed key shares.

5. Confirm:
   new configuration returns an installation certificate. Old members then
   erase the writable state and retain only the handoff receipt.

6. Resume:
   new configuration completes the accepted updates covered by frontier_sid.
   Updates that were not admitted before the frontier enter a new aggregation
   instance under the successor configuration.
```

这里的 `frontier_sid` 把“继续完成一个活动聚合实例”和“让同一个实例无限接收新客户端”区分开来。交接前已经被记录接受的更新继续完成；交接时仍在网络中的更新按照新实例重新提交。这样模型版本保持连续，单个 `sid` 的写入边界也能在异步网络中明确验证。

交接的状态有两种实现形态。若保护后端支持线性合并的聚合状态，旧配置只需转移一个受保护的聚合累加器、参与集合摘要和恢复门槛信息。若保护后端必须保存每个客户端的保护记录，则交接需要转移活动实例中尚未完成的客户端记录。论文首个实现采用前一种状态表示，逐客户端保护记录作为成本对照。

### 7.3.2 交接的性能组成

一次交接的时间可以分解为：

```text
T_h = T_freeze + T_cert + T_transfer
      + T_refresh + T_install + T_confirm
```

`T_freeze` 是旧配置固定 frontier 的时间，`T_cert` 是配置和状态证明的生成时间，`T_transfer` 是活动状态传输时间，`T_refresh` 是后继配置刷新保护状态的时间，`T_install` 是新配置验证并安装状态的时间，`T_confirm` 是旧状态清除确认时间。只有 `T_transfer` 和 `T_refresh` 必然依赖保护状态大小与委员会规模；其他部分主要受异步消息延迟和证明处理速度影响。

设同时存在 `m` 个活动实例，委员会规模为 `n_old` 和 `n_new`，客户端更新向量维度为 `d`，每个实例已有 `k_sid` 个更新。交接通信量写成：

```text
B_h = B_cert + B_refresh
      + sum_sid B_state(sid)
```

当后端按委员会成员保存聚合份额时，活动实例状态只随委员会规模和模型维度增长，不随客户端更新数量保存逐客户端保护载荷：

```text
B_state(sid) = O(n * d + |A_sid| + B_metadata)
```

一次从 `C_old` 到 `C_new` 的重分享需要读取旧份额并建立新份额，因此交接通信量满足：

```text
B_h = O(B_cert + B_refresh
        + sum_sid ((n_old + n_new) * d
                   + |A_sid| + B_metadata))
```

当后端必须转移每个客户端的受保护记录时：

```text
B_state(sid) = O(k_sid * d + |A_sid| + B_metadata)
```

两者差异决定了交接是否适合真实 FL。本文的优势不是让交接成本与模型维度无关，而是把客户端数量从状态迁移的主项中移除。模型参数很大时，单个活动实例的状态传输可能高于一次普通客户端上传；活动实例较多时，状态传输和密钥刷新会同时放大。因此实验不能只报告一次配置转换的总耗时，还需要报告每个活动实例的状态大小和每个配置成员的通信量。

交接带来的训练损耗有三部分：活动实例在 `T_h` 期间产生的等待，交接后更新产生的额外陈旧度，以及保护状态刷新所消耗的 CPU 和网络资源。新配置仍然可以接收新聚合实例，所以系统不需要暂停整个训练服务。论文应当把该效果与两类基线区分：固定委员会没有交接成本，但无法提供动态成员；全量交接会把已封存记录也纳入迁移，成本随历史状态增长；周期性重建通过暂停或排空活动实例简化转换，却把等待集中到训练路径。

与现有联邦学习工作相比，Buffalo 的固定 assistant 配置在正常运行时没有委员会交接成本；一旦 assistant 集合变化，pairwise key 重建或 share transfer 会产生额外 setup 和通信成本。Setup Once, Secure Always 处理动态用户的加入和退出，但其聚合服务器与中间节点保持稳定，因此没有本文的委员会状态交接。Flower SecAgg+ 将安全聚合放在同步轮次边界，配置变化可以等待轮次结束，代价表现为下一轮启动延迟；本文允许新的聚合实例并行开始，代价表现为活动实例的交接和陈旧度。FedBuff 一类异步 FL 主要承担缓冲和模型推进，不承担委员会保护状态的迁移。

实验中使用以下归一化指标比较交接损耗：

```text
handoff slowdown = (T_dynamic - T_static) / T_static
handoff bytes per active instance = B_h / m
effective staleness increase = tau_dynamic - tau_static
throughput loss = 1 - updates_dynamic / updates_static
model utility loss = accuracy_static - accuracy_dynamic
```

这些指标可以把本文的交接代价与固定委员会异步 FL、安全聚合 setup、全量迁移和周期性重建放在同一张表中。当前阶段不预设交接一定优于所有基线，论文需要证明的是：在相同成员变化轨迹下，只交接活动状态能够用有限的通信和等待代价保持训练连续性，并让已封存状态的迁移成本保持为记录级别。

### 7.4 封存记录规则

`Commit_sid` 生成后，实例的参与集合、聚合值和模型结果固定，进入只读阶段。后续配置只接收 `sid` 的封存记录和 frontier。只有在可写状态完成退役后才生成 `Seal_sid`；任何旧 generation 的 share、repair contribution、pending state 或 endpoint key 都不能成为 `Commit_sid` 之后的交接输入。

### 7.5 迟到消息与恢复

节点先合并已经认证的配置和 frontier，再处理恢复消息。消息若属于旧配置、旧 generation 或已经封存的 `sid`，只能产生拒绝记录，不能产生可安装的旧状态。恢复操作只重建当前配置中仍然 live 的窗口。

### 7.6 密码学组件的选择

本文把密码学组件分成两层。客户端更新沿用 Buffalo 的 RLWE 向量保护。RLWE 密钥先在系数域中表示，再由窗口级阈值 ElGamal 保护；委员会状态使用按窗口组织的可验证重分享，在配置交接时保持同一窗口公钥，并在旧上下文完成交接后清除可写状态。

前向安全加密可以限制密钥泄露对过去密文的影响，后向安全可以限制新成员访问加入前的材料。这两种性质无法单独决定窗口归属、聚合结果何时固定、旧状态如何从交接输入中排除，也无法替代只释放聚合结果的开启接口。每个 epoch 具有控制上限的移动敌手所需的组件组合是：

```text
client update protection
    + per window threshold aggregation state
    + epoch refresh and resharing
    + sealed record exclusion after finalization
    + verifiable erasure of the old writable state
```

其中阈值共享负责跨节点恢复，epoch 刷新负责限制同一活动窗口跨配置的状态组合，窗口封存规则让后继配置只获得结果记录。候选后端为每个活动窗口生成一个随机阈值 ElGamal 密钥，客户端使用窗口公钥加密 RLWE 密钥的有界系数，委员会只持有窗口解密密钥的份额。配置变化时重分享这个随机标量；受保护更新和加密系数保持不变。Buffalo 作为固定委员会安全聚合基线，用于衡量动态能力带来的客户端保护、交接和开启成本。

这里需要区分两个密码学接口。向量保护和聚合密钥累加负责当前实例的客户端更新保护；活动状态跨委员会迁移需要可验证 share transfer，不能把初始份额分发算法直接当作交接协议。窗口服务只接收保护有效性、聚合状态版本和封存结果，`authorize_open`、`partial_open` 和 `combine_open` 共同完成一次绑定最终状态的整体开启，`erase` 在安装确认或封存后调用。PVSS、VSSR 和 Silent Threshold Encryption 作为能力对照，不作为首个默认实现。

前向安全加密可以限制密钥泄露对过去密文的影响，后向安全可以限制新成员访问加入前的材料。这两种性质仍然需要实例接收截点、活动状态重分享和封存后的状态排除；它们是可组合的保护条件，不是本文交接规则的替代品。

## 8. 研究结果的候选层次

### 8.1 动态隐私终结刻画

把配置交接边加入恢复闭包：

```text
Cl_rec^dyn(X) = Cl_rec(X union HandoffEdges).
```

动态 privacy finality 要求在 `Seal_sid` 之后，任何客户端单项开启集合 `D` 都不满足：

```text
D subseteq Cl_rec^dyn(X_current union X_hist).
```

这把固定委员会的访问结构条件推广到跨配置状态交接。

### 8.2 跨配置攻击与性质分离

给出 State Resurrection across Configurations，说明普通动态阈值刷新、普通 recovery handoff 或配置证明链不能自动推出历史 FL 更新的隐私终结。攻击只使用公开协议事件、合法恢复和按周期受界的状态暴露。

### 8.3 系统实现

实现配置感知的窗口分配、旧/新配置并行推进、活动状态交接、封存记录规则、迟到消息处理和崩溃恢复。核心系统指标是训练是否继续推进，以及动态交接增加了多少延迟、通信和持久状态。

### 8.4 系统证据

评估以下场景：

- 不同加入、退出和替换速率；
- 节点在聚合、交接、封存和恢复时崩溃；
- 旧配置与新配置之间的延迟交接消息；
- 旧/新委员会连续移动腐化；
- 多个异步窗口同时处于不同配置；
- 配置切换期间的客户端纳入率、更新陈旧度、模型推进延迟和模型质量。

同时测量配置交接延迟、恢复延迟、通信量、持久状态大小和被拒绝的迟到消息数量。

## 9. 与现有动态异步 BFT 的关系

动态异步 BFT 的配置证明链可以启发我们的配置发现和新节点追赶；其离开节点消息遗漏模型可以启发 FL 服务对退出节点的活性处理；其每配置离开额度可以作为本文恢复和聚合门槛推导的参考变量。

本文不直接使用其 ADKR 的密钥交接语义。ADKR 的目标是让新配置继续拥有共识所需的阈值密码学能力，而本文需要区分共识能力、当前窗口能力和已封存窗口能力。新配置可以获得前两类状态，不能获得第三类状态。

本文也不直接采用其他动态异步 BFT 工作中的成员规模条件。已有条件描述共识在 Byzantine 节点和离开节点下的协议要求；本文需要重新分析：

```text
configuration agreement
aggregate release
handoff of live state
privacy sealing
repair liveness
```

这些条件是否可以共享同一组成员参数，是需要证明和实验共同回答的问题。

### 9.1 面向现有工作的攻击审计

现有工作是否能被攻击，取决于它承载的应用状态。审计对象不是原协议的共识安全，而是把其配置交接机制用于 FL 安全聚合后的组合接口。

| 工作 | 原协议保持的对象 | 对 FL 隐私终结的审计问题 |
|---|---|---|
| 动态异步 BFT | 新配置的阈值密码学能力、配置证明链和共识状态 | 若应用层把某个 `sid` 的旧解密状态放入配置追赶流程，迟到消息和新配置是否能安装该状态 |
| DyCAPS | 旧/新委员会之间不变的秘密 `s` 和刷新后的 share | 若 `s` 是历史窗口的开启秘密，秘密连续性是否直接变成历史窗口可持续开启 |
| Optimistic DPSS | 旧 share 经 reshare 后在新委员会中保持同一秘密，必要时执行 share recovery | `Transfer commitments -> Reshare -> Select -> Recover -> Compute` 是否把未封存和已封存窗口混用 |

DyCAPS 明确允许相邻委员会完全不相交，并在 handoff 中保持秘密值不变；Optimistic DPSS 也把旧 share 重分享给新委员会并保持同一秘密。它们适合维护持续使用的 threshold state，却没有 `Seal_sid` 之后的终端状态。若将历史 FL 实例的解密秘密直接作为这种持久秘密，攻击者可以先后读取旧、新配置的 share，或者等待新配置完成 recovery，从而重新形成旧实例的解密能力。

动态异步 BFT 的情况需要更精确地表述。这类协议解决共识随机性和阈值密码学的配置切换，配置证明链帮助新成员追赶最新配置；原协议通常没有 FL 客户端密文和 `sid` 窗口。因此攻击对象不是动态共识本身，而是检查“配置证明 + FL 窗口解密状态”的组合是否允许旧 `sid` 状态跨配置传播。

### 9.2 攻击的可证伪形式

对任意候选动态交接机制，先标记目标窗口是否满足：

```text
Handoff(old_state, C_old, C_new) -> state_new(sid)
```

若 `state_new(sid)` 能参与旧窗口的 `Recover`、`PartDec` 或等价开启操作，则它是一条跨配置 recovery edge。攻击者只需验证以下两种执行是否都被协议接受：

```text
E1: handoff message arrives before Commit_sid;
E2: the same message arrives after Commit_sid or after C_new becomes current.
```

若 `E2` 仍能安装 `state_new(sid)`，则存在 delayed handoff resurrection。若 `E2` 被拒绝，但 `C_new` 的已安装状态仍可与旧配置暴露状态共同打开 `sid`，则存在跨配置累积。只有当旧状态分类、frontier 检查、交接确认和后续擦除共同阻断这两条路径，动态隐私终结才成立。

这给出一个可重复的文献审计流程：先提取交接消息和状态输出，再将一个 FL `sid` 绑定到这些对象，最后执行两配置自适应调度。审计结果可以是“攻击成立”“攻击被 frontier 阻断”或“原工作未定义该应用状态”，三者不能混写。

### 9.3 公开密文下的会话状态组合攻击

对 DyCAPS/Optimistic DPSS，最小组合实例使用一个普通阈值解密数据层：客户端公开

```text
ct_u = Enc(pk_sid, k_u)
z_u  = x_u + G(sid, k_u)
```

委员会使用 threshold state `s_sid` 处理 mask key。训练完成后，模型服务器已经发布 `Y_sid`，但窗口记录中的 `ct_u` 仍然存在。

若将 `s_sid` 作为 DPSS 的持久秘密，攻击轨迹为：

```text
1. C_0 按 DPSS.Share 持有 s_sid 的 shares，并完成 sid 的模型聚合。
2. C_0 -> C_1 执行普通 DPSS.Handoff；新委员会获得同一 s_sid 的 refreshed shares。
3. Commit_sid 生成后，攻击者请求 C_1 执行合法 Recon/PartDec。
4. C_1 使用持久 threshold state 处理公开的 ct_u，得到 k_u 或其单项解密结果。
5. 攻击者恢复 x_u，或区分两组具有相同聚合值的客户端更新。
```

该攻击需要数据层允许阈值状态对单项 `ct_u` 执行 `Decrypt/PartDec`。如果数据层严格限制为只释放聚合结果的开启接口，单项解密路径被接口隔离；此时仍需检查聚合密文、恢复转录和成员状态是否留下另一条 `sid` capability edge。

攻击的关键不是敌手在 DPSS handoff 中学到了秘密。DyCAPS/Optimistic DPSS 的目标正是让合法新委员会继续拥有秘密的恢复能力。本文要证明的是：在 `Seal_sid` 之后，这种能力对于目标实例应当消失。两种目标分别是：

```text
DPSS secrecy:  未达到门槛的敌手不能得到 s_sid
FL privacy:   达到协议门槛的未来委员会也不能再用 s_sid 打开已封存 sid
```

前者不推出后者。这个区分使组合攻击可以作为系统基线，而不会错误地声称 DPSS 的安全性被破坏。

### 9.3.1 参数化的两配置反例

令 `C_0` 和 `C_1` 分别使用重构门限 `q_0` 和 `q_1`，并令 `s_sid` 是普通 threshold decryption 的秘密。攻击不依赖两个委员会存在成员重叠。`C_0` 完成窗口后，`C_0 -> C_1` 的合法 handoff 使 `C_1` 获得同一 `s_sid` 的 `q_1` 个可用 share。此时：

```text
public transcript:  ct_u = Enc(pk_sid, k_u), Y_sid, CC_sid, Commit_sid, Seal_sid
authorized state:  q_1 shares of the same s_sid in C_1
```

如果 `Seal_sid` 之前没有把 `sid` 从 handoff 输入集合中删除，或 `C_1` 仍把 `sid` 视为可恢复对象，则 `C_1` 的合法 `Recon/PartDec` 可以处理 `ct_u`。敌手先观察 `Y_sid` 和配置变更记录，再选择要求恢复 `sid` 的配置路径；它不需要发出协议外的解密查询。两个等聚合世界只在某个 `x_u` 上不同的情况下，单项 `k_u` 就足以区分这两个世界。

该反例有两个重要边界：

1. 如果聚合接口从根本上拒绝单项 `ct_u`，并且 `s_sid` 只能用于唯一的聚合结果开启，那么“持久秘密直接解密单项密文”的路径消失，但仍需审计聚合密文和恢复转录；
2. 如果 `Seal_sid` 之前已经把 `sid` 从 handoff 输入中删除，并且持有者形成退役记录，`C_1` 只得到 sealed record，则该反例不成立。

因此这个结果不是“DPSS 不能抵抗移动腐化”，而是一个接口分离：**secret continuity 不蕴含应用层隐私终结。**

### 9.4 三类基线的当前可达性判断

**DyCAPS：直接组合风险。** DyCAPS 的 handoff 在旧委员会和新委员会之间保持同一个秘密 `s`，并允许相邻委员会完全不相交。其目标是让 `s` 在委员会变化后继续可重构；如果应用层把历史 `sid` 的解密秘密作为 `s`，则 `C_1` 仍然拥有打开该实例的能力。这里的攻击不否定 DyCAPS 对持续秘密的 secrecy，而是说明持续秘密语义与 `Seal_sid` 的终止语义不能直接重合。只有在每个 `sid` 使用独立状态，并在 `Seal_sid` 后排除该 `sid` 的 handoff，组合才可能满足本文目标。

**Optimistic DPSS：直接组合风险。** 该方案的 `Transfer commitments -> Reshare -> Select -> Recover -> Compute` 将旧 share 重新分发给新委员会，并保持秘密值不变；`Recover` 还可以补足未到达的新 share。若交接对象包含已输出实例的开启状态，攻击者可以利用配置切换后的新 share 或恢复实例重新得到旧能力。方案中旧节点在交接后删除敏感信息有助于减少残留，但它没有定义 `Seal_sid`、sealed record 或按训练实例拒绝旧交接，因此仍需要应用层的隐私边界。

**动态异步 BFT：条件组合风险，原协议本身未定义该应用状态。** 这类协议通过配置证明、节点追赶和阈值密钥刷新支持动态异步共识。其阈值密码学状态主要服务后续共识随机性；原协议通常没有客户端密文、聚合 mask 或 `sid` 历史窗口。只有当 FL 适配层把旧窗口的解密或恢复材料放入配置脚本、追赶状态或交接消息时，本文攻击才有具体输入。若适配层只让新配置处理新的窗口，并且旧窗口在原配置中完成封存，动态共识机制本身不自动产生本文攻击。

因此，文献实验不应统一报告“被攻击/未被攻击”，而应报告：

```text
direct composition risk   -- 原语明确把目标秘密交给新配置
conditional composition   -- 只有应用层把 sid 状态放入交接才触发
application gap            -- 原协议没有定义 FL 状态，无法直接判断
```

## 10. 首篇论文的推荐范围

推荐采用“配置级动态委员会 + 异步窗口并行推进 + 未封存状态交接 + 已封存状态不可复活”的范围。

暂不做：任意时刻任意成员变更、无限制的跨窗口状态转移、通用动态密码学基础设施，以及将所有动态 BFT 的活性问题同时纳入论文。

这一路线既保留系统连续运行的价值，也让动态成员产生明确的新技术问题：**状态交接如何影响已经完成训练窗口的隐私终结。**

## 11. 待验证问题

1. 动态配置的认证来源是否采用已有异步一致机制，还是需要单独的配置服务。
2. 未封存窗口的活动状态交接是否可以在不暴露客户端 mask key 的条件下实现。
3. `Seal_sid` 是否需要收集所有曾经持有 `sid` 状态的配置确认，还是可以由跨配置证明压缩。
4. 旧委员会在交接期间永久离开时，哪些消息可以安全丢弃，哪些状态必须由剩余 helper 恢复。
5. 自适应攻击在 DyCAPS、Optimistic DPSS 和其他动态异步工作中是否都能构造出具体实例。
6. 动态成员带来的主要代价是交接延迟、额外通信，还是持久 tombstone 状态。

## 12. 当前判断

动态成员版本比固定委员会版本更适合作为系统论文主线。它把异步 FL 的持续训练、委员会故障恢复和历史更新保护放进同一个服务问题，同时与动态异步 BFT、DPSS 和现有异步 SA 形成清晰分工。

最终论文要证明的是一个条件性结论：在明确的配置证书、门槛可达性、状态退役和活动状态交接条件下，委员会可以变化，训练可以继续，`Seal_sid` 之后的单客户端更新不会通过跨配置恢复重新出现。

### 12.1 文献核对后的主张边界

本文的研究对象是 **asynchronous federated learning under committee reconfiguration**，而不是一般的动态成员 FL。论文不争夺动态客户端选择、动态聚合权重或常规异步优化的贡献；这些机制作为 workload 和比较背景存在。本文的新增问题位于 FL 服务和安全聚合的交界处：聚合委员会在更新仍在途时变化，系统必须同时处理学习进度、参与集合和历史更新的隐私边界。

由此得到一条更清晰的论文主张：

> 聚合委员会可以在异步训练持续进行时完成配置转换；未完成窗口由后继配置继续处理，已确定窗口只留下封存记录，后续配置不能凭借交接或恢复重新获得其单客户端更新的开启能力。

这条主张比“支持动态节点”更具体，也比单独防止重复计数或消息重放更能体现 FL 系统价值。重复和重放只作为违反窗口参与集合或结果稳定性的可观察表现，不作为论文标题级问题。

### 12.2 基线和比较口径

| 基线 | 在本文中的角色 | 需要改动的边界 |
|---|---|---|
| `Buffalo-native` | buffered asynchronous secure aggregation | 保持原协议，记录其 assistant 集合和 dropout 语义 |
| `Setup-Once-native` | 动态用户安全聚合 | 保持原协议，作为用户动态而非委员会动态的对照 |
| 固定多聚合器异步 Byzantine 聚合 | 聚合器故障和异步消息对照 | 保持固定聚合器集合，记录其窗口与模型推进方式 |
| `Static` | 本文服务的固定委员会对照 | 不注入配置转换 |
| `Full-transfer` | 普通动态交接对照 | 配置变化时迁移全部窗口材料 |
| `Periodic-rekey` | 通过周期重建状态完成转换的对照 | 配置变化期间等待重建完成 |
| `Selective-finality` | 本文候选方案 | 只转移未完成窗口，封存窗口只传封存记录 |

上游安全聚合论文不需要被改写成本文协议。适配层只负责把同一客户端到达轨迹、模型版本和成员事件交给不同后端，并记录窗口归属、参与集合、交接结果和服务成本。这样实验比较的是配置交接语义，而不是把不同论文的优化器和参数调优混在一起。

### 12.3 按周期受界的委员会暴露

每个 epoch 具有控制上限的移动敌手用于检验跨配置状态是否形成历史开启路径。敌手在每个 epoch 内控制不超过 `f_r` 个节点，在相邻 epoch 之间可以根据已观察事件释放旧节点并选择新节点。活动窗口在交接时安装后继配置的新保护上下文，旧 epoch 的可写状态被擦除。这个模型不提供任意历史查询接口，也不把攻击写成对动态 BFT 原语的直接破坏。

论文需要区分两条性质：

```text
secret continuity:
    后继委员会能够继续处理仍在进行的窗口

privacy finality:
    已确定窗口的单客户端更新不再由后继委员会重新开启
```

普通阈值重分享可以提供第一条性质，但第二条性质需要窗口封存、交接边界和恢复规则共同定义。这正是长期滚动腐蚀能够检验的系统设计价值。

### 12.4 敌手模型的既有基础与本文实例化

周期性状态暴露、share refresh 和安全擦除已经在 proactive secret sharing 与动态委员会研究中形成基础。DyCAPS 讨论了按周期选择、释放和重新选择节点，并结合 handoff 与 secure erasure 维持长期秘密。本文沿用这类长期服务事实，将模型对象改成异步 FL 的活动窗口、模型版本和隐私终结事件。

当前 FL 安全聚合论文的敌手模型不同。`Buffalo`、`Setup Once, Secure Always` 和异步 Byzantine 聚合分别处理服务器/assistant 恶意、动态用户和固定聚合器故障，安全分析没有把聚合委员会在多个配置间移动作为主要对象。前向和后向保密能够隔离轮次密钥泄露，但它不决定配置交接后哪些历史 FL 状态仍可恢复。

因此本文定义的是面向 FL 的、每个 epoch 具有控制上限的移动敌手实例，而不是新的通用敌手理论。敌手满足当前 epoch 的控制上限，可以根据公开配置记录、消息到达和恢复事件选择下一步控制与释放；它可以读取被控制节点的当前状态，释放后的历史读取结果继续有效；安全擦除和状态交接由协议明确保证；敌手不获得任意历史查询接口。

本文增加的对象是训练实例 `sid` 和它的隐私终结事件。对 `sid`，敌手视图包含跨配置读取的状态、迟到消息和恢复转录。`Seal_sid` 之后，后继配置只能读取封存记录，敌手视图与后继状态的合法闭包不能形成该实例的单客户端开启集合。这个条件把传统的 secret continuity 与本文的 privacy finality 分开：前者允许新配置继续处理活动实例，后者要求已完成实例不再被重新开启。

论文将该模型放在系统和威胁模型章节，用一段定义和一个两配置轨迹说明。它的作用是检验配置交接是否把历史状态重新带回训练服务，论文的主要证据仍然是模型推进、窗口结果稳定性、交接延迟和状态开销。

## 13. 论文正文四个核心章节的思路稿

前面的章节记录研究问题、攻击轨迹和候选组件。下面给出论文正文的组织方式。它仍然是思路稿，作用是固定每一章回答的问题、使用的概念和需要验证的结论，后续再根据实现结果压缩成正式论文文字。

### 13.1 相关工作：从异步训练到配置交接

相关工作按系统问题组织，而不是按密码学原语排列。

异步和缓冲式联邦学习工作首先解决客户端速度不同带来的等待问题。FedBuff 将多个客户端更新放入缓冲区，再以异步方式推进全局模型；FLSim 提供了可重放的客户端训练和异步调度环境；Buffalo 将安全聚合放入缓冲异步训练，并处理客户端保护、assistant 参与和聚合结果释放。这些工作说明异步训练可以保持模型推进，也提供了本文的训练事件和主要外部基线。它们的聚合权威在一次训练服务中保持固定，因而没有处理委员会改变时在途聚合状态的归属问题。

异步安全聚合工作关注更新保护、掉线处理和聚合完整性。Buffalo 的主要接口适合保护客户端更新，并允许只释放聚合结果。Setup Once, Secure Always 处理动态用户和一次性 setup，但聚合服务器与中间节点保持稳定。两类工作都能作为本文的组件基础和比较对象。本文进一步问的是：当保护状态的持有者本身发生配置转换时，已经完成的聚合是否仍然保持隐私终结。

异步 Byzantine 联邦学习工作，例如 Catalyst，关注延迟、恶意更新和模型鲁棒性。它们提供异步调度和恶意客户端控制的实验方法。本文沿用这类工作对训练质量、更新陈旧度和恶意更新的评价方式，但把委员会状态暴露与客户端 Byzantine 更新分开，避免把两个故障来源混成一个安全结论。

动态异步 BFT 和动态 proactive secret sharing 工作解决配置连续性、成员变化和长期秘密维护。Turritopsis 研究异步共识如何跨越配置变更继续运行；DyCAPS、Optimistic DPSS 和 APSS 研究委员会之间的状态交接、重分享和恢复。这些工作提供配置证书、成员离开和状态转移的设计背景。它们维护的是后继配置继续使用的共识能力或长期秘密，而本文需要表达另一种状态：某个 FL 聚合实例完成后，后继配置只获得结果记录，不能继续获得单客户端更新的开启能力。

前向安全和后向安全可以限制密钥泄露与成员加入之间的时间影响。它们仍然需要一个应用层的状态归属规则，才能判断哪个训练实例已经完成、哪些交接消息仍然有效以及哪个恢复操作必须停止。因此，本文把这些性质视为保护组件的接口条件，而不是用它们替代聚合实例的隐私终结规则。

相关工作最后收束到一个缺口：已有研究分别解决异步模型推进、更新保护、恶意更新和动态委员会，但没有把“在途聚合继续推进”和“已完成聚合不再重新开启”放在同一项联邦学习服务中。本文的方案与实验围绕这个交叉点展开。

### 13.2 安全模型：受 epoch 约束的移动敌手

系统包含客户端集合 `U`、配置序列 `C_0, C_1, ...` 和异步消息网络。配置 `C_r` 包含委员会成员、聚合门槛、恢复门槛和配置证明。一个 epoch 对应一个配置周期。成员可以加入、退出、崩溃并在后继配置中恢复。网络允许消息延迟、重排和重复，离开或崩溃节点造成的未交付消息可以永久缺失。

每个客户端更新属于一个聚合实例 `sid`。实例记录模型版本 `v_sid`、客户端集合 `A_sid`、配置上下文 `C_sid`、当前记录版本 `g_sid` 和结果状态。结果状态从活动变为已封存，封存后只允许读取记录。配置转换可以跨越多个仍处于活动状态的实例。

敌手采用每个 epoch 具有控制上限的移动模型。敌手在 epoch `r` 内最多控制并读取 `f_r` 个委员会节点，可以根据已经公开的配置证明、消息到达和恢复事件选择下一步控制对象。敌手释放旧节点后，已经读取的内部状态仍保留在敌手视图中。敌手可以观察公开记录并控制真实协议中的崩溃、恢复、成员变化和状态恢复操作。它不获得一个可以任意查询历史内部状态的数据库接口，也不把攻击定义为自适应查询。

客户端 Byzantine 行为单独建模。客户端可以提交恶意更新，聚合器按照底层异步鲁棒算法决定纳入规则。委员会节点的状态暴露影响保护状态和恢复路径，客户端 Byzantine 更新影响模型质量。两者在实验中可以组合，证明中分别表述。

本文关注三项性质。第一，窗口归属唯一性：一个客户端更新至多进入一个确定的 `sid` 记录。第二，结果稳定性：`sid` 封存后，迟到消息、恢复消息和后继配置交接不能改变 `A_sid`、模型结果或模型版本。第三，隐私终结：在满足配置转换、状态交接和安全擦除条件时，后继配置与敌手历史视图的联合恢复闭包不能形成 `sid` 的单客户端开启集合。

这个模型给出清晰的适用范围。它允许长期移动控制，也保留每个配置周期的状态暴露上限；它适合描述跨配置状态累积，不承担通用移动敌手理论的建立。对仍处于活动状态的 `sid`，每次配置转换都刷新其保护状态，使不同 epoch 的已读份额不能直接合并成一次有效开启。主定理还需要明确每个 epoch 的控制上限低于该 epoch 的恢复门槛，并要求敌手在单个 epoch 内无法取得完整开启集合。论文需要把 `f_r`、配置门槛、刷新条件、擦除条件和活动实例数量作为系统参数报告。若敌手在某个 epoch 内已经取得完整开启集合，本文只保证结果稳定性，隐私终结不覆盖这次暴露。

### 13.3 协议方案：按聚合实例决定可交接状态

协议把每个聚合实例表示为：

```text
R_sid = (sid, v_sid, C_sid, g_sid, A_sid, q_sid,
         state_sid, result_sid, frontier_sid)
```

其中 `state_sid` 是聚合值的阈值共享，只包含继续完成活动聚合所需的保护状态，不包含客户端明文或逐客户端开启材料；`result_sid` 在封存前为空，`frontier_sid` 记录旧配置已经接受的更新集合和记录版本。记录分为活动记录和封存记录。活动记录可以交给后继配置，封存记录只携带实例标识、客户端集合、模型结果、配置证明和封存证明。

客户端更新按照到达顺序提交给当前配置。当前配置先检查实例状态、模型版本、记录版本和客户端标识，再决定是否纳入。配置变更产生由旧配置确认的后继配置证明。旧配置冻结已经接收的活动实例；新配置可以同时开启新实例，并在交接完成后继续填充未完成的原实例。

交接记录绑定：

```text
H = (sid, v_sid, g_sid, C_old, C_new,
     frontier_sid, generation, transition_certificate)
```

新配置只有在验证 `H`、当前 frontier、实例状态和阈值共享重分享结果后才暂存活动状态。安装确认只证明后继状态已暂存，不改变写入权；旧配置仍是唯一恢复来源。旧配置形成退役回执后，原实例才在新配置下恢复纳入。旧配置在确认前崩溃时，剩余旧成员须满足旧配置的门槛才能完成恢复与交接；后继安装不能代替这一门槛，也不能代替旧状态退役。

实例达到聚合条件后，当前配置固定客户端集合、聚合值和模型结果，生成 `Commit_sid`。旧可写状态完成退役后生成 `Seal_sid` 和 `sealed record`。后继配置只安装 `sealed record`。属于旧配置、旧记录版本或已提交实例的迟到消息生成拒绝结果，并且不能产生新的可安装状态。

方案的最小伪代码如下：

```text
procedure Handle(event, C_r):
    R <- load(event.sid)

    if event is an update:
        require R is writable and event.version = R.g_sid
        require event.client is not in R.A_sid
        admit event and update R.state_sid and R.A_sid

    if event is a configuration change to C_{r+1}:
        for each active R:
            fix R.frontier and pause admissions to R.sid
            resharing <- transfer_aggregate_shares(R, C_{r+1})
            send H(R, C_r, C_{r+1}, resharing)
        install sealed records without writable state

    if event is a handoff:
        require R is active
        require H matches R and the transition certificate
        require resharing verifies under C_{r+1}
        install the new protection context and generation + 1
        confirm installation, erase old shares, record retirement, then resume admissions on R.sid

    if R satisfies the aggregation condition:
        compute result_sid
        publish Commit_sid and the result record
        erase writable state for sid
        record Seal_sid after retirement

    if event is late, stale, or targets a sealed record:
        record rejection and keep R unchanged
        route an eligible unadmitted update to the resumed sid; use a new sid
        only when the source instance is sealed or abandoned
```

结果发布和活动材料清除之间使用 `committed` 与 `seal_pending` 两个边界。`Commit_sid` 固定参与集合、聚合值和模型结果，并关闭所有写入、恢复和交接操作；只有旧可写状态完成退役并进入事件日志后，才生成 `Seal_sid`，实例随后进入 `sealed`。退役失败的实例保持只读，不重新开放窗口或把后继配置的状态当作历史实例的可写副本。

客户端更新保护、聚合结果释放、活动状态交接和状态刷新属于保护插件。实例归属、配置验证、封存记录和迟到消息处理属于联邦学习服务。这个边界使 Buffalo 或其他异步安全聚合实现可以接入同一协议流程，也使明文向量后端能够先验证服务行为。

#### 13.3.1 成员变更与密钥上下文

方案把客户端资格和聚合委员会成员资格分开处理。两类成员事件具有不同的状态转移和密钥语义：

| 对象 | 加入 | 退出 | 密钥处理 |
|---|---|---|---|
| 客户端 | 通过认证后，从当前模型版本起提交新更新 | 停止后续提交，已经进入活动实例的更新继续完成 | 不改变委员会密钥；新提交使用当前实例保护上下文 |
| 聚合委员会节点 | 在后继配置生效后安装新阈值份额，并参与活动状态交接 | 在后继配置生效后失去写入权，交接确认后清除旧活动状态 | 刷新配置级阈值上下文，并对活动聚合共享执行重分享 |

客户端加入和退出不会触发全局重密钥。新客户端获得当前配置的认证材料和实例保护参数后即可提交；它不获得已经封存实例的恢复材料。客户端退出不会撤回已经接受的更新，因为这些更新已经属于原实例的聚合输入。未进入 `frontier` 的旧上下文更新由服务拒绝；具备后继提交资格的客户端在原实例恢复纳入后使用新代数重新保护，模型版本不兼容时重新训练。已退出客户端只在重新取得资格后才能重新提交。

委员会加入和退出形成一次新的配置转换。配置服务先确认后继成员集合，再生成新的配置认证上下文和阈值共享上下文。旧配置固定每个活动实例的 `frontier`，停止该实例的新写入，对聚合共享执行可验证重分享，后继配置验证并安装 `generation + 1` 的状态。安装确认前，旧配置保留唯一恢复来源；确认后，旧节点清除活动共享和旧写入权限。已封存实例跳过重分享，后继配置只读取封存记录。

密钥状态分为三层。身份认证密钥可以保持稳定，用于识别加入、退出和交接消息；配置级阈值上下文随着委员会配置变化；实例级聚合共享在活动交接时刷新，逻辑聚合值保持不变。前向安全和后向安全可以限制密钥暴露的时间范围，但实例归属、更新重提交和封存记录仍由服务规则决定。

完整的成员变更路径如下：

```text
admit membership request
    -> publish successor configuration
    -> grant client submission or committee share only at the effective point
    -> freeze frontier for every active instance
    -> reshare live aggregate state to the successor committee
    -> install and confirm one successor writable state
    -> erase the old writable state
    -> resume eligible client updates on the unfinished original instance
```

该路径的关键性质是成员事件不会改变已经封存的训练结果，也不会让同一个活动实例同时拥有两个可写配置。客户端事件改变参与资格，委员会事件改变保护上下文；两者通过实例记录中的配置编号、`generation` 和 `protection_context` 保持可验证的对应关系。

#### 13.3.2 首选保护实例化：系数域阈值保护

Buffalo 的 JL 路径不直接作为活动交接后端。论文把 JL 密钥定义在 `Z_{N^2}`；开源实现没有把密钥切成小域分量，而是用 `SSS(2048)` 在素数 `2^2203-1` 上直接分享约 2048 位的客户端密钥。Optimistic DPSS 的秘密位于承诺群的素数阶域，并把秘密承诺纳入交接证明。直接组合需要把整个 DPSS 承诺层迁移到约 2203 位的群，现有实现无法提供这一路径。

首选实例化保留 Buffalo 的 RLWE 向量保护，把阈值保护放到 RLWE 密钥的系数域。设客户端 `u` 采样系数向量

$$
a_u=(a_{u,1},\ldots,a_{u,m}),\qquad a_{u,j}\in[-\rho,\rho],
$$

并令 `s_u = NTT(a_u)`。Buffalo 开源实现使用方差参数 `8` 的中心二项分布，采样器给出的系数绝对值上界为 `rho=16`；当前接口导出的是 59 位 NTT 表示，本文需要增加系数域导出和导入。

每个活动实例 `sid` 使用独立的阈值 ElGamal 密钥：

$$
z_{sid}\xleftarrow{R}\mathbb F_q,\qquad
PK_{sid}=z_{sid}G,qquad
\{[z_{sid}]_{r,i}\}_{i\in C_r}.
$$

第一版在 BLS12-381 G1 中实例化阈值 ElGamal，密文机密性依赖 G1 中的 DDH 假设。初始委员会通过批量可验证共享生成一组窗口密钥。配置转换时，Optimistic DPSS 只重分享仍处于活动状态的 `z_sid`；窗口封存后，各配置清除该窗口的密钥份额。客户端使用公开的 `PK_sid` 提交更新，因此其保护消息不依赖当前委员会名单。

客户端保护模型更新和每个 RLWE 密钥系数：

$$
c_u=\mathsf{LWE.Protect}(pp_{\mathsf{LWE}},NTT(a_u),x_u),
$$

$$
e_{u,j}=\mathsf{TEG.Enc}(PK_{sid},a_{u,j}G)
       =(r_{u,j}G,\ a_{u,j}G+r_{u,j}PK_{sid}).
$$

活动实例保存：

```text
S_sid = (
    protected_update_sum,
    encrypted_lwe_coefficient_sum,
    threshold_key_shares_{r,sid},
    accepted_update_ids,
    frontier,
    generation
)
```

对已接受集合 `A_sid`，服务器累加受保护更新和系数密文：

$$
C_{sid}=\bigoplus_{u\in A_{sid}}c_u,\qquad
E_{sid,j}=\bigoplus_{u\in A_{sid}}e_{u,j}.
$$

交接时，`C_sid` 和 `E_sid` 作为绑定 `frontier` 的公开聚合记录传递，旧委员会只对窗口秘密 `z_sid` 执行可验证重分享：

$$
\mathsf{DPSS.Handoff}_{C_r\rightarrow C_{r+1}}
 (\{[z_{sid}]_{r,i}\})
 \longrightarrow \{[z_{sid}]_{r+1,j}\}.
$$

`PK_sid` 和窗口内已有密文保持不变。已接受更新直接保留；后继客户端只向聚合服务提交同一窗口公钥下的系数密文，其密文直接加入 `E_sid`。

窗口达到参与门槛并固定最终集合后，委员会为 `E_sid` 产生一次阈值解密。令

$$
A_j=\sum_{u\in A_{sid}}a_{u,j},\qquad |A_j|\le B_{\max}\rho.
$$

阈值解密得到 `A_j G`。系统预先建立区间 `[-B_max rho,B_max rho]` 的点表并恢复 `A_j`；在 Buffalo 参数 `B_max=512,rho=16` 下，每个系数只有 `16385` 个候选值。随后计算

$$
S_{sid}=NTT((A_1,\ldots,A_m))\bmod q_{\mathsf{LWE}},\qquad
\mathsf{LWE.Agg}(C_{sid},S_{sid})=\sum_{u\in A_{sid}}x_u.
$$

这一步把 Buffalo 扩展中昂贵的大域离散对数改成有界系数查表。代价转化为每个客户端 `m` 个曲线密文和每次封存 `m` 个阈值解密结果。论文需要通过微基准判断这一代价是否适合目标模型；优化重点是并行曲线运算、批量验证和窗口密钥批量生成，不改变协议语义。

协议消息按以下顺序传递：

```text
Update(u, sid, v, c_u, {e_u,j}, proof_u)
    -> Admit(sid, update_id, c_u, {e_u,j})
Freeze(sid, frontier, A_sid, C_sid, {E_sid,j}, [z_sid])
    -> KeyHandoff(sid, generation + 1, [z_sid]', proof)
    -> Install(sid, generation + 1, frontier, C_sid, {E_sid,j})
    -> Confirm(sid, generation + 1)
    -> EraseOldShares(sid, generation)
    -> Resume(sid, generation + 1)
    -> ThresholdOpen(sid, fixed_set)
    -> Seal(sid, result_sid, A_sid, proof_sid)
```

`Update` 核验窗口公钥和受保护载荷；`Freeze` 固定旧配置已接收前缀；`KeyHandoff` 转移窗口阈值密钥份额；`Confirm` 转换所有权；旧份额完成清除后 `Resume` 才恢复实例纳入；`ThresholdOpen` 只处理固定参与集合；`Seal` 清除窗口密钥份额并保留结果记录。

Buffalo 原生 JL 路径继续作为固定委员会性能基线。它可以说明标量 JL 包装相对系数域阈值保护节省了多少客户端计算和通信，但其大域 Shamir 份额不承担本文的动态交接。若系数域阈值保护的客户端开销超过目标部署预算，论文保留旧委员会完成或放弃窗口作为能力对照，主协议的正确性主张仍以真实阈值后端通过阶段 D 为准。

### 13.4 证明路线：围绕训练结果，而不是堆叠密码学引理

证明章节只保留系统所需的三个命题和一个隐私主定理。密码学组件提供阈值安全、消息认证、聚合完整性和擦除条件；正文证明追踪实例记录的状态转移与交接边界。

命题一是窗口归属唯一性。对每个 `sid`，记录版本和客户端标识检查保证一次更新至多被写入一个活动记录。配置交接只复制当前记录，不重新生成客户端纳入事件，因此交接不会增加有效更新序列。

命题二是条件性计算连续性。给定有效配置证明、满足实例级交接可用性条件的活动记录交接和后继配置的服务条件，重配置执行保留已接受前缀，并在一个额外等待时间后追加后续更新。交接改变可见延迟 `d_h`，不改变已接受前缀；无法满足交接条件的实例进入 `abandoned`，不被伪造为已完成实例。

命题三是结果稳定性。封存记录是吸收状态。任何旧版本消息在 frontier 检查中被拒绝；任何后继配置只能读取 `sealed record`。因此 `A_sid`、结果版本和模型结果在封存后保持不变。

主定理是隐私终结。在每个 epoch 的控制上限、活动状态刷新、有效状态交接、`Commit_sid` 后的状态排除和旧可写状态退役成立时，敌手的历史视图与后继配置状态的恢复闭包不能形成 `sid` 的单客户端开启集合。证明分为三步：先按 epoch 划分已读取状态，再利用刷新性质排除不同 epoch 份额的直接合并，随后沿交接记录判断活动状态是否仍可达，最后使用 `Seal_sid` 切断从 `sealed record` 到旧开启材料的边。该结论只对满足交接可用性条件的活动实例给出连续性；对未满足条件的实例，协议保证其不被后继配置重新打开。

联邦学习部分给出性质保持结果。若底层异步聚合器在陈旧度 `\bar\tau`、客户端 Byzantine 比例和随机梯度条件下满足既有收敛或鲁棒性界，本文服务在满足交接可用性条件时保留已接受前缀，并在异步调度允许的陈旧度范围内追加更新。因此既有 FedBuff 类型的界只需加入交接造成的等待和陈旧度项：

```text
1/T * sum_{t=0}^{T-1} E[||grad F(w_t)||^2]
  <= (F(w_0)-F_*)/(eta*T)
     + c_1*L*eta*sigma^2/B
     + c_2*L^2*eta^2*(bar_tau + d_h + 1)^2*G^2.
```

这里 `d_h` 表示交接造成的等待，`B` 是有效聚合缓冲大小。该式用于说明系统设计如何影响已有异步训练界，最终常数随选定的 FedBuff 实现确定。本文不把收敛率作为新的优化算法贡献，实验负责测量 `d_h`、陈旧度、模型质量、实例完成率和放弃率。

### 13.5 实验代码：先验证服务语义，再接入真实训练

实验代码沿用当前 `experiments/reconfigurable_fl_sim.py`，把它作为第一阶段的事件回放器。回放器现在把活动交接分成导出、安装和确认，并记录 `frontier`、`generation`、保护上下文、交接状态和交接字节。确认失败时旧配置仍可封存已经接受的更新，后继配置不能提前获得写入权。当前阶段不需要先拆出大型框架，也不需要把 Buffalo 的密码学代码复制进模拟器。

下一步增加真实模型训练产生的有效陈旧度和模型版本序列。回放轨迹已经显式表示：截点后的旧上下文更新被拒绝，客户端随后通过 `client_resubmit` 带新保护上下文进入后继实例。所有策略读取同一轨迹，因此可以同时比较固定配置、全量交接、周期性重建和本文方案的更新重路由代价，并单独测量确认失败对训练推进的影响。

交接微基准的抽象后端已固定为 `open_state`、`admit_update`、`export`、`reshare`、`confirm`、`seal` 和 `erase` 七个操作。它只核算聚合状态规模、交接字节和状态阶段，不实现具体密码学。系数域阈值保护后端接入时替换这些操作的内部状态生成、窗口密钥重分享和验证逻辑，窗口服务与训练事件保持不变。

第二阶段使用 FLSim 产生真实客户端训练完成事件和向量更新。一个薄适配器把训练事件转成统一的 `ClientUpdate`，交给现有窗口服务决定纳入和封存。窗口服务返回聚合后的模型更新，再交给 PyTorch 继续训练。FLSim 上游代码保持原样。

第三阶段把 `ClientUpdate.payload` 替换为 RLWE 受保护更新和阈值加密的密钥系数，记录保护时间、通信量、聚合延迟和状态大小。Buffalo 原生运行作为外部基线，本文策略使用独立适配器接入；Flower SecAgg+、Catalyst 和 Setup Once, Secure Always 分别作为同步安全聚合、Byzantine 更新和动态用户的对照。

实验先完成三个检查：同一轨迹下有效更新序列可重放；封存结果在迟到消息和连续配置转换下保持一致；交接等待能够映射为模型陈旧度。三个检查稳定后，再进行 CIFAR 10 和 FEMNIST 的训练实验，最后测量保护成本。当前组件接入见 `experiments/REAL_COMPONENT_BRINGUP.md`；早期组件、基线及参数讨论保存在 `experiments/archive/legacy-design/EXPERIMENT_BUILD.md`。

### 13.6 当前论文范围

论文的主张集中在动态委员会下的异步联邦学习服务。贡献点写成协议机制、实现和联邦学习评价，敌手模型用于界定保证，证明用于支撑窗口结果和隐私终结。动态成员模型本身不单列为贡献点，前向安全和后向安全也不单独承担本文的核心叙事。

正文暂不展开通用动态密码学基础设施、任意成员变化下的新优化算法和所有动态 BFT 活性问题。实验先证明服务连续性、结果稳定性和交接代价，再决定保护插件的最终实例化。这样论文的中心保持在联邦学习系统，同时保留足够清晰的安全边界和理论支撑。

### 13.7 方案冻结稿：状态、操作与密钥边界

本节把前面的设计收束为一个可以实现和评价的协议方案。协议不要求客户端知道同一实例中的其他客户端，也不要求整个联邦学习服务在委员会变化时停止。

#### 配置记录

配置记录由成员变更服务产生：

```text
C_r = (
    configuration_id,
    predecessor,
    committee_members,
    threshold,
    auth_context,
    effective_boundary,
    transition_certificate
)
```

`transition_certificate` 证明 `C_r` 是有效的后继配置。它确定成员集合、阈值和生效边界，但不携带任何历史窗口的单客户端保护材料。

#### 活动实例记录

每个活动实例只存在一个可写记录：

```text
L_sid = (
    sid,
    base_model_version,
    owner_configuration,
    generation,
    accepted_update_ids,
    frontier,
    protected_update_sum,
    encrypted_lwe_coefficient_sum,
    threshold_key_shares,
    window_public_key,
    handoff_status
)
```

`handoff_status` 依次表达 `owned`、`handoff_pending`、`installed`、`confirmed`、`committed`、`seal_pending`、`sealed` 或 `abandoned`。其中 `handoff_pending` 表示活动状态已冻结但后继配置尚未确认，`committed` 表示参与集合和聚合结果已经固定，`seal_pending` 表示结果已发布但活动材料尚未收到退役回执。

`accepted_update_ids` 和 `frontier` 决定训练输入的逻辑归属；受保护模型、系数密文和窗口阈值密钥份额使实例可继续接收并在满足参与门槛时开启。实例的 `generation` 每完成一次配置交接递增。配置编号、代数和保护上下文必须一一对应，旧记录不能覆盖新记录。

#### 封存记录

实例完成后只留下：

```text
F_sid = (
    sid,
    model_version,
    accepted_update_ids,
    accepted_client_ids,
    aggregate_result,
    owner_configuration,
    generation,
    commit_certificate,
    retirement_certificate
)
```

`F_sid` 不包含 `protected_update_sum`、`encrypted_lwe_coefficient_sum`、`threshold_key_shares`、逐客户端保护材料或恢复转录。后继配置可以验证和读取 `F_sid`，但不能从中重新建立活动实例。

#### 操作顺序

协议操作固定为以下十步：

```text
1. JoinClient / LeaveClient
   update client submission eligibility; keep committee context unchanged

2. Admit
   verify client identity, sid, model version, protection context, and update_id

3. Freeze
   fix frontier_sid and close admission for the old context

4. Transfer
   verifiably reshare threshold_key_shares to C_{r+1}

5. Install
   successor verifies the transition certificate and installs generation + 1

6. Confirm
   successor certifies installation; sid remains frozen until retirement

7. Retire
   old members erase writable shares and recovery material

8. Transfer ownership
   record the retirement receipt and make C_{r+1} the sole owner

9. Resume
   successor continues the accepted inputs covered by frontier_sid

10. Commit and Seal
   open the aggregate once, publish Commit_sid, retire remaining live state,
   and record Seal_sid
```

`JoinClient` 和 `LeaveClient` 只改变客户端后续提交资格。`Freeze` 固定旧配置已接收的更新前缀。交接及旧份额清除完成后，后继配置在**同一个未完成实例** `sid` 上恢复接收，以新代数和保护上下文纳入后续更新。截点后的旧上下文提交需要客户端重新保护；模型版本仍在陈旧度容许范围内时可复用本地训练结果，否则客户端下载新模型重新训练。已经退出且未重新取得资格的客户端不能借重新提交绕过退出决定。封存或明确放弃的实例才把合格的迟到更新导向另一实例。

#### 三类密钥状态

| 状态 | 客户端加入或退出 | 委员会加入或退出 | 交接后的结果 |
|---|---|---|---|
| 身份认证密钥 | 不变，资格由配置记录控制 | 新节点注册，退出节点失去后继配置资格 | 仍可验证成员与消息身份 |
| LWE 公共参数和窗口公钥 | 加入者获得当前参数并使用窗口公钥加密系数 | 活动实例沿用同一 `PK_sid` | 客户端无需重发已接收更新 |
| 活动实例阈值解密份额 | 不变 | 在曲线标量域中重分享给后继委员会 | 密文聚合值不变；旧份额清除后退出恢复路径 |

活动实例的 LWE 公共参数、`PK_sid` 和旧前缀的受保护聚合值保持不变。旧委员会把窗口解密秘密的份额可验证地重分享给后继委员会；新客户端继续在同一公钥下提交系数密文。安装确认改变服务所有者，清除回执之后才开放该实例在新代数下的写入和结果开启。回执表明诚实持有者执行清除，移动敌手的长期保证还依赖每个周期的暴露上限及安全擦除假设；确认消息本身不证明恶意节点已经删掉私存份额。

#### 六个核心算法

下面六个算法构成方案的最小协议核心。前两个算法处理训练更新，第三和第四个算法处理委员会变化，后两个算法处理结果发布和历史状态终结。

```text
CreateInstance(model_version, C_r):
    sid <- fresh aggregation-instance identifier
    (PK_sid, shares_r) <- distributed_threshold_setup(C_r)
    create live record (sid, model_version, C_r, generation = 0,
                       PK_sid, shares_r, empty aggregate)
    return sid, PK_sid

AdmitUpdate(update, sid, C_r):
    R <- read live record sid
    require R.status = owned
    require eligible(update.client, C_r)
    require update.model_version = R.model_version
    require update.generation = R.generation
    require verify_protection(update, R.PK_sid)
    require update.id not in R.accepted_update_ids
    append update.id to R.accepted_update_ids
    add its protected payload to R.aggregate
    return accepted with the new record version

FreezePrefix(sid, C_r):
    R <- read live record sid
    require R.owner = C_r and R.status = owned
    R.frontier <- (R.accepted_update_ids, R.record_version,
                   digest(R.aggregate))
    R.status <- handoff_pending
    certify R.frontier under the transition certificate
    return the certified frozen record

HandoffActiveState(R, C_r, C_{r+1}):
    require R.status = handoff_pending
    verify the transition certificate and R.frontier
    shares_{r+1} <- proactive_reshare(R.shares_r, C_{r+1}, R.PK_sid)
    verify shares_{r+1} against sid, source generation, target generation,
            and R.frontier
    install a staged record with generation + 1 and the same PK_sid
    issue an installation certificate for C_{r+1}
    erase the old writable shares after the successor confirms installation
    resume sid under C_{r+1} only after the erase receipt
    return the resumed record

FinalizeAggregate(R):
    require R.status in {owned, confirmed} and |R.accepted_update_ids| >= threshold
    fix A_sid and digest(R.aggregate)
    cert <- authorize_open(sid, R.generation, A_sid, digest(R.aggregate))
    shares <- partial_open(R.shares, cert)
    result <- combine_and_open(R.aggregate, shares, cert)
    return result and cert

EraseAndSeal(R, result, cert):
    publish Commit_sid = (sid, R.model_version, A_sid, result, cert)
    mark sid seal_pending and reject writes, recovery, and handoff
    erase writable aggregate state, key shares, and recovery material
    record Seal_sid and mark sid sealed
    accept later messages only as sealed-record reads
```

`authorize_open` 产生的证书绑定 `sid`、代数、最终参与集合以及受保护聚合状态的摘要。诚实成员只为该证书对应的完整聚合状态生成部分开启结果，后端不暴露可对任意单项密文调用的普通 `open` 接口。这样“只开启聚合结果”成为状态认证和阈值开启共同执行的协议条件，而不是适配层的一句约定。

`HandoffActiveState` 只改变份额分布和服务所有者，保持 `PK_sid` 与已经接受的密文不变。`proactive_reshare` 在新的委员会中刷新份额多项式，但保留同一窗口秘密；每个 epoch 内的状态暴露受门槛约束，刷新完成后旧份额被清除。交接失败时保留旧配置的唯一恢复来源，后继配置不创建第二个可写副本。`EraseAndSeal` 完成后，任何配置都只能读取封存记录，不能重新请求该实例的部分开启。

该协议把服务语义和密码学操作分开：`frontier`、实例归属和最终性证书属于联邦学习服务；阈值设置、主动式重分享、部分开启和清除属于保护后端。论文实现可以替换后端，但必须保持六个算法的输入边界和结果语义。

六个算法的前置条件和失败结果如下。失败处理不创建第二个可写实例，也不把未确认的状态交给后继配置。

| 算法 | 前置条件 | 成功输出 | 失败结果 |
|---|---|---|---|
| `CreateInstance` | 后继配置记录有效，模型版本已确定 | 唯一 `sid`、`PK_sid` 和初始共享状态 | 不创建实例，不产生可用份额 |
| `AdmitUpdate` | 实例可写，客户端具备资格，模型版本和代数匹配 | 更新标识进入接受日志，受保护载荷加入聚合状态 | 拒绝更新，聚合状态不变 |
| `FreezePrefix` | 当前配置拥有实例，实例仍可写 | 经配置协议确认的 `frontier` 和冻结状态 | 保留当前所有者和可恢复状态 |
| `HandoffActiveState` | `frontier` 已确认，后继配置证书有效 | 同一 `PK_sid` 下的后继份额、安装证明和唯一所有者 | 保留旧配置为唯一恢复来源，不安装后继副本 |
| `FinalizeAggregate` | 实例可写，参与集合达到门槛，聚合摘要固定 | 绑定最终集合和聚合摘要的开启证明及聚合结果 | 不发布结果，不改变活动聚合状态 |
| `EraseAndSeal` | `Commit_sid` 已发布，结果已验证 | `Seal_sid`、退役回执和只读状态 | 保留 `seal_pending`，禁止恢复、写入和再次开启 |

#### 三条方案不变量

方案与普通阈值重分享的差异可以用三条不变量表达。普通重分享只要求后继委员会继续恢复同一个秘密；本文还要求这个秘密服从聚合实例的训练状态。

1. **计算连续性。** 对仍处于活动状态的实例，交接前后的受保护聚合状态保持不变，`PK_sid` 保持不变，后继配置只能在已确认的 `frontier` 之后追加合格更新。于是交接改变的是状态持有者，而不是已经完成的训练输入。
2. **最终性单调。** 实例一旦发布结果，就不存在从最终状态返回活动状态、重新接受更新或再次生成开启授权的有效转换。迟到消息可以留下拒绝记录，但不能改变参与集合和模型结果。
3. **开启能力收缩。** 活动状态可以在配置之间转移，最终状态只能转移结果事实。后继配置的状态集合中不存在从封存记录到旧聚合份额、恢复材料或部分开启的有效路径。

前两条不变量支撑训练连续性和结果稳定性，第三条才给出本文相较于“异步安全聚合加标准重分享”的隐私边界。标准重分享可以保持秘密连续，却没有把“实例已经发布结果”作为禁止后续状态转移的条件；本文把这一条件绑定到最终参与集合、聚合状态摘要和开启授权上。

#### 方案成立所需的条件

方案只依赖四个可验证条件：

1. 成员服务能够产生有效的后继配置记录，并明确配置生效边界；
2. 活动实例的保护后端能够在不恢复窗口解密秘密或客户端更新明文的情况下重分享阈值密钥份额，并让后继客户端在同一窗口公钥下继续累加；
3. 旧配置在后继配置确认后擦除活动份额，且后继配置不会安装旧代数；
4. 异步训练层能够把截点后的更新重新提交或按陈旧度规则丢弃，并记录原因。

若第 2 条不成立，可以让旧委员会将足额实例封存后切换配置；未达发布门槛的实例进入明确的放弃与客户端重提路径。两者均为对照，不构成活动实例连续交接。Buffalo 原生 pairwise key 重建属于这类能力边界。若第 3 条不成立，新配置可处理其他实例，但原实例保持冻结且不能声称满足长期隐私终结。

#### 未完成缓冲区的连续性条件

设 `frontier_sid` 已纳入 `a` 个更新，实例的最低可发布参与数为 `B`。若 `a < B`，且冻结后只准更新进入新实例，则旧实例永远无法达到 `B`。本文的连续性依赖同实例的后继接收：旧前缀和新后缀组成最终且唯一的参与集合 `A_sid = frontier_sid ∪ suffix_sid`，满足 `|A_sid| >= B` 才开启并发布；两段更新必须使用同一可同态组合的实例公钥，新后缀携带后继配置与代数。若交接失败，旧配置仅能恢复冻结前缀并重试，不能在未认证的旧上下文中增加后缀。该条件是保护后端的能力门槛，也是下一轮回放和微基准要直接检验的训练连续性事实。

### 13.8 代码构建的论文化边界

代码实现分为四个可替换层：

```text
training workload
    -> event trace and scheduler
    -> window and configuration service
    -> protection backend
```

训练层只产生本地更新、模型版本和完成时间；事件层重放客户端到达、成员变化、消息延迟和节点故障；窗口服务实现本文的协议状态；保护后端实现更新保护、聚合、份额转移、开启和清除。层间只传递统一记录，不复制另一层的状态机。

第一版只实现事件回放和窗口服务语义，使用抽象保护后端测量状态规模。第二版接入真实客户端训练，确认交接等待如何表现为模型陈旧度。第三版接入系数域阈值保护插件，并把 Buffalo 作为独立性能基线，分别测量保护、份额转移和开启成本。这样每一项论文主张都有对应的实验层，不把训练调度、委员会变化和密码学调试放在同一个不可诊断的程序中。
