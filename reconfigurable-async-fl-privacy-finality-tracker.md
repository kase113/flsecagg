# 可重配置异步联邦学习隐私终结研究追踪

> 建档日期：2026-09-13
> 研究主题：Reconfiguration-Safe Privacy Finality for Asynchronous Federated Learning
> 当前文档：动态委员会版本的研究追踪。当前方案以 [论文结构稿](reconfigurable-async-fl-manuscript-structure.md) 第 3.1、3.2 节为准；消息模型与文献依据见 P144，双实例方案见 P145，组件、消息流程与成本核对见 P146，退出后的材料恢复检查见 P147，真实 DPSS 接入与实验文档归档见 P148，原生组件复现见 P149，真实加密交接接入见 P150，独立保存者恢复见 P151，多保存者与保存者退出见 P152。早期条目保留研究过程。

## 1. 当前研究判断

新的主问题是：

> 在完全异步、委员会持续加入退出和节点恢复的环境中，如何让 FL 服务持续推进，同时保证委员会交接不会重新打开已经参与训练的客户端更新？

动态成员不再作为普通系统需求，而是作为核心技术问题：委员会交接会转移恢复状态，恢复状态又决定历史客户端更新是否仍然可开启。论文的目标是构建 **reconfiguration-safe privacy finality**，而不是简单支持动态成员列表。

文献核对后的主线名称收紧为 **reconfiguration-safe asynchronous federated learning**。动态用户参与、客户端掉线和异步缓冲已经有成熟工作覆盖；本文聚焦的是聚合权威变化时，训练工作和历史更新保护如何同时保持连续。

## 2. 当前方案

```text
客户端更新
    -> 异步训练窗口
    -> 配置 C_r 下的聚合
    -> 模型版本推进
    -> 窗口封存 PF_sid
    -> 配置变更与节点恢复
    -> 只交接 live state，sealed window 只传播 tombstone/frontier
```

固定委员会版本中的 `CC_sid`、`PF_sid` 和 `Recovery-Closure` 继续保留，但配置历史和 handoff edge 加入恢复闭包：

```text
Cl_rec^dyn(X) = Cl_rec(X union HandoffEdges).
```

## 3. Turritopsis 阅读结论

来源：`/home/yzc/flagg/consensus/Gao 等 - 2025 - Turritopsis Practical Dynamic Asynchronous BFT.pdf_by_PaddleOCR.md`

### 可借鉴

- 配置序列 `C_0, C_1, ...` 和基于本地状态的配置推进，不依赖全局时钟；
- 加入/退出请求进入异步共识；
- 配置证明链、catch-up 和 help-sync；
- 离开节点停止执行后，相关未交付消息可能遗漏；
- 每配置限制离开节点数量；
- 区分 Byzantine 节点和诚实离开节点对活性的不同影响；
- 允许旧配置与新配置在交接期间协作。

### 不直接采用

- ADKR 的阈值密钥整体交接语义；它服务于新配置继续产生共识随机性，不能直接承担 `sid` 历史能力的删除；
- `n >= 3t + 2l + 1` 作为本文统一参数；本文还需满足聚合、封存、交接和恢复条件；
- Turritopsis 的配置级状态作为 FL 窗口状态；本文必须绑定 `sid`、模型版本和 privacy frontier；
- Turritopsis 的部分移动腐化模型作为文献参照；本文采用面向 FL 配置交接的 epoch-bounded mobile adversary。

## 4. 新的自适应攻击

名称：**Cross-Configuration State Resurrection**。

攻击者只执行真实协议允许的操作：

```text
观察配置证书和公开消息
    -> 延迟 repair/handoff 消息
    -> 读取旧配置的部分状态
    -> 释放并选择新配置节点
    -> 触发合法恢复或交接
    -> 读取新配置状态
    -> 检查是否形成旧 sid 的授权开启集合
```

该模型不是自适应查询模型。敌手没有任意数据库查询接口，适应性只体现在根据公开配置状态、消息交付和已读状态选择下一次腐化、恢复或交接时机。

### 攻击分支

1. **Post-seal delayed handoff：** `PF_sid` 前生成的旧修复消息在封存后到达，新配置仍安装旧状态。
2. **Pre-seal handoff residue：** 未封存窗口的状态已交给新配置，但旧配置尚未完成擦除，敌手跨配置累计旧份额。
3. **Configuration-proof replay：** 旧配置产生的有效状态证明在新配置中仍能被解释为当前状态。

攻击成功的必要观察点是：旧消息可跨 frontier 安装、sealed state 可进入 handoff、或配置转换没有覆盖曾经持有 `sid` 状态的节点和配置。

### 2026-09-13（P70：收紧跨配置自适应攻击的适用对象）

重新核对 Turritopsis 后，明确不能把 `Adaptive Cross-Configuration Resurrection Attack` 写成对 Turritopsis 共识安全的直接攻击。Turritopsis 的安全目标是动态异步共识的安全性和活性；它没有声称保护 FL 客户端更新的 aggregate-only 隐私。本文的攻击对象应是“动态异步 BFT/DPSS 配置交接机制与 FL 安全聚合状态的组合接口”。

最小攻击固定两个配置 `C_0 -> C_1` 和一个已经发布 `Y_sid`、尚未完成 `PF_sid` 的窗口。攻击者观察配置证明，读取 `C_0` 的部分 `sid` 状态，延迟 handoff/repair 消息，根据交接结果选择 `C_1` 中的恢复目标，读取新配置状态，再执行合法 recovery。若

```text
Cl_rec(X_hist union X_current union HandoffEdges)
```

包含 `Gamma_dec^cap(sid)` 中的某个授权集合，则旧窗口可以被重新打开。每个时刻的腐化上限保持不变；适应性只来自根据公开配置和状态读取结果选择下一步腐化、恢复和消息调度。

攻击不适用于以下已闭合的组合：`C_1` 对已封存窗口只接收 sealed record，旧配置完成相关状态清除，旧 handoff 受 frontier 拒绝，且新配置无法从配置证明链恢复旧 `sid` 状态。该边界把攻击转化为方案的可检验条件，而不是对所有动态 BFT 工作的泛化指控。

Turritopsis 可作为配置证明链、catch-up/help-sync、离开消息遗漏和动态密钥交接的运行参照。后续逐篇审计必须回答它们在承载额外 FL `sid` 状态时的接口语义；若原文没有该状态，结论写为“未覆盖本文隐私目标”，不写成共识协议漏洞。

## 5. 候选贡献

1. **Reconfiguration-safe asynchronous aggregation：** 设计按窗口处理委员会重配置的聚合协议，活动窗口继续计算，已完成窗口转化为只读结果。
2. **Finality-preserving state handoff：** 通过 live-state handoff、epoch 状态刷新和 sealed record，把训练连续性与已完成窗口的隐私终结放在同一条执行路径中。
3. **系统实现与 FL 评价：** 在统一异步训练轨迹下比较固定委员会、全量迁移、周期重建和本文方案，测量模型推进、训练质量、交接延迟、通信和持久状态。

epoch-bounded mobile adversary 属于威胁模型，用于界定上述保证的适用条件，不作为独立贡献点。

## 6. 必须保持的系统边界

- 客户端动态参与和委员会节点动态参与分开建模；前者是 FL 窗口行为，后者是配置交接行为；
- 配置变更不要求全服务停机，但旧配置和新配置的职责必须按窗口划分；
- 已封存窗口不向后续配置交接旧 share、repair share、pending plaintext、endpoint key 或旧恢复转录；
- 未封存窗口的状态交接需要可验证安装和旧状态清除条件；
- 离开节点导致的消息遗漏必须进入活性模型；不能用可靠异步网络假设掩盖离开后的停止执行；
- epoch-bounded mobile adversary 的周期控制上限、配置交接条件和窗口状态清除条件分别定义，服务条件与隐私条件保持清晰。

## 7. 需要重新推导的参数

Turritopsis 的 `n_c >= 3t_c + 2l_c + 1` 只作为动态异步共识参考。本文至少需要分别推导：

```text
descriptor agreement
aggregate opening
live-state handoff
privacy sealing
repair liveness
```

固定委员会首个参数点 `n=3f+2`、`q_dec=q_rec=2f+1` 可以作为局部基线；动态配置需要写成 `n_r, f_r, l_r, q_dec,r, q_rec,r`，并说明每次交接如何刷新活动窗口的保护上下文。

## 8. 系统实现路线

### 第一阶段：配置与窗口绑定

- 为每个窗口保存 `sid`、模型版本、配置编号和 `CC_sid`；
- 新配置处理新窗口，旧配置排空已有窗口；
- 配置证明和新节点追赶只同步公开配置记录。

### 第二阶段：状态交接

- 对未封存窗口定义 live-state handoff；
- 对已封存窗口定义 sealed record/tombstone；
- 交接确认绑定旧配置、新配置、generation 和 frontier；
- 节点重启先读取封存记录，再恢复当前配置的 live state。

### 第三阶段：故障轨迹与评估

- 注入延迟 repair/handoff、节点永久离开、节点崩溃和连续移动腐化；
- 比较 static committee、ordinary dynamic handoff、epoch/rekey 和 live-state-only handoff；
- 记录训练吞吐、窗口延迟、客户端陈旧度、配置切换延迟、恢复延迟、通信量、持久状态和模型质量。

## 9. 近期研究任务

1. 从 Turritopsis、DyCAPS、Optimistic DPSS 等文献提取配置交接的精确定义、消息遗漏模型和移动腐化范围；
2. 为自适应跨配置攻击写出最小 `l=1`、两配置、单窗口反例；
3. 判断攻击在“已封存状态禁止交接”规则下是否被完全阻断；
4. 推导 live-state handoff 的最小旧配置 helper 条件和新配置安装条件；
5. 判断 `PF_sid` 是否需要跨配置 holder 集合证明；
6. 设计配置切换期间不暂停新窗口的系统执行路径；
7. 在现有异步 SA/ACS 实现基础上列出最小新增状态和通信消息；
8. 仅在上述模型和攻击闭合后，选择具体密码学组件和实现接口。

## 10. 当前裁决

动态成员版本值得继续推进，并且比固定委员会版本拥有更强的 OSDI 叙事：系统必须在委员会变化时保持训练连续性，同时让已完成窗口的隐私边界跨越所有未来配置。

当前不把 Turritopsis 的 ADKR、配置参数或证明直接移植到本文。Turritopsis 提供动态异步共识的运行参照；本文的新增问题是配置交接与 FL 历史更新隐私之间的耦合。

后续研究的核心判据是：如果只增加成员列表和配置证书，动态版本不构成新贡献；如果能够实现并验证 live-state-only handoff、sealed-state tombstone 和自适应跨配置攻击下的 privacy finality，动态委员会就是论文的核心贡献。

### 2026-09-13（P71：完成动态成员文献的组合攻击审计框架）

补充核对 DyCAPS 和 Optimistic DPSS 后，动态成员版本的攻击对象进一步明确：不是声称 Turritopsis、DyCAPS 或 Optimistic DPSS 的共识/DPSS 安全定理失效，而是审计它们的配置交接机制承载 FL `sid` 状态时是否产生历史开启能力。

DyCAPS 的 handoff 允许旧/新委员会进行秘密保持不变的异步交接，且委员会可以完全不相交；Optimistic DPSS 通过 `Transfer commitments -> Reshare -> Select -> Recover -> Compute` 将旧 share 重分享给新委员会并保持同一秘密。若历史 FL 窗口的解密秘密直接作为这种持续秘密，攻击者可以通过旧/新配置的移动暴露或合法 recovery 重新形成旧窗口的开启能力。这里的缺口是应用语义缺口，不是对原 DPSS 秘密保持定理的反例。

Turritopsis 的 ADKR 和配置证明链解决动态异步共识的阈值密码学切换、配置发现和离开消息遗漏；原协议没有 FL 客户端密文或 `sid` 状态。因此只能把它作为组合基线：检查 ADKR、catch-up 或 help-sync 是否会传播旧 FL 状态，以及迟到消息在新配置中是否仍可安装。

统一的可证伪审计固定两个配置和一个窗口，检查：

```text
Handoff(old_state, C_old, C_new) -> state_new(sid)
```

并分别调度“交接消息在 `PF_sid` 前到达”和“同一消息跨过 `PF_sid` 或配置切换后到达”。若后者仍可安装旧状态，得到 delayed-handoff resurrection；若安装被拒绝但旧/新配置状态仍可共同打开 `sid`，得到 cross-configuration accumulation；若原协议未定义该应用状态，结论记录为未覆盖。

下一步优先完成 Turritopsis、DyCAPS、Optimistic DPSS 的逐项状态/消息审计，再决定动态版本的最小交接协议和参数条件。自适应攻击继续限定为公开协议事件、合法恢复、消息调度和移动状态暴露，不引入任意历史查询接口。

### 2026-09-13（P72：完成三类动态成员基线的攻击可达性分层）

逐项核对结果如下：

| 基线 | 当前判断 | 原因 |
|---|---|---|
| DyCAPS | 直接组合风险 | handoff 在旧/新委员会间保持同一秘密 `s`，且支持完全不相交委员会；若 `s` 承载历史 `sid` 解密能力，新委员会继续拥有该能力 |
| Optimistic DPSS | 直接组合风险 | `Transfer commitments -> Reshare -> Select -> Recover -> Compute` 重分享旧 share 并保持同一秘密；可选 recovery 会增加历史状态的恢复路径 |
| Turritopsis | 条件组合风险/应用状态未定义 | ADKR、proof chain、catch-up/help-sync 服务动态共识；原协议没有 FL 客户端密文和 `sid` 历史状态，只有适配层把这些状态放入交接才可执行本文攻击 |

这些判断不声称原协议的共识、DPSS 或阈值密钥安全定理失效。真正的攻击对象是“动态成员机制 + FL 历史窗口状态”的组合。对每个基线，最小审计固定 `C_0 -> C_1` 和一个 `sid`，检查同一交接对象分别在 `PF_sid` 前后到达时是否仍可安装，以及新旧配置状态是否可以共同形成旧窗口的授权开启集合。

### 2026-09-13（P73：形成公开密文下的具体组合攻击）

为避免“长期恢复可能泄露历史窗口”停留在口号层面，新增一个 session-state composition attack：客户端公开 `ct_u=Enc(pk_sid,k_u)`，委员会用 threshold state 处理 mask key，`C_0` 完成模型聚合后通过 DyCAPS/Optimistic DPSS 将同一 `s_sid` 重分享给 `C_1`。`PF_sid` 之后，敌手只需请求新配置执行合法 `Recon/PartDec`；若接口允许处理单项 `ct_u`，就可得到 `k_u` 并恢复 `x_u`，或者区分等聚合的两组更新。

该攻击的前提是数据层暴露普通单项 threshold decryption。若接口严格限制为 aggregate-only opening，则单项解密路径被接口隔离，审计必须继续检查聚合密文、恢复转录和配置状态是否生成其他 `sid` capability edge。攻击针对的是“DPSS 持续秘密 + 普通单项解密 + FL 历史密文”的组合，不是 DPSS secrecy 定理本身。

因此论文需要明确区分：

```text
DPSS secrecy:  未达到门槛的敌手不能得到持续秘密
PF privacy:   已封存窗口不能被未来合法委员会重新打开
```

这一区分将 DyCAPS/Optimistic DPSS 从“可能被攻击的论文”转化为有明确攻击接口的强基线，也进一步说明本文必须同时设计 aggregate-only opening 和 sealed-state handoff 规则。

### 2026-09-13（P74：收紧两配置反例与自适应性）

将组合攻击参数化为两个委员会 `C_0,C_1`、重构门限 `q_0,q_1` 和一个持续秘密 `s_sid`。`C_0` 完成模型聚合后，攻击者先观察 `Y_sid`、`CC_sid` 和配置变更记录，再选择触发或利用 `C_0 -> C_1` 的合法 handoff。若新配置得到同一个 `s_sid` 的 `q_1` 个 share，且 `PF_sid` 没有从 handoff 输入中删除该 `sid`，则新配置可以对公开 `ct_u=Enc(pk_sid,k_u)` 执行合法 `Recon/PartDec`，得到单客户端 `k_u` 并恢复 `x_u`。

该实例不需要委员会重叠，也不需要协议外的解密 oracle；自适应性来自攻击者根据公开输出和配置状态选择交接/恢复路径。若接口严格限制为 aggregate-only opening，或 `PF_sid` 前完成 `sid` 状态清除并向新配置只传 sealed record，则这条单项解密反例被阻断，后续审计转向聚合密文、恢复转录和状态残留。

核心区分固定为：

```text
secret continuity  !=  application-level privacy finality
```

这使攻击成为动态成员基线的接口级分离，而不是对 DyCAPS/Optimistic DPSS secrecy 定理的攻击结论。

当前可重复的结果分类固定为：

```text
direct composition risk
conditional composition risk
application gap
```

下一步不再笼统地寻找“攻击动态 BFT 论文”，而是为 DyCAPS 和 Optimistic DPSS 写出明确的 session-state composition attack，为 Turritopsis 写出配置状态未承载 FL `sid` 时的应用缺口说明。只有攻击输入、合法操作和成功事件都闭合后，才把它们放入论文的 baseline comparison。

### 2026-09-13（P75：将下一阶段转为系统规格）

当前主线从“继续扩展跨配置攻击”转为“先固定可运行的动态异步 FL 服务契约”。论文的中心系统命题是：客户端更新持续到达、委员会可以加入退出和恢复时，服务不暂停新的训练窗口；尚未完成的窗口可以转移，已经确定模型结果的窗口进入不可逆的封存状态。

为避免研究继续滑向密码学论文，下一阶段只固定以下四个窗口结果：

```text
accepted    -> 当前配置继续收集和聚合
transferred -> 未完成窗口由新配置继续处理
finalized   -> 模型版本、参与集合和封存结果确定
rejected    -> 迟到或过期消息不再改变结果
```

最小系统由窗口调度器、配置交接器和持久窗口记录组成。配置变更期间，旧配置处理已经接收的窗口，新配置处理后续窗口；交接器只转移未完成窗口的当前计算状态。窗口 finalized 后，后续配置只读取封存证明，不读取旧计算材料；迟到消息只产生拒绝结果，不触发重新聚合或恢复。

下一步的直接产出是系统规格、故障轨迹和基线对照表，先回答训练连续性、窗口完成率、结果一致性、交接延迟、通信和持久记录开销。固定委员会、迁移全部窗口状态的普通动态交接、周期性重新建立聚合密钥和本文选择性交接作为四类比较对象。新的密码学构造和长篇安全证明暂缓，密码学模块先按客户端保护、聚合释放、未完成窗口转移和封存后材料清除四个接口定义。

该调整使动态成员成为系统贡献：成员变化不只是可用性功能，而是决定哪些异步训练工作能够继续、哪些历史结果必须终结的调度与状态组织问题。跨配置攻击继续保留为故障场景和设计依据，不再成为论文主体。

### 2026-09-13（P76：完成动态异步 FL 系统规格）

新增 `reconfigurable-async-fl-system-spec.md`，将主线落实为可运行的服务契约。规格固定：

```text
accepted    -> 收集并聚合客户端更新
transferred -> 未完成窗口交给后继配置
finalized   -> 模型结果和参与集合确定，只读取封存记录
rejected    -> 迟到、重复或过期消息不改变训练结果
```

规格进一步定义了窗口归属唯一、客户端纳入单调、模型版本单调、交接可继续、封存不可改和迟到消息不产生训练效果六条不变量；加入、退出、崩溃恢复、迟到消息和连续配置转换六类故障轨迹；以及 `Static`、`Full-transfer`、`Periodic-rekey` 和 `Selective-finality` 四类基线。

近期实现顺序固定为：先用确定性事件驱动模拟器验证服务不变量，再接入已有异步 FL 框架观察模型训练指标，最后替换不同安全聚合实现测量密码学开销。密码学构造和长篇安全证明继续作为接口支撑，系统主评价集中于窗口完成率、客户端纳入率、模型推进速度、模型质量、交接/恢复延迟、通信量和持久记录大小。

该规格把动态成员贡献具体化为窗口级服务决策：委员会变化时，未完成训练工作继续推进，已经确定的训练结果保持终结。下一步产出为基线对照表和模拟器输入格式。

### 2026-09-13（P77：统一实验计划与动态主线）

现有 `experiments/EXPERIMENT_PLAN.md` 已同步到动态成员主线。动态配置转换从次要扩展调整为核心实验维度，固定委员会作为对照。主比较对象现在包括：

```text
Selective-finality   -> 只转移未完成窗口，封存窗口只传封存记录
Full-transfer        -> 配置变化时转移所有活动窗口材料
Periodic-rekey       -> 通过周期性重建状态完成配置转换
Static               -> 委员会固定
```

实验场景将 `S7`（活动窗口中的加入、退出和委员会交接）与 `S8`（多个配置转换和并发窗口）列为核心场景。归档的 `archive/legacy-mainlines/experiments/privacy_finality_sim.py` 是单窗口抽象事件模拟器，只能验证迟到消息和封存边界；动态成员结果需要按照系统规格补充配置转换和多窗口事件轨迹，归档 CSV 结果不作为动态系统结果。

近期工作顺序因此固定为：定义统一事件轨迹输入，扩展四类基线的窗口行为，验证窗口完成率、模型推进、结果一致性、交接延迟、通信和持久记录开销，再接入真实异步 FL 框架。密码学实现仅作为同一聚合接口下的替换项，系统主评价保持在训练连续性和窗口终结性。

### 2026-09-13（P78：固定跨基线事件轨迹格式）

在 `reconfigurable-async-fl-system-spec.md` 中补充事件轨迹输入。每条轨迹统一描述客户端更新、配置安装、节点退出、节点崩溃/恢复和交接消息交付；`order` 仅是模拟器的逻辑顺序，不改变完全异步的协议模型。

所有基线共享同一轨迹文件，只替换四个系统决策：活动窗口是否迁移、迟到记录是否接受、窗口何时确定结果、配置变化期间是否暂停新窗口。统一输出窗口终态、模型版本、纳入客户端集合、交接延迟、完成顺序、拒绝消息数和持久记录大小。

该输入格式使动态成员实验可以直接比较训练连续性与状态记录开销，避免将网络轨迹差异误当作协议收益。下一步是按该格式扩展现有单窗口模拟器的多窗口和配置事件生成，不引入新的安全模型或密码学证明。

### 2026-09-13（P79：实现动态事件驱动模拟器入口）

新增 `experiments/reconfigurable_fl_sim.py`，替代归档的 `archive/legacy-mainlines/experiments/privacy_finality_sim.py`。新入口读取统一 CSV 事件轨迹，支持多窗口、配置安装、窗口封存、节点退出/崩溃/恢复、迟到交接消息和四类窗口处理策略：`Static`、`Full-transfer`、`Periodic-rekey`、`Selective-finality`。

本次实现把 `window_finalize` 纳入事件格式，使窗口结果的确定时刻由轨迹明确给出。每个策略共享同一事件序列，只改变活动窗口转移、配置转换期间的新窗口接收和封存窗口对迟到消息的处理。输出包括窗口终态、纳入客户端、交接延迟、完成顺序、拒绝消息、持久记录大小和被阻塞更新数量。

动态入口命令固定为：`python3 experiments/reconfigurable_fl_sim.py --trace experiments/reconfigurable_trace.csv --output experiments/reconfigurable_results.csv`。仓库同时保留最小轨迹样例 `experiments/reconfigurable_trace.csv`；入口只读取轨迹文件，不生成客户端数据或模型参数，同一轨迹可以重复交给四类策略，结果文件按窗口输出。

原单窗口模拟器及其已有结果已移入旧主线归档。新入口当前仍使用抽象记录，承担系统行为验证和基线对照；真实模型训练接入放在事件轨迹语义稳定之后。

### 2026-09-13（P80：校准周期重建与封存事件语义）

复核 `experiments/reconfigurable_fl_sim.py` 后，明确 `Periodic-rekey` 的比较语义：配置登记后，已有窗口继续由旧配置处理；后继配置完成转换前，新窗口更新等待或被拒绝；旧窗口完成后后继配置才获得新窗口服务资格。`window_finalize` 只接受当前所属配置的结果，跨配置封存事件被拒绝。

这一区分使 `Full-transfer`、`Selective-finality` 和 `Periodic-rekey` 分别代表三种可观察的服务策略：活动窗口全部迁移、活动窗口选择性迁移、已有窗口排空后再接收新窗口。动态实验因此比较训练连续性与配置转换代价，不把三种策略混成同一种交接流程。

本轮进一步固定 `Full-transfer` 的状态语义：配置转换时它连同已封存窗口的完整记录一起迁移，因此已完成窗口的持久记录开销保持在活动记录规模；`Selective-finality` 对已封存窗口只保留封存记录。两者在活动窗口的训练结果可以一致，差异体现在历史记录开销和交接工作量，形成可解释的系统对照。

### 2026-09-13（P81：补齐全量交接基线差异）

动态模拟器将 `Full-transfer` 实现为迁移所有窗口记录，包括已经封存的完整记录；`Selective-finality` 只迁移未完成窗口，并为已封存窗口保留较小的封存记录。这样两种策略可以在相同客户端和网络轨迹下产生相同的训练结果，同时在交接工作量和持久记录大小上形成清晰对照。

