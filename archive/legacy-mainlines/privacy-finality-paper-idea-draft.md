# Keeping Asynchronous FL Moving Without Reopening Past Updates

## Privacy Finality for Long-Lived Asynchronous Secure Aggregation

> 文档定位：论文思路稿，不是定稿，也不把尚未证明的命题写成既成结果。  
> 核心对象：长期运行的异步安全聚合、移动自适应腐化、会话级隐私终结、可恢复但不可复活的密码学状态。  
> 核心叙事：**让密钥从故障中恢复的机制，也可能让它从“被遗忘”中恢复。**

## Manuscript Reorganization (2026-09-13)

本稿此前积累了完整的理论和密码学审计材料，但主文叙事不能按研究日志的
时间顺序展开，也不能让安全证明取代系统设计。OSDI 版本先讲一个长期运行的
异步 FL 服务如何接收更新、推进模型、处理故障并恢复委员会；`privacy finality`
是这个服务必须兑现的一项安全保证。理论刻画和密码学接口用于说明设计为什么
成立，详细证明放在安全章节和附录。

主文的章节顺序、证明预算和素材迁移规则统一见
`privacy-finality-manuscript-structure.md`。当前阶段不写完整主文初稿，
本文件是唯一的叙事和方案思路稿；后续章节保留为论证素材库，写作时应按
本节的引言和方案路线抽取，而不是把每个接口和 hybrid 作为新的主线结果。

### 主文阅读顺序

```text
长期运行的异步 FL 服务
    -> 服务目标与故障场景
    -> 完整协议路径与实现
    -> 训练窗口封存和故障恢复
    -> 安全模型与 privacy finality 保证
    -> FL 性能、恢复代价和模型质量
    -> 密码学实例化与附录证明
```

`Joint-AO^mob`、`F_PF^mob`、`PVOD`、`CSO-VE`、`KeyOrigin` 和 `PECC` 不再
并列承担论文贡献。它们分别属于聚合假设、理想功能、传输接口、联合证明
接口、密钥来源接口和擦除信道条件；只有在主文的 FL 定理需要时才引入。

## 引言论文路线与方案思路（当前版本）

> 本节定位为思路稿中的写作蓝图。后续写作围绕本节的论证顺序、方案对象
> 和公式展开；研究日志中的旧路线保留为素材档案。

### 写作提醒

引言从一个真实的训练场景开始，再说明现有工作解决了什么，最后引出本文要
加上的保证。每个技术对象都要回答一个 FL 问题。公式用来固定边界，密码学
组件放在方案成立所需的位置，不让组件名称主导叙事。

### 1. 引言论证顺序

引言先让读者看到长期异步 FL 服务中的具体风险，再说明本文的目标和解决
路径。推荐顺序如下。

#### 第一段：异步 FL 的运行场景

联邦学习将模型训练分布到多个数据持有方。跨设备、跨机构和边缘节点具有
不同的计算速度、在线时间和网络条件，异步 FL 按更新到达情况推进模型，让
已完成的客户端及时贡献训练结果。生产服务通常维护一个持续到达的更新缓冲，
在达到数量或时间条件后形成一次聚合，再把新的模型版本分发给后续客户端。

#### 第二段：现有 secure aggregation 的价值

Secure aggregation 使服务器获得授权集合上的聚合更新，并保护单客户端更新。
短种子掩码将高维模型保护转化为短密钥的聚合问题，适合 buffered asynchronous
FL 的通信模式。FedBuff、Buffalo 以及相关异步 SA 工作已经建立了缓冲聚合、
迟到客户端处理和聚合期间的隐私效率基础，为长期运行的 FL 服务提供了稳定的
聚合基础。本文在此基础上继续处理模型输出后的委员会状态。

#### 第三段：长期运行中的关键场景

同一个 FL 服务还要处理委员会崩溃、节点恢复、份额修复和配置交接。故障恢复
可能在一次聚合输出之后才完成，旧的修复消息也可能在异步网络中晚到。长期
移动腐化允许敌手在不同时间读取不同节点的状态。只要这些状态还保存着历史
客户端的 mask key，敌手就能沿着合法恢复路径重新打开已经进入模型训练的
单客户端更新。训练结果已经被使用，原始更新却继续留在可恢复状态中，这正是
长期 FL 服务需要处理的保密性风险。

#### 核心问题

因此，本文的核心问题是：

> **在完全异步、长期移动腐化和可恢复委员会状态下，如何在输出一个异步 FL
> 聚合后，持续支持未来会话的故障恢复，同时让该聚合中的每个单客户端更新
> 永久处于聚合泄漏范围之外？**

这个问题把模型训练的输出边界与委员会的故障恢复放在同一个系统目标中，要求
方案同时处理异步顺序、长期状态暴露和服务连续性。

### 2. Challenges and Our Solutions

#### Challenge 1：异步训练窗口需要一个可执行的封存点

异步服务必须在两种压力之间选择更新窗口：窗口过短会减少可用客户端，窗口
过长会增加等待和单项更新的保留时间。实际系统还要处理输出之后才到达的更新、
重复提交以及缓冲区中尚未纳入模型的客户端。FedBuff 和 Buffalo 通过 buffer
与聚合策略改善训练吞吐，ACS/共识协议确定参与集合；这些机制分别服务于训练
吞吐和集合一致性。本文把“已用于训练的更新何时从可开启状态中退出”加入同一
个异步训练决策，并把它与后续故障恢复连接起来。

#### Our Solution 1：把训练输出与隐私封存绑定

本文为每个异步训练窗口建立唯一描述符

```text
D_sid = (sid, S_sid, w_sid, H_ct, H_out),
```

异步一致机制确定 `D_sid` 并生成 computation certificate `CC_sid`。委员会
依据 `D_sid` 打开授权聚合并输出模型更新；随后它沿着
单调的 privacy frontier 完成状态封存，生成 `PF_sid`。`CC_sid` 固定进入模型
的客户端集合与权重，`PF_sid` 固定已使用更新的隐私封存点。迟到更新进入下一
个描述符，或按服务策略留在待处理缓冲中；它们不会改变已经输出的模型版本。

#### Challenge 2：故障恢复必须绕开已封存的训练窗口

封存一个训练窗口之后，委员会仍要为崩溃或被接管的节点恢复未来聚合所需的
状态。VSSR、proactive secret sharing 和动态委员会协议为份额连续性、节点
修复与配置迁移提供了重要基础；前向安全加密为有序时间段提供了密钥演进。
在异步恢复场景中，修复请求、私有子份额、待处理 transcript 和交接状态会跨
越模型输出到达。修复过程一旦引用历史窗口的材料，恢复服务就可能重新产生该
窗口的开启能力。现有恢复机制以秘密连续性和服务连续性为核心，本文进一步给
出历史训练更新沿所有合法恢复路径退出的条件。

#### Our Solution 2：用 Recovery-Closure 约束故障恢复

本文将 direct share、recovery share、transcript、channel state 和 handoff
state 统一表示为 typed capabilities，并定义恢复闭包 `Cl_rec(X)`。对封存
集合 `A_sid`、封存前暴露能力 `B` 和封存后仍可导出的旧能力 `R_sid`，定义

```text
E_sid(B,A_sid) = B union R_sid union C_old(P-A_sid).
```

其中 `C_old(P-A_sid)` 表示封存集合之外仍保留的旧能力。privacy finality
要求每个授权解密集合 `D in Gamma_dec^cap(sid)` 满足

```text
D is not a subset of E_sid(B,A_sid).
```

方案通过 state-complete sealing 清除 `sid` 的 direct share、local recovery
state、pending state 和 endpoint state；恢复操作只生成当前 generation 的
live state，并绑定目标、generation 和 frontier。对应的设计目标是

```text
R_sid = emptyset,
```

此时 `E_sid` 退化为 direct-capability 的 robust-hitting 条件。第一项挑战确定
训练窗口的封存点，第二项挑战把故障恢复约束为 closure-preserving 的状态转换；
两者共同给出长期异步 FL 的 privacy finality。

### 3. Our Contributions

引言最后集中呈现三项贡献：

1. **A complete asynchronous FL service path.** 设计从客户端更新接收、缓冲窗口
   形成、委员会聚合、模型版本推进到窗口封存和故障恢复的端到端流程，并明确
   迟到更新、重复提交、崩溃和迟到修复消息的处理结果。
2. **Privacy finality as a service guarantee.** 将 `CC_sid`、`PF_sid` 和
   `Recovery-Closure` 放入同一个 FL 服务模型，说明已进入模型训练的单客户端
   更新如何在后续恢复和长期移动腐化下保持不可重新打开，并给出相应的安全模型
   和条件定理。
3. **An implementable evaluation of the design tradeoffs.** 基于现有
   asynchronous SA/ACS 组件实现封存与 current-state recovery，系统评估客户端
   纳入率、陈旧度、模型推进延迟、封存与恢复代价、通信/持久状态以及模型质量。

引言中的贡献名称保持在“服务路径、隐私保证、系统证据”这三个层次。
`PVOD`、`CSO-VE`、`KeyOrigin`、`PECC` 和逐代 simulator 作为实现条件与附录
材料出现。

### 4. 方案整体概述

方案从客户端更新如何进入一次训练窗口开始。客户端提交更新 `x_u`，并使用
短种子 `k_u` 形成

```text
z_u = x_u + G(sid,k_u).
```

对 `D_sid` 中的客户端集合 `S_sid` 和权重 `w_sid`，委员会只恢复

```text
K_sid = sum_{u in S_sid} w_u*k_u,
```

从而输出

```text
Y_sid = sum_{u in S_sid} w_u*x_u.
```

客户端更新始终以掩码形式进入委员会，委员会只恢复授权集合上的聚合掩码。
一次训练窗口按下面的顺序推进：

```text
1. Accept:     异步确定 D_sid，生成 CC_sid。
2. Aggregate:  只打开 K_sid，输出 Y_sid。
3. Seal:       按 frontier 封存窗口状态，生成 PF_sid。
4. Repair:     依据 frontier 只恢复 live generation state。
```

`Seal` 是方案的关键动作。节点先完成目标窗口的状态替换，再生成 sealing
acknowledgement。公开证书记录集合 `A_sid` 和 frontier。修复参与者先合并已知
frontier，再贡献当前 live state。后续训练照常使用新的状态，已封存窗口不再
进入修复结果。

### 5. 方案伪代码

以下伪代码用于表达整体协议控制流，具体密码学接口在后续章节单独选择。

```text
ProcessAsyncWindow(sid, arriving_updates):
    D <- AgreeDescriptor(sid, arriving_updates)
    CC <- CertifyComputation(D)
    K  <- OpenAggregateMask(D, CC)
    Y  <- ReleaseModelUpdate(D, K)
    emit (Y, CC)

    A <- SelectSealingQuorum(D, exposure_bound)
    for i in A:
        st_i <- SealWindowState(st_i, sid, frontier(D))
        ack_i <- AcknowledgeSealing(i, sid, frontier(D))
    PF <- CertifyPrivacyFinality(sid, D, A, {ack_i})
    emit PF

    on Repair(target, request_frontier):
        frontier <- MergeFrontier(request_frontier)
        live_state <- RecoverLiveState(target, frontier)
        InstallLiveState(target, live_state, frontier)
```

伪代码中的 `SealWindowState` 覆盖 direct share、local recovery material、
pending state 和 endpoint state；`RecoverLiveState` 生成下一代可用状态。`PF`
记录客户端集合、权重、封存集合和 frontier，物理擦除假设由系统模型承载。

### 5.1 系统设计与实现蓝图

思路稿阶段需要先把协议写成一个可以落地的 FL 服务，再选择具体密码学接口。
实现章节应围绕以下四个组件组织，但不把它们写成彼此独立的密码学贡献：

1. **客户端与模型服务器。** 客户端从指定模型版本计算更新，携带窗口标识和
   防重复提交信息发送到模型服务器。服务器维护待处理更新，按照数量、时间和
   陈旧度策略形成候选窗口，并向委员会提交窗口描述符。
2. **聚合委员会。** 委员会对同一个描述符确认参与集合和权重，完成一次
   aggregate-only 打开，再把模型更新和描述符返回模型服务器。模型服务器只在
   `CC_sid` 确认后推进模型版本。
3. **封存与迟到处理。** 模型版本推进后，委员会为该描述符完成封存。封存记录
   必须包含窗口标识、模型版本、参与集合、frontier 和确认集合。迟到客户端更新
   进入新的窗口或被明确丢弃；迟到修复消息只能更新当前仍需服务的状态。
4. **崩溃恢复。** 节点重启先读取封存记录，再恢复当前窗口所需状态。恢复过程
   不从旧窗口的备份重建已封存能力；恢复失败时，模型服务器保留已发布模型版本，
   只重试当前窗口或后续窗口的服务。

实现评估至少需要回答：窗口何时关闭、客户端等待多久、重复和迟到更新如何计数、
封存期间崩溃会丢失哪些工作、恢复需要多少通信和持久状态，以及 privacy frontier
对模型更新延迟和模型质量的影响。安全证明只负责说明这些处理规则在攻击模型下
保护已完成窗口的单客户端更新；系统章节负责说明它们如何共同支撑持续训练。

### 6. 方案公式与主文证明预算

主文需要保留四组公式：

1. **FL 更新：** `z_u`、`K_sid` 和 `Y_sid`，说明方案保护的是模型更新，
   而非抽象密文本身；
2. **训练窗口对象：** `D_sid`、`CC_sid`、`PF_sid`，说明模型输出和隐私
   封存的职责分工；
3. **闭包条件：** `Cl_rec(X)` 和 `E_sid(B,A_sid)`，说明恢复能力如何进入
   隐私访问结构；
4. **异步参数：** `A_sid in H_b(Gamma_dec^cap(sid))`、`R_sid=emptyset`、
   `|A_sid|=n-f` 和 `n=3f+2, q_dec=q_rec=2f+1`，说明安全与恢复活性的
   共同边界。

正文保留一个 closure-aware criterion、一个 recovery-state separation 和
一个条件协议实现定理。完整 simulator、优势项和密码学接口证明进入附录，
实验聚焦客户端纳入、更新陈旧度、聚合/封存/恢复延迟、状态成本和模型质量。

### 7. 固定的系统模型与攻击轨迹

下一阶段固定下面这组模型。后续定义、定理和实验都沿用同一条更新处理路径，
问题边界也随之保持稳定。

#### 7.1 参与者与一次训练窗口

模型服务器接收客户端更新，委员会 `P` 负责确定进入窗口的客户端集合并打开
授权聚合。对客户端 `u`，更新 `x_u` 使用短种子 `k_u` 掩码后发送。委员会只
得到窗口的加权掩码和模型更新：

```text
z_u = x_u + G(sid,k_u)
K_sid = sum_{u in S_sid} w_u*k_u
Y_sid = sum_{u in S_sid} w_u*x_u
```

一次窗口包含四个可观察时刻：客户端更新进入缓冲的 `t_in`，委员会确定
`D_sid` 的 `t_cc`，模型服务器发布 `Y_sid` 的 `t_out`，以及委员会完成
状态封存并发布 `PF_sid` 的 `t_seal`。顺序固定为

```text
t_in <= t_cc <= t_out <= t_seal.
```

`D_sid` 固定 `S_sid` 和 `w_sid`。`t_out` 之后到达的更新进入后续窗口，已有
描述符和模型版本保持不变。`t_seal` 之后到达的旧修复消息也会被处理，但它
只能针对当前 generation 生成 live state。

#### 7.2 网络、故障与敌手

网络完全异步，消息的发送顺序和到达顺序可以不同。委员会最多容纳 `f` 个
同时被腐化的节点，恢复门槛为 `q_rec`，聚合开启门槛为 `q_dec`。敌手可以在
不同时间腐化不同节点并读取当时的本地份额、修复材料、待处理消息和信道状态，
同时控制已腐化节点发送的消息。对目标窗口 `sid`，敌手在 `t_seal` 之前能够
永久保留的旧 capability 数量记为 `b`，首个参数点取 `b=f`；敌手可以在后续
窗口继续移动到其他节点。正确节点完成封存后清除 `sid` 的局部材料，系统把这
一擦除行为作为物理模型中的假设。

这里的 `b` 是目标窗口的状态暴露预算，不是全局腐化上限，也不是解密查询次数。
敌手可以在不同窗口选择不同的节点，并在封存后继续读取当前状态；对某个 `sid`，
只有 `t_seal` 之前被永久保存的旧 capability 计入 `B_sid`。敌手只能使用协议
公开的消息和合法恢复操作，系统不提供任意选择的解密查询。

首个结果固定委员会，取

```text
n = 3f + 2,       q_dec = q_rec = 2f + 1.
|A_sid| >= n - f = 2f + 2.
```

这里的 `n=3f+2` 有两个不同作用。它让聚合和修复保留足够的正确节点，也让
target 被排除后仍有 `2f+1` 个正确 helper。privacy finality 还要求封存集合
满足 `|A_sid|>=2f+2`；在 `b=f` 和 `q_dec=2f+1` 时，这正好等于 `n-f`，
因此封存证书处在异步活性的紧边界。动态委员会只作为同一封存条件的后续扩展。
这样，论文首先回答固定委员会中“模型已经发布、节点仍会修复”这一核心问题，
再讨论配置交接带来的额外恢复边。

封存证书记录 `A_sid` 个不同节点的确认。正确节点只有在完成该窗口的局部材料
清除后才确认；Byzantine 节点的确认可能与实际擦除不一致，这些节点的旧能力
统一计入 `B_sid`。因此安全证明使用的是

```text
|A_sid| >= n-f,
|B_sid| <= b,
A_sid in H_b(Gamma_dec).
```

证书规模和能力预算承担不同角色：前者保证每个授权解密集合至少包含一个已
完成封存的正确节点，后者覆盖提前读取和虚假确认留下的旧能力。

#### 7.3 Canonical delayed-repair attack

攻击轨迹只需要一个训练窗口和一次修复请求。它包含以下步骤：

1. 客户端提交 `S_sid` 中的更新，委员会为各节点准备当前 generation 的份额。
2. 节点在 `t_out` 之前发送修复材料。网络把其中一部分延迟到 `t_seal` 之后。
3. 委员会确定 `D_sid`，打开 `K_sid`，模型服务器发布 `Y_sid`。
4. 正确节点完成 `sid` 的状态封存并发布 `PF_sid`。
5. 延迟修复消息到达。一个普通恢复协议把它当作有效的旧 generation 输入，
   重新安装与 `sid` 相关的份额或恢复边。
6. 敌手先读取封存前的部分份额，再在后续时刻移动到其他节点。旧修复输出和
   后续读取合在一起后，形成 `Gamma_dec^cap(sid)` 中的一组能力，单客户端的
   `k_u` 随之可被恢复，`x_u` 也从 `z_u` 中被打开。

这条轨迹把问题集中在一个具体的服务时序上：模型服务器已经使用了 `Y_sid`，
委员会在处理迟到修复消息时又产生了 `sid` 的开启能力。它同时覆盖聚合输出、
消息延迟、状态封存和移动腐化四个因素，可作为主文的 motivating attack。

#### 7.4 方案在同一轨迹中的行为

本文方案在第 4 步把 `PF_sid` 写入每个正确节点的本地状态，并把 frontier
传播给后续修复参与者。第 5 步的消息仍然可以到达，但恢复过程先合并 frontier，
再判断目标 generation。对已经封存的 `sid`，恢复结果只包含当前 live state，
不生成 `sid` 的旧 capability。于是攻击轨迹中的恢复边被截断在 `R_sid` 之外，
闭包条件回到

```text
R_sid = emptyset.
```

`PF_sid` 把这条处理规则写入后续恢复输入。主文的安全结果需要证明：在这一
规则和 `A_sid in H_b(Gamma_dec^cap(sid))` 下，授权开启集合对移动敌手保持不可达；
活性结果则需要证明未来窗口的 live state 仍能完成修复。

#### 7.5 后续证明与实验的对应

系统模型冻结后，理论部分只保留三条对应关系：

1. `t_out` 固定 computation finality，`t_seal` 固定 privacy finality。
2. 延迟修复消息产生 recovery-closure；旧 capability 是否进入闭包决定攻击
   是否成功。
3. frontier 约束和 live-state repair 同时给出隐私条件与恢复活性条件。

实验据此观察五组指标：客户端纳入与更新陈旧度、模型输出延迟、封存延迟、
故障修复延迟，以及恢复后保留的状态量。实验结果用于测量封存规则对 FL 服务
的影响，三条理论关系负责说明安全边界。

### 8. 主文正式定义与定理对齐

这一节把第 7 节的时序压缩成主文可以使用的三个正式结果。定义只描述模型
更新和委员会状态之间的关系，具体加密算法留在实例化部分。

#### 8.1 Computation finality

对一次训练窗口 `sid`，`CC_sid` 是关于

```text
D_sid = (sid, S_sid, w_sid, H_ct, H_out)
```

的有效证书。若 `CC_sid` 已形成，模型服务器发布的更新固定为

```text
Y_sid = sum_{u in S_sid} w_u*x_u.
```

此后到达的客户端更新属于其他窗口。`CC_sid` 因此回答模型服务器已经使用了
哪些更新，以及这些更新在聚合中的权重是多少。

#### 8.2 Recovery closure

令 `B_sid` 表示在 `t_seal` 之前被敌手保存的历史 capability，`A_sid` 表示
已经完成状态封存的节点集合，`C_old(P-A_sid)` 表示封存后仍保留在其他节点
上的旧 capability。令 `R_sid` 表示从迟到修复、备份、信道或交接状态中还能
导出的 `sid` 旧 capability。定义

```text
E_sid(B_sid,A_sid)
  = Cl_rec(B_sid union C_old(P-A_sid) union R_sid).
```

`Cl_rec` 对所有合法的修复、部分解密、交接和状态读取规则取闭包。它记录的
是敌手在 `t_seal` 之后沿协议允许的路径能够得到哪些能力，而不是某一类节点
身份的简单计数。

#### 8.3 Privacy finality

令 `Gamma_dec^cap(sid)` 表示能够打开 `sid` 中某个单客户端更新的 capability
集合族。对已经形成 `PF_sid` 的训练窗口，privacy finality 的能力层判据为

```text
for every admissible B_sid:
    for every D in Gamma_dec^cap(sid):
        D is not a subset of E_sid(B_sid,A_sid).
```

这个判据与第 7 节的攻击轨迹直接对应。普通恢复路径把迟到修复消息加入
`R_sid`，因此可能让某个 `D` 进入闭包。本文方案要求封存后只产生当前 live
state，使

```text
R_sid = emptyset.
```

此时判据退化为 `Robust-Hitting`：每个授权解密集合都必须与 `A_sid` 相交，
并且相交部分大于敌手在封存前能够保存的 capability 数量 `b`。能力层判据与
客户端更新隐私之间还需要 aggregate-only transcript security；该安全条件
保证两个具有相同授权聚合的更新世界在委员会视图中保持不可区分。

#### 8.4 三项主文结果

**主文定理 1：Privacy-Finality Characterization。** 在唯一 `CC_sid`、有效
`PF_sid`、能力边可由合法协议操作实现的条件下，`E_sid(B_sid,A_sid)` 避开
`Gamma_dec^cap(sid)` 中的每个授权集合，当且仅当敌手不能通过未来状态暴露和
合法恢复得到 `sid` 的单客户端开启能力。加入 aggregate-only transcript
security 后，该能力结论推出客户端更新的 post-finality 隐私。

该定理是技术稿 Theorem 44 的主文版本。无恢复边时得到 Robust-Hitting；有
恢复边时，退休集合本身不足以描述安全性，闭包才是完整对象。

**主文命题 2：Recovery-State Localization Separation。** 若封存后的剩余
委员会状态和合法恢复贡献能够生成某个
`D in Gamma_dec^cap(sid)`，且开启操作只检查本地安装状态，没有使用与能力
绑定的 frontier，那么未来全状态暴露会复活 `sid` 的单客户端开启能力。直接
份额删除、单调公开 frontier 和底层份额原语的安全性都不改变这个结论。

该命题是技术稿 Proposition 22 的主文版本。它解释了第 2 项挑战的理论边界：
封存规则必须约束能力的生成和使用，节点是否安装了某个旧状态只是其中一环。

**主文定理 3：Conditional Realization。** 若客户端聚合满足 `Joint-AO^mob`，
`CC_sid` 唯一绑定 `D_sid`，修复过程满足共同 helper、frontier binding、
state-complete sealing、typed capability isolation 和 opaque delivery，且

```text
A_sid in H_b(Gamma_dec)
```

则 `Accept -> Aggregate -> Seal -> Repair` 实现 `F_PF^mob` 的正确性、活性和
privacy finality。其安全误差由聚合视图、恢复闭包、frontier 使用、上下文绑定
和未覆盖恢复边的优势项组成。

该定理是技术稿 Theorem 42 的主文版本。它把前两个结果接到一个可运行的
异步 FL 服务上，同时明确当前工作的密码学实例化边界。

#### 8.5 主文证明顺序

主文按下面的顺序呈现证明，避免让底层密码学细节抢走 FL 问题的中心位置：

1. 先由 `CC_sid` 和 `PF_sid` 固定训练输出与封存边界。
2. 再证明 `E_sid` 的闭包判据，并给出迟到修复导致能力复活的分离攻击。
3. 最后把 aggregate-only opening、封存规则和 live-state repair 组合成
   `F_PF^mob`，只在附录展开优势项。

### 8.6 固定参数的紧边界

对 `q`-out-of-`n` 的解密访问结构，封存前暴露预算为 `b` 时，Robust-Hitting
要求封存集合大小至少为

```text
tau_b(Gamma_q) = n - q + b + 1.
```

代入本文的首个参数点：

```text
n = 3f + 2,
q_dec = 2f + 1,
b = f,
tau_b(Gamma_dec) = 2f + 2 = n - f.
```

因此，`A_sid in H_b(Gamma_dec)` 在该参数点等价于

```text
|A_sid| >= 2f + 2.
```

异步封存的响应集合最多只能依赖 `n-f=2f+2` 个最终正确响应者，所以安全与
活性在这里相交于同一个值。封存证书的含义也随之明确：最坏情况下，所有正确
节点都要完成该窗口的状态封存；最多 `f` 个 Byzantine 节点可以缺席或提交
无效确认，真正的安全性由 `B_sid` 对残留能力的预算吸收。

`q_rec=2f+1` 承担另一项任务。修复目标从 helper 集合中排除后，委员会剩余
`3f+1` 个节点，最多 `f` 个 Byzantine 节点 withholding，仍有 `2f+1` 个
正确 helper。因此 `n=3f+2` 支持 target-excluded live repair；它本身并不
降低 `A_sid` 的 privacy-finality 要求。后续协议证明必须分别证明：封存集合
达到 `2f+2`，以及每次 live repair 获得 `2f+1` 个共同 helper。

### 8.7 `Seal` 的可证明协议条件

`Seal` 的实现只需要一个与训练窗口绑定的原子屏障。节点收到 `Seal(sid,D_sid)`
后，先把 `sid` 标记为待封存，再清除 direct share、修复材料、待处理明文和
端点临时密钥，最后发送确认。这个顺序由一次原子状态转换保证：确认出现时，
该节点已经进入封存后的状态。

节点在封存中途崩溃时，恢复过程先完成这条待封存记录，再处理旧 generation 的
修复消息。因而旧修复消息可以到达，但它不能先于封存动作产生新的 `sid` 能力。
`PF_sid` 收集至少 `n-f=2f+2` 个不同确认后发布；它不承担物理擦除证明，
而是记录已确认集合和 frontier，并让后续恢复使用同一边界。

对 live generation，修复仍使用 target-excluded 的 `2f+1` 个共同 helper。对
已经封存的 `sid`，修复请求先与 frontier 比较，输出只允许属于当前 live
generation。于是 `Seal` 的两个证明条件可以分开写成：

```text
seal safety:  |A_sid| >= n-f  and  A_sid in H_b(Gamma_dec)
repair liveness:  |H| = q_rec = 2f+1,
                  H excludes target and contains 2f+1 correct helpers.
```

在首个参数点，前一条件化为 `|A_sid|>=2f+2`，后一条件由
`n-1-f=2f+1` 个正确的非 target 节点满足。两者共同支撑 Theorem 3，前者
负责历史隐私，后者负责未来窗口的修复进展。

### 8.8 `B_sid` 的记账规则

`B_sid` 按 capability 的来源记账，而不是按消息条数记账。对同一个客户端更新，
按下面的规则处理：

| 读取或消息 | 归入的位置 |
|---|---|
| `t_seal` 之前读取的旧 share、修复材料或可保存的 endpoint key | `B_sid` |
| `t_seal` 之前生成、`t_seal` 之后到达的旧修复消息 | `R_sid` 或 `Cl_rec` 中对应的恢复边 |
| `t_seal` 之后读取的、已经完成封存的旧材料 | 只能来自残留 `C_old(P-A_sid)`；正确节点清除后不再产生该项 |
| 当前 generation 的 live state | 当前状态集合；通过 generation 和 coordinate 标签与旧 `sid` 隔离 |

因此，客户端更新在 `t_out` 之后、`t_seal` 之前被读取，仍然计入 `B_sid`。
`t_out` 表示模型已经使用该更新，`t_seal` 才表示委员会完成旧能力封存。一个
在 `t_seal` 之后到达的修复消息不会自动计入 `B_sid`，它必须经过 frontier
检查；若它仍能导出旧 capability，就进入 `R_sid` 并直接影响 closure criterion。

这条记账规则允许敌手在服务运行期间长期移动，同时把证明责任集中到目标窗口的
封存边界。它也把 delayed-repair 实验中的 `retained_capabilities`、
`post_finality_openings` 和 `stale_repair_accepts` 分别对应到历史预算、闭包
扩张和旧恢复边三个观察量。

#### 8.9 `Privacy-Finality` 安全游戏

前面的能力判据说明何时可以形成旧的单客户端开启能力；本节把它写成一个与
异步 FL 服务直接对应的区分实验。该实验是选择性的单描述符实验：敌手先选定
目标窗口和挑战更新，挑战后继续进行长期移动腐化和合法恢复。它不提供任意历史
记录查询，也不把“不能成功解密”预先写成操作限制。

**预挑战阶段。** 挑战者固定委员会 `P`、参数 `n=3f+2`、瞬时腐化上限 `f`、
目标窗口 `sid` 以及参与集合 `S_sid`、权重 `w_sid` 和模型维度。敌手指定诚实
客户端的两组更新

```text
X_0 = {x_{u,0}}_{u in H_sid},
X_1 = {x_{u,1}}_{u in H_sid},
```

并满足

```text
sum_{u in H_sid} w_u*x_{u,0}
  = sum_{u in H_sid} w_u*x_{u,1}.
```

两组更新可以逐客户端不同，但授权加权聚合相同。挑战客户端在本实验中保持
诚实；委员会节点可在挑战前后被移动腐化。挑战上下文还固定每个客户端的
`sid`、坐标和 generation 标签，避免把标签变化误当成隐私泄漏。对每个世界，
挑战者按照聚合开放游戏生成短种子 `k_{u,b}`，形成公开的掩码更新

```text
z_{u,b} = x_{u,b} + G(sid,k_{u,b}),
```

并要求

```text
sum_{u in H_sid} w_u*k_{u,0}
  = sum_{u in H_sid} w_u*k_{u,1}.
```

因此两个世界的授权聚合掩码相同，`Y_sid` 也相同；客户端掩码、密文、部分解密
和相关证明全部进入同一次 `Joint-AO^mob` 挑战。该联合视图定义了
aggregate-only 安全的公开转录边界，长期状态层不单独模拟这些挑战相关对象。

**挑战阶段。** 挑战者随机选择 `beta in {0,1}`，用 `X_beta` 执行一次完整的
`Accept -> Aggregate -> Seal` 路径，输出

```text
Y_sid = sum_{u in S_sid} w_u*x_{u,beta},
CC_sid, PF_sid.
```

两个世界共享同一授权描述符、客户端集合、权重、模型输出和封存语义。若实现的
`CC_sid` 还包含 ciphertext digest 或其他数据相关摘要，该摘要不被强行要求逐字
相同，而是作为 `DataView_beta` 的一部分交给 `Joint-AO^mob`；`CC_sid` 的授权
字段必须相同。这样既保持 `CC_sid` 的绑定作用，也避免把公开密文摘要误当成
控制层常量。`PF_sid` 的集合、frontier 和封存结果在两个世界中相同；其中依赖
挑战密文的证明和部分解密同样属于 `DataView_beta`。

**挑战后阶段。** 敌手获得完整公开转录，并按完全异步网络调度合法事件：

```text
Corrupt(i)       -> 当前节点状态及本次腐化时已经公开的历史状态
Release(i)       -> 释放当前腐化位置，保持已读取 capability
Publish/Process  -> 发送或处理异步消息
Recover(rid,i,T) -> 请求并执行带 frontier 的 live-state recovery
Retire(sid,T)    -> 处理封存请求及其确认
ExposeAllCurrent -> 最终读取所有节点的当前状态、缓冲区和恢复转录
```

每个时刻同时腐化节点数不超过 `f`，目标窗口在封存前永久保留的旧 capability
满足 `|B_sid|<=b`。`Corrupt` 在消息发送时已经看到的 key、point 或 endpoint
状态立即进入 `B_sid`；之后才到达的消息按照其恢复边进入 `R_sid` 和
`Cl_rec`。这些操作都是真实协议允许的操作，实验中没有额外的解密 oracle。
挑战者继续处理迟到修复、崩溃恢复和当前委员会状态暴露；它不会把旧窗口重新
提交给模型聚合。

**最终视图与优势。** 令

```text
View_beta = (DataView_beta, StateView, PublicContext, X_hist).
```

`DataView_beta` 包含读取挑战更新、客户端密文、聚合密文、部分解密或数据相关
证明的对象；`StateView` 只包含 frontier、generation、恢复状态、当前份额和
公开调度信息。长期状态层必须满足：除 `DataView_beta` 已覆盖的对象外，
`StateView` 对 `beta` 独立。敌手输出 `beta'`，定义

```text
Adv_Privacy-Finality(A)
  = |Pr[beta'=beta] - 1/2|.
```

若敌手在封存后通过合法恢复或最终状态暴露获得某个
`D in Gamma_dec^cap(sid)`，则记录 `OpenOne(sid)` 失败事件；该事件不因输出
`Y_sid` 而被抵消。其可行性完全由

```text
E_sid(B_sid,A_sid)
  = Cl_rec(B_sid union C_old(P-A_sid) union R_sid)
```

决定：若存在 `D subseteq E_sid(B_sid,A_sid)`，实验允许敌手用该能力打开单个
客户端更新；若对所有可行 `B_sid` 和所有授权集合都不存在这种包含关系，则
`OpenOne(sid)` 被能力层排除。这个条件正是 Theorem 44 的主文表达，而不是
对腐化或恢复操作的事先筛选。

**主文安全目标。** `Privacy-Finality` 要求在所有满足移动腐化、消息延迟、
封存和恢复规则的执行中，同时成立：

```text
1. no OpenOne(sid) after PF_sid;
2. View_0 and View_1 are computationally indistinguishable.
```

第一项由 `Recovery-Closure` 和 `A_sid in H_b(Gamma_dec^cap(sid))` 给出；第二项
还需要 aggregate-only transcript security。主组合定理把它们分开记账：

```text
Adv_Privacy-Finality(A)
  <= Adv_RCL-Sim/AO(A_1)
     + Adv_Joint-AO^mob(A_2)
     + Adv_Context/Correctness(A_3)
     + Adv_Uncovered-Edge(A_4)
     + negl(lambda).
```

其中 `Adv_RCL-Sim/AO` 负责恢复状态和迟到转录的视图替换，
`Adv_Joint-AO^mob` 负责同一授权聚合下的数据相关公开对象，
`Adv_Uncovered-Edge` 负责检查是否存在未被类型账本覆盖的恢复能力边。若理想
`RCL` 满足 `R_sid=emptyset`，且封存集合满足 Robust-Hitting，则第一项中的
能力层失败事件为零；`Joint-AO^mob` 仍负责客户端更新的 aggregate-only 隐私。

这个游戏也明确了动态委员会的进入方式。首版固定 `P` 以隔离核心判据；后续若
允许成员加入、退出或 handoff，交接被建模为带 `(sid,generation,frontier)` 标签
的合法恢复边，并直接加入 `Cl_rec`。只有证明交接不会生成已封存 `sid` 的旧能力，
动态委员会扩展才保持同一个安全游戏，而不是另起一套隐私定义。

## 引言思路与方案总览（当前写作阶段）

> 历史版本：本节保留早期素材，当前写作以“引言论文路线与方案思路”为准。

本节不是论文正文，而是后续写作必须遵守的论证路线。引言只需要让读者
相信一个异步 FL 的安全问题，并理解本文方案为什么改变了 secure
aggregation 的生命周期语义；不在引言中展开 `PVOD`、NIZK、hybrid 或
优势项。

### 1. 引言的六段论证路线

**第一段：从异步 FL 的真实运行方式开始。**

说明跨设备、跨机构或边缘 FL 的客户端完成时间不同，服务器不能等待一个
同步轮次中的所有客户端。异步或 buffered asynchronous FL 通过持续接收
更新、在条件满足时形成聚合来减少 straggler 对训练的影响。这里要强调：
一个会话不是抽象的密码学 ciphertext 集合，而是一次实际的模型更新，包含
客户端集合、权重、聚合输出和后续训练状态。

**第二段：说明 secure aggregation 已经解决了什么。**

现有 SA 允许服务器得到授权集合上的聚合更新，却不能得到单个客户端更新。
短种子掩码和 aggregate-only opening 已经能够处理高维模型，因此本文不再
声称重新发明这些数据面机制。把已有工作放在“计算期间如何隐藏单项更新”
这个位置，主动缩小本文与 Buffalo、OPA、TACITA 等工作的重叠。

**第三段：给出一个不依赖密码学破坏的长期运行攻击。**

聚合输出后，委员会仍要处理 crash recovery、节点 cure、share repair 或
配置交接。设某个恢复消息在隐私终结前已经生成，但因异步网络延迟到终结
之后；或者恢复层保存了可以重新生成旧 share 的 local state。未来敌手逐步
腐化不同节点，便可能重新获得某个客户端的 mask key。这个攻击中，聚合值
没有被篡改，ACS 没有回滚，底层 VSS/加密也没有被破解；失败来自“恢复机制
仍然保留历史开启能力”。

**第四段：提出核心概念，而不是提出一个新密码学名词。**

指出 computation finality 和 privacy finality 是两个不同事件。前者回答
“哪些客户端及其权重被纳入了哪个聚合”，后者回答“该聚合中的单项更新何时
对未来状态暴露和恢复永久不可恢复”。本文的研究问题是：在完全异步和长期
移动腐化下，能否让 privacy finality 成为一个具有明确判据的协议事件。