### 2026-09-13（P82：生成多窗口多配置事件轨迹）

新增 `experiments/generate_reconfigurable_trace.py`，按照窗口并发度、每窗口客户端数、配置转换次数、节点数和固定种子生成统一 CSV 轨迹。轨迹包含窗口更新、窗口封存、配置登记、节点离开/崩溃/恢复和封存窗口的迟到交接消息；四类策略读取同一轨迹，只改变窗口处理决策。

动态实验现在可以通过 `--windows-per-configuration` 控制并发窗口，通过 `--transitions` 控制委员会变化次数，通过 `--clients-per-window` 控制每个窗口的客户端规模。生成器不产生模型参数和密码学材料，输出只用于验证训练连续性、窗口终态、交接延迟、拒绝消息和记录开销。

本轮同时收紧封存事件：只有已经接受客户端更新的窗口才能进入 `finalized`，被固定委员会或周期转换拒绝的新窗口不会生成空的封存结果。该规则保证基线输出反映真实纳入集合。

### 2026-09-13（P83：完成 OSDI 动态版本结构稿）

新增 `reconfigurable-async-fl-manuscript-structure.md`。论文叙事固定为：持续运行的异步 FL 服务在委员会变化中处理客户端窗口；核心问题是未完成窗口如何继续、已完成窗口如何终结；第一个挑战是窗口跨越配置边界，第二个挑战是训练连续性与历史记录规模之间的取舍；对应方案是窗口记录和选择性交接。

结构稿把系统设计、实现和 FL 评价放在正文中心，安全性章节压缩为窗口终结定义、跨配置迟到交接轨迹和一个条件性结果。评价使用相同事件轨迹比较 `Static`、`Full-transfer`、`Periodic-rekey` 和 `Selective-finality`，主要观察窗口完成率、客户端纳入率、模型推进、模型质量、交接/恢复延迟、通信和持久记录大小。

### 2026-09-13（P84：固定真实 FL 适配边界）

新增 `reconfigurable-async-fl-adapter-spec.md`，固定训练框架、窗口服务和更新保护插件的职责边界，以及 `ClientUpdate`、`ConfigurationEvent` 和 `AggregateResult` 三类统一记录。适配层负责窗口归属、更新纳入、配置转换、窗口封存、恢复和日志；客户端本地训练、模型评估和保护插件保持独立。

动态系统第一入口改为 FLSim 事件回放，用于保持客户端到达和陈旧度的一致；Buffalo 作为主要异步安全聚合对照；Flower SecAgg+ 作为常规安全聚合控制；Catalyst 作为 Byzantine 鲁棒性控制。真实 FL 接入顺序固定为：合成向量回放、FLSim 本地训练、Buffalo 保护实现、Flower/Catalyst 对照。

该边界把论文评价集中到窗口完成率、客户端纳入率、模型推进、模型质量、陈旧度、交接/恢复延迟、通信和持久记录大小。密码学组件作为同一适配接口中的替换项，不改变窗口状态和模型版本规则。

## 11. 记录格式

后续每次更新记录：日期、阅读文献、模型变化、攻击变化、协议变化、实现变化、可证伪条件和未解决问题。未证明的结果标记为候选，不把协议条件写成安全定理。

### 2026-09-13（P85：完成动态成员与滚动腐蚀模型稿）

新增 `reconfigurable-async-fl-dynamic-adversary-model.md`，将下一阶段研究对象固定为动态配置下的连续异步 FL 服务。模型借鉴 Turritopsis 的两个系统事实：配置由节点本地视图推进，诚实离开会造成尚未交付消息遗漏；本文将这两个事实重新映射到 FL 窗口，不直接复用其共识容错公式或协议状态。

模型定义了潜在节点集合、局部配置视图、客户端训练窗口、配置交接和滚动自适应腐蚀敌手。敌手可以根据公开配置和窗口事件选择腐蚀、释放、恢复和消息调度对象，但遵守认证和配置安装规则。攻击对象是窗口状态在配置边界上的系统行为，失败表现包括重复纳入、窗口复活、结果分歧、恢复放大、训练阻塞和历史状态增长。

方案主线收紧为三项机制：活动窗口的唯一归属与交接、完成窗口的只读封存记录、恢复节点按最新配置视图恢复活动状态。候选系统条件 `SC1-SC6` 分别覆盖配置后继顺序、窗口唯一归属、活动状态完整交接、封存后的准入类别、按当前视图恢复和后继配置的服务可用性。每条条件都配有可复现实验反例和日志指标。

本轮明确论文重点：动态成员机制服务于训练连续性、窗口结果稳定性和状态开销；密码学组件只提供更新保护接口。下一步先扩展事件轨迹中的滚动腐蚀与恢复状态，再核对 FLSim 客户端训练接口，不扩展新的密码学构造或长篇安全证明。

### 2026-09-13（P86：同步滚动腐蚀事件与系统实验计划）

更新 `experiments/EXPERIMENT_PLAN.md` 和 `reconfigurable-async-fl-system-spec.md`。实验主张改为：在异步客户端到达、委员会变化和滚动腐蚀下，活动窗口继续推进，已完成窗口保持同一结果。主要观测项改为窗口重开/重复纳入、接受集合一致性、模型版本推进、交接与恢复延迟、持久记录大小和模型质量。

事件轨迹新增 `node_corrupt`、`node_release` 和 `recover_state` 三类节点级事件，用于表示长期运行中的状态暴露和恢复选择。它们只描述服务节点控制与状态恢复，暂不引入单项解密或自适应查询。现有基础回放器保持不变，下一版回放器再实现这些事件。

本轮把 Turritopsis、动态 proactive secret sharing 和阈值刷新方案定位为配置交接和状态迁移对照。论文评价仍以动态 FL 服务行为为中心，密码学实现只作为更新保护和成本测量插件。

### 2026-09-13（P87：完成滚动腐蚀事件回放）

扩展 `experiments/reconfigurable_fl_sim.py` 和 `experiments/generate_reconfigurable_trace.py`，支持 `node_corrupt`、`node_release` 和 `recover_state`。节点腐蚀记录独立于崩溃和退出，释放后允许后续配置选择新的节点；恢复请求只安装当前配置下活动窗口的状态，已封存窗口继续产生拒绝记录。

使用真实的“生成 CSV，再加载 CSV”路径完成确定性回放检查：活动窗口恢复计数正确，滚动腐蚀峰值按释放保持为 1，配置转换中的腐蚀事件计数正确；Python 语法检查通过。系统规格和实验计划同步标记该事件支持已经完成。

下一步转向 FLSim API 映射和 live-training replay，保持节点级腐蚀轨迹与更新保护操作分离。

### 2026-09-13（P88：完成 FLSim API 映射核对）

通过公开仓库源码和 GitHub API 核对 FLSim 主分支，版本为 `7311f2db471f89f14a0c8c9ea1c9584171677f5a`。FLSim 的 `AsyncClientDevice` 负责本地训练并返回 `delta`、`final_local_model` 和 `weight`；`AsyncTrainer` 通过 `AsyncTrainingSimulator` 安排训练事件，并在内置路径中直接调用 `AsyncAggregator.on_client_training_end` 推进全局模型；`FedBuffAggregator` 按 buffer size 批量推进。

据此修订 `reconfigurable-async-fl-adapter-spec.md`：FLSim 负责客户端训练、训练完成顺序和陈旧度生成，外部窗口服务负责窗口归属、配置交接、封存和模型版本。FLSim 内置的即时全局更新路径不作为动态窗口裁决者。真实 FL 接入先使用 FLSim 客户端与事件调度组件，再将已接受窗口的聚合结果交给选定优化器。

本轮完成适配边界核对，未修改密码学模型。下一步是在外部设备按该边界实现 live-training bridge，并用固定配置轨迹比较四类窗口策略。

### 2026-09-13（P89：收紧 FLSim 与动态窗口服务的职责）

同步 `experiments/EXPERIMENT_PLAN.md` 的旧术语。FLSim 作为客户端训练事件和陈旧度的 workload 来源，动态窗口服务维护窗口归属、配置转换、封存和模型版本；APSS、DyCAPS 等工作进入状态迁移和服务成本对照，不进入主要 FL 准确率排名。

FLSim 的异步训练器内置了客户端更新后的全局模型推进路径，因此真实适配需要在该路径之前接入窗口服务，或者让窗口服务独立维护模型快照后再调用选定优化器。该结论成为 live-training bridge 的接口前提，避免将 FLSim 的默认异步聚合语义误认为本文的动态成员机制。

### 2026-09-13（P90：完成实验构建稿）

新建 `experiments/EXPERIMENT_BUILD.md`，将实验组织为客户端 workload、异步事件调度、窗口服务和聚合后端四层。文档固定了开源组件和职责：FLSim 负责客户端训练与异步事件，Buffalo 作为主要异步安全聚合基线，Flower SecAgg+ 作为同步安全聚合控制，Catalyst 作为异步 Byzantine 更新控制，APSS 和 DyCAPS 只作为状态迁移成本参考。

基线分为三类：本文服务内的 `Static`、`Full-transfer`、`Periodic-rekey` 和 `Selective-finality` 策略对照；Buffalo-native、Buffalo-reset、FedBuff/FLSim 和 Flower 的端到端外部对照；APSS、DyCAPS 和可复现后再纳入的 PPFA-BAA 补充对照。文档明确所有上游仓库保持原样，适配只负责 workload 转换、成员事件注入和日志采集；Buffalo-reset 单独标记为外部重启包装，不冒充 Buffalo 原生能力。

实验执行顺序固定为 trace semantics、cleartext model-bearing FL、protected-update integration、外部基线和动态故障评估。首个数据集采用 CIFAR-10，主指标为窗口完成率、模型版本推进、模型质量、交接/恢复延迟、重复窗口、持久状态和通信开销。该构建稿将密码学限制在更新保护插件和成本测量，不把实验推进为密码学安全分析。

### 2026-09-14（P91：完成本地文献与公开检索核对）

阅读 `papers/` 中新增的 `Setup Once, Secure Always`、Buffalo、异步 Byzantine 聚合和动态秘密共享相关材料，并用 Crossref/OpenAlex 检索 dynamic aggregation、dynamic membership、reconfigurable federated learning 等关键词。当前没有发现同时定义异步 FL、聚合委员会重配置、在途聚合状态交接和封存结果稳定性的直接工作。

文献边界整理如下：

| 路线 | 已解决的问题 | 尚未覆盖的本文问题 |
|---|---|---|
| `Setup Once, Secure Always` | 动态用户、用户掉线、单次 setup、前向和后向保密 | 中间服务器被假设为持续在线，没有聚合委员会重配置和窗口状态交接 |
| `Buffalo` | buffered asynchronous secure aggregation、assistant 掉线和聚合完整性 | assistant 集合变化需要重新建立 pairwise keys，或改用 share transfer；动态 assistant 被作为后续扩展 |
| 异步 Byzantine 聚合 | 多聚合器、异步网络、聚合器崩溃或 Byzantine 行为 | 聚合器集合固定，协议没有跨配置的在途窗口和历史状态语义 |
| 动态客户端/动态聚合 FL | 客户端选择、动态拓扑、动态边缘聚合点和陈旧度处理 | 没有安全聚合状态交接，也没有封存结果跨配置稳定性 |
| DyCAPS、Optimistic DPSS、Turritopsis | 动态委员会、秘密重分享、配置证明和异步状态追赶 | 目标不是 FL 客户端更新；未定义 `sid`、模型版本和 privacy frontier |

因此，论文不再把“动态成员安全聚合”作为宽泛问题，也不把“动态用户”写成创新。核心问题改写为：

> 当客户端更新已经进入传输或聚合过程，而聚合委员会发生变化时，异步 FL 如何继续推进学习，并让每个已确定的模型结果保持固定的参与集合和隐私边界？

长期滚动腐蚀保留为强化威胁模型。它用于说明普通秘密重分享只能保持秘密连续性，不能自动保证已完成 FL 窗口的隐私终结。本文的系统主张仍然是训练连续性、结果稳定性和状态开销；滚动腐蚀是检验交接规则的压力场景，不单独扩展为密码学论文。

基线角色进一步固定：`Buffalo` 是主要异步安全聚合基线，`Setup Once, Secure Always` 是动态用户安全聚合基线，异步 Byzantine 聚合是固定多聚合器故障基线，动态客户端和动态边缘聚合工作是训练调度基线。`DyCAPS`、`Optimistic DPSS` 和 `Turritopsis` 只用于交接语义和状态迁移审计，不直接声称它们被原论文中的安全定理击破。

下一步工作由“继续寻找更大的攻击”转为三项核对：明确 `Buffalo` 开源实现中的 assistant 状态边界，定义同一事件轨迹下四类窗口交接策略，确认 FLSim 或真实 FL 适配层能够记录模型版本、参与集合和交接结果。只有这些接口闭合后，才选择具体的阈值保护和状态恢复组件。

### 2026-09-14（P92：厘清长期滚动腐蚀的既有模型与本文边界）

本轮核对了 `Buffalo`、`Setup Once, Secure Always`、异步 Byzantine 聚合、DyCAPS、Optimistic DPSS 和 Turritopsis 的敌手描述，并回溯 proactive secret sharing 文献。结论是：长期滚动腐蚀已经有标准术语和模型谱系，通常称为 `mobile adversary`，并通过 proactive share refresh、secure erasure 或 epoch handoff 限制长期泄露。

现有材料的边界如下：

| 工作 | 正式敌手模型 | 与本文的关系 |
|---|---|---|
| `Buffalo` | 服务器和部分客户端/assistant 的恶意控制，另有掉线模型；安全分析使用固定腐蚀集合 | 异步安全聚合基线，不处理跨配置移动腐蚀 |
| `Setup Once, Secure Always` | 半诚实或恶意用户、intermediate server 和 Aggregator，按固定腐蚀集合证明；前向/后向保密针对轮次密钥 | 动态用户基线，不是动态聚合节点模型 |
| 异步 Byzantine 聚合 | 固定的 Byzantine 聚合器集合和客户端崩溃集合 | 固定聚合权威下的异步故障基线 |
| DyCAPS | 正式定义 PPT mobile adversary，可按 epoch 自适应腐蚀并释放节点，依靠 handoff、刷新和擦除维持长期秘密 | 最接近的动态委员会密码学模型 |
| Optimistic DPSS | 论文的正式模型以每个 epoch 的 static PPT adversary 为主，同时讨论逐步腐蚀带来的长期泄露风险 | 提供动态 DPSS 交接参照，但不等同于完整 rolling model |
| Turritopsis | 正式安全分析采用 static corruption；实验另测 partially mobile corruption | 动态异步 BFT 的运行参照，不承载 FL 窗口隐私语义 |

因此，本文需要定义滚动腐蚀模型，但不需要把它包装成新的通用密码学敌手。论文中应明确写成：**基于 mobile adversary 的 FL 专用组合模型**。已有模型规定腐蚀、释放、刷新和擦除的基本能力；本文增加 `sid`、模型版本、窗口参与集合、配置交接和 `PF_sid` 后的隐私终结作为应用对象。

本文敌手模型的最小形式固定为：每个配置 `C_r` 有瞬时腐蚀上限 `B_r`；敌手可以根据公开配置转换和异步消息选择腐蚀、释放、恢复和调度；释放节点不再接受新的主动控制，但已经读取的状态继续暴露；安全擦除是协议条件；敌手没有任意历史查询接口。对已封存窗口，成功事件是后继配置和敌手历史视图共同形成该窗口的合法单客户端开启能力。

这项定义的创新价值来自目标对象，而不是“mobile adversary”这个名称本身：传统 proactive sharing 保护长期秘密连续可用，本文还要求已完成 FL 窗口的开启能力随 `PF_sid` 终结。论文的安全性部分只需给出该组合目标、一个跨配置攻击轨迹和对应的条件性结论；正文重点仍然放在窗口推进、状态交接和模型训练。

### 2026-09-15（P93：确定 epoch-bounded mobile adversary 与 FL 证明路线）

本文最终采用 **epoch-bounded mobile adversary**，中文写作“受限的 epoch-mobile adversary”。每个 epoch 最多控制并读取 `f_r` 个委员会节点，敌手可以根据公开事件在相邻 epoch 之间选择新的控制对象，已经读取的状态继续保留在敌手视图中。活动窗口跨 epoch 时安装后继配置的新保护上下文，交接完成后清除旧 epoch 的可写状态；窗口封存后只保留结果记录。

该模型沿用动态委员会和 proactive sharing 中的周期状态刷新与安全擦除事实，把成功事件改写为 FL 窗口的跨配置状态复活。论文把它放在威胁模型中，不把它写成新的通用敌手理论。

证明路线收紧为三个正文结果：

1. **重配置透明性：** 唯一窗口归属、完整交接记录和后继服务条件保证已接受更新序列与带交接延迟的异步 FedBuff 执行一致。
2. **训练性质保持：** 在底层聚合器的陈旧度、Byzantine 比例和随机梯度条件成立时，交接只改变有效陈旧度，不改变聚合器面对的更新序列，因此沿用其收敛和鲁棒性界。
3. **隐私终结：** 在 epoch-bounded mobile adversary、封存后状态排除和安全擦除条件成立时，后继配置无法通过交接和恢复重新获得封存窗口的单客户端开启能力。

正文系统章节负责方案、实现和模型质量；隐私终结以一个条件性主定理支撑系统语义，详细原语证明放入附录。

### 2026-09-16（P94：重新核对异步 FL 中的动态成员处理）

本轮只核对异步联邦学习和安全聚合材料，不把动态 BFT 的成员变更流程当作 FL 的现成答案。结论是：现有异步 FL 工作中的“动态成员”至少包含三种不同对象，不能用一个加入或退出流程统一描述：

| 成员类型 | 现有异步 FL 的典型处理 | 是否改变系统密钥 |
|---|---|---|
| 客户端用户 | 每个聚合实例重新确定参与集合。用户提交更新即进入候选集合，掉线用户按协议从本次聚合中移除；后续实例可以重新加入 | 采用每次实例新鲜掩码时，不需要改变长期系统密钥 |
| assistant 或 decryptor | Buffalo 先固定候选 assistant 集合，再按本次 buffer 中仍在线的 assistant 子集完成恢复；掉线 assistant 不一定触发全局重配置，只要剩余门槛满足 | assistant 集合本身变化时，Buffalo 需要重新建立客户端与 assistant 的 pairwise key，或使用份额转移式的新保护后端 |
| 聚合委员会 | 现有异步 FL 安全聚合论文没有给出完整的委员会加入、退出、在途聚合状态交接和历史结果封存流程 | 需要改变委员会阈值份额或后继配置的保护上下文，不能把 assistant 掉线处理当作委员会重配置 |

#### 异步 FL 中动态客户端的完整语义

`Setup Once, Secure Always` 的动态性主要位于用户侧。用户不需要参加初始用户之间的密钥交换；每个训练实例使用新鲜随机掩码，允许获准用户在不同实例加入或退出。服务为本次实例收集至少门槛数量的受保护更新，用户掉线只影响本次实例的可用输入，不改变后续实例的系统密钥。该设计把“动态用户”转化为“每个实例重新确定参与集合”，没有处理聚合权威更换。

Buffalo 的异步语义更接近缓冲实例。客户端为自己的异步更新产生新鲜保护密钥，服务器收集达到 buffer 条件的更新，assistant 帮助恢复本次 buffer 的聚合密钥。assistant 在执行过程中可以掉线，协议使用仍在线 assistant 子集完成恢复，前提是门槛满足。Buffalo 明确指出，若 assistant 集合本身发生变化，现有 pairwise key 关系需要重新建立；另一条路线是使用能够进行份额转移的同态阈值加密，但会增加解密成本。

因此，现有论文给出的完整处理可以概括为：

```text
client joins an aggregation instance
    -> receives current model and instance context
    -> creates fresh protected update
    -> submits before the instance closes

client leaves or drops out
    -> its update is absent from this instance, or its already accepted
       protected update remains in the instance
    -> dropout recovery uses the remaining threshold
    -> later instances use a newly selected participant set
```

这套流程保护的是客户端参与集合和本次聚合的可用性。它没有回答聚合委员会离开后，谁继续持有在途实例的保护状态，也没有规定已经完成的实例是否还能进入后继配置的恢复路径。

#### 本文需要补齐的成员变更流程

本文必须把客户端动态和委员会动态分开写。建议协议使用以下完整流程：

```text
1. Request
   A node submits a join or leave request for the service membership.

2. Decide
   The current service membership mechanism authenticates the request and
   produces a successor configuration record. A local timeout or silence
   cannot by itself approve a membership change.

3. Prepare keys
   The successor committee establishes its configuration authentication key
   and threshold protection shares. New aggregation instances use the new
   protection context.

4. Freeze active instances
   Each active instance fixes a frontier. The old committee stops admitting
   new updates to that instance, while the service continues accepting new
   instances under the successor configuration.

5. Handoff
   The old committee transfers only the active instance state covered by the
   frontier. The successor verifies the configuration record, instance state,
   and current generation before installing it.

6. Confirm and erase
   The successor returns an installation confirmation. The old committee
   erases its writable state and keeps only a receipt. A failed confirmation
   leaves the instance recoverable only through the still valid old state.

7. Seal
   Once the instance produces its aggregate result, the service publishes a
   sealed record. Later configurations receive the result record, not the
   instance opening state.
```

加入和退出请求只改变后继配置的成员集合。密钥变化分三层处理：

1. 后继配置的阈值签名或认证密钥随配置变化；
2. 活动实例的保护状态在交接时刷新或重分享，生成新的 generation；
3. 已封存实例不再进入密钥交接，后继配置只保存封存记录。

客户端更新不需要因为委员会变更而全部重新训练。已经产生且位于 frontier 之前的更新继续完成；交接之后产生的新更新进入后继配置创建的新聚合实例。若保护后端支持对聚合状态进行份额重分享，客户端密文可以保持不变；若后端不支持这种状态迁移，则只能重新保护尚未完成的更新，或者放弃该实例并将其更新提交到新实例。这个选择必须在协议和实验中明确记录。

#### 当前方案的关键缺口

此前思路稿把“活动状态交接”写得过于抽象。真正需要固定的是：

```text
what moves:
    aggregate state, accepted update identifiers, model version,
    frontier, generation, and protection shares

what does not move:
    sealed instance opening state, retired shares, stale recovery messages,
    and client plaintext updates

when keys change:
    successor configuration installation, active instance handoff,
    and instance finalization use different key events
```

当前不应声称 Buffalo 可以直接承担本文的委员会交接。Buffalo 的 assistant 动态扩展本身已经指出，assistant 集合改变需要重新建立 pairwise key，或改用份额转移和同态阈值加密。本文需要先选择一个支持“活动实例保护状态可迁移、封存实例状态可排除”的后端，再把 Buffalo 放在外部异步安全聚合基线位置。

#### 交接性能的比较口径

交接损耗拆成四部分：

```text
freeze and frontier certification
active state transfer
successor key refresh or resharing
installation, confirmation, and old-state erasure
```

固定委员会的异步 FL 没有这些成本。Buffalo 的正常运行也没有委员会交接成本，但 assistant 集合改变时需要 pairwise key 重建或份额转移。动态用户安全聚合只在用户参与集合上变化，用户加入或退出不要求更换稳定的中间服务器和聚合权威。本文的额外成本来自聚合权威变化，重点指标为：

```text
handoff latency per active instance
handoff bytes per active instance
successor key refresh time
model staleness increase
throughput loss during configuration change
sealed record bytes per finalized instance
```

交接成本不能只报告总时间。若一次配置变化同时存在 `m` 个活动实例，状态传输和保护状态刷新会按活动实例数增长。若保护后端只能转移逐客户端记录，成本还会随本次实例中的 `k_sid` 增长；若后端能转移紧凑聚合状态，成本可以主要随模型维度和委员会规模增长。该差异是本文实验中最重要的系统问题之一。

### 2026-09-16（P95：确定下一步研究任务）

下一步不继续扩展动态 BFT 相关讨论，也不立即实现完整密码学协议。先完成以下三项闭合工作：

1. **固定成员语义。** 在系统规格中分别定义客户端加入或退出、assistant 掉线、聚合委员会加入或退出三种事件，明确每种事件是否改变密钥上下文、是否影响活动实例和是否影响已封存实例。
2. **固定交接后端。** 选择一个可以表达“活动实例份额刷新，封存实例不交接”的最小保护后端。先以抽象阈值聚合状态完成协议回放，再评估 Buffalo 式逐客户端保护状态能否迁移。
3. **做交接微基准。** 在相同模型维度、活动实例数、委员会规模和配置变化轨迹下，测量固定委员会、全量迁移、周期重建和选择性交接的等待、通信、状态大小、模型陈旧度和吞吐损耗。

完成这三项后，再进入真实 CIFAR 10 异步训练。真实训练需要回答的首个问题不是最终准确率，而是：交接期间活动实例是否继续完成，模型版本是否连续，交接等待是否表现为可量化的陈旧度，以及交接成本是否随历史窗口数量保持有界。

### 2026-09-16（P103：完成异步联邦学习成员变更与密钥语义审计）

本轮只核对异步联邦学习和安全聚合文献，不把分布式共识的成员交接模型作为联邦学习成员管理的依据。审计对象包括 Buffalo、Setup Once, Secure Always，以及异步拜占庭联邦学习工作。结论是：现有工作主要解决“客户端在不同聚合批次中动态参与”，没有完整定义“聚合委员会在活动异步聚合过程中加入、退出并迁移保护状态”的服务流程。

#### 1. 现有异步联邦学习工作的实际处理

Buffalo 采用 buffered asynchronous FL。服务器维护可用客户端集合和当前缓冲区，客户端完成本地训练后独立提交更新；服务器收集达到缓冲区大小的首批更新，形成一次聚合并清空缓冲区。客户端是否参加某个缓冲区由提交时机决定，客户端没有在提交前获知同批次的其他客户端。客户端掉线表现为本次更新没有进入缓冲区，超时或未提交不会触发全局密钥更新。

Buffalo 的主协议有固定的 assistant 集合。初始设置阶段，客户端注册公钥，并与每个 assistant 建立 pairwise key。每个聚合实例使用新的 LWE 密钥和 JL 密钥保护更新，客户端再把必要的密钥材料通过秘密共享和认证加密交给 assistant。这样，客户端的每次更新可以独立进入异步缓冲区，但 assistant 集合本身并没有在主协议中完成动态交接。

Buffalo 在扩展部分讨论 assistant 动态化：客户端需要在发送保护更新前知道新的 assistant 集合，并为新的 client assistant 对建立 pairwise key。因此 assistant 集合改变时需要重新建立相关密钥。论文没有给出旧 assistant、活动缓冲区、已经提交的保护更新和新 assistant 之间的完整状态迁移协议。这一结论只能支持“动态 assistant 会引入密钥重建成本”，不能作为本文活动委员会交接的现成方案。

Setup Once, Secure Always 处理的是动态客户端集合，而不是动态聚合委员会。其每轮使用新鲜随机掩码，客户端无需在初始设置阶段与其他客户端预先建立长期共享种子。新客户端在获准后可以直接参与当前聚合，退出客户端停止提交；中间服务器和聚合器根据实际收到的掩码更新形成共同的活跃客户端集合，只对共同集合进行聚合。掉线客户端的更新被排除，不需要恢复其掩码。由于客户端掩码按轮独立生成，客户端加入或退出不会触发全局密钥重建。

这两类工作中的“动态”都发生在客户端参与集合层面。它们没有改变聚合权威的保护上下文，也没有回答一个活动异步聚合已经接收部分更新后，委员会自身发生变化时如何继续聚合。因此本文需要把客户端动态参与和委员会动态重配置分成两个层次。

#### 2. 本文的完整成员变更语义

本文将成员分成客户端和聚合委员会节点。两者的加入、退出和密钥变化如下：

| 对象 | 加入 | 退出或掉线 | 是否改变委员会密钥 |
|---|---|---|---|
| 客户端 | 通过身份认证后，在当前活动实例使用该实例的保护上下文提交；若错过接收截点，则在后继实例重新保护并提交 | 尚未被接收的更新直接消失；已经接收的更新仍属于原实例，客户端离开不撤销已接收更新 | 否 |
| 聚合委员会节点 | 在后继配置生效后获得新配置的阈值份额，并只安装允许迁移的活动实例状态 | 在配置生效点后停止写入；退出前或恢复机制中提供必要的交接份额；旧状态随后擦除 | 是，刷新配置上下文和活动实例份额 |

客户端加入不需要改变委员会密钥。客户端只需要通过当前配置的认证，获得当前实例的公开保护参数，并提交一次带有实例标识和模型版本的更新。客户端退出也不触发重密钥：已经进入 frontier 的更新继续参与聚合，尚未进入 frontier 的更新没有原实例的状态效果。该语义与 Buffalo 和 Setup Once, Secure Always 对动态客户端参与的处理一致，但本文还增加了异步交接后的重新提交规则。

委员会加入意味着后继配置获得新的成员集合和新的阈值保护上下文。新节点不能直接继承旧节点的写入权限，也不能从配置记录恢复已经封存实例的开启材料。对于仍然活动的实例，旧委员会把聚合状态的共享值重分享给后继委员会；秘密值和已接受更新集合保持不变，分享多项式、节点份额、配置编号和写入权限发生变化。对于已经封存的实例，不执行重分享，只传播结果记录、参与集合和封存证明。

委员会退出不是简单地从成员列表中删除一个身份。退出配置必须包含生效边界，边界之前的旧配置继续处理已接收状态，边界之后的新配置处理新实例。旧节点在确认交接后删除活动实例份额、恢复材料和旧配置写入状态，只保留不可开启的交接回执。若旧节点在交接前崩溃，系统只有在剩余节点满足恢复门槛时继续交接；否则该活动实例保留在旧配置中，后继配置不能创建第二个可写副本。恢复节点重新加入后继配置时按新成员处理，不自动恢复旧配置的写入权。

#### 3. 密钥变化的精确定义

论文不再使用“成员变化后密钥全部更新”这一笼统表述，而是区分三类密钥状态：

1. 身份认证密钥用于识别客户端和委员会节点，可以保持长期有效。成员加入需要注册，成员退出需要撤销或标记为不属于后继配置，但不要求所有参与者重新建立身份密钥。
2. 配置级阈值上下文随委员会配置变化。后继配置拥有新的成员索引、阈值份额和配置验证材料。该上下文决定谁可以写入和开启当前配置下的活动聚合状态。
3. 实例级聚合状态在活动交接时重分享。重分享保持聚合状态的语义值不变，但不保留旧节点的份额。实例封存后删除该状态，后继配置只接收封存记录。

因此，委员会变化会改变保护上下文和份额，不一定改变活动聚合的逻辑值；客户端加入和退出不会改变委员会密钥。前向安全和后向安全可以作为实例级保护的附加性质，但它们本身不定义成员变更的生效边界、活动状态的迁移范围或封存状态的排除规则。

#### 4. 交接期间的异步训练路径

配置变化不暂停整个联邦学习服务。旧配置先为每个活动实例确定接收截点，并记录 `frontier`、模型版本、已接受更新集合和当前聚合状态。旧配置可以继续处理截点前已经接收的更新。交接完成后，后继配置安装活动状态并处理新的聚合实例；客户端使用新的保护上下文提交后续更新。

截点后仍在网络中传播的旧上下文更新不会被强行转换为后继配置的更新。服务拒绝该更新，并向客户端返回 `client_resubmit` 所需的模型版本和后继实例标识。客户端使用后继上下文重新保护同一训练结果后再提交。这样既避免旧密文与新委员会保护状态混用，也避免客户端因为委员会变化而重新执行本地训练。

这一流程与已有异步联邦学习工作的差别在于：已有工作把未及时提交的客户端更新视为本批次之外的更新；本文还需要处理一个已经部分接收、部分聚合的活动实例，并保证该实例在委员会交接后只有一个可写状态。

#### 5. 本轮裁决与下一步

当前可以固定以下论文表述：

> 异步联邦学习已有动态客户端参与机制，但没有解决聚合委员会变化时活动聚合状态如何连续迁移的问题。本文把客户端动态参与、委员会配置变化和实例级保护状态分开处理：客户端加入和退出不触发委员会重密钥，委员会变化则刷新配置级阈值上下文，并只对未封存实例执行聚合状态重分享。

下一步按以下顺序执行：

1. 在系统规格中补齐客户端事件和委员会事件的状态转移表，尤其固定交接前已经提交但尚未进入 frontier 的更新如何处理。
2. 审计候选保护后端是否分别支持客户端更新保护、活动聚合状态重分享、封存后状态清除和移动腐蚀下的安全擦除。
3. 在抽象回放器中加入客户端新加入、客户端退出、委员会加入、委员会退出和退出节点崩溃五类轨迹，验证单写入权、客户端重提交和封存不可复活。
4. 之后再选择真实密码学实现。若候选后端只能迁移逐客户端保护材料，就把重新保护或实例放弃作为明确对照，不把它隐藏在交接实现中。

### 2026-09-16（P96：把交接方案落到可实现的保护状态）

本轮完成了方案契约的第一次收敛，重点是让“动态委员会”成为联邦学习协议中的可验证状态迁移，而不是把密钥更新泛化为一个工程步骤。

#### 成员事件的正式划分

加入和退出是配置事件，改变后继委员会集合。崩溃和恢复是可用性事件，不自动改变配置；恢复节点只有在后继配置中重新出现时才获得写入权。退出节点再次出现按照加入处理，不能直接恢复旧配置中的写入权。客户端加入和退出仍然按聚合实例重新确定参与集合，assistant 掉线只影响当前实例的恢复门槛，委员会变更才触发活动实例交接。

#### 保护后端的首选实例化

第一版协议采用 PVSS 加按实例聚合的阈值共享。客户端更新被编码为可验证份额，委员会节点只在本地累加份额，活动实例记录保存聚合值的阈值共享和已接受更新标识。配置转换时，旧委员会对聚合共享执行异步可验证重分享，后继委员会安装新的 `Share_{r+1,sid}`，不重构聚合明文，也不搬运逐客户端开启材料。封存后删除活动共享，后继配置只读取结果记录。

这一选择把密码学组件的职责限定为三件事：客户端更新保护、活动聚合共享的重分享、封存前后的状态清除。DKG 或等价的阈值上下文建立过程提供新委员会的共享上下文；前向安全加密可以作为附加保护，但不承担实例归属、交接边界或封存语义。

#### 交接状态契约

活动记录固定为：

```text
sid, model_version, accepted_update_ids,
frontier, generation, share_context,
aggregate_share, handoff_status
```

`frontier` 是旧配置已经接受的最后记录版本和更新集合，不表示消息发送时间。边界确定后仍在网络中的旧上下文更新不进入原实例，客户端可以在后继配置创建的新实例中重新提交。旧配置在安装确认前保持唯一写入权；确认后才删除活动共享和逐客户端保护材料。确认失败时重试同一交接或继续使用旧配置，不产生两个可写副本。

封存记录只包含模型结果、模型版本、参与集合、配置历史和封存证明，不包含活动聚合共享、旧保护上下文或恢复材料。该排除规则把结果稳定性和隐私终结连接起来，也使封存记录的迁移成本与历史活动窗口数量分离。

#### 当前论文方案

协议流程固定为：配置服务确认后继配置，旧配置为每个活动实例固定接收截点，旧委员会对聚合共享执行可验证重分享，后继委员会验证交接记录并安装 `generation + 1`，安装确认后旧状态清除，新配置继续完成已经接受的更新，未接受更新进入新的聚合实例，最终结果进入只读封存记录。

论文方案章节应围绕这一流程给出一个整体概述、一个活动实例记录定义和一段伪代码。证明保留重配置透明性、结果稳定性和隐私终结三个结果；收敛性只说明交接增加有效陈旧度，不把论文扩展成新的优化算法。实验先用抽象阈值共享状态验证交接，再接入 PVSS 和真实 FL 训练。

#### 下一步

先扩展 `experiments/reconfigurable_fl_sim.py` 的记录模型，使模拟器显式记录 `frontier`、`generation`、保护上下文版本、活动聚合状态大小、交接阶段和确认失败路径；随后生成包含未接收迟到更新的轨迹，验证它们被重新提交到新实例而不是重复进入旧实例。微基准通过后再实现 PVSS 保护插件和 FLSim 训练适配器。

### 2026-09-16（P97：完成最小交接回放器）

本轮把方案契约映射到 `experiments/reconfigurable_fl_sim.py` 和 `experiments/generate_reconfigurable_trace.py`，完成了第一阶段的可回放闭环。

实现内容：

1. 轨迹增加 `protection_context` 和 `handoff_confirm` 事件；交接路径现在区分活动状态导出、后继安装和安装确认。
2. 窗口记录增加 `frontier_record_version`、`generation`、保护上下文、交接状态和交接字节。`frontier` 使用已接受记录版本表达，不把消息发送时间假设成全局顺序。
3. 确认完成后，后继配置取得窗口写入权并递增 `generation`；确认失败时，旧配置仍可封存已接受更新，后继配置不能写入该窗口。
4. `Full-transfer` 继续迁移已封存记录，`Selective-finality` 只迁移活动记录；两类策略在同一轨迹下保持可比较的状态规模差异。

验证结果：

```text
normal trace:   64 events -> 32 window records, all strategies replayed
failed handoff: sid-1 finalizes with owner_configuration=C0 and generation=0
```

该回放器仍然是服务语义模型，不代表 PVSS 已经接入。下一步先补充“确认失败后客户端重提交到新实例”的轨迹和结果字段，再实现抽象阈值共享插件，最后接入真实异步 FL 训练。PVSS 的协议参数和 Buffalo 的原生保护流程继续分开记录。

### 2026-09-16（P98：补齐接收截点后的更新重提交）

本轮把交接边界落实为可观察的两步行为：

```text
old-context client_update after frontier
    -> rejected by the old instance
client_resubmit(source_window, new_window, new_context)
    -> accepted by the successor instance
```

回放器新增 `client_resubmit` 事件和 `source_window` 字段。源实例不增加参与集合，目标实例使用后继配置的保护上下文并单独记录 `resubmitted_updates`。`Static` 和 `Periodic-rekey` 会保留旧实例的接收行为，`Selective-finality` 和 `Full-transfer` 会执行截点与重提交，因此同一轨迹可以直接比较不同策略对客户端更新的处理。

这一行为明确了协议的训练语义：交接不试图判断异步网络中的发送时间，而是以旧配置已经接受的记录为边界。客户端更新不会被静默丢弃，未进入旧实例的更新通过新实例重新参与训练；已进入旧实例的更新不会在新实例重复计入。

验证重点新增两项：源实例的 `accepted_clients` 在重提交前后保持不变，目标实例只增加重提交客户端；重提交使用新 `protection_context`，不携带旧实例的可写保护状态。下一步进入抽象阈值共享插件，插件只模拟份额累加、重分享、安装和清除，不改变这套窗口事件语义。

当前生成器输出 82 条事件和 44 个窗口记录。对 `sid-1` 的选择性交接回放显示：源实例由 `C1` 继续拥有，旧上下文更新被拒绝 1 次；`sid-1-reroute` 由 `C1` 接收 `late-sid-1`，`resubmitted_updates=1`，保护上下文为 `ctx-C1-1`。这一区分把客户端更新的重路由成本和活动状态交接成本分开记录。

### 2026-09-16（P99：固定抽象阈值共享后端接口）

为避免在窗口语义尚未稳定时引入完整密码学实现，新增 `experiments/abstract_threshold_backend.py` 作为交接微基准后端。它提供七个操作：

```text
open_state
admit_update
export
reshare
confirm
seal
erase
```

后端记录每个活动实例的保护上下文、维度、已接受更新标识、交接阶段和估算状态字节。`export` 固定接收截点，`reshare` 生成后继配置的 `generation + 1` 状态，`confirm` 之后旧状态才可以清除；`seal` 只输出结果记录，`erase` 清除活动共享。后端不保存明文向量，不重构聚合秘密，也不声称提供 PVSS 安全性。

这个接口与论文方案的对应关系已经写入实验构建稿和适配规格。下一步用它对不同维度、委员会规模和活动实例数运行交接微基准，确认状态字节与交接通信量的增长关系，再将同一接口替换为 PVSS 实现。

### 2026-09-16（P100：建立交接成本微基准入口）

新增 `experiments/handoff_microbench.py`，以抽象后端执行一个完整的多实例交接路径：旧配置建立活动聚合状态，接收更新，固定 `frontier`，重分享给后继配置，确认安装，封存结果并清除旧状态。

微基准输出以下量：

```text
source_state_bytes
successor_state_bytes
handoff_bytes
sealed_record_bytes
```

参数覆盖模型维度、旧新委员会规模、阈值、活动实例数量和每个实例的更新数量。该入口只测量状态和通信规模，不把抽象后端当作 PVSS；后续替换后端后复用相同参数和输出字段。

一次验证运行使用维度 1024、8 个活动实例、每实例 16 个更新和阈值 3。委员会从 4 个成员变为 6 个成员时，源状态累计为 `1,049,600` bytes，后继状态为 `1,573,888` bytes，交接通信量为 `2,623,488` bytes，封存记录为 `768` bytes。该结果符合状态规模随活动实例数、模型维度和后继委员会规模增长的预期。

### 2026-09-16（P101：完成交接成本参数扫描）

在固定阈值 3、每实例 16 个更新的条件下完成三组扫描：

| 变化因素 | 参数范围 | 交接通信量变化 |
|---|---|---|
| 模型维度 | 256、1024、4096；4 到 6 个成员；8 个活动实例 | `657,408` -> `2,623,488` -> `10,487,808` bytes |
| 活动实例数 | 1、8、32；维度 1024；4 到 6 个成员 | `327,936` -> `2,623,488` -> `10,493,952` bytes |
| 后继委员会规模 | 4、6、8；维度 1024；8 个活动实例 | `2,099,200` -> `2,623,488` -> `3,147,776` bytes |

扫描确认本文的“紧凑状态”应准确表述为：交接状态不随客户端保护载荷数量线性增长，但随模型维度、活动实例数和委员会规模增长。该结果修正了早期 `O(d + |A_sid|)` 的过强表述，当前方案的活动状态为 `O(n*d + |A_sid|)`，从旧委员会到新委员会的交接通信为 `O(m*(n_old+n_new)*d)` 加上记录和配置证明开销。

下一步不再扩展抽象后端功能，转向把该接口映射到 PVSS 或可验证重分享实现，并保持同一组参数和输出字段，以便区分状态规模收益与具体密码学实现成本。

### 2026-09-16（P102：区分 PVSS 分发与跨配置重分享）

本轮固定密码学接口边界：PVSS 只负责客户端更新在当前委员会中的可验证份额分发；活动实例从 `C_r` 迁移到 `C_{r+1}` 由异步可验证重分享完成。后者输入聚合份额、接收截点和旧保护上下文，输出后继配置的 `generation + 1` 聚合份额，不重构聚合明文。

适配规格现在使用以下抽象操作：

```text
setup_context
protect_update
accumulate
export_aggregate
reshare_aggregate
open_aggregate
erase
```

这一区分避免把“PVSS 能够分发份额”误写成“PVSS 自动解决委员会交接”。下一步只审计一个候选 PVSS 或阈值聚合实现是否能提供 `protect_update` 和 `accumulate`，再单独选择可验证重分享实现；窗口服务和实验轨迹保持不变。

### 2026-09-16（P104：成员变更审计的最新裁决）

本轮关于加入、退出和密钥变化的完整结论已经写入 P103。最新裁决如下：

1. 现有异步联邦学习工作中的动态成员主要指客户端参与集合。Buffalo 以缓冲区收到的更新决定本次聚合参与者，客户端掉线只导致更新不进入当前缓冲区；其主协议的 assistant 集合固定，动态 assistant 只在扩展部分讨论，集合变化需要重新建立 client assistant pairwise key。
2. Setup Once, Secure Always 允许客户端在不同聚合轮次加入和退出，使用每轮新鲜随机掩码，因此客户端成员变化不触发委员会密钥变化。该工作没有处理聚合委员会本身变化时的活动状态迁移。
3. 本文必须区分客户端成员和聚合委员会成员。客户端加入和退出不改变委员会密钥；委员会加入和退出改变后继配置的阈值上下文，并对未封存实例的聚合共享执行重分享，已封存实例只传播结果记录。
4. 下一步先在系统规格中固定两类事件的状态转移和交接前后的更新归属，再审计真实保护后端，最后把客户端加入、客户端退出、委员会加入、委员会退出和退出节点崩溃加入回放轨迹。

### 2026-09-16（P105：把成员审计结论落成协议方案）

本轮完成了方案层收敛，并同步更新 `reconfigurable-async-fl-system-spec.md` 和 `reconfigurable-async-fl-privacy-finality-idea-draft.md`。

方案现在明确区分两类成员：客户端加入和退出只改变提交资格，不改变委员会密钥；聚合委员会加入和退出形成后继配置，刷新配置级阈值上下文，并对未封存实例的聚合共享执行重分享。身份认证密钥可以保持稳定，活动实例的逻辑聚合值保持不变，实例级共享份额和写入权限随交接变化。

完整路径固定为：成员请求确认，后继配置发布，在生效点授予提交资格或阈值份额，旧配置固定 `frontier`，活动状态重分享，后继配置安装并确认唯一可写状态，旧状态清除，后续客户端更新进入新实例。已封存实例只传递封存记录，迟到旧上下文更新由客户端使用新上下文重新提交。

回放器新增 `client_join`、`client_leave` 和 `committee_join` 事件。客户端退出后的更新会被拒绝，客户端重新加入后可以使用当前上下文提交；委员会加入会把节点加入可用节点集合，不改变已有窗口的交接状态。轨迹生成器新增 `--include-membership-events`，可以在同一异步轨迹中注入客户端和委员会成员事件。

下一步是运行带成员事件的完整轨迹，检查客户端资格、活动窗口唯一写入权、交接后的保护上下文和封存结果，再进入候选 PVSS 与可验证重分享后端的接口审计。

### 2026-09-16（P106：完成成员事件回放验证）

本轮完成成员事件的最小实现和文档同步。系统规格新增客户端资格单调、配置上下文隔离两个不变量，以及客户端加入、客户端退出、委员会加入和委员会退出的故障轨迹。思路稿新增成员变更与密钥上下文小节，明确身份认证密钥、配置级阈值上下文和实例级聚合共享的三层关系。

回放器新增 `client_join`、`client_leave` 和 `committee_join` 事件，轨迹生成器提供 `--include-membership-events` 选项。使用两次配置转换、三窗口并发和成员事件的轨迹回放结果为：客户端退出后的旧上下文提交进入对应窗口的拒绝计数，后继配置中重新加入的客户端进入新窗口，活动窗口仍按 `generation` 和新 `protection_context` 完成交接与封存；`graft check` 通过。

当前方案已经可以进入保护后端构建。下一步不再扩展成员事件类型，先为 `protect_update`、`accumulate`、`reshare_aggregate`、`open_aggregate` 和 `erase` 建立一个候选后端能力矩阵，再选择一条真实可实现的 PVSS 加可验证重分享组合接入抽象后端。

### 2026-09-16（P107：确定首个保护后端方向）

本轮审计了 Buffalo、Efficient Verifiable Secret Sharing with Share Recovery、Threshold Encryption with Silent Setup 和现有适配接口，调整了后端选择。

首个实现不直接采用“PVSS 加重分享”作为默认方案。PVSS 可以提供可验证份额分发，VSSR 可以提供同一配置内的份额恢复，但二者都不能单独提供本文需要的跨委员会活动状态重分享。Silent Threshold Encryption 支持不同 decryptor universe，但原语本身不提供联邦学习向量聚合，也不会自动迁移旧 universe 的活动密文。

当前首选是 Buffalo 兼容的两层后端：向量更新使用 LWE 保护，实例密钥材料使用加法同态阈值加密保护，委员会只对已经接受更新的聚合密钥份额执行可验证转移。交接状态包含受保护向量聚合值、受保护密钥聚合值、聚合密钥份额、`frontier` 和 `generation`。后继委员会只开启聚合向量，封存后删除可写份额。

这一选择带来一个明确的实现风险：Buffalo 指出 TEG share transfer 可以支持动态 assistant，但阈值开启可能引入额外离散对数计算。下一步先在抽象后端中加入 `aggregate_key_share` 和 `encrypted_key_sum` 两类状态，再实现一个只测量转移与开启成本的 Buffalo 兼容插件。只有性能和接口审计通过后，才接入真实 Buffalo 密码学代码。

### 2026-09-16（P108：分离委员会退出与节点崩溃）

为保证成员语义完整，回放器和事件规格新增 `committee_leave`。`committee_leave` 表示配置变更中的永久成员退出，`node_crash` 表示暂时不可用，`node_recover` 只恢复可用性。旧轨迹中的 `node_leave` 保留兼容，带成员事件的新轨迹使用 `committee_leave`。

这样，方案中的四类事件已经可以分别表达：客户端加入、客户端退出、委员会加入、委员会退出；崩溃和恢复作为可用性事件独立处理。下一步进入聚合密钥状态的抽象建模，不再增加成员事件种类。

### 2026-09-16（P109：把首选后端写入方案章节）

本轮将保护后端从“PVSS 加重分享”的候选描述调整为更贴近异步联邦学习的 Buffalo 兼容两层方案。客户端更新使用向量级 LWE 保护，实例密钥材料使用加法同态阈值加密保护；委员会节点累加受保护向量和受保护密钥材料，交接只转移活动实例的聚合密钥份额。

方案稿现在给出了 `C_sid`、`E_sid` 和 `[K_sid]_i` 的聚合公式，明确 `pk_sid` 和受保护聚合值在活动交接中保持不变，份额持有者集合、`generation` 和保护上下文发生变化。交接消息固定为 `Update`、`Admit`、`Freeze`、`ShareTransfer`、`Install`、`Confirm` 和 `Seal`。后继委员会只开启聚合向量，封存后删除所有可写份额。