**第五段：预告解决思路。**

本文不通过一次性 key refresh 或全局 epoch 解决问题，而是把每个已确定的
FL 聚合描述符绑定到单调的 retirement frontier。聚合打开后，系统形成独立
的 privacy-finality certificate；退休不仅删除 direct share，还关闭所有
能够生成旧 capability 的 recovery path；未来恢复只搬运 live state。由此，
“可恢复性”和“历史不可复活”被放进同一个 capability closure 条件中。

**第六段：用三项结果结束引言。**

引言最后只列三项结果：

1. privacy finality 的 FL 生命周期定义，以及它与 computation finality 的
   区别；
2. recovery-closure 判据和 delayed-recovery separation，说明普通 refresh、
   VSS recovery、forward security 单独都不够；
3. 一个面向异步 FL 的条件协议语义，证明在 aggregate-only data plane、
   状态完整退休和 live-state-only recovery 下可以保持隐私终结、聚合正确性
   和恢复活性。

引言不列 `AOR-1`--`AOR-5`、`PVOD`、`CSO-VE`、`KeyOrigin` 等接口名；这些
内容只有在方案和安全定理之后才出现。这样读者首先看到的是 FL 问题和结果，
而不是密码学组件清单。

### 2. 方案的核心对象

方案围绕一个异步 FL 聚合描述符 `D_sid` 展开：

```text
D_sid = (sid, S_sid, w_sid, H_ct, H_out)
```

它固定会话标识、被纳入的客户端集合、权重、客户端密文集合和输出用途。
客户端更新仍采用短种子掩码：

```text
z_u = x_u + G(sid,k_u),
K_sid = sum_{u in S_sid} w_u*k_u.
```

数据面只打开 `K_sid` 对应的授权聚合，不打开单个 `k_u`。因此本文的新增
安全对象不是单个 ciphertext 的加密方式，而是 `D_sid` 从提交、打开、退休
到未来恢复的完整生命周期。

### 3. 方案的四步生命周期

**Step 1: 异步确定聚合。**

控制面通过认证 ACS 或等价的异步一致机制确定唯一 `D_sid`，生成
`CC_sid`。`CC_sid` 只负责客户端集合、权重和聚合上下文的一致性，不宣称
历史隐私已经终结。

**Step 2: aggregate-only 打开。**

委员会对 `D_sid` 执行现有的 aggregate-only 数据面，输出加权模型更新或
等价的聚合结果。单客户端更新、单个 mask key、receiver evaluation 和可用于
单项解密的中间对象不进入公开 transcript。本文把这一点作为数据面接口，
不在主文重新证明底层加密构造。

**Step 3: 形成 privacy finality。**

输出后，满足异步活性约束的退休集合执行 state-complete retirement：删除
目标 `sid` 的 direct share、recovery-local state、pending recovery state 和
endpoint 解封状态，并合并单调 frontier。只有满足访问结构条件的退休集合
才能形成 `PF_sid`。`PF_sid` 不是物理擦除证明，而是一个受模型约束的协议
事件；Byzantine 虚假确认计入历史暴露能力。

**Step 4: 只恢复未来仍需使用的状态。**

节点 crash 或 cure 后，恢复操作只重建当前 generation 中仍然 live 的功能
状态。每条恢复贡献绑定目标、恢复实例、generation 和 frontier；参与者先
吸收已经知道的退休事实，再生成恢复贡献。任何被 frontier 支配的 `sid` 都
不能重新进入 `Recover`、`Install`、`Use` 或 `PartDec`。

### 4. 方案的安全核心

方案的安全性用两个层次表达，主文只展示结论，不展开长 hybrid。

第一层是直接访问结构。若 `A_sid` 是退休集合，`B_sid` 是退休前敌手保存的
旧能力，普通情形要求每个授权解密集合 `D` 都满足：

```text
|D intersection A_sid| > |B_sid|.
```

这就是 Robust-Hitting；它说明需要退休哪些节点。

第二层是恢复闭包。若退休后仍有 recovery relation 可以导出旧 capability，
就不能只计算节点集合。令 `R_sid` 表示退休后仍可由合法恢复边导出或重新
安装的旧能力，则有效集合是：

```text
E_sid(B,A_sid) = B union R_sid union C_old(P-A_sid).
```

privacy finality 的判据是所有 `D in Gamma_dec^cap(sid)` 都不满足
`D subseteq E_sid(B,A_sid)`。方案的关键设计目标不是让 `R_sid` 变小，而是
通过 state-complete retirement 和 frontier-bound recovery 使：

```text
R_sid = emptyset.
```

此时一般闭包判据才退化为 Robust-Hitting。该关系是方案的理论落点，也是
方案与普通“VSS + refresh + 前向安全加密”组合的区别。

### 5. 密码学组件的最小分工

首版只保留四类组件，不把它们包装成四项贡献：

1. **数据面：** 采用已有的 aggregate-only threshold encryption 或短种子
   聚合机制，负责隐藏单客户端更新并打开授权聚合；
2. **控制面：** 采用 ACS/异步一致机制，负责唯一 `D_sid`、`CC_sid` 和
   退休事件的因果顺序；
3. **状态面：** 采用 current-share-only 的可验证恢复，负责恢复 live
   state，不恢复 master key 或 retired state；
4. **边界面：** 采用认证的单调 frontier、状态完整擦除和私有传输条件，
   负责使迟到消息和未来 cure 不产生 resurrection edge。

前向安全加密适合作为信道或有序世代的辅助组件，秘密共享适合作为可验证
分发和 live-state recovery 的基础。无序 `sid` 的隐私终结由 frontier、
state-complete retirement 和 recovery closure 共同定义。具体的 opaque
delivery 或 key-origin 采用条件接口表达，相关实例化进入后续技术章节。

### 6. 主文证明纪律

正文只保留三个证明单元：

1. 一个 privacy-finality / closure-aware criterion；
2. 一个 recovery-state localization separation；
3. 一个条件协议实现定理，连同一句话的 correctness、liveness 和代价说明。

逐代 simulator、`PVOD`、`CSO-VE`、`KeyOrigin`、`PECC` 和优势求和进入附录，
主文集中呈现它们支撑的生命周期结论。实验则回答方案对异步 FL 的影响：
客户端纳入率、陈旧度、聚合延迟、退休延迟、恢复延迟、通信/状态成本和模型
质量，而不是重复证明安全性。

## 1. 一句话问题

现有异步安全聚合协议通常证明：即使客户端掉线、消息乱序或部分服务器 Byzantine，系统仍能确定并输出一个聚合结果。但是，对长期运行的委员会而言，输出完成并不意味着历史隐私已经终结。节点可能在未来被腐化、重启、治愈、恢复或换届；只要某条合法恢复路径能够重新生成已经擦除的旧解密份额，攻击者就可能重新打开已完成会话中的单个客户端更新。

本文研究一个此前未被现有安全定义直接捕获的问题：

> **在完全异步、会话并发无序、委员会长期遭受移动腐化且最终所有节点的当前状态都可能暴露时，什么条件才能保证一个已经输出聚合值的会话，其单项更新永远不能被未来的恢复、治愈和换届重新解密？**

我们的答案不是单独使用前向安全加密，也不是给现有协议增加一次密钥刷新，而是把隐私终结定义为一个对所有未来可达恢复状态都保持成立的吸收态：

```text
Privacy Finality
= safe retirement quorum
+ recovery-closed no-resurrection
+ aggregate-only opening
```

## 2. 研究背景

### 2.1 异步联邦学习需要长期运行的安全聚合

跨设备联邦学习很难按同步轮次运行。移动设备、卫星、边缘节点和跨地域机构可能长时间离线，网络延迟也可能高度不稳定。Buffered asynchronous FL 因此允许服务器持续收集更新，只要缓冲区达到条件就形成一次聚合，而不等待所有客户端。

安全聚合在这一流程中承担一个基本任务：服务器或委员会只能获得某个授权集合上的聚合结果，不能恢复单个客户端更新。典型协议使用以下结构：

```text
z_u = x_u + G(sid, k_u),
```

其中 `x_u` 是客户端更新，`k_u` 是短 mask key，`G` 是可聚合的伪随机扩展。密码学协议只需安全地恢复

```text
K_sid = sum_{u in S_sid} w_u k_u,
```

随后移除聚合掩码，而不应逐个恢复 `k_u`。

这一结构已经能显著降低客户端通信：高维梯度仍在明文群或模环上做加法，昂贵密码学只处理 `lambda` 位种子。TACITA、OPA、Buffalo 等工作分别覆盖 one-shot private aggregation、短种子掩码和 buffered asynchronous aggregation 的重要部分。因此，本文不把“把梯度换成短种子”作为创新点，也不重新发明静态 aggregate-only 数据面。

### 2.2 现有安全模型通常在输出时停止

大量安全聚合、阈值加密和 PVSS 定义关注一次执行中的攻击者能力：

- 静态腐化集合在协议开始前确定；
- 自适应腐化在一次安全游戏中累计不超过阈值；
- 密钥刷新按同步或逻辑 epoch 隔离；
- 协议输出后，历史服务器状态不再进入安全实验；
- share recovery 只要求正确恢复一个原始份额，而不区分该份额是否已经因为隐私终结而必须永久消失。

这些模型适合一次性执行，却没有回答长期服务中的关键问题：今天未被攻破的节点，可能在数月后被逐个攻破；今天删除的状态，可能在明天的 crash recovery、proactive repair 或 committee handoff 中被合法重建。

### 2.3 共识终结不等于隐私终结

异步 BFT 已经给出了成熟的 computation finality。ACS、可靠广播和异步共识可以确定：

- 哪些客户端更新被纳入；
- 采用什么权重；
- 哪个聚合 ciphertext 被授权打开；
- 所有正确节点是否接受同一个结果。

记这一证书为 `CC_sid`。它证明计算已经终结，但不证明历史解密能力已经消失。

本文引入不同的对象 `PF_sid`：privacy-finality certificate。它证明的不只是“若干节点声称删除”，而是由证书覆盖的退休集合、会话生命周期内已经泄漏的旧能力以及所有未来合法恢复路径共同决定的安全事实：任何未来可达状态都无法重新形成旧会话的一个授权解密集合。

这一区分是全文的概念起点：

```text
CC_sid: which aggregate is final?
PF_sid: which individual-opening capabilities are gone forever?
```

## 3. 激励攻击：一次合法恢复如何击穿已经完成的会话

考虑 `n=3f+1` 个委员会节点，解密和隐私终结都采用 `2f+1` 门限。会话 `sid` 输出后，有 `2f+1` 个节点执行穿孔和擦除，并形成 `PF_sid`。攻击者在会话存活期间已经读取并保存至多 `f` 个旧份额。未来，攻击者再获得全体节点的当前状态。

如果退休后的状态没有任何恢复边，那么攻击者最多拥有：

```text
f 个历史保存份额
+ f 个未进入退休证书的当前旧份额
= 2f 个旧份额，低于 2f+1 门限。
```

这正是 Robust-Hitting 条件给出的安全边界。

但是，假设 crash recovery 为了可用性保存了一个 VSS backup，或者允许任意 `q_rec` 个 helper 恢复目标节点的旧份额。攻击者只需触发一次完全合法的恢复，就可能从 `2f` 个旧能力扩张到 `2f+1` 个。此时：

- 每个参与者都可能正确执行了协议；
- `CC_sid` 没有被回滚；
- `PF_sid` 的签名没有被伪造；
- 底层 VSS 和阈值加密也没有被破解；
- 隐私仍然因为“恢复了一个本应永远消失的份额”而失败。

这不是传统重放攻击的简单变体。重放只是触发方式，根因是安全定义没有把**所有可生成旧 capability 的恢复关系**纳入隐私访问结构。

## 4. 为什么现有组件不能直接解决

### 4.1 前向安全加密只处理时间前缀

前向安全加密通常按 period 更新密钥，使当前密钥不能解密较早 period 的 ciphertext。它适合全序时间，但本文中的 `sid` 可以任意重叠：

```text
sid_A starts
sid_B starts
sid_B finalizes
sid_C starts
sid_A finalizes
```

系统需要删除 `{sid_B}`，保留 `{sid_A,sid_C}`，随后再删除 `{sid_A}`。这不是一个时间前缀。把它编码为全局 epoch 会引入同步关闭点、阻塞慢会话，或者迫使所有未完成会话重新加密。

Silent Setup STE 对这一边界给出了清楚参照：其 forward security 仍依赖周期 key update；post-compromise security 通过成员本地重采样并发布新 `pk/hint` 获得。它们都能解决有序世代中的密钥演化，但不能直接提供稳定公共键下的无序 `sid` 退休和 punctured-state recovery。

### 4.2 Puncturable encryption 没有解决阈值恢复

单接收者 puncturable encryption 可以在标签 `sid` 上更新 secret key，使更新后的 key 即使暴露也不能解密该标签。DFPE 还允许交错执行 allow/deny 更新。

困难在于委员会不持有一个完整 key，而持有 secret-shared 或分布式状态。对 Shamir share 逐点应用一般非线性 `Puncture` 会提高分享多项式次数；连续穿孔继续累积 degree growth。先重构完整 key 再穿孔则在过程中暴露旧 master capability。普通 VSS handoff 只保持同一个秘密，并不知道哪些标签必须永久消失。

因此，“现成 PE + Shamir sharing”不是一个黑盒答案。需要的是 share-compatible puncture、受 frontier 支配的分布式状态变换，或一种避免直接对共享 PE key 做非线性更新的构造。

### 4.3 Batched threshold encryption 穿孔的是客户端侧对象

BEAT-MEV、BEAST-MEV、WBTE 和 LightBEAT 解决的是公开池中的选择性批量解密。LightBEAT 使用 HIDP 将 puncturable PRF setup/storage 从平方级降低到准线性，这是重要的强近邻。

但其 punctured key 由客户端产生并随 ciphertext 公开；委员会仍持有普通 threshold-ElGamal shares。委员会只聚合解密 `sum k_i`，然后结合每个客户端的公开 punctured key 恢复批内每条消息。LightBEAT 的 HIDP adaptive security 是对自适应选择 punctured identity 的原语安全，而 full protocol 仍采用 static committee corruption。

因此，epochless BTE 证明了“无 per-epoch setup 的批量选择性解密”可以实现，但没有处理：

- 委员会长期 state 的 per-`sid` 穿孔；
- 输出后全体当前状态暴露；
- crash/cure 后恢复已穿孔状态；
- aggregate-only 而非逐条 batch opening。

### 4.4 Proactive secret sharing 保持秘密，本文要求删除能力

PSS、APSS、CHURP、DyCAPS、Shanrang 和动态委员会 DPSS 的目标，是在成员变化或移动腐化下持续维护同一个长期秘密。它们通过 refresh、reshare 和 handoff 让新状态继续代表原秘密。

本文的目标相反：系统必须继续服务未来会话，但对已经退休的 `sid`，恢复过程不得再保持对应能力。普通 handoff 若忠实保持原 master secret，就可能忠实恢复历史解密能力。

区别可以概括为：

```text
PSS correctness: preserve the secret across failures.
Privacy finality: preserve future service while destroying selected past capabilities.
```

### 4.5 VSSR 恢复份额，但没有退休语义

VSSR 使用 recovery polynomial 与 DPRF，从 `k` 个有效贡献恢复缺失份额，是异步 BFT 中非常合适的局部恢复基线。其安全游戏允许 compromise、contribution 和 recovery query 自适应发生，但对每个 commitment 累计限制可用来源少于 `k`。论文也明确把 proactive share recovery 留作未来工作。

更重要的是，一个 VSSR share 的 recovery-complete state 不只包含 direct share，还可能包括：

```text
direct share
+ recovery-polynomial shares
+ DPRF contribution capability
+ public nonce / commitment
+ pending recovery transcript.
```

退休时只删除 direct share 并不充分。只要足够多节点仍保留该 commitment 的 recovery-polynomial state，未来暴露就可能重新生成旧 share。

这里也不能反向过度声称“共享 DPRF 必然不安全”。DPRF share 单独通常不能恢复旧份额；真正需要分析的是它与残留 coordinate-local recovery state 的联合能力。这正是恢复闭包模型的价值。

此外，VSSR 在典型 `n=3f+1` 配置中以 `f+1` 个有效贡献恢复目标 share。该门限适合一次 sharing 的可用性，却不能直接进入本文的长期模型：repair-amplification 会把有效历史隐私门限降到 `f+1`。本文若复用 VSSR 技术，必须把恢复访问结构重新参数化到至少与解密门限同等安全，或者限制其只处理从未退休的 coordinate；不能把原协议作为无修改黑盒。

## 5. 核心研究问题

本文集中回答一个主问题：

> **能否在稳定公共键、完全异步和长期移动腐化下，为 aggregate-only secure aggregation 建立一种 recovery-closed privacy finality，使任意已退休 `sid` 的解密能力在 crash recovery、节点治愈和委员会换届后仍不可复活？**

主问题分解为四个相互咬合的子问题：

1. **刻画问题：** 对一般解密访问结构和一般恢复关系，隐私终结的必要充分条件是什么？
2. **异步问题：** 当退休、恢复和迟到消息并发发生时，什么状态机条件才能让退休成为吸收态？
3. **密码学问题：** 如何恢复仍活跃 capability，同时不恢复已经退休 capability？
4. **复杂度问题：** 稳定公共键、精确无序穿孔、紧凑状态、低交互恢复和零未来活性误差能否同时达到？

## 6. 系统与敌手模型

### 6.1 网络与会话

- 委员会节点通过完全异步认证信道通信；消息可任意延迟、乱序和重放，但最终发送给正确节点的消息会被交付。
- 聚合会话以唯一 `sid` 标识，可以任意重叠，不假设全局 epoch、同步时钟或已知消息延迟上界。
- 每个 `sid` 由 ACS 或等价异步协议固定唯一描述符：

```text
D_sid = (sid, cfg, S_sid, weights, H_ct, H_out).
```

- 每个诚实节点只为唯一 `D_sid` 释放部分聚合解密材料。

### 6.2 长期移动自适应腐化

- 敌手可跨会话自适应选择腐化节点，并永久保存读取到的所有历史状态。
- 长期腐化集合的并集可以覆盖整个委员会。
- 任意时刻最多 `f` 个节点主动 Byzantine。
- 对每个尚未退休的会话或尚未完成的恢复实例，敌手累计读取的易失秘密状态至多 `b` 个参与者。

最后一条不是技术便利，而是信息论必要条件。若只限制同时腐化数，却允许敌手在异步延迟期间无限快移动，它可以在擦除前依次读取足够多份额，任何阈值方案都会失败。

### 6.3 最终暴露目标

对已经形成 `PF_sid` 的会话，安全实验允许攻击者获得：

- 所有未被安全擦除的协议 transcript；
- 会话生命周期内已窃取并保存的旧状态；
- 所有委员会节点未来某时刻的当前状态；
- 所有由协议允许的 recovery、cure 和 handoff 输出。

即使如此，攻击者也只能得到授权聚合值，不能区分两组具有相同授权加权和的客户端更新。

### 6.4 首篇工作的范围

首篇工作把固定身份委员会中的移动腐化与 crash/cure 作为主模型。完整 join/leave/reconfiguration 通过跨配置 handoff closure 给出扩展定理，而不把 membership agreement、stake update 和委员会选举同时塞入核心协议。

本文不研究：

- adaptive-query 或跨多次精确聚合输出推断数据库记录；
- 未来直接腐化并读取仍保存原始训练数据的客户端；
- 无安全擦除模型下的软件 certified deletion；
- 只限制瞬时腐化、但允许无限快移动的无条件 continuous-mobile security。

这些边界不是叙事中心。本文正面解决的是委员会密码学状态在长期恢复过程中的 no-resurrection。

## 7. 第一理论核心：Privacy Finality 是鲁棒横截

设委员会节点集合为 `P`，旧会话 `sid` 的解密访问结构为 `Gamma_dec`。`Gamma_dec` 中每个集合 `D` 都足以形成旧解密能力。

令：

- `A_sid`：已经执行有效原子 `Puncture+Erase` 的退休节点集合；
- `B_sid`：退休前已经被攻击者读取并永久保存旧 capability 的节点集合；
- `|B_sid| <= b`。

若暂时不考虑恢复，未来全体当前状态暴露后仍可获得旧能力的节点集合是：

```text
X_sid = B_sid union (P - A_sid).
```

因此，隐私终结的精确条件是：

```text
for every B_sid with |B_sid| <= b:
    B_sid union (P - A_sid) notin Gamma_dec.
```

等价地：

```text
for every D in Gamma_dec:
    |D intersection A_sid| > b.
```

这给出 **Robust-Hitting Characterization**：退休集合必须与每个授权解密集合相交超过攻击者能够提前保存的旧份额数。它不是单纯数签名，而是访问结构超图上的鲁棒横截条件。

### 7.1 阈值系统的紧边界

对于 `q`-out-of-`n` 解密访问结构和 `a=|A_sid|`，只知道 `|B_sid|<=b` 时，最坏可用旧份额数为：

```text
n - a + min(a,b).
```

所以 privacy finality 当且仅当：

```text
n - a + min(a,b) < q.
```

在有用区间 `a>=b` 中，它化为：

```text
n - a + b < q.
```

对 `n=3f+1`、`b=f`，解密活性与异步退休活性共同给出紧点：

```text
q = a = 2f+1.
```

这一结果的重要性不在算术本身，而在于它统一了三件通常分开证明的事：解密活性、退休活性和未来暴露后的历史隐私。

### 7.2 Retirement-Liveness Sandwich

对一般访问结构，令 `Gamma_cert` 是协议接受的退休证书集合族，`Gamma_live` 是 Byzantine withholding 后可能响应的节点集合族。安全和活性要求：

```text
privacy safety:
    Gamma_cert subseteq H_b(Gamma_dec)

privacy liveness:
    for every L in Gamma_live,
    exists A in Gamma_cert such that A subseteq L.
```

其中 `H_b(Gamma_dec)` 是全部 `b`-鲁棒横截集合族。该形式自然支持加权节点、分层信任和非对称访问结构，比固定 `2f+1` 计数更一般。

## 8. 第二理论核心：恢复会改变隐私访问结构

Robust-Hitting 只计算“当前谁还持有旧份额”，但 share recovery 会从已有 capability 推导新的 capability。为此，把系统表示为一个 typed capability hypergraph，而不是只把节点身份当作顶点。

### 8.1 Recovery Closure

对固定 `sid`，定义能力宇宙：

```text
C_sid = C_dec union C_rp union C_dprf union C_backup union C_handoff,
```

分别表示直接解密份额、recovery-polynomial state、DPRF contribution capability、持久 backup 和跨配置 handoff output。每条合法恢复规则表示为有向超边：

```text
e = (U -> c), where U subseteq C_sid and c in C_sid.
```

例如，`q_rec` 个当前 share 和一组新鲜恢复随机性可以导出目标节点的新 share；足够多 recovery-polynomial shares 与 DPRF contributions 可以导出旧 share；一个有效 handoff certificate 可以导出新配置中的 share。

对初始能力集合 `X subseteq C_sid`，定义最小恢复闭包：

```text
Cl_E(X) = the least Y such that
    X subseteq Y, and
    for every edge (U -> c) in E,
    U subseteq Y implies c in Y.
```

下文把这个闭包简记为 `Cl_rec`。令 `X_current` 表示未来全体当前状态暴露得到的 typed capabilities，`X_hist(B_sid)` 表示会话生命周期腐化留下的历史 typed capabilities，并令 `Gamma_dec^cap(sid)` 是足以解密 `sid` 的 capability 集合族。那么真正的 privacy-finality 条件是：

```text
for every admissible B_sid:
    no D in Gamma_dec^cap(sid) satisfies
    D subseteq Cl_rec(X_current union X_hist(B_sid)).
```

这就是 **Repair-Closure Characterization**。当每个节点只有一种直接解密 capability 时，它退化为前面的节点集合表达；Robust-Hitting 则是所有退休标签恢复边都已经失效、因此 `Cl_rec(X)=X` 时的特例。typed 版本避免错误地把一个 DPRF share、一个 recovery-polynomial share和一个直接解密 share视为同一种能力。

### 8.2 Repair Amplification

若任意 `q_rec` 个旧 helper capability 可以恢复任意目标旧份额，而解密门限是 `q_dec`，则攻击者只需先达到较小门限，再通过恢复闭包扩张。阈值系统的安全条件变为：

```text
n - a + min(a,b) < min(q_dec, q_rec).
```

因此，低门限恢复并非“只提高可用性”。它会降低系统的有效历史隐私门限。在 `n=3f+1,b=f,a<=2f+1` 时，`q_rec` 和 `q_dec` 都必须至少为 `2f+1`。

### 8.3 Recovery-State Localization Barrier

设普通恢复黑盒通过持久全局状态 `G` 和标签局部状态 `L_sid` 生成旧 capability：

```text
Recover(G, L_sid, helper states) -> old capability for sid.
```

若退休只删除 direct share，既没有让 `G` 对 `sid` 穿孔，也没有让一个满足 Robust-Hitting 的节点集合删除全部 `L_sid`，那么未来暴露可以重新运行合法恢复关系，将旧 capability 加回 `Cl_rec`。

这得到一个条件版黑盒分离：wrapper-level tombstone 不能自动把 ordinary VSSR/DPSS 变成 privacy-final recovery。必须满足至少一项：

1. `L_sid` 完全 coordinate-local，并在退休时与 direct share 原子删除；
2. 全局恢复权 `G` 本身支持无序、可验证、share-compatible 的 per-`sid` puncture；
3. 系统 rekey 或进入新 epoch，使全部旧恢复材料失效。

第三条是已有系统常用出口，但改变公共键或引入全局世代。前两条构成本文的核心构造空间。

## 9. 第三理论核心：异步恢复中的因果栅栏

即使恢复材料最终会被删除，完全异步网络仍可延迟退休前生成的合法恢复消息，并在 `PF_sid` 后交付。

设 `m_old` 是退休前生成的有效恢复或 handoff 消息。如果：

- `m_old` 的认证在退休后仍有效；
- 消息没有绑定一个支配 `Retired(sid)` 的 frontier；
- 接收者状态机允许它安装旧 capability；

则调度者可构造两个对接收者局部不可区分的执行：一个在退休前交付 `m_old`，一个在退休后交付同一消息。为了满足恢复活性，节点在第一个执行中必须接受；如果没有额外因果信息，它在第二个执行中也会接受，从而复活旧能力。

这给出 **Causal-Fence Necessity**：所有可能生成或安装 secret capability 的消息都必须携带并验证单调 frontier，或者改变密钥世代，使旧消息在密码学上失效。这里还必须区分“安装安全”和“transcript 安全”：即使 `CheckInstall` 拒绝旧恢复输出，只要归档 contribution 与未来暴露的接收者/channel state 可以离线导出旧 share，攻击者仍已获得 capability。完全异步下，尚未看到 `PF_sid` 的 helper 可能在退休前合法生成随后迟到的 contribution；因此协议必须同时约束已知退休后的 contribution generation、旧 transcript 的 post-finality 可解封性和最终安装。

所需 frontier 合并必须满足：

```text
Merge is commutative, associative, and idempotent;
installed frontier never decreases;
recovery output for T_req cannot install under T_current > T_req.
```

因此节点状态机至少包含：

```text
Active -> Retiring -> Punctured -> Active
Active -> Recovering -> Active
```

当 `Recovering` 状态收到更新的 `PF_sid` 时，只能提升 `T_req` 或取消并重启恢复。任何基于旧 frontier 完成的恢复输出都不能安装。

## 10. 解决方案总览

本文采用编译器式结构，把已经成熟的静态聚合数据面与新的长期状态层分开：

```text
Long-Lived Async Secure Aggregation
    = Static Aggregate-Only Opening
    + Recovery-Closed Lifecycle (RCL)
    + Asynchronous CC/PF control plane.
```

### 10.1 数据面：只聚合短 mask key

客户端计算：

```text
z_u = x_u + G(sid, k_u)
ct_u = Enc(PK, sid, k_u)
pi_u = proof of ciphertext/mask consistency.
```

ACS 固定 `S_sid`、权重和唯一 ciphertext digest。委员会只对：

```text
ct_sum = EvalAdd({w_u * ct_u : u in S_sid})
```

释放部分解密，最终只得到 `K_sid=sum w_u k_u`。安全游戏比较两组单项 keys，只要求它们具有相同授权加权和。这一层可复用 TACITA-style extended CPA aggregate-opening 安全，不把逐条 BTE 当作黑盒。

### 10.2 状态面：RCL

`RCL` 提供四个核心接口：

```text
Puncture(sid, T)
Contribute(rid, target, T_req)
Recover(rid, target, T_req, contributions)
CheckInstall(state, recovered_state, T_current)
```

它必须保证：

- 已退休 `sid` 的 direct capability 和 recovery-complete local state 一起消失；
- 仍活跃会话和未来会话可在 crash 后恢复；
- 恢复不先重构未穿孔 master secret；
- 所有贡献绑定 `rid/target/cfg/T_req`；
- 已归档 contribution 与未来 channel/receiver state 不能导出 retired capability；
- Byzantine 节点不能让不同正确节点安装不一致 state；
- 未来暴露全部当前状态后，旧标签的 recovery closure 仍不包含授权解密集合。

### 10.3 控制面：分离 `CC_sid` 与 `PF_sid`

协议先形成 `CC_sid`，固定唯一授权聚合。完成聚合释放后，节点执行原子状态转换：

```text
Puncture committee state for sid
+ erase raw per-client/per-session state
+ erase sid-local recovery state
+ advance local frontier
+ sign retirement acknowledgement.
```

当确认集合属于 `H_b(Gamma_dec)` 时形成 `PF_sid`。`PF_sid` 不声称证明 Byzantine 节点真的物理擦除；虚假确认节点被计入历史能力集合 `B_sid`，Robust-Hitting 正是为此设计。

### 10.4 证明面：可验证状态转换而非“擦除证明”

NIZK 或可验证承诺用于证明：

- 客户端 mask 与 ciphertext 使用同一个 `k_u`；
- 部分聚合解密绑定唯一 `D_sid`；
- recovery contribution 来自承诺的当前 share；
- recovered state 与目标 frontier 一致；
- 跨坐标 ciphertext 加密同一个 mask key。

物理擦除仍是诚实节点模型假设。本文证明的是：只要诚实节点按状态机擦除，Byzantine 虚假确认、历史暴露和所有合法恢复路径都被访问结构条件吸收。

## 11. 最小具体构造：BF-RPTA

一般 puncturable threshold state 很难直接实例化。本文使用 coordinate deletion 给出一个最小、可分析的正向见证。

### 11.1 基本思想

系统维护 `m` 个独立 threshold aggregate-opening coordinates。每个会话通过不可偏置盐将 `sid` 映射到 `k` 个坐标：

```text
I_sid = {H_1(salt,sid), ..., H_k(salt,sid)}.
```

客户端将同一个短 mask key 一致地编码到这些坐标，并附带跨坐标同明文证明。会话退休时，证书中的节点删除 `I_sid` 上的全部 direct shares 和 coordinate-local recovery state。Bloom-style one-sided 性质保证：已退休 `sid` 没有 false negative，因此其全部指定坐标都会失去旧能力。

未来新会话只有在所有候选坐标都已被历史退休占用时才无法服务。这是 liveness false positive，而不是 privacy failure。

### 11.2 Current-Share-Only Repair

BF-RPTA 不保存一个能在未来重新打开任意 coordinate 的 durable encrypted backup。目标节点只能从其他节点**当前仍存活的 coordinate shares**交互恢复：

```text
LSR.Repair(rid, target, coordinate, T_req).
```

退休坐标没有恢复接口。对活跃坐标，至少 `q_rec` 个当前 helper 可以使用新鲜临时随机性生成可验证贡献；恢复完成后临时状态被擦除。

如果 repair 和 decryption 使用相同访问结构，且退休集合满足 Robust-Hitting，那么退休坐标的初始旧能力集合低于恢复门限，无法触发任何生成直接解密 share 的恢复边：

```text
Cl_rec(X_sid) intersection C_dec = X_sid intersection C_dec.
```

与此同时，未退休坐标的恢复活性必须按 target exclusion 计算：缺失目标不能作为自己的 helper，因此至少需要 `n-f-1` 个其他正确节点。于是 `n=3f+1,q_rec=2f+1` 不足以保证 repair；可行的 homogeneous reusable repair 至少要求 `n>=2f+b+2`，在 `b=f` 时为 `n>=3f+2`。

### 11.3 防止恶意选择 `sid`

公开固定哈希允许攻击者 grinding `sid`，不能直接套用随机输入的 Bloom false-positive 分析。协议先承诺会话描述，再通过异步共同随机性生成不可偏置高熵盐：

```text
SC_sid = certificate for salt and session commitment.
CC_sid binds H(SC_sid).
```

客户端提交所用坐标在 `SC_sid` 后确定。攻击者不能在看到坐标后无限尝试不同 `sid`。这一机制只保护未来 liveness 分析，不放松退休会话的 privacy guarantee。

### 11.4 代价与意义

BF-RPTA 的节点状态为：

```text
m = Theta(R log(1/epsilon))
```

个功能坐标，其中 `R` 是计划支持的退休会话数，`epsilon` 是未来会话 liveness false-positive 上界。修复一个节点的朴素代价为 `O(m*C_LSR(n))`。

这一构造的价值不是宣称它在所有参数上最优，而是提供第一个与理论刻画精确对齐的 witness：

- 退休会话 privacy 无 false negative；
- 恢复闭包对退休坐标不扩张；
- 未来会话保持高概率活性；
- 状态代价达到 one-sided approximate-membership 的渐近下界。

## 12. 状态与复杂度下界

### 12.1 精确本地线性穿孔下界

设本地功能状态空间为 `V`，每个会话 `tau` 的解密 capability 是线性泛函 `ell_tau:V->F`，本地穿孔为线性映射 `P_tau:V->V`，并要求：

```text
ell_tau o P_tau = 0
ell_sigma o P_tau = ell_sigma, for every sigma != tau.
```

则不同 `ell_tau` 必须线性无关，因此：

```text
dim(V) >= M,
```

其中 `M` 是可独立退休的标签数。该结果说明，精确、任意标签、无交互、share-local 的线性穿孔不能同时保持固定维紧凑状态。

这不是对所有 puncturable encryption 的无条件下界。非线性 trapdoor delegation、每次追加随机 secret component、通用 MPC 或 rekey 可以绕开线性模型，但会分别支付状态、交互或公共键更新成本。

### 12.2 近似 frontier 空间下界

把 coordinate-deletion frontier 看成 one-sided approximate-membership structure：

- 对已退休标签不允许 false negative；
- 对未退休标签误判概率至多 `epsilon`；
- 最多支持 `R` 个退休标签。

标准计数给出至少：

```text
R log_2(1/epsilon) - O(R)
```

bits。Bloom frontier 使用 `Theta(R log(1/epsilon))`，因此在这一明确模型内常数因子近最优。

### 12.3 Recoverable Puncture Tradeoff

两个下界与 BF-RPTA 共同形成论文的复杂度主线：

```text
exact arbitrary-label local puncture
    -> linear functional state or stronger nonlocal machinery

approximate one-sided frontier
    -> Theta(R log(1/epsilon)) state
    -> epsilon future-liveness error
```

这把论文从“某个新协议”提升为一个稳定公共键下 recoverable puncture 的状态、交互和活性误差权衡。

## 13. 动态委员会扩展

动态成员不是简单增加一个 DPSS 模块。普通 DPSS handoff 的正确性目标是把同一个 secret 从旧委员会传给新委员会；如果 handoff 输入包含退休前 master state，它可能跨配置复活旧 `sid`。

### 13.1 Project-Then-Handoff

正确顺序是：

```text
Project(T)
    -> remove every retired coordinate/capability
    -> Handoff(cfg_old, cfg_new, live coordinates only).
```

所有 handoff 消息必须绑定：

```text
cfg_old, cfg_new, rid, coordinate, T_req.
```

新委员会只安装满足以下条件的 state：

- 来源配置和目标配置唯一；
- handoff certificate 有效；
- `T_req` 不低于本地已知 frontier；
- coordinate 在 `T_req` 下仍为 live；
- 状态承诺与目标公共键/配置承诺一致。

### 13.2 Handoff Closure

令 `E_rec` 是同配置恢复边，`E_ho` 是跨配置 handoff 边。定义：

```text
Cl_{rec+ho}(X) = closure under E_rec union E_ho.
```

跨配置 privacy finality 要求：

```text
for every retired sid and admissible future corruption B:
Cl_{rec+ho}(X_sid union B) notin Gamma_dec(sid).
```

目标定理 **Handoff-Closure Preservation** 表述为：若旧配置满足 `PF_sid`，所有 handoff 边只从 projected live state 出发，目标配置安装时验证同一或更高 frontier，则换届保持 `PF_sid`；反之，任意从 pre-projection backup 出发的合法 handoff 边都会进入闭包，并可构造匹配复活攻击。

这一扩展使动态委员会具有理论意义。贡献不是“支持 churn”，而是说明什么样的 churn protocol 能保持已经完成的隐私终结。

## 14. 完整协议流程

### 14.1 Setup

1. 委员会建立 `Static-AO` 的稳定公共参数和 threshold coordinate states。
2. 建立异步认证、ACS、共同随机性和状态承诺参数。
3. 初始化空 frontier `T_i`。

### 14.2 Session Certification

1. 客户端或协调层提交 `sid` 与公开元数据 commitment。
2. 委员会产生不可偏置 `salt_sid` 和 `SC_sid`。
3. 客户端据此确定 `I_sid`，提交 masked update、coordinate ciphertexts 和一致性证明。

### 14.3 Computation Finality

1. ACS 确定 `S_sid` 和唯一描述符 `D_sid`。
2. 节点拒绝不在 `D_sid` 中或证明无效的 ciphertext。
3. 形成 `CC_sid`。

### 14.4 Aggregate Release

1. 每个节点只对 `D_sid` 的聚合 ciphertext 发布部分解密。
2. 收集解密访问集合后恢复 `K_sid`。
3. 输出唯一聚合 `sum w_u x_u`。
4. 不输出单客户端 `k_u` 或 `x_u`。

### 14.5 Privacy Retirement

1. 节点验证 `CC_sid` 和 release context。
2. 进入 `Retiring`，阻止同一 `sid` 启动新恢复。
3. 删除 `I_sid` 上的 direct share、local recovery state 和 pending transcript。
4. 提升 frontier 并完成原子安装。
5. 擦除旧状态后签发 retirement acknowledgement。
6. 当确认集合属于 `H_b(Gamma_dec)` 时形成 `PF_sid`。

### 14.6 Cure and Recovery

1. 恢复节点请求当前 `T_req` 下的 live coordinates。
2. helper 只对 live coordinate 生成绑定 `rid/target/cfg/T_req` 的贡献。
3. 目标节点验证贡献和恢复状态承诺。
4. contribution 只编码 `T_req` 下的 projected live state，并使用可擦除的 target-ephemeral channel 或等价 transcript-hiding 机制。
5. 若期间 frontier 提升，则旧恢复输出作废，旧解封能力也必须失效。
6. `CheckInstall` 成功后原子替换当前 state，并擦除临时恢复材料和接收者 ephemeral secret。

## 15. 安全证明路线

### 15.1 定义层

先定义三个独立但组合的安全对象：

1. `G_AO^sel`：固定目标 `sid` 和唯一授权描述符，两组 challenge updates 具有相同聚合；
2. `G_RCL^rec`：Byzantine recovery correctness、frontier monotonicity、stale-output rejection 和 future-service liveness；
3. `PF` event：未来全体当前状态暴露与所有合法 recovery/handoff transcript 下的 individual-update indistinguishability。

### 15.2 必要性

- Robust-Hitting 不满足时，选择与退休集合交集至多 `b` 的授权解密集，得到 matching exposure attack。
- Repair-Closure 不满足时，按闭包拓扑顺序逐步触发合法恢复，直到形成授权解密集合。
- 没有 generate/extract/install 三重 causal fence 时，延迟退休前合法恢复消息，在 `PF_sid` 后安装或离线提取旧 state。
- 保留 durable unpunctured backup 时，未来暴露 recovery authority 后重放 backup。

### 15.3 充分性

固定目标 `sid*`：

1. 用 `G_RCL^rec` 排除 stale recovery install，并证明所有可生成的旧 capability 都包含在 `Cl_rec` 中；
2. 用 Repair-Closure 条件证明闭包不包含任何 `D in Gamma_dec`；
3. 使用支持跨坐标同明文约束的联合向量 `Static-AO` 游戏，将 challenge world 0
   替换为 world 1；不能未经证明地逐坐标 hybrid；
4. 模拟客户端一致性证明和 Byzantine invalid contribution；
5. 用唯一 `CC_sid` 排除同一 ciphertext 在不同集合或权重下被重复授权；
6. 用 mask PRG 的伪随机性将单项更新隐藏归约到 mask key 安全。

最终得到：在 causal-generation-bounded mobile 模型下，形成 `PF_sid` 的会话即使经历任意后续 cure、合法 recovery、配置 handoff 和全体当前状态暴露，也只泄漏协议授权的聚合结果。

## 16. 主要挑战与对应技术

| 挑战 | 为什么困难 | 本文方法 |
|---|---|---|
| 输出完成后仍可能泄漏 | 未来腐化可读取当前密钥并处理归档 ciphertext | 将 `CC_sid` 与 `PF_sid` 分离，定义 post-finality exposure game |
| Byzantine 虚假擦除确认 | 软件签名不能证明物理擦除 | 把虚假确认计入 `B_sid`，用 Robust-Hitting 吸收 |
| 恢复重新生成旧份额 | VSS correctness 恰好要求恢复原 share | 用 Repair-Closure 刻画所有生成路径，退休 recovery-complete state |
| 异步迟到恢复消息 | 合法旧消息可在退休后到达或被未来密钥解封 | 单调 frontier、transcript hiding 与 generation/extraction/installation 三重栅栏 |
| 无序 `sid` 无法用 FSE 前缀表示 | 并发会话终结顺序与开始顺序不同 | per-`sid` puncture 与可交换 frontier |
| Shamir share 上非线性穿孔 | degree growth 或重构旧 master key | coordinate deletion + current-share-only linear repair |
| 精确紧凑状态难以兼得 | 独立标签需要独立功能维度 | 线性状态下界与 approximate frontier tradeoff |
| 动态委员会复制旧能力 | DPSS handoff 默认保持原秘密 | `Project(T)` 后只 handoff live coordinates |

## 17. 主要贡献

论文的贡献应组织成一个闭环，而不是一组松散组件。

### Contribution 1: Privacy Finality Definition

提出长期异步安全聚合的 privacy finality。该定义显式包含并发 `sid`、会话生命周期内移动腐化、退休后的全体当前状态暴露、crash/cure、恢复 transcript 和 aggregate-only leakage。

概念贡献是把“聚合输出正确”与“历史单项能力永久终结”分离，使长期 secure aggregation 可以被独立审计。

### Contribution 2: Access-Structure Characterization

证明退休集合的 Robust-Hitting 必要充分条件，并给出 retirement-liveness sandwich。结果适用于一般、加权和非对称访问结构；阈值系统得到紧参数：

```text
n - a + min(a,b) < q.
```

### Contribution 3: Recovery-Closure Theory

提出 capability recovery hypergraph 和 `Cl_rec`，证明 privacy finality 等价于恢复闭包避开全部授权解密集合。由此得到 repair-amplification：恢复门限会成为新的有效隐私门限。

这是论文最重要的理论提升，因为它解释了为何“安全删除份额 + 安全 VSS recovery”两个分别安全的组件可以组合出不安全的长期系统。

### Contribution 3A: Cross-Generation Affine Coupling

对 current-share-only resharing，提出 `L_E` 驱动的跨代仿射耦合：同一个
vanishing polynomial 同时扰动每代 current polynomial 和每个 helper polynomial，
保持所有 residual/history 可见点、helper equality relation 和 resharing 递归
不变，却统一平移每代秘密。该引理把“每轮少于门限”提升为整条 repair 链的
视图模拟工具，解释为何 hidden helper 不会因 generation 更替而被逐轮拼接。
它只覆盖线性 share layer；aggregate-opening 的非线性恢复边仍需单独审计。

### Contribution 3B: Cross-Coordinate Coupling Lemma

将 3A 从单坐标推广到 BF-RPTA 的多坐标情形：独立坐标分享使用各自的 residual
vanishing polynomial，但由同一个隐藏 `Delta` 耦合，使同一 mask key 的跨坐标
关系在整条 repair 链上保持。该引理刻画了一个可组合的模拟不变量：公开的一致
性关系并不等价于授权开启能力。若 `Static-AO` transcript 能从多坐标 partial
shares 产生额外 opening，则主定理的失败可以精确归因于数据面组合，而不是
share resharing 的代数部分。

### Contribution 4: No-Resurrection Barriers

给出三类匹配负面结果：

- Puncture-Recursion：持久 backup 与未穿孔 recovery authority 会恢复旧能力；
- Recovery-State Localization Barrier：删除 direct share 而保留可组合的局部恢复状态不足；
- Causal-Fence Necessity：无 frontier 支配的迟到恢复消息可在退休后安装旧状态。

这些结果共同关闭“普通 DKG/VSSR/DPSS + 现成 PE”的直接黑盒组合。

### Contribution 5: RCL and the BF-RPTA Conditional Instance

定义 recovery-closed lifecycle 接口，给出 coordinate-local deletion 和 current-share-only repair 的异步状态机，并把它与 `Joint-AO^mob` 数据面接口组合。TACITA-style `Static-AO` 只有在通过 adaptive lifting 后，才能作为该接口的具体数据面。

BF-RPTA 以 `epsilon` 级未来会话活性误差换取 `Theta(R log(1/epsilon))` state，同时对已退休会话保持确定性 privacy finality。

### Contribution 6: Matching State Tradeoff

证明精确线性 share-local puncture 的 `Omega(M)` 功能维数下界，以及 one-sided approximate frontier 的 `R log(1/epsilon)-O(R)` 空间下界。BF-RPTA 在后一个模型内渐近匹配。

### Contribution 7: Dynamic-Committee Preservation

把 committee handoff 纳入同一个 closure framework，给出 `Project-Then-Handoff` compiler 与 Handoff-Closure Preservation 条件。它说明已有 DPSS 可以承担 live-state 搬迁，但不能替代 privacy projection。

动态扩展是否进入主贡献，取决于最终是否得到必要性与充分性定理；基础 churn 支持本身不作为创新声明。

## 18. 与现有工作的明确区别

| 工作方向 | 已解决问题 | 本文新增对象 |
|---|---|---|
| 异步 SA / Buffalo | 掉线和缓冲异步下的聚合隐私与效率 | 长期移动腐化、退休后全状态暴露、恢复闭包 |
| TACITA / OPA | 静态 one-shot aggregate-only opening | 可恢复、可穿孔的长期委员会 state |
| FSE | 全序时间前缀的历史 ciphertext 安全 | 并发无序 `sid` 的独立 privacy finality |
| PE / DFPE | 单接收者标签撤销 | 阈值访问结构、Byzantine 退休 quorum、share recovery |
| BEAT-MEV / LightBEAT / WBTE | epochless 或 weighted batch opening | 不逐条输出、委员会状态穿孔、future exposure |
| APSS / DPSS / CHURP | 移动腐化或动态委员会下保持长期秘密 | 选择性销毁历史 capability，同时恢复未来服务 |
| VSSR | 异步恢复原始 share | 恢复关系按退休标签关闭，避免 recovery resurrection |

本文不与这些工作争夺相同指标。它建立的是一个此前被不同文献分别绕开的交叉问题：

```text
aggregate-only
+ unordered session retirement
+ long-lived mobile corruption
+ post-retirement total current-state exposure
+ Byzantine asynchronous recovery
+ stable public key.
```

## 19. 创新价值

### 19.1 新安全概念

Privacy finality 将安全聚合从“一次协议执行”提升为“长期服务中的不可逆状态性质”。它可以成为分析 threshold decryption、private mempool、分布式密钥托管和动态访问控制系统的通用工具。

### 19.2 新组合失败模式

论文揭示一种反直觉现象：容错恢复和历史隐私不是自动兼容的。一个 individually secure 的 VSS recovery layer 可以扩张另一个 individually secure 的 puncturable decryption layer 的有效访问结构。Repair-Closure 给出统一、可机械检查的判据。

### 19.3 新理论权衡

本文不只证明“某方案不安全”，而是连接：

- 访问结构鲁棒横截；
- 恢复 hypergraph closure；
- 异步因果状态机；
- share-local 代数下界；
- approximate-membership 空间下界。

这为稳定公共键下 recoverable puncture 给出一组可以比较不同构造的理论坐标。

### 19.4 新协议设计原则

`Project-Then-Recover/Handoff` 是直接可用的系统原则：任何状态恢复前，先按不可回滚 privacy frontier 投影；恢复协议只能操作投影后的 live state。这个原则比“记得删除旧 key”更精确，也能指导真实系统审计。

## 20. 应用价值

### 20.1 长期异步联邦学习服务

生产级 FL 聚合服务器会长期运行、重启、迁移和滚动升级。即使每轮协议本身安全，持久备份、灾难恢复和节点替换仍可能让数月前的客户端密文重新可解。Privacy finality 给出端到端生命周期保证。

### 20.2 卫星与边缘网络

LEO 卫星和间歇连接边缘设备具有长延迟、掉线和节点替换，难以依赖全局 epoch。无序会话退休和 project-before-handoff 比周期全局换键更符合其网络结构。

### 20.3 跨机构联合建模

医院、银行和企业联盟通常要求稳定身份和可审计密钥治理，同时又有灾备与成员变更。`PF_sid` 可以作为一项独立审计事件，说明某次训练任务的单项解密能力已从所有允许恢复路径中移除。

### 20.4 私有 mempool 与分布式托管

尽管本文以 secure aggregation 为主要应用，恢复闭包也适用于 threshold encrypted mempool 和分布式托管：区块 finality、交易公开或访问撤销后，旧 decrypt capability 是否会被下一次 committee recovery 重新生成。

## 21. 实验与评估计划

实验只服务于理论叙事，不重复实现完整 FL 系统。

### 21.1 微基准

- `Puncture` 每个会话的本地时间和确认通信；
- current-share-only repair 的延迟与通信；
- `CheckInstall` 和 frontier merge 开销；
- 跨坐标同明文证明的生成与验证成本；
- `Project-Then-Handoff` 相对普通 DPSS handoff 的额外开销。

### 21.2 端到端原型

实现一个最小 buffered asynchronous aggregation service：

- 客户端一次提交 masked vector 和短 key ciphertext；
- `n=4,7,10,16,31,64` 的委员会规模；
- 模拟 WAN 延迟、Byzantine withholding、节点 crash/cure；
- 并发运行多个无序完成的 `sid`；
- 在 `PF_sid` 后执行恢复与全体当前状态导出，验证旧 coordinate 不可恢复。

### 21.3 关键比较

比较对象不应是普通同步 SA 的训练精度，而应是长期状态机制：

- 每 coordinate 独立 VSSR/AVSS repair；
- BF-RPTA current-share-only repair；
- epoch rekey/DPSS baseline；
- 不带 frontier 的恢复，用作 resurrection attack demonstration。

### 21.4 主要图表

1. 退休容量 `R`、误差 `epsilon` 与状态 `m` 的权衡；
2. repair latency 随 `m,n,f` 的变化；
3. 并发退休和恢复竞争下的完成率；
4. epoch rekey 与 unordered puncture 在慢会话比例增加时的阻塞差异；
5. project-before-handoff 的状态量与普通全量 handoff 的比较。

### 21.5 首轮模拟器与基线

首轮已实现 `experiments/privacy_finality_sim.py`。它使用离散事件调度器和抽象
typed capability ledger，不表示真实群元素或明文，因此只用于检验协议层攻击与
代价。固定种子运行：

```text
python3 experiments/privacy_finality_sim.py --trials 200 --output experiments/results.csv --seed 7
```

每个 trial 只采样一次延迟和 withholding 场景，并由所有基线复用，从而将比较
配对在相同的异步轨迹上。

当前四个机制基线为：

- `fgsr`：frontier 后拒绝旧 repair，并原子清理退休坐标状态；
- `unfenced`：接受迟到旧代 repair，并保留旧 share；
- `vssr`：把 recovery response 建模为持久的旧代 opening edge；
- `epoch`：直到全局 epoch 边界才清理旧状态。

首轮固定参数下，`fgsr` 与 `epoch` 的 violation rate 为 `0`，而 `unfenced` 与
`vssr` 为 `1`；在共享同一延迟/withholding 场景的配对实验中，前三者平均
finality time 约为 `20.6`，`epoch` 约为 `40`。该结果只验证模拟器
是否重现预期的机制分离，不构成 ACSS、通道或聚合加密的安全证明。后续应在
保持同一攻击接口的前提下，逐步替换抽象 capability ledger 为实际 ACSS 和
消息测量，以检验 19.31 的三个条件接口。

完整的可移植实验方案、开源基线地址、参数矩阵、指标和执行顺序见
`experiments/EXPERIMENT_PLAN.md`。其中 Buffalo 是必选主端到端比较，PPFA-BAA
在 artifact 可访问且成功复现后加入；Flower SecAgg+ 与 FLSim 是控制组，Catalyst
作为不含安全聚合的 Byzantine utility control；APSS、DyCAPS 和 NFSA 只用于组件/状态
成本对照，不与端到端 FL 准确率直接排名。

## 22. 论文结构建议

1. **Introduction：** 从“恢复击败擦除”的执行开始，建立 `CC != PF`。
2. **Model：** 完全异步、causal-generation-bounded mobile corruption、最终当前状态暴露和 aggregate-only leakage。
3. **Privacy Finality：** Robust-Hitting 与 retirement-liveness sandwich。
4. **Recovery Closure：** Repair-Closure、repair amplification 和 matching attacks。
5. **No-Resurrection：** Puncture-Recursion、Recovery-State Localization、Causal-Fence Necessity。
6. **Construction：** `Joint-AO^mob + RCL` conditional compiler、BF-RPTA、current-share-only repair。
7. **Lower Bounds：** 精确线性穿孔与 approximate frontier 空间下界。
8. **Dynamic Committees：** Project-Then-Handoff 与 Handoff-Closure Preservation。
9. **Evaluation：** 状态、通信、恢复延迟与异步竞争。
10. **Related Work：** 按“打开对象、腐化生命周期、恢复语义、退休后暴露”四维比较。

## 23. 引言式叙事草稿

Secure aggregation is commonly treated as complete once an authorized aggregate has been released. This view is adequate for one-shot executions, but it is incomplete for long-lived asynchronous services. Their decryption committees do not disappear after one aggregation: members crash, recover, refresh shares, migrate state, and are eventually replaced. An adversary may therefore collect old shares before retirement and obtain every member's current state afterwards. More subtly, a recovery protocol may legitimately reconstruct a share that the aggregation protocol had erased. No primitive is broken; privacy fails because recovery changes the effective access structure after the proof has stopped reasoning about it.

We call the missing property privacy finality. Consensus finality determines which aggregate is released. Privacy finality determines when every individual-opening capability for that aggregate has become permanently unreachable, including through future recovery and committee handoff. This distinction is particularly important in asynchronous systems: sessions overlap and finalize out of order, so forward-secure period updates cannot express the required selective retirement; delayed pre-retirement messages may arrive after finality; and waiting for every honest member contradicts asynchronous liveness.

We characterize privacy finality in two layers. Without recovery, a retirement set must be a robust hitting set of the decryption access structure. With recovery, this condition is insufficient: the closure of all retained capabilities under every legal recovery edge must still avoid every authorized decryption set. This recovery-closure view exposes a general composition failure. Ordinary VSS, proactive refresh, and dynamic handoff are designed to preserve a secret across failures. When wrapped around puncturable aggregation state, the same correctness property can resurrect a retired capability.

Based on this characterization, we formulate a recovery-closed lifecycle for aggregate-only threshold state. Every recovery contribution is bound to a monotone privacy frontier, stale recovery outputs cannot be installed, and retirement removes not only direct shares but all coordinate-local recovery state. The BF-RPTA construction is a conditional instance whose data-plane obligation is `Joint-AO^mob`; TACITA supplies only the static starting point for that lifting. Matching lower bounds explain the state/liveness tradeoff: exact share-local linear puncturing requires state linear in the number of independently retired labels, while one-sided approximate frontiers require `R log(1/epsilon)-O(R)` bits.

The resulting guarantee survives a threat model not captured by prior asynchronous aggregation protocols: the adversary may move across committee members for the lifetime of the service, retain every historical snapshot it obtains, trigger Byzantine recovery, and eventually expose all current committee states. Once a session becomes privacy-final, no future execution can recreate enough capability to open an individual contribution, while the same stable public infrastructure continues serving overlapping future sessions.

## 24. 摘要式叙事草稿

长期运行的异步安全聚合服务必须在节点故障后恢复密码学状态，但恢复机制可能重新生成已经擦除的历史解密份额。现有安全聚合通常在聚合值输出时结束安全分析，前向安全加密依赖有序时间世代，普通 VSS/DPSS 则以保持原秘密为正确性目标；它们都没有刻画并发无序会话在恢复、治愈和委员会换届后的不可逆隐私终结。

本文提出 **privacy finality**：一个会话不仅已经确定并输出唯一聚合，而且在所有未来合法恢复与状态暴露下，其单项解密能力都不可重新形成。我们首先证明，不考虑恢复时，privacy finality 等价于退休集合对解密访问结构的鲁棒横截条件；对 `q`-out-of-`n` 系统得到紧边界 `n-a+min(a,b)<q`。随后，我们将 share recovery 表示为 capability hypergraph，证明真正的安全条件是历史能力集合的恢复闭包不包含任何授权解密集合，并由此得到恢复门限降低有效隐私门限的 repair-amplification 结果。我们进一步证明，未受单调 frontier 支配的迟到恢复消息、持久未穿孔 backup，以及只删除 direct share 的 ordinary recovery wrapper 都可能复活已经终结的能力。

为实现 recovery-closed privacy finality，本文提出 `Joint-AO^mob + RCL` 的条件编译框架：数据面只打开短 mask key 的唯一聚合，长期状态层通过 coordinate-local deletion、current-share-only repair 和 stale-state rejection 保持退休吸收态。一个 BF-RPTA 实例以 `Theta(R log(1/epsilon))` 状态支持 `R` 次退休，对已退休会话提供确定性隐私，并以至多 `epsilon` 的概率拒绝未来会话；其具体数据面安全仍取决于 `Static-AO` 到 `Joint-AO^mob` 的提升。我们给出匹配的 one-sided approximate-membership 空间下界，以及精确线性 share-local 穿孔的 `Omega(M)` 功能维数下界。Project-Then-Handoff 暂作为同一闭包定理的后续扩展，而不是当前主构造的无条件结论。

## 25. 当前最关键的证明任务

本轮已将第一个协议级证明切口写入
`repair-closure-theorem-draft.md:721` 和 `repair-closure-theorem-draft.md:2004`：
Common-H 的 agreement/availability 现在有条件引理，state-complete resharing
也有独立的代数引理。这里的“完成”只指条件协议层形式化，不表示 APSS 或其他
现有实现已经满足这些接口。

下一阶段不继续扩张协议功能，只完成以下三个决定主线能否成立的任务：

1. **完成 FGSR 的 privacy 实例化。** 在 `Joint-AO^mob`、`L1--L3`、opaque adaptive repair 和 `PECC` 下，把抽象 edge set 实例化到 current-share-only repair，证明退休坐标删除全部 recovery-complete state 后 `Cl_rec(X) intersection C_dec = X intersection C_dec`。
2. **完成密码学接口审计。** 对一个 ACSS 构造分别证明 opaque delivery、helper equality proof simulation 和 PECC；不能把 APSS 的 static secrecy 定理直接当作长期安全性。
3. **完成数据面 lifting。** 证明 TACITA-style `Static-AO` 在辅助输入、并发 `R_eq`、partial decryption 和自适应状态暴露下能够提升为 `Joint-AO^mob`；若不能，保留独立 `Joint-AO^mob` 假设并将 BF-RPTA 定位为条件实例。

动态委员会、packed repair 和 exact puncture 都建立在这三个任务之后。它们不会替代基础闭环。

## 28. 本轮主线修正：选择性 Frontier-Gated Resharing

本轮把候选构造从“VSSR + ephemeral PKE”修正为 **Frontier-Gated Selective Resharing (FGSR)**。原因不是 VSSR 的验证性不足，而是其恢复代数和状态形状不适合长期 cure：`k` 个 contribution 重构 masked polynomial，未来 DPRF 暴露会产生 group-transcript amplification；恢复结果又丢失 recovery-polynomial components，不能作为下一次 helper state。

FGSR 的正向流程是在 live coordinate 上重分享同一 secret，使所有正确节点得到新的、可继续 repair 的 complete current share；在 retired coordinate 上由 authenticated frontier 同时关闭 generation、decryption 和 installation。DyCAPS 的 bivariate handoff 是最接近的技术基线，APSS 是擦除/刷新基线，Optimistic DPSS 是高效 handoff 基线，但没有一篇现成工作证明无序 `sid` retirement、future full-state exposure、迟到 transcript 和可重复 repair 的联合闭包安全。

新的最小参数目标为：

```text
n = 3f+2,
q_dec = q_rec = 2f+1,
retirement history budget b = f,
target-excluded correct responders = 2f+1.
```

这使论文叙事从“给已有 VSSR 增加删除”提升为：**把异步 proactive resharing 的正确性重新解释为一个带选择性隐私前沿的恢复闭包问题，并证明 target exclusion 决定最小冗余。**

One-shot share-to-share resharing 给出该参数点的最小正向见证：把缺份额 target 作为新状态接收者，其他正确旧节点通过共同 helper set 提供 `2f+1` 个可验证 resharing inputs，所有正确节点线性合成同一份 fresh sharing。该流程不复制 DyCAPS 的四阶段 handoff，而让 resharing 本身同时完成 repair 和 refresh。尚需完成的不是普通 resharing 正确性，而是三项本文特有的证明：迟到 private subshare transcript 的 frontier security、retired coordinate 的 closure，以及 repair 输出对下一次 repair 的 state completeness。

FGSR v0.1 进一步要求：`H` 必须来自 availability-certified ACS；每个 helper 必须证明新多项式的常数项等于其当前 share；所有 live 节点必须安装同一个 `F'`，不能只修复 target。实现上只保留 `Authorize -> Parallel Reshare -> Aggregate/Install/Erase` 三道门控，不复制 DyCAPS 的 bivariate zero-polynomial 和四阶段 handoff。朴素版本仍为每 coordinate `O(n^2)` 通信，packed/batched 优化留到安全主定理之后。

### 28.1 首个证明切口：Common-H Agreement 与 Availability

`n=3f+2` 只解决 target-exclusion 的数量问题，不自动解决 Byzantine helper
可用性。论文中的第一个正向证明必须把 `Common-H` 拆为两个引理：

**Agreement 引理。** 所有正确节点最终接受唯一的：

```text
(rid, ell, cfg, T_req, H)
```

其中 `H` 不包含 target，且每个 helper 的旧 share commitment、resharing
commitment 和实例状态都绑定同一上下文。该引理由 validated ACS 的一致性、
proposal binding 和 deterministic set encoding 提供。它排除“不同节点按本地
到达顺序选择不同 `H`”导致的两个 sharing polynomial。

**Availability 引理。** 对每个 `h in H`，证书不只是表示 helper 广播了
commitment，而必须表示其 VSS/AVSS 输入已经达到所有正确 receiver 可恢复的
完成状态。否则 Byzantine helper 可以先进入 `H`，再只向部分 receiver 发送
`f_h(j)`，使 target 永远无法安装 `F'(target)`。

在 target 正确但缺失旧 share、至多 `f` 个其他节点 withholding 时，target
排除后有：

```text
n - f - 1 = 2f+1
```

个正确旧节点。若这些节点的 AVSS instances 最终完成，ACS 可以从它们形成
`|H|=2f+1` 的 availability-certified 集合；这才推出 target-excluded
liveness。若底层 AVSS 只有 dealer agreement，没有 all-correct-receiver
availability，则不能直接作为 FGSR 的 `H` 证书，必须补可恢复性证明。

这一区分构成本文的第一个可检验边界：

```text
counting feasibility  !=  Byzantine availability
```

它也限制贡献表述：当前不能声称“任意现有 ACS + VSS 都实现 FGSR”。首个构造
应明确选择满足 all-correct-receiver completion 的异步 VSS/AVSS 接口，并把
`H` 的证书验证写入协议定义。

**候选协议 wrapper。** 令 `P^- = P \ {target}`，则候选者数为
`n'=3f+1`。每个 `h in P^-` 作为 AVSS dealer，receiver 集仍包含 target；
只有在自己的 AVSS instance 完成、且 `f_h(0)=z_h` equality proof 验证通过后，
`h` 才向 `P^-` 的 validated ACS 提交 descriptor。ACS 输出集合 `V` 满足
`|V|>=n'-f`，所有节点再按相同的 descriptor 排序确定：

```text
H = Canonical_{2f+1}(V),    |H|=2f+1.
```

`H` 中允许出现 Byzantine helper，但每个入选 descriptor 都必须携带 AVSS
completion certificate。故安全目标不是识别诚实身份，而是保证每个被选输入对
所有正确 receiver 最终可恢复。至多 `f` 个 Byzantine 节点时，`H` 至少包含
`f+1` 个 honest helper；target 不参与 ACS 提案，避免其缺失旧 share 阻塞集合
选择，但仍作为 AVSS receiver 收到所有选中 `f_h(target)`。

该 wrapper 的活性前提写成明确接口。可验证的最小 `AvailCert_h` 是 `P^-` 中
至少 `2f+1` 个节点对同一 AVSS instance 签署 `READY(rid,ell,h,C_h)`；每个
READY 只能在本地 deliver 认证点值后产生。证书至少含 `f+1` 个 honest READY。
结合 AVSS 的 agreement/propagation 语义：一个正确 receiver deliver 后，所有
正确 receiver 最终 deliver 同一值，target 即使不参与 ACS 提案也最终获得点值。

```text
AVSS-Complete(h) =>
  all correct receivers eventually obtain one authenticated point f_h(j)
  consistent with the committed f_h.
```

如果底层 primitive 只有“dealer agreement”而没有上述 receiver availability
或 propagation 性质，则 ACS 的 `H` 证书不足以支持 FGSR；这不是通过提高
`q_rec` 可以修复的缺口，必须换用更强的 VSS/RBC wrapper。

**首个密码学实例。** 为避免把旧 share `z_h` 写入公开 descriptor，第一版采用
Pedersen 风格的系数承诺。当前 `F` 的 commitment 给出 `F(h)` 的承诺 opening，
helper 对新多项式 `f_h` 的常数项另有 opening；helper 用零知识关系证明证明
两者承诺的消息相等，但不公开 `z_h`：

```text
Com_F(h) opens to z_h
Com_{f_h}(0) opens to the same z_h
```

`CurrentShareProof_h`、`EqualityProof_h` 和每个 receiver 点值的 VSS proof
共同构成 `ValidDesc_h`。这不是新的密码学原语，而是选择一个能直接表达
“两个承诺的消息相等”的现有 VSS 接口。KZG 可作为后续通信优化，但不能在没有
额外 zero-knowledge opening-equality 证明的情况下直接替代该接口。

### 28.2 证明顺序与失败判据

完成 `Common-H` 后，按以下顺序推进：

1. 证明 equality proof 确保 `f_h(0)=z_h=F(h)`，从而 `F'(0)=F(0)`；
2. 证明所有 live 节点安装同一个 state-complete `F'`，且下一次 repair 可
   直接把 `F'(j)` 作为常数项；
3. 在 typed capability closure 中证明 receiver 单点、归档密文和未来全状态
   暴露不能合成 retired coordinate 的旧 share；
4. 证明 retirement 支配 pending generation、解封和安装边，迟到 transcript
   只能被拒绝，不能形成新的恢复能力。

若第 3 步失败，结论应是“private subshare + future state exposure 不能提供
transcript finality”，而不是继续叠加前向安全加密。若第 1、2 步失败，则
One-Shot FGSR 只能作为反例或计数基线，不能进入主定理。

### 28.2.1 退休闭包的 edge 分类

对每个 FGSR edge，证明只允许以下归宿：

| edge | 退休前生成 | 退休后尝试 |
|---|---|---|
| `share -> helper polynomial` | 计入 archived/pending closure | generation gate 拒绝 |
| `polynomial -> encrypted subshare` | 进入 transcript simulator | 无有效 `ValidDesc` |
| `ciphertext + receiver key -> plaintext` | `A` 密钥擦除，`U` 状态入 residual closure | frontier/context 校验拒绝 |
| `subshares -> F'` | 形成对应 `rid` 的 pending/live output | stale output 不得安装 |
| `F' -> current state` | `install < retire` 先安装，随后 `A` 删除，`U` 保留 | instance order 拒绝 |

这一区分避免错误地把迟到消息“删除”。已生成消息仍属于攻击者视图；安全性
来自它只能落入历史、残留或可模拟 transcript，且不能再产生闭包之外的新能力。
若某条边无法归入上述集合，`Retirement-Closure` 不能成立。

### 28.3 单次 repair 的 transcript-hiding 引理

这里必须区分“退休证书形成”和“所有节点都已看到证书”。令 `A_ell` 为已经
确认 retirement 并擦除该 coordinate 状态的节点，`U_ell=P\A_ell` 为尚未确认
的残留节点。完全异步活性不允许要求所有节点先擦除；退休后的 `X_current`
可以包含 `U_ell` 的最新 `F'` 或 pending state，但这些状态必须进入
`Cl_rec`，不能被误删。首个紧参数要求：

```text
|A_ell| >= n-f = 2f+2,
|U_ell| <= f,
|B_ell| <= b=f,
|U_ell| + |B_ell| < q_rec=2f+1.
```

若所有节点都保留 `F'`，全体状态暴露当然能重构 `F'(0)=F(0)`；真正的安全
条件不是“退休后没有 `F'`”，而是 residual current state、历史暴露和迟到
transcript 的恢复闭包都不能形成授权集合。

在单个 repair instance 的保守版本中，`|B_ell|<=b=f`，并定义 `B_ell` 为在擦除前
读取该 coordinate 敏感状态的节点集合，并将所有 Byzantine 保留状态计入其中。
对未被 `B_ell` 完整暴露的 helper，
攻击者至多看到 `b` 个 receiver evaluations；因为：

```text
degree(f_h) = d = 2f,
number of exposed points <= b = f <= d,
```

fresh 高阶系数使这些点值在信息论上不揭示 `f_h(0)=z_h`。被完整腐化的 helper
最多贡献 `b` 个旧 direct shares，进入 `X_hist(B_ell)`，不能被计为新的 transcript
能力。对未暴露 receiver，归档 ciphertext 在 ephemeral secret 擦除后由
IND-CPA 模拟；对暴露 receiver，plaintext evaluations 已被 `B_ell` 计入历史
视图。Pedersen commitment 的 hiding 和 equality/VSS proof 的零知识性允许
模拟公开承诺与证明，而不需要知道未暴露的 `z_h`。

因此得到单次实例的条件结论：

```text
archived ciphertexts + post-retirement residual X_current
    -/-> a new direct-share capability outside residual closure
```

前提是 `A_ell` 节点删除 helper coefficients、receiver plaintext 和 ephemeral
keys；`U_ell` 的残留材料显式计入 closure；frontier 支配后不再产生新的
generation/extraction/install edge。该引理尚不等于长期多次 repair 组合定理；
跨实例的历史 `B_ell`、旧 commitment、frontier 和 concurrent retirement 仍需
按 typed capability closure 证明。

**多次 repair 组合条件。** 同一 coordinate 的实例必须由唯一 instance order
串行化；每轮使用独立 `rid`、高阶随机系数和 receiver ephemeral keys；整个
coordinate 生命周期累计读取节点集合仍满足 `|B_ell|<=b=f`。此时每轮最多给
攻击者 `b<=d` 个新 evaluation points，单次 hybrid 可按 instance order 归纳
组合。retirement 与最后一个 repair 的竞态只有两种合法结果：

```text
retire < install(rid)  => discard F' and all pending materials
install(rid) < retire  => install F', then atomically erase F'
```

以上是便于审计的 session-lifetime 保守版本；当前长期自适应模型由 28.16 的
causal generation interval 条件替代。两者都要求 `A_ell` 节点不再保留该 coordinate 状态；`U_ell` 的残留状态按
generation type 进入 closure。该组合结论依赖**累计**暴露上界、实例串行化和
`|U_ell|+|B_ell|<q_rec` 的基线计数；仅限制瞬时 Byzantine 数量，不能推出
长期 transcript finality。这个条件引理完成前，不把单次 simulator 宣称为完整
`PF_sid` 定理。

### 28.4 Retirement-Closure 条件定理（累计暴露的保守版本）

定义退休后的可见能力集合：

```text
X_pf(ell) = X_hist(B_ell)
             union X_current(U_ell)
             union ArchivedPreRetirement(ell).
```

其中 `A_ell` 已确认擦除，`U_ell=P\A_ell` 是异步残留集合。若同时满足：

1. `|A_ell|>=n-f` 且 `|U_ell|+|B_ell|<q_rec`；
2. retirement frontier 支配后禁止 generation、extraction、installation；
3. `A_ell` 原子删除 direct/pending/ephemeral state，`U_ell` 状态完整进入
   closure；
4. 所有退休前 transcript 满足多实例 transcript-hiding；
5. 动态 handoff 只读取 projected live coordinates；

则：

```text
Cl_FGSR(X_pf(ell)) ∩ Gamma_dec^cap(ell) = emptyset.
```

证明按 frontier/instance 顺序归纳：退休后没有新的合法生成边；迟到消息只
属于已归档 transcript，由 transcript-hiding 条件不能扩张 residual closure；
`U_ell` 与 `B_ell` 的 direct capabilities 不足以形成 `q_rec` 授权集合；
handoff 不复制 retired coordinate。

该定理仍是条件结果。`Cross-Generation Affine Coupling` 可关闭线性
share-to-share 层的多代组合；当前最关键的剩余任务是证明 `E_ell` 覆盖全部
可见状态，并排除 aggregate-opening capability 的额外非线性恢复边。

### 28.5 理论核心：One-Hidden-Helper Residual Cut

单次 transition 的关键不是泛泛地说“有 fresh randomness”，而是一个紧的
残余切分。令：

```text
E_ell = U_ell union B_ell,
|E_ell| <= 2f,
|H| = q_rec = 2f+1,
degree(f_h) = 2f.
```

必存在 `h* in H\E_ell`。该 helper 的多项式系数已被擦除；攻击者至多观察
`2f` 个 `f_{h*}` evaluations，而多项式 degree 也是 `2f`。fresh 高阶系数
使这些点值不能推出常数项 `f_{h*}(0)=F(h*)`。因此单次 transition 至多暴露
`2f` 个旧 `F(h)` direct shares，缺失的第 `2f+1` 个点阻止旧 sharing 重构。

这给出 `n=3f+2,q_rec=2f+1` 的真正理论含义：参数同时提供 target-excluded
liveness 和一个未暴露 helper 的信息论 residual cut。它不是简单把 BFT 委员会
从 `3f+1` 加一。

但该引理只覆盖单次 sharing transition。若多个 generation 的隐藏 helper 通过
旧 commitment、pending transcript 或 residual state 形成跨代恢复边，单次
`One-Hidden-Helper` 不能自动组合。需要保持整条 resharing 链视图不变的跨代
耦合变换；该变换现在作为下一条代数引理写出。

**信息论证明工具。** 对暴露位置集合 `E` 定义：

```text
L_E(X) = product_{j in E}(X-j) / product_{j in E}(-j).
```

`L_E(0)=1` 且 `degree(L_E)=|E|<=2f=d`。任意与观察值一致的 helper polynomial
`f` 都可变为 `f_delta=f+delta L_E`：所有 `E` 上的 evaluations 不变，而
`f_delta(0)=f(0)+delta`。因此未暴露 helper 的常数项在信息论上不可由 transcript
推出。该工具要求 `E` 覆盖所有可见 evaluations，并排除 helper 已泄漏完整系数。

对整条链 `F^0 -> ... -> F^R`，令每轮 helper set 为 `H_r`，对任意 `Delta`
同步定义：

```text
F^r_Delta(X) = F^r(X) + Delta*L_E(X)
f^r_{h,Delta}(X) = f^r_h(X) + Delta*L_E(h)*L_E(X).
```

因为 `L_E` 在 `E` 上为零、在零点为一，所有暴露的 direct share 和 subshare
point 不变；因为 `|H_r|=d+1` 且 `degree(L_E)<=d`，
`sum_h lambda_{r,h}L_E(h)=1`，故每个 `F^r_Delta` 仍满足原 resharing
递归，而每代秘密统一平移 `Delta`。若 `h in E`，扰动系数为零；其余 helper
属于已擦除且未暴露状态。Pedersen hiding、关系证明 zero knowledge 和对未暴露
receiver 的 IND-CPA 共同完成视图模拟。

这关闭了线性 share-to-share 层的跨代组合缺口；剩余任务转为证明 `E` 覆盖
全部可见状态，以及 aggregate-opening capability 没有额外的非线性恢复边。

### 28.6 多坐标 aggregate-opening 边界