该选择保留了 FL 论文需要的向量保护和异步缓冲路径，同时把动态委员会新增的密码学工作集中到聚合密钥转移。PVSS、VSSR 和 Silent Threshold Encryption 改为能力对照，不再作为默认实现。下一步是为抽象后端补充 `encrypted_update_sum`、`encrypted_key_sum` 和 `aggregate_key_share` 的状态模型，并单独测量转移与开启成本。

### 2026-09-16（P110：完成聚合密钥状态的抽象建模）

抽象后端现在显式区分三类活动状态：`encrypted_update_sum`、`encrypted_key_sum` 和 `aggregate_key_share`。单个活动实例的估算状态为：

```text
metadata + 2 * dimension * element_bytes
         + committee_size * key_share_bytes
```

这对应首选 Buffalo 兼容后端的状态语义。它不保存逐客户端保护载荷，接受更新标识作为窗口元数据独立记录。维度 1024、8 个活动实例、委员会从 4 个成员变为 6 个成员时，抽象微基准得到：源状态 `526,336` bytes，后继状态 `526,848` bytes，交接通信量 `1,053,184` bytes，封存记录 `768` bytes。

此前按每个委员会成员保存完整向量份额的扫描结果保留为上界对照，不再作为首选后端的复杂度描述。下一步实现同一接口的 Buffalo 兼容保护插件，首先测量向量开启、聚合密钥转移和委员会规模变化的 CPU 与通信成本。

### 2026-09-16（P111：补齐动态联邦学习中的加入、退出与密钥处理）

本轮重新核对 Buffalo 和 `Setup Once, Secure Always` 对动态成员的实际处理，并把它们与本文的委员会重配置问题分开。结论是：现有异步联邦学习工作已经能够处理客户端参与集合变化，但没有给出聚合委员会在活动缓冲区中加入、退出后继续完成同一聚合的完整流程。

#### 1. 现有异步联邦学习工作的完整边界

Buffalo 的基本单位是异步缓冲区。客户端完成本地训练后独立提交更新，服务器收集先到的更新，缓冲区达到容量后完成一次聚合并清空。客户端是否进入某个缓冲区由更新到达决定，客户端掉线只表示该更新没有进入当前缓冲区。已经上传的受保护更新仍然属于原缓冲区，客户端之后离线不会撤销这条更新，也不会触发全局密钥变化。

Buffalo 的原生 assistant 集合在设置阶段建立。每个客户端与 assistant 建立 pairwise key，并在每个异步缓冲区使用新鲜的 LWE 密钥和聚合密钥材料。论文的动态 assistant 讨论给出两种方向：客户端预先获知新的 assistant 集合并重新建立 pairwise key，或者改用支持 share transfer 的加法同态阈值加密。前者需要重新建立客户端与 assistant 的密钥关系，后者需要承担更高的开启成本。论文没有把旧 assistant、活动缓冲区、已经提交的密文和新 assistant 组织成一个可以继续运行的委员会交接协议。

`Setup Once, Secure Always` 的动态性位于客户端集合。每个实例使用新鲜随机掩码，获准客户端可以加入后续实例，退出客户端停止提交；服务按照实际收到的更新形成当前参与集合。客户端加入和退出不要求改变长期系统密钥。该工作同样没有处理聚合权威变化时活动实例的保护状态迁移。

因此，现有工作的成员处理可以准确写成：客户端加入当前实例需要获得当前公开参数并提交新的受保护更新；客户端退出或掉线使尚未提交的更新离开当前实例，已经接收的更新继续参与原实例；后续实例重新确定客户端集合。该处理没有覆盖委员会密钥份额的转移。

#### 2. 本文的完整成员变更路径

本文把客户端和聚合委员会作为两类不同成员。客户端变化只改变提交资格，委员会变化才触发活动聚合状态交接。

客户端加入时，服务完成身份认证和当前配置检查，返回当前模型版本、实例标识和保护上下文。客户端在本地训练后，用该实例的公开保护参数生成一次新的受保护更新，服务验证实例归属、模型版本和 `update_id` 后纳入聚合。客户端加入不改变委员会密钥，也不要求已有客户端重新建立密钥。

客户端退出时，服务停止向该客户端分配新的训练任务，并撤销其后续提交资格。已经被旧实例接收的更新保持在该实例中，不能因为客户端退出而删除或重新计数。尚未被接收的更新不进入旧实例。若更新在接收截点之后到达，服务返回后继实例和当前保护上下文，客户端使用新上下文重新保护后提交；模型版本不兼容时，客户端下载当前模型并重新训练。客户端退出和重新加入都不触发委员会重密钥。

委员会加入或退出先产生后继配置记录，记录前驱配置、成员集合、阈值、配置生效边界和配置验证材料。旧配置在后继配置完成安装确认前仍然是活动实例的唯一写入方。对于每个尚未封存的实例，旧配置执行以下路径：

```text
publish successor configuration
    -> fix frontier for the active instance
    -> stop admitting old-context updates
    -> refresh and transfer the aggregate secret shares
    -> successor verifies and installs generation + 1
    -> successor confirms the unique writable state
    -> old members erase writable shares and recovery material
    -> new updates use a successor instance and successor context
```

交接传递的是活动实例的聚合状态、已接受更新标识、模型版本、`frontier`、`generation` 和新的聚合密钥份额。受保护的聚合向量和聚合密钥材料可以保持不变，前提是后端支持在同一实例公钥下进行份额转移。交接改变的是份额持有者集合、配置上下文和写入权限。后继委员会不能从旧配置记录中恢复已经封存实例的开启材料。

委员会退出不是立即删除成员身份。退出成员在生效边界前参与交接，后继委员会完成安装确认后，退出成员删除活动实例份额、恢复材料和旧配置写入状态，只保留不能开启聚合结果的交接回执。退出成员在交接前崩溃时，旧配置只有在剩余成员满足恢复门槛时才能完成交接；后继配置不能在没有安装确认的情况下创建第二个可写副本。节点恢复只恢复可用性，恢复节点必须按照当前配置重新获得份额，不能自动恢复旧配置的写入权。

#### 3. 密钥是否改变

密钥变化分为三层：

| 密钥或状态 | 客户端加入或退出 | 委员会加入或退出 | 作用 |
|---|---|---|---|
| 身份认证密钥 | 保持有效，成员资格通过配置记录控制 | 节点加入注册，退出撤销后继配置资格 | 识别提交者和配置成员 |
| 新实例的公开保护参数 | 使用当前实例参数 | 后继实例生成新的参数 | 保护新提交的客户端更新 |
| 活动实例的聚合密钥份额 | 不变 | 通过刷新或重分享生成后继配置份额 | 让后继委员会继续开启同一活动聚合 |

本文的首选后端保留活动实例的逻辑聚合密钥和受保护聚合值，改变其阈值份额和配置编号。份额刷新必须配合旧份额的安全擦除；否则离开的委员会成员仍可能使用旧份额参与恢复。受限的 epoch mobile adversary 模型要求每次交接后旧活动份额完成擦除，并限制单个 epoch 中被腐蚀并暴露份额的委员会成员数量。新实例使用新保护上下文，已封存实例删除可开启状态，只保留模型结果、参与集合和封存证明。

这一区分也明确了 Buffalo 的位置：Buffalo 原生方案可以作为异步安全聚合基线，但不能直接声称支持本文的委员会交接。本文需要增加一个支持活动聚合密钥份额刷新和转移的保护后端适配，或者把“重新开启新实例并重新保护更新”作为明确的失败对照。不能把 pairwise key 重建简写成活动状态已经迁移。

#### 4. 本轮更新后的研究判断

本文研究问题现在可以表述为：

> 当客户端更新持续异步到达，聚合委员会发生加入或退出时，如何让已经部分接收的活动聚合继续推进，同时保持更新只计入一次、旧配置不再写入、已封存结果不重新开启，并控制状态交接对模型推进和训练吞吐的影响？

这个问题仍然是异步联邦学习的系统问题。密码学组件负责保护更新和转移活动聚合份额，论文主体评价的是模型版本连续性、活动实例完成率、陈旧度、交接延迟和训练吞吐，而不是扩展为新的通用密码学原语。

### 2026-09-16（P112：确定本轮对话后的下一步）

下一步先完成协议语义闭合，再进入真实密码学实现。顺序固定为：

1. 在实验记录中加入一条完整成员轨迹，覆盖客户端加入、客户端退出、委员会加入、委员会退出、交接前迟到更新、交接确认失败和节点恢复。轨迹需要分别记录更新是否已进入 `frontier`，以及客户端是否需要重新训练。
2. 为 Buffalo 原生方案和本文的活动状态交接方案建立同一接口的能力对照，明确哪些步骤是 Buffalo 已有能力，哪些步骤需要新增份额刷新和交接层。
3. 在抽象后端中加入旧份额擦除、后继份额安装和开启结果一致性检查，验证委员会退出后不存在两个可写状态，封存后不存在可恢复的活动份额。
4. 用固定模型维度、活动实例数和委员会规模测量交接延迟、交接通信量、开启时间、模型陈旧度和吞吐变化。完成这组结果后，再决定是否值得接入 Buffalo 的真实密码学代码。

本轮暂不扩展新的成员事件类型，也不把客户端动态参与重新包装成论文贡献。真正需要验证的是：委员会变化是否能够以有限的交接代价保留异步联邦学习的训练连续性。

### 2026-09-16（P113：冻结协议方案并完善代码构建计划）

本轮开始从问题审计进入方案构建，但暂不实现新的代码。思路稿新增了方案冻结稿，明确了三类记录和九个协议操作。

#### 方案状态

配置记录包含后继配置、成员集合、阈值、认证上下文、生效边界和配置证书。活动实例记录包含模型版本、唯一写入配置、`generation`、已接受更新、`frontier`、两个受保护聚合值和活动聚合密钥份额。封存记录只包含聚合结果、参与集合和封存证明，不包含任何可写份额或恢复材料。

协议流程固定为：客户端加入或退出、更新接收、固定 `frontier`、活动聚合份额重分享、后继配置安装、唯一写入权确认、旧状态擦除、后继实例继续训练、结果封存。客户端事件不改变委员会密钥；委员会事件刷新配置级阈值上下文和活动实例份额。迟到旧上下文更新重新保护后提交，模型版本不兼容时重新训练。

首选保护实例化仍是 Buffalo 兼容的两层保护：向量更新保护和聚合密钥份额转移。Buffalo 原生 assistant 机制只作为外部基线，不能直接承担本文的活动委员会交接。方案稿也明确了后端不能提供份额转移时的“实例放弃并重新保护”对照路径。

#### 代码构建计划

实验构建稿新增代码蓝图，冻结四层边界：训练 workload、事件轨迹、窗口与配置服务、保护后端。统一记录包括 `ClientUpdate`、`LiveWindow`、`ConfigurationEvent` 和 `AggregateResult`。保护后端只负责更新保护、聚合、活动状态导出与重分享、聚合开启和清除；窗口服务负责 `frontier`、唯一写入权、客户端重提交和封存。

代码按五个阶段推进：

1. 当前回放器完成四类策略和完整成员轨迹的状态验证；
2. FLSim 接入真实训练完成事件；
3. 抽象后端接入窗口服务并验证封存后的状态排除；
4. Buffalo 兼容后端测量保护、开启和份额转移成本；
5. 接入外部基线和连续配置故障场景。

本轮不新增 Python 模块，不引入 RPC、进程编排和密码学依赖。下一步先审计阶段 A 的结果字段和验收条件，确保同一轨迹能够验证更新至多计入一次、`frontier` 单调、代数不回退、交接失败时只有一个可恢复所有者、封存后没有可写保护状态。阶段 A 通过后再抽取窗口服务和训练适配器。

### 2026-09-16（P114：完成阶段 A 回放审计，冻结实现前的数据契约）

本轮没有修改代码，只运行并审计现有回放器。带客户端和委员会成员事件的轨迹包含 90 条事件，四类策略生成 44 个窗口记录。当前入口、CSV 轨迹和基本交接路径可以运行，但结果字段还不能完整证明本文的协议不变量。

#### 当前证据与缺口

1. `accepted_clients` 可以观察客户端集合，但没有独立 `update_id`，因此不能证明同一训练结果只纳入一次。
2. `frontier_record_version` 已经输出，但当前记录版本没有随更新纳入递增，不能证明 frontier 是更新集合的真实边界。
3. `owner_configuration` 和 `handoff_status` 可以观察最终所有者，但没有写入尝试、旧配置拒绝原因和所有者历史，不能证明交接期间不存在两个写入者。
4. `generation` 和保护上下文已经输出，但缺少旧代数确认、重复安装和旧状态恢复的专门轨迹。
5. 抽象后端内部能够把状态标记为 `erased`，但回放结果没有擦除收据，也没有区分活动状态大小、封存记录大小和擦除后的状态大小。
6. `resubmitted_updates` 和 `source_window` 已经输出，但没有记录原始更新标识、是否重新训练以及模型版本兼容结果。

因此，当前回放结果可以支持“事件入口和基本交接流程可运行”，不能支持“所有安全和状态不变量已经被实现”。这一区分已经写入实验构建稿的 Phase A 审计。

#### 冻结的数据契约

下一轮实现前，轨迹事件增加 `update_id`、`source_update_id`、`source_generation`、`target_generation`、`handoff_attempt_id`、`rejection_reason` 和 `retrained`。窗口结果增加 `accepted_update_ids`、`frontier_update_ids`、`owner_history`、`write_attempts`、`handoff_failures`、`recoverable_owner`、`erase_status`、`sealed_state_bytes` 和 `state_change_after_seal`。

`update_id` 表示一次训练结果，重新保护同一训练结果时生成新的目标提交记录，并通过 `source_update_id` 关联。客户端重新下载模型并重新训练时才将 `retrained` 记为真。这个字段区分了密码学重新保护和机器学习重新计算。

阶段 A 的验收条件固定为：更新标识至多进入一个接受集合，`frontier_update_ids` 等于冻结时的接受快照，按接收顺序记录的更新日志以该快照为保持顺序的前缀，写入配置只在有效确认后变化，代数只递增，交接失败时只有一个可恢复所有者，旧代数写入被拒绝，封存窗口没有状态改变，旧状态擦除先于旧所有权消失，重新提交保留来源和模型版本关系。

#### 下一步

下一步只完善回放器的数据契约和确定性轨迹设计，不接入 FLSim、Buffalo 或真实密码学。先补齐三个场景：交接确认失败后旧状态恢复、旧代数重复安装被拒绝、封存后迟到消息和恢复请求同时到达。阶段 A 的逐事件日志通过后，再抽取窗口服务和训练适配器。

### 2026-09-16（P115：修正 frontier 验收语义）

本轮进一步审计阶段 A 的不变量表述，修正了 `frontier` 的数据语义。`frontier_update_ids` 是冻结时已接受更新集合的快照，不直接称为集合的前缀；只有按接收顺序保存的 `accepted_update_log` 才能声明 frontier 是其保持顺序的前缀。该修正已经同步到实验构建稿，避免后续实现用无序集合证明接收顺序。

当前阶段仍停留在方案和代码构建设计，不接入真实训练或密码学。下一步实现前需要冻结逐事件日志、更新标识、交接失败、旧代数恢复和封存后状态变化五类记录。

### 2026-09-16（P116：冻结三条阶段 A 确定性轨迹）

本轮把阶段 A 从字段审计推进到可实现的轨迹规格，仍未修改 Python 代码。实验构建稿新增三条单窗口确定性轨迹：

1. `A1-handoff-failure`：确认失败后由旧配置恢复，同一交接成功重试。目标是证明失败确认不会产生第二个可写副本，旧配置在成功确认前始终是唯一恢复来源。
2. `A2-stale-generation`：后继配置安装后发送旧代数恢复、确认和更新。目标是证明代数严格递增，旧代数不能重新安装、恢复或写入。
3. `A3-sealed-rejection`：封存后交付旧上下文更新、迟到交接消息和恢复请求。目标是证明封存记录吸收后续消息，参与集合和结果保持不变。

每条轨迹都要求逐事件输出 `update_id`、`source_update_id`、`handoff_attempt_id`、所有者、代数、状态阶段、拒绝原因、擦除状态和封存后状态变化。阶段 A 的证据不再是单个最终 CSV，而是事件日志与窗口摘要的对应关系。

下一步仍然是代码实现前的设计核对：明确三条轨迹的 CSV 字段、预期状态表和拒绝原因枚举；核对后再开始阶段 A 的最小字段改造。真实 FLSim、Buffalo 和密码学后端继续等待阶段 A 通过。

### 2026-09-16（P117：厘清失败交接时的配置与窗口所有者）

本轮补充了阶段 A 的一个关键实现约束。全局当前配置和单个活动窗口的所有者不能使用同一个字段表示：新配置可以立即接收新的聚合实例，但确认失败的活动实例仍由旧配置保留唯一恢复来源。只有后继配置确认安装后，该活动实例的 `owner_configuration` 和 `recoverable_owner` 才切换到后继配置。

这意味着阶段 A 需要同时记录：

```text
active_configuration
window.owner_configuration
window.writer_configuration
window.recoverable_owner
handoff_status
```

当前回放器在 `config_install` 后立即切换全局配置，尚未表达这一区分；该行为已经登记为实现缺口。实验构建稿新增了拒绝原因枚举和 A1 的预期状态表，明确“旧配置仅可恢复”不等于“旧配置继续接受新写入”。

下一步继续停留在构建方案阶段，先核对状态字段能否覆盖失败交接、旧代数拒绝和封存拒绝三条轨迹，再进入最小字段改造。

### 2026-09-16（P118：统一适配规格中的状态与记录契约）

本轮将适配规格与实验构建稿统一。后续实现使用四类核心记录：`ClientUpdate`、`LiveWindow`、`ConfigurationEvent` 和 `AggregateResult`，并明确以下字段不能合并：

```text
active_configuration
owner_configuration
recoverable_owner
generation
handoff_status
```

配置安装可以立即改变全局 `active_configuration`，但只有有效的 `handoff_confirm` 才改变活动窗口所有者。旧配置冻结后不能接受新客户端写入，但在确认失败期间仍可恢复已接受的活动状态。这个规则已经写入适配规格的实现数据契约。

适配规格同时固定了 `update_id`、`source_update_id`、`accepted_update_log`、`frontier_update_ids`、`erase_status` 和 `state_change_after_seal` 的含义，并规定逐事件日志是窗口摘要的依据。阶段 A 的三个门槛现在在系统规格、实验构建稿和适配规格中保持一致。

当前仍不实现代码。下一步是对这三份文档做一次字段交叉检查，消除残留的旧字段名和重复语义，然后再开始阶段 A 的最小字段改造。

### 2026-09-16（P119：完成三份实现文档的字段对齐）

本轮交叉检查发现系统规格缺少阶段 A 的扩展字段表，已补齐 `update_id`、来源更新、交接代数、交接尝试、拒绝原因、所有者状态和擦除状态字段。现在实验构建稿、系统规格和适配规格共同使用：

```text
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

三份文档都明确：事件日志是窗口摘要的依据；全局当前配置可以先切换，活动窗口所有者必须等待有效交接确认；失败交接保留旧配置恢复能力；封存后的状态改变必须产生拒绝记录。

当前代码构建方案已经完成字段层面的闭合。下一步仍保持不实现代码，转入阶段 A 的接口调用顺序审查，重点确认窗口服务和保护后端之间的边界不会让后端绕过 `frontier` 或封存规则。

### 2026-09-16（P120：冻结窗口服务与保护后端的调用边界）

本轮完成阶段 A 之后的接口调用顺序设计，仍未实现代码。核心边界固定为：窗口服务决定客户端资格、frontier、窗口所有者、代数切换和封存；保护后端只执行受保护更新验证、聚合、活动状态导出与重分享、聚合开启和擦除。

#### 三条调用链

客户端更新路径为：客户端生成受保护载荷，窗口服务预检配置、资格、模型版本、代数和 `update_id`，后端执行原子累加，服务提交接受日志。预检失败不调用后端，累加失败不提交接受日志，避免出现密文已经累加但服务记录没有纳入的状态。

活动交接路径为：服务冻结窗口并记录 frontier，后端导出、重分享和暂存安装，服务验证安装结果并确认，后端收到确认后的擦除令牌才清除源状态。安装失败或确认失败保留源状态和旧恢复所有者，成功确认只切换一次 owner。

封存路径为：服务检查完成条件，后端开启聚合，服务验证并发布封存记录，后端封存并擦除活动状态。开启或封存发布失败时窗口保持可恢复状态，不产生封存结果。安装完成但旧状态暂未清除时显式记录 `erase_pending`，不把它写成已经完成隐私终结。

#### 幂等与失败语义

后续实现为提交、交接、安装、擦除和封存分别使用 `admission_token`、`handoff_token`、`install_token`、`erase_token` 和 `seal_token`。重复请求返回第一次结果，不得再次累加、再次安装、再次切换 owner 或生成第二份封存记录。

实验构建稿新增了阶段 C 测试矩阵和停止条件。阶段 C 先使用抽象后端验证调用边界，只有事件日志能够重建 owner history、失败交接保留源状态、封存后没有状态改变时，才进入真实保护后端和 FLSim。

下一步仍不实现代码，先对调用链中的 `freeze -> export -> reshare -> staged install -> confirm -> erase` 和 `open -> publish -> seal -> erase` 做一次论文方案与系统规格交叉核对，确认协议叙事、接口名称和失败状态完全一致。

### 2026-09-16（P121：补齐封存待清除状态）

本轮补充了封存过程中的 `seal_pending` 状态。聚合结果发布后，窗口已经不能接受更新、恢复或交接；后端可能仍在等待活动保护材料的擦除回执。只有 `erase_receipt` 写入事件日志后，窗口才进入 `sealed`。擦除失败记录为 `erase_pending`，不允许回退为活动实例，也不允许后继配置恢复该窗口。

系统规格、适配规格、思路稿和实验构建稿现在共同区分：

```text
handoff_pending: 活动状态已冻结，等待后继所有者确认
seal_pending:    结果已固定，等待活动保护材料清除
sealed:          结果固定且擦除回执已记录
```

这个状态补充避免把“模型结果已经发布”和“旧开启状态已经清除”混成一个事件。下一步做最后一次方案交叉核对，重点检查 `handoff_pending`、`seal_pending`、`erase_pending` 在协议章节、系统规格和实验指标中的名称一致性。

### 2026-09-16（P122：统一状态枚举和转移）

本轮交叉核对发现旧状态枚举没有表达 `handoff_pending` 和 `seal_pending`。已同步修正系统规格、适配规格、思路稿和实验构建稿：活动记录的状态现在包含 `owned`、`handoff_pending`、`installed`、`confirmed`、`seal_pending` 和 `sealed`；`seal_pending` 只有在擦除回执记录后才能进入 `sealed`。

方案伪代码也已补上封存结果发布、进入 `seal_pending`、执行擦除和验证 `erase_receipt` 的顺序。这样阶段 C 可以直接检查状态转换，而不需要从 `final_status` 反推保护材料是否已经清除。

当前代码构建方案在接口、字段、调用顺序和状态枚举四个层面已经闭合。下一步仍不实现代码，做一次最终的阶段 A 至 C 构建清单核对，确认每个阶段都有输入、输出、验收条件和停止条件。

### 2026-09-16（P123：完成阶段 A 至 C 的最终构建清单）

本轮完成代码构建方案的阶段化收束，仍未实现代码。实验构建稿新增最终清单，固定三个阶段：

#### 阶段 A：轨迹和服务语义

输入是 `A1-handoff-failure`、`A2-stale-generation`、`A3-sealed-rejection` 三条轨迹和四类窗口策略。输出是逐事件日志、窗口摘要和阶段清单。验收重点是更新日志可重放、frontier 快照正确、所有者不重叠、失败交接保留恢复所有者、`seal_pending` 和 `sealed` 拒绝状态改变事件。

#### 阶段 B：真实异步训练接入

输入是 FLSim 的客户端训练事件和阶段 A 的记录契约。适配器只负责把训练结果转换为 `ClientUpdate`，窗口服务仍然决定纳入、重路由、交接和封存。只有 `finalized AggregateResult` 可以推进全局模型。阶段 B 不引入真实密码学。

#### 阶段 C：抽象保护状态后端

输入是阶段 A 的服务调用和阶段 B 或合成向量。重点验证 `preflight -> verify -> accumulate -> commit`、`freeze -> export -> reshare -> staged install -> confirm -> erase` 和 `open -> publish -> seal_pending -> erase -> sealed` 三条调用链。验收包括幂等令牌、暂存安装、擦除待定状态和封存后的可写状态排除。

每个阶段都固定输入、输出、验收证据和停止条件，并生成 `phase_gate.json` 决定是否允许进入下一阶段。阶段 C 通过后才接入 Buffalo 兼容保护实现；阶段 D 不得改变 A 至 C 的窗口和事件语义。

当前代码构建方案已形成唯一执行顺序：A 验证服务状态，B 验证真实训练桥接，C 验证保护状态边界，D 测量真实密码学成本。下一步可以开始阶段 A 的最小字段改造；在此之前不接入 FLSim、Buffalo 或 RPC。

### 2026-09-16（P124：拆分阶段 A 的最小工作包）

本轮继续完善实现前的构建方案，没有修改代码。阶段 A 现在拆分为五个按依赖顺序执行的工作包：

1. `A0 schema freeze`：冻结 `TraceEvent`、`ClientUpdate`、`EventResult`、`LiveWindow` 和 `AggregateResult`，同时冻结 CSV 列顺序和枚举值。
2. `A1 trace validation`：检查事件序号、幂等 token、代数关系、来源更新关系和封存后事件字段。
3. `A2 window service state`：只实现窗口所有者、恢复所有者、frontier、代数和封存状态，不接触真实后端。
4. `A3 policy isolation`：让 `Static`、`Full-transfer`、`Periodic-rekey` 和 `Selective-finality` 只改变交接策略，共用服务状态与日志。
5. `A4 summary and gate`：从逐事件日志派生窗口摘要、配置摘要和 `phase_gate.json`。

每个工作包都有明确的输入、输出、停止条件和下一个依赖。阶段 A 向阶段 B 只交付 schema、轨迹 manifest、列定义、通过的 `phase_gate.json` 和服务契约，不交付模拟器的隐含内存状态。

这一步使代码构建从“开始改回放器”变成可审计的最小顺序：先冻结记录，再验证轨迹，再实现状态，再隔离策略，最后生成门禁证据。下一步进入 A0 的字段和枚举最终核对，仍不接入 FLSim、Buffalo 或 RPC。

### 2026-09-16（P125：按异步联邦学习文献重写成员变更与密钥路径）

本轮重新核对了本地异步联邦学习和安全聚合文献，明确不使用分布式共识论文的成员交接流程作为联邦学习事实依据。重点材料是缓冲异步协议 Buffalo 和按轮处理动态用户的 `Setup Once, Secure Always`。两类工作都把动态性放在客户端参与集合，或把助手节点视为聚合实例的恢复参与者；它们没有完成“聚合委员会在一个已经接收部分更新的异步实例中发生变化”这一流程。

#### 1. 现有异步联邦学习如何处理加入和退出

Buffalo 使用 buffered asynchronous FL。客户端独立完成本地训练并提交更新，服务器按到达顺序填充 buffer；buffer 达到阈值后形成一次聚合并清空。客户端加入的实际含义是：客户端获得当前模型和本次实例所需的保护参数，完成训练后提交一个新鲜保护的更新。客户端没有进入某个 buffer 的预先承诺，服务根据更新是否在 buffer 关闭前到达决定是否纳入。

客户端退出、掉线和延迟在现有工作中通常按本次实例的参与集合处理：

```text
update is received before the instance closes
    -> verify and admit it into this aggregation instance

client leaves or drops before admission
    -> its update is absent from this instance

client has already submitted an accepted update
    -> keep that update in the instance; do not withdraw or count it again

the instance reaches its threshold
    -> aggregate only the admitted set and start a new instance
```

`Setup Once, Secure Always` 采用相近的客户端语义，但它通过每轮新鲜随机掩码和中间服务器收集共同活跃用户集合来处理动态用户。新用户无需参加初始用户间密钥交换即可参与获准的训练实例；退出或掉线用户不出现在本轮共同活跃集合中。该论文的中间服务器和聚合器仍是固定的服务角色，论文还明确把中间服务器掉线留作后续工作。因此，它解决的是每轮用户集合变化，而不是聚合权威变化。

#### 2. 本文采用的完整事件路径

本文把“客户端加入或退出”和“委员会加入或退出”分成两条状态路径。客户端事件只影响后续更新资格；委员会事件影响活动聚合状态的所有权和阈值份额。

**客户端加入。** 服务验证身份和当前配置，返回当前模型版本、目标实例、实例代数和公开保护上下文。客户端本地训练后生成一次新的受保护更新，并提交 `update_id`、实例标识、模型版本和配置代数。服务先验证资格、实例状态、模型版本和幂等标识，再调用保护后端累加。客户端加入不改变委员会密钥，也不要求已有客户端重新建立密钥。

**客户端退出或掉线。** 服务从生效边界开始停止向该客户端分配新的训练任务，并拒绝其后续提交。已经进入活动实例 `frontier` 的更新属于该实例的固定输入，继续完成聚合；尚未被接收的更新不进入旧配置前缀。退出客户端只有重新取得资格才能再次提交。对仍具资格的客户端，迟到旧上下文更新在原实例完成交接后使用后继代数重新保护并提交；原实例已封存或放弃时才进入新实例。模型版本不兼容时重新训练。客户端退出不改变委员会密钥。

**委员会加入。** 当前配置先确认后继成员集合、阈值、配置代数和认证材料。新委员会通过 DKG 或可验证重分享获得后继配置份额。对每个未封存实例，旧委员会固定 `frontier` 并停止该实例的新写入；保护后端导出活动聚合状态及其配置证明，后继委员会验证实例标识、模型版本、`frontier`、代数和配置记录后暂存安装。后继委员会确认安装后，活动实例的恢复所有者才切换，旧委员会随后擦除旧份额和旧写入状态。新实例直接使用后继配置。

**委员会退出、崩溃和恢复。** 计划退出使用同一交接路径，但在后继配置确认前，退出节点仍属于旧实例的恢复集合；确认后才失去写入和恢复资格。崩溃不是自动批准配置变化：旧配置只有在剩余节点满足恢复门槛时才能继续导出或完成交接，否则活动实例保留旧配置的唯一恢复来源。恢复节点按当前后继配置重新获得份额，不能自动恢复旧配置的写入权。后继配置不能在没有确认的情况下创建第二个可写或可恢复副本。

**封存。** 已封存实例只向后继配置传播模型结果、参与集合和封存证明。它不再传播旧份额、恢复材料、逐客户端开启材料或可写聚合状态。结果发布后先进入 `seal_pending`，活动保护材料完成擦除并记录回执后才进入 `sealed`。

#### 3. 密钥到底改变什么

密钥语义必须按对象区分，而不是写成“成员变化后重新密钥”：

| 对象 | 客户端加入或退出 | 委员会加入或退出 |
|---|---|---|
| 身份认证密钥 | 保持有效，资格由配置记录控制 | 新节点注册，退出节点在后继配置中撤销 |
| 新实例保护参数 | 使用当前实例参数 | 后继实例使用后继配置参数 |
| 活动实例聚合状态 | 不变 | 对阈值份额和配置上下文执行刷新或重分享 |
| 已封存实例状态 | 不变 | 不交接可恢复材料，只复制封存记录 |

本轮初步考虑过同一活动实例公钥下的阈值开启份额转移。后续 P127 经 Buffalo 密钥域核对后调整为：转移旧前缀的聚合 JL 密钥份额，后继客户端向新委员分发各自的新份额。保护单客户端仍依赖最低参与数、单次聚合开启及旧份额清除。

Buffalo 的现有主协议不能直接完成这一步。它的客户端与 assistant 之间存在 pairwise key；论文明确指出 assistant 集合改变时需要重新建立相关 pairwise key，或者改用支持 transfer share 的加法同态阈值加密。后者会增加 LWE/JL 聚合密钥的阈值解密成本，而且 Buffalo 没有给出旧 assistant、在途 buffer 和新 assistant 之间的完整交接流程。因此，本文不能把 Buffalo 的动态 assistant 讨论写成已经解决委员会交接。

若保护后端不支持同一公钥下的活动状态重分享，该活动实例可由旧委员会达到参与门槛并封存；未能完成时明确放弃该实例，由仍具资格的客户端根据模型版本重新保护或重新训练后进入新实例。其他新实例可以并行使用后继配置。服务不能仅凭新配置记录把不可迁移的旧密文改写为新配置可开启的状态，也不能假设服务能够解开单客户端更新后重新加密。

#### 4. 本轮研究判断与下一步

当前最准确的研究问题是：

> 异步联邦学习已经能够处理客户端在不同聚合实例中的加入、退出和掉线，但当聚合委员会在活动实例尚未完成时发生变化，现有方案没有给出保护状态、写入权和恢复权的连续迁移。本文研究如何以一次可验证的活动状态交接保留异步训练推进，并在交接后排除旧配置和已封存实例的恢复路径。

下一步先做 `A0 schema freeze`，不接入 FLSim 或真实密码学：

1. 固定客户端事件、委员会事件、配置代数、实例代数和 `frontier` 的字段与枚举。
2. 为一条轨迹同时覆盖客户端加入、客户端退出、委员会加入、委员会退出、交接前迟到更新、确认失败、节点恢复和封存后消息。
3. 在事件结果中区分 `client_ineligible`、`old_configuration`、`old_generation`、`frontier_closed`、`unavailable_owner` 和 `sealed_window`。
4. 在阶段 C 的抽象后端中先验证“同一公钥下份额刷新保持活动聚合不变”；若该接口无法表达，再把“等待旧配置封存”作为 Buffalo 兼容后端的明确对照路径。

完成 A0 和 A1 后，才开始实现窗口服务状态；真实 Buffalo 接入放在服务语义通过之后。

### 2026-09-16（P126：修正未完成缓冲区的连续性，落实构建判据）

重新检查 P125 的交接语义发现一处实质性缺口：若旧配置冻结时已有 `a < B` 个更新，并把此后的所有更新都导向新实例，旧实例无法达到最低参与数 `B`，论文宣称的“活动聚合继续完成”便不能成立。本轮已同步修订思路稿、系统规格、适配规格和实验构建稿：在 `frontier` 固定旧前缀后，新配置暂存并确认活动实例、旧份额清除完成，同一 `sid` 在新代数下继续接收合格客户端的后缀。确认失败期间旧配置是唯一恢复来源但窗口保持冻结；确认成功但旧份额尚未清除时，后继配置已取得所有权，原实例仍暂停接收和开启，其他实例可以继续运行。已经退出的客户端无法借重提交绕开资格检查。

本轮最初把保护层设为同态阈值加密的候选组件。后续 P127 核对 Buffalo 的 JL 密钥域后，候选实例化调整为跨委员会重分享**已接收前缀的聚合 JL 密钥份额**；原有向量 LWE、JL 保护及新客户端份额交付方式保持。抽象回放和清除回执只能验证服务行为；它们不能证明真实份额可转移、物理擦除或密码学安全。滚动腐蚀下的隐私性质依赖暴露门槛与诚实持有者的安全擦除；擦除回执不构成对恶意持有者私存旧份额的证明。

实验构建稿新增第 24 节，列出 A0 的五类记录及输入 CSV 顺序、事件/状态枚举、缺省规则，并增加 `T7`：旧前缀 2 个更新、最低人数 3，确认与清除后 `C1` 在同一 `sid` 纳入第 3 个更新；去掉清除回执则应持续暂停。旧三条轨迹已补暂存安装、交接及封存清除时序。A0 是**文档契约**，当前生成器/回放器仍没有这些字段和行为，不应声称已经通过阶段 A。

下一步在暂不实现代码的前提下，核对本地 Buffalo 转写与候选标量重分享组件：列出 JL 密钥域、聚合份额求和范围、可验证重分享 API 和动态成员恶意安全条件。完成该能力审计后，再根据第 24 节字段契约实施阶段 A 的轨迹与窗口服务。

### 2026-09-16（P127：Buffalo 密钥域审计与候选后端改选）

已查 Buffalo 第 4 节与第 5 节：JL 的公开模数 `N` 由两个大素数相乘，客户端 JL 密钥选自 `Z_{N^2}`，实际参数写为 `log2(N)=2048`；每次异步更新使用新 JL 密钥，并将其份额发给固定 assistant。在线第 3 轮中助手各自先求所接收的客户端份额之和，服务器从阈值份额恢复**该次 buffer 的聚合 JL 密钥**，再开启聚合 LWE 密钥及向量。Buffalo 的动态 assistant 扩展明确指出：改用椭圆曲线同态阈值加密时，对 JL/LWE 大域密钥求离散对数会增加显著成本。这些事实不支持 P126 原先的“每实例椭圆曲线阈值加密 JL 密钥”首选方案。

新的候选是**先聚合，后重分享**：旧委员会先对 `frontier` 已纳入集合完成密文、份额和参与集合的一致性核对，把活动实例的 JL **聚合标量份额**可验证地转移给后继委员；旧委员会擦除该实例的逐客户端份额和旧聚合份额后，后继委员在同一 `sid` 接受新客户端的 JL 份额并继续求和。高维模型的 LWE 保护与 JL 保护保持 Buffalo 式处理，后继客户端仍需同新委员建立安全的份额交付渠道。因此论文贡献是未完成缓冲区的跨配置聚合连续性及已封存状态的排除，而不是发明新同态加密。

此候选仍有关键未完成条件：JL 密钥域与重分享份额域的编码关系、每个旧纳入更新的份额可用性、旧节点恶意时的可验证跨组重分享、重分享过程中不得构造部分或差集聚合开启、诚实旧份额清除与受限移动敌手门槛。思路稿 13.3.2 和实验构建稿 24.3 已按此修改；阶段 D 才可用具体密码学实例和成本给出肯定结论。下一步先阅读本地可验证重分享/VSS 工作，选择与 Buffalo 密钥域兼容的**一个**具体组件并列出参数及信任假设；此核对结果决定是否进入真实保护后端实现。A0/T7 的服务轨迹不依赖该组件，可以按第 24 节继续设计。

### 2026-09-17（P128：完成组件裁决，改用系数域阈值保护）

本轮审计了 Buffalo 开源仓库提交 `3a8dfbfddc0bda145f20eebb0f50faaee3b2fbd5` 的实际调用链。`OursSS.py` 使用 `SSS(2048)` 直接分享 JL 客户端密钥；`get_field(2048)` 选择素数 `2^2203-1`。客户端根据缓冲规模缩短随机密钥，使至多 `B_max` 个密钥之和仍落在该素数域中。`olympia/util/shamir_sharing.py` 中的 `GF(2^31-1)` 属于数组分享和 packed sharing 工具，没有进入 JL 密钥分享路径。P127 中把它视为 Buffalo JL 路径候选域的判断已被本轮调用链审计修正。

Optimistic DPSS 的秘密位于承诺群的素数阶域，安全定义允许交接转录泄露 `g^s`，并把均匀随机秘密作为默认条件。它的现有实现和复杂度结论面向常规曲线标量域。把 Buffalo 约 2048 位的 JL 聚合密钥直接放入该协议，需要同时更换多项式承诺、向量承诺、阈值签名和证明所用的群；这不属于可直接复用的组件，也会把论文主线推向新的密码协议。因此，“先聚合 JL 标量，再直接接 Optimistic DPSS”不再作为首选实例化。

新的首选后端保留 Buffalo 的 RLWE 模型保护，把阈值加密放到 RLWE 密钥进入 NTT 之前的系数域。Buffalo 的 RLWE 实现用方差参数 `8` 的中心二项分布采样密钥系数，采样范围满足 `|a_u,j| <= 16`；当前 `convert_key` 导出的是模数约为 59 位的 NTT 系数。本文增加系数域导出和导入，使客户端对小系数执行阈值 ElGamal 加密：

```text
a_u,j in [-rho, rho]
s_u = NTT(a_u)
c_u = LWE.Protect(s_u, x_u)
e_u,j = TEG.Enc(PK_sid, a_u,j * G)
```

每个活动实例使用独立且均匀随机的曲线标量 `z_sid`，公钥为 `PK_sid=z_sid*G`。客户端只依赖公开窗口密钥。委员会持有 `z_sid` 的阈值份额，配置变化时用 Optimistic DPSS 重分享仍然活动的窗口密钥；模型密文和系数密文保持不变。窗口封存后清除 `z_sid` 的所有活动份额，后继配置只接收封存记录。

对参与集合上限 `B_max`，聚合系数满足 `|A_j| <= B_max*rho`。阈值解密得到 `A_j*G`，系统通过有界点表恢复整数。以 Buffalo 的 `rho=16` 和 `B_max=512` 为例，每个系数对应 `16385` 个候选点。这个范围允许直接查表，避开 Buffalo 动态 assistant 扩展中对大域 JL 或 NTT 系数求离散对数的瓶颈。恢复系数向量后再执行 NTT，得到聚合 RLWE 密钥并开启模型聚合。

该组合使用现有组件的边界如下：Buffalo 提供 RLWE 更新保护；阈值 ElGamal 实例和窗口密钥接口仍需实现，Optimistic DPSS 提供均匀曲线标量在动态委员会间的异步可验证重分享候选。需要新增的实现包括 RLWE 系数域导出和导入、与 DPSS 使用同一标量域的 ElGamal 实例、窗口密钥批量生成、系数点表和窗口服务适配。Buffalo 原生 JL 路径保留为固定委员会性能基线。

剩余研究问题集中在四项系统条件：

1. 系数域导入和原生 NTT 密钥求和必须逐项等价；
2. 初始委员会需要批量生成窗口级随机阈值密钥，并把 setup 成本与训练稳态成本分开；
3. 客户端每次更新需要提交 `m` 个曲线密文，必须测量计算、带宽和并行化收益；
4. 当前首版安全主张要求客户端遵循密钥采样和加密算法，恶意客户端的系数范围证明与模型投毒归入鲁棒聚合扩展。

思路稿 7.6、13.3.2 和 13.7，系统规格 4.5，适配规格 2.1 至 2.2，以及实验构建稿 17.5 和 24.3 已同步。阶段 D 新增组件验证矩阵，依次检查 RLWE 系数转换、阈值密文加法、有界点表解码、动态份额交接和窗口封存。

下一步先写阶段 D0 的微基准参数表和接口补丁清单：固定曲线与序列化格式、RLWE 维度、`rho`、`B_max`、委员会规模、门槛和成员重叠率；随后只实现系数导出和导入的等价性检查。该检查通过后再实现阈值 ElGamal 和 DPSS 适配，避免同时修改 RLWE、曲线密码和窗口服务。

### 2026-09-17（P130：研究过程复核与证明边界收紧）

本轮以 `AGENT.md` 为最高优先级复核了研究过程。主线演化是合理的：问题从“重复计数和重放”逐步收敛到委员会变化下的异步训练连续性，再进一步确定为活动窗口的状态交接与已封存窗口的隐私终结。这个问题仍然属于联邦学习系统研究，因为主要评价对象是模型推进、窗口完成、客户端纳入、交接延迟和训练质量；密码学组件承担保护状态迁移和结果释放的支撑作用。

当前叙事中有三项内容已经闭合：

1. `frontier` 由旧配置的成员管理协议确认，不能由单个节点声明；
2. 活动窗口继续接收后继配置下的更新时，旧前缀与新后缀使用同一窗口公钥，并以集合并集形成唯一参与集合；
3. 新配置只接收活动状态，已封存窗口只传播封存记录，迟到的旧代数消息只能产生拒绝结果。

本轮还发现并修正了两个容易造成错误承诺的地方。第一，G1 中的密文假设统一写为 G1 中的 DDH 假设，不再把它写成 XDH。第二，Buffalo 的系数导出和导入接口尚未实现，RLWE 候选后端仍处于设计和接口审计阶段；删除了依赖这些未实现接口的检查脚本，因此当前材料不声称已经完成 Buffalo 原生扩展或真实密码学验证。

对现有工作和候选组件的判断保持分层：Buffalo 提供固定委员会缓冲异步安全聚合基线；Optimistic DPSS 提供动态委员会重分享的候选能力；本文新增的是把这些能力约束到 FL 活动窗口和封存结果的组合语义。受 epoch 约束的移动敌手是本文的应用安全模型，用于描述长期滚动腐蚀和跨配置状态累积，不把它包装成新的通用移动敌手理论。证明只需围绕窗口结果稳定性、交接后旧代数失效和隐私终结给出必要条件，系统论文主体仍是服务执行和实验评价。

下一步顺序重新固定为：

1. 完成 A0 schema freeze，冻结配置事件、窗口事件、`frontier`、代数、所有者、确认和擦除回执字段；
2. 用现有回放器验证加入、退出、崩溃恢复、确认失败、后继接收和封存后迟到消息；
3. 以 Buffalo 原生运行作为固定委员会基线，记录其实际接口，不提前假定它支持动态委员会交接；
4. A0 语义稳定后，再单独审计 Buffalo 的系数域转换接口，确认逐项等价性后才实现阈值 ElGamal 和 DPSS 适配。

这一路线遵循 `AGENT.md` 的要求：先修正根本语义和证据边界，不加入哈希、SHA 或无效的 smoke test，也不把尚未运行的密码学后端写成实验结果。

### 2026-09-17（P131：形成六个核心算法并收紧整体开启接口）

本轮开始正式构建协议方案。方案的最小核心由六个算法组成：`CreateInstance`、`AdmitUpdate`、`FreezePrefix`、`HandoffActiveState`、`FinalizeAggregate` 和 `EraseAndSeal`。它们分别覆盖聚合实例建立、客户端更新纳入、旧配置输入前缀确认、活动状态跨委员会交接、整体聚合结果发布和历史状态终结。

方案的关键变化是把“只开启聚合结果”从文字约定改为后端接口条件。`FinalizeAggregate` 先生成绑定 `sid`、实例代数、最终参与集合和受保护聚合状态摘要的 `aggregate-open certificate`，委员会只针对该证书生成部分开启结果，后端再合并得到一个聚合结果。接口不提供可对任意单项密文调用的普通开启操作。这样可以明确区分阈值解密原语本身与联邦学习服务要求的 aggregate-only opening。

活动实例交接保持同一 `PK_sid` 和已接受密文不变，只刷新窗口秘密的委员会份额。`HandoffActiveState` 只有在后继配置验证交接记录并确认唯一所有者后，才允许清除旧配置的可写份额；清除回执之前，实例保持暂停，其他聚合实例继续运行。交接失败时旧配置仍是唯一恢复来源，后继配置不能安装第二个可写副本。

移动腐蚀模型的使用边界也固定下来：每个 epoch 的腐蚀上限限制单个配置周期内可读取的份额集合，活动实例在配置交接时执行主动式份额刷新，旧份额在确认后清除；已发布结果不再进入重分享输入。本文需要证明的是在这些条件下跨 epoch 的历史视图不能重新形成已封存实例的开启集合，而不是提出新的通用移动敌手理论。

同步更新了思路稿、适配规格和实验构建稿。实验接口现在使用 `authorize_open`、`partial_open` 和 `combine_open`，不再把无条件的 `open_aggregate(state)` 作为后端契约。抽象回放器仍然只验证状态顺序和记录语义，不能证明真实整体开启或份额安全；真实后端实现前必须完成两项核验：

1. 证明部分开启请求只能由最终状态证书授权，并且证书摘要对应唯一的聚合密文集合；
2. 在两配置和多 epoch 轨迹中验证活动实例的同公钥连续性、旧份额刷新、交接失败恢复和封存后拒绝路径。

下一步不是继续增加密码学原语，而是为六个算法写出状态前置条件、输出事件和失败结果表，并将现有回放器的 A0 字段与这些算法逐项对应。完成对应关系后，再实现一个不读取明文的抽象 `aggregate-open certificate` 流程，最后才进入系数域 Buffalo 后端。

### 2026-09-17（P129：冻结阶段 D0 参数与最小接口）

本轮完成了组件裁决后的全文一致性检查，修正思路稿中残留的 JL 份额渠道、`protected_key_sum` 旧字段和一个损坏的公式控制字符。活动实例现在统一保存 `protected_update_sum`、`encrypted_lwe_coefficient_sum`、窗口阈值密钥份额和 `PK_sid`。

阶段 D0 固定 Buffalo 的 `m=2048`、`q_LWE=332366567264636929`、中心二项分布参数 `8`、`rho=16` 和 `B_max=512`。源码中的采样器对 16 对随机比特求差，因此系数严格落在 `[-16,16]`。候选阈值 ElGamal 使用 BLS12-381 G1，通信按 48 字节压缩点计量，并依赖 G1 中的 DDH 假设；该选择与 Optimistic DPSS 的公开实现共享标量域。委员会规模取 `8、16、32`，Byzantine 上限为 `f=floor((n-1)/3)`，共享次数为 `f`，阈值解密需要 `f+1` 份，配置确认需要 `n-f` 票。相邻委员会重叠率取 `0%、50%、100%`。实验同时扫描 `1、4、8` 个活动窗口，以观察窗口密钥批量生成与交接摊销。

实现接口分为三组。Buffalo 绑定只增加 `export_coefficients` 和 `import_coefficients`；阈值保护后端提供窗口密钥生成、批量系数加密、密文累加、部分解密与有界解码；交接层只提供 `reshare_window_key`。窗口服务继续使用通用聚合后端契约，不读取曲线或 NTT 内部状态。

首个可运行检查保持最小范围：对 `1、16、64、512` 个 Buffalo 密钥验证 `NTT(sum a_u)` 与原生 NTT 密钥求和逐项相等，并检查所有导出系数满足 `|a_u,j| <= 16`。这项检查通过后，下一步实现单窗口阈值 ElGamal 微基准，测量 `m=2048` 个系数的加密、累加、部分解密、点表恢复和实际通信量；随后才连接 Optimistic DPSS handoff。

### 2026-09-17（P132：六算法前置条件与方案核验入口）

P131 已将方案从流程描述推进为六个核心算法，P132 进一步补齐每个算法的前置条件、成功输出和失败结果。当前协议方案以 `CreateInstance`、`AdmitUpdate`、`FreezePrefix`、`HandoffActiveState`、`FinalizeAggregate` 和 `EraseAndSeal` 作为唯一核验入口。

本轮明确 `CreateInstance` 使用分布式阈值建立，只输出窗口公钥和委员会份额，不让任何单一参与方获得窗口秘密。`HandoffActiveState` 通过主动式重分享保持同一 `PK_sid`，但改变份额持有者和实例代数；交接失败时旧状态仍是唯一恢复来源。`FinalizeAggregate` 需要最终状态证书，证书绑定实例标识、代数、最终参与集合和聚合状态摘要；后端只为该证书生成部分开启结果，禁止把普通单项开启作为协议接口。

当前方案的关键安全边界可以压缩为三条：

1. 只有经旧配置确认的输入前缀能够进入交接，后继配置沿同一实例继续接收合格后缀；
2. 只有经最终状态证书授权的完整聚合状态能够产生开启结果；
3. 结果发布后，活动份额、恢复材料和可写状态退出所有后继配置的输入。

这三条边界分别对应训练连续性、整体开启和隐私终结。它们比继续增加密钥刷新或证明术语更适合作为方案章节的主线。下一步将现有回放器事件逐项映射到六个算法，重点检查确认失败、节点恢复、交接期间迟到更新和封存后的开启请求；回放器只能核验调用顺序和结果语义，不能替代真实后端的阈值安全验证。

P129 中关于无条件 `open_aggregate` 和“首个可运行系数检查”的内容属于此前阶段记录，当前有效接口以 P131 和 P132 为准。系数域 Buffalo 扩展、阈值 ElGamal 和 DPSS handoff 尚未实现，暂不写入实验结果。

### 2026-09-17（P134：确定方案相对标准重分享的核心判据）

本轮进一步核验方案是否只是“异步安全聚合加标准阈值重分享”。结论是：若只执行普通重分享，后继委员会能够继续恢复同一秘密，但协议没有理由知道某个聚合实例已经发布结果，也没有规则阻止该实例重新进入恢复路径。本文的新增约束必须落在聚合实例状态，而不是落在“重分享”这个原语名称上。

思路稿现在用三条不变量表达这一差异：

1. 活动实例的受保护聚合状态和 `PK_sid` 在交接前后保持不变，后继配置只能在已确认前缀之后追加合格更新；
2. 结果发布后实例不能返回活动状态、重新接受更新或再次生成开启授权；
3. 活动保护状态可以迁移，封存状态只能传播结果事实，不能形成通向旧份额、恢复材料或部分开启的有效路径。

这三条不变量把系统价值和安全价值连接起来：前两条保证已经完成的客户端计算能够继续形成稳定模型结果，第三条保证委员会变化不会延长已发布聚合的单客户端开启能力。它也给出直接组合基线的明确比较点，避免把标准 DPSS 的秘密连续性误写成本文的贡献。

当前协议方案已具备系统实现所需的抽象边界，但真实密码学结论仍未成立。整体开启证书必须由后端强制绑定唯一的最终聚合状态；主动式重分享必须在旧份额清除和每个 epoch 暴露上限下完成；Buffalo 系数域转换仍需真实接口验证。下一步执行 A0 字段与回放器状态的逐项对照，暂不实现新的密码学原语。

### 2026-09-17（P133：六算法与 A0 回放契约对齐）

本轮将六个核心算法与实验事件逐项对应。`CreateInstance` 由显式实例创建或首个客户端更新触发；`AdmitUpdate` 对应客户端更新和重新提交；`FreezePrefix` 对应配置变化时的已接受输入快照；`HandoffActiveState` 跨越状态恢复、安装确认和旧份额清除；`FinalizeAggregate` 对应最终参与集合确认和结果发布；`EraseAndSeal` 对应封存记录与清除回执。

这项对齐揭示了当前回放器的真实边界：它可以记录更新纳入、配置变化、恢复、确认和结果确定，但尚未模拟最终状态证书、整体开启授权和真实擦除。因此，当前回放结果只能支撑训练连续性、唯一归属、状态阶段和结果稳定性，不能支撑阈值安全或 aggregate-only opening 的密码学结论。

A0 的下一项实现任务已经收紧为三条：

1. 显式记录 `FreezePrefix` 的 `frontier_update_ids`、记录版本和聚合摘要；
2. 让 `handoff_confirm` 只有在安装成功后生效，并让 `erase_receipt` 决定后继实例何时恢复纳入；
3. 让 `window_finalize` 先经过最终集合确认，并把结果发布与 `seal_pending`、`sealed` 区分开。

完成这三条后，才接入不含明文的抽象整体开启证书；系数域 Buffalo 后端继续排在其后。这样方案、回放器和实验评价使用同一组状态边界，避免把抽象事件结果误写成密码学或完整 FL 实现结果。

### 2026-09-17（P135：冻结 A0 记录 schema）

本轮将 A0 字段契约固化为 `experiments/phase-a-schema.json`。schema 现在统一规定 `TraceEvent` 的 17 列顺序、事件枚举、代数和交接标识，以及 `EventResult`、`LiveWindow` 和 `AggregateResult` 的状态枚举与必需字段。`erase_receipt` 已成为正式事件，`erase_status`、`handoff_status` 和 `rejection_reason` 的取值不再由实现自行扩展。

schema 冻结只完成记录层，不代表回放器已经支持这些字段。当前 `experiments/reconfigurable_fl_sim.py` 仍读取旧的 11 列输入，也没有完整记录 `frontier_update_ids`、最终状态证书或擦除回执。下一步修改回放器时必须让旧轨迹显式标记为旧版本或拒绝加载，不能把缺失字段填成默认值后报告 A0 通过。

这一步为协议方案提供了唯一的实现入口：六个算法的输入和输出可以映射到固定事件，失败结果可以映射到固定状态。下一步只改回放器的记录读取和状态保存，不接入 FLSim、Buffalo 或真实密码学后端。

### 2026-09-18（P136：完成 A0 回放语义）

本轮完成阶段 A0 的最小实现。`experiments/reconfigurable_fl_sim.py` 现在严格读取冻结的 17 列 A0 轨迹；旧的 11 列轨迹直接拒绝，不通过默认值补齐。回放器逐事件输出 `event_result`、固定拒绝原因、更新标识、源更新标识、所有者、可恢复所有者、实例代数、交接状态、清除状态、已接受更新序列和 `frontier_update_ids`，窗口摘要同时保留最终状态和交接开销。

状态顺序已经落地：配置安装冻结活动前缀；安装确认只能发生在后继状态已经安装之后；确认后所有权转移到后继配置，但旧状态清除回执到达前，新更新返回 `pending`；清除回执后同一实例可以继续纳入更新；最终化先进入 `seal_pending`，实例清除回执到达后才进入 `sealed`。已封存实例的迟到消息、恢复请求和重复操作保持拒绝。

新的确定性轨迹覆盖两次配置交接、交接前迟到更新、安装确认、清除回执、同一实例跨配置续收、重新提交到新实例和最终封存。全协议回放检查通过：选择性终结策略产生 18 个已封存窗口；同一 `update_id` 在清除前后只被纳入一次；第二次配置交接使用实例局部代数 `0 -> 1`，不再把全局配置编号误作实例代数。

这项结果只证明 A0 的服务状态语义和事件可追溯性。它不证明真实阈值加密、整体开启证书、主动式重分享或 FL 模型收敛。下一步分两条线：先加入确认失败和删除清除回执的对照轨迹，验证旧配置恢复与后继暂停；再在不读取明文的抽象后端中加入绑定最终聚合状态的 `authorize_open -> partial_open -> combine_open` 流程。真实 Buffalo、阈值加密和动态重分享继续排在 A0 对照通过之后。

### 2026-09-18（P137：交接可用性与方案安全模型一致性审查）

本轮审查了“连续性依赖旧配置存在足够诚实服务节点完成交接和清除”这一条件。结论是：如果把它写成每个活动实例在任意成员离开轨迹下都必须继续，假设确实过强；如果把它写成实例级的条件性活性，它与异步动态 FL 和动态主动式秘密共享的通常写法一致。Buffalo 和 Setup Once, Secure Always 主要处理动态客户端、掉线和 assistant 状态，聚合服务本身相对稳定，因此没有给出委员会状态跨配置迁移的实例级活性结论。动态 PSS、DyCAPS 和 Optimistic DPSS 通常要求可验证刷新或重分享达到恢复门槛，并允许在节点不足时延迟刷新或等待可用服务集合；它们不要求所有旧节点在线。

思路稿现在采用实例级交接可用性条件：源配置中足够的诚实服务节点生成已确认前缀，后继配置安装经过验证的新份额，并形成旧状态退役记录。这里的“足够”由源配置恢复门槛和后继配置安装门槛决定。条件成立时，后继配置保留已接受前缀并追加后缀；条件暂时不成立时，实例保持冻结；源配置最终离开前仍无法完成时，实例进入 `abandoned`，合格客户端改用新实例提交。新实例和其他活动实例继续推进，系统整体活性不依赖每个历史实例都完成迁移。

本轮将结果确定与隐私封存拆成两个事件：`Commit_sid` 固定参与集合、聚合值和模型结果，`Seal_sid` 表示旧可写状态已经退役。`Commit_sid` 之后的迟到消息、恢复请求和交接材料不能改变结果；`Seal_sid` 之后后继配置只读取封存记录。这样交接可用性只承担活动实例的计算连续性，退役条件承担移动敌手下的隐私终结，避免把两种保证压成一个过强假设。

同步更新了思路稿、动态敌手模型和系统规格：补充 `f_r < \tau_r`、不同 generation 份额不可直接组合、交接期间联合暴露条件、`confirmed/committed/sealed/abandoned` 状态和失败交接路径；将 FL 收敛表述改为“保留已接受前缀并在允许的陈旧度范围内追加后缀”，不再声称交接后产生完全相同的更新序列。实验代码本轮保持不变，后续需要增加交接暂缓、实例放弃和 `Commit` 与 `Seal` 分离的轨迹。

下一步先完成 A0 回放器与新状态语义的字段对照，再决定是否同步修改实现状态枚举。真实密码学后端仍需单独验证联合暴露条件和旧状态退役，不能由抽象回放结果替代。

### 2026-09-18（P138：A0 回放器实现交接放弃与 Commit/Seal 分离）

本轮完成阶段 A0 的最小实现修改。`window_finalize` 现在把实例置为 `committed` 并进入 `seal_pending`，结果已经固定但旧可写状态尚未退役；封存配置的 `erase_receipt` 到达后才转为 `sealed`。迟到更新、恢复请求和交接请求在 `committed`、`sealed` 或 `abandoned` 状态下不能改变实例。

交接确认现在只记录后继状态安装完成，仍由旧配置持有恢复权。只有源配置的退役回执到达后，所有者、实例代数和可写资格才转移到后继配置。这样回放器与协议稿中的“安装确认”和“状态退役”顺序一致。

新增 `handoff_abandon` 事件。交接条件长期无法满足时，实例进入 `abandoned`，不创建后继可写副本；合格客户端可以通过 `client_resubmit` 进入新实例，其他实例继续处理。轨迹生成器增加 `--include-handoff-abandonment` 选项，A0 schema 同步增加该事件和 `abandoned` 状态。

验证结果：普通多配置轨迹和包含放弃交接的轨迹均可生成并回放；普通轨迹产生 `committed -> sealed` 的结果路径，放弃轨迹产生 `abandoned` 原实例和独立完成的重提实例。`py_compile`、A0 轨迹生成与回放均通过。当前结果仍只证明服务状态语义，不证明真实阈值重分享、擦除或隐私安全。

下一步补充固定的 A1 至 A4 单窗口轨迹与逐事件期望表，再进入抽象 `authorize_open -> partial_open -> combine_open` 后端；不把放弃实例的服务结果写成密码学隐私保证。

### 2026-09-18（P139：统一实验文档与当前实现边界）

本轮统一系统规格和实验构建稿中的状态顺序：后继安装确认保留源配置所有权，退役回执使所有权和代数转移；`Commit_sid` 固定结果并用于一次模型更新，`Seal_sid` 记录清除完成；`abandoned` 实例没有可用于模型更新的结果。早期记录中的 `finalized` 和“确认后转移所有权”属于旧版本描述，当前以 P138、P139 为准。

A0 已完成 17 列轨迹读取和主要状态转移，阶段 A 的完整验收仍待完成。源码核对显示，A1 中源配置恢复请求会被全局配置检查拒绝，失败确认后的重复安装尚未满足目标轨迹。最低聚合人数及最终状态授权也仍需实现。文档将这些目标与已经实现的正常交接、放弃和 Commit/Seal 分离明确区分。

本轮已保存 A1 至 A4 固定轨迹并完成逐事件比较。A1 允许源配置恢复并重试同一交接；A2 拒绝旧代数恢复和写入；A3 在 `sealed` 后拒绝更新、消息和恢复；A4 使放弃实例停止写入和恢复，并允许合格更新进入新实例。真实训练和密码学后端仍排在这些服务语义检查之后。

### 2026-09-18（P140：完成 A1 至 A4 服务语义回放）

本轮根据 `AGENT.md` 做根因修复，没有加入哈希、SHA 或额外测试框架。回放器现在区分全局活动配置与活动实例的恢复所有者：配置安装后，后继配置可以创建新实例；源配置仍可在确认失败时恢复同一交接尝试并使状态回到 `handoff_pending`。客户端写入继续由活动配置和实例状态共同判断。

新增四条固定 A0 轨迹：`A1-handoff-failure.csv`、`A2-stale-generation.csv`、`A3-sealed-rejection.csv` 和 `A4-handoff-abandon.csv`。逐事件回放结果如下：A1 的源恢复、重装和确认成功，退役回执后所有权转移；A2 的旧代数操作被拒绝，合法代数继续填充同一实例；A3 的迟到更新、交接消息和恢复请求在封存后全部被拒绝；A4 的放弃实例拒绝后续写入和恢复，重提实例与其他新实例可以完成。

这一阶段只支撑窗口服务语义、单写入权、实例连续性和 `Commit/Seal/abandon` 状态边界。它没有支撑最低参与数策略、整体开启授权、真实阈值重分享、擦除的物理保证或模型收敛。下一步实现抽象 `authorize_open -> partial_open -> combine_open` 记录流程，并把它绑定到 `committed` 实例的唯一结果；随后再进入真实训练桥接。

### 2026-09-18（P141：实现抽象整体开启流程）

本轮在 `experiments/abstract_threshold_backend.py` 中实现 `authorize_open`、`partial_open` 和 `combine_open`。证书绑定实例标识、配置、代数、状态版本、维度、已接受更新集合和开启门槛。部分开启只能引用同一证书，并且只能由当前委员会成员产生；合并需要达到门槛且拒绝跨证书组合。

交接微基准同步改为完整顺序：`confirm -> erase(source) -> activate(successor) -> authorize_open -> partial_open -> combine_open -> seal -> erase(successor)`。这修正了此前微基准直接在 `confirmed` 状态调用 `seal` 的接口缺口，也把安装确认和后继可写明确分开。

新增 `experiments/ABSTRACT_OPENING_TRACKER.md`，记录有效路径、拒绝路径和抽象边界。当前流程只检查状态顺序和证书绑定，不代表真实阈值开启安全；证书仍使用更新标识集合作为状态绑定占位，最低参与人数策略和真实认证材料留待后续实现。

### 2026-09-18（P142：补齐整体开启的 FL 绑定与拒绝检查）

本轮复核抽象后端后补上三项约束。第一，`AggregateOpenCertificate` 增加 `model_version`，防止聚合结果接入错误模型版本。第二，后端记录已擦除的 `HandoffRecord`，后继状态只有在源状态确实完成 `erase` 后才能激活。第三，同一证书只能合并一次，部分开启必须来自证书绑定的委员会成员，低于门槛或跨证书组合均被拒绝。

有效路径微基准和定向拒绝检查均通过。检查覆盖未清除不可激活、非成员不可部分开启、低于门槛不可合并、重复合并不可再次发布、未完成开启不可封存。该后端仍是抽象状态模型，不能替代真实认证、阈值安全和安全擦除证明。

### 2026-09-19（P143：修正抽象交接与最终化顺序，保存可重复检验）

本轮继续核验抽象整体流程，复现了同一交接产生两个可写后继、交接时维度可变、安装确认前源状态可清除三个问题；同时发现微基准的 `seal -> erase` 顺序与方案要求相反。抽象后端现在登记唯一实例和唯一后继，维度直接继承源交接记录，源清除以安装确认为前提，激活消费待安装状态。开启授权进入 `opening`，成功合并才进入 `committed`，清除后生成封存记录。封存记录保留实例与模型版本，使用已完成结果中的最终集合。

新增 `experiments/check_abstract_protocol.py`，检查两次连续交接、同一实例继续接收、冲突后继、旧记录复用、证书字段替换、跨实例组合、人数门槛、重复合并及封存后的拒绝行为。六种确认、清除、激活排列全部检查，只有 `confirm -> erase -> activate` 全部成功。此前临时脚本把布尔拒绝当作异常拒绝产生误报，本轮按实际接口分别断言，并直接重用部分开启检查重复合并。

定向检查、交接微基准、编译检查和 schema JSON 语法检查通过。以维度 32、旧委员会 4 人、新委员会 5 人、门槛 3、活动实例 2 个运行，源状态、后继状态、交接和封存记录的符号估算分别为 `4608/4672/9280/192` 字节。数值沿用既有占位规模，真实编码、证明、重传和元数据成本需要具体组件测量。

完整记录保存在 `experiments/ABSTRACT_OPENING_TRACKER.md`，实验构建稿与适配规格同步更正清除顺序。当前抽象后端与服务回放器仍独立运行；下一步连接 `window_finalize`、唯一 `AggregateOpening` 和 `erase_receipt`，并落实最低参与人数及放弃实例的后端处理，再进入真实训练。

### 2026-09-20（P144：消息可达性、实例推进条件及沿既有 FL 工作继续研究）

#### 本轮决定

依据 `AGENT.md`，本轮把既有工作作为方案基础：从 Flamingo 的解密委员会轮换继续研究异步在途聚合，从 LightSecAgg 的聚合恢复与预处理研究减少退出等待。研究对象仍是持续训练中的动态安全聚合。设计目标是保留已确认纳入的客户端计算，使服务更替期间的训练继续推进，并固定已提交结果。

当前结构稿补充了消息丢失、保护载荷可用性、不同操作的参与条件和恢复顺序。$\tau_r$ 表示聚合开启门限；客户端缓冲人数 $k$ 与一致协议的确认人数分别设置。$\ell_r$ 用于故障轨迹和参数分析，正文的活性以一次聚合所需工作能否完成来陈述。

#### 相关工作核对及可继续研究的问题

本轮优先核对本地转写，并在线访问论文原文或正式书目页。以下区分原文机制和本文的研究推论。

| 工作与核对位置 | 原文提供的机制 | 本文在其基础上继续研究 |
|---|---|---|
| [FedBuff，AISTATS 2022](https://proceedings.mlr.press/v151/nguyen22b.html)，正式摘要与书目信息 | 缓冲式异步聚合，兼容安全聚合，并给出光滑非凸条件下的收敛分析 | 将缓冲中的受保护计算跨服务延续，测量服务变化引入的等待、陈旧度与参与差异 |
| [LightSecAgg，MLSys 2022](https://arxiv.org/html/2109.14236v3)，第 3、4、6 节及附录 B | 编码并分发掩码，随后恢复活动用户的聚合掩码；支持异步 FL，并可将编码准备与训练重叠 | 研究哪些准备工作可以提前完成，哪些聚合恢复材料在退出前交付后仍然可用；进一步检查这些机制与服务更替及主动腐蚀的组合 |
| [Flamingo，S&P 2023](https://eprint.iacr.org/2023/486)，第 4.6 节、附录 B.4、结尾的敌手讨论 | 每隔 $R$ 轮更换解密者；通过可验证重分享保持秘密、公钥并改变持有者，可调整人数与门限；正文讨论跨更换的份额累积风险 | 将周期性更换扩展到多个完成进度不同的异步聚合，按实例决定交接或完成开启；受限移动敌手下的组合分析继续沿主动重分享研究推进 |
| Buffalo，本地转写第 5 节 Online Round 2、3 | 助手核对缓冲参与集合，服务器从至少 $t$ 份聚合贡献恢复聚合密钥，验证阶段也依赖足够在线助手 | 将固定参与集合后的聚合恢复与集合尚在增长时的服务交接分开安排，保留其整体恢复思路 |
| Willow，本地 `Secure Aggregation with One-Shot Clients` 第 2.1、6.7 节 | 动态客户端单次提交，委员会承担准备、验证和解密，区分不同输出交付保证 | 继承客户端与辅助角色的分工，继续研究辅助节点本身退出时的职责延续 |
| [Setup Once, Secure Always，ASIACCS 2026](https://doi.org/10.1145/3779208.3785414)，本地转写动态用户机制 | 用户可以在训练轮次之间加入、退出，使用中间服务器辅助聚合 | 研究训练用户变化与秘密持有者变化同时发生的情形，分别核对密文、份额及认证材料如何处理 |
| Privacy-Preserving Federated Averaging with Byzantine Aggregators in Asynchronous Networks，本地转写第 4 节 | 固定聚合者集合；正确参与者之间可靠异步交付；$n_a>3t_a$，$n_c>4t_c$；明确考虑异步参与偏差 | 将其通信和学习分析作为参照，增加服务节点退出导致的消息遗漏与状态延续条件 |
| [DyCAPS](https://eprint.iacr.org/2022/1169) 与 [CHURP](https://eprint.iacr.org/2019/017) | 秘密保持不变时刷新份额并更换持有者；两者的网络与协议条件各有规定 | 在 FL 的活动实例中复用适合网络和敌手模型的组件，以实例完成进度缩减重分享工作 |

Flamingo 的原文需要准确区分两层结论。第 4.6 节确实使用主动秘密共享思想处理解密者更换；其结尾同时明确正式敌手模型是跨轮静态的，并把更强适应性作为研究方向。因此，委员会更换与跨更换风险分析已经提供了实质基础，本文进一步研究受限移动敌手下异步训练状态的延续。后续应从原文条件出发构造扩展方案，并比较扩展前后的能力与代价。

#### $\ell_r$ 的作用与更合适的表述

离开人数或掉线人数是通用的可用性参数。相关工作用不同记号刻画它：LightSecAgg 用 $D$ 表示掉线数，Flamingo 用 $\delta_D$ 表示解密者掉线比例。记号 $\ell_r$ 本身没有独立技术含义；可继承的是对可用性和隐私之间关系的分析方法。

LightSecAgg 选择参数满足：

$$
T<U\le N-D,
$$

其中 $T$ 是合谋上限，$U$ 是聚合掩码恢复所需的编码贡献数，$D$ 是掉线数。降低 $U$ 可以允许更多掉线，同时改变编码、存储和通信成本。该结果分析的是它自身的客户端与掩码协议，具体开销随 $U-T$ 等参数变化，适合启发本文的恢复设计与参数实验。

Flamingo 对其解密者的掉线比例和恶意比例要求 $\delta_D+\eta_D<1/3$，并让解密者职责与提交训练更新的客户端集合分开。这提供了更直接的 FL 参照：先确定某类参与者承担什么职责，再为该职责设置容错条件。

若在本文的一次开启操作中，最多 $f_r$ 个节点拒绝贡献，另有至多 $\ell_r$ 个不同的诚实节点无法贡献，则数值可行性要求：

$$
f_r<\tau_r\le n_r-f_r-\ell_r.
$$

这里 $\ell_r$ 与被计入 $f_r$ 的节点分开统计，且对应当前操作缺少的贡献。已经正确交付的部分开启可以继续计入；随后退出的发送者无需再次提供同一份贡献。冻结确认、秘密重分享和结果确认仍各有推进条件。

例如，$n_r=7,f_r=2,\tau_r=3$，再有一个诚实节点失联时，还可能取得四个诚实节点的开启贡献；若当前一致组件需要五个确认，而两个恶意节点均拒绝响应，则新的开启授权或提交决定仍会等待。若相关授权已经确认，已交付的三份有效开启可以恢复聚合值。这个例子说明，开启门限、消息是否已交付，以及一致决定完成到哪一步，应当一起分析。

本轮采用的改进是按操作写出充分前提，保留具体组件的数值条件。它使模型与训练过程对应得更准确。更高掉线容忍度需要具体协议和证明支持；下一阶段重点检验能否通过提前完成职责减少后续对旧节点在线的依赖。

#### 消息、缓冲和状态延续的统一处理

1. **消息交付。** 持续在线诚实节点之间最终交付；离线或退出前尚未交付的消息允许丢失。其他节点已经保存的材料由保存者继续传送。消息到达后仍需核验当前实例记录及份额代数。
2. **纳入确认。** 已确认更新同时具备一致的纳入记录与可取得的保护载荷。确认者先保存载荷再确认；复制和保存条件由所用可用性协议保证。回执用于核验纳入事实，实际恢复使用载荷。
3. **状态延续。** 后继服务取得与冻结前缀一致的密文、权重、基础模型版本、验证材料和新份额，再按清除与激活条件继续接收更新。成员集合可以不相交，必要交接工作仍须完成。
4. **结果提交。** 开启只合并同一授权与同一份额代数下不同成员的有效贡献。模型应用位置在提交结果时确定，新模型与已应用标记原子保存。结果固定后，清除继续按原持有者职责完成。
5. **条件性推进。** 所需参与者要能够完成源前缀确认、载荷交付、重分享、后继安装、清除和开启等必要操作，并有足够合格更新最终到达。无限次打断同一实例的成员变化可以使它持续等待。其他实例的推进也依赖各自可用性及公平资源调度。

秘密材料的物理清除属于执行假设，退役签名记录协议事件。攻击者已复制的材料计入历史视图。累计暴露按实例份额代数计算，持续到该代材料实际满足清除条件；新服务启动时，旧代暴露预算仍然有效。

#### 沿 Flamingo 与 LightSecAgg 深入的方案路线

**具体场景。** 服务更替时，一个实例仍在收集更新，另一个已经确认最终集合并等待开启，还有一个结果已用于模型。周期性切换可以提供新的份额持有者；本文进一步利用这三种计算进度，分别安排旧节点何时能够退出，以及哪些状态需要交给新服务。

**继承 Flamingo。** 保留其“改变秘密持有者，同时保持既有公钥可用”的技术思路。对仍需纳入更新的实例，用适合异步及受限移动敌手的重分享组件延续状态。对已经授权开启的实例，允许旧持有者先交付可验证的聚合开启贡献，避免等待全部收集和模型发布才完成自己的开启职责。秘密、公钥和密文的具体对应关系仍沿用当前实例密钥方案。

**借鉴 LightSecAgg。** 将与最终参与集合无关的随机性和编码准备尽量放到训练期间，将依赖最终集合的聚合恢复放在集合确定之后。首版先利用现有门限后端验证这种任务安排；编码恢复作为后续候选，核对是否能够减少等待或通信。预先交付的材料须绑定其允许的用途，跨代转录仍需满足受限移动敌手的安全条件。

**需要解决的新增问题。** 在最终参与集合尚未确定时，旧节点怎样交付足够材料，使后继服务能够继续聚合，同时保持整体开启的授权边界？当集合已经确定时，哪些贡献交付后允许发送者退出，哪些一致性或清除职责仍要求其参与？这两问直接决定客户端计算能否保留和退出等待能否缩短。

先比较三种调度：原服务完成所有旧实例后退出；所有活动实例统一重分享；按实例进度分别完成开启或交接。三种策略先使用相同保护后端和相同故障预算，隔离调度机制的收益。测量已确认更新保留率、实例完成率、旧节点所需在线时长、模型推进、通信和陈旧度。墙上时间来自实验测量；理论结论围绕依赖哪些参与者、需要完成哪些步骤和状态是否保持展开。

下一步完成一个双实例方案推演：一个实例继续接收更新，一个实例等待聚合开启；明确每个旧节点最后一项必要工作，以及此后退出对两者的影响。随后据此确定是否需要加入编码恢复。这个方向延续现有成果，也给出能够单独检验的系统改进目标。

#### 本轮文档与验证范围

更新论文结构稿的模型、方案、伪代码及分析口径；为早期动态模型稿添加当前依据说明。修正“任意已完成本地计算均可保留”的过宽表述，保证对象明确为已确认纳入且满足状态可用性条件的更新。收敛部分采用条件明确的训练轨迹保持与后续分析计划。

本轮使用 graft 定位已有抽象协议与回放器，文献依据来自上述原文和本地转写。此次更新属于研究方案和文档修订，实验代码与真实密码学实现保持现有状态。

### 2026-09-20（P145：两个并发聚合的交接与旧节点退出）

#### 研究结论与继承关系

本轮完成 P144 提出的双实例方案推演。当前方案按聚合进度处理服务更替：仍在接收更新的实例延续密文状态并刷新秘密份额；已获整体开启授权的实例交付足够可验证的开启材料；后继服务承接结果确认和模型应用。旧节点的退出条件由尚需完成的交接、开启、清除及协议职责共同决定。

在线复核 [Flamingo 原文](https://eprint.iacr.org/2023/486.pdf)第 4.6 节及 [LightSecAgg 原文](https://arxiv.org/html/2109.14236v3)的恢复与预处理描述。Flamingo 提供改变份额持有者、保持秘密和公钥的基础，本文进一步按并发实例的完成进度安排这项操作。LightSecAgg 提供从已交付编码贡献恢复聚合掩码、将准备工作与训练重叠的基础，本文据此分析哪些必要工作可以在节点退出前完成。

本轮确定的设计扩展是：**后继服务取得继续训练或恢复最终聚合所需的材料，并承接相应的结果确认权限，使原持有者完成交付与清除后能够退出。** 原方案已经具备活动状态重分享和结果最终性；本轮补齐已授权开启实例的结果确认路径，以及旧节点退出与秘密清除的先后关系。

#### 一个具体的双实例场景

原服务和后继服务各有七个节点，允许至多两个腐蚀节点，开启门限取三。这里的人数仅用于展示轨迹；重分享、数据保存及一致协议分别使用满足其假设的参数。设原服务诚实节点为 $p_1,\ldots,p_5$，其余两个节点可能拒绝响应；后继也满足自己的故障与通信条件。

两个实例的缓冲人数均为 $k=3$：

| 实例 | 更替前的计算进度 | 后继需要获得的对象 | 延续后的工作 |
|---|---|---|---|
| $sid_a$ | 已确认客户端 $a_1,a_2$，还在等待第三个更新 | 已确认输入及密文、权重、模型版本、验证材料，以及重分享产生的新份额 | 继续接收 $a_3$，再形成最终聚合 |
| $sid_b$ | 已确认 $b_1,b_2,b_3$，有唯一整体开启证书，等待足够贡献 | 最终密文、权重与版本、原开启证书、不同原持有者的有效贡献及证明 | 恢复固定聚合，由当前服务确认并应用结果 |

两个实例使用独立实例密钥。$sid_a$ 的重分享保持公钥不变，份额代数增加；$sid_b$ 保留原开启证书及原份额代数，合并门限仍采用证书中的原门限。后继人数或新实例门限的变化通过各自记录处理。

#### 从交接决定到训练继续

| 事件 | $sid_a$ 的处理 | $sid_b$ 的处理 | 旧节点还需完成什么 |
|---|---|---|---|
| 1. 原服务确认最终服务记录 | 冻结已确认的两个更新 | 固定已有开启证书及最终集合 | 交付最终记录、密文和验证材料 |
| 2. 后继安装记录并取得后续结果确认权限 | 保持冻结，准备安装新份额 | 承接该固定聚合的结果确认 | 完成仍需原持有者参与的秘密运算 |
| 3. 两个实例并行处理 | 原持有者执行可验证重分享，后继验证新份额 | 原持有者产生绑定同一证书的部分开启，后继接收并验证 | 继续完成重分享中的必要响应；交付尚缺的开启贡献 |
| 4. 后继确认材料可用 | 完整状态和新份额满足安装条件 | 至少三份不同成员的有效贡献及全部解码材料已可取得 | 按各实例及所用组件要求清除旧秘密材料，交付退役依据 |
| 5. 原持有者完成剩余职责并退出 | 满足退役条件后，后继恢复纳入 | 后继依靠已保存材料恢复结果 | 两个实例均已消除对该节点未来响应的依赖 |
| 6. 后继继续训练 | $a_3$ 到达，沿同一实例完成聚合 | 后继确认 $Commit_{sid_b}$ 并应用一次 | 原成员可以保持离线 |

第 3、4 步的两个实例分别推进；$sid_b$ 可以更早发布结果。表中把其发布安排到第 6 步，是为了展示一种有效执行：原节点退出后，后继仍可独立完成该聚合的结果确认。新实例在后继具备初始化与服务条件后也可执行。

原服务最终记录还交付已确认的模型应用序列，以及已提交但尚待应用的结果。若 $sid_b$ 的提交先于交接决定，后继继承该结果和位置；若交接决定先行，后续提交使用后继的授权。原组继续参与重分享内部所需的协议步骤，实例的新纳入和结果决定则服从当前授权。各类职责的完成分别判断。

#### 旧节点的最后一项必要工作

对同时持有这两个实例份额的诚实节点，采用以下可检查的退出条件。它们是一组充分条件，后续可依据具体组件进一步减少等待。

| 职责 | 完成依据 | 完成后仍由谁处理后续工作 |
|---|---|---|
| 服务记录 | 经原服务一致确认的最终记录已经安装到后继，后继取得发布权限 | 当前授权服务确认结果与模型顺序 |
| $sid_a$ 的秘密状态 | 后继完成状态及份额安装，原节点完成组件规定的剩余消息和本地清除，退役依据可取得 | 后继等待新客户端并完成聚合 |
| $sid_b$ 的整体开启 | 后继已保存完整最终密文及至少三份有效开启，原节点完成其秘密清除与退役材料交付 | 后继合并、验证、确认并应用结果 |
| 其他实例及公共职责 | 该节点承担的其他重分享、记录交付或认证转换义务已经完成 | 相应后继或协议参与者接续 |

例如，$p_1,p_2,p_3$ 的有效贡献已经足够恢复 $sid_b$ 时，$p_4,p_5$ 无需再为这个固定聚合产生额外开启；它们仍需满足自己的秘密清除要求及 $sid_a$ 的剩余职责。$p_1$ 发出贡献之后，需要等到接收方确实取得材料并满足保存条件。重分享中的分发、验证与必要的纠错响应，由具体组件规定其完成点。

后继对材料的保存可以先采用完整复制。在固定的七人后继组、至多两人故障且五人确认完整保存的示例中，至少三个诚实确认者持有整个 $sid_b$ 开启材料。其可用性仍依赖这些保存者完成相应服务职责；后继再次更替时，尚待提交的材料继续传送。这是具体的保存前提，人数本身不能覆盖无限连续退出。

本轮充分条件使整个旧组的退出可以先于 $a_3$ 到达，也可以先于 $sid_b$ 的模型应用。各个节点更早退出的机会，还取决于其在所选重分享协议中是否已经完成全部职责。

#### 推演发现的两个实质问题及方案修改

**结果确认仍依赖旧组。** P144 允许旧节点交付开启后退出，但此前的 `Agree(Commit)` 没有指明由谁继续执行。七人原组需要五个确认时，即使后继取得三份有效开启，原组大量退出仍会使依赖旧组的提交停住。

当前方案让结果确认权限随经一致确认的最终服务记录转移。后继验证旧证书和贡献，对由它负责的待提交结果执行当前一致协议。开启证书继续固定原份额持有者和唯一最终集合。这样，秘密运算来源与结果确认权限各有依据，旧组的未来投票从该提交路径中移除。

**清除秘密时也删除了恢复结果所需的材料。** 若实现把实例的秘密份额、已经交付的部分开启和最终密文一起删除，后继可能失去完成结果所需的数据。

当前方案区分本地秘密材料与已授权聚合的恢复材料。后继取得并可靠保存完整开启材料后，原持有者可以按组件条件清除秘密份额。部分开启及证明、最终密文和解码参数继续保存。$Seal_{sid}$ 仍要求结果已提交及清除条件齐备，清除完成与结果提交可以按不同顺序到达。

已授权聚合在足够有效贡献可取得时就可恢复。隐私模型因此将该聚合视为允许输出，模型应用位置可以随后确定。这与实例进入 `opening` 后保持同一最终集合的规则一致。

#### 交错消息与故障检查

| 检查情形 | 推演结果与适用条件 |
|---|---|
| $sid_a$ 冻结后收到第三个客户端的旧提交 | 原服务维持冻结前缀；后继激活后重新核验同一更新标识及保护上下文，通过后追加一次 |
| $sid_b$ 的某份开启仅发出，接收方尚未保存 | 该贡献仍属未完成交付；退出可能使它丢失，完成条件按实际可取得的贡献计算 |
| 收到重复贡献、其他实例贡献或另一代份额贡献 | 按原证书核验，并按不同原成员计数；只接受同一最终聚合下的有效贡献 |
| $sid_b$ 有三份有效贡献，发布权限尚未交接 | 聚合值可以恢复，原组仍按当前授权负责结果确认；整组提前退出尚缺服务记录条件 |
| 原组提交与服务变更交错 | 以原组最终一致记录确定已提交或待提交分支；后继继承原提交，或沿原开启授权提交同一结果 |
| $sid_a$ 的后继安装完成，退役条件仍待满足 | 后继继续等待该实例的激活；$sid_b$ 及具备条件的新实例可推进 |
| 新组再次更替，$sid_b$ 已可恢复但尚未进入模型 | 连同原证书和必要材料转交；其开启代数保持原值，发布权限沿当前服务链推进 |
| 原节点崩溃并保留旧秘密，随后被腐蚀 | 暴露仍计入原份额代数；清除与恢复按既定模型处理，服务更替记录不重置这项累计暴露 |

这些检查是方案层的逐事件推演。新规则尚需在具体组件及抽象后端中实现后验证。

#### 三种处理方式及可检验的收益

| 处理方式 | 对仍在收集更新的实例 | 对已授权开启的实例 | 旧节点退出的主要等待 |
|---|---|---|---|
| 原组完成所有旧实例后退出 | 原组等待后续客户端并聚合 | 原组完成开启与结果提交 | 包含后续客户端到达和旧组最终提交 |
| 统一迁移未完成实例 | 迁移计算状态并重分享 | 若也迁移秘密份额，需构造保持同一最终集合的合法新代开启路径 | 所有未完成实例的秘密状态迁移 |
| 本轮按实例进度处理 | 迁移状态并重分享 | 交付旧代有效开启材料，由后继确认结果 | 必要的秘密运算、材料交付、权限交接与清除 |

第二种方式作为待实现的安全对照：开启之后再次迁移份额，需要规定新代授权如何继承同一最终集合，以及每次合并所使用的单一代数。现有 `Full-transfer` 名称及抽象代码本身不代表已经实现这项能力，后续对照按实际构造标注。

若在同一到达轨迹中，$a_3$ 较晚到达，而所需重分享、开启交付和清除已经完成，本轮方案允许原组更早退出；等待全部旧实例完成的方式仍需等到 $a_3$ 到达。这个条件性差异直接对应维护替换期间的旧节点在线时长和训练连续性。

通信量需要计入 $sid_b$ 的完整开启材料、保存确认和结果验证。相比重分享，实际收益取决于模型维度、实例数量、开启材料大小和组件成本。实验先统一后端、故障预算与客户端轨迹，再分别报告旧节点在线时长、已确认更新保留率、实例完成率、模型推进、陈旧度和通信量。

#### LightSecAgg 的进一步优化位置

当前双实例路径可以使用已有门限后端研究。LightSecAgg 提供的下一步是将独立于最终参与集合的准备工作提前执行，并调整恢复冗余以减少最终等待。对 $sid_a$，可以准备随机性、编码或重分享预处理；具体内容需满足目标协议的安全条件。对 $sid_b$，最终集合已经确定，可以生成并保存只用于该聚合的恢复贡献。

将未满额前缀的开启贡献直接公开，会使后继可能恢复人数不足的前缀聚合。准备阶段应保持这些信息受保护；最终聚合的授权决定何时允许恢复。由此得到一个继续研究的问题：怎样在保持这一授权条件的同时，让更多计算在客户端到齐前完成？后续先分析现有组件已经支持的预处理，再判断是否需要引入编码恢复。

#### 文档、实现状态与下一步

论文结构稿已同步修改服务权限、两个算法、开启材料保存、清除顺序、隐私允许输出以及交接通信量。正文保留两个算法，详细事件表留在本追踪中。

graft 核对表明，现有抽象后端在 `combine_open` 成功后直接置为 `committed`，`erase` 的当前路径也围绕整体实例状态组织；它尚未表示本轮的后继结果确认、开启材料持久保存和逐节点清除。因此，本轮完成的是方案推演与文档更新，代码仍代表此前的抽象边界。

下一步将两个路径对应到实际密码学组件：列出每一步的发送者、接收者、可验证材料和完成依据，核对重分享的最后一次必要旧节点响应，以及公开可验证开启贡献能否在发送者清除后独立合并。以此得到完整的消息流程和通信成本，再决定预处理或编码恢复的优化。

### 2026-09-20（P146：具体组件、消息交付与通信成本）

#### 本轮结论

本轮把双实例方案对应到具体组件。已授权聚合采用系数域阈值 ElGamal 和可公开验证的部分开启，接收者取得足够有效贡献后可独立合并。仍需纳入更新的实例采用主动重分享延续密钥；旧成员的最后一次秘密运算、消息真正可取得的时点，以及新成员完成刷新是三个不同事件。

这一核对产生两项后续研究依据。第一，DyCAPS 和 Optimistic DPSS 已经提供旧成员较早结束参与的机制，本文继续研究这些机制在退出可能丢失消息、多个聚合并发推进时的使用方式。第二，开启材料的通信随密钥系数维度增长，按实例安排退出的价值应同时由旧节点在线时间和完整通信量衡量。

#### 文献与实现依据

| 来源 | 核对内容 | 对本文的含义 |
|---|---|---|
| [DyCAPS 原文](https://eprint.iacr.org/2022/1169)，本地 `dycaps_2022_1169_layout.md` 第 II.B 节、第 V 节、图 6 至 8、Lemma 4 | 私密且前向安全的异步通道；已发送消息最终交付；每个诚实旧成员先取得前次有效份额。旧组完成 Prepare、ShareReduce 后清除并离线，新组完成刷新及份额分发 | 提供受限移动敌手下的参考结构；本系统的退出丢消息模型需要落实消息交付，连续交接需要保持其份额就绪前提 |
| [Optimistic Asynchronous DPSS，S&P 2026](https://eprint.iacr.org/2025/880)，2026-05-18 完整版第 4.1 节、算法 1 至 3 | 每个 epoch 开始时选定至多 $t$ 个腐蚀节点。旧成员取得分享证明并广播后删除秘密；新组通过一致选择和内部恢复得到新份额 | 可证明分享与后继恢复是重要优化基础；现有安全论证适用于该 epoch 内固定集合的模型 |
| [Optimistic DPSS 开源实现](https://github.com/opDPSSTeam/Implementation)，`internal/DPSS/DPSS.go` | 旧节点广播承诺及分享证明，后继验证证明后执行选择；使用独立的签名验证对象 | 提供消息流程和性能实现参考，内存清除及本文的退出保存条件需另行落实 |
| [DyCAPS 开源实现](https://github.com/DyCAPSTeam/DyCAPS) | 原论文公布的实现仓库，本轮确认可访问 | 用于后续核对完整重分享的实际消息及成员结束条件 |
| Buffalo 系数域方案，P128、P129 | 既定候选参数 $m=2048,\rho=16$；实例随机标量保护有界系数 | 沿用已有保护选择，本轮明确部分开启公式与字节预算 |
| Flamingo 第 4.6 节及 LightSecAgg 恢复、预处理部分，见 P144、P145 | 委员会轮换、既有贡献支持聚合恢复、准备工作与训练重叠 | 本文沿这些机制研究参与职责何时完成，以及提前准备如何影响退出等待 |

对 Optimistic DPSS 的敌手模型，本轮同时核对本地 PDF 与在线完整版，二者相关表述一致。P128、P129 中将其列为候选后端的选择继续用于功能和性能研究；周期内自适应腐蚀下的保证需要相应扩展。保持本文受限移动敌手模型，以 DyCAPS 的相关分析作为参考，并核对增加的公开材料与传输方式。

#### 已授权聚合：具体开启组件

实例密钥为 BLS12-381 G1 上的随机标量 $z$，公钥为 $zG_1$。旧组持有同一代的多项式份额 $z_i$。每个成员的公开验证值 $X_i=z_iG_1$ 要与这代重分享输出相符：使用该组件的份额承诺及验证依据确认，验证值随代数刷新。

客户端在保护前将样本权重用于模型增量编码，密钥系数仍按原分布采样。因此最终系数和的范围由参与人数与 $\rho$ 决定。若改为密文生成后再按客户端权重缩放，系数和范围也需乘入相应权重；首版采用前一种流程。

对第 $j$ 个系数：

$$
e_{u,j}=(r_{u,j}G_1,\ a_{u,j}G_1+r_{u,j}zG_1),\qquad
(U_j,V_j)=\sum_{u\in A_{sid}}e_{u,j}.
$$

成员 $i$ 生成 $D_{i,j}=z_iU_j$，附带已有 Chaum–Pedersen 型非交互证明，证明同一个秘密份额满足：

$$
X_i=z_iG_1,\qquad D_{i,j}=z_iU_j.
$$

证明的上下文绑定最终开启证书、成员、系数位置和份额代数。接收方同时核验成员资格、份额验证值、完整系数向量及证明。选取任意 $\tau_r$ 个不同的有效成员后，以该代插值系数 $\lambda_i$ 计算：

$$
V_j-\sum_i\lambda_iD_{i,j}
=\left(\sum_{u\in A_{sid}}a_{u,j}\right)G_1.
$$

在 $[-k\rho,k\rho]$ 中恢复系数和，然后执行 NTT 并解码受保护的加权模型和。合并只使用已交付的公开可验证材料，秘密份额在此前满足交付与清除条件后可以销毁。具体证明库的安全假设、群编码与成员公钥验证仍需在实现时固定。

这里采用的是既有门限加密与等离散对数证明；研究机制在于这些材料如何跨服务保留并支撑原节点退出。输入模型沿用系数采样和载荷有效性要求，恶意客户端扩展需同时验证密钥范围及其与受保护更新的关系。

#### 密钥与群参数的组合条件

实例解密密钥、服务认证密钥、阈值签名密钥、交接接收密钥独立生成。尤其在使用双线性群时，要审查公开材料中是否出现与实例秘密相关的另一源群元素。

例如，若额外公开 $zG_2$，对于单个客户端系数密文 $(U,V)$，观察者可测试一个小范围候选值 $a$ 是否满足：

$$
e(V-aG_1,G_2)=e(U,zG_2).
$$

该等式会泄露有界系数，破坏原先依赖 G1 中 DDH 的保护。因此，实例秘密 $z$ 及其份额只通过所选加密和重分享接口使用，服务签名使用独立秘密。KZG 的 G2 设置参数可以存在，但其秘密须与实例秘密独立；加入公开份额验证值时也应审查完整转录。

这是组件组合的具体约束，未据此断言已有 DPSS 实现存在漏洞。DyCAPS 的复用份额生成阈值签名技巧需要按本文的加密用途重新选择，直接采用独立认证材料可以保持两种用途分离。

#### 活动实例：重分享的实际结束条件

DyCAPS 的旧成员持有二元多项式的完整份额。份额转换时，旧成员向指定新成员发送一个求值及其证明；新成员取得足够有效求值后形成中间份额，再在新组内完成刷新和分发。原文图 6 中，旧成员发送必要的 Reduce 消息后清除并离线。Lemma 4 明确旧组只参与前两个阶段。

因此，“旧组必须一直在线到新组完成所有计算”可以进一步放松。原文保证依赖已发送消息最终交付。本文允许发送者退出后在途消息丢失，需要把退出前的最后一项职责从发出消息落实为使必要消息可取得。

先采用一个容易审查的保存方案：每个旧成员将发给所有新成员的必要私密消息分别加密，形成完整的交付批次；后继保存这个批次的副本，指定接收者之后取出属于自己的消息并验证。复用已有保护载荷的保存机制即可表达这一流程。

| 步骤 | 发送者与接收者 | 传送内容 | 完成依据 |
|---|---|---|---|
| 1. 确认实例及成员依据 | 原服务至后继 | 冻结前缀、当前份额承诺、合法后继及接收公钥 | 后继验证服务记录与实例绑定 |
| 2. 完成原成员的份额转换 | 每个旧持有者至后继保存者 | 按指定接收者分别加密的求值及证明，连同验证所需公开材料 | 旧持有者完成该组件要求的全部外发输入 |
| 3. 保存必要消息 | 后继保存者至旧持有者 | 对完整批次的认证保存确认 | 达到明确的保存条件；确认者实际持有全部密文 |
| 4. 原持有者结束该实例职责 | 旧持有者至后继 | 本地清除后的退役记录 | 交付条件成立，且其后再无组件规定的旧成员响应 |
| 5. 后继取得并处理消息 | 后继内部 | 指定接收者取得密文、解密、验证，继续刷新与恢复 | 产生有效新份额及其承诺 |
| 6. 恢复客户端纳入 | 当前服务内部 | 同一输入前缀、新份额及退役依据 | 满足实例激活条件 |

在 $n'=3f'+1$、至多 $f'$ 个故障保存者的参考情形中，收集 $n'-f'$ 个完整批次保存确认，至少意味着 $n'-2f'=f'+1$ 个诚实保存者持有该批次。保存者持续履行本次交付职责时，指定接收者可以从这些副本取得完整的原始消息。秘密份额仍只交给各自指定接收者，保存者看到的是密文。

确认内容是完整的必要消息批次。只确认“某些接收者各自收到了自己的份额”可能留下其他诚实接收者无法恢复的输入，所需恢复关系必须由组件证明。本轮采用完整批次复制，把这一条件落实为实际数据可用性。

交接消息可使用认证的临时接收公钥和标准公钥加密封装，例如独立的 HPKE 接收密钥。保存密文本身不提供前向安全；接收者完成本次交接后还需销毁相应私钥、解密中间状态及可恢复副本。接收密钥在删除前的腐蚀暴露纳入对应交接视图。具体实现须满足 DyCAPS 的私密及前向安全通道要求，保持同一实例跨代的联合暴露条件。

这项保存改动使旧节点有机会在后继完成刷新前退出。P145 的算法仍以实际安装后退役作为保守路径；提前退出作为本轮明确了消息流程的优化候选，待完成通信实现与原组件假设的对应核验。后继连续启动下一次交接时，仍须满足原组件对每个诚实旧成员已有有效份额的前提。

#### 从 Optimistic DPSS 进一步改进

Optimistic DPSS 算法 1 的分享方先分发份额、收集新组确认，再取得分享证明。算法 3 的旧节点广播该证明后删除私密信息；后继通过一致协议选择有效分享，并在缺少本地份额时向新组内其他节点恢复。因此，它已经把部分“保存整个消息批次”的需求转化为更紧凑的可恢复性证明。

本文可以沿这一机制研究：旧成员在交付分享证明及所需承诺后退出，后继用已有的内部恢复完成接替。退出丢消息模型下，最后的公开证明和承诺仍要可取得；直接广播后离线仍需相应交付条件。

这一方向的潜在收益是减少完整批次复制的通信和状态。下一阶段应同时检验其 epoch 内固定敌手分析怎样扩展到本文模型，以及原接收者退出时恢复材料是否仍然足够。原文的分享证明、恢复结构和完整实现都作为可复用基础。

#### 已授权实例：完整消息流程

| 步骤 | 发送者与接收者 | 内容及验证 | 结束条件 |
|---|---|---|---|
| 1. 交付最终聚合依据 | 原服务至后继 | 唯一开启证书、参与集合、模型版本、权重、最终密文及原代验证参数 | 后继核验授权并取得完整解码输入 |
| 2. 产生开启贡献 | 原证书中的持有者至后继 | 全部系数的部分开启及证明，绑定同一证书 | 接收者确认有效且来自不同原成员 |
| 3. 确认恢复材料可用 | 后继保存者至原持有者 | 已有至少 $\tau_r$ 个成员完整有效贡献、最终密文及元数据的保存确认 | 满足公开恢复材料的保存条件 |
| 4. 结束秘密持有 | 仍持有该实例秘密的旧节点 | 销毁秘密份额及相关恢复秘密，交付退役材料 | 满足组件清除条件，其他实例职责另行完成 |
| 5. 恢复和应用聚合结果 | 后继内部 | 合并、系数解码、RLWE 聚合解码，再确认唯一结果及模型位置 | 由当前服务完成提交和一次应用 |

第一版可让响应的原成员直接向所有后继发送开启贡献，使后继自行验证和收集，避免结果恢复依赖某个临时收集者持续在线。后继确认完整恢复材料已保存后，原成员按清除条件退出。后续通过标准批量证明或经过验证的可靠分发降低重复传送成本。

开启贡献是最终聚合的公开恢复材料，与仍需重分享的私密输入分别处理。部分开启证明使用标准非交互组件时，原持有者的最后一次秘密操作就是生成对应贡献和证明；此后仍需完成交付确认与本地清除。

#### 通信预算

以下为候选编码的解析预算，未运行真实密码学基准。沿用 P129 的 $m=2048$，压缩 G1 点取 48 字节，标量取 32 字节。为便于核算，先为每个系数使用包含两个群承诺和一个响应标量的证明，计 128 字节；证明压缩或批量化另行比较。

令 $b_G$ 为一个点的字节数，$b_\pi$ 为一个证明的字节数，则：

$$
S_K=2mb_G,\qquad
S_{\mathrm{partial}}=m(b_G+b_\pi),
$$

$$
S_{\mathrm{opening}}
=S_C+S_K+\tau_r S_{\mathrm{partial}}+S_{\mathrm{meta}}.
$$

$S_C$ 表示受保护模型聚合，$S_{\mathrm{meta}}$ 包括最终集合、证书、份额验证依据、编码参数及权重。预算采用完整成员贡献；同一成员任一坐标验证失败时，该向量不计入有效完整贡献。

| 项目 | 候选参数下的字节数 | 计量范围 |
|---|---:|---|
| 一个客户端的系数密文向量 | 196,608，即 192 KiB | $2m$ 个点；模型密文与输入证明另计 |
| 一个成员的完整开启贡献及逐系数证明 | 360,448，即 352 KiB | $m$ 个贡献点及 $m$ 份证明 |
| 三个成员的开启贡献及证明 | 1,081,344，即 1,056 KiB | 开启门限为三 |
| 系数密文加三人贡献 | 1,277,952，即 1,248 KiB | 尚需加入 $S_C$ 与 $S_{\mathrm{meta}}$ |
| 七个旧成员各向七个后继发送完整贡献 | 17,661,952，即 16.84375 MiB | 首次完整发送的总量；密文、确认、重传与成员协议另计 |

最后一行是指定发送方式的总传输预算。有效贡献可能较早到齐，实际实现可以停止冗余发送；异步重传和故障恢复增加的字节单独测量。候选基线也需要完成聚合开启，比较时分别列出一次正常开启的共同成本与更替引入的增量。

对活动实例，每次重分享的是实例秘密标量，代价主要随成员数增长。DyCAPS 在等规模委员会中给出 $O(\lambda n^3)$ 位通信；Optimistic DPSS 的原模型和设置条件下，乐观情形为 $O(\lambda n^2)$，最坏情形为 $O(\lambda n^3)$。这些复杂度对应各自原协议，应用层密文和消息保存开销另加。

若一个旧成员向 $n'$ 个新成员各发送一个长度为 $b_{\mathrm{packet}}$ 的加密求值消息，则 $n$ 个旧成员直接发送的载荷是 $nn'b_{\mathrm{packet}}$。把每位旧成员的完整批次复制给所有 $n'$ 个后继，载荷变为：

$$
C_{\mathrm{copies}}=n(n')^2b_{\mathrm{packet}},\qquad
\Delta C=nn'(n'-1)b_{\mathrm{packet}}.
$$

这里 $\Delta C$ 是替换原始发送方式后的额外复制量，避免与原 DPSS 成本重复相加。认证、公开参数、回执和故障补发另外计量。在相同规模下，完整批次复制仍可能达到立方通信量；这解释了继续研究可证明分享与后继内部恢复的价值。

以七人旧组和七人后继为例，一个标量求值加一个 G1 证明为 80 字节，若采用增加 32 字节封装公钥和 16 字节认证标签的封装，载荷取 128 字节，则完整复制这些求值载荷为 43,904 字节。该数值只用于展示复制项，未计入其他承诺、签名、消息标识及新组刷新通信。

#### 对主线和实验的影响

本轮主线进一步明确为：**按照聚合的计算进度，让旧节点把后续训练所需的材料交付给后继，并在完成本地职责后退出。** 已有动态秘密共享解决持有者更换，本文研究这种更换怎样支持未满额聚合继续训练、已授权结果继续发布，以及退出等待与通信之间的取舍。

实验应同时报告旧节点最后一次秘密运算、交付完成、实际退出、后继就绪和模型应用的时刻。这些是测量事件，协议判断继续使用收到的消息和有效证据。分别比较安装完成后退出与消息可取得后退出，固定同一客户端到达、故障预算和保护后端。

下一步先验证提前退出的交付条件：指定接收者暂时失联、原发送者退出、随后接收者恢复，仍能取得并验证自己的交接输入；新组内部继续完成原组件。并行核对一组系数密文在份额清除后是否能由已保存的贡献独立解码。通过后再选择批量证明、可证明恢复或编码方法优化通信。

本轮完成原文与公开实现入口核对、消息表和解析字节预算，正文同步加入组件分工及开启公式。现有抽象代码仍使用符号贡献，真实密码学、提前退出优化及性能结论均待对应实现验证。

### 2026-09-20（P147：发送者退出后的独立恢复）

#### 本轮判断

发送者结束参与后，后继可以继续使用已经交付的材料。两类实例需要的条件不同：活动实例的接收者还需要解密交接输入，已授权实例则可从完整开启贡献恢复聚合。前者保留指定接收者的接收私钥，后者只需公开恢复材料。

本轮增加 `experiments/check_departure_recovery.py`，以独立进程检验这些数据依赖，使用本机已有 PyNaCl 1.5.0。完整重分享和可公开验证开启仍按 P146 的组件方案推进；本轮结果支持其中的材料恢复步骤。

#### 执行与证据

先写检查，确认缺少材料生成时出现预期失败，再实现生成与恢复。最终运行命令：

```bash
python3 experiments/check_departure_recovery.py
```

材料生成子进程返回后即结束。返回内容包含接收者自己的交接私钥、源签名公钥、按接收者加密的消息批次，以及公开的系数密文和部分开启。源签名私钥、实例秘密、多项式系数及成员秘密份额均未返回。系数恢复在新的子进程中运行，输入只有公开材料。

| 路径 | 成功条件 | 实际检查结果 |
|---|---|---|
| 交接输入 | 真实加密消息副本、指定接收者私钥、可信源签名公钥 | 三个完整副本中移除一个，接收者仍取得并验证原载荷 |
| 输入取回与认证 | 保留正确密钥并取得对应消息 | 缺少副本、换用新私钥、源公钥不符、密文篡改和取错接收者均被拒绝 |
| 系数聚合 | 同一上下文、足够不同成员的完整正确贡献 | 四种三人子集和四人集合都恢复三个客户端的系数和 $[3,0,-4]$ |
| 贡献集合检查 | 人数、实例、代数和向量完整性符合预置条件 | 人数不足、重复成员、跨代、跨实例和缺项均被拒绝 |
| 未验证贡献的对照 | 所有成员的首个贡献点均被加上一个基点 | 合并值变为 $[2,0,-4]$，说明代数合并需要与贡献证明验证组合 |

最后一项用于检验贡献验证的必要性。身份、代数与维度检查只能确认材料的对应关系；正确部分开启还须满足 P146 的等离散对数关系。正式开启流程在计入贡献之前验证该证明。

交接使用 SealedBox 加密及独立 Ed25519 签名，签名内容绑定实例、代数和接收者。载荷是代表 Reduce 输入的固定字节串；批次复制与一个副本不可用在本地模拟。开启使用 Ed25519 素数阶子群检验门限 ElGamal 的插值和有界整数恢复。论文候选仍为 BLS12-381，本次运行没有测量 P146 的编码或通信预算。上下文由检查直接给定，认证共识证书、DPSS、贡献证明和 RLWE 解码都留给对应组件。进程结束用于检查后续计算是否依赖源进程，物理安全清除继续作为单独假设。

#### 对恢复条件的修正

**第一，恢复时保留仍有效的接收秘密。** 原先“恢复节点先清理过期状态”的要求，需要明确哪些材料仍有效。尚待取得的交接消息仍依赖其指定私钥；节点应先依据当前记录判断职责，再清理已经失效的秘密。接收私钥保留到相关输入被处理、组件的恢复条件满足后清除。私钥丢失后重新加入可以取得新的成员身份，原密文的解密则需要原密钥或组件另行提供的份额恢复。

这一条件同时影响隐私。旧发送者的秘密已经清除时，接收私钥仍可能解开保存的交接输入。腐蚀统计须覆盖该私钥、解密中间值及其能恢复的相关秘密，并依据主动重分享组件分析新旧视图的联合暴露。

**第二，副本保存是一项持续职责。** P146 中的 $n'-f'$ 个完整批次确认，在该保存期间故障上限为 $f'$ 时，给出至少 $n'-2f'$ 个诚实持有者。消息最终可取得还要求接收者恢复后能联系到诚实完整副本。保存者持续退出时，需要继续转交材料和交付职责；确认时的人数不能单独推出未来可用性。

**第三，保存输入与输入有效性分别检查。** 一个保存者可以持有全体接收者的密文，却无法验证其他接收者解密后得到的求值是否有效。完整复制落实了消息可取得性；有效输入数量、源方作恶处理及新份额恢复沿用 DPSS 的证明与接收规则。旧节点提前退出的条件应包含该组件要求的全部外发材料和响应。

#### 对方案和下一阶段的安排

论文结构稿第 3.1.2 节补充接收私钥的恢复规则，第 3.3 节补充持续保存职责和本轮验证范围。两个主体算法继续使用已经约定的保守安装条件，提前退出仍作为待接入完整组件的优化。

当前抽象后端的 `combine_open` 通过原进程登记表识别贡献，并将合并直接记为 `committed`。它适用于早期状态顺序检查。本轮增加独立恢复实验，后续接入时应让公开材料支持合并，再由当前服务分别决定结果提交及模型应用。

下一步聚焦组件接合：从所选 DPSS 实现中确认旧节点最后一次必需响应，以及缺失接收私钥时的新组内部恢复能力；同时选定具备证明验证的部分开启实现。沿用双实例场景，比较后继安装完成后退出与完成可恢复交付后退出，报告旧节点在线时长、后继就绪时间、客户端计算保留率和通信增量。系统收益由这一比较验证，正文继续围绕训练连续性组织。

### 2026-09-20（P148：真实 DPSS 接入与实验目录整理）

#### 本轮完成

按用户要求，将所需上游代码集中在 `experiments/upstream/`，拉取 DyCAPS、Optimistic DPSS 和 Buffalo。DyCAPS 最初下载于 `artifacts/`，本轮已移动至实验目录。三个上游仓库保持原样。

旧 `EXPERIMENT_BUILD.md` 与 `EXPERIMENT_PLAN.md` 移至 `experiments/archive/legacy-design/`，保留此前基线方案与执行记录；当前入口为 `experiments/README.md` 和 `experiments/REAL_COMPONENT_BRINGUP.md`。抽象协议、已有故障轨迹及材料恢复检查继续作为回归依据。历史条目中的旧文档路径对应此次归档文件。

#### 实际接入结果

新增 `experiments/dycaps_handoff_test.go` 和 `experiments/run_dycaps_handoff.py`，通过 Go overlay 调用原版组件。生成进程运行 VSS、Prepare 和 ShareReduce，保存真实消息后结束；随后独立启动后继进程，运行 PrepareReceive、ShareReduceReceive、ProactivizeAndShareDist 及其内部 MVBA。

先为两个客户端生成三系数向量的密文和，后继完成交接后再保护并纳入第三个向量。所用系数为 $(1,2,-3)$、$(4,-1,1)$ 和 $(-2,-1,-2)$。最终从真实 BLS12-381 点中恢复有界整数，得到 $[3,0,-4]$。

| 检查 | 运行结果 |
|---|---|
| 旧组进程结束，后继只读交接消息 | 完成刷新及份额分发 |
| 四个新成员的份额与原份额比较 | 全部发生变化 |
| 四人中任意两人的全部六种组合 | 实例公钥保持；聚合均为 $[3,0,-4]$ |
| 16 份原始 Reduce 求值及 KZG 见证 | 全部通过验证 |
| 将这 16 个求值分别加一 | 原 KZG 验证器全部拒绝 |
| 每个后继只收到两个不同旧节点的输入 | 完成交接与同一聚合 |
| 一个后继暂时只有一份 Reduce 输入 | 100 ms 观察期间未完成；补齐保存的消息后完成 |

这里 $n=4,f=1$，完整份额的开启门槛为 $f+1=2$；一致及签名相关流程采用 $2f+1=3$，客户端缓冲人数取三。参数沿用真实组件，区别于前一轮代数检查中预置的三人开启门槛。

负数编码在初次运行中暴露适配问题：原库的字符串导入使用大整数绝对值。当前适配代码改为有限域减法，检查覆盖正、负和零聚合。故障设计也按实际门槛修正：四节点中丢一条消息仍可能成功，暂停条件应是可用有效输入不足两个。

运行命令为 `python3 experiments/run_dycaps_handoff.py`，sender、successor、quorum、recover 四阶段均通过。公开结果、环境信息及原始日志位于 `experiments/results/dycaps-handoff/`；临时交接文件在结束后删除。旧的两项 Python 检查也重新执行通过。

#### 上游运行与范围

DyCAPS 的基础 BLS、多项式承诺和插值测试通过。上游完整测试含命令包格式化检查错误及固定端口测试，本轮未将全包结果记为通过。新增实验仅在编译视图中接入测试，原协议代码保持原样。

Optimistic DPSS 基础组件分组测试通过；全包测试涉及未安装的 Pointproofs 原生库和固定端口冲突。隔离运行 `TestDpssNew` 后，测试在 45 秒限时内未完成，日志保存在 `experiments/results/optimistic-dpss-test.log`。继续将它作为可证明恢复优化的参考，后续定位具体等待原因。该观测本身不构成协议活性反例。

Buffalo 已下载，仓库含 FLSim 副本及 RLWE 代码。本机已有 PyTorch 和 NumPy，缺少 Bazel，RLWE 扩展尚未构建。

本次真实交接检验使用每组一个进程、组内通道、可信初始化方和上游公开测试 KZG 设置。临时文件包含私密 Reduce 输入，用于组件接合；真实私密传送与安全清除尚待实现。KZG 求值证明已运行，最终部分开启的证明尚未接入。因此，本轮结果支撑诚实执行下的状态延续和跨交接聚合，移动敌手隐私、实际网络代价及训练性能仍分别验证。

#### 下一步

以已跑通的交接为基础，将真实 Reduce 消息接入按接收者加密的保存及恢复流程，再加入可验证的部分开启。随后接 Buffalo 的 RLWE 编码与小规模训练，保持同一纳入集合和模型应用次序，验证成员变化前后的模型轨迹。模型质量与旧节点在线时长的对照实验沿此实现扩展。

### 2026-09-20（P149：原生组件核验与基线边界）

#### Buffalo

Buffalo 的 Bazel 原生构建已经完成，C++ RLWE API 测试和 Python 原生测试通过。项目侧核验覆盖 $2^{11}$ 维加解密、五个独立密钥在同一 RLWE 上下文中的模加聚合、密钥向量求和、共享矩阵 seed 下的单实例复现以及 Python 包装器的往返路径。三个入口分别记录在 `experiments/results/upstream-verification/buffalo/`。

探索性检查还发现一个需要保留的基线边界：将五个客户端建成独立 Python 对象并仅共享 seed 时，聚合解密结果不稳定。该路径不计为通过，也没有修改 Buffalo 上游代码。当前实验只能把上游已经测试的同一上下文聚合作为密码学组件基线；真正多进程客户端到服务的路径需要单独定位。FLSim 的两个 FedBuff 一致性测试仍失败，一个指标隔离测试通过，因此 Buffalo 还不能作为完整动态 FL 系统验证。

#### Optimistic DPSS

用上游 `cmd/test_main.sh` 的参数语义复现 $n=4,f=1$ 八进程交接。一次运行中四个新成员和两个旧成员完成，两个旧成员停在 `wpACSS` 交互；另一次运行在新成员处理承诺时出现 `input string length must be equal to 48 bytes`，其余进程等待。两次均在 30 秒限时内没有完整通过。基础 BLS、DPRF、party、承诺、多项式、VSS、Reed Solomon 和 vector commitment 测试仍通过；Pointproofs 原生库缺失和固定端口复用继续阻断全量测试。

该结果把 DPSS 的定位收紧为“组件测试已通过，原生交接入口待定位”，不能据此宣称动态交接端到端可运行。首个真实交接基线仍采用已完成原生 TCP 与十节点核验的 DyCAPS。详细命令、日志和限制见 `experiments/REAL_COMPONENT_BRINGUP.md`。

#### 下一步

先把 Buffalo 的多进程 seed 共享问题缩小到上游 RLWE 上下文初始化或进程间包装方式，再决定是否将其用于小模型端到端比较；并行把已通过的 DyCAPS Reduce 输入接入按接收者保存与恢复流程。DPSS 暂不进入主性能表，直到原生交接能够稳定完成并通过独立结果检查。

### 2026-09-20（P151：独立保存者与发送者退出）

#### 流程修改

将加密交接拆成五个独立阶段：`sender` 生成真实 Prepare/ShareReduce 消息，`persist` 保存加密封装，随后由 `successor`、`quorum` 和 `recover` 读取保存库。保存库只包含实例元数据、源公钥、后继公钥和加密封装；后继私钥通过独立的后继密钥文件提供，发送者原始 fixture 在 persist 阶段完成后删除。

保存者不解密消息，也不需要访问 Reduce 求值或旧成员份额。后继恢复时重新验签、解密并反序列化原始 protobuf 消息，再交给 DyCAPS 的 `PrepareReceive` 和 `ShareReduceReceive`。因此测试覆盖了发送者进程结束后，保存库仍能支撑真实交接输入的路径。

#### 结果

运行命令：

```bash
python3 experiments/run_dycaps_handoff.py \
  --output experiments/results/dycaps-handoff-saver