BF-RPTA 若用多个 coordinate 编码同一个 mask key，不能默认认为各坐标的
门限安全可直接相乘。必须审计潜在边：

```text
partial shares at ell_1
  + partial shares at ell_2
  + cross-coordinate consistency proof
  -> aggregate-opening capability.
```

首版约束每个 coordinate 使用独立 degree-`d` sharing randomness；跨坐标证明只
证明 ciphertext/mask 的同明文关系，采用 zero knowledge，不提供任何 share
opening。于是 `Gamma_dec^cap` 按 coordinate 分解，跨坐标只留下公开元数据和
证明边。若复用高阶系数或公开跨坐标线性关系，多个坐标的 partial shares 可能
形成额外方程，降低有效门限；此类 packed 方案暂不进入主定理。

这一步将最终组合证明拆成明确接口：`Cross-Generation Affine Coupling`
负责单坐标多代线性 sharing，`Cross-Coordinate Nonlinear Isolation` 负责
证明 Static-AO 的 aggregate-opening capability 不被跨坐标组合扩张。

### 28.7 Cross-Coordinate Affine Coupling：同一秘密关系下的全局模拟自由度

上一节只规定了不能出现哪些跨坐标边；还需要一个正向代数引理说明：在独立
坐标 sharing 的首版构造中，跨坐标一致性本身不会消灭单坐标的隐藏自由度。
设坐标集合为 `I`。对每个 `ell in I`，第 `r` 代 sharing polynomial 为
`F^r_ell`，degree 为 `d_ell`，所有未来可见的 receiver positions 与残留节点
状态包含在 `E_ell` 中，且：

```text
|E_ell| <= d_ell,
|H_{r,ell}| = d_ell+1,
f^r_{ell,h}(0) = F^r_ell(h).
```

定义每个坐标自己的 vanishing polynomial：

```text
L_ell(X) = product_{j in E_ell}(X-j) / product_{j in E_ell}(-j).
```

对所有坐标和所有 generation 使用同一个未知 `Delta`，但使用坐标自己的
`L_ell`：

```text
F^r_{ell,Delta}(X) = F^r_ell(X) + Delta*L_ell(X),

f^r_{ell,h,Delta}(X) = f^r_{ell,h}(X)
                         + Delta*L_ell(h)*L_ell(X).
```

逐坐标应用 Lagrange 插值可得：

1. `E_ell` 上的 direct shares 与 subshare points 不变；
2. `f^r_{ell,h,Delta}(0)=F^r_{ell,Delta}(h)`，所以 helper equality relation
   不变；
3. `sum_h lambda_{r,ell,h}L_ell(h)=L_ell(0)=1`，所以每一代 resharing 递归
   仍然成立；
4. 若所有坐标原本编码同一个 mask key，则每个坐标的秘密都变为
   `k+Delta`，跨坐标相等关系保持不变。

这给出一个重要但有边界的结论：独立坐标的同明文 zero-knowledge consistency
proof 不会自动把不同坐标的 partial shares 变成新的 opening。对未暴露 helper，
每个坐标仍保留同一个 `Delta` 的视图模拟自由度；对已暴露位置，所有观察值仍
完全一致。Pedersen hiding 与关系证明的 zero knowledge 负责公开 transcript，
而不是负责证明聚合开启安全。

这里的“同一个 `Delta`”是跨坐标耦合的关键：若每个坐标使用互不相关的平移，
则可能破坏“编码同一 mask key”的关系；若共享高阶系数或公开跨坐标 opening，
则会增加新的线性方程，改变隐藏 helper 的维数。于是，独立高阶随机性、同一
秘密关系和零知识一致性证明构成候选定理的明确假设，而不是实现细节。

该引理仍不是 `Static-AO` 的完整 aggregate-only 安全证明。特别是，不能把
同一 mask key 的多坐标 ciphertext 逐坐标替换：替换一个 coordinate 而保持
其它坐标不变，会被跨坐标 consistency proof 检测。正式组合还需证明一个联合
向量游戏：

```text
joint vector Static-AO challenge preserves the same aggregate,
and its consistency proof remains simulatable;
cross-coordinate consistency proof -/-> aggregate-opening capability.
```

因此本工作的正向叙事不是“用前向安全加密保护多个坐标”，而是：**当长期
异步 repair 同时作用于多坐标时，什么条件能够保持一个跨 generation、跨
coordinate 且不泄漏授权开启能力的全局模拟不变量。** 研究对象是该条件的
必要性、充分性及其与访问结构的关系；协议构造只作为检验该理论的见证。

### 28.8 学术命题与证伪标准

当前主定理应写成一个条件性组合命题，而不是一组工程功能的罗列。候选形式是：

```text
Common-H availability
+ Cross-Generation/Cross-Coordinate Affine Coupling
+ frontier-closed recovery closure
+ joint-vector Static-AO security
------------------------------------------------
=> Cl_rec(X_pf) ∩ Gamma_dec^cap = emptyset.
```

其中每一项对应一个可独立证伪的数学命题。若耦合变换无法覆盖某类可见状态，
则得到 residual-cut 失效边界；若联合向量 `Static-AO` 游戏无法容纳跨坐标
一致性约束，则得到数据面不可组合的反例；若动态 handoff 引入 retired
coordinate 的合法恢复边，则得到 `Handoff-Closure` 反例。只有这三类边界均
被闭合，才可将 FGSR 与 BF-RPTA 写成完整安全定理。

### 28.9 联合向量 `Static-AO` 组合引理（已被 28.11 修正）

跨坐标缺口可以在不发明新的加密原语的情况下转化为一个明确的组合引理。
设 `I` 是坐标集合。每个 coordinate `ell` 使用独立的 `Static-AO_ell` 参数和
加密随机性；客户端 `u` 在所有坐标中加密同一个短 key `k_u`，并生成一个证明
`pi_u`，声明这些 ciphertext 具有同一明文。挑战者选择两组 key vectors
`K_0=(k_{u,0})` 与 `K_1=(k_{u,1})`，满足：

```text
sum_u w_u*k_{u,0} = sum_u w_u*k_{u,1}.
```

每个坐标都公开其 ciphertext、aggregate ciphertext、可验证部分解密和唯一
聚合输出；证明转录绑定所有坐标，但只声明跨坐标明文相等。该游戏只泄漏
授权的加权和，不泄漏 individual key。

组合引理需要三个明确假设：

1. 每个 `Static-AO_ell` 满足选择性 aggregate-only 安全，并允许挑战者在同一
   权重向量下替换 `K_0` 与 `K_1`；
2. 一致性证明使用双模式 CRS：真实模式具有 soundness/knowledge soundness，
   模拟模式允许对任意跨坐标 ciphertext 向量生成可接受的模拟证明，且两种
   CRS 与相应证明转录计算不可区分；
3. 坐标之间不共享高阶 share 系数、解密秘密或公开线性 opening，RCL 的状态
   视图与挑战 key vectors 独立。

**混合证明。** 从世界 0 的真实执行开始。第一步将一致性证明的 CRS 和所有
真实证明替换为模拟 CRS 与模拟证明；由于世界 0 中语句为真，这一步由双模式
零知识性成立。随后依次遍历 `ell in I`，在第 `ell` 个 hybrid 中只将该坐标的
`K_0` ciphertext/aggregate/decryption transcript 换成 `K_1` 版本。此时其它
坐标仍可能包含 `K_0`，跨坐标语句在代数上不一定为真，但模拟 CRS 允许生成
相应证明；而该坐标的两个 key vectors 具有相同授权加权和，所以可以直接调用
`Static-AO_ell` 的 aggregate-only 安全。遍历结束后得到世界 1 的全部
`K_1` ciphertext，最后将模拟 CRS/证明换回真实模式，端点语句重新为真。

因此有候选界：

```text
Adv_Joint-AO
  <= 2*Adv_DualMode-ZK
     + sum_{ell in I} Adv_Static-AO_ell
     + negl(lambda).
```

这一步解决了原来的 hybrid 组织缺口：逐坐标替换的问题由模拟证明吸收，而
每个坐标的加密转录仍由已有 `Static-AO` 安全性负责。它尚未解决证明系统的
实例化问题。普通只支持真实语句模拟的 NIZK 不足以支撑中间 hybrid；论文必须
明确采用具有模拟 CRS 和多定理模拟能力的证明系统，并单独证明真实模式下的
soundness。

由此，`Cross-Coordinate Affine Coupling` 负责长期 sharing state 的联合模拟，
上述 `Joint-AO` 引理负责客户端 ciphertext 数据面的联合模拟。两者结合后，
才可以从坐标内 `Gamma_dec^cap` 闭包推出 BF-RPTA 的 aggregate-only privacy；
跨坐标证明本身不再作为新的解密 capability 来源。

### 28.10 TACITA 兼容性审计与 go/no-go 判据（已被 28.11 修正）

TACITA 的 modified STE 扩展 CPA 已经覆盖以下坐标级事实：挑战者给出两组
等长消息集合，要求两组消息之和相同；挑战者返回诚实 ciphertext，攻击者可以
加入受腐化控制的 ciphertext；随后公开聚合 ciphertext 和聚合 partial
decryption。该定义正好支持每个 coordinate 的 `Static-AO_ell`，但其腐化集合
在挑战消息前固定，并没有定义多个独立 STE 实例之间的同一客户端 key 关系。

因此现有材料的结论应分成两层：

```text
TACITA extended CPA
    => coordinate-level Static-AO_ell,

TACITA extended CPA
  + dual-mode, simulation-sound equality proof
  + independent coordinate parameters
    => Joint-AO, by Section 28.9.
```

TACITA 原文不能直接提供第二行中的跨坐标证明模拟，也不能把其静态腐化安全
自动提升为 RCL 所需的长期移动腐化安全。因而当前的 go/no-go 判据是：

1. 若采用标准双模式 simulation-sound NIZK，并能把每个 ciphertext 的明文与
   客户端 commitment 绑定，则 `Joint-AO` 可以作为条件组合定理继续证明；
2. 若只保留 TACITA 原有证明系统，则必须把 `Joint-AO` 作为独立数据面假设，
   不能把它写成 TACITA 的直接推论；
3. 若不接受双模式 NIZK 或联合安全假设，应改变数据面，令各 coordinate 使用
   独立 key 并重新设计 mask 聚合关系，而不是继续沿用同一 key 的证明路线。

这使论文的主张保持准确：本文新增的是长期 `Repair-Closure` 与联合组合定理，
TACITA 只承担静态坐标级 aggregate-only 基线。

**候选实例化。** 客户端为短 key `k_u` 生成隐藏 commitment
`Com_u=Com(k_u;r_u)`。对每个 coordinate `ell`，客户端发送 TACITA-style
`Static-AO_ell` ciphertext `ct_{u,ell}`，并附带一个 simulation-extractable
NIZK，证明存在 `(k_u,r_u,rho_{u,ell})` 使：

```text
Com_u = Com(k_u;r_u)
and ct_{u,ell} = Enc_ell(k_u;rho_{u,ell}).
```

也可以把所有 `ell in I_sid` 的等式合并为一个 batched relation。真实 CRS 下，
proof of knowledge 保证每个坐标确实使用同一 `k_u`；模拟 CRS 下，`SimProve`
可以处理 hybrid 中尚未满足该关系的 ciphertext 向量。已有阈值加密工作给出了
simulation-extractable NIZK 的标准接口和 `SimProve` 算法，因此这里需要的是
关系实例化与性能分析，而不是新的证明范式。

该实例化使 `Joint-AO` 的证明前提具体化为 commitment hiding、NIZK 的双模式
模拟与 simulation soundness，以及 TACITA 每个坐标的 extended CPA。仍需检查
TACITA ciphertext 的随机性和随机预言机调用能否有效写入上述 NP relation；若
该关系依赖不可模拟的公开 opening，则回退到独立 `Joint-AO` 假设。

### 28.60 实验之后的决定性工作：从接口到构造

实验基线已经转移到其他设备。当前论文的研究问题保持不变：异步联邦学习中的安全聚合，在长期移动自适应腐化、迟到消息和份额恢复同时存在时，何时真正获得隐私终结。现阶段不应把工作推进成更多 FL 系统比较；决定性任务是把 `Adaptive-Opaque-Repair` 落成一个可证明的固定委员会构造。

首先冻结理想功能 `F_PF-SA` 和事件序列：聚合集合证书 `CC_sid`、聚合开放、退休屏障 `PF_sid`、局部擦除、未来腐化和恢复。安全定义必须分别记录公开 transcript、发送时已经暴露的历史能力和擦除后的状态。这样可以严格说明：共识终结只固定输出，隐私终结还必须阻断 `Cl_rec`。

具体构造优先采用私有、可验证、无公开 scalar 的 current-share repair。接收者使用公开承诺检查恢复份额，无效响应局部丢弃；公开层只发布 receipt 和 availability metadata。构造必须同时证明异步 withholding 下的 Common-H、`PECC`、原子擦除、跨坐标能力隔离以及退休后的 `AOR-5`。只有这条路线无法兼顾活性和验证时，才进入 metadata-only `ZK-Invalidity`；本地文献审计已经表明普通 NIZK、VSSR recovery verification 和 Janus complaint 都不提供该接口。

该阶段的核心交付物是一张 typed-edge ledger，而不是工程模块表。每条恢复、使用、部分解密和投诉边都要回答四个问题：它何时产生，谁能看到，何时擦除，退休标签是否支配它。随后按 `AOR -> L1--L3 -> Joint-AO^mob -> Recovery-Closure` 的依赖顺序完成证明。

论文的 go/no-go 标准也在这里确定：如果 repair 仍必须公开 scalar 或保留可由全局恢复权组合出的 `sid`-local 状态，则原样 Janus/hbACSS 不能作为具体长期安全实例；正文应保留抽象 FGSR 主定理、Robust-Hitting 刻画、no-resurrection 必要性和条件数据面定理，不把条件假设包装成完成构造。只有在 current-share repair 闭合后，动态委员会才作为 Recovery-Closure 的推论加入。

这一步完成后再写摘要、相关工作和最终实验叙事。当前主线的学术价值来自一个清晰的边界：**privacy finality 是访问结构上的 robust hitting，加上异步状态机中的 absorbing retirement；它不是 forward secrecy、普通 VSS 或一次输出证书的别名。**

## 26. 主要原文依据

- LightBEAT：静态腐化、公开 HIDP punctured key、threshold-ElGamal committee state 和逐条 `Combine`，见 `LightBEAT_Scalable_Epochless_Batched_Threshold_Encryption_via_Hierarchical_Identity-Based_Puncturing.pdf_by_PaddleOCR-VL-1.6.md:381`、`:437`、`:598`、`:620`、`:722`。
- VSSR：recovery polynomial、DPRF、恢复查询安全边界和非 proactive 定位，见 `Efficient Verifiable Secret Sharing with.pdf_by_PaddleOCR-VL-1.6.md:122`、`:132`、`:230`、`:331`、`:588`。
- Silent Setup STE：forward security 与 post-compromise security 的周期更新/换键边界，见 `Threshold Encryption with Silent Setup.pdf_by_PaddleOCR-VL-1.6.md:731`。
- BEAST-MEV：动态委员会只作为组合 proactive secret sharing 的预期扩展，见 `usenixsecurity25-bormet.pdf_by_PaddleOCR-VL-1.6.md:374`。
- Batched threshold encryption with epoch IDs and proactive churn discussion，见 `usenixsecurity25-choudhuri.pdf_by_PaddleOCR-VL-1.6.md:249`、`:373`。
- Speeding Dumbo：ACS 的 agreement、validity、termination 语义及 `n-f` 输出下界，见 `/home/yzc/flagg/speeding_dumbo.txt:317`、`:326`、`:331`。
- 详细定理推导、近邻矩阵和前期审计见 `long-lived-adaptive-corruption-audit.md`。

## 27. 最终记忆点

这篇工作的最强记忆点不是“我们做了一个更复杂的安全聚合协议”，而是：

> **Privacy is not final when a share is erased. It is final only when every legal way of recovering that share has also been retired.**

在长期异步系统中，恢复不是隐私证明之外的运维细节，而是访问结构的一部分。本文用 Robust-Hitting 刻画谁必须退休，用 Repair-Closure 刻画什么能力还能被恢复，用 causal frontier 保证退休在异步执行中不可回滚，再用 recoverable puncture 构造把这一理论变成可运行协议。

### 28.11 联合证明缺口的正式修正（supersedes 28.9--28.10）

上一版使用 `Com_u=Com(k_u;r_u)`，但从 `K_0` 切换到 `K_1` 时还必须切换
commitment；原 hybrid 因此遗漏了一个 endpoint。首版构造删除这个不必要的对象，
直接对每个客户端使用一个 batched NP relation：

```text
x_u = (ctx_sid, u, {ek_ell, tag_sid,ell, w_u, ct_u,ell}_{ell in I_sid})

R_eq(x_u; k_u, {rho_u,ell}_{ell in I_sid}) iff
  for every ell in I_sid,
    ct_u,ell = Enc_ell(ek_ell, tag_sid,ell, w_u*k_u; rho_u,ell).
```

`ctx_sid` 绑定会话、身份、坐标集合、权重编码和门限参数；proof 只证明所有坐标
使用同一个 `k_u`，不公开 `k_u` 或 opening。零权重允许存在，只要 `w_u*k_u`
在 TACITA 的加法明文域中可计算；整数权重必须先固定无歧义的域编码。

**条件联合定理。** 令两组 honest key vectors `K_0,K_1` 满足：

```text
sum_u w_u*k_u,0 = sum_u w_u*k_u,1.
```

假设每个 `Static-AO_ell` 支持由归约者独立生成其它坐标、公开参数和证明
transcript 的 auxiliary-input embedding；`R_eq` 使用双模式 simulation-sound
NIZK，模拟 CRS 可对任意 statement 生成可验证的 `SimProve`，且真实/模拟 CRS
与任意多项式数量的 transcript 不可区分；坐标之间不共享高阶系数、解密秘密或
公开跨坐标线性 opening，证明 transcript 不产生解密 capability。则：

```text
Adv_Joint-AO
  <= 2*Adv_DualMode-ZK
     + sum_{ell in I_sid} Adv_Static-AO_ell^aux
     + negl(lambda).
```

证明先把真实 CRS/proofs 替换为模拟 CRS/`SimProve`；此时 statement 真实成立。
再按固定坐标顺序替换第 `ell` 个坐标的 honest ciphertext、aggregate ciphertext、
partial decryption 和输出。令 `m_u,b=w_u*k_u,b` 后，每一步都是 TACITA 的等长、
等和 challenge；其它坐标由归约者生成，模拟 proof 吸收暂时不满足的 `R_eq`。
完成所有替换后 statement 再次真实成立，恢复真实 CRS/proofs。该证明把原来
“逐坐标替换会被 consistency proof 检测”的缺口收敛为两个明确接口：
`DualMode-ZK` 和 `Static-AO^aux`。

`aux` 是归约接口，不是普通 IND-CPA 自动提供的性质。若 TACITA 的正式游戏不能
容纳该嵌入，`Joint-AO` 必须保留为独立联合数据面假设，不能写成 TACITA 的直接
推论。

**固定权重审计。** TACITA 的等和条件直接覆盖 `m_u=w_u*k_u`，不要求权重非零
或可逆；它要求权重在挑战前固定、参与集合固定且所有坐标采用相同编码。若权重
在异步执行后确定，或 adversary 能在看到 ciphertext 后调整权重，当前归约失效。
相关阈值加密工作给出了 `Setup(crs,td)`、`Prove`、`Verify`、`SimProve` 接口，
但没有自动给出本文的 dual-mode、任意 statement simulation 和跨坐标组合性质。

### 28.12 `Static-AO^aux` 的可归约 lifting lemma

`aux` 可以进一步从“额外假设”收窄为一个可检查的归约接口。固定坐标 `ell` 和
某个 hybrid，构造 TACITA extended-CPA adversary `B_ell`：

1. `B_ell` 把联合游戏中的固定腐化集合和参与集合提交给 TACITA challenge，并
   将 challenge 坐标的 `ek_ell`、公开参数交给联合 distinguisher；
2. `B_ell` 自行生成所有 `j != ell` 的独立 TACITA 参数、密文、aggregate ciphertext
   和 partial-decryption transcript，并按照 hybrid 选择 `K_0` 或 `K_1`；
3. 联合 distinguisher 给出的两组 key vectors 被映射为 TACITA message sets
   `S_b={Encode_T(w_u*k_u,b)}`。由于加权和相同，`S_0` 与 `S_1` 满足 TACITA 的
   等和条件；
4. TACITA 返回第 `ell` 个坐标的 challenge ciphertext、聚合 ciphertext 和
   partial decryption 后，`B_ell` 将它们嵌入联合视图，并在模拟 CRS 下对所有
   honest `R_eq` statement 运行 `SimProve`。

若腐化 client 的 ciphertext 需要发送给 TACITA challenge，`B_ell` 原样转发其
message/randomness，并保留 TACITA 对 malformed ciphertext 的检查；其它坐标的
腐化 transcript 由 `B_ell` 本地生成。于是 `B_ell` 的视图正是相邻两个 hybrid，
并得到：

```text
Adv[H_{ell-1}, H_ell] <= Adv_Static-AO_ell + negl(lambda).
```

该 lifting 成立需要四个可验证条件：坐标参数和随机性相互独立；其它坐标的完整
transcript 可由归约者在知道 `K_0,K_1` 时本地采样；TACITA challenge 允许其标准
的腐化 ciphertext extension；`R_eq` 的模拟器可在看到 challenge ciphertext 后
生成 proof。因而对当前 BF-RPTA 设计，`Static-AO^aux` 可以作为归约义务而不是
额外密码学假设。若共享 TACITA hidden setup、共享 RO 状态、跨坐标公开线性
opening，或 partial-decryption transcript 依赖其它坐标的秘密，该 lifting 不成立，
必须回退到独立 `Joint-AO` 假设。

**TACITA 方程落地。** 对坐标 `ell`，令 `ek_ell=(C_ell,Z_ell)`，并把 TACITA
的公开矩阵和向量记为 `A_ell(ek_ell,tag_sid,ell,t)` 与 `b_ell`。若客户端随机
取 `sd_u,ell`，令 `s_u,ell=RO(ctx_sid||ell||sd_u,ell)`，则 `R_eq` 可展开为：

```text
rho_u,ell = sd_u,ell
ct_u,ell = (tag_sid,ell,
            s_u,ell^T * A_ell,
            s_u,ell^T * b_ell + Encode_T(w_u*k_u)).
```

其中 `Encode_T` 是 TACITA 明文到其群/加法明文域的固定编码。TACITA 的聚合满足：

```text
Aggr_ell({ct_u,ell}_u)
  = (tag_sid,ell, sum_u ct2_u,ell, sum_u ct3_u,ell),
```

并要求同一坐标的 tag 一致；`PartDec` 只对聚合 ciphertext 的 ciphertext-specific
component 计算 partial decryption。于是 `R_eq` 的电路可以检查 `sd` 的随机预言
机派生、上述线性方程和 `Encode_T(w_u*k_u)`，但它必须在 ROM 中允许 oracle query，
或把相应 oracle values 纳入可验证 statement。若选用的 NIZK 不能表达该 RO-aware
relation，则当前只能保留独立 `Joint-AO` 假设，不能声称由 TACITA 直接实例化。

### 28.13 `SE-NIZK` compatibility gate

当前文献只能支持证明系统接口的候选来源，不能直接关闭本工作的实例化义务。
要让 28.11 的逐坐标 hybrid 成为正式归约，证明系统必须同时满足：

1. `Setup_real` 与 `Setup_sim` 的 CRS 分布计算不可区分；
2. `SimProve(td,x)` 对任意公开 statement `x` 都输出可验证 proof，包括 hybrid
   中暂时不属于 `R_eq` 语言的 statement；
3. 模拟器支持多项式数量的并发、多定理 proof transcript，并对腐化客户端的
   未查询 statement 保持 simulation soundness/extractability；
4. TACITA 的随机预言机调用与 NIZK 的证明查询具有明确的 oracle 组合规则，不能
   默认把两个 simulator 可独立编程。

Choudhuri 等的工作明确给出 `Setup(crs,td)`、`Prove`、`Verify`、`SimProve` 和
weak simulation-extractability 接口，并在 programmable ROM 下使用它们；但其
可见定义主要说明真实 statement 的零知识性，不能仅凭接口名称推出本文所需的
arbitrary-statement simulation。若能补齐上述四项，28.11 的 `Joint-AO` 归约
继续成立；若只能得到普通 NIZK，则 `Joint-AO` 保留为独立数据面假设。

### 28.14 证明缺口的收敛：主定理与实例化定理分层

这里的缺口不是 `Repair-Closure` 或 `RCL` 的缺口，而是把一个跨坐标的公开
consistency proof 拆成逐坐标 TACITA hybrid 时产生的组合缺口。若在第 `ell` 个
坐标替换 ciphertext，混合 transcript 中同一客户端的其他坐标仍绑定旧 key，
则原 `R_eq` statement 可能暂时为假；普通 NIZK 的真实语句模拟无法支撑这一步。

本文采用两层定理结构：

1. **主定理层。** `BF-RPTA` 的 privacy-finality 定理直接假设联合的
   `Joint-AO` 数据面。该游戏一次性挑战完整的跨坐标 ciphertext、aggregate
   ciphertext、partial-decryption transcript 和公开 consistency transcript，
   并只要求两组 key vectors 的加权总和相同。主定理不调用逐坐标 NIZK
   simulator，也不把 TACITA 的静态坐标游戏强行提升为联合游戏。
2. **实例化层。** 只有在选定的 NIZK 满足 `DM-SE-NIZK^{RO,eq}` 时，才使用
   28.11--28.13 的逐坐标 lifting，得到：

   ```text
   Adv_Joint-AO
     <= 2*Adv_DM-SE-NIZK^{RO,eq}
        + sum_ell Adv_Static-AO_ell^aux
        + negl(lambda).
   ```

   `DM-SE-NIZK^{RO,eq}` 要求 simulated CRS 与真实 CRS 不可区分，且 simulated
   `SimProve` 对任意公开 `R_eq` statement 都可验证，包括中间 hybrid 的假
   statement；extractor 和 soundness 还要在 TACITA 与 NIZK 共享的 programmable
   RO 下成立。Choudhuri 等的 weak simulation-extractability 接口只能作为候选
   依据，不能直接填充这一接口。

   首版论文的安全结论因此写成：

   ```text
   Privacy-Finality(BF-RPTA)
     <= Joint-AO + RCL-Sim/AO + Robust-Hitting + protocol correctness.
   ```

   若后续给出 `DM-SE-NIZK^{RO,eq}` 的标准假设实例化，则再把 `Joint-AO` 替换
   为上面的 TACITA 归约。若实例化无法关闭，论文仍保留完整的长期异步理论
   结果；未完成的是静态数据面的具体组合优化，而不是主线安全定义或
   `Repair-Closure` 证明。

**研究决策。** 暂不把跨坐标 consistency proof 作为首版主构造的必要组件；它
只能作为可选的恶意客户端格式验证层。主隐私定理使用完整联合向量游戏，从源头
移除“逐坐标 hybrid 必须模拟假 statement”的隐藏前提，同时保留同一 mask key
的功能叙事。

### 28.15 `Joint-AO` 正式游戏与主组合定理

为避免把跨坐标一致性证明拆坏，主线使用一次性联合游戏。固定会话 `sid` 的
客户端集合 `U`、静态腐化集合 `C`、诚实集合 `H=U-C`、坐标集合 `I_sid`、
权重和预挑战上下文参数。挑战者生成每个坐标的独立数据面参数，敌手提交两组
诚实客户端 key vectors `K_0,K_1`，满足：

```text
sum_{u in H} w_u*k_{u,0} = sum_{u in H} w_u*k_{u,1}.
```

世界 `b` 中每个坐标加密的明文是：

```text
m_{u,ell,b} = Encode_T(w_u*k_{u,b}).
```

挑战者一次性生成所有坐标 ciphertext、跨坐标 consistency transcript、aggregate
ciphertext、合法 partial decryption、`H_ct/H_out` 等挑战相关摘要、唯一
aggregate-opening certificate 和共同聚合输出；敌手控制的固定 transcript 在两个
世界中相同。敌手看到完整公共
transcript 和辅助输入，但看不到任何单项 opening。于是：

```text
Adv_Joint-AO(A)
  = |Pr[b'=0 in Exp_Joint-AO(0)]
      - Pr[b'=1 in Exp_Joint-AO(1)]|.
```

该定义的关键是：consistency proof 被作为联合挑战 transcript 的一部分，而不是
在每个坐标 hybrid 中单独模拟。它要求的只是完整向量两端具有相同授权聚合，
因此比逐坐标 `Static-AO` 更强，但正好匹配 BF-RPTA 的实际公开视图。

主组合定理写成：

```text
Adv_Privacy-Finality(A)
  <= Adv_RCL-Sim/AO(A)
     + Adv_Joint-AO(A')
     + Adv_Context/Correctness(A'')
     + negl(lambda).
```

证明顺序为：先用 `RCL-Sim/AO` 替换所有恢复、handoff 和迟到 transcript；再由
`CapSafe` 保证残余状态闭包不含任何单项解密授权集合；随后调用一次 `Joint-AO`
切换完整跨坐标数据面；最后由 `CC_sid` 唯一绑定和 key-homomorphic mask 正确性
保证两个世界的聚合输出及控制决策一致。该证明不做 coordinate-local hybrid，
所以主定理不依赖对假 `R_eq` statement 的 NIZK 模拟。

这一步正式闭合了“长期状态安全如何接入聚合开放安全”的证明接口：长期贡献
由 `RCL + Robust-Hitting` 给出，数据面贡献由 `Joint-AO` 给出。TACITA 的逐坐标
归约仍是后续条件实例化，不再承担主组合证明的隐含前提。

这里还必须显式加入 **state-layer/data-plane noninterference**：`RCL-Sim/AO` 不仅
不能恢复完整的单项解密 capability，恢复、handoff、当前状态暴露和 stale-state
检查的输出也必须在两个 challenge worlds 中同分布；任何依赖 challenge ciphertext
的 partial decryption 或 proof 都必须被纳入 `Joint-AO` 的 `DataView_b`。因此主视图
分解为：

```text
View_b = (DataView_b, StateView, PublicContext_pre),
```

其中 `DataView_b` 由 `Joint-AO` 覆盖，`StateView` 不依赖 `b`。`CapSafe` 只排除
完整未授权 opening，不能自动排除较小的残余泄漏；两者是独立证明义务。BF-RPTA
的首版分层满足该条件，因为 RCL 只修复委员会 threshold decryption shares，
客户端 mask key 只出现在数据面 ciphertext 和共同 aggregate opening 中。

更精确地，`Puncture/Recover/CheckInstall` 只能读取预挑战上下文、frontier/generation
元数据和当前委员会份额；如果某个状态转换读取 `H_ct`、`H_out` 或 partial
decryption，它的输出必须随同这些对象进入 `DataView_b`。在此条件下，BF-RPTA 的
`RCL-Sim/AO` 可由单坐标 transcript-hiding、状态承诺绑定和退休闭包推出，而不会
把挑战相关摘要偷偷留在 `StateView` 中。

### 28.16 长期自适应腐化：实例局部预算

此前的全生命周期 `|B_ell|<=f` 是保守条件。更准确的放宽是按因果状态屏障定义
generation interval：从安装 `F^r` 到下一次接受安装或 retirement barrier 之间，
`B_{ell,r}` 收集全部当前份额、helper polynomial、receiver plaintext 和临时密钥
暴露，而不是只统计 repair 消息期间。若没有下一次屏障，区间延伸到 retirement。
令 `B_{ell,ret}` 为最终区间暴露集合，要求：

```text
|B_{ell,r}| <= f,
|U_ell| <= f,
|U_ell union B_{ell,ret}| <= 2f < q_rec.
```

不同 interval 可以暴露不同节点；长期敌手可以跨生命周期移动到所有身份，但每个
屏障间隔使用 fresh helper-polynomial coefficients 和 receiver ephemeral keys，
完成后擦除这些材料，并由 `(rid,generation,frontier)` 拒绝旧 share 或 pending
transcript 重新作为新 helper 输入。

在单次 transcript-hiding 成立、且每代 current sharing 只从上一代认证 current
state 产生时，对 `R` 个因果有序 repair instances 可以按前缀视图进行自适应
hybrid：

```text
Adv_Transcript-Hiding^R
  <= sum_{r=1}^R Adv_Sim_r
     + Adv_Generation-Binding
     + R*negl(lambda).
```

这使“长期自适应腐化”成为可证明的主线条件：安全性依赖每个因果屏障间隔的局部
相关状态预算、fresh resharing 和不可回滚的代际隔离，而不是一个永远固定的全局
腐化集合。屏障是必要条件：若旧 share 仍能跨代参与 repair、plaintext helper
contribution 未擦除，或敌手能在下一次屏障前读完全部当前份额，则必须退回累计
`B_ell` 上界。

### 28.17 代际屏障必要性

这不是把瞬时腐化预算换一个名字。若某个 coordinate 的同一代 sharing 在两个
状态变化屏障之间持续有效，异步调度器可以延迟所有 fresh resharing 和擦除消息；
敌手保持至多 `f` 个主动腐化，却依次读取 `q_dec` 个不同节点的同代份额，随后
释放节点并继续轮换。保存的 `q_dec` 个份额即可重构旧解密 capability。于是：

```text
instantaneous corruption <= f
does not imply privacy
unless a causal barrier performs fresh install + old-edge invalidation + erase.
```

因此，长期安全的真正假设是 generation interval 内的暴露预算，而不是无限速
continuous-mobile。该屏障是每个 coordinate 的局部状态事件，不是全局同步 epoch；
它必须同时阻止旧 share 参与未来 recovery、安装和解密边，并在下一次暴露区间前
完成状态擦除。

### 28.18 Generation-local 到 Retirement-Closure 的正式推论

28.16 的局部预算必须真正进入闭包定理，而不能只作为模型描述。对 coordinate
`ell` 的 generation intervals `r=0,...,R`，其中 `R` 是 retirement 前的最终区间，
为所有能力和 transcript 保留 generation tag，定义：

```text
X_pf^loc(ell) = union_{r=0}^R X_hist^r(B_{ell,r})
                 union X_current(U_ell)
                 union ArchivedPreRetirement^tagged(ell).
```

若满足：

1. 每个 `|B_{ell,r}|<=f`，`|U_ell|<=f`，且最终区间满足
   `|U_ell union B_{ell,R}|<=2f<q_rec`；
2. 每次接受安装都在完整前缀视图条件下使用 fresh helper-polynomial
   coefficients 和 receiver ephemeral keys；
3. `Cross-Generation Affine Coupling` 保持暴露点与 equality relation 不变，并在
   generation 间传播共同 affine shift；它是 distributional coupling，不是合法协议
   transition。`(rid,generation,frontier)` 使旧代 share/transcript 不能直接成为新代输入；
4. 完成实例擦除 helper coefficients、plaintext evaluations 和 ephemeral keys，
   19.5 的单次 simulator 覆盖全部 typed pre-retirement transcript；
5. retirement frontier 关闭 `ell` 的 generation、extraction、installation 和
   decryption edges，stale output 被拒绝，handoff 只投影 live coordinates；
6. 跨 coordinate consistency 和 aggregate-opening transcript 不产生超出
   generation-tagged current-share closure 的新 capability。

则有：

```text
Cl_FGSR(X_pf^loc(ell)) intersection Gamma_dec^cap(ell) = emptyset.
```

证明采用按 interval 的前缀 hybrid。第 `r` 代的 `B_{ell,r}` 由此前视图决定，
`L_{B_{ell,r}}` 的 affine shift 保持该代所有暴露点和 equality relation，并让 coupled
secret 在可接受 affine family 内移动；generation tag
阻止不同代的点值直接合并。退休最终代不再使用单独的 `B_{ell,R}` 计数，而使用
`L_{U_ell union B_{ell,R}}`；集合大小至多 `2f`，而共同 helper 集大小为
`q_rec=2f+1`，所以至少保留一个终端 hidden helper。接受安装是唯一允许的跨代边，
它生成 fresh、带标签的 current shares；擦除、frontier dominance 和 stale rejection
移除其余边。条件 6 排除跨 coordinate 或 aggregate-opening 的非线性恢复边，于是闭包不能
第一次推进到授权解密集合。

该推论把长期自适应腐化从“每代 fresh randomness”提升为可检查的组合定理。它仍
不把 19.5 的单次 simulator 或跨坐标非线性隔离从普通 VSS 正确性中自动推出；这两项
是 FGSR 具体构造必须分别完成的证明义务。

### 28.19 One-step simulator 的对象级证明义务

为避免“private subshare 在擦除后自然安全”的跳步，首个 FGSR 实例必须给出
对象级 simulator。固定 repair instance rid、coordinate ell 和 generation r；
simulator 只接收 pre-challenge context、公开承诺、Common-H 证书和 residual
typed state，不接收未暴露的旧 current share。

| 对象 | 模拟方式 | 归属 |
|---|---|---|
| Authorize 的 rid/coordinate/frontier 元数据 | 重放认证公开上下文 | StateView |
| ValidDesc、AvailCert、Common-H | 重放证书，或只模拟 ZK proof | StateView |
| helper/current-share commitment、equality/VSS proof | 未暴露 helper 使用 hiding/ZK 模拟；已暴露对象进入历史视图 | StateView 或历史 closure |
| receiver ephemeral public key | 独立于客户端 key 诚实采样 | StateView |
| 已擦除 receiver 的 subshare ciphertext | 对应 ephemeral secret 擦除后用 PKE IND-CPA 替换为随机密文 | simulated transcript |
| 被暴露 receiver 的 plaintext evaluation | 直接纳入对应 generation 的历史暴露 | X_hist^r |
| 退休后仍保留的 plaintext/pending state | 完整纳入 U_ell residual state | X_current |
| F'、install certificate、erase event | 只重放 generation/frontier 绑定的状态转换 | StateView 或 X_current |
| challenge-dependent partial decryption、H_ct/H_out、aggregate certificate | 不进入 StateView，一次性纳入 Joint-AO | DataView |
| 其他依赖 individual key 或 individual plaintext 的对象 | 计入 uncovered edge，停止安全声称 | 未建模能力 |

Hybrid 顺序为：先替换已擦除接收者的密文，再模拟未暴露 helper 的承诺与证明，
然后用 L_{B_{ell,r}} 完成 live generation 的条件分布，用
L_{U_ell union B_{ell,ret}} 完成终端退休代，最后对所有 challenge-dependent
数据面对象调用 Joint-AO。自适应的 B_{ell,r} 由完整前缀视图决定；它不能被事后
改写为一个静态集合。