```

`sender`、`persist`、`successor`、`quorum`、`recover` 五阶段全部通过。persist 记录 32 个已保存封装，保存库不包含后继私钥，并确认发送者 fixture 已删除。正常路径打开 32 个封装，quorum 路径打开 16 个，recover 路径在缺少输入时等待 100 ms，随后从保存库补开剩余封装，最终打开 32 个。三条交接路径都保持实例公钥、刷新四份新份额，并恢复系数聚合 $[3,0,-4]$；16、8、16 份有效 Reduce 证明分别通过。

#### 研究边界

该实验已经把“消息可取得”从源节点进程中分离出来，但保存者仍是诚实进程，后继私钥由测试夹具预置。P152 已加入两个保存者的完整副本复制和保存者 A 退出路径；交付确认、部分副本和保存职责接力仍待实现。

### 2026-09-20（P150：真实加密交接接入）

#### 实际修改

在 `experiments/dycaps_handoff_test.go` 的 overlay 中，将真实序列化 `Prepare` 和 `ShareReduce` 消息封装为按后继区分的密文。每个后继拥有自己的 Curve25519 接收密钥，源进程使用匿名盒加密消息，并用 Ed25519 签名绑定后继、发送者和消息类型。后继先验签，再用自己的私钥解密，最后把原始 protobuf 消息交给 DyCAPS 的接收函数。上游仓库保持原样。

#### 运行结果

运行命令：

```bash
python3 experiments/run_dycaps_handoff.py \
  --output experiments/results/dycaps-handoff-encrypted