因此单步误差至少显式分解为 PKE IND-CPA、proof simulation、affine coupling、
state commitment、generation binding、uncovered edge 和 negligible 项。只要
某个迟到 ciphertext、pending plaintext 或状态摘要没有落入这张表，28.18 的
Retirement-Closure 推论仍然只是条件结果。

### 28.20 具体密码学实例与 Uncovered-Edge 归零

首个 proof-friendly 实例采用 Pedersen 系数承诺。对 degree-d sharing F，
helper h 生成：

```text
f_h(X) = z_h + sum_{k=1}^d a_h,k X^k,
z_h = F(h).
```

helper 对 f_h 的系数发布 Pedersen commitments，并用零知识 equality proof
证明 f_h 的常数项与 F 在 h 处的 evaluation 是同一消息，不公开 z_h。由
Common-H 的确定性 Lagrange 系数，所有正确节点安装同一 F'，并有
F'(0)=F(0)。KZG 不进入首个安全实例，除非另行补齐 zero-knowledge
opening-equality 接口。

AVSS 需要满足一个明确的 opaque delivery 接口：公开 transcript 只包含
commitment、validity proof、READY/availability certificate 和元数据；
f_h(j) 通过绑定 rid、coordinate、generation、helper、receiver 和 frontier
的认证私密通道交付。一个正确 receiver 成功 deliver 后，所有正确 receiver
最终获得同一点值。若 AVSS 公开点值或可重构的系数信息，则不能令
Adv_Uncovered-Edge 为零。

对象级归属如下：

| 对象 | 归属 |
|---|---|
| authorization、Common-H、AvailCert、frontier/generation metadata | StateView |
| Pedersen commitments、equality/VSS/AVSS proofs | StateView 或历史 closure |
| 已擦除 receiver 的 subshare ciphertext | PKE IND-CPA 模拟 transcript |
| 被暴露 receiver 的 plaintext | 对应 B_{ell,r} 的历史 closure |
| U_ell 保留的 plaintext/pending state | residual X_current |
| F'、install、erase、stale rejection | generation/frontier 绑定的状态层 |
| partial decryption、H_ct/H_out、aggregate certificate | DataView，由 Joint-AO 覆盖 |

因此，simulator 可以先重放公开上下文，再模拟未暴露 helper 的 commitment
和 proof，替换已擦除接收者的密文，用 L_{B_{ell,r}} 或终端
L_{U_ell union B_{ell,ret}} 完成条件点值，最后一次性调用 Joint-AO 生成
challenge-dependent 数据面对象。所有 U_ell 状态必须原样保留，不能借助
异步擦除假设删除。

在 opaque AVSS、equality proof、PKE、原子擦除、generation binding 和
state commitment 成立时，得到：

```text
Adv_Uncovered-Edge = 0.
```

这一步把“使用某种 VSS/PKE”变成可审计的密码学实例化，而不是把普通 VSS
correctness 当作 transcript finality。剩余主缺口收敛为：证明所选 AVSS
确实满足 opaque delivery，以及证明跨 coordinate aggregate-opening 不
产生新的 capability。

### 28.21 现有 AVSS/PVSS 的实例化可行性裁决

现有文献不能直接提供 28.20 所需的完整实例，但可以拆出三个层次：

| 文献接口 | 可复用部分 | 必须补齐的部分 |
|---|---|---|
| APSS/ACSS | 私有点值交付、所有正确 receiver 最终获得一致 share、异步可用性 | 静态 Byzantine 假设、全局 refresh 语义、target-excluded current-share repair、frontier retirement |
| DyCAPS/DPSS | 异步移动委员会、forward-secure private channel、擦除纪律 | epoch/handoff 结构、bivariate state、不是 per-coordinate 无序 retirement |
| adaptive PVSS | 自适应腐化下的 commitment、公开加密 share transcript、解密正确性证明 | 原文明确不假设 secure erasure；未来暴露 receiver secret 可解封历史 ciphertext |

因此首个构造不把 APSS、DyCAPS 或 adaptive PVSS 作为完整黑盒。我们定义
AVSS-opaque：公开 transcript 只能暴露承诺、有效性证明、availability
certificate 和元数据；点值只能经 receiver-specific ephemeral channel 交付，
并在 commit/cancel/install 后擦除对应 plaintext 和 secret key。APSS/ACSS
提供 availability 的候选基线；Pedersen commitment 和常数项 equality proof
提供隐藏及 secret preservation 接口；receiver-ephemeral PKE 提供退休后
transcript replacement。

该拆分还限制公开 commitment 的用法：Feldman 或 Pedersen commitment 只能作为
验证元数据，不能被任何后续 recovery 或 decryption 算法当作 scalar share。
否则 group-valued commitment 会形成新的 typed capability edge，必须重新计算
当前实例化结论是条件性的：若选定的异步 VSS 不能证明 AVSS-opaque，首版就
不能把它写成 BF-RPTA 的长期安全实例；应保留 RCL-Sim/AO 的抽象定理，而不是
用 adaptive PVSS 的 one-shot security 代替 opaque delivery 和擦除证明。

### 28.22 Cross-Coordinate Nonlinear Isolation：能力类型保持引理

本节关闭 28.18 和 28.21 中最后一个未覆盖边。核心不是假设“不同坐标的随机性
足够新”，而是限制协议中哪些对象可以作为解密能力的输入。对每个坐标 `ell`、
generation `r` 和会话 `sid`，给每个秘密承载对象附加不可伪造的类型标签：

```text
Share(ell,r,i)       -- receiver i 的标量 share 或 evaluation
RepairShare(ell,r,h,i)
AggregateKey(sid)    -- 只由 Joint-AO 的唯一授权输出产生
ProofMeta(sid,ell)   -- 只用于验证公开 consistency statement
```

协议的秘密操作满足三条语法约束：

1. `Interpolate_{ell,r}` 和 `PartDec_{ell,r}` 只接受同一 `(sid,ell,r)` 的
   正确类型对象。`Repair_{ell,r -> r+1}` 只接受坐标 `ell` 的第 `r` 代源
   对象，并输出带 `r+1` 标签的新 `Share`；该转换不接受其他坐标的秘密输入。
2. 跨坐标对象只进入 `R_eq` 的公开 statement 和零知识 proof。验证结果是
   `ProofMeta(sid,ell-set)`，不含 scalar opening、receiver evaluation、
   decryption share，也不能作为任何秘密操作的 witness 输入。
3. 坐标参数、share 随机性和 receiver ephemeral key 相互独立；不存在跨坐标
   公开线性 opening、共享高阶系数或依赖其他坐标秘密的 partial decryption。
4. proof verification 只能影响公开 acceptance metadata，或影响已在固定
   `Joint-AO` context 中声明的数据面选择；它不能根据隐藏 witness 选择单项
   ciphertext、partial decryption 或 recovery branch。否则该选择必须作为新的
   `DataView` edge 建模。

把满足这三条约束的对象和操作闭包记为 `TypedCl(T)`。定义 `Cap_ell(T)` 为只用
坐标 `ell` 的 `Share`、`RepairShare`、认证状态和公开元数据得到的标量解密
能力，定义 `Cap_AO(T)` 为 `Joint-AO` 唯一允许的 aggregate-only 输出。

**能力类型保持引理。** 若跨坐标 proof 满足多定理零知识性，验证算法只读取
公开 statement，且上述三条语法约束成立，则对任意完整 transcript/state view
`T`：

```text
Cap(T) subseteq (union_ell Cap_ell(T) union Cap_AO(T)).
```

更具体地，任何由 `TypedCl(T)` 产生的 individual-key opening capability，都
可以正规化为一条只包含单一 coordinate `ell` 的推导；跨坐标 proof、proof
verification result 和 coordinate metadata 在该推导中只能作为公共条件，不能
提供新的秘密方程。因而，如果对每个 `ell` 都有：

```text
Cl_rec(T) intersection Cap_ell(T) = emptyset
```

且 `Cap_AO(T)` 只输出授权聚合，则：

```text
Cl_rec(T) intersection Gamma_dec^cap = emptyset.
```

**证明。** 对产生 capability 的最短操作推导按末步归纳。末步若是 `Interpolate`、
`Repair` 或 `PartDec`，由类型转换规则，其全部秘密输入具有相同的 coordinate；
`Repair` 只发生 `r -> r+1` 的显式代际转换。归纳假设消去其中的跨坐标公共对象后，得到 `Cap_ell(T)` 中的
能力。末步若是跨坐标 proof verification，它的输出类型为 `ProofMeta`，按约束
2 不能进入秘密操作，因此不能成为 individual-key capability 的末步。若它控制
公开 acceptance 或已声明的数据面选择，该影响已经由公共 context 或 `Cap_AO`
覆盖；约束 4 排除其他通向秘密操作的路径。末步若是 `Aggregate` 或唯一授权输出，只能落入 `Cap_AO(T)`；其泄漏由 `Joint-AO`
定义覆盖。其他公开元数据不承载秘密值，不能改变上述类型闭包。于是每条推导均
落入右侧集合，得到第一式；结合 `CapSafe` 与 aggregate-only 输出定义，得到
第二式。

这里的“非线性隔离”不是普通 NIZK 的自动性质。它要求构造者证明实现没有隐藏
的类型转换，例如把两个坐标的 partial decryption 相乘、把 commitment 当作
scalar share，或让 proof verification 结果参与后续 key recovery。若任一转换
存在，就产生一条新的 `Gamma_dec^cap` 边，不能令 `Adv_Uncovered-Edge=0`，也
不能使用本引理。

该引理与 28.7 的区分是必要的：`Cross-Coordinate Affine Coupling` 只说明
多坐标 sharing 的联合条件分布仍有 affine completion；本引理说明数据结构和
操作闭包不会因跨坐标组合而扩大能力集合。前者是分布耦合，后者是能力非干扰。
二者共同把 28.18 的条件 6 具体化为可审计的语法接口，而不是把“独立坐标”
当作完整安全证明。

### 28.23 对 `Adv_Uncovered-Edge` 的收敛

在 28.20 的 AVSS-opaque、Pedersen/equality proof、generation binding、原子
擦除和本节能力类型保持接口均成立时，所有秘密承载对象只有三种归属：

```text
historical/current closure  -- generation-tagged single-coordinate state
DataView                    -- Joint-AO covered aggregate transcript
public metadata             -- challenge-independent StateView
```

因此不存在第四类可由跨坐标组合产生的 individual-key 对象，得到：

```text
Adv_Uncovered-Edge = 0.
```

这个结论只对首版的独立坐标构造成立。若未来为了压缩通信而引入 packed
coordinates、共享高阶系数或跨坐标 partial decryption，必须重新定义
`TypedCl` 并重新计算 `Gamma_dec^cap`；不能把本引理作为优化后的黑盒安全性。

### 28.24 `AVSS-opaque` 的文献接口审计与 go/no-go

`AVSS-opaque` 是本文为证明服务定义的接口，不是“使用 AVSS”即可自动获得的
性质。它至少包含五项：

```text
(OD1) 公开消息不含标量点值、evaluation 或可重构系数；
(OD2) 点值通过绑定 receiver 的认证私密通道交付；
(OD3) barrier 后擦除 receiver plaintext 与 ephemeral decryption state；
(OD4) recovery response 不产生新的公开 scalar opening edge；
(OD5) validity/availability 最终保证所有正确 receiver 得到一致点值。
```

本地 APSS 文献可以作为 (OD2) 和 (OD5) 的候选来源。其 commitment revelation
公开的是 `g^{p(i)}` 及 DLEq proof，而不是标量 `p(i)`，所以在离散对数假设下
可能满足 (OD1) 的 scalar-free 部分。但 APSS 的 secrecy 针对静态腐化集合，且
排除了诚实节点已经开始 reconstruction 的执行；它研究的是全局 refresh，不是
target-excluded selective repair 和 per-`sid` retirement。因此不能把 APSS 的
agreement、availability 或 secure-erasure 讨论直接升级为 `RCL-Sim/AO`。

VSSR 更直接地揭示了边界：其 recovery contribution 包含被 masking 的原始
share 和 DPRF contribution，恢复者重构多项式后再扣除 masking value。该接口
适合恢复缺失 share，却正好新增一条 recovery edge；其 secrecy 也不覆盖
reconstruction 已开始的状态。若在 retirement 后直接调用 VSSR，(OD4) 失效，
除非将 recovery contribution 重新绑定到 frontier 并证明它不会形成公开标量
opening。

DyCAPS 证明异步协议中可以同时使用私密通道、移动腐化预算和显式擦除，但其安全
性依赖高门限 handoff 状态及特定四阶段流程，不能作为本文 per-coordinate、
unordered retirement 的黑盒。本文只借鉴其模型证据，不复制其 handoff 结构。

因此首版实例化采用明确的 go/no-go 判据：只有当候选 ACSS/AVSS 对公开 transcript、
腐化 oracle、reconstruction 行为和擦除时序共同证明 (OD1)--(OD5) 时，才能把它
写成 `AVSS-opaque` 实例。只要恢复消息含标量 share，或未来状态暴露能够解开归档
点值，该候选就保留在抽象定理之外，并计入 `Adv_Uncovered-Edge`；普通 AVSS
 agreement/availability 不足以关闭该缺口。

### 28.25 从 APSS/ACSS 到 `AVSS-opaque` 的条件转换命题

APSS 最适合复用的部分是 ACSS 式的完整点值交付，而不是完整的全局 proactive
refresh。设 `C` 是为 helper polynomial `f_h` 提供交付的 ACSS 层，要求：

```text
(PC1) 标量 evaluation f_h(j) 只经 receiver 的私密通道交付；
(PC2) 公开 transcript 只含绑定承诺、有效性元数据和 availability 证据，
      不含标量 evaluation 或可标量重构的系数；
(PC3) validity/availability 最终保证所有正确 receiver 得到同一个承诺点值；
(PC4) receiver 能验证自己的点值，而无需打开其他 receiver 的点值。
```

定义 `Eph(C)`：`f_h(j)` 始终只保留在 receiver-specific 私密通道中。receiver
用公开承诺验证点值后，只发布包含 `(rid,ell,generation,h,j,frontier)` 和承诺
标识符的认证 `READY` receipt，不发布点值。receiver 在 commit、cancel 或
retirement 时擦除明文和 channel endpoint state，helper 在实例完成后擦除多项式
系数；frontier 之后不接受 recovery response。

**条件转换命题。** 若 `C` 满足 (PC1)--(PC4)，私密通道在规定擦除后能抵抗
未来 endpoint 暴露，且 `READY` receipt 经过认证并绑定 frontier，则 `Eph(C)`
满足 (OD1)--(OD5)。

证明按接口逐项对应：由 (PC2) 以及 `READY` 只含元数据得到 (OD1)；(PC1) 给出
(OD2)，(PC3) 给出 (OD5)。endpoint 与 buffer 擦除给出 (OD3)：barrier 之后，
腐化 oracle 没有可恢复点值的通道状态。由于 barrier 后没有 recovery response，
且每个 receipt 都绑定 frontier，不会产生新的公开 scalar opening edge，得到
(OD4)。认证和标签检查保证迟到 receipt 不能把点值安装到另一代。

首个具体实例化路线因此不再需要公开密文或 `EncEq`：复用 APSS 底层 ACSS 的
交付 API，关闭公开标量/evaluation revelation，只公开承诺元数据和 `READY`
receipt。这消除了 false-statement simulation 的额外 NIZK 缺口。若未来采用公开
relay 的加密点值，则必须另行提供 simulation-sound 或 dual-mode proof 将密文
绑定到承诺；该变体不进入首个定理。当前剩余义务收敛为：

1. 证明该 ACSS 的公开 transcript 满足 (PC2)；
2. 证明私密通道及腐化 oracle 可见的每个 buffered endpoint 满足擦除后的保密性；
3. 证明 receipt 与 availability certificate 足以支撑 Common-H。

APSS 的全局 refresh 定理、静态腐化安全游戏和 VSSR recovery procedure 不进入
该转换命题。三项义务完成后，`Eph(C)` 才能进入 FGSR 的具体安全定理；否则仍只
能使用抽象 `AVSS-opaque` 条件结果。

### 28.26 信道保密与前向安全的严格区分

需要把 28.25 使用的信道假设单独命名。令 `View_ch(tau)` 包含 barrier 时刻的
在途消息、receiver channel buffer、明文和本地密钥状态。若 receiver 在 `tau`
之前未被腐化并完成规定擦除，而敌手在 `tau` 之后腐化 receiver 仍无法区分其
交付标量，则称该信道满足 **post-erasure confidentiality (PECC)**。这是“信道
加端点状态转移”的性质，不是某个加密算法单独的性质。

普通认证私密通道只保证双方诚实时的传输期保密；它不自动保护未来腐化时仍在
缓冲区中的迟到消息或明文。前向安全加密能保护长期密钥更新后留下的历史密文，
但不能自动擦除 receiver 已保存的明文、待处理密文或临时私钥。因此：

```text
forward-secure channel + 不擦除端点状态       -> 不足；
端点擦除 + 保留可由未来密钥解开的密文         -> 不足；
PECC + 原子端点擦除                            -> 足以支撑 OD3。
```

首版 `Eph(C)` 直接假设 PECC，并让点值不进入公共 transcript。若信道或 buffer
会向敌手暴露密文，则可用 receiver-ephemeral encryption 实现 PECC，但临时私钥
和明文仍必须属于同一个原子擦除事件。这一分层避免把前向安全加密误写成退休
隐私终结本身。

**信道失败引理。** 若 barrier 后仍有可解密的在途密文，或腐化 oracle 可见的
buffer 仍保留交付标量，则敌手可在 barrier 后立即腐化该 receiver 并恢复标量，
同时保持瞬时腐化数不变。因此 (OD3) 与 `RCL-Sim/AO` 会独立于 sharing 或聚合
加密原语而失败。

### 28.27 APSS/ACSS 的逐项接口裁决

APSS 原文需要区分底层 ACSS sharing API 与其后续的 public commitment revelation。
底层 ACSS 让正确 receiver 得到标量 share 和 Feldman commitment；`GenZeroPoly`
还会公开 evaluation 的群编码和 DLEq proof。对 FGSR 的裁决如下：

| 条件 | APSS/ACSS 证据 | `Eph(C)` 中的结论 |
|---|---|---|
| `PC1` | pairwise private authenticated channel，receiver 本地得到标量点值 | 可复用，但需加入临时 endpoint 保护 |
| `PC2` | 公开 Feldman 系数承诺；`GenZeroPoly` 另有公开 evaluation revelation | 有条件可复用：只取 ACSS，关闭公开 evaluation revelation，承诺只能作验证元数据 |
| `PC3` | ACSS completeness 保证所有正确 receiver 最终持有同一承诺点值 | 可复用 |
| `PC4` | receiver 可用公开承诺验证自己的点值 | 可复用 |
| 长期自适应隐私 | APSS 使用 static corruption game，并排除 reconstruction 已开始的执行 | 不能直接继承为 FGSR 定理 |

因此，具体候选不是原样 APSS，而是：复用 APSS 风格的 ACSS 传输，关闭公开
evaluation revelation，将其包在 `Eph(C)` 中，并且每次只服务一个带 frontier
标签的 helper polynomial。群值承诺只能作为验证对象，`g^{f_h(j)}` 不能被当作
scalar recovery share。只有在实现和证明均排除其他公开 evaluation encoding，且
腐化 oracle 覆盖 channel buffer 与 endpoint state 时，该候选才通过接口审计。

这也固定 APSS 在论文中的角色：它提供可用性和 receiver-local verification 的
候选底座，`Eph(C)` 提供 `RCL-Sim/AO` 所需的 transcript 与擦除接口；代际局部
自适应组合、退休闭包和跨坐标隔离仍是独立定理，不从 APSS 的 static secrecy
引理中继承。

### 28.28 BF-RPTA 的首个完整条件实例化定理

前面的接口裁决允许我们把“抽象 FGSR 定理”和“具体密码学实现”连接起来，
但仍不能声称 APSS 原文已经给出本文的长期安全性。令 `FGSR-Eph(C)` 在每个
带 frontier 的 helper 实例中使用 APSS 风格的 ACSS 层 `C`、只含元数据的
`READY` receipt，以及 BF-RPTA 的状态转换规则。假设：

1. 对每个被接受的 descriptor，`Common-H` 完备且可用；其输出、插值集合和
   Lagrange 系数由 pre-challenge context 与认证 frontier 唯一决定。
2. `C` 满足 (PC1)--(PC4)，第 `r` 代 opaque delivery 的误差为
   `Adv_ACSS-opaque^r`。
3. helper equality proof 将 `f_h(0)` 绑定到 `F^r(h)`，具有可靠性和模拟器，
   其区分误差为 `Adv_Eq-Simulation^r`；该 proof 只验证 helper 关系，不公开
   evaluation。
4. 私密通道及腐化 oracle 可见的全部 channel buffer 满足 `PECC`，误差为
   `Adv_PECC^r`；明文、临时密钥、helper 系数和 pending endpoint state 在规定
   barrier 上原子擦除。
5. 每个安装的 share 与 receipt 都绑定
   `(sid,ell,generation,frontier)`；迟到 transcript 不能跨代安装或重新打开已
   退休实例，失败代价记为 `Adv_Generation-Binding`。
6. proof metadata 满足 28.22 的 proof-noninterference，且满足其中的类型能力
   隔离：跨坐标操作只能产生 `ProofMeta`，或产生 `Joint-AO^mob` context 已声明
   的数据面对象。
7. 完整数据面在自适应 prefix context 下满足 `Joint-AO^mob`。state layer、
   affine coupling、上下文或正确性失败分别由
   `Adv_State-Commitment`、`Adv_Affine-Coupling` 和
   `Adv_Context/Correctness` 界定。

**定理（条件 BF-RPTA 实例化）。** 对任意因果 generation-bounded mobile
敌手，以及多项式数量 `R` 的 helper generations，有：

```text
Adv_Privacy-Finality(FGSR-Eph(C))
  <= Adv_Joint-AO^mob
     + Adv_Affine-Coupling
     + Adv_State-Commitment
     + Adv_Generation-Binding
     + Adv_Context/Correctness
     + sum_{r=1}^R (
         Adv_ACSS-opaque^r
         + Adv_Eq-Simulation^r
         + Adv_PECC^r
       )
     + R*negl(lambda).
```

**证明思路。** 对每个因果 generation interval 应用 28.18 的
Retirement-Closure 推论。28.19 的 one-step simulator 将 ACSS transcript、
equality proof、receipt 和 endpoint exposure 替换为 challenge-independent
state view，三项逐代接口误差界定这些替换。代际绑定阻止迟到 transcript 跨越
安装或退休屏障；原子擦除与 `PECC` 消除屏障之后 receiver 本地的点值能力；
`Common-H` 与类型能力隔离则阻止 repair 和跨坐标控制流生成新的 scalar
opening edge。剩余的 accepted data-plane objects 由 `Joint-AO^mob` 一次性联合挑战，
终次退休关系由 affine coupling 处理。对 `R` 代进行 hybrid，得到上式中的逐代
误差和可忽略项。

这个定理的条件密码学义务恰好收敛为三项：opaque ACSS delivery、helper proof
simulation 和 post-erasure channel confidentiality。它不调用 APSS 的 global
refresh 定理、static corruption game 或 reconstruction secrecy claim。因此本文
下一步的具体工作是为一个 ACSS 构造证明这三个接口；在完成前，28.28 是从抽象
FGSR 到候选实现的严格桥梁，而不是“APSS 原样已经实现长期 privacy finality”
的结论。

### 28.29 本轮 ACSS 接口审计结论

本地 APSS 转写表明，APSS 的底层 ACSS 可以作为 `FGSR-Eph(C)` 的候选传输层，
但不能作为本文长期安全性的现成证明。可复用的是：私密 scalar delivery、
receiver-local commitment verification，以及在有效实例完成后向正确 receiver
传播一致 share 的可用性结构。必须关闭 APSS 后续 `GenZeroPoly` 的 public
evaluation revelation，因为 FGSR 的公共 transcript 只能包含 commitment metadata、
availability evidence 和 frontier-bound receipt。

仍未由 APSS 提供的三项义务是：

1. helper 的 `f_h(0)=F^r(h)` 两承诺消息相等性证明及其模拟；
2. 含 channel buffer 和 endpoint state 的 post-erasure confidentiality；
3. 从静态、单次 ACSS 安全到 causal-generation-bounded mobile adversary 下的多代组合。

因此论文中的准确表述是“APSS-style ACSS transport + FGSR privacy wrapper”，而
不是“APSS 实现了 FGSR”。这一区分已成为后续密码学实例化的 go/no-go 条件：
只要公开 transcript 含有 scalar evaluation，或擦除后 endpoint 仍可被腐化读取，
当前条件隐私定理就不能直接使用。

### 28.31 三项密码学接口的安全游戏

为避免把接口名称当作安全证明，定理稿 `repair-closure-theorem-draft.md:2238`
现在分别定义了三个游戏：

1. `Adv_ACSS-opaque`：比较真实 ACSS transcript 与不掌握未暴露 receiver
   evaluation 的 simulator transcript，并单独要求公开消息不含标量点值、每个
   正确 receiver 最终得到一致点值。
2. `Adv_Eq-Simulation`：比较真实 helper equality proof 与不掌握
   `z_h=F^r(h)` 的并发模拟 transcript；soundness 和 proof-noninterference
   单独计项，不能由普通零知识术语自动推出。
3. `Adv_PECC`：允许敌手在擦除屏障后暴露在途消息、buffer 和剩余 endpoint
   state，仍要求无法区分两个等长交付标量；helper 自身在 barrier 前持有的
   `z_h/f_h` 不由 PECC 隐藏，而由 generation exposure budget 和 helper-state
   erase 条件处理。

三项优势在每个 generation 的 transcript-hiding hybrid 中相加，再与
`State-Commitment`、`Generation-Binding`、`Affine-Coupling` 和
`Uncovered-Edge` 一起进入主定理。这样主线的下一步变成可审计的具体任务：为
一个 ACSS/承诺/信道组合分别给出三个游戏的 reduction，而不是继续笼统地寻找
“更强的前向安全加密”。

### 28.32 APSS-style ACSS 的候选实例化裁决

首个候选不再称为“直接复用 APSS”，而定义为
`C_APSS^opaque`：复用 APSS 的 ACSS 交付与传播骨架，关闭 `GenZeroPoly` 的
public evaluation revelation，在需要模拟时把 Feldman commitment layer 替换为
可隐藏的承诺，并接入 frontier-bound `READY` receipt。

逐项 reduction ledger 已写入定理稿 `repair-closure-theorem-draft.md:2359`。
其中 `PC1/PC3` 可由 ACSS 私密交付和 completion-propagation 候选支持，`PC2`
只有在所有 evaluation revelation 都关闭后才成立，`PC4` 需要重新检查承诺替换
后的本地点值验证。APSS 的 DLEq proof 不能直接充当
`f_h(0)=F^r(h)` 的两承诺消息相等性证明。

首个候选的条件误差界为：

```text
Adv_ACSS-opaque
  <= Adv_ACSS-Transcript-Sim
     + Adv_Commitment-Hiding
     + Adv_READY/Label-Soundness
     + Adv_Public-Evaluation-Leakage
     + negl(lambda).
```

如果公共 evaluation 消息完全删除，最后一项可置为零；但必须通过协议定义和
实现审计证明，而不能引用 APSS 的 revelation 阶段作为现成依据。

### 28.34 首个具体 ACSS 候选：`hbACSS0 + hbPolyCommit`

本地转写审计后，首个具体候选从抽象的 `C_APSS^opaque` 收紧为
`C_hb0^opaque`：采用 hbACSS0 的 univariate ACSS、`OK/READY` amplification 和
hbPolyCommit evaluation proof，加入 receiver-ephemeral encryption、frontier
label，以及退休后禁止 share recovery。

它比直接引用 APSS 更适合当前证明，因为 hbACSS 明确给出了 READY 可用性链和
静态 transcript simulator。但原协议的 implication proof 会触发 key disclosure
以恢复缺失 share；若该路径能在 retirement 后执行，旧 AVID ciphertext 就会成为
新的 scalar-opening edge。因此必须把 implication、key reveal 和 share recovery
全部置于 frontier gate 之后拒绝。

Haven++ 的 packed/bivariate 版本暂不作为首个实例：它会引入共享高阶系数和
packed recovery，正好违反当前跨坐标 typed-isolation 的简化边界。候选优势界和
适配条件见定理稿 `repair-closure-theorem-draft.md:2508`。

### 28.35 hbACSS recovery的 frontier gate

原 hbACSS 的 `IMPLICATE -> KEYREVEAL -> RECOVER` 路径会在恢复缺失份额时披露
receiver key。FGSR 现在将该路径显式绑定到
`(rid,sid,ell,cfg,generation,T_req)`，只允许 `Live/Recoverable` 坐标接受；
`Retired` 状态原子擦除 endpoint、pending plaintext 和 recovery state，并拒绝
所有迟到的 implication、key-reveal 和 recovery 消息。

定理稿 `repair-closure-theorem-draft.md:2568` 的 `Lemma 13/14` 分别保留活跃
坐标的恢复活性、排除退休坐标的 recovery edge，`Theorem 10` 给出相应闭包包含式。
这使 hbACSS 的 recovery 不再被当作全生命周期黑盒，而成为只对 live coordinate
开放、对 retired coordinate 吸收态关闭的局部操作。

### 28.36 generation-local hbACSS simulator

定理稿 `repair-closure-theorem-draft.md:2670` 将 hbACSS 原论文的 static-key
simulator 提升为条件性的 generation-local simulator：每个 interval 只接收
`B_{ell,r}` 暴露状态和上一 interval 的模拟视图，使用 hbACSS transcript simulation、
hbPolyCommit hiding/ZK、ephemeral-PKE、PECC 和 affine coupling 生成下一代视图。

该 lifting 明确要求 simulator 对任意自适应身份集合 `B_{ell,r}`、并发
`rid/coordinate/generation/frontier` 标签都成立；原论文只给出固定静态腐化集合
的 simulator，不能直接满足这一要求。`Proposition 15` 的优势界已将这一差异
显式列为 `Adv_hbACSS-StaticSim^r` 和 generation-binding 项。

### 28.37 P1 typed-edge ledger：自适应密钥暴露是实际缺口

本轮把 `C_hb0^opaque` 的实例化义务从笼统的“生成级模拟”细化为十类 typed
edges：承诺生成、点值到加密 payload、密钥解密、READY receipt、
`IMPLICATE -> KEYREVEAL`、recovery、安装、擦除后的代际传递、证明控制流和
跨坐标数据面。定理稿 `repair-closure-theorem-draft.md:2660` 之后的 Lemma 16
给出了对应的逐代优势界。

这里出现了一个不能被普通 IND-CPA 掩盖的关键区别。原 hbACSS simulator 可以在
知道静态 corrupted-key set 后，把其他公开密钥设为随机字符串，并为它们生成
零密文；但在长期移动腐化模型中，公开密钥和 AVID ciphertext 先出现，敌手随后
才选择下一个节点。若该节点的长期 secret key 之后暴露，归档 ciphertext 仍可被
解密，旧 evaluation 就重新进入 recovery closure。

因此首个具体实例至少要满足一个明确接口：

```text
AK1: 可自适应生成且可安全擦除的密钥接口；或
AK2: 每个 repair instance 使用 ephemeral receiver key，并有 PECC 证明屏障后
     暴露不能解封旧 payload；或
AK3: 已有的自适应门限加密定理同时覆盖 receiver-key exposure schedule 和
     AVID ciphertext transcript。
```

当前候选只继续审计 `AK2`。hbACSS 原文的 long-term-key optimization 不满足它，
因为之后暴露 receiver secret 仍可恢复共享对称密钥。若 AVID 仍允许公开 transcript
或 channel buffer 导出 scalar evaluation，则 `Adv_Uncovered-Edge` 保持非零，
`C_hb0^opaque` 只能作为条件候选，不能写成首个具体安全构造。

这一步的价值在于把“hbACSS 能否用于长期自适应 FGSR”变成可否证的接口问题：
不是引用原论文的 static secrecy，而是逐项证明旧 payload 在 barrier 后没有新的
`Key -> Point -> Recover` 路径。

### 28.38 AK2：per-instance key-erasure 接口

当前只继续审计 `AK2`。对每个 repair context `Q`，receiver 生成一次性的
`(pk_Q,i,sk_Q,i)`，AVID 只保存加密 payload 和 metadata；退休时原子擦除
`sk_Q,i`、pending plaintext、evaluation opening、recovery key material 和
endpoint buffer，但允许公开保留 ciphertext。于是安全目标不是删除网络记录，而是
证明退休后不存在新的

```text
retained ciphertext -> receiver key -> scalar point -> recovery contribution
```

路径。定理稿 `19.42` 将该性质写成 `PECC` 游戏，`Lemma 17` 给出退休坐标
`Recovery-Closure` 不扩大的条件结论。

该接口同时明确了历史暴露的边界：退休前合法的 `KEYREVEAL` 所泄露的 key、point
和 recovery material 永久进入 `X_hist^r(B_{ell,r})`；退休后对 `Retired` 坐标的
key reveal、implication 和 recovery 请求直接拒绝。因而 AK2 不会把“擦除”错误地
解释为撤销此前已经发生的暴露。

AK2 仍不是完整构造。必须继续分别证明：

1. 自适应选择 `B_{ell,r}` 后，公开密钥和 AVID transcript 的模拟仍成立；
2. hbPolyCommit evaluation proof 在并发 frontier label 下可模拟且不产生 scalar opening；
3. 跨坐标 aggregate transcript 满足 `Joint-AO`，而不是仅满足坐标级 IND-CPA。

如果第一项只能依赖静态 corrupted-key set，或者 AVID/channel buffer 在屏障后仍可
导出旧 point，`C_hb0^opaque` 只能保留为条件接口；这不会影响抽象的
`Recovery-Closure` 和 `privacy-finality` 定理。

### 28.39 Adaptive AVID/commitment barrier

hbACSS 的 AVID 定义只保证异步交付、可用性和一致性；原 secrecy proof 允许敌手
看到所有 AVID 消息。因此“payload 是通过 AVID 传输的”不能直接推出自适应
transcript simulation。更具体地，公开 commitment `C` 和 AVID transcript 先被
固定，敌手之后才选择本代腐化节点；这要求模拟器能够回答事后暴露而不修改既有
开口关系。

定理稿 `19.43` 将该问题拆成五项接口：

```text
AC1  commitment 支持自适应一致开口，或模拟器拥有等价 trapdoor/share oracle；
AC2  barrier 前腐化的 receiver 具有可自适应模拟的 payload/key state；
AC3  barrier 后腐化由 AK2/PECC 处理，状态中没有旧 key/plaintext；
AC4  AVID blocks、receipt 和 reconstruction metadata 不产生 scalar capability；
AC5  每个 pre-frontier KEYREVEAL 在下一次自适应选择前进入历史暴露视图。
```

这带来一个重要的 go/no-go 结论：per-instance ephemeral key 只关闭
`ciphertext -> old key -> old point` 的退休后路径；它不自动解决 pre-frontier
adaptive simulation。原 hbACSS static simulator 加普通 Pedersen hiding 和
IND-CPA 不能直接支撑完整的长期移动敌手定理。若不引入 equivocal/adaptive
commitment 与 non-committing encryption，`C_hb0^opaque` 必须作为条件接口，不能
写成本文已经完成的具体构造。

### 28.40 Janus-style transport 的位置

本地 Janus DKG 文档提供了一个可复用的参考接口：hiding commitment、可在事后
腐化时一致开口的状态模拟、可模拟的加密 ciphertext 以及 secure erasure。它说明
AC1/AC2 有现成的密码学路线，不必把自适应加密重新包装成本文贡献。

但 Janus 不能直接替代 FGSR。它的目标是 DKG/key sharing；投诉路径可以主动公开
某个 ciphertext 的明文，也没有 per-coordinate frontier、退休后的 recovery
closure 或 aggregate-only `Joint-AO`。因此论文中的正确组合方式是：

```text
Janus-style adaptive transport  -> 负责 AC1--AC3 的局部交付模拟
FGSR frontier gate              -> 负责 AC4--AC5、退休吸收态和 no-resurrection
Joint-AO                        -> 负责跨坐标 aggregate-only 数据面
```

定理稿 `19.44` 的 Proposition 19 给出该 transport substitution 的边界。复用
Janus-style transport 本身不构成贡献；真正的贡献仍是异步 secure aggregation 中
`Robust-Hitting + Recovery-Closure + absorbing retirement` 的统一刻画，以及它在
长期移动腐化下对 aggregate-only 输出的应用。

当前构造选择因此变为：优先审计 Janus-style transport 是否能在不公开退休坐标
scalar 的前提下满足 Common-H/READY 和 helper equality；若不能，保留条件
`AVID-opaque` 接口，不再声称 `hbACSS0 + 普通 PKE` 已经完成实例化。

### 28.41 Complaint 的发送时刻与 frontier gate

Janus-style complaint 路径还必须采用明确的异步时间语义。公开
`KEYREVEAL` 的暴露时刻是它进入公共 transcript 的时刻，而不是其他节点后来
接收或处理它的时刻：

```text
send(KEYREVEAL) < T*  -> key/point/recovery material 进入历史视图；
receive(message) >= T* 且 state=Retired -> 不产生新的 recovery edge；
send(KEYREVEAL) >= T* -> 不允许发布或接受该边。
```

定理稿 `19.45` 的 Lemma 18 证明，退休前发送、退休后到达的公开解密材料只能
重复已经计入 `X_hist` 的能力，不能因为异步延迟重新生成旧 capability。若某实现
要求退休后继续处理 complaint 才能保持活性，则它不能进入首个 FGSR 定理；活性必须
在 `Live/Recoverable` 阶段完成。

### 28.42 `F_AWF` 的 Publish/Process 语义

本轮把 send-time exposure 从证明注释提升为理想功能接口。`F_AWF` 现在显式维护：

```text
Publish(Q,m)  -> public event or reject
Process(Q,m,T_local) -> accept or reject
```

对公开 `KEYREVEAL`，`Publish` 发生时就把 key、可验证 point 和派生 recovery
material 加入历史暴露视图；`Process` 只决定节点状态机是否接受安装或恢复。因而
退休前发送、退休后到达的消息会保留在 `X_hist`，但不会产生新的 retired-coordinate
recovery edge；退休后才发送的 `KEYREVEAL` 直接被拒绝。

这一定义解决了完全异步协议中“迟到消息是否算已经泄露”的歧义，也使 `F_AWF`、
`Lemma 18` 和 `Recovery-Closure` 使用同一个事件语义。它不增加新的密码学假设，
但如果实现把公开 complaint 的活性放在退休之后，则该实现不满足首个 FGSR 模型。

### 28.43 Complaint transcript 与 `Joint-AO` 的因子化

公开 complaint 不能因为来自 recovery 模块就自动归入 `StateView`。当前将其拆为：

```text
Comp_state = 只读取 Q、frontier、generation、helper validity、current share
             state 和 recovery schedule 的消息；
Comp_data  = 读取 client ciphertext、weights、H_ct、H_out、aggregate ciphertext、
             partial decryption 或 output state 的消息及其控制分支。
```

`Comp_state` 中的公开 `KEYREVEAL` 仍须按 send event 计入 `X_hist`，但只要它的
分布在给定历史视图后与 challenge key vectors 无关，就可以留在 `StateView`。
`Comp_data` 及其决定是否发送该消息的控制分支必须整体移入 `DataView_b`，由一次
完整的 `Joint-AO` challenge 覆盖。

定理稿 `19.46` 的 Proposition 20 给出该因子化条件。若 recovery proof、receipt
或 complaint predicate 能根据单个客户端 ciphertext/weight 选择解密分支，就会产生
`Adv_Complaint-Noninterference`，不能再从普通 `RCL-Sim/AO` 推出隐私终结。首个
实例必须用 typed API 保证 recovery 只处理委员会 share capability，不读取客户端
数据面；否则公开 complaint transcript 会成为未建模的 individual-key opening oracle。

### 28.44 `R_eq`、aggregate certificate 与 partial decryption 的对象级裁决

针对 TACITA-style 数据面，当前分类固定为：

| 对象 | 归属 | 原因 |
|---|---|---|
| `R_eq(ctx,u,{ct_{u,ell}},w_u)` 及其 proof | `DataView_b` | statement 读取 challenge ciphertext，witness 含 mask material |
| aggregate certificate `(S,w,tag,H_ct,H_out)` | `DataView_b` | 绑定具体 client set、ciphertext multiset 和输出上下文 |
| `PartDec(sk_j,ct_D,tag)` 及 proof | `DataView_b` | ciphertext-specific，必须和 aggregate ciphertext 一起挑战 |
| helper `IMPLICATE/KEYREVEAL/RECOVER` | `StateView + X_hist` | 只处理 repair context/current share，不读取客户端数据 |
| invalid aggregate complaint | `DataView_b` | 其分支读取 aggregate ciphertext、proof 或 partial decryption |
| ACSS `READY`/availability receipt | `StateView` | 只含 authenticated metadata，不含 scalar evaluation |

因此不能把 `R_eq` 或 partial decryption 当作普通状态层证明。即使单个 partial
decryption 不直接打开明文，它的 ciphertext-specific component 仍可能区分两个
等和 key vector。定理稿 `19.47` 的 Lemma 19 证明，在 `R_eq` 的并发模拟、
proof-noninterference、descriptor uniqueness 和 complaint factorization 成立时，
所有 challenge-dependent 输出都被一次 `Joint-AO` 覆盖。

当前裁决仍是条件性的：TACITA 的 extended CPA 是坐标级数据面依据，但本地证据
尚未关闭 auxiliary-input、并发 `R_eq` proof 和 complaint-branch simulation。
普通 NIZK soundness 不能代替这些接口，故主定理继续显式保留 `Joint-AO`。

### 28.45 TACITA 的静态边界与论文的真正下一步

TACITA 不是本文长期自适应数据面定理的现成证明。其 extended CPA 游戏在
challenge 前固定 `Cor`，因此只覆盖固定腐化集合下的一次 aggregate opening。本文
需要的 `Joint-AO^mob` 则允许敌手在观察完整 generation transcript 后，自适应地
轮换腐化节点、发起恢复并在退休后暴露当前状态；挑战视图还必须联合包含所有
坐标的 `R_eq`、aggregate certificate、ciphertext-specific partial decryption 和
公开 complaint 分支。

因此论文不再采用“逐坐标调用 TACITA，再用秘密共享补长期安全”的叙事。这个组合
有两个独立断点：未来腐化可能解封旧 ciphertext，残留 recovery state 可能重建已
退休份额。前者是 adaptive-key/PECC 问题，后者是 Recovery-Closure 问题；TACITA
的静态 aggregate game 都没有这两个 oracle 或状态转移。

论文中应明确写出以下边界命题：

```text
TACITA Static-AO + ordinary repair
    does not imply Joint-AO^mob or privacy finality.
```

要把 `Static-AO` 提升为本文所需接口，至少必须额外证明：

1. generation-local receiver state 和公开 transcript 的自适应模拟；
2. 退休后暴露不能解封保留 ciphertext 的 `PECC`；
3. 多坐标、等和消息、aggregate certificate 和 partial decryption 的一次性联合
   challenge；
4. 并发 `R_eq`、无效聚合投诉及其控制分支的 proof-noninterference；
5. repair 不会重新产生退休坐标 capability 的 localization/closure 定理。

这使主线的创新位置更清楚：TACITA 提供数据面基线，FGSR 提供异步长期状态层的
`Robust-Hitting + Recovery-Closure + absorbing retirement` 理论；两者之间的
`Joint-AO^mob` lifting 是一个需要单独证明的桥，而不是可以在叙事中略过的工程
组合。

### 28.46 实验之外的证明交付顺序

当前阶段只推进一条证明依赖链：

```text
P0  固定 Joint-AO^mob 的游戏和完整视图；
P1  完成 Static-AO separation 与 recovery-state localization attack；
P2  在 Joint-AO^mob 和 opaque adaptive repair 假设下完成 FGSR 组合定理；
P3  用 adaptive threshold decryption + simulation-sound R_eq 尝试具体提升；
P4  根据未闭合项决定“具体构造”或“抽象主定理 + 分离/条件实例化”的论文形态。
```

P2 之前不扩展动态委员会。动态 handoff 只有在证明它不增加退休坐标的
`Cl_rec` 后，才能作为推论加入；否则会把核心的长期自适应问题稀释成系统功能清单。
实验只负责验证 P1 的攻击、P2 的状态机边界和活性/通信代价，不能替代上述证明。

### 28.47 `Joint-AO^mob` 的正式游戏接口

现有 19.17 是静态 `Joint-AO` 游戏：腐化集合在挑战前固定，且没有挑战后的状态
暴露。为了让主定理与长期移动腐化模型一致，本文现在把它扩展为一个单一挑战位
覆盖的 `Joint-AO^mob` 游戏。

敌手先通过 prefix oracle 观察公开 setup、异步 `Publish/Process` 事件以及合法的
corrupt/recover/retire 操作。每次腐化返回当前可读状态和此前已经公开的历史状态；
擦除材料不可再读，但擦除前已经暴露的材料永久计入 `X_hist`。下一次腐化节点、
恢复上下文和退休请求均可由完整前缀视图自适应决定。

在一次 `Challenge` 中，敌手提交一批并发 descriptor 和两组 key vectors。每个
descriptor 的两组向量必须具有相同授权加权和。挑战者用同一个 bit 生成所有坐标的
client ciphertext、`R_eq`、aggregate certificate、ciphertext-specific partial
decryption、无效聚合分支和 aggregate-only 输出。挑战后继续允许自适应腐化、恢复、
退休和 `Publish/Process` 查询。

视图强制分解为：

```text
View_b = (DataView_b, StateView, PublicContext_pre, X_hist).
```

`DataView_b` 包含所有读取 challenge ciphertext、权重、`R_eq`、aggregate ciphertext、
partial decryption 或 output descriptor 的对象及其控制分支；`StateView` 只能读取
frontier、generation、helper validity、current-share state 和 recovery schedule。
公开 `KEYREVEAL` 在 send event 进入 `X_hist`，不能因为稍后才 receive 而重新分类。

因此，`Joint-AO^mob` 不是给 TACITA 增加一个“adaptive”标签，而是要求完整数据面
和状态暴露在同一个因果游戏中被模拟。现有 TACITA 只能作为其中的静态坐标基线；
论文必须另外证明 adaptive lifting，或者保留 `Joint-AO^mob` 为独立假设。

该定义还给出一个可证伪的审计标准：如果某个 recovery/complaint 分支读取单个
client ciphertext 并据此决定是否发布 partial decryption 或 certificate，它就违反
`StateView` 的类型约束，必须整体移入 `DataView_b`；如果无法放入同一个联合挑战，
该具体实例停止在条件结果，而不再声称完成长期安全。

### 28.48 P1：Recovery-State Localization Barrier 的正式攻击

`Joint-AO^mob` 解决的是数据面挑战如何覆盖自适应 transcript；P1 还必须解决一个
独立的状态面问题。把普通恢复包装器的状态写成：

```text
State_i = (G, L_sid, d_i(sid), T)
```

其中 `G` 是跨会话的持久恢复权，`L_sid` 是会话局部 recovery material，
`d_i(sid)` 是直接解密 capability，`T` 是公开 frontier/tombstone。如果退休只
删除 `d_i(sid)`，但 `G` 没有按 `sid` 穿孔，且足够多节点仍保留 `L_sid`，那么普通
`Recover` 关系仍可生成 `d_i(sid)'`。

若旧 descriptor 上的 `Use_sid` 仍接受该 capability，则攻击者在未来暴露所有当前
状态后，可以合法执行 recovery，再直接对保留的旧 client ciphertext 做 individual
partial opening，恢复客户端 mask key。
`CheckInstall` 的 tombstone 只能阻止节点把恢复结果安装成当前状态，不能阻止攻击者
离线得到并使用该 capability。

因此得到正式分离：

```text
delete direct share + monotone tombstone
    does not imply
retired recovery closure is absorbing.
```

这不是说 VSSR/DPSS 的原始安全性失效。它们的正确性目标是保持一个长期秘密或恢复
一个缺失份额；本文需要的是更强的 `Cl_rec` 性质，即退休标签的恢复闭包不能再包含
任何能够进行 individual opening 的授权集合。若恢复机制只能再次输出同一个授权
aggregate，且不能产生 individual opening 或第二个独立 aggregate descriptor，则必须
在安全定义中明确这一较弱目标，不能把它直接写成区分攻击。要进入当前 FGSR 模型，
至少要做一项：删除/穿孔全部 `sid`-local recovery material；让恢复权和 `Use_sid`
都绑定 frontier；或者切换到使旧 capability 无效的新加密/恢复世代。

该攻击稿现在成为 P1 的第一项证明：它既能作为 VSSR/DPSS 的黑盒分离，也能作为
实验中 stale-repair violation 的理论解释。下一项是把攻击写成与 `Gamma_dec^cap`
和 `Cl_rec` 直接对应的 proposition，并验证 FGSR 的 current-share-only repair
确实删除了攻击所需的 `L_sid`。

### 28.49 P1：Static-AO wrapper separation

把 `TACITA Static-AO` 当作黑盒数据面，再外接未穿孔的 ordinary recovery，会得到
一个可直接区分的长期攻击。攻击者先提交两组具有相同授权加权和、但在某个客户端
`u` 的 mask key 上不同的向量，获得静态 TACITA challenge transcript。静态游戏中的
corruption set 仍然固定。

随后在 wrapper 层执行：退休 `sid`，自适应暴露保存 `G` 与 `L_sid` 的当前状态，
调用合法 recovery，得到足够的 capability，再对保留的 `ct_{u,ell}` 做 individual
opening。恢复出的 key 与两组 challenge key 比较后即可判断 challenge bit，成功率
接近 1。静态 TACITA transcript 本身没有被破解；区分信息来自静态游戏没有建模的
post-challenge state exposure 和 recovery interface。

因此得到更具体的分离：

```text
Static-AO secure
    + unpunctured recovery wrapper
    does not imply Joint-AO^mob.
```

该结论只针对存在 individual-opening capability 或第二个独立 aggregate descriptor
的接口。若一个实现始终只能输出同一个授权 aggregate，则不能使用上述 individual
opening 攻击；它必须改用“第二 descriptor/数据相关分支”的 `DataView_b` 分析。

FGSR 的退休审计由三项检查组成：

```text
L1  future StateView 中不存在 retired-coordinate local recovery material；
L2  retained global recovery authority 单独不能重新生成该 material；
L3  所有 surviving Use/PartDec 路径都执行 frontier-bound retired-label check。
```

这三项是当前 P1 到 P2 的接口桥：P1 证明 ordinary wrapper 为什么失败，P2 证明
current-share-only FGSR 在满足 L1--L3 时如何把失败路径从 `Cl_rec` 中排除。

### 28.50 FGSR 抽象状态机如何满足 L1--L3

FGSR 的抽象退休操作执行 state-complete erasure，退休后仅保留：

```text
frontier >= T*, retired(sid), public metadata, live-coordinate states.
```

它不保留退休 generation 的 direct share、repair share、recovery-polynomial share、
DPRF contribution、pending endpoint secret 或 `sid`-local backup。接口同时规定：

```text
Recover(retired sid, ...) -> reject;
Use/PartDec(retired sid, ...) -> reject;
live recovery -> require current generation and frontier label.
```

因此在抽象 FGSR 层，`L1--L3` 的两个失败项为零：

```text
Adv_Recovery-Localization = 0,
Adv_Frontier-Use = 0.
```

具体实现仍需分别证明：擦除后 endpoint/buffer 确实不再暴露旧材料，公开 transcript
不含 scalar recovery material，以及 `Use/PartDec` 的 frontier 检查不能被旧 descriptor
或迟到标签绕过。定理稿 19.53 将这些实现缺口保留为 `PECC`、opaque transcript 和
generation-binding 优势项；它没有把抽象状态转移误当成物理擦除证明。

### 28.51 P2：四阶段组合混合

FGSR 主证明现在固定为四个 hybrid：

```text
H0  真实 FGSR 执行，包含自适应腐化和合法 recovery；
H1  按 generation 顺序把 ACSS、equality proof、receipt 和 endpoint exposure
    替换为 challenge-independent StateView，保留 DataView_b；
H2  用一次 Joint-AO^mob challenge 替换完整 DataView_0 为 DataView_1，覆盖所有
    descriptor、coordinate、certificate、partial decryption 和控制分支；
H3  用 context uniqueness、mask correctness 和 Cross-Generation Affine Coupling
    处理剩余输出。
```

对应优势界为：

```text
Adv[H0,H3]
  <= Adv_Joint-AO^mob
     + Adv_Affine-Coupling
     + Adv_State-Commitment
     + Adv_Generation-Binding
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + Adv_Context/Correctness
     + sum_r(Adv_ACSS-opaque^r
            + Adv_Eq-Simulation^r
            + Adv_PECC^r)
     + R*negl(lambda).
```

关键点是 H1 不把 challenge-dependent 分支塞进 state simulator，H2 不做逐坐标
hybrid，因而不会要求 NIZK 对中间 false statement 进行证明。具体构造只有在逐项
证明这些接口后，才能把相应优势项化为 negligible；模块名称本身不能删除任何一项。

### 28.52 P2：将 L1--L3 接入 FGSR 组合定理

定理稿 19.31 现在把 `L1--L3` 作为 BF-RPTA 条件实例的独立假设，并将其失败
分别记为 `Adv_Recovery-Localization` 与 `Adv_Frontier-Use`。主界变为：

```text
Adv_Privacy-Finality(FGSR-Eph(C))
  <= Adv_Joint-AO^mob
     + Adv_Affine-Coupling
     + Adv_State-Commitment
     + Adv_Generation-Binding
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + Adv_Context/Correctness
     + sum_r(Adv_ACSS-opaque^r
            + Adv_Eq-Simulation^r
            + Adv_PECC^r)
     + R*negl(lambda).
```

这一步把 P1 的攻击变成 P2 的证明接口：`L1` 排除未来 `StateView` 中的
`sid`-local recovery material，`L2` 排除 retained global authority 的单独重建，
`L3` 排除绕过 `CheckInstall` 的旧 `Use/PartDec`。在理想的 FGSR 状态机中两项
优势为零；在具体实现审计完成前，它们必须保留在安全界中。

因此当前的组合定理不是“VSSR recovery 加一个 tombstone”，而是：

```text
Joint-AO^mob data plane
  + opaque adaptive repair
  + L1--L3 recovery localization
  + frontier-safe Use/PartDec
  => privacy finality.
```

### 28.33 Hiding commitment 下的本地点值验证

本轮补齐了 Pedersen commitment 版本的一个实现缺口。若
`C_k=g^{a_k}h^{rho_k}`，则 receiver `j` 的 evaluation commitment 为
`C_F(j)=g^{F(j)}h^{R(j)}`。因此 receiver 不能只像 Feldman 版本那样比较
`g^{F(j)}`；ACSS 必须通过 receiver-specific 私密通道交付 `(F(j),R(j))`，或
交付一个只供 receiver 验证的 opening proof。该 opening material 不进入
`READY` 或公共 transcript，并在 pending subshare 擦除时删除。

定理稿 `repair-closure-theorem-draft.md:2131` 的 `Lemma 10` 证明本地验证的
正确性，`Lemma 11` 证明 `2f+1` 个经过本地验证的 `READY` 签名在 ACSS
completion-propagation 条件下推出 `AVSSComplete_h`，`Proposition 12` 则给出
ACSS transcript simulation 的第一版优势分解。由此，Pedersen hiding 不再只是
写作假设，而被明确纳入 endpoint state、PECC 和 simulator 的对象分类。

### 28.30 FGSR 专用 Retirement-Closure 归约

定理稿 `repair-closure-theorem-draft.md:2155` 已将抽象的
`Retirement-Closure` 具体连接到 FGSR 四步 wrapper。证明按最终 derivation edge
分类：旧 descriptor 受 frontier/generation binding 拒绝，迟到 subshare 受
opaque delivery 与 `PECC` 隔离，pending `F'` 只有受 frontier guard 支配的
`Install` 边，退休后的残留 state 不再拥有 repair 或 decryption edge，而跨代、
跨坐标对象由 typed capability isolation 和 `Joint-AO` 排除。

该定理的结论不是“擦除后没有任何状态”，而是：残留状态只能作为攻击者已有的
`X` 进入闭包，不能通过新的合法恢复边生成旧 coordinate 的能力。因而在
`|U_ell union B_{ell,ret}| < q_rec` 下，未来全状态暴露不会扩大旧能力集合。
目前剩余的不是新的协议控制流，而是为三项密码学接口给出具体构造证明：
opaque ACSS delivery、helper equality-proof simulation 和 `PECC`。

### 28.53 实验转移后的主线裁决：先证明接口，再谈具体构造

当前工作仍然是一篇异步联邦学习安全聚合论文，但论文的核心贡献不是再做一
个 FL 工程系统。核心问题是：在完全异步、长期运行、移动自适应腐化和需要份额
恢复的安全聚合中，什么时候一次已经完成的聚合能够获得真正的
`privacy finality`，即未来状态暴露和迟到恢复都不能重新扩大其访问结构。

实验基线在其他设备运行后，本机的首要任务转为证明闭环。当前状态必须准确表述
为“两层结果”：

1. **理论层。** `Robust-Hitting`、`Recovery-Closure`、absorbing retirement、
   no-resurrection 必要性和 `Joint-AO^mob` 组合定理构成抽象主结果。它们不依赖
   hbACSS 或 Janus 已经给出本文所需的具体长期自适应安全。
2. **实例层。** Janus-style transport 和 hbACSS 只能作为候选底层交付接口。
   它们分别只覆盖部分自适应承诺/交付能力，不能自动覆盖 FGSR 的退休 frontier、
   recovery closure、aggregate-only 数据面和未来全状态暴露。因此首版只能给出
   条件实例化，除非逐项完成 AC1--AC5 证明。

这使叙事区别于“前向安全加秘密共享”：前向安全可以限制某些历史密文在
未来密钥暴露后的解密能力，但它不刻画异步恢复边、公开 complaint、跨坐标聚合
和退休状态的访问结构闭包。本文的对象是整个恢复—使用图，而不是单个密钥的
时间演化。

**实验之外的执行顺序：**

1. 定义独立的 `Adaptive-Opaque-Repair` 接口，明确 `Publish`、`Process`、
   `KEYREVEAL` 的 send-time 暴露、endpoint/buffer 暴露、原子擦除和 retired-label
   拒绝。
2. 证明该接口经过 FGSR wrapper 后满足 `L1--L3`，并正式完成 `H0 -> H1 -> H2 -> H3`
   的主定理；所有未证明接口继续保留为显式优势项。
3. 写出最小 no-resurrection 攻击和匹配的 absorbing-retirement 充分条件，形成
   “没有 frontier 就不可能有 privacy finality”的必要性结果。
4. 将 Janus/hbACSS 放入条件实例化章节，只逐项映射 AC1--AC5，不把已有工作
   的局部自适应安全改写成本文的具体构造定理。
5. 最后再整理动态委员会推论、相关工作分离表和论文正文。动态节点、packed
   repair 和新的密码学原语在上述接口未闭合前都不扩展。

因此下一步不是继续寻找更多 FL 基线，而是完成一份可审计的接口证明表：每一
个 scalar capability 从哪里产生、何时进入历史视图、何时被擦除、退休后哪条
边阻断它。该表闭合后，论文才从“有吸引力的协议框架”进入“可投稿的理论结果”。

### 28.54 `Adaptive-Opaque-Repair`：连接控制面与数据面

前面的 `F_AWF` 只规定公开 frontier 如何合并，`RPTA` 只规定当前委员会状态
如何参与聚合。两者之间仍缺一个严格的状态层接口：在自适应腐化、迟到消息和
恢复并发下，修复 transcript 与 endpoint state 必须可以被模拟，同时不能产生
新的 scalar capability。本文将这一接口命名为 `Adaptive-Opaque-Repair`，简称
`AOR`。它是证明接口，不是额外的工程组件。

对修复上下文

```text
Q = (sid, ell, r, rid, i, T_req, C_ctx)
```

`AOR` 暴露 `Publish`、`Process`、`Expose`、`Retire`、`Recover` 和
`CheckInstall`。其中 `Publish` 的发送事件立即更新 `X_hist`，而 `Process` 只
决定本地是否接受该消息。腐化发生在退休前时可以暴露 endpoint key、明文或
opening；退休后只能看到擦除后的状态、公开密文和元数据。这个接口因此把
“公开过的能力”和“节点后来是否接收消息”严格分开。

`AOR` 的安全游戏以真实修复传输和只接收 `PublicView`、`X_hist`、frontier 的
模拟器为两个世界。`PublicView` 只能包含认证标签、承诺、opaque payload、receipt、
availability evidence 和状态机结果；point value、临时解密钥、evaluation
opening、pending plaintext 和 recovery scalar 属于 `HiddenState`。模拟器必须
保持公开 transcript、标签和 accept/reject 结果的分布一致，但不能因为未来会
发生腐化而提前获得隐藏标量。

因此定义

```text
Adv_AOR^mob
  = |Pr[Real_AOR=1] - Pr[Sim_AOR=1]|.
```

`AOR` 还必须满足五个性质：

1. **Causal publication：** 所有公开 `KEYREVEAL` 在发送时计入历史视图；
   退休后发送的 reveal 被拒绝。
2. **Opaque delivery：** AVID、receipt 和 availability 证据不携带可重构的
   scalar opening。
3. **Adaptive state consistency：** 公开承诺固定后，后续腐化仍能得到与既有
   transcript 一致的状态。
4. **Post-frontier opacity：** endpoint、buffer 和恢复响应不能在退休后导出旧
   point capability。
5. **Frontier absorption：** 迟到的 `Install`、`Use`、`PartDec`、`Recover`
   和 `KEYREVEAL` 都被 retired label 吸收。

这给出主证明中 `H0 -> H1` 的单一接口归约：

```text
Adv[H0,H1]
  <= sum_r Adv_AOR^mob(r)
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + R*negl(lambda).
```

若未来能把 `Adv_AOR^mob` 归约到 adaptive commitment、hbACSS transcript
simulation、`PECC`、complaint noninterference 和 generation binding，论文得到
具体实例；否则仍然得到完整的抽象 FGSR 定理和一个边界清晰的条件实例化。
这比直接把 hbACSS、Janus、前向安全加密或普通 VSS 拼在一起更严格：每个组件
只能关闭它实际覆盖的 AOR 边。

### 28.55 `AOR-5` 与 Robust-Hitting 的必要性/充分性对应

令 `A` 为 `PC_sid` 覆盖的退休节点，`R` 为退休后仍可由迟到合法消息重新安装
旧 capability 的节点，`B` 为退休前已经暴露的旧 capability。则退休后的有效
暴露集合可以写成：

```text
B_eff = B union R union (P - A).
```

对固定的暴露集合 `B`，精确条件是每个解密集合都不能被有效暴露集合覆盖：

```text
D is not a subset of B union R union (P - A).
```

若敌手可以任意放置至多 `b` 个暴露节点，则对应的最坏情况计数条件为：

```text
|D intersection (A - R)| > b.
```

当 `AOR-5` 成立时，所有 stale `Install/Use/PartDec/Recover/KEYREVEAL` 边都被
frontier 吸收，因此 `R=emptyset`，条件退化为 `Robust-Hitting`。如果没有
`AOR-5`，普通退休证书即使满足 Robust-Hitting，也可能因一个迟到恢复边产生
`R`，使同一证书失去隐私终结性。

因此论文的两个核心条件各自承担不同任务：`Robust-Hitting` 约束谁必须被
穿孔，`AOR-5` 约束异步状态机是否允许已穿孔能力复活。稳定公钥、迟到消息和
恢复活性同时存在时，若恢复路径不携带支配退休事实的单调状态，就能构造
前后两个不可区分执行，使旧消息在退休后重新安装 capability。这是
no-resurrection 必要性，而不是对普通 forward secrecy 的重复表述。

### 28.56 P4：具体归约的证据裁决

原文审计后的结论是：Janus 的自适应模拟确实提供了本文 AC1/AC2 所需的一个
强参考。它在公开承诺后擦除 sharing polynomial，并利用可后开口的 hashed-ElGamal
密文回答中途腐化；但其 complaint 路径会让争议密文公开可解密。因此 Janus
不能未经 wrapper 直接成为 FGSR repair transport。

hbACSS 则明确允许敌手看到所有 AVID 消息和公开密文。它的
`IMPLICATE -> KEYREVEAL -> RECOVER` 路径公开接收者密钥，长期密钥优化仍允许
未来暴露状态解密旧 payload。hbACSS 能支持 availability/evaluation correctness，
但不能单独关闭 AOR-2、AOR-4 或 AC4。

当前具体归约保持为：

```text
Adv_AOR^mob(r)
  <= Adv_Adaptive-Commitment^r
     + Adv_hbACSS-StaticSim^r
     + Adv_PECC^r
     + Adv_Complaint-Noninterference^r
     + Adv_Generation-Binding^r
     + negl(lambda).
```

这不是否定 Janus 或 hbACSS，而是划清它们的贡献边界：Janus 提供自适应状态
模拟的密码学路线，hbACSS 提供异步可验证交付和恢复正确性，FGSR wrapper 才
负责 per-coordinate frontier absorption，`Joint-AO^mob` 负责 aggregate-only
数据面。下一步是证明 complaint/decryption 分支可以被替换为 metadata-only、
frontier-safe 分支；若做不到，论文保留条件接口，不声称具体长期安全构造。

### 28.57 Complaint-Noninterference 的独立边界

如果 complaint 的公开内容和保留的 ciphertext 一起能够导出 evaluation point
或 recovery scalar，那么仅增加 tombstone 并不能使该路径满足 AOR。退休后发送
的 complaint 必须在 `Publish` 阶段拒绝；退休前发送的 complaint 则已经在发送
时暴露 key、point 和 recovery material，必须永久进入 `X_hist`。若 complaint
分支读取 challenge-dependent ciphertext、权重或 partial decryption，还必须随
同一 `Joint-AO^mob` challenge 进入 `DataView`。

因此真正可接受的 wrapper 只有两类：

1. metadata-only complaint，并提供不泄露 individual opening 的
   simulation-sound proof；
2. 只允许 live/recoverable 阶段 complaint，并明确计入 pre-frontier exposure。

Janus 和 hbACSS 的当前 theorem 都没有直接提供这两个接口。故
`Adv_Complaint-Noninterference` 仍然是独立的、可证伪的具体构造义务，而不是
可以由普通 AVID correctness 或 forward-secure encryption 自动删除的记号。

### 28.58 候选正向路线：零知识无效性 blame

要关闭 complaint 缺口，可以把公开 `KEYREVEAL` 替换成 metadata-only 的
`ZK-Invalidity` 证明。证明只断言接收者知道一个有效解密 witness，且解码结果
不满足绑定的 evaluation validity relation，或满足一个独立定义的可验证解密失败
关系；它不公开 receiver secret key、decoded point 或 evaluation opening。

该接口至少要求：

1. **Completeness：** 原本需要 `KEYREVEAL` 的 dealer fault 都能生成证明；
2. **Soundness：** honest payload 不能被恶意 receiver 伪造为 recovery trigger；
3. **Adaptive zero knowledge：** commitment/ciphertext 已公开后，receiver 被
   腐化时证明和状态仍可模拟；
4. **Data-plane factorization：** 证明本身不含 scalar，依赖 ciphertext、权重、
   `R_eq` 或 partial decryption 的分支仍进入同一次 `Joint-AO^mob`。

在这些条件、frontier-bound complaint 和上下文绑定成立时，
`Adv_Complaint-Noninterference` 可以归约为 `Adv_ZK-Invalidity`。但普通 NIZK
并不自动证明解密失败、异步可用性或 challenge-dependent publication branch；
所以这只是下一条具体构造路线，不能现在写成已经闭合的实例。

### 28.59 `ZK-Invalidity` 的本地文献裁决

本地文献没有直接提供该接口：VSSR 的 `vssRecoverVerify*` 验证的是恢复贡献，
Choudhuri 的 `Setup/Prove/Verify/SimProve` 面向密文/PPE 合法性和选定批次解密，
Silent-Setup 的 simulation-extractable NIZK 用于绑定密文部件和 CCA 部分解密，
而 Janus 的 complaint 反而公开争议密文的可解密能力。

因此不能把普通 SE-NIZK、VSSR recovery proof 或 verifiable decryption 直接写成
`ZK-Invalidity`。具体方案仍须独立定义“解密失败/评价无效”的 NP relation，证明
completeness、soundness、adaptive zero knowledge，并证明其 publication branch
与 `Joint-AO^mob` 因子化。当前 `Adv_ZK-Invalidity` 继续保留为显式条件项。

### 28.61 投诉自由的 current-share resharing 候选

为绕开 Janus/hbACSS 的公开 complaint 缺口，当前优先候选改为投诉自由的
current-share resharing。修复和主动刷新使用同一个代际转换：每个 helper 用当前
份额作为新随机多项式的常数项，发送私有、可验证的 evaluation；接收者验证成功
后才签发 `READY`。验证失败只导致缺少 `READY`，协议不公开 `KEYREVEAL`、evaluation
opening 或 scalar blame。

对 `n=3f+2`、次数 `2f` 的当前分享 `F^r`，选出
`H subseteq P-{u}`，`|H|=2f+1`，并令

```text
f_h(X)=F^r(h)+sum_{k=1}^{2f} a_{h,k}X^k,
F^{r+1}(X)=sum_{h in H} lambda_h f_h(X).
```

helper 通过零知识 equality proof 证明 `f_h(0)=F^r(h)`；evaluation 通过 opaque
ACSS 私有交付；所有正确接收者使用同一个 `H` 和同一组 Lagrange 系数。于是
`F^{r+1}(0)=F^r(0)`，修复目标和其他正确节点共同进入下一代分享。安装时原子擦除
旧份额、当前 evaluation opening `rho_j^r`、helper 多项式系数、私有 evaluation
opening、pending plaintext 和端点密钥，只保留新份额、承诺、generation 与 frontier。

Pedersen 版本因此将当前隐藏状态写成
`(z_j^r,rho_j^r,C^r,r,T_j)`。其中 `rho_j^r` 让 helper 能证明当前 evaluation
commitment 与新多项式常数项承诺包含同一个 `z_j^r`；它本身不公开，但必须进入
`PECC` 和退休擦除语义。若删除 `rho_j^r`，协议只能公开 evaluation artifact、
公开 `z_j^r`，或引入未定义的 equality-proof witness。

这条路线把真正的难点从“如何零知识证明解密失败”转移为一个更清晰的
`Common-H` 接口：异步 withholding 下，所有正确节点必须最终选择同一组 helper，
且每个被选 helper 为每个正确接收者提供同一个承诺绑定的 evaluation。若某个
实现必须公开 scalar blame 才能完成这一点，它就不能作为本文的 opaque repair
实例。该路线因而可能缩短证明链，但没有自动得到一个现成构造；`opaque-ACSS`、
`PECC`、equality-proof simulation 和 generation-local mobile exposure 仍需逐项证明。

本候选的主要价值是结构性的：它把 `Adv_Complaint-Noninterference` 从一个需要
新型 `ZK-Invalidity` 的密码学假设，降为协议语法上的零项；剩余优势只来自交付、
证明、擦除、共同 helper 选择和代际绑定。相应的 go/no-go 条件和状态转移表已写入
定理稿 `19.62`。如果 current-share resharing 仍无法满足 `Common-H` 或必须保留
可组合的旧恢复状态，论文保留抽象 FGSR 主定理、Robust-Hitting、no-resurrection
和条件 AOR 实例，不把候选写成完成的长期安全协议。

### 28.62 APSS/hbACSS 对 Common-H 的证据裁决

APSS 的 ACSS 定义给出一个有用的局部接口：一个实例一旦由某个诚实节点完成，
所有诚实节点最终得到同一低次多项式的一致份额；其 VABA 阶段再对经过验证的
polynomial proposal 达成共同选择。这可以作为 `Common-H` 的候选传输基础。
APSS 还明确要求刷新后删除旧份额并支持 graceful exit，这与移动腐化下的状态
生命周期相容。

但 APSS 的 `GenZeroPoly` 会公开 `g^{p(i)}` evaluation commitment 和相应 DLEq
证明。对本文而言，这些不是普通 metadata；它们必须进入 typed-edge ledger，
并证明不能形成 scalar 或 aggregate-opening capability。因此首版只能复用 APSS
的 base ACSS/VABA 形状，移除公开 evaluation revelation，并加入
`f_h(0)=F^r(h)` 的 helper equality proof。

hbACSS 的 `OK/READY` 机制确实接近所需的 Common-H availability，但它的实际故障
路径是公开 `IMPLICATE -> SK -> share recovery`。这直接违反投诉自由候选的
scalar-free transcript 条件；其原始静态 secrecy 证明也不能替代 `PECC` 和
generation-local adaptive simulation。

因此当前底层裁决是：

```text
APSS base ACSS/VABA       -> Common-H 的条件证据
APSS GenZeroPoly 原样      -> 公开 evaluation，不能直接使用
hbACSS 原样                -> 公开 key-reveal，不能直接使用
```

下一步应构造 `C_CSR^opaque` 的适配接口并完成 adaptive、generation-labelled、
scalar-free transcript simulation；这比继续搜索新的 FL 基线更接近论文的核心
理论结果。

### 28.63 `C_CSR^opaque` 的正式接口

把投诉自由路线写成可验证的接口。对
`Q=(rid,c,r,T_req,C^r,u)`，helper `h` 的公开对象是

```text
Desc_h=(Q,C_h,pi_eq,h,AvailCert_h),
READY(Q,h,j),
```

而 `evaluation` 和本地 opening 只通过私有交付到接收者 `j`。接口需要满足：

- descriptor 绑定完整上下文、helper 身份和 generation；
- `pi_eq,h` 证明 `f_h(0)=F^r(h)` 且不公开 scalar；
- `AvailCert_h` 包含 `2f+1` 个非 target 的 `READY` 签名，因此至少有一个诚实节点
  完成本地验证；ACSS completeness 再将该完成事件传播到所有正确接收者；
- `READY` 只在本地验证成功后发布；
- transcript 不含 evaluation、解密钥、recovery point 或可重构组合；
- pending evaluation、buffer 和 endpoint key 都受 generation barrier 与 `PECC` 保护。

在 `P-{u}` 上运行 validated ACS，得到共同的有效 descriptor 集 `V`，再以确定性
规则取 `H=Canonical_{2f+1}(V)`。由 ACS agreement/validity/termination，加上每个
被选 descriptor 的 ACSS-complete 证据，可以条件证明所有正确节点得到同一个 `H`
和每个 `h in H` 的一致 evaluation。该证明只负责 Common-H；隐私终结仍由
scalar-free transcript、frontier absorption、原子擦除和 `Joint-AO^mob` 负责。

因此论文下一项正式证明是：

```text
ACS correctness + opaque ACSS completeness
    => Common-H Agreement + Common-H Availability
```

APSS 的 base ACSS/VABA 可以作为这一映射的候选来源，但 APSS `GenZeroPoly` 的
公开 `REVEAL(g^{p(i)},pi_i)` 必须删除或重新证明其不会形成 capability。该接口
闭合后，`Adv_Complaint-Noninterference` 从 wrapper 层消失，论文的条件 AOR 界只
保留 `C_CSR^opaque`、frontier、recovery-localization 和 `Joint-AO^mob` 项。

### 28.64 `EqProof^mob`：当前最小密码学证明缺口

Pedersen 版本的真正缺口不是“有没有一个 equality proof”，而是它能否适应长期
状态暴露。公开 statement 为

```text
(E_h^r,D_{h,0},C^r,C_h,Q),
```

helper 在 barrier 前被腐化时，模拟器必须给出与所有已发布 commitment 一致的
`(z_h^r,rho_h^r)`；barrier 后被腐化时，只能给出下一代状态或 tombstone，不能
恢复已擦除的 `rho_h^r`。因此 `EqProof^mob` 必须同时满足 statement binding、
adaptive simulation、关系 soundness 和 branch noninterference。

普通 Pedersen hiding 只能隐藏 commitment，普通 NIZK zero knowledge 也不自动提供
“公开 commitment 后再腐化”的 witness consistency。首版应把这项义务单独记为
`Adv_EqProof^mob`，并检查 dual-mode/equivocal commitment 与 simulation-extractable
proof 是否能在同一 labelled CRS 下提供它。若不能，保留 `C_CSR^opaque` 条件接口，
不把 equality proof 名称当作已经完成的自适应证明。

### 28.65 `EqProof^mob` 的本地文献裁决

Choudhuri 的 SE-NIZK 提供 `Setup/Prove/Verify/SimProve`、weak
simulation-extractability 和直线提取，可以作为 `R_eq` 证明系统的候选组件；但其
安全定理针对静态敌手和密文/PPE statement。它没有定义 helper 在 commitment
公开后被腐化、再经历擦除、随后只能返回 tombstone 的状态接口。

VSSR 提供 Pedersen commitment、evaluation witness 和 recovery verification，但其
安全游戏用每个 commitment 的 `compromise/contrib` 次数限制表达隐藏性，没有
`frontier`、generation barrier 或 post-erase corruption。因此 VSSR 能支持
`R_eq` 的代数形式，不能直接支持 `EqProof^mob`。

当前最小实例化目标是：