```

| 路径 | 打开封装 | 有效 Reduce 证明 | 聚合结果 |
|---|---:|---:|---|
| 正常 successor | 32 | 16 | $[3,0,-4]$ |
| quorum，保留两个旧发送者 | 16 | 8 | $[3,0,-4]$ |
| recover，延迟后继 0 的部分消息 | 32 | 16 | $[3,0,-4]$ |

四个后继共保存 32 个加密封装；四个阶段均通过，份额刷新、公钥保持和六种两人恢复检查继续通过。recover 路径先让接收线程在缺少消息时等待，100 ms 后从保存的加密封装解密并验证剩余输入，说明交接消息保存可以与原版 Reduce 接收逻辑直接衔接。

#### 范围与下一步

该实验验证消息机密性、来源认证和真实 Reduce 输入恢复，密钥由测试夹具预置到对应后继，不能替代论文中的密钥分发、清除和受限移动敌手证明。下一步把保存确认、部分副本和保存职责接力接入本轮多保存者路径，再连接部分开启与模型更新应用。

### 2026-09-20（P152：多个保存者与保存者退出）

将加密交接运行器扩展为七个阶段：`sender` 生成消息，`persist` 写入保存者 A，`replicate` 将完整保存批次复制到保存者 B，`retire` 删除 A 的保存库，随后由 `successor`、`quorum` 和 `recover` 只读取 B。后继私钥仍保存在独立的后继密钥文件中，复制过程不读取或复制私钥。

该路径检验保存者 A 退出后，后继仍能从 B 取得并验证全部按后继加密的 Prepare 和 ShareReduce 封装，同时保留延迟恢复、输入门槛、KZG 验证、公钥保持和系数聚合检查。本轮 A、B 均按诚实保存者运行，复制采用完整批次；多个保存者故障阈值、恶意副本检测和保存职责接力协议仍待实现。

### 2026-09-21（P153：本文协议内核与实现追踪）

本轮将实现重点转到本文的聚合延续机制。新增 `experiments/reconfigurable_async_fl.py`，复用已有抽象份额组件，独立实现实际加权聚合、按实例选择延续方式、固定开启授权、结果提交及模型应用。本文协议记录把聚合恢复与提交分开；新服务可以在旧实例等待交接时推进新训练。

`python3 experiments/check_our_protocol.py` 通过 66 个主轨迹事件与逐项重放检查。活动实例跨组保留两个客户端的已完成更新，纳入第三个迟到更新后恢复 $(7/4,-1/4)$；与已授权实例、新实例共同产生的模型为 $(53/24,-35/24)$。独立检查覆盖重复纳入、参与集合绑定、全部六种交接事件顺序、贡献者退出、两次不相交更替与两代重叠暴露。原抽象协议回归和 Python 编译检查通过。

新增 [本文方案实现追踪](experiments/OUR_PROTOCOL_IMPLEMENTATION.md)，记录文件职责、运行命令、结果路径与下一轮任务。当前版本是理想认证事件驱动的数值协议内核，采用抽象安装、贡献与退役通知。移动腐蚀检查记录每个共享周期的累计暴露预算；隐私结论仍依赖真实密码学和清除条件。下一轮将同一双实例流程接到真实交接和可验证开启，再接实际本地训练。