```text
dual-mode/equivocal commitment
 + simulation-extractable NIZK for R_eq
 + adaptive commitment state
 + PECC
 -> EqProof^mob
```

在这条联合接口完成前，`Adv_EqProof^mob` 保持显式优势项；不把已有
`SimProve` API 直接改名为本文的自适应长期安全证明。

### 28.66 `EqProof^mob` 的条件 hybrid

当前可以把 equality 层写成一条可审计的混合链：

```text
H0  真实 commitment、真实 R_eq proof、真实 endpoint state
H1  切换到 simulation/equivocation CRS
H2  用 SimProve 替换所有 R_eq proof
H3  对未暴露 commitment 做 adaptive equivocation，并按 barrier 回答 corruption
H4  用 PECC 模拟擦除后的 endpoint/buffer state
H5  拒绝错误 generation/frontier/context 的 proof 与 receipt
```

`H3` 需要单独的 `Adv_Equivocal-Opening^mob`：公开 commitment 已经固定后，敌手
才选择腐化时间，模拟器仍能在 barrier 前提供一致 `(z,rho)`，在 barrier 后不再
提供已擦除 `rho`。因此不能把它归入普通 Pedersen hiding。

定理稿 `19.68` 给出了条件优势界。其重要边界是：该 hybrid 只处理 state-layer
`R_eq`；如果 proof 分支读取客户端 ciphertext、aggregate descriptor 或 partial
decryption，仍必须进入 `Joint-AO^mob`。下一步是检查现有 dual-mode commitment 与
SE-NIZK 是否能满足这条 adaptive opening game。

### 28.67 Janus 对 `EqProof^mob` 的局部实例化

Janus 是当前最接近 `EqProof^mob` 的本地工作。它使用隐藏 Pedersen VSS、接收者
加密 evaluation、分享多项式擦除和可编程随机预言机，使模拟器能够在自适应腐化
后把公开 dummy ciphertext 一致地解释为被要求的状态。因而它可以为 `H1--H3`
提供局部路线。

但映射有明确边界：Janus 的证明对象是 DKG 分享，不是带
`(sid,ell,generation,frontier)` 标签的 current-share `R_eq`；其 secure erasure
没有覆盖 FGSR 的 pending evaluation、receiver buffer 和退休坐标；其 complaint
会让争议 ciphertext 公开可解密。因此 Janus 可以作为
`Adv_Equivocal-Opening^mob` 的条件 transport substitution，不能直接把该项归零，
更不能直接成为 `C_CSR^opaque` 的完整实例。

当前正式映射为：

```text
Janus adaptive commitment/encryption/erasure
  -> H1/H3 的局部证据
R_eq relation + labels + PECC + frontier absorption
  -> FGSR 仍需独立证明
```

下一步是把 Janus 的可后开口 ciphertext 状态改写成本文的 labelled endpoint game，
并检查在无 complaint 分支中是否仍能满足 `D5/D6`。如果不能，保留
`Adv_Janus-Equivocation`，不宣称具体实例闭合。

### 28.68 从候选协议到可投稿主定理：证明矩阵

实验基线已经在其他设备运行，本文的下一阶段不是继续增加 FL 数据集或协议
基线，而是把主张压缩为一条审稿人可以逐项检查的证明链。论文的核心对象仍是
异步联邦学习中的 aggregate-only secure aggregation；`FGSR` 只是满足该安全目标
的一种 state-layer 机制。

主定理所需的六个层次如下：

| 层次 | 学术问题 | 结果形式 |
|---|---|---|
| 正确性 | 共同 helper 集合是否存在且无需 target 参与 | `Common-H` 条件引理 |
| 访问结构 | 长期移动腐化下哪些恢复路径仍可达 | `Recovery-Closure` / `Robust-Hitting` |
| 异步状态 | 迟到、重放和退休后请求是否会复活旧能力 | frontier absorption 与 no-resurrection 必要性 |
| 状态隐私 | commitment、evaluation、endpoint 和 buffer 是否可被事后腐化模拟 | `RCL-Sim/AO`、`EqProof^mob`、`PECC` |
| 数据面隐私 | 多坐标 aggregate opening 是否泄露单项 key | `Joint-AO^mob` |
| 联合结论 | 上述条件是否共同推出客户端更新的 privacy finality | `F_PF^mob` 主组合定理 |

因此，当前论文的正式叙事是：

```text
异步安全聚合中的隐私并不在聚合输出时自动终止；
它只有在所有可达恢复路径的闭包被 frontier 永久封闭时才终止。
```

这一区分使本文区别于普通 forward secrecy。前向安全加密只限制未来密钥对旧
密文的解密；`Privacy-Finality` 还要求旧 share、evaluation、recovery transcript、
endpoint buffer 和跨坐标 proof 分支都不能在未来重新组合出 individual-key
capability。

当前条件主定理可写为：

```text
Adv_PF^mob
  <= Adv_RCL-Sim/AO
     + Adv_Joint-AO^mob
     + sum_r(Adv_ACSS-opaque^r
             + Adv_EqProof^mob(r)
             + Adv_PECC(r))
     + Adv_Common-H/Correctness
     + Adv_Generation/Context-Binding
     + Adv_Frontier-Absorption
     + Adv_Uncovered-Edge
     + negl(lambda).
```

这里的价值不在于把所有项形式上相加，而在于给出一个可证伪的边界：若某个
公开 complaint、scalar evaluation、partial decryption 或 proof-controlled branch
生成了新的单项恢复边，该边必须进入显式优势项，不能被普通 NIZK、Pedersen
hiding 或 forward-secure channel 一笔带过。

下一项研究工作固定为 `R_eq` 与 `Joint-AO^mob` 的联合审计：逐项给出 statement、
witness、公开 transcript、corruption oracle 和 data-dependent branch。只有在这
一审计完成后，才决定 `C_CSR^opaque` 是可以具体实例化的协议，还是应以“抽象
主定理 + sharp separation + 条件密码学接口”的形式投稿。动态委员会继续保留为
`Recovery-Closure` 的后续推论，不进入当前主定理。

### 28.69 `R_eq` 的两层含义与联合审计结论

审计首先修正一个不能继续保留的记号歧义。本文有两个不同的等式关系：

| 关系 | 证明内容 | 安全位置 |
|---|---|---|
| `R_eq^share` | helper 的 `f_h(0)=F^r(h)`，witness 为 `(z_h^r,rho_h^r,beta_{h,0})` | 状态层，进入 `EqProof^mob`、`PECC` 和 `RCL-Sim/AO` |
| `R_eq^agg` | 客户端 mask/key、密文、权重与 aggregate descriptor 的一致性 | 数据层，必须进入同一个 `Joint-AO^mob` challenge |

`R_eq^share` 可以成为 state-layer 对象的前提是：repair context 不读取 challenge
相关客户端密文，`READY` 只影响 repair acceptance，并且 proof 不依据隐藏 witness
选择 partial decryption、单项 ciphertext 或 recovery branch。它必须支持公开
commitment 后的自适应腐化，以及擦除 `rho_h^r` 后只返回下一代状态或 tombstone。

`R_eq^agg` 则不能被普通 equality-proof simulation 吸收。其 statement 读取
challenge ciphertext、权重或 aggregate context；其 proof、certificate 和
partial decryption 即使不公开明文，也可能区分等和但不同的 key vectors。因此
它们必须作为一个整体进入 `Joint-AO^mob`，不能逐坐标替换。

这一步得到的关键结论是：使用同一个 NIZK 库并不意味着只需要一个安全证明。首版
具体实例至少要分别提供：

```text
R_eq^share -> adaptive post-erase simulation + label binding + PECC
R_eq^agg   -> concurrent challenge-dependent simulation + Joint-AO^mob
```

若其中任一接口仍未闭合，论文仍可保留 `Privacy-Finality` 的抽象主定理、
`Recovery-Closure`/no-resurrection 下界和条件密码学实例，但不能声称已经完成
长期自适应的具体 FGSR 构造。这个区分是当前最重要的理论审计结果。

### 28.70 现有数据面文献的最终裁决

对本地转写文档逐项核对后，当前没有现成工作可以直接提供
`R_eq^agg -> Joint-AO^mob` 的提升：

- TACITA 的 modified STE 支持等和挑战、ciphertext-specific partial decryption 和
  对手选择的附加密文，但 `Cor` 在挑战前固定；原文明确指出自适应腐化版本不在
  讨论范围内。因此它是 `Static-AO` 的强基线，不是长期移动腐化的数据面定理。
- Choudhuri 等人的 SE-NIZK 提供 `SimProve`、提取和 ciphertext/PPE 关系证明，
  但主安全定理针对 static PPT adversary。它没有回答 commitment 已公开后再腐化、
  擦除 endpoint state、并发 repair context 和 proof-controlled publication branch。
- Janus 能支撑局部 adaptive equivocation/erasure，但其目标是 DKG 分享，不能替代
  aggregate-only `Joint-AO^mob`。

因此首版论文必须在两条路线中择一：

```text
路线 A：构造新的 adaptive lifting，补齐 Joint-AO^mob；
路线 B：保留 Joint-AO^mob 为显式接口，并把静态到长期模型的分离定理作为贡献。
```

路线 B 不是退让，而是一个可证伪的理论结果：它证明即使静态 aggregate opening
和普通 proof simulation 都成立，只要缺少自适应状态暴露、frontier 和 recovery
closure，privacy finality 仍不成立。当前应先完成路线 B 的严格主定理与匹配攻击，再
评估路线 A 是否值得引入新的门限加密组件。

### 28.71 静态聚合安全到长期隐私终结的匹配攻击

为了让分离结果不是术语比较，本文加入一个最小反例。设协议使用固定门限公钥，
客户端分别加密 `k_1,...,k_m`，协议只打开 `K=sum_u k_u`。在静态 aggregate-opening
游戏中，敌手只能在 challenge 前固定至多 `f` 个腐化节点，因此两个等和但不同
目标分量的向量 `K_0,K_1` 对敌手不可区分。

在长期移动模型中，敌手可以选择三个不相交的节点集 `B_1,B_2,B_3`，大小分别为
`f,f,1`，每次只腐化一个集合并在下一次移动前释放它。三波之后累计暴露
`2f+1=q_dec` 个旧份额；在 `n=3f+2` 下这些节点总能放入委员会。若没有
state-complete refresh 和 frontier 擦除，敌手即可重构旧解密钥并打开目标客户端
密文。即使固定密钥被刷新，只要退休坐标保留可恢复旧 share 的 recovery object，
同样的攻击也可以在未来调用该对象。

因此存在：

```text
static aggregate opening secure
    + protocol correctness
    + instantaneous corruption bound
    -> privacy finality 仍然失败
```

这证明普通 forward secrecy、静态 aggregate encryption 或一次性的 threshold
decryption 定理都不能单独承担本文的主结论。本文真正新增的条件是：长期暴露视图
必须由 `Joint-AO^mob` 覆盖，且所有退休坐标的恢复闭包必须由 `Recovery-Closure`
和 frontier absorption 封闭。

### 28.72 `F_PF^mob`：把聚合终结与隐私终结放进同一功能

现有 `F_AWF` 只描述 frontier 和 capability 的吸收态，`G_RPTA^sel` 只描述选择性
挑战。论文需要一个明确的组合接口 `F_PF^mob`，其安全范围是一个固定目标会话、
一个固定授权聚合描述符和一次 challenge；敌手可以自适应移动腐化、延迟消息、
恢复节点状态，但不能查询任意历史数据库记录。这与用户级 adaptive-query 工作
是不同问题。

对

```text
D_sid = (S_sid, w_sid, H_ct, H_out, tag_sid)
```

功能维护 `phase in {Open, Closed, Retired}`、单调 frontier、`X_hist` 和当前状态。
核心接口为：

```text
Bind(sid,D_sid) -> CC_sid
Submit(sid,u,x_u) -> accept/reject
OpenAggregate(sid,CC_sid) -> sum_u w_u*x_u
Retire(sid,PC_sid) -> PF_sid
Publish/Process(Q,m,T_local)
Recover(rid,target,T_req,opaque_state)
Corrupt(i,t) -> permitted leakage
```

`CC_sid` 只固定参与集合、权重、ciphertext digest 和授权 aggregate；
`OpenAggregate` 只返回加权总和。`PF_sid` 则要求退休集合满足
`A_sid in H_b(Gamma_dec)`，并把 frontier 变成不可回滚的退休状态。

安全实验中，敌手提交两组 `X_0,X_1`，满足：

```text
sum_u w_u*x_{u,0} = sum_u w_u*x_{u,1}.
```

挑战者随机选择 `b` 执行功能，并继续回答合法的 corruption、`Publish/Process`、
retirement 和 recovery 事件。视图包含 `CC_sid`、共同聚合、`PF_sid`、
`X_hist`、擦除后的当前状态和恢复转录；数据相关 ciphertext、certificate、
`R_eq^agg` 及 partial decryption 由同一个 `Joint-AO^mob` challenge 生成。

功能的关键语义是：退休前 send event 已公开的 key/point 进入 `X_hist`，不能被
后续擦除撤销；退休后只能返回当前代状态和 tombstone，不能恢复旧 share、opening、
endpoint key、pending plaintext 或 recovery-complete old state。`F_AWF` 只负责
控制面 capability absorption，`F_PF^mob` 进一步规定 aggregate-only 数据面和未来
全状态暴露，因此前向安全或普通 `F_AWF` 都不足以实现它。

本定义不把 `CapSafe` 写成 query admissibility。游戏只限制瞬时腐化数、每个
generation 的外生 exposure budget、终端 residual-set budget，以及消息标签和
frontier 的语法有效性；真实 `Corrupt/Recover` 若返回旧 capability，仍必须进入
view，并使协议承担相应的安全优势或失败项。`CapSafe` 是 `Recovery-Closure` 的
证明结论，不是实验入口处预先假设的条件。

对每个 coordinate/generation，暴露统一按以下方式记账：

```text
pre-frontier state -> X_hist^r(B_{ell,r})
post-frontier current state -> X_current(U_ell)
challenge-dependent branch -> DataView_b
other capability edge -> Adv_Uncovered-Edge
```

这样可以避免一个循环证明：不能因为某个对象会破坏 privacy finality，就把产生
该对象的腐化或恢复 query 定义为“不合法”。

### 28.73 FGSR wrapper 与 `F_PF^mob` 的接口闭合

FGSR 的 `ReshareAggregate(Q,H)` 只是在 helper 多项式之间做 Lagrange 组合，不能被当成
客户端更新的 aggregate release。为了避免同名操作偷换，论文将其称为
`ReshareAggregate`，并采用如下映射：

```text
F_PF Bind          -> ACS context + unique CC_sid
F_PF Submit        -> client encoding + Joint-AO^mob challenge
F_PF OpenAggregate -> aggregate ciphertext + authorized partial decryption
F_PF Retire        -> Retire(c,T*) + atomic puncture/erase + PF_sid
F_PF Publish       -> AOR Publish, including send-time KEYREVEAL exposure
F_PF Process       -> AOR Process_i + local frontier check
F_PF Recover       -> Authorize -> ParallelReshare -> ReshareAggregate -> Install
F_PF Corrupt       -> Expose_i + mobile corruption oracle
```

这给出一个条件 wrapper theorem：若 `Joint-AO^mob`、`Common-H`、AOR-1--AOR-5、
typed capability isolation、state-complete erasure 和
`A_sid in H_b(Gamma_dec)` 均成立，则组合协议实现 `F_PF^mob`，误差项为：

```text
Adv_Joint-AO^mob
  + sum_r Adv_AOR^mob(r)
  + Adv_Common-H/Correctness
  + Adv_Recovery-Localization
  + Adv_Frontier-Use
  + Adv_Context/Binding
  + negl(lambda).
```

当前最重要的接口结论是：FGSR 负责恢复闭包和退休吸收，`Joint-AO^mob` 负责
aggregate-only 数据面，`CC_sid` 负责唯一聚合上下文；三者不能由一个普通 VSS、
一个 threshold decryption theorem 或一个 `SimProve` API 互相替代。

### 28.74 论文结果层次与投稿边界

正文应按理论强度组织，而不是按协议模块组织：

1. `Robust-Hitting`：给出退休集合与访问结构之间的必要/充分刻画；
2. `Recovery-Closure` 与 causal frontier：证明恢复路径和异步迟到消息如何改变
   隐私访问结构，并给出 no-resurrection 必要性；
3. `Static-AO` 分离定理：用三波 `f,f,1` 移动腐化攻击证明静态聚合安全不蕴含
   长期隐私终结；
4. FGSR 条件组合定理：在 `Joint-AO^mob`、AOR 和 Common-H 下实现 `F_PF^mob`；
5. 具体密码学审计：明确 TACITA、SE-NIZK、Janus 和 hbACSS 的局部可复用性质及
   尚未关闭的优势项。

因此，本文即使暂时没有完成新的 adaptive opaque transport，也仍然有清晰的
学术贡献：访问结构刻画、异步 no-resurrection 下界、静态到长期模型的匹配分离，
以及一个把 aggregate-only 数据面与 recovery-closed 状态面组合起来的条件编译
定理。具体构造只有在 `Adv_Joint-AO^mob` 和 `Adv_AOR^mob` 被进一步归约后，才可
从“条件协议框架”升级为“具体长期安全聚合协议”。

### 28.75 恢复闭包感知的退休判据

前面的 `Robust-Hitting` 只针对直接 capability 集合。对退休 coordinate `c`，还需
把退休之后仍可由恢复关系生成的能力纳入访问结构。令 `A` 是退休证书覆盖的节点，
`B` 是退休前已暴露的能力集合，`R_c` 是退休后仍能通过合法恢复边重新生成旧能力
的节点集合，则有效旧能力集合为：

```text
E_c(B,A) = B union R_c union (P - A).
```

在 capability ledger 完整且每个 individual opening 都需要某个
`D in Gamma_dec^cap(c)` 时，privacy finality 等价于：

```text
for every D in Gamma_dec^cap(c),
    D is not a subset of E_c(B,A).
```

对 `|B|<=b` 的最坏暴露，这等价于：

```text
|D intersection (A - R_c)| > b.
```

因此 `Robust-Hitting` 只有在 `R_c=emptyset` 时才是充分条件。普通 VSSR/DPSS
如果保留可重用的 `sid`-local recovery state，或者保留能够重新生成该状态的全局
恢复权，即使删除 direct share、发布单调 tombstone，也可能有 `R_c != emptyset`。
此时其原始 correctness 和 static sharing security 仍可成立，但不能实现本文的
`F_PF^mob`。

`AOR-5` 和 state-complete erasure 的作用正是把 `R_c` 归零：所有退休后的
`Recover`、`Install`、`Use`、`PartDec` 和 `KEYREVEAL` 边必须被 frontier 拒绝，
退休 coordinate 的恢复输入也必须从未来状态中消失。由此，本文的理论分工可以
压缩为：`Robust-Hitting` 处理“证书覆盖了哪些节点”，`Recovery-Closure` 处理
“这些节点还能否被恢复边重新获得”，而 `AOR-5` 是二者在完全异步状态机中的连接。

这给 VSSR/DPSS 的黑盒审计提供了单一判据：若不能证明退休 coordinate 的
`R_c=emptyset`，就只能作为恢复正确性基线，不能作为 FGSR 的长期隐私实例。

### 28.76 退休闭包的接口审计矩阵

`R_c=emptyset` 需要逐类关闭恢复边，而不是由一个 tombstone 统称保证：

| 对象/事件 | 可能的旧能力路径 | 必须关闭的接口 | 未关闭时的项 |
|---|---|---|---|
| 旧 direct share 或 recovery share | 未来腐化直接读取标量 | state-complete erasure、`PECC` | `Adv_Recovery-Localization` / `Adv_PECC` |
| pending repair payload、channel buffer | 未来 endpoint 暴露后解密旧点值 | `AVSS-opaque`、post-erasure channel confidentiality | `Adv_ACSS-opaque` / `Adv_PECC` |
| 迟到 `Recover`/`Install` | stale 消息重新安装旧状态 | AOR-5、generation binding、frontier-bound install | `Adv_Frontier-Use` / `Adv_Generation-Binding` |
| 持久 global recovery authority | 未来重建 retired local state | coordinate puncture 或 recovery-state localization | `Adv_Recovery-Localization` |
| 公开 proof/receipt metadata | 隐藏 witness 选择标量分支 | typed capability isolation、proof noninterference | `Adv_Uncovered-Edge` |
| aggregate ciphertext/partial decryption | 数据面打开单个客户端值 | 一个联合 `Joint-AO^mob` challenge | `Adv_Joint-AO^mob` |
| 退休前公开 reveal | 该能力已经在退休前发送 | `Publish` 时写入 `X_hist` | 已允许泄漏，不重复计入 |

若上述每一行均被证明，且跨 coordinate 转换被拒绝或纳入同一个
`Joint-AO^mob` challenge，则第一版 capability universe 中不存在未覆盖的退休后
恢复边，因而 `R_c=emptyset` 且 `Adv_Uncovered-Edge=0`。这就是 Theorem 44 从
抽象判据进入具体 `C_CSR^opaque`、`PECC`、equality proof 和 frontier-bound
`Use/PartDec` 接口的最小证明清单。

当前候选的保守裁决如下：

| 接口 | 可复用的局部证据 | 仍未关闭的部分 |
|---|---|---|
| `AVSS-opaque` | APSS/hbACSS 的私有交付和异步 availability | recovery/evaluation transcript 的 scalar isolation |
| `PECC` | Janus 的擦除语义和 ephemeral transport | endpoint buffer、pending repair state 的未来暴露 |
| `EqProof^mob` | Janus equivocation、Choudhuri SE-NIZK simulation/extraction | 公开 commitment 后腐化、label、post-erase consistency |
| frontier-bound `Use/PartDec` | FGSR 抽象状态机 | 具体 capability 必须绑定 frontier |
| coordinate-local recovery authority | FGSR 的 puncture/state shape | 现有 VSSR/DPSS 未提供黑盒实例 |
| `Joint-AO^mob` | TACITA 的 static aggregate opening | adaptive post-challenge lifting |

所以首版具体路线只能写成条件 `C_CSR^opaque` transport：它显式依赖 `PECC`、
`EqProof^mob`、coordinate-local retirement 和 frontier-bound data-plane use。APSS、
hbACSS、Janus、TACITA 只能作为局部组件和归约目标，不能被写成已经完成的长期
自适应安全实例。

### 28.77 首版 `C_CSR^opaque` 的状态映射

首版只考虑独立 coordinate `c=(sid,ell)`。协议状态分为：

```text
PersistentLive_i(c) = (T_i(c), z_i(c), C_i(c), instance_i(c))
PublicRepair(Q)    = (Q, H, {C_h}, {pi_eq,h}, READY, AvailCert)
Pending_i(Q)       = (Q, ct_i, ek_i, plaintext_i, verified_i)
Retired_i(c)       = (T_i(c), C_i(c), tombstone_i(c))
```

每个 `Q` 还必须携带 coordinate-local 的

```text
O_c = (prefix_c, rank_c(rid), parent_c, T_req, OrderCert_c)
```

`OrderCert_c` 证明 `rid` 在同一 coordinate 的唯一实例序位置；retirement 是同一
序列中的后续事件，并支配所有尚未生效的 pending instance。它不是全局 epoch，也
不要求不同 coordinate 同步。

其中 `PersistentLive` 只保留 current share、commitment 和实例序证书；公开 repair
transcript 只含标签、承诺、证明和 availability metadata；`Pending` 只在私密
交付到 `Install` 或取消之间存在；退休后只保留 frontier、commitment 和 tombstone。
退休状态中不能留下任何可作为旧 coordinate 恢复输入的对象。

状态转换固定为：

```text
Authorize(Q)       -> live、frontier 和 instance order 检查
DeliverVerify(Q)   -> label、ciphertext、EqProof 检查后创建 Pending
Install(Q)         -> 聚合 helper polynomial，更新 current share/commitment 并擦除旧状态
CancelOrRetire(Q)  -> 擦除 Pending；退休后只保留 Retired state
Process/Recover    -> stale、retired 或乱序请求拒绝
Use/PartDec        -> 必须使用认证的当前 frontier 和 live coordinate
```

所有检查都必须在 authorize、delivery、install 和 use 阶段执行；只在 repair 开始
时检查 frontier 无法防止并发 retirement 下的迟到安装。若该状态映射的每一行都
满足 `AVSS-opaque`、`PECC`、`EqProof^mob`、AOR-5、coordinate-local recovery
authority 和 `Joint-AO^mob` 要求，则 Theorem 44 的 `R_c=emptyset` 条件成立。
这里仍然是条件实例化：状态名称本身不证明擦除、信道安全或恢复权穿孔。

### 28.78 单次 `C_CSR^opaque` 模拟器

对一个 repair context `Q`，模拟器只获得 `Q`、共同 helper 集合、公开承诺、允许的
`B_r` 暴露状态、`X_hist`、残留状态和 frontier。混合顺序固定为：

```text
S0  真实 labelled C_CSR；
S1  用 EqProof^mob 模拟 R_eq^share；
S2  用 AVSS-opaque 模拟未暴露的私有 evaluation 和 endpoint state；
S3  在 barrier 后用 PECC 模拟 Pending/buffer，只保留 next state 或 tombstone；
S4  用 Common-H 和 affine coupling 保持 READY、certificate 和安装关系；
S5  拒绝 stale/retired 的 Recover、Install、Use、PartDec，并显式计入未覆盖边。
```

允许的 pre-barrier 腐化所读取的 `y`、opening 或 endpoint key 直接进入
`X_hist^r(B_r)`；模拟器不获取任何未暴露的 evaluation、`rho_h^r`、临时密钥或
helper polynomial 系数。由此得到单次 repair 的条件界：

```text
Adv_OneStep-C_CSR^r
  <= Adv_EqProof^mob(r)
     + Adv_ACSS-opaque^r
     + Adv_PECC^r
     + Adv_Common-H/Correctness^r
     + Adv_Pending-Order^r
     + Adv_Generation-Binding^r
     + Adv_Frontier-Use^r
     + Adv_Uncovered-Edge^r
     + negl(lambda).
```

该命题是首版具体构造的最小密码学证明入口。它不把 APSS、hbACSS、Janus 或普通
Pedersen proof 自动视为满足前提；只有在所有并发 context 都完成这条 reduction 后，
`C_CSR^opaque` 才能从条件接口升级为具体实例。

### 28.79 Pending 取消与退休顺序

同一 coordinate 的 repair 和 retirement 不能依赖各节点本地的消息到达顺序。需要由
validated agreement 给出共同的实例序 `prec_c`：

```text
Install(rid) effective only if rid precedes Retire(c,T*) in prec_c;
CancelOrRetire(c,T*) erases every pending rid not already effective;
after Retire(c,T*), no pending rid transitions to PersistentLive(c).
```

如果 `Install` 在共同序中先于 `Retire`，它只产生带新 generation label 的 current
state，并在随后退休时一起关闭；如果 `Retire` 先发生，pending output、plaintext、
receiver key 和 verification buffer 全部擦除，不能安装。局部节点收到消息的顺序
不能改变这个共同序。

因此，pending 分支的额外失败项是：

```text
Adv_Pending-Order
+ Adv_Frontier-Use
+ Adv_Generation-Binding
+ Adv_PECC
+ Adv_Uncovered-Edge
```

这一步补齐了“只在 `Authorize` 检查 frontier”留下的并发缺口。它仍是条件状态机
引理，具体实现必须提供 instance-order certificate、原子擦除和 PECC。

### 28.80 `OrderCert_c` 的序列一致性接口

现有 helper-set `ACS^-` 只负责产生共同的 `H`，不能自动决定 repair 与 retirement
的相对顺序。首版需要一个 coordinate-local 的 `SeqACS_c`：

```text
e = (c, kind, rid, Q_digest, T_req, parent_c)
SeqACS_c.propose(e) -> append-only prefix or reject
OrderCert_c = (c, parent_c, k, e_digest, quorum_signature)
```

它必须满足：

- sequence agreement：所有正确节点对同一 rank 接受同一 event；
- prefix consistency：不同 accepted prefix 只能是扩展关系；
- validity：证书绑定完整 request、frontier 和 event kind；
- termination：满足活性条件的 event 最终被排序或明确拒绝。

在 target-excluded 的 `3f+1` 个参与者中，首版可用 `2f+1` quorum，并要求正确
节点在同一 `(coordinate,parent,rank)` 上至多签署一个 event。由此，`OrderCert_c`
的失败项为：

```text
Adv_Order-Agreement
+ Adv_Order-Prefix
+ Adv_Order-Validity
+ Adv_Order-Termination
+ Adv_Order-Certificate-Soundness
```

关键边界是：Theorem 33 的 helper-set agreement 只能证明共同 `H`，不能证明
`Install(rid)` 与 `Retire(c,T*)` 的相对顺序。因此 `SeqACS_c` 或等价的 ordering
proof 是 `D1/D6` 的真实前提，不应隐藏在普通 ACS agreement 中。

### 28.81 实验之后的理论主线：从集合共识到隐私终结

实验只负责展示长期移动腐化下的现象、比较现有方案的失效模式，并不承担核心安全
结论。本稿在实验之外的下一步是完成一个严格的理论链：

```text
SetACS insufficiency
 -> minimal SeqACS_c / OrderCert_c
 -> one-step C_CSR^opaque simulation
 -> Recovery-Closure composition
 -> Privacy-Finality under Joint-AO^mob
```

第一步应成为正文中的独立分离结果。Juno 的 AVC、APSS/hbACSS 的 ACS/ACSS 层以及
DyCAPS 的 epoch handoff 都能产生共同值、共同集合或共同 epoch 输出，但都没有向
wrapper 暴露 repair 与 retirement 的 causal acceptance、parent 和 frontier 关系。
因此，把无序事件集合按 digest 排序不能实现 `D1/D6`：它只改变展示顺序，不能判断
pending repair 在退休前是否已经生效。

这条分离结果的价值在于，它把论文的创新点从“又一个异步 secure aggregation 协议”
提升为一个更基本的问题：**在长期移动腐化下，聚合正确性所需的异步集合共识，何时
足以支持隐私状态的最终关闭；何时必须升级为带恢复闭包语义的事件序列共识。**

后续证明按以下三个定理组织：

1. `SetACS` 到 `SeqACS_c` 的不足性命题及 `OrderCert_c` 的最小充分接口；
2. 带该接口的单次 `C_CSR^opaque` 模拟定理，显式保留
   `EqProof^mob`、`PECC`、opaque ACSS、generation binding 和 frontier-bound use
   的优势项；
3. 沿 coordinate-local prefix 的 `Recovery-Closure` 组合定理，最终得到
   `F_PF^mob` 的 privacy-finality 结论。

首版论文不再扩张到动态委员会、packed repair、恶意梯度或自适应查询数据库。若第
一个定理证明在目标网络模型下无法得到非平凡的 `SeqACS_c`，它本身就构成论文的
理论边界；若可以得到，则第二、三项决定是否能形成完整的 FGSR 实例。下一次实际
工作是写出两个相同 ACS 集合输出、但要求不同 pending 处理的异步执行，并将其正式
化为 Proposition 49 的证明，而不是继续增加实验基线。

### 28.82 `SetACS`/`SeqACS_c` 的正式观察接口

为避免把“可以对集合排序”和“可以证明事件先后”混为一谈，首版采用如下接口区分：

```text
SetACS_c(proposals) -> S subset of E_c
SeqACS_c.propose(e,parent_c) -> (prefix_c,OrderCert_c)
```

`SetACS_c` 只向 wrapper 暴露共同事件集合、公开 descriptor 和 validity evidence；
它不暴露事件进入共同状态的 causal position。`SeqACS_c` 还必须让证书绑定 parent、
rank、完整 request digest 和 frontier context，并满足：

```text
Install-before-retire: 退休前已经生效的合法 repair 不被当作 stale；
No-install-after-retire: 退休后才被接受的 repair 不能进入 live state。
```

令 `e_R` 为 repair，`e_T` 为 retirement，并构造两个都输出
`S={e_R,e_T}` 的异步执行：执行 `E_pre` 中 `e_R` 在 `e_T` 前生效；执行 `E_post`
中 `e_T` 先关闭 frontier，`e_R` 的最后一条交付随后才到达。对只观察 `S` 的 wrapper，
两次执行输入相同；但 `E_pre` 要求保留/安装 repair，`E_post` 要求擦除 pending repair。
因此 digest 排序只能产生固定展示顺序，不能替代 `OrderCert_c`。

该形式化给 Proposition 49 增加了两个必要的语义前提：repair validity/liveness 和
retirement completeness。没有前者，wrapper 可以通过永远取消 repair“满足”退休安全；
没有后者，wrapper 可以通过永远接受旧 repair“满足”修复可用性。论文的分离结果要求
两者同时成立，因而真正隔离的是 causal event order，而不是任意的列表排序。

### 28.83 有序单次归约：把 `Adv_Pending-Order` 拆开

在 `OrderCert_c` 已经验证、`CancelOrRetire` 与 generation erase 共用一个原子屏障的
条件下，单次 `C_CSR^opaque` 的失败项写成：

```text
Adv_EqProof^mob
+ Adv_ACSS-opaque
+ Adv_PECC
+ Adv_Common-H/Correctness
+ Adv_Order-Agreement
+ Adv_Order-Prefix
+ Adv_Order-Validity
+ Adv_Order-Termination
+ Adv_Order-Certificate-Soundness
+ Adv_Atomic-CancelOrRetire
+ Adv_Generation-Binding
+ Adv_Frontier-Use
+ Adv_Uncovered-Edge
```

这一步把原来笼统的 `Adv_Pending-Order` 拆成两类可审计问题：`SeqACS_c` 是否给出
唯一、可扩展且绑定 frontier 的 prefix；以及退休屏障是否确实擦除了所有不先于
退休生效的 pending instance。前者是异步共识/证书问题，后者是状态擦除与密码学
暴露问题，二者不能由同一个“frontier check”措辞代替。

因此，下一项具体证明不是继续设计 FL 聚合流程，而是完成 Proposition 50 的两个
局部归约：先证明 certificate chain 不会产生 fork，再证明 barrier 后模拟器不需要
任何未暴露的 evaluation、endpoint key 或 helper polynomial。只有这两步完成后，才
进入沿 `Recovery-Closure` 的多次 repair 组合。

### 28.84 最近候选：连续 ACS slot，而不是直接复用 Turritopsis

本地审计发现 Turritopsis 是目前最接近 `SeqACS_c` 的公开路线：它连续执行
`ACS[c,r]`，把每个共同 ACS 输出作为 block，并在配置内形成有序交易序列。它说明
“集合共识加外部顺序上下文”可以产生序列语义，但它本身仍不满足本文接口：checkpoint
按一组 block 生成，不是每个 coordinate-local repair/retirement event 的
`OrderCert_c`；同时其移动腐化和 key refresh 与配置更替绑定，不覆盖固定委员会的
长期移动暴露模型。

因此下一步构造目标改为 `SeqACS^slot`：

```text
P_0 = coordinate genesis
S_k = ACS_c(k, parent=parent_digest(P_{k-1}))
E_k = Canonicalize(S_k)
P_k = P_{k-1} || E_k
OrderCert_c(k) = (c,k,parent_digest,event_digest,frontier_context,signature)
```

这里的关键不是对单个 ACS 集合做 digest 排序，而是把 parent 作为下一 slot 的输入，
只有共同 slot 决定后才推进 prefix，并为该决定签发可转移证书。需要证明的性质是
slot agreement、prefix consistency、event validity、generation binding、无跳 slot
终止和移动 signer exposure 下的证书 soundness。

同一 slot 同时包含 repair 与 retirement 时，协议必须公开规定其序列语义；该规则
直接定义 `Install-before-retire` 与 `No-install-after-retire`，不能交给本地消息到达
顺序。若 `SeqACS^slot` 成立，它可以填充 Proposition 50 的 ordering 部分，但不
自动解决 `PECC`、opaque delivery 和 `Joint-AO^mob`。

### 28.85 `SeqACS^slot` 的条件定理

将候选写成独立定理：假设每个 slot 的 ACS 满足 agreement、validity、termination，
并且 slot admission 保证每个 live event 最终进入某个 slot，或得到带理由的认证拒绝。
每个 proposal 绑定 coordinate、rank、parent context、完整 request、generation 和
event kind；canonicalization 确定且去重；正确 signer 对同一 slot parent 至多签发一
个证书；证书机制在移动 signer state 逐代暴露时仍保持 soundness。

则得到 `SeqACS^slot` 的 sequence agreement、prefix consistency、validity 和
termination，失败优势为：

```text
Adv_SlotACS-Agreement
+ Adv_SlotACS-Validity
+ Adv_SlotACS-Termination
+ Adv_Slot-Admission
+ Adv_Canonicalization
+ Adv_Parent-Binding
+ Adv_Certificate-Soundness
+ Adv_Mobile-Signer-Exposure
```

其中 `Adv_Slot-Admission` 不能从普通 ACS validity 推出：它负责防止 retirement 被
永久遗漏或被无认证替换。`Adv_Mobile-Signer-Exposure` 也不能被普通 threshold
signature unforgeability 覆盖，因为固定委员会的签名状态可能跨 generation 累积暴露。
该条件定理如果成立，就能替换 Proposition 46 中笼统的 `Adv_Pending-Order`，但不
会自动解决 `PECC`、opaque delivery 或 `Joint-AO^mob`。

### 28.86 前向安全阈值签名的准确位置

Libert--Yung 的前向安全阈值模型明确使用逻辑 period、`Update` 和当前 share 暴露
查询，并要求目标 period 的累计暴露份额低于解密阈值。这个结构可以启发
`OrderCert_c` 的签名层：把 coordinate-local slot rank 当作逻辑 period，在 prefix
推进后删除旧 rank 的 signing state，并拒绝滞后节点继续签署旧 rank。

但这只能处理 `Adv_Mobile-Signer-Exposure`：

```text
forward-secure threshold signing -> 旧 OrderCert 不可伪造的候选
forward-secure signing alone     -> 不等于 PECC、AOR-5 或 Joint-AO^mob
```

它不能删除 repair evaluation、endpoint key、recovery authority，也不能阻止聚合
certificate/partial decryption 成为旧 coordinate 的开启路径。因此本文的密码学分工
固定为：`FSig_c`（若能完成异步 rank 映射）保护 ordering certificate，`PECC` 保护
退休后的状态暴露，`Joint-AO^mob` 保护 aggregate-only 数据面；三者不能合并成一个
“前向安全”假设。

### 28.87 `Adv_Slot-Admission` 的独立分离

普通 ACS 的 agreement、validity、termination 都不保证某个具体 retirement event 最终
被纳入。一个正确节点提出合法 `e_T`，其他节点提出不同的合法 descriptor；ACS 可以在
所有节点产生相同输出、每个 slot 都终止、每个输出都满足正确提案数量的同时一直遗漏
`e_T`。只要存在新的合法 repair/no-op proposal，后续 slot 可以重复这个执行。

因此需要独立的 admission 接口：

```text
Admit_c(e) -> AdmissionCert_c(e)
SlotACS_c(k,parent,AdmissionCerts) -> E_k or RejectCert_c(e,reason)
```

`AdmissionCert_c` 必须让 retirement 在有限 slot 中被纳入，或得到可转移的拒绝证书；
否则它会无限停留在 pending，违反 privacy finality。单纯收集 endorsement 也不够，
除非 slot 决策规则把该 endorsement 解释为 priority constraint。这是独立的
ordering/liveness 原语，不能从 ACS validity 或普通 threshold signature soundness
自动推出。

### 28.88 普通阈值签名的移动腐化攻击

令 `q_sig=2f+1`，委员会成员长期持有同一 verification key 下的 signing share。即使
敌手每个 interval 只暴露 `t` 个新节点，且始终满足瞬时腐化上限，经过
`ceil(q_sig/t)` 个 interval 后即可累计获得 `q_sig` 个 share，并离线伪造任意旧
`OrderCert_c`。这不会恢复任何 repair 明文，却足以伪造 D1/D6 所依赖的排序、安装或
取消授权。

因此普通 threshold signature 不能承担 `Adv_Mobile-Signer-Exposure`。只有 rank-specific
的 forward-secure signer state 才可能阻断这条攻击，而且还必须处理异步节点处于不同
rank 时的混合状态：旧 rank 的签名请求要被拒绝，旧 share 要确实擦除，晚到证书不能
重新打开已关闭 prefix。`FSig_c` 仍只是条件候选，不是现成组件的直接替换。

### 28.89 `FSig_c` 的异步 mixed-rank 条件

标准 forward-secure primitive 假设全局 period 单调推进，而本协议中不同节点可能处于
不同 slot rank。对节点状态 `(r_i,sk_i^{r_i},P_i)`，需要满足：

```text
Sign_i(k,e)       -> 只有 k=r_i 且 e 扩展 P_i 时允许
Accept_i(C_k)     -> 只有 C_k 扩展 P_i 且 rank 不倒退时允许
Update_i(k)       -> 原子安装 C_k、推进 rank、擦除旧 signing state
LateCert_i(C_j)   -> j<r_i 且不在已认证 prefix 中时拒绝
```

并定义 `E_{c,k}` 为 rank `k` 的 signing state 在本地擦除前被读取的节点集合，要求
`|E_{c,k}|<q_sig`。这不是时间窗口，而是以本地 erase 为边界；一个永远落后的节点
不能被证明成已经完成更新。

在这些条件下，`FSig_c` 才能给出 mixed-rank signer soundness：同一 rank 不出现两个
冲突证书，晚到旧证书不能重新打开已关闭 prefix。其失败项包括
`Adv_FSig-Soundness`、`Adv_Parent-Binding`、`Adv_Rank-Transition`、
`Adv_Rank-CatchUp`、`Adv_Late-Certificate-Rejection` 和
`Adv_Mobile-Signer-Exposure`。

这个条件也暴露了新的理论边界：不能因为一个节点完成 `Update` 就宣布 rank 已关闭；
要么把每个 rank 的累计暴露上界作为敌手模型的一部分，要么构造 collective erase
certificate。后者本身又会回到 `Slot-Admission` 与 privacy-finality 证明，不能用
普通 forward-secure key update 一笔带过。

### 28.90 主线修正：首篇不需要永久可验证的 `FSig_c`

上面的累计腐化攻击针对的是更强接口：未来无状态验证者仅凭公钥仍接受旧
`OrderCert_c`。首篇固定委员会并不需要这种 timeless certificate。节点已有单调 prefix
和 frontier，因此排序证书采用状态相对接受：parent 必须等于本地 current head，rank
必须是下一位置，事件必须处于 live frontier，且不能跨越已经接受的 retirement。

退休后即使敌手最终获得足够 signing shares 并伪造旧证书，节点也会因为 parent/rank
或 frontier 不匹配而拒绝。未完成退休的节点仍属于 Theorem 44 的 `P-A`，已经计入
恢复闭包；伪造证书只有在让 `A` 中节点回滚或复活旧状态时才新增攻击能力，而这正是
`AOR-5`、frontier-use 和 state-recovery rollback 的失败事件。

因此首篇密码学分工修正为：

```text
live-rank quorum authentication -> 排序决定在当前 rank 的真实性
monotone prefix + AOR-5          -> 退休后旧证书失效
PECC                             -> 退休后敏感状态不可恢复
Joint-AO^mob                     -> aggregate-only 数据面
```

`FSig_c` 降为扩展：只有要求动态成员、无状态验证者或永久公开审计时才需要。这个修正
消除了“必须先证明所有 signing share 已擦除，才能相信擦除证书”的循环，也使论文重新
聚焦安全聚合的 recovery closure，而不是发展一套新的前向安全阈值签名协议。

### 28.91 Sticky retirement admission

单次 ACS 不保证纳入某个特定 retirement，但不需要为此再发明一个 agreement primitive。
正确节点收到合法且仍 live 的 `Retire(c,T*)` 后，将它保留在本地 pending 集合，并在
之后每个 coordinate slot 的 proposal 中重复携带，直到某个共同 slot 已包含它或当前
prefix 已证明它 terminal。

在认证最终扩散、slot 顺序执行、ACS termination 和“决定集合至少包含一个正确提案”
条件下，retirement 最终会出现在所有正确提案中；此后的某个 ACS 输出必然选中至少一个
包含它的正确提案。对选中 proposal 做 `UnionValid` 即可得到 retirement。因此
`Adv_Slot-Admission` 被归约到 diffusion、ACS termination、correct-proposal inclusion、
validity stability 和 `UnionValid`，不再需要独立的 `AdmissionCert_c`。

同一 sticky 规则也用于 repair：合法 repair 最终进入某个 slot，或者 retirement 先成为
terminal event，使该 repair 得到认证取消。协议的 repair liveness 不要求在 coordinate
已经退休后仍安装修复状态。

### 28.92 同 slot 的 retirement-dominates 规则

若一个 slot 的共同有效事件集合中包含唯一合法 `Retire(c,T*)`，则该 slot 只输出
retirement，并取消同 slot 的全部 repair；只有前一 prefix 中已经生效的 repair 会进入
退休屏障。若 slot 不含 retirement，再对 repair 做确定性 canonicalization。

这条规则不依赖本地消息到达顺序，也不是任意 digest 排序。其语义依据是：同 slot 的
repair 尚未进入 `PersistentLive`，取消它不会破坏已经完成的修复；而让它与 retirement
竞争会重新产生 pending resurrection。由此同时满足 `Install-before-retire` 和
`No-install-after-retire`。

### 28.93 首篇 ordering 实例化定理

把连续 ACS slot、sticky proposal、`UnionValid`、retirement-dominates、live-rank
quorum authentication 和 state-relative acceptance 组合后，可得到固定委员会版本的
`SeqACS^slot`。证明按 slot rank 归纳：ACS agreement 给出相同 selected proposal set，
确定性 canonicalization 给出相同 `E_k`，parent context 保证 prefix 只能扩展；sticky
规则给出事件最终决定或 terminal cancellation；同 slot 冲突由 retirement-dominates
统一处理。

排序失败优势为：

```text
Adv_SlotACS-Agreement + Adv_SlotACS-Validity + Adv_SlotACS-Termination
+ Adv_Correct-Proposal-Inclusion + Adv_Event-Diffusion
+ Adv_Event-Validity-Stability + Adv_UnionValid + Adv_Canonicalization
+ Adv_LiveRank-Authentication + Adv_Parent-Binding
+ Adv_Frontier-Use + Adv_AOR-5 + Adv_State-Recovery-Rollback
```

该定理不使用 `FSig_c` 或 `AdmissionCert_c`，并正式填充 Proposition 50 的 ordering
前提。首篇剩余单步证明缺口收敛为 `EqProof^mob`、opaque ACSS delivery、`PECC`、
`Common-H`、generation binding 和 uncovered-edge audit；动态成员与 timeless public
audit 保留为扩展。

### 28.94 PECC 的正确叙事：删除解封能力，而不是删除网络密文

现有 PECC 表述中最容易被质疑的点，是把 retirement barrier 写成“擦除在途消息”。
异步网络无法保证已经发送的密文消失，协议也不需要该保证。正确安全目标是：密文可以
永久归档、任意延迟并在退休后送达，但已经确认退休的 endpoint 不再具有把该密文转换为
旧 scalar capability 的状态。

因此，对每个 endpoint `e=(Q,h,i)`，barrier 是节点 `i` 接受共同 retirement rank 的
本地线性化点 `tau_i`。PECC challenge 只覆盖在 `tau_i` 前未被腐化的 endpoint；若节点
在 barrier 前被腐化，其 key、plaintext 和 opening 直接进入 `X_hist`，由 generation
暴露预算处理。barrier 后的腐化则返回完整残留状态，包括归档密文、网络队列和 buffer，
但 endpoint key、plaintext、verification workspace 已被擦除，且 retired label 不能
重新注册 key、解密、恢复或安装。

该定义带来一个重要简化：PECC 本身可以由每实例 receiver-ephemeral PKE 归约。对主动
密文环境使用 IND-CCA；若 authenticated channel 保证唯一合法密文且两个有效 payload 的
处理结果相同，IND-CPA 即可。它不需要 puncturable encryption，也不需要让 PECC simulator
在 barrier 前自适应打开 challenge endpoint。后一个任务属于完整 `AVSS-opaque/AOR-3`
状态一致性，而不是 PECC。

### 28.95 Barrier-complete delayed-state closure

定理稿新增 Proposition 59 和 Theorem 60。状态被完整划分为：

```text
Endpoint     = key + plaintext + evaluation opening + receive buffer + verification state
HelperTemp   = polynomial coefficients + payload copies + encryption randomness
               + send buffer + unreleased recovery response
Network      = ciphertext + delivery metadata + public receipt
Retired      = frontier + commitment + tombstone
```

`Network` 可以永久存在；`CancelOrRetire` 在节点本地 barrier 原子地进入 absorbing
`Retired` 状态，并擦除 `Endpoint`、`HelperTemp` 以及已经安装的旧 coordinate state。
对从未生成 endpoint key 的实例，retirement 关闭后续注册边；对已生成但尚未交付的实例，
临时 key 擦除使迟到密文不可解封；对已交付但尚未安装的实例，pending plaintext、opening
和 interpolation state 被删除；对已经在共同 prefix 中先安装的实例，retirement 删除其
最新 current share；retirement 先排序时，AOR-5 拒绝后续安装。

令 `A_c` 为已确认擦除的节点，`U_c=P-A_c`。定理证明，向基础暴露
`X_hist union X_current(U_c) union X_adv` 加入全部归档与在途公开密文，不会为 `A_c`
新增旧 capability。它把 Proposition 50 中抽象的 `Adv_PECC +
Adv_Atomic-CancelOrRetire` 具体归约为每 endpoint 的 PKE/label authentication 安全和一个
state-complete barrier 事件。未确认节点的 endpoint 状态始终进入 `X_current(U_c)`，因此
该结论没有假设异步网络中的所有节点同时擦除。

这一步关闭的是 receiver/helper pending-state resurrection，而不是完整 AOR。下一步应
处理 opaque ACSS delivery：证明公开 transcript、availability certificate 和 receiver
verification 对未暴露 evaluation 可联合模拟，并与当前 PECC 分区在 barrier 处无缝衔接。

### 28.96 新发现：局部 `READY` 不能推出 repair target 可恢复

对 complaint-free 候选的进一步审计发现，原来的 `2f+1 READY` 推理不成立。若每个
signer 只证明自己解密到了有效 evaluation，Byzantine helper 可以向这 `2f+1` 个
non-target signer 发送有效密文，同时向 repair target `u` 发送无效密文。证书仍然形成，
AVID 也只能保证 `u` 取回这个无效密文，不能保证其 plaintext 满足承诺多项式关系。

hbACSS 通过 `IMPLICATE + share recovery` 解决这种 partial-success 情形；删除公开
key-reveal/recovery 分支后，不能继续继承其 completeness。提高 READY 门限也不能解决，
因为异步活性不能等待 Byzantine 节点，而任意可终止的 signer 集合都可能遗漏某个正确
receiver。定理稿 Proposition 61 将其写成两个公开视图不可区分、target 输出不同的分离。

这不是小的证明瑕疵，而是决定协议形状的必要性结果：无 complaint 的完整交付必须让
每个 receiver ciphertext 的正确性在解密前即可验证。

### 28.97 PVOD：公开可验证、标量不公开的 evaluation delivery

候选 transport 改为 **Publicly Verifiable Opaque Delivery (PVOD)**。helper 对多项式
`f_h` 发布 hiding commitment，并为每个 receiver `j` 生成公开的子份额承诺 `M_{h,j}` 以及：

```text
M_{h,j} = Com(f_h(j); rho^M_{h,j})
ct_h,j = Enc(pk_Q,j,
             (f_h(j), rho^D_{h,j}, rho^M_{h,j}); omega_h,j, Q,h,j)

pi_ved,h,j proves:
  EvalOpen(D_h,j; f_h(j),rho^D_{h,j})=1
  and ct_h,j encrypts an opening consistent with M_{h,j}.
```

所有 `(M_h,j,ct_h,j,pi_ved,h,j)` 作为一个向量经 AVID dispersal。`AVAIL(Q,h)` 不再表示
“我已经解密自己的 evaluation”，而只表示“完整向量的公开证明均通过，且我完成了该
AVID disperse instance”。因此 `2f+1` 个 non-target AVAIL 至少包含 `f+1` 个正确存储
节点，满足 AVID availability 的恢复条件；target 随后可取回自己的密文。`R_ved`
soundness 保证该密文解密为承诺多项式在 target index 的唯一 evaluation。

这个变化同时解决两个问题：

1. `Common-H` correctness 不再依赖 target 本地 READY，也不需要 scalar complaint；
2. AVAIL pattern 只依赖公开验证与存储完成，不携带 hidden evaluation validity bit。

代价是每个 helper 需要面向所有 receiver 的 verifiable-encryption proof，首版通信量为
二次量级。本文暂不加入 proof aggregation 或 packed repair；先证明基础构造，再由实验
判断是否需要批处理优化。

### 28.98 Opaque delivery 的联合归约

定理稿 Lemma 62 证明 transport transparency：给定 PVOD ciphertext/proof vector，AVID
blocks、retrieval metadata、AVAIL 和 `AvailCert` 都只是该公开向量、公开随机性和调度的
PPT 后处理，因此不需要额外的“AVID privacy”假设。

真正的 pre-barrier 密码学要求被收敛为 commitment-assisted `CSO-VE[R_ved]`：攻击者看到整个相关 Shamir
evaluation 密文向量后，可以自适应腐化至多 `f` 个 receiver；simulator 必须为这些
endpoint 打开与既有 ciphertext/proof 一致的 key 和 plaintext state，同时不获得其余
evaluation。该性质需要 public subshare commitments、可选择打开或 non-committing 的
加密、以及 concurrently simulatable 且 simulation-sound 的 `R_ved` proof 共同满足；普通
IND-CPA 或只支持同分布明文的 RIND-SO 不能自动推出这一性质，因为被选择打开的 plaintext
受同一个隐藏多项式常数约束。

Theorem 63 将 opaque ACSS delivery 分解为：

```text
generation-local affine coupling + hiding commitment
+ CSO-VE[R_ved] for pre-barrier adaptive corruptions
+ ephemeral-PKE PECC for post-barrier corruptions
+ R_ved soundness and full-context labels
+ AVID correctness/availability
```

文献位置也更清楚：hbACSS 的 evaluation proof 位于密文内部，并依赖 implication/recovery；
Janus 提供 adaptive ciphertext equivocation，但允许 complaint 公开解密；Illusi 提供标准
假设下的 adaptive PVSS 与公开 share validity，但输出 group-valued shares，无法直接作为
FGSR 所需的 scalar Shamir repair。PVOD 是这些接口之间缺失的 frontier-bound 组合，而
不是对某篇现有工作的改名。

下一步应具体化 `CSO-VE[R_ved]`：先固定“相关 Shamir 明文 + 自适应 key opening +
承诺开口 + proof transcript”联合 game，再判断标准模型的 selective-opening PKE、
dual-mode 或 uniform-preimage-sampleable commitment、以及 simulation-sound NIZK 能否
给出标量 repair 的实例。若只能证明独立明文或 group-valued share，不能将其作为本文的
端到端构造。

### 28.99 CSO-VE 的论文级证明边界

`CSO-VE` 不是把几个熟悉的密码学名词并列即可得到的组件，而是本文必须明确证明的
联合安全接口。公开的 `M_{h,j}` 解决“验证密文而不公开 evaluation”的绑定问题；
selective-opening/non-committing encryption 解决攻击者先看完整向量、后选择 endpoint
腐化的问题；equivocation 或 uniform preimage sampling 解决模拟承诺之后仍需给出一致
开口的问题；`PECC` 只处理 endpoint 到达 retirement barrier 后的状态消除。

因此，本文的具体密码学定理应采用以下结构：先由 generation-local affine coupling 固定
与已暴露份额相容的多项式视图，再在同一 labelled transcript 中证明 `M`、密文和
`R_ved` proof 的联合模拟，最后用 `PECC` 完成 barrier 后的状态闭合。任何只给出普通
IND-CPA、静态 NIZK zero knowledge 或 RIND-SO 的证明，都只能覆盖其中一层，不能关闭
Theorem 63 的 pre-barrier gap。

这条边界使创新叙事更准确：本文不是提出一个新的通用选择打开加密，而是首次把
“相关标量 Shamir repair 的自适应透明交付”作为异步 FGSR 的必要密码学接口，并证明它
如何与 frontier-gated retirement、recovery closure 和 aggregate-only privacy finality
组合。具体实例化能否在标准假设下成立，是当前唯一需要继续攻克的构造问题。

### 28.100 主线接口更名与旧候选的状态

自本节起，`READY` 仅作为相关工作中的原协议术语；本文主线使用 `AVAIL`。`AVAIL`
表示公开 PVOD descriptor 已通过逐 receiver 的 `R_ved` 验证且 AVID dispersal 已完成，
不表示某个节点已经私下解密 evaluation。旧的 metadata-only `READY` 路线保留为
Proposition 61 的不可行候选，不再进入 `FGSR-PVOD` 的安全定理。

### 28.101 具体构造筛选与 go/no-go 判据

当前最小构造是 proof-carrying encrypted opening。helper 对每个 receiver `j` 生成
多项式 opening `(y,rho^D)`，再生成公开承诺 `M=Com(y;rho^M)`，加密
`(y,rho^D,rho^M)`，并证明 `D_h`、`M` 与密文中的三者一致。receiver 只在本地解密和
验证，随后在 frontier barrier 擦除 key、明文、两个 opening、加密随机性、证明随机性
和解密缓冲区。公开 descriptor 只有 `(M,ct,pi)` 与 AVID 元数据。

这个构造进入主定理必须同时满足四个条件：

1. `M` 的承诺在真实设置中隐藏，在模拟设置中可 equivocate 或满足 uniform
   preimage-sampling，且后期开口分布与真实执行一致；
2. 加密支持密文向量发布之后的自适应 endpoint key opening，并支持由同一个隐藏 Shamir
   多项式产生的相关 payload；
3. `R_ved` 的证明系统可并发模拟且 simulation-sound，模拟 proof 能和后续 corruption
   返回的 key 与 opening 保持一致；
4. `PECC` 覆盖 endpoint 的全部解封状态，并将网络中永久保留的迟到密文视为公开网络状态。

这里还必须固定 receiver key 的来源：首篇固定委员会模型中的 `pk_{Q,j}` 在 repair
开始前已经注册，并且对 adversary 可见；repair simulator 不因生成 PVOD vector 而获得
对应 secret key。若把所有 receiver key 都改为 simulator 自己生成，则只能得到一个更强
trusted-setup 下的局部证明，不能支持 stable-key 的长期自适应腐化结论。

APSS 的 Section 7.3 只解决了“公开承诺 + 加密开口”的语法，不能直接提供第 2 项；其
RIND-SO 分析明确指出未知 PVSS secret 诱导的相关明文需要额外 simulation argument。
Janus 的自适应状态 equivocation 可作为第 2、3 项的技术参考，但其 complaint 后公开
解密违反 `D5`。Illusi 的公开可验证 PVSS 不能直接替代标量 Shamir repair。因而这些工作
分别是组件证据，不是本文的端到端构造。

下一步只验证一个候选 PKE：对隐藏 degree-`2f` polynomial 的完整 evaluation vector
写出 late-key-opening hybrid。如果 simulator 需要隐藏常数、不能一致回答后期开口，或
必须发送 scalar complaint，则该候选从主定理中剔除；只有满足联合 game 且保持 `AVAIL`
public-only 的候选，才继续写完整标准模型实例化。

候选原语的边界如下：Libert--Yung 的前向安全阈值加密满足外部公钥、自适应腐化和历史
period 保密，但依赖全局 period，且没有证明密文对应 `D_h` 的 scalar Shamir opening；
它只能作为 key-exposure 对照，不能直接实现 `CSO-VE`。Janus 的 Pedersen + encrypted
opening + erasure 机制最接近 pre-barrier state simulation，但其 complaint 会使争议
密文公开可解密，移除 complaint 后必须重新证明 target-excluded delivery。APSS Section
7.3 提供公开承诺和加密开口的语法，却明确留下未知 secret 的相关向量模拟缺口。Illusi
提供公开可验证 PVSS，但其 group-valued share 不能直接执行 scalar repair。

这些结论不是对已有方案安全性的否定，而是对本文所需接口的精确筛选：下一步只需选择
一个具有外部公钥 late-key-opening 能力的候选，尝试完整相关向量 hybrid；不满足者直接
作为相关工作边界，不再继续堆叠协议层。

### 28.102 HPW15 的定位：接收方开钥，而非本文的完整接口

Hazay--Patra--Warinschi 的 receiver selective opening 工作是当前最直接的理论起点。其
攻击者观察完整密文向量后选择一组 receiver，并获得这些 receiver 的解密密钥；这与本文
移动腐化中的 key exposure 在语义上相近。该工作还区分 `rind-so` 与更强的 `rsim-so`，并
由 NCER 通过假密文和后期开口实现 receiver-side 模拟
(`/tmp/hpw15.txt:298-312`, `:962-1018`)。

但它不能直接填充本文的 `CSO-VE[R_ved]`。第一，HPW15 的理想模拟器自行生成公钥--私钥
对并保留私钥；本文的固定委员会模型要求 receiver 公钥在 repair 前由外部注册，repair
模拟器不能取得对应私钥。第二，HPW15 的消息分布可以相关且可重采样，但其定理没有处理
“隐藏多项式 evaluation + evaluation opening + public commitment”这一同一 witness 诱导的
向量。第三，它没有 `R_ved`、AVID 可用性和并发 proof transcript；承诺与 NIZK 的加入需要
独立证明后期开钥仍与公开证明保持一致。

因此本文明确区分：

```text
sender-opening SO:    暴露 (m_i, r_i)
receiver-opening SO:  暴露 sk_i
本文所需:              外部注册 sk_i 的后期开启 + 相关 scalar Shamir witness
                       + 公共 opaque-delivery proof 的联合模拟
```

Pan--Wagner--Zeng 的 `SIM-SO-CCA` 属于第一类 sender-opening，不能替代 HPW15 的
receiver-opening，也不能直接支持本文。新的理论问题不是重新命名 selective opening，而
是给出一个 external-key correlated receiver-opening 定义，并证明它与 `R_ved` 和 `PECC`
组合。这个接口若能在标准假设下实现，将把“长期移动腐化下的异步标量修复”从条件主定理
推进到具体构造；若当前候选无法实现，则失败精确界定论文的构造障碍。

下一步只审计一个 NCER/dual-mode 候选：模拟器不得持有 endpoint secret key，必须在完整
密文向量发布后应答选定 receiver 的 key opening，并让所有 opening 来自同一个隐藏
degree-`2f` polynomial，同时保持 `R_ved` 接受。任何需要模拟器生成全部 key、暴露 scalar
complaint 或修改公开 proof 的路线，都不进入本文主构造。

### 28.103 HPW15 的 `ksim` 仍不足以关闭 Key-Origin

HPW15 的 key-simulatable PKE 只证明真实公钥和 oblivious 公钥（连同其采样说明）在分布上
不可区分。它解决的是公开 key distribution hybrid，而不是后期开钥。HPW15 的 NCER 和
tweaked NCER 开口算法分别依赖原始 `sk`，形如 `nOpen(sk,e*,t,m)` 或 `tOpen(sk,pk,e*,m)`；
这意味着模拟器必须先持有由 key generation 产生的秘密状态
(`/tmp/hpw15.txt:452-524`, `:1450-1535`)。

本文所需的 `KeyOrigin` 因而是更强的接口：

```text
SimKeyGen  -> (pk,tau)             不产生 endpoint sk
SimKeyOpen -> sk_star              在密文已发布后开启到指定 plaintext
```

要求 `pk` 与外部注册公钥不可区分，`sk_star` 能解开既有模拟密文并与指定 evaluation
一致，且整个被腐化 endpoint state 与真实注册状态不可区分。这个接口还必须和 `M`、
相关 Shamir witness 以及 `R_ved` proof 联合成立。

HPW15 的 extended key-simulatable PKE 允许 oblivious 公钥没有对应合法私钥；这有助于分离
安全概念，却不能直接作为必须解密真实 payload 的 receiver endpoint。因此当前最准确的
叙事是：HPW15 提供 receiver-SO 和公钥模拟的理论基座，本文新增的是外部密钥后期开启与
相关代数 witness 的组合问题，而不是简单套用 NCER。

下一步先定义 `KeyOrigin` 的完整安全实验，再寻找能够在不输入原始 `sk` 的情况下实现
`SimKeyOpen` 的 dual-mode/非承诺式加密。只有 `H1` 关闭后，才继续 `H2` 的相关 Shamir
向量 hybrid；这样可以避免把一个仅支持 key-generated setting 的证明误写成本文主定理。

### 28.104 更深的缺口：Key-Origin，而不仅是前向安全

外部预注册公钥带来一个先于 NCER 的模拟问题。真实执行中，`pk_{Q,j}` 在 repair 前已经
存在，匹配的 `sk_{Q,j}` 由 endpoint 持有；若 endpoint 在 barrier 前被腐化，攻击者得到
该私钥以及与公开密文一致的本地 opening。若模拟器只得到公钥而没有 key-generation
witness，就无法一般性地产生一把既服从注册分布、又能解开既有密文的私钥。让模拟器自行
生成所有 key 会回到 HPW15 的 key-generated 模型，不能支撑 stable-key 的移动腐化叙事。

因此 `CSO-VE` 必须额外包含 `KeyOrigin` 子游戏，并明确采用下列二者之一：

1. oblivious/dual-mode key generation，使模拟器能够解释外部公钥并在后期开启一致的合法
   私钥；
2. 理想实验提供一个受限 key-opening oracle，返回真实注册私钥，同时明确不交付未开启的
   evaluation 或 witness。

普通唯一私钥 PKE 不自动满足任一条件。HPW15 的 key-simulatable PKE 是值得继续审计的
   技术方向，但它至多解决 key-origin；其 receiver-SO 定理仍需与相关 Shamir payload、
   `M` 和 `R_ved` 联合证明。

论文级 hybrid 顺序固定为：

```text
H0  外部注册 key + 相关 Shamir payload + 真实 R_ved
H1  KeyOrigin：切换到 oblivious/dual-mode key explanation
H2  NCER：替换未开启 endpoint 的密文，并回答 barrier 前的 key opening
H3  Commitment/R_ved：保持同一隐藏多项式关系并完成公开证明模拟
H4  PECC：仅在 endpoint barrier 之后消除本地状态
```

这说明主线的理论贡献不会落在“使用前向安全加密”本身，而在于证明 key-origin、相关
代数 witness 和 public opaque delivery 可以在异步 frontier 下同时成立。下一步只审计
HPW15 的 key-simulatable 路线能否提供 `H1`；若不能，论文保留条件主定理，并把
external-key correlated receiver-opening 作为明确的构造障碍。

### 28.105 YLH20：一个有条件的 Key-Origin 候选

Yang 等人 2020 年的 multi-challenge receiver-SO 工作改变了当前候选排序。其
`SIM-RSO_k-CPA` 允许同一公钥承载 `k` 个 challenge ciphertext，并在 DDH 下构造了
模拟安全方案。模拟器先发布公钥和 malformed ciphertext，收到被腐化 receiver 的消息后，
再构造能够解开既有密文的 secret key；该过程不需要原始 endpoint secret key
(`/tmp/ylh20.txt:903-951`, `:1000-1060`)。这正是 `SimKeyOpen` 所需的基本形状。

但 YLH20 仍有明确的模型边界。其 simulator 通过 `S1` 控制 public-key generation，
而不是接收一个由独立 registry 预先固定的任意 `pk`。因此它支持的是：把 receiver key
registration 纳入本文协议，并使用 YLH20 的特殊 key distribution；如果本文坚持任意
stable public key 在 repair 前已经由外部固定，则 YLH20 不能自动解释该精确公钥。

此外，YLH20 的构造以 bit message 为基本形式，多个 ciphertext 共用一个 key 时需要
与 payload 长度相匹配的 secret-key entropy；它没有处理 `M`、隐藏 Shamir polynomial
witness、`R_ved` proof 和 `PECC` 的联合模拟。故其正确定位是：

```text
YLH20 -> 可行的 KeyOrigin/receiver-SO 候选
本文新增 -> 相关 scalar Shamir opaque delivery 的组合定理
```

这给主线带来一个可检验的分叉：优先尝试“协议管理的特殊 receiver key registration”
版本，以 YLH20 关闭 `H1`；同时保留“任意外部固定公钥”版本作为更强模型。若前者可以
与 `R_ved` 和 `PECC` 联合闭合，论文获得具体构造；若只能在后者下工作，则将 YLH20
作为关键相关工作，并把精确公钥解释能力作为理论边界。

### 28.106 YLH20 到 PVOD 的 lifting 路线

可以把一个 endpoint payload 编码为 `L` 个 bit ciphertext，并让它们共用一个 YLH20
receiver key。真实 endpoint 保存一个 field component 和 `L` 个 binary branch components；
模拟器先发布全部 malformed ciphertext，再在得到被开启 payload 的 `L` 位后调用 `S3`
构造一致 secret key。这样，相关 Shamir payload 的相关性只出现在理想功能交付和
`D_h` 约束中，不要求模拟器预先知道未开启 evaluation。

但 `R_ved` 的模拟必须准确处理这一点：YLH20 的 malformed ciphertext 没有真实的
encryption randomness，因此模拟器不能用普通真实 witness 生成 proof。正确做法是在
simulation CRS 下生成 simulated `R_ved` proof，并用 commitment equivocation 让
`M_{h,j}` 在后期开启时与 payload 一致；simulation-soundness 负责阻止攻击者利用模拟
proof 产生新的无效公开对象。

由此得到一个清晰的条件 lifting lemma：在 DDH、dual-mode hiding commitment 和并发
simulation-sound NIZK 下，协议管理的 YLH20 key registration 可以模拟任意相关 payload
向量的 pre-barrier endpoint view。其代价是每个 `L`-bit payload 需要 `L` 个 YLH20
bit ciphertext 和 `L` 个 branch components，除非后续证明批处理；这应作为 receiver-SO
equivocation 的理论代价明确报告。

因此当前最有价值的构造路线是：先对单个 generation 完成 YLH20-PVOD lifting，再接回
`PECC` 和 frontier closure。该路线支持协议管理的稳定密钥；任意外部固定公钥仍是更强
模型，不应由 YLH20 的 `S1` 模拟悄然替代。

### 28.107 `H3 -> H4` 的条件 lifting lemma

在 proof 已切换到 `SimProve`、承诺已进入可 equivocate mode 后，YLH20 的 malformed
ciphertext hybrid 可以和隐藏 Shamir 多项式解耦。对 endpoint/bit pair 排序，用 DDH
逐项把真实的 `g_j^w` 替换为 uniform group element，再乘上 YLH20 的 `h^alpha` 因子；
其余 ciphertext coordinates 和最终密文分量由模拟 key state 计算。proof 已被模拟，
因此 malformed ciphertext 不需要真实 encryption witness。

若 `P` 为 endpoint 数、`L_Q` 为 payload 编码长度，则该步骤给出
`O(|P| L_Q) * Adv_DDH` 的条件界。隐藏多项式常数只作为 affine-coupling 的辅助状态
存在，不进入 DDH challenge；被开启 endpoint 的 payload 直到 `S3` 才交付。
`S3` 按每一位选择 binary branch，并调整共享 field component，保持 public-key equation
不变，使生成的 key 解密既有 malformed ciphertext 到指定 payload。

该 lifting 需要三个硬条件：`SimProve` 能为 false statement 生成 accepting proof；公开
proof 在腐化后保持不变；系统没有对 malformed ciphertext 的 public decryption 或
complaint path。任一条件缺失，DDH 只能证明普通 YLH20 RSO，不能证明 PVOD。

因此 `H3 -> H4 -> H5` 现在可作为协议管理、context-keyed 分支的条件 lemma；严格任意
外部公钥和无界 key reuse 仍不在结论内。

### 28.108 单 generation hybrid 与长期复用边界

固定一个 generation `Q` 和 receiver `j`，令 `L_Q` 为 endpoint 私有 payload
`(y_{Q,j},rho^D_{Q,j},rho^M_{Q,j})` 的编码长度。`R_ved` 使用的 encryption randomness
只属于 proof witness，不作为 endpoint payload。单 generation 的候选 hybrid 为：

```text
H0  真实 YLH20 key、真实编码密文、真实承诺和 R_ved
H1  YLH20 的模拟 key-registration 视图
H2  在公开 statement 仍为真时切换到 simulated R_ved proof
H3  切换到可 equivocate 的 commitment mode
H4  S2 发布的 malformed ciphertext vector
H5  腐化时由 S3 按已开启 payload 构造一致 secret key
H6  barrier 后由 PECC 替换为擦除状态
```

证明顺序不能先替换密文再生成真实 proof：malformed ciphertext 没有真实 encryption
randomness。应先在真实 statement 上切换 simulated `R_ved`，再切换可 equivocate commitment，
最后通过 YLH20 的 DDH hybrid 替换 malformed ciphertext；此时 simulated proof 可接受假
statement。`H4 -> H5` 才是后期开钥与相关 Shamir evaluation 的一致性步骤。
隐藏多项式相关性通过 affine coupling 和承诺开口维持，不应被普通 RSO 的独立明文
直觉替代。

YLH20 的 `k` 还带来长期复用限制：同一公钥只能在预先界定的 challenge 数下使用，且
私钥 entropy 随 challenge 数和消息长度增长。因此最干净的论文构造是为每个 labelled
`(Q,j)` 注册 fresh context key，并让一个 key 只服务一个 finite `L_Q` payload；同一
稳定公钥跨无界 generation 复用不属于 YLH20 定理。这个限制反而与 frontier/PECC 的
每坐标状态闭合相容，但必须在协议模型和复杂度分析中显式写出。
external-key correlated receiver-opening 作为明确的构造障碍。

### 28.109 `KeyOrigin` 的形式化安全游戏

将 `KeyOrigin` 具体写成外部密钥非承诺式接口。每个带标签的 endpoint 在 repair payload
确定前产生同一个公开接口：

```text
RealKeyGen(1^lambda) -> (pk,sk)
SimKeyGen(1^lambda)  -> (pk,tau)
SimEnc(pk, public-context) -> (ct,sigma)
SimKeyOpen(tau,sigma,m,public-state) -> sk_star
```

真实实验返回 `(sk,y,state)`，模拟实验在公开完整密文和 proof 向量后，只有当 endpoint
在 barrier 前被腐化时才得到理想功能交付的 `y`，再调用 `SimKeyOpen` 返回
`(sk_star,y,state_star)`。模拟器始终不获得未开启 evaluation，也不获得真实 `sk`。

安全性比较完整联合 transcript，而不是分别比较 key generation、encryption 和 proof：

```text
Real:  (pk,sk) <- RealKeyGen; ct <- Enc_pk(y); corruption -> (sk,y,state)
Ideal: (pk,tau) <- SimKeyGen; (ct,sigma) <- SimEnc_pk;
       corruption(y) -> (SimKeyOpen(tau,sigma,y,state),y,state_star)
```

该游戏量化于满足移动腐化界限的自适应时序，以及由同一个隐藏 degree-`2f` polynomial
生成的全部 `(y_j)_j`。barrier 后只返回擦除状态和公开保留密文，由 `PECC` 排除旧状态
重建；`R_ved` proof 被纳入 `public-state`，必须在每次后期开启后仍然一致。

这给出清晰的层次分工：`KeyOrigin` 解释外部公钥并产生可解密的模拟 key，相关 NCER
保持向量分布，承诺保持 `M` 开口，`R_ved` 保持公开绑定，`PECC` 处理 barrier 后状态。
仅有 HPW15 的 `ksim` 不能提供 `SimKeyOpen`，因此不能关闭本文的 `H1`。

后续构造只需围绕这一个游戏推进：先证明 `KeyOrigin`，再证明相关 NCER 和
`Commitment/R_ved` 联合模拟，最后接入 `PECC`。如果候选依赖真实 `sk` 或在腐化后重发
公开 proof，就应当停止实例化并将其记录为构造障碍。

### 28.110 隐藏多项式的联合承诺/proof lemma

剩余的 `D_h` 关系可以单独归约。令 `y_j=Eval(D_h,j)`，真实公开对象为
`M_j=Com(y_j;rho^M_j)`；模拟模式先生成与消息无关的 `M_j`，在 endpoint 被开启时再
用 `OpenSim(M_j,y_j)` 得到一致 opening。完美隐藏的 Pedersen commitment 是条件候选：
模拟 group element 保持均匀分布，trapdoor 可在之后打开到任意 scalar。

证明顺序固定为：先对真实 statement 使用 NIZK zero knowledge 切换 `SimProve`，再切换
equivocable commitment，随后应用 YLH20 的 malformed-ciphertext DDH hybrid。这样，
`M_j` 与未开启 evaluation 的相关性只保留在模拟器内部的 affine-coupled polynomial；
公开 proof 不会重新暴露该相关性。endpoint 被开启时，理想功能交付 `y_j`，同时完成
`M_j` opening 和 YLH20 `S3` key opening。

该 lemma 需要三个条件：affine coupling 能与实际 `D_h` commitment 分布联合；
`OpenSim` 返回完整 endpoint opening state；`SimProve` 对 malformed false statement
仍生成 accepting proof。缺少任一条件时，只能得到普通 receiver-SO，不能得到 PVOD。
