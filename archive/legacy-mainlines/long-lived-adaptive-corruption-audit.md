# 长期移动自适应腐化下的异步安全聚合：模型与可行性审计

> 状态：研究主线候选，尚未形成已证明结果  
> 日期：2026-09-10  
> 当前收敛题目：`When Recovery Defeats Erasure: Privacy Finality for Long-Lived Asynchronous Secure Aggregation`

## 0. 执行结论

这条线可以开展，但不能直接声称“完全异步下抵抗无限快的 continuous-mobile adversary”。只限制任意时刻最多腐化 `t` 个节点，而不限制同一秘密存活期间的累计腐化，敌手可以依次读取 `t+1` 个份额；这在信息论上已经足以破坏阈值隐私。

当前值得推进的论文问题是：

> 在完全异步网络中，长期运行的聚合委员会可跨会话被移动、自适应地腐化，敌手最终可以访问所有委员会节点；能否利用安全聚合秘密“按会话产生、聚合后消费并擦除”的生命周期，在没有全局 epoch、没有永久共享秘密的条件下，保证未来腐化不泄露已经完成会话的单个更新？

经 `B*` 联合分布检查，使用独立每会话密钥时，分享层安全性由标准 Shamir 线性平移直接给出，协议结构不足以形成主贡献。当前问题进一步收窄为：

> **委员会能否长期复用一个稳定公共加密键，让任意重叠、无全局顺序的 `sid` 在授权聚合解密后被独立穿孔；随后即使敌手获得全体委员的当前密钥状态，也不能解密该 `sid` 的历史单客户端 ciphertext？**

仅把目标改名为 puncturable threshold aggregation 仍不足以形成论文主线：DFPE 已覆盖交错标签撤销，epochless BTE 已覆盖批量阈值选择性解密。因此从本轮起，密码学原语降为实现载体，主线升级为：

新增全文复核进一步支持这个转向。LightBEAT 的 HIDP 穿孔对象是客户端公开的 punctured PRF key，委员会仍持有普通 threshold-ElGamal shares；其所谓 adaptive security 是自适应选择 punctured identity 的 ROM 原语安全，不是委员会自适应腐化。协议 `Combine` 输出批内每条明文，且全文明确采用 static committee corruption。Silent Setup 的 forward security 仍依赖周期 key update，post-compromise security 通过成员本地重采样并发布新 `pk/hint` 实现；它不保持本课题要求的稳定公共键，也不表达无序 `sid` 的独立退休。

### 0.1 投稿级主线：Privacy Finality

> **When Is an Aggregate Truly Final?** 在完全异步网络中，`CC_sid` 只终结了“哪个值被输出”；`PF_sid` 才终结了“哪些历史单项信息永远不可恢复”。研究目标是构造并刻画一种由异步委员会共同产生的 privacy-finality event，使未来移动腐化、主动刷新和任意迟到消息都不能复活已终结会话。

三个核心对象必须分离：

1. `CC_sid`：集合、权重和输出值的共识终结；
2. `PF_sid`：足够多节点完成原子折叠/擦除后的隐私终结；
3. `T_sid`：节点对已终结会话的单调 tombstone/capability state，保证 refresh/cure 不会把旧解密能力重新引入系统。

第一主定理候选不再局限于阈值计数。令 `Gamma_dec` 是允许解密访问集合族，`B_sid` 是退休前已被暴露并可永久保留旧能力的节点集合，`A_sid` 是完成有效 `CollapseErase(sid)` 的节点集合。未来全体当前状态暴露后仍不能解密旧单项，当且仅当：

```text
B_sid union (P - A_sid) not in Gamma_dec.
```

对 `q`-out-of-`n` 阈值访问结构，给定实际集合的精确条件是：

```text
|B_sid union (P - A_sid)| < q.
```

若只知道 `|B_sid|<=b_sid` 而不知道交集，最坏上界才是 `n-a+min(a,b_sid)`；在 `a>=b_sid` 时进一步化为 `n-a+b_sid`。

更强的统一表述是 **Robust-Hitting Theorem**。把 `Gamma_dec` 看成解密超图，`A_sid` 是退休集合，`b` 是会话生命周期内仍可保留旧能力的节点上界，则：

```text
PF(A_sid,b)  iff  for every D in Gamma_dec, |D intersection A_sid| > b.
```

等价形式是：

```text
for every B_sid with |B_sid|<=b,
B_sid union (P-A_sid) not in Gamma_dec.
```

证明：一个解密集合 `D` 能在退休后被敌手形成，当且仅当 `D intersection A_sid` 全部落入 `B_sid`。若该交集大小不超过 `b`，令 `B_sid=D intersection A_sid` 就得到匹配攻击；若所有交集都大于 `b`，任意大小至多 `b` 的暴露集合都无法覆盖它。定义 `H_b(Gamma_dec)` 为满足该条件的鲁棒横截族，并令 `tau_b(Gamma_dec)` 为其中最小 `A_sid` 大小。于是 `a>=tau_b` 是任何构造的必要下界；一般情形的充分条件是协议实际可产生的退休集合族 `Gamma_ret subseteq H_b(Gamma_dec)`，而不是单看集合大小。

对阈值访问结构 `Gamma_q`，有：

```text
tau_b(Gamma_q) = n - q + b + 1.
```

该定理把 N4 从一个 quorum 计数引理提升为访问结构上的鲁棒横截性；未来可以研究非阈值访问结构、加权委员会和动态退休访问结构，而不改变核心安全游戏。

其加权版本为：若节点权重是 `mu(i)`，敌手在一个 `sid` 生命周期内可保留旧能力的总权重不超过 `beta`，则要求每个 `D in Gamma_dec` 满足 `mu(D intersection A_sid)>beta`。这不是 WBTE 的 weighted threshold correctness：WBTE 权重描述批量解密时的服务器授权，而这里的权重描述退休集合对未来暴露的切断能力。

### 8.9.2 退休安全—异步活性夹逼

令 `Gamma_cert` 为协议可接受的退休证书集合族，`Gamma_live` 为在 Byzantine withholding 和消息延迟下可能成为响应者的集合族。只要证书形成只依赖确认集合，则 privacy-finality 的两个方向可分离为：

```text
Safety:  Gamma_cert subseteq H_b(Gamma_dec)
Liveness: for every L in Gamma_live,
          exists A in Gamma_cert such that A subseteq L
```

Safety 是鲁棒横截性；liveness 是每个可活跃响应集合都包含一个安全证书。对阈值访问结构和 `n-f` 个最坏响应者，选取精确大小 `a` 的证书时，二者分别给出 `a>=n-q+b+1` 和 `a<=n-f`；解密本身还要求 `q<=n-f`。这统一解释了 `b<=n-2f-1`，并说明一般访问结构不能只看证书大小，必须同时检查 `Gamma_cert` 的形状和 `Gamma_live` 的覆盖关系。

投稿级要求是把它提升为异步事件序列定理：`CC_sid`、`PF_sid`、Byzantine withholding、延迟消息和未来全体腐化必须同时出现在同一个可组合定义中。

第二主定理候选是 **no-resurrection theorem**：如果一个刷新/治愈消息可以在不携带 `T_sid` 的情况下被接收，且接收者无法区分该消息是在 `PF_sid` 之前还是之后生成，那么敌手可以延迟该消息并在未来恢复旧 `sid` capability。因而任何满足长期隐私的协议必须让 capability state 对退休集合单调增长，或明确放弃以下至少一个目标：无全局 epoch、落后节点恢复、未来全体状态暴露。

这比“前向安全加密”多出的核心问题是：前向安全只让时间状态单调；本课题要求**按任意 `sid` 单调、在不同节点局部历史不一致时仍可组合、且与主动刷新和异步恢复相容**。

现有工作的分离口径：

| 基线 | 已解决的对象 | 没有解决的对象 |
|---|---|---|
| Libert--Yung FSE threshold | 全局 period 的历史密文保护 | 无序 `sid` 退休、aggregate-only、异步 PF 证书 |
| Green--Miers PE / Derler et al. DFPE | 单接收者标签穿孔，后者支持交错 allow/deny | 阈值委员会、Byzantine quorum、聚合输出绑定、移动刷新 |
| BEAT-MEV / wBTE；Agarwal et al., IEEE S&P 2026, DOI `10.1109/SP63933.2026.00175`, ePrint `2025/2115` | 对公开池中任意选中批次逐条阈值解密；wBTE 支持服务器权重且通信不随总权重增长 | 静态按权重腐化、广播输入、固定索引/setup；不提供 aggregate-only 输出、per-`sid` 退休、长期移动腐化或退休后全体状态暴露 |
| LightBEAT | HIDP 将 BEAT-MEV 的 puncturable PRF setup 降至 `O(N log^2 N)`；用户公开 punctured key，委员会只聚合解密 `sum k_i` | full protocol 是 static corruption；`Combine` 逐条输出；没有委员会状态穿孔、cure/repair 或未来全体当前状态暴露 |
| Silent Setup STE | 无 DKG 的多委员会门限加密；可通过周期更新获得 FSE，并通过本地换键获得 PCS | FSE 仍是时间世代；PCS 改变成员 `pk/hint`；没有稳定键下的无序 `sid` 穿孔与 punctured-state recovery |
| VSSR | 异步 VSS 的可验证 share recovery；recovery polynomial 和 DPRF 支持从 `k` 个贡献恢复缺失份额 | 安全游戏对每个 commitment 累计限制少于 `k` 个 compromise/contribution/recovery 来源；不是长期 mobile/proactive security，且 proactive share recovery 明确留作 future work |
| DyCAPS / Shanrang / bDPSS | 异步或乐观异步的 epoch-mobile proactive refresh | per-`sid` 隐私终结、无复活刷新、aggregate-only |
| NFSA / OPA / Buffalo | 单服务器或异步 FL 的高效掩码聚合 | 长期移动委员会、未来全体状态暴露、可证明 PF 事件 |

明确的关闭条件：若 no-resurrection 只需把现有 DFPE 的 deny-list 原样复制到每个委员，且 `PF_sid` 只是普通 quorum 计数、整个跨会话证明是直接并行组合，则关闭密码学构造叙事，保留 frontier 下界作为短论文候选。

这个问题保留 SA 的核心约束：客户端 one-shot、只允许聚合密文解密、会话按 quorum 关闭；不再研究每会话重新生成完整密钥的直接方案。

正向结果必须建立在一个明确的最小放松上：对每个 coordinate generation interval，
敌手在当前代安装到下一次接受安装或 retirement barrier 之间累计暴露的节点不超过
隐私阈值；没有下一次 barrier 时，区间延伸到 retirement。本文称其为
`causal-generation-bounded mobile adversary`。它允许长期最终腐化所有节点，但
要求每个代际屏障前不能读完全部当前份额；若允许无限快轮换穿过屏障前的擦除窗口，
continuous-mobile 下的阈值隐私仍然不成立。

这个条件不是全局 epoch：generation 只绑定一个 coordinate 的状态安装、刷新和
退休事件，不要求不同 `sid` 或不同 coordinate 使用共同时钟。它是协议必须证明的
局部状态屏障，而不是把每个会话重新命名成同步 epoch。

论文的理论价值不能只来自这个新名字。最低贡献组合应当是：

1. 给出纯异步 SA 下腐化速度、状态生命周期、诚实客户端纳入和历史隐私之间的不可兼得边界；
2. 证明该边界与 Alexandru--Blum--Katz--Loss 的通用 PSS 不可能性有何联系、又为何不完全相同；
3. 给出稳定公钥、无序会话穿孔、只解密授权聚合密文的理想功能与协议，并证明 past-update forward privacy；
4. 证明所需放松接近必要，而不只是把“每 epoch 至多 `t`”改写成“每 session 至多 `t`”。

## 1. 研究对象与安全目标

### 1.1 系统对象

- 长期委员会 `P={P_1,...,P_n}`，首版取 `n=3f+1`，任意时刻最多 `f` 个主动 Byzantine 节点。
- 聚合会话由唯一标识 `sid` 区分；不同 `sid` 可任意重叠，没有全局同步 epoch。
- 每个客户端对一个 `sid` 至多提交一次更新，提交后可以永久离线。
- 每个会话只需要输出一个由协议确定集合 `S_sid` 上的线性聚合，不维护跨会话永久共享秘密。
- 网络完全异步：认证点对点消息最终送达，但敌手控制消息顺序和任意有限延迟。

### 1.2 首篇论文只保护什么

主要目标是保护长期委员会未来腐化之前已经完成的客户端更新：

```text
Past-update forward privacy:
在 sid 完成并执行规定擦除后，即使敌手在后续会话中最终腐化所有委员会节点，
其联合视图也只能得到允许泄漏的聚合值和公开元数据，不能恢复 sid 中任一受保护客户端的单个更新。
```

客户端腐化必须单独处理。若客户端长期保留旧更新或能从持久训练数据重新计算旧更新，那么未来腐化该客户端会直接得到该值，任何 SA 协议都无法阻止。因此首版采用以下二选一口径，并优先选择第一种：

- **主口径：** 移动腐化只作用于长期委员会；客户端腐化集合在每个会话内定义，已腐化客户端的输入不受保护。
- **增强口径：** 允许会话后腐化客户端，但只保护客户端已经擦除的会话更新与协议随机数，不保护其持久原始数据或可重计算信息。

不能笼统宣称“未来腐化所有客户端后仍保护其旧梯度”。

## 2. 四类敌手模型必须严格区分

令 `Corr(tau)` 是物理时刻 `tau` 正被敌手控制的委员会节点集合；令 `Read_i(sid)` 表示敌手在节点 `P_i` 擦除 `sid` 的敏感状态前读取过该状态。

| 模型 | 腐化预算 | 能否长期换人 | 是否依赖 epoch | 能否最终覆盖所有节点 | 本项目判断 |
|---|---|---|---|---|---|
| `adaptive-total` | 整次执行累计腐化节点并集至多 `t` | 否 | 否 | 否 | 近期 adaptive PVSS/threshold decryption 的典型口径 |
| `epoch-mobile` | 每个 epoch 内至多 `t_e`，下一 epoch 可换人 | 是 | 是 | 是 | DyCAPS、Shanrang、bDPSS 一类口径 |
| `continuous-mobile` | 任意时刻 `|Corr(tau)|<=t`，不限制轮换速度和累计读取 | 是 | 否 | 是 | 对持久阈值状态一般不可能；不能作为正向定理假设 |
| `causal-generation-bounded mobile` | 任意时刻主动 Byzantine 至多 `f`；每个 coordinate generation interval 的暴露集合至多 `t` | 是 | 否，只使用局部状态屏障 | 是 | 当前候选模型 |

其中：

```text
E_sid = { i in [n] : Read_i(sid) happens before P_i erases st_i[sid] }.
```

建议首版取 `t=f`，但在定义中分开：`f` 控制异步协议的正确性与活性，`t` 控制每个 generation interval 的状态暴露。敌手释放一个节点后仍永久保留已经读取的信息；节点恢复诚实时只能清理本地状态，不能让敌手遗忘。不同 interval 可以暴露不同节点。

### 2.1 这个模型比 epoch-mobile 强在哪里

- 会话没有统一开始和结束时刻，`sid_1`、`sid_2` 可以部分或完全重叠。
- 节点可在任意协议事件后被腐化，而不是只能在 epoch 开始选择集合。
- 不同会话可暴露完全不同的节点，长期并集可以是整个委员会。
- 安全证明必须按每个会话的敏感状态生命周期组合，而不能按全局 epoch 做归纳。

### 2.2 这个模型仍然放松了什么

- 它限制的是同一 generation interval 内的累计状态暴露，不只是同时腐化数；不同 interval 的暴露集合可以变化。
- 它需要真实的安全擦除或等价的历史密钥隔离；普通文件删除不够。
- 它不保证每个诚实客户端一定纳入输出；完全异步下，永久延迟和掉线不可区分。
- 若敌手能在某个 causal barrier 前轮换并读取超过 `t` 个相关节点，或读完该代全部当前份额，本模型条件已被违反，协议不声称隐私。

这组限制必须作为定理前提公开写出，不能藏在“mobile adversary”一词中。

## 3. 现有工作基线矩阵

| 工作 | 网络 | 腐化口径 | 擦除/历史隔离 | 时间结构 | 是否覆盖本问题 |
|---|---|---|---|---|---|
| Alexandru--Blum--Katz--Loss 2022 | 纯异步/变化网络 | proactive/mobile 审计 | 讨论旧消息与未来腐化 | epoch/catch-up | 给出通用异步 PSS 不可能性，是必须跨越的负面基线 |
| APSS / key refresh, ePrint 2022/1586 | 完全异步 | 版本主体含静态/受限扩展 | 必须删除旧份额；擦除与活性耦合 | refresh/termination 机制 | 覆盖异步刷新组件，不覆盖无全局 epoch 的 SA 会话隐私 |
| Shanrang, ePrint 2022/164 | 完全异步 | CHURP 式 epoch-mobile | 依赖周期刷新与 epoch 状态 | 本地 epoch/handoff | 维护永久秘密；不是 session-lifetime 模型 |
| DyCAPS | 完全异步 | 每 epoch 自适应至多 `t_e<n_e/3`；腐化节点保持到 epoch 结束 | 旧 epoch 擦除、forward-secure private channels | local-event epoch/handoff | 强基线，但不允许 epoch 内连续换人 |
| bDPSS, ePrint 2025/880 / S&P 2026 | 最坏异步、乐观同步 | 文中称 static PPT；每 epoch 开始腐化至多 `t_e` | 新 epoch 腐化不能读取旧 epoch 私密状态 | local clock + epoch handoff | 已覆盖批量随机秘密的 epoch 刷新；不能把 mask 直接套用后声称创新 |
| Flamingo | 多轮 SA | 静态恶意腐化，集合跨所有轮次不变 | 非长期移动模型 | aggregation rounds | 不覆盖未来腐化全体解密者 |
| Aion | 聚合器间部分同步，客户端通信异步 | 每轮给出恶意集合上限，但没有长期 corruption interface | 未形式化历史状态擦除 | rounds + BFT | 不是完全异步，也未证明长期 mobile security |
| Bacho--Chen--Loss 2026 aggregatable PVSS | 同步或异步均可 | 单次执行累计至多 `t` 个 adaptive corruptions | 不需要安全擦除 | 无 proactive 生命周期 | 可作为会话内 PVSS 组件，不提供跨会话 mobile 定理 |
| Das--Ren--Yang 2025 threshold ElGamal | 原语安全游戏 | 单次游戏累计至多 `t` 个 adaptive corruptions | 非 proactive/mobile | 单次密钥执行 | 可作为会话内阈值解密组件 |
| Shoup 2026 adaptive threshold decryption | 原语安全游戏 | adaptive corruption；多 epoch proactive 仅讨论 | proactive 扩展预期需要擦除 | 建议周期 epoch | 明确未给多 epoch 的完整证明 |

基线审计的直接结论是：

1. “adaptive secure”不等于“mobile secure”；前者通常在整个游戏中累计最多腐化 `t` 个节点。
2. “fully asynchronous DPSS”不等于“无 epoch continuous-mobile”；现有方案用 epoch、handoff、旧状态隔离或额外信道条件限制攻击。
3. “multi-round SA”不等于“未来腐化安全”；Flamingo 的腐化集合跨轮固定，Aion 也没有给出状态暴露与擦除接口。

## 4. ABKL 延迟消息攻击：适用部分与 SA 特有出口

### 4.1 攻击为何击中通用 PSS

ABKL 的核心调度不是简单“网络很慢”，而是把旧消息变成未来腐化后的额外份额：

1. 敌手延迟发往某个诚实节点 `P_1` 的 epoch-1 消息，使其停留在旧 epoch；
2. 其余节点继续进入后续 epoch；
3. 敌手在未来腐化 `P_1`，再交付旧消息并读取其可恢复状态；
4. 这些跨 epoch 信息与敌手已有份额组合，破坏新 epoch 的隐私；
5. 若协议拒绝处理旧 epoch 消息，落后节点又无法追赶，破坏活性。

原文进一步指出，需要某种 asynchronous forward-secure channel 或外部 clock tick 才能同时维护隐私与追赶；普通 forward-secure encryption 本身并不自动解决异步密钥推进问题。

### 4.2 攻击为何也能击中朴素长期 SA

以下任一设计都会重新落入同一陷阱：

- 所有会话复用长期阈值解密密钥；敌手归档客户端 ciphertext，未来依次腐化节点后解密旧份额。
- 节点为保证所有迟到客户端纳入而永久保留每客户端份额、mask 或旧会话解密密钥。
- 用通用 DPSS 持续刷新一个永久 mask master key，并要求落后节点以后追上当前状态。
- 只在协议描述里写“轮次结束后擦除”，却没有定义节点何时能在纯异步网络中安全判定结束。

### 4.3 SA 可能避开的结构性原因

SA 与通用 PSS 的关键差异不是“SA 更简单”，而是秘密用途不同：

- PSS 要长期保存同一个秘密，落后节点最终仍需获得当前份额。
- SA 的单客户端份额和 mask 只为一个 `sid` 的一个聚合值服务；聚合份额形成后，单输入份额没有继续存在的功能必要。
- SA 可以由 ACS/异步一致性机制确定一个 quorum 输入集合，并排除尚未完成提交的客户端。
- 节点得到已认证的会话描述符后，可以先把所有单输入份额折叠为一个聚合份额，再立即擦除单输入状态；随后只释放聚合份额。

因此候选出口是 `quorum inclusion + aggregate-then-erase + session key isolation`，而不是让每个落后节点追赶一个永久秘密。但这个出口不免费：未收到终结描述符的落后节点仍可能保留敏感状态，因此正向定理仍需要 `|E_sid|<=t`，或另一个能替代该条件的可验证擦除/腐化速率机制。

## 5. 不可能性结果 `v0`

本节已把事件模型、定理陈述和攻击执行写到 proof-sketch 级别；尚未完成 UC/游戏化证明。

### 5.1 异步事件模型

一次执行是事件序列 `pi=(e_1,e_2,...)`。敌手选择所有事件的交错顺序，但公平执行最终调度每个持续诚实节点，并最终交付诚实方之间已经发送的消息。

允许事件：

```text
InvokeSubmit(C_u, sid, x_u)  客户端本地调用提交
Send/Deliver(m, P_i)         发送或交付消息
Step(P_i)                    委员执行一个本地协议步骤
Corrupt(P_i)                 读取全部未擦除状态、控制 P_i，并可删除/篡改状态
Release(P_i)                 敌手停止主动控制；节点状态仍不自动可信
Cure(P_i)                    从认证代码和公开转录重置，擦除残留秘密状态
Erase(P_i, sid, label)       不可逆删除指定会话状态
Close(P_i, sid, D_sid)       接受不可回滚输入集合
Output(P_i, sid, D_sid, y)   输出聚合结果
```

`Corrupt(P_i)` 是调度器事件，不消耗网络轮次。若模型没有额外规定，敌手可以在两个诚实 `Step` 之间安排多个 `Corrupt/Release` 对。`Release` 只改变当前控制集合；若要把节点重新计为诚实，必须执行 `Cure`。

首版采用保守恢复语义：`Cure(P_i)` 后，节点不追赶正在进行或已经关闭会话的私密状态，只能验证公开终结证书并以新临时密钥加入未来会话。对某个正在进行的 `sid`，被腐化且尚未发布有效聚合份额的节点继续按该会话故障节点计数。这样避免假设一个被篡改节点能神谕式恢复旧份额，也避免重新引入通用 PSS 的 catch-up 要求。

移动腐化还带来可用性约束：敌手可在腐化时删除份额。若同一 `sid` 在产生足够输出份额前被依次腐化的节点数没有累计上限，敌手可以逐个销毁所有会话状态，即使任意时刻只控制一个节点。因此 `|E_sid|<=t` 不仅是隐私条件，也限制会话完成前的累计状态破坏；首版需证明剩余 `n-t` 个节点足以关闭并输出。

对会话 `sid`，节点 `P_i` 的敏感状态 `Sens_i(sid)` 包含：

- 客户端明文份额或可与公开转录组合恢复份额的随机数；
- 能解密归档会话 ciphertext 的长期或临时秘密密钥；
- 聚合前仍能分离出单客户端贡献的中间状态；
- 其他超出允许泄漏 `L_sid` 的会话状态。

只编码已授权输出 `y_sid` 的最终聚合份额不计入敏感状态，但必须证明其分布可由 `L_sid` 模拟，不能靠命名排除。

定义实际暴露集合：

```text
E_sid(pi) = { i : Corrupt(P_i) 发生时 Sens_i(sid) 非空 }.
```

本段的 `session-lifetime-bounded mobile` 只保留为历史保守定义：它要求满足 `|E_sid(pi)|<=t` 的执行。当前模型改用 coordinate-local causal generation interval；纯异步协议仍无法阻止敌手在 barrier 前连续腐化多个节点，因此 interval 上界必须作为定理执行条件公开写出。

### 5.2 隐私实验

至少选择两个受保护客户端 `C_u,C_v`。挑战输入向量 `X^0,X^1` 满足：

```text
x_u^0 != x_u^1,
x_u^0 + x_v^0 = x_u^1 + x_v^1,
其他输入相同，且 L_sid(X^0) = L_sid(X^1).
```

敌手选择挑战位 `b` 对应执行后，获得公开转录、腐化客户端输入、所有腐化时未擦除状态、授权描述符和输出。若其区分 `b` 的优势不可忽略，则协议不满足 single-input privacy；会话完成后的新腐化仍提高该优势时，不满足 past-update forward privacy。

### 5.3 N1：历史密钥暴露屏障

**定理候选 N1。** 设会话完成后的公开转录为 `T_sid`。若存在节点集合 `Q`，使 `|Q|` 达到输入分享的重构阈值，且未来腐化每个 `P_i in Q` 所得状态与 `T_sid` 可恢复该节点关于目标客户端的有效份额，则任何允许敌手最终腐化 `Q` 的协议都不满足 past-update forward privacy。

**攻击执行。** 敌手在会话期间只归档 ciphertext，不必超过在线腐化阈值；会话输出后依次腐化 `Q`，取得长期密钥、旧会话密钥或未擦除份额；从 `T_sid` 恢复足够份额并重构 `x_u^b`，从而区分保持相同聚合值的 `X^0,X^1`。

**作用。** N1 证明安全擦除、历史密钥隔离、可信不可导出状态三者至少需要一个。普通“未来换密钥”不够；旧密钥若仍可从未来状态恢复，攻击不变。

### 5.4 N2：即时移动腐化屏障

令 `q` 为恢复某个受保护输入所需的最少兼容节点状态数；Shamir `(t+1)`-out-of-`n` 分享中 `q=t+1`。

**定理 N2（proof sketch）。** 若存在可达配置 `gamma`，其中 `q` 个不同节点同时持有关于 `x_u` 的未擦除兼容敏感状态；腐化返回完整当前状态；安全模型只限制任意时刻 `|Corr|<=b`，其中 `b>=1`，但不限制累计腐化或腐化事件速度，则协议不能实现 single-input privacy。

攻击轨迹：

| 步骤 | 调度事件 | 当前腐化数 | 敌手新增视图 |
|---|---|---:|---|
| 0 | 调度协议到达 `gamma`，暂停诚实 `Step` | 0 | 公开转录 |
| 1 | `Corrupt(P_1)`，读取 `Sens_1(sid)` | 1 | 第 1 个兼容状态 |
| 2 | `Release(P_1)`；是否随后 `Cure` 不影响敌手既有视图 | 0 | 保留第 1 个状态副本 |
| 3 | 对 `P_2,...,P_q` 重复腐化与释放 | 始终不超过 1 | 累计 `q` 个状态 |
| 4 | 恢复 `x_u^b` 并区分挑战位 | 0 | 隐私被破坏 |

整个攻击满足 `|Corr|<=1<=b`。它不需要旧 epoch、reshare、落后节点或跨会话消息，因此不是 ABKL 定理的直接实例。

**结论。** 以下条件至少需要一个：会话生命周期累计暴露上限、两个新腐化之间的最小驻留时间且诚实擦除能在其间执行、可信硬件不可导出状态、外部同步擦除事件。仅写“任意时刻至多 `t` 个腐化”不构成长期隐私模型。若腐化还能删除状态，同类串行调度也破坏会话可用性。

### 5.5 N3：完整诚实纳入与异步终结不可兼得

固定一个合法客户端 `C*`。最终输出必须包含输入集合及该集合的正确聚合，不能在不知道 `x_*` 时把 `C*` 空挂在集合中。

**定理 N3（deterministic）。** 在没有时钟或完美故障检测器的完全异步网络中，若允许 `C*` 在发送前掉线，则输出集合不可回滚的 SA 协议不能同时满足：

1. **Crash-tolerant termination：** `C*` 不发送时，其余前提满足的会话仍终结；
2. **Complete honest inclusion：** 诚实 `C*` 一旦调用 `InvokeSubmit`，就必须被最终集合纳入；
3. **Set finality：** `Close(sid,D_sid)` 后集合不因迟到消息改变。

成对执行：

| 执行 | `C*` 行为 | 敌手调度 | 委员会在前缀 `rho` 内所见 |
|---|---|---|---|
| `E_0` | 发送前掉线 | 公平调度其余各方 | 无 `C*` 消息 |
| `E_1` | 调用 `InvokeSubmit(C*,sid,x*)` 并发送 | 把全部 `C*` 消息延迟到 `rho` 之后 | 与 `E_0` 完全相同 |

由 crash-tolerant termination，`E_0` 存在有限前缀 `rho`，某正确委员关闭并输出不含 `C*` 的集合。确定性与不可区分前缀迫使 `E_1` 在 `rho` 作出相同输出，因此违反 complete honest inclusion；若迟到后改集合，则违反 set finality。

**随机化扩展。** 若 `E_0` 以概率 1 终结，则对任意 `epsilon>0`，存在有限前缀长度 `T`，使其在 `T` 前终结的概率至少为 `1-epsilon`。在 `E_1` 中把 `C*` 消息延迟到 `T` 后，两执行在 `T` 前分布相同，因此协议以至少 `1-epsilon` 的概率排除诚实 `C*`。故不能同时以压倒性概率满足三项性质。

**对长期隐私的推论。** past-update forward privacy 需要不可回滚关闭点，节点才能把单输入状态折叠并擦除。N3 表明：掉线容忍场景必须采用 quorum inclusion、明确截止事件或额外故障检测假设。N2 限制状态暴露；N3 限制输出语义，二者不是同一定理。

### 5.6 与 ABKL 的严格关系

| 维度 | ABKL Theorem 6 | N2 | N3 |
|---|---|---|---|
| 被保护对象 | 跨 epoch 永久不变的秘密 | 单个 SA 会话输入 | 会话输入集合与终结 |
| 攻击资源 | 旧 epoch 消息 + 未来 epoch 腐化 | 同一配置内串行状态读取 | 掉线/延迟不可区分 |
| 是否需要 reshare | 是 | 否 | 否 |
| 破坏性质 | privacy 或 catch-up liveness | single-input privacy | termination、inclusion、finality 三者之一 |
| SA 可用出口 | 不适用：秘密必须继续存在 | 只能增加暴露限制或硬件/时间假设 | quorum inclusion 后聚合并擦除 |

ABKL 说明永久秘密的纯异步 proactive refresh 存在追赶障碍。N2 更基础：即使完全没有 epoch 和 refresh，只要同一会话状态允许即时串行读取，隐私已经失败。N3 则利用 SA 特有的客户端提交和集合关闭语义，不是 PSS 结论的改写。

### 5.7 当前发表判断

N1、N2 是必要模型审计，但单独过小。N3 是严格的异步集合终结引理，也接近经典 crash/delay 不可区分论证。三者目前不足以单独支撑顶会论文。

下一项必须形成真正主定理：

> **Exposure--Finalization Frontier：** 刻画何种可验证关闭证据允许委员把每客户端状态不可逆降维为只泄漏授权聚合的状态；证明关闭前的移动暴露下界，并给出关闭后即使未来腐化全体委员仍安全的匹配构造，支持任意重叠 `sid`。

若该结果退化为“假设 `|E_sid|<=t`，然后每会话独立运行已有 VSS/ACS”，主线关闭。若重叠会话下的自适应模拟、迟到 ciphertext 处理或状态降维需要新的证明技术，则继续构造。

## 6. 理想功能 `F_LL-SA` `v0.1`

### 6.1 会话状态

功能为每个 `sid` 维护：

```text
Sigma_sid = (phase, P, rule, Inputs, D, CC, y, RC,
             life[1..n], exposed, corrupted_clients)

phase in {COLLECTING, CLOSED, RELEASED}
life[i] in {EMPTY, RAW, COLLAPSED, PUBLISHED, CURED}
```

规范化描述符与证书：

```text
D_sid = (sid, committee, model_id, inclusion_rule,
         [(client_id, input_commitment, weight)]_canonical,
         recipient)

CC_sid = CloseCertificate(sid, digest(D_sid))
RC_sid = ReleaseCertificate(sid, digest(D_sid), commitment(y))
```

`CC_sid` 必须满足唯一性：同一 `sid` 不存在两个可由正确节点接受且绑定不同 `D` 的证书。证书可由 ACS/MVBA 决定记录实例化，不能只假设若干普通签名在未来密钥全部泄漏后仍永久不可伪造。

### 6.2 功能接口

```text
Start(sid, P, rule, f, t)
Submit(sid, C_u, x_u, metadata)
Close(sid, D_sid, CC_sid)
CollapseErase(sid, P_i)
Publish(sid, P_i, z_i, proof_i)
Release(sid, y, RC_sid)
Corrupt(P_i)
ReleaseControl(P_i)
Cure(P_i)
```

- `Start`：创建唯一 `sid`，公开委员会、策略和阈值。
- `Submit`：仅在 `COLLECTING` 接受客户端首次提交；泄漏客户端标识、承诺、权重和长度，不泄漏 `x_u`。
- `Close`：仅接受规范化 `D_sid`、有效 `CC_sid`、满足 `rule` 的已提交输入集合；第一次成功后设置 `phase=CLOSED`，后续不同 `D` 永久拒绝。
- `CollapseErase`：仅在节点已接受 `CC_sid` 且持有 `D_sid` 所需有效份额时执行；把 `life[i]` 从 `RAW` 原子变为 `COLLAPSED`。
- `Publish`：发布绑定 `D_sid` 的可验证聚合份额后设置 `life[i]=PUBLISHED`。
- `Release`：足够有效聚合份额唯一确定 `y` 后输出一次；重复调用返回同一记录。
- `Cure`：清空全部未公开会话状态；节点不能恢复当前或历史 `sid` 的私密状态，只能加入未来会话。

### 6.3 原子状态降维

对已关闭会话，正确节点执行一个腐化粒度上的原子转换：

```text
CollapseErase_i(sid, D_sid):
    require VerifyClose(CC_sid, sid, D_sid) = 1
    require every selected client share is locally valid
    z_i = sum_{u in S_sid} w_u * share_i(x_u)
    proof_i = ProveAggregateShare(sid, D_sid, i, z_i)
    persist (sid, digest(D_sid), z_i, proof_i)
    erase all per-client shares, session decryption keys,
          session authentication secrets no longer needed,
          proof randomness, plaintext buffers
```

若腐化可发生在上述赋值与擦除之间，敌手仍可读取原始份额；因此正向定理必须明确采用原子本地步骤或把中途腐化计入 `E_sid`。`COLLAPSED/PUBLISHED` 状态只有在证明可由允许泄漏模拟后才不计入 `Sens_i(sid)`。

### 6.4 腐化返回值

`Corrupt(P_i)` 总是泄漏长期身份状态和所有未擦除会话状态。对目标 `sid`：

| `life[i]` | 腐化可见内容 | 是否计入 `E_sid` |
|---|---|---|
| `EMPTY` | 公开元数据 | 否 |
| `RAW` | 单输入份额、会话解密/认证秘密、缓冲区 | 是 |
| `COLLAPSED` | `z_i`、证明状态、公开元数据 | 条件性否；需模拟证明 |
| `PUBLISHED` | 已公开聚合份额与证书 | 否 |
| `CURED` | 公开转录、新会话状态 | 否 |

未来腐化全部委员时，普通长期签名密钥也会泄漏。若安全目标包含“历史证书永久可验证且不可产生冲突证书”，必须增加以下之一：前向安全签名、每会话认证密钥并在关闭后擦除、外部不可回滚日志、理想认证信道。否则首版只能保证会话执行期间的 agreement 与完成会话的输入保密，不能保证未来全体腐化后的公开审计唯一性。

### 6.5 安全与活性条件

- **Admissibility：** 每个 `sid` 满足 `|E_sid|<=t`，任意时刻主动控制节点数至多 `f`。
- **Unknown-input floor：** 每个输出至少含两个对敌手未知且权重非零的受保护输入；否则输出本身恢复单输入。
- **Agreement/validity：** 正确节点只接受唯一 `D_sid` 及其精确聚合。
- **Session privacy：** 同允许泄漏输入向量的执行不可区分。
- **Past-update forward privacy：** 所有正确节点完成 `CollapseErase` 后，未来腐化不增加单输入信息。
- **Conditional output delivery：** 最多 `t` 个节点在发布前被暴露、删除或篡改状态时，剩余 `n-t` 个节点仍足以形成关闭证据和至少 `t+1` 个有效聚合份额。
- **Explicit exclusion：** 功能不保证任意延迟客户端被纳入。

## 7. 最强黑盒基线 `B*`

### 7.1 假设组件

`B*` 故意使用最强合理组件，检验主线是否只是直接组合：

1. 每个 `sid` 独立的临时解密键和认证键；公钥清单在客户端提交前固定。
2. 支持自适应腐化的非交互 PVSS/AVSS，分享多项式次数为 `t`，承诺支持线性聚合和份额验证。
3. 异步可靠分发：客户端只发布一次 PVSS 转录，委员会负责后续传播；客户端可离线。
4. 带外部有效性的 ACS/MVBA，输出唯一入选集合及 `CC_sid`。
5. 擦除模型支持 `CollapseErase` 原子步骤。
6. 认证采用理想信道、前向安全认证或不可回滚会话公钥注册；普通可长期伪造的签名不够。

2026 aggregatable PVSS 只提供单次执行 adaptive-total 安全，可作为第 2 项候选；它本身没有证明上述多会话、擦除和 mobile composition。Willow 已覆盖 one-shot/dynamic 客户端和 `min_n` 式排除，但其主要定理是 static active adversary。Aion 已采用“先 BFT 提交在线集合，再广播聚合 mask 份额，最后重构”的结构，但聚合器网络是部分同步。

### 7.2 消息流程

1. **Key manifest：** 委员会固定 `KM_sid={(pk_i,sid,apk_i,sid)}_i`；客户端拒绝未绑定 `sid` 的键。
2. **One-shot submit：** 客户端 `C_u` 生成次数 `t` 的分享多项式，发布加密份额、承诺和有效性证明 `tr_u,sid`，随后离线并擦除分享随机数。
3. **Availability：** 委员会验证并可靠传播 `tr_u,sid`；节点只为可恢复且承诺一致的转录标记 ready。
4. **Close：** ACS/MVBA 在 ready 转录上决定 `D_sid`，输出唯一 `CC_sid`；迟到客户端进入新会话，不能修改本会话集合。
5. **Collapse：** 节点收齐 `D_sid` 所需本地份额后执行原子 `CollapseErase`。
6. **Publish：** 节点可靠广播 `(z_i,proof_i,digest(D_sid))`。
7. **Release：** 任意 `t+1` 个有效聚合份额重构 `y`；收集方发布 `RC_sid`。为抵抗最多 `t` 个 withholding，系统等待最多 `n-t` 个正确贡献者中的任意 `t+1` 个。

### 7.3 条件安全论证

- PVSS/AVSS 绑定每个客户端输入与次数 `t` 的分享多项式。
- ACS/MVBA 唯一确定 `D_sid`，阻止不同集合的聚合份额混合。
- 在 `|E_sid|<=t` 下，敌手在降维前最多得到每个受保护输入的 `t` 个节点份额。
- `z_i` 是授权聚合多项式在点 `i` 的值；未来得到全部 `z_i` 只恢复已允许输出 `y`。
- 对保持相同 `y` 的两组受保护输入，可重新选择各输入分享多项式，使已暴露原始份额与聚合多项式联合分布一致；该重编程是正式模拟证明的核心义务。
- 会话键与 `sid` 域分离并擦除后，未来腐化不能解密归档客户端转录。

这不是完整证明。最关键缺口：单会话 adaptive PVSS 的 standalone 游戏是否支持带辅助输入、任意并发 `sid`、中途 `CollapseErase` 和未来全部密钥暴露。若不能黑盒调用，需要联合模拟；若已有 UC 组件直接覆盖，构造新颖性大幅下降。

### 7.4 复杂度基线

设入选客户端数 `m`，向量维度 `d`，委员会规模 `n`：

```text
client payload       = m * C_PVSS(n, d)               total
availability traffic = m * C_RBC(PVSS transcript)
close traffic        = C_ACS(m, n)
release traffic      = O(n * (d + proof_share))
pre-close state      = O(m * d) field elements / committee node
post-collapse state  = O(d) field elements / committee node
```

Aggregatable PVSS 可压缩证明或公共转录，不能消除每个委员取得与其对应私密份额所需的数据。`B*` 的主要结构收益是状态从 `O(m*d)` 降到 `O(d)`，不是通信自动与 `m` 无关。

### 7.5 覆盖审计与当前裁决

| 组件/性质 | 直接最近邻 | 是否可主张新颖 |
|---|---|---|
| one-shot、动态客户端、允许忽略迟到提交 | Willow/OPA | 否 |
| 先固定集合再释放聚合份额 | Aion、现有本地 validator | 否 |
| 异步集合一致与输入分享 | ACS/AVSS/Dumbo-MPC | 否 |
| 单次 adaptive PVSS/threshold decryption | 2025--2026 新原语 | 否 |
| epoch-mobile 永久秘密维护 | Shanrang/DyCAPS/bDPSS | 否；且模型不同 |
| 重叠会话、会话级擦除、未来全体腐化的联合模拟 | 当前未见直接覆盖 | 待证明，不得先宣称首次 |
| 无全局 epoch 的会话认证密钥隔离 | 当前未见直接覆盖 | 可能是必要组件，也可能需要额外假设 |

`B*` 在理想认证、原子擦除和可组合 adaptive PVSS 全部作为黑盒时几乎直接实现目标。当前结论：**协议结构本身不足以投稿。** 继续价值只可能来自以下至少一项：

1. 证明现有 standalone adaptive PVSS 无法直接组合，并给出新的多会话擦除模拟技术；
2. 在不依赖全局 epoch 的情况下实现可验证会话认证键隔离，同时避开 ABKL 的旧消息攻击；
3. 给出比 `|E_sid|<=t` 更可执行、且与异步活性匹配的移动腐化条件；
4. 证明 Exposure--Finalization 下界与 `B*` 达到的状态降维上界严格匹配。

若四项均失败，方向降为应用性增强，不再按顶会理论主线推进。

## 8. 联合分布检查：分享层可直接模拟

### 8.1 设定

考虑一个会话的 `h>=2` 个受保护客户端。客户端 `C_j` 使用独立随机次数 `t` 多项式：

```text
p_j(X) = x_j + sum_{k=1}^t a_{j,k} X^k,
a_{j,k} <-$ F.
```

公开权重 `w_j` 非零。关闭后的聚合多项式：

```text
g(X) = sum_{j=1}^h w_j p_j(X),
g(0) = y = sum_{j=1}^h w_j x_j.
```

敌手在 `CollapseErase` 前获得节点集合 `E` 上的任意客户端份额子集，且 `|E|<=t`；关闭后可以获得整个 `g`，因为全部聚合份额最终公开或在未来腐化中泄漏。

### 8.2 暴露保持平移引理

**Lemma L1（perfect coupling）。** 给定两组输入 `x=(x_1,...,x_h)` 与 `x'=(x'_1,...,x'_h)`，若：

```text
sum_j w_j x_j = sum_j w_j x'_j,
```

则敌手看到的 pre-close 暴露份额与完整 post-close 聚合多项式的联合分布完全相同。

令：

```text
delta_j = x'_j - x_j,
L_E(X) = product_{i in E} (X-i)/(-i).
```

由于所有分享点非零，`L_E(0)=1`；由于 `|E|<=t`，`deg(L_E)<=t`。对每个客户端定义：

```text
p'_j(X) = p_j(X) + delta_j * L_E(X).
```

得到：

1. `p'_j(0)=x'_j`；
2. 对每个暴露节点 `i in E`，`p'_j(i)=p_j(i)`；
3. `sum_j w_j p'_j(X)=g(X)+L_E(X)sum_j w_j delta_j=g(X)`；
4. 从 `{p_j}` 到 `{p'_j}` 是随机系数空间上的双射，因此保持均匀分布。

即使某节点只收到部分客户端份额，取所有实际暴露节点的并集 `E` 仍同时保持全部已见份额。该证明还允许敌手获得所有 `g(i)`，不只允许其获得最终常数项 `y`。

### 8.3 自适应与重叠会话

对自适应腐化，按两执行使用相同敌手随机带并耦合公开转录。每次腐化返回的已见份额在上述映射下逐值相同，敌手因此选择相同下一事件；归纳到会话关闭后，完整视图相同。

对任意重叠会话 `sid_1,...,sid_r`，若每个会话使用独立分享随机数且分别满足 `|E_sid|<=t`，可对每个 `sid` 独立应用 `L_{E_sid}`。消息任意交错不改变乘积双射。该结论不覆盖同一客户端秘密或分享随机数跨会话复用；复用会引入额外线性关系，首版协议禁止。

### 8.4 紧性

当某会话 `|E|>=t+1` 时，不存在次数不超过 `t`、在全部 `E` 上为零且在零点取值 1 的多项式。敌手也可直接从 `t+1` 个份额恢复 `p_j(0)`。因此 L1 的 `|E|<=t` 与 N2 的攻击阈值精确衔接。

### 8.5 裁决

分享层的 Exposure--Finalization Frontier 已退化为标准 Shamir 隐私及线性同态：

```text
pre-close <= t 个节点暴露  +  post-close 任意聚合份额暴露
                         => 只泄漏授权聚合。
```

该引理适合作为协议证明中的技术引理，不足以成为论文主定理。重叠会话在独立随机数下也是直接乘积组合。由此关闭“状态降维本身需要新代数证明技术”的叙事。

剩余未决点缩减为密码学组合与密钥生命周期：

1. adaptive PVSS 的 ciphertext、NIZK 和腐化随机带能否实现 L1 对应的在线重编程；
2. 会话认证/解密键如何在无全局 epoch 下注册、擦除并抵抗未来身份密钥泄漏；
3. 是否存在比每会话重新生成全部键更低成本的 post-compromise secure 机制。

若第 1 项由已有 adaptive PVSS 证明直接给出，第 2 项只能靠理想信道或现有 forward-secure 签名，第 3 项无新结果，则当前主线不具备顶会理论新颖性。

### 8.6 新增强基线：forward-secure 与 puncturable encryption

#### Libert--Yung 2012

*Adaptively Secure Forward-Secure Non-interactive Threshold Cryptosystems* 已提供稳定公钥、非交互阈值解密、可验证解密份额、非交互本地密钥更新和自适应腐化安全。其 forward security 明确保护过去 period：未来攻破达到阈值的服务器后，旧 period ciphertext 仍保密。

它没有直接覆盖当前候选，原因必须精确表述：

- 生命周期被划分为全局离散 `t=0,...,T-1`；`Encrypt`、`Share-Decrypt` 和 `Update` 都显式接收 period number。
- 安全游戏由单个全局 `Update` query 推进当前 period。
- 挑战 period 及此前累计取得的 key shares 少于解密阈值；这不是无限速 continuous-mobile。
- 密钥只能从 period `t` 单调更新到 `t+1`，不能让重叠会话 `sid_a`、`sid_b` 按任意顺序独立退休。
- 方案不提供 SA 所需的加法同态聚合接口。

因此，“稳定公钥 + forward-secure threshold decryption”不是新贡献；可能的新点只在 **unordered per-session retirement + homomorphic aggregate-only decryption**。

原文定位：`/tmp/libert-yung-forward-threshold.txt:177` 描述稳定公钥与非交互更新；`:530` 定义 `Setup/Update/Encrypt/Share-Decrypt/Combine`；`:586` 的全局 `Update` query 与 `:602` 的累计腐化约束给出模型边界。DOI：`10.1007/978-3-642-34704-7_1`。

#### Green--Miers 2015

*Forward Secure Asynchronous Messaging from Puncturable Encryption* 引入 puncturable encryption：接收者可撤销特定消息或 period 的解密能力，无需联系发送者或重新分发发送方材料。这直接说明“无序消息退休”已有单接收者原语。

当前仅核对 Crossref/OpenAlex 元数据与摘要，未取得可读全文；不能据此判断其全部自适应安全细节。已确认的差异只有：该工作面向单接收者异步消息，不是阈值委员会、可验证部分解密或同态聚合。DOI：`10.1109/SP.2015.26`。

#### 其他 puncturable 基线

- Susilo--Duong--Le--Pieprzyk 2020 给出从 delegatable fully key-homomorphic encryption 构造 puncturable encryption。这里的 fully key-homomorphic 指把带公开变量 `x` 的 ciphertext 转换到函数条件 `f(x)=y`，明文保持不变；它不是对 SA 明文向量执行加法/FHE。其标准接口只有 `KeyGen/Encrypt/Puncture/Decrypt`，安全游戏在穿孔后给出一次当前 key exposure，不提供阈值份额、可验证部分解密或聚合明文同态。原文：`/tmp/generic-puncturable-encryption-2020.txt:247`、`:278`、`:448`。DOI：`10.1007/978-3-030-59013-0_6`。
- Shen--Chi--Lin 2026 的 *Puncturable Fully Homomorphic Encryption Based on Bloom Filter* 把 key revocation/forward secrecy 加入 FHE。当前只核对正式摘要；摘要未给 threshold/mobile committee 口径。DOI：`10.7717/peerj-cs.3675`。

初轮 OpenAlex/Crossref 题名与摘要检索未发现同时满足“threshold + puncturable + homomorphic + adaptive corruption”的直接工作；这只是检索线索，不是不存在性证据，后续必须做 IACR、DBLP 和引用链核验。

#### wBTE 与 aggregate-only 的黑盒分离

Agarwal et al. 的 wBTE 原文定义 `Pi-BDec` 的输出为所选批次的全部明文 `{m_i}`，并在构造中用聚合 key `K=sum_i K_i` 加上每个公开 `K_i*` 逐项恢复这些消息。它与本课题的理想功能存在接口级分离：

```text
F_wBTE(batch) -> {m_i : i in batch}
F_agg-only(S,w) -> sum_i w_i*m_i
```

当批次至少包含两个输入时，后者的输出不能模拟前者的逐项输出。标准 SA 可以公开 masked update `y_i`，所以真正的分离是：把 `x_i` 作为 wBTE 明文会逐条泄露更新；把 mask seed `k_i` 作为 wBTE 明文并配合 `y_i=x_i+G(k_i)` 会逐条泄露所有去掩码材料。删除 `K_i*` 又破坏 wBTE 的逐项解密等式，因而不再是标准 wBTE 黑盒调用。因此 wBTE 可以作为效率和批量选择性解密的强基线，但不能直接作为 aggregate-only SA 的黑盒组件。

原文还给出一个对当前构造问题很重要的负面信号：将阈值同态加密直接替换进 key-homomorphic puncturable PRF 会产生 source-group/target-group 的类型不匹配；其修复需要把 PRF 评估、阈值解密密钥和 CRS 元素进行**非黑盒代数耦合**（`/tmp/wbte-eprint.txt:403-425`）。这说明“阈值化一个现成 puncturable PRF”不能作为当前问题的直接方案；但 wBTE 的目标仍是逐项恢复，而不是只恢复聚合 mask key。

### 8.7 基线修正：不需要对 `d` 维模型做 puncturable FHE

此前把最强简单基线写成“Shamir 分享整个更新，再向 `n` 个独立 puncturable PKE 接收者发送 `n` 份 `d` 维 ciphertext”，其客户端成本为 `Theta(n*d)`。这个基线过弱。

OPA 已明确采用更强的标准压缩：客户端只分享短种子 `k_u`，发送

```text
z_u = x_u + G(sid, k_u),
```

其中 `G` 是 leakage-resilient seed-homomorphic PRG 或 key-homomorphic PRF。委员只聚合 `k_u` 的短份额；服务器恢复 `K=sum_u k_u` 后计算 `G(sid,K)=sum_u G(sid,k_u)`，从 `sum_u z_u` 去除总 mask。OPA 原文在 `/home/yzc/flagg/extract_One-shot_Private_Aggregation_with_Single_Client_Interaction.txt:466` 定义 seed homomorphism，在 `:527` 描述按委员公钥加密辅助信息，在 `:541`--`:563` 明确从分享长 mask 改为分享短种子。其敌手是 static malicious，见 `:136`，因而不覆盖当前长期移动腐化目标。

Buffalo 也把 `d` 维更新与较短聚合键分开处理；其客户端通信为模型项加短键/委员会项，而非 `n*d`，见 `/home/yzc/flagg/Buffalo A Practical Secure Aggregation Protocol for Buffered Asynchronous Federated Learning.pdf_by_PaddleOCR.md:313`、`:400`、`:411`。因此当前候选不应把“避免 `n*d`”作为贡献。

修正后的最强简单基线 `B_seed` 为：

1. 每个委员独立运行一个稳定公钥 puncturable PKE；
2. 客户端 Shamir 分享短 mask key `k_u`，向 `n` 个委员各加密一个标量/短向量份额；
3. 客户端上传一个 `d` 维 masked update `z_u`；
4. 委员在 `CC_sid` 确定后只发布聚合 key share，随后独立穿孔 `sid`。

其每客户端通信是 `O(d+n*kappa)` 量级，而不是 `O(n*d)`；委员会敏感状态与工作量可与 `d` 无关。这个方案已给出稳定公钥、无序退休和长期全体腐化前向隐私的直接候选，代价是每客户端仍有 `n` 个短 ciphertext，且公开验证聚合 key share 需要额外证明。

### 8.8 当前密码学候选：紧凑无序穿孔阈值 mask-key 聚合

SA 层只需要加法同态地加密短 mask key，不需要 puncturable FHE。令 `q` 为解密门限，暂定原语接口：

```text
Setup(lambda, n, q) -> (PK, {SK_i}, {VK_i})
EncryptKey(PK, sid, k_u) -> ct_u
EvalAdd(sid, {ct_u}) -> ct_K
PartialDecrypt(SK_i, sid, CC_sid, ct_K) -> mu_i
VerifyShare(VK_i, sid, CC_sid, ct_K, mu_i) -> {0,1}
Combine(sid, ct_K, {mu_i}) -> K = sum_u k_u
Puncture(SK_i, sid) -> SK'_i
```

必需性质：

- **Stable public key：** 新会话不重新发布 `PK`，客户端只需一次获得公共键。
- **Unordered puncture：** `Puncture(sid_a)` 不要求 `sid_a`、`sid_b` 存在全局顺序，也不破坏未穿孔会话。
- **Aggregate-only authorization：** `CC_sid` 绑定唯一客户端集合、全部 `ct_u` 及其确定性聚合 `ct_K`；正确委员只为该 `ct_K` 生成份额。该性质是协议策略加可验证绑定，不是假设已腐化委员会遵守接口。
- **Threshold robustness：** 至少 `q` 个有效份额唯一解密，至多 `f` 个 Byzantine withholding 时仍可输出，因此 `q<=n-f`。
- **Adaptive pre-puncture security：** 目标 `sid` 的旧 key-share 状态累计暴露少于 `q` 个。
- **Post-puncture total exposure：** 足够正确委员穿孔后，敌手可以获得全体委员当前 `SK'_i`，仍不能解密该 `sid` 的历史单客户端 ciphertext。
- **Cross-session mobility：** 不同 `sid` 的 pre-puncture 腐化集合可以不同，长期并集覆盖全体委员。
- **Compact client path：** 每个客户端只产生一个短 key ciphertext；结合 mask 后总通信目标为 `O(d+kappa)`，而 `B_seed` 为 `O(d+n*kappa)`。

对 compact 单 ciphertext 候选，直接把现有 puncturable PKE 的 secret key 做 Shamir 分享不是一般黑盒变换。若 `Puncture` 对秘密状态是次数 `delta>1` 的非线性映射，节点本地对次数 `t` 的 Shamir 份额应用该映射，会把分享多项式次数提高到至多 `delta*t`；连续穿孔会继续增长，除非增加交互式 degree reduction/refresh。这个观察只否定 compact 的朴素 share-then-puncture，不是否定 `B_seed` 的独立 PE 组合，也不是一般不可能性定理。

### 8.9 `N4`：输出证书与安全退休证书之间的门限边界

`CC_sid` 只证明输入集合和输出已经确定；它不证明足够多节点已删除 `sid` 的旧解密能力。为此单独定义 `PC_sid`：节点只有在本地完成 `Puncture+Erase` 后才签署 puncture acknowledgment，收集 `a` 个不同节点的确认形成退休证书。这里不用 `RC_sid`，因为第 7 节已用该符号表示 release certificate。

令 `b_sid=|E_sid|` 表示在本地穿孔前已被敌手读取并可永久保留的不同旧份额数。它是会话生命周期累计暴露量，不是某一时刻的 Byzantine 数。已暴露节点即使后来恢复、真实穿孔或发送确认，也不能让敌手忘记旧副本；未暴露 Byzantine 节点还可以确认后拒绝擦除。因此最坏情况下，把所有可保留旧份额统一计入 `b_sid`。

**定理候选 N4（Puncture-quorum frontier）。** 令 `B_sid` 是执行结束时敌手仍拥有旧能力的节点集合；它包含被提前读取并保留旧份额的节点，也包含伪造确认但实际未擦除的 Byzantine 节点。若 `|B_sid|<=b_sid`，而 `PC_sid` 只携带 `a` 个不同节点的确认，则未来全体当前状态暴露后仍可形成旧解密能力的节点集合为：

```text
D_sid = B_sid union (P - A_sid)
|D_sid| = n - a + |A_sid intersection B_sid|
max |D_sid| = n - a + min(a,b_sid).
```

因此，对 `q`-out-of-`n` 阈值解密，**仅依赖退休确认数量的最坏情况条件**是：

```text
n - a + min(a,b_sid) < q.
```

**计数证明。** `P-A_sid` 中的节点尚未被证书约束；`A_sid intersection B_sid` 中的确认节点虽然签名确认，但旧能力仍在敌手手中。故可用能力恰为 `B_sid union (P-A_sid)`。在只知道 `|B_sid|<=b_sid` 时，敌手让 `B_sid` 尽量覆盖 `A_sid`，交集最大为 `min(a,b_sid)`，得到上界。反向攻击把暴露集合安排为该最大交集，并延迟未确认节点；若条件失败，就能凑出至少 `q` 份。

在有用区间 `a>=b_sid` 内，这才简化为旧式公式 `n-a+b_sid<q`。若 `b_sid>=a`，最坏情况下所有确认节点均已被敌手掌握旧能力，`|D_sid|=n`，普通确认签名不提供退休安全。

完全异步活性要求当前至多 `f` 个 Byzantine 节点全部沉默时仍能形成证书，故 `a<=n-f`。由于安全区间必须有 `a>=b_sid`，live retirement certification 必须满足

```text
n + b_sid - q + 1 <= a <= n - f,
a >= b_sid,
```

可行当且仅当 `q>=b_sid+f+1`。再结合解密抗 `f` 个 withholding 所需 `q<=n-f`，存在可行门限当且仅当

```text
b_sid <= n - 2f - 1.
```

在 `n=3f+1` 且采用当前首版暴露上限 `b_sid<=f` 时，最紧的唯一门限点是

```text
q = a = 2f+1 = n-f.
```

这给出一个比“重放/重复计数”更完整的理论叙事：**输出完成不等于历史隐私已经可公开确认；累计移动暴露、异步活性、解密门限、虚假擦除确认和未来全体腐化共同迫使一个精确 quorum。** 特别地，当 `b_sid=f` 时，常见 `q=f+1` 方案需要 `a=n`，可被一个沉默 Byzantine 永久阻断。若 `b_sid>f`，即使仍有 `b_sid<q` 因而穿孔前机密性尚未立即失效，`n=3f+1` 下也不存在同时满足解密活性和公开退休活性的 `q`。

该定理仍依赖理想认证、前向安全签名或不可回滚日志来防止未来身份密钥泄漏后伪造旧 `PC_sid`，并假设正确节点确认前已原子穿孔和擦除。

### 8.9.1 `NR`：退休必须是吸收态

旧版本的 NR 把“退休证书形成”误当成“每个被计入证书的节点都已退休”，因而不能直接从迟到消息推出 `PF` 破坏。正确对象是**可复活的退休集合**。

令 `A` 是 `PC_sid` 声称已经执行 `Puncture+Erase` 的集合，令 `R subseteq A` 是在退休后仍可能通过延迟旧消息重新安装 `sid` 能力的节点集合。对一次给定的复活轨迹，未来状态暴露后的有效旧能力集合为

```text
B_eff = B union R union (P - A),
```

其中 `B` 是退休前已经被敌手保存旧能力的节点集合。对固定的 `B`，`PF_sid` 的精确条件不是只对原始 `A` 应用 Robust-Hitting，而是

```text
for every D in Gamma_dec,
D is not a subset of B union R union (P - A).
```

若敌手可以任意放置至多 `b` 个暴露节点，其最坏情况计数形式为
`|D intersection (A - R)| > b`。

特别地，若未来可以暴露所有当前状态，任何非空 `R` 都会使相应节点重新进入可用集合；只要存在某个 `D` 满足 `|D intersection (A-R)| <= b`，就能组合 `R` 与至多 `b` 个旧能力节点恢复 `D`。因此 `PF` 不是一次性证书属性，而是要求 `A` 对所有迟到消息执行保持不变：退休必须是一个**吸收态**。

### 8.9.2 `NR` 事件序列定理

**NR-Event Theorem（条件版）。** 假设存在节点 `p` 和退休前生成的合法旧状态消息 `m_old`，满足：

1. `p in A`，即 `p` 已被 `PC_sid` 计入并执行了退休操作；
2. `m_old` 的认证在退休后仍有效，且不携带或不受本地单调 `T_p >= Retired(sid,h)` 支配；
3. 在收到 `m_old` 后，状态机可以重新安装 `sid` 的旧能力或旧解密份额。

则存在完全异步执行使 `p in R`。若进一步存在 `D in Gamma_dec` 使 `|D intersection (A-R)| <= b`，则该执行违反 `PF_sid`。

**证明。** 在 `E_before` 中于退休事件之前交付 `m_old`，它必须被接受，否则一个尚未退休会话的合法恢复被拒绝。在 `E_after` 中先让 `p` 完成退休，再延迟交付同一 `m_old`；由于消息认证内容相同且没有支配它的单调状态，接收状态机仍接受它，故 `p in R`。此时 `D intersection (A-R)` 中至多有 `b` 个节点，敌手保留这些节点的旧能力，并从 `P-A` 与 `R` 暴露当前状态，得到 `D` 的全部能力，矛盾。

该定理不声称“所有异步刷新都不可能”，也不声称任意单节点复活都会立即破坏 `PF`。它只给出精确的匹配条件：复活必须削弱某个授权解密集合的退休横截性。普通 forward-secure 时间周期和普通签名不能替代这个 per-`sid` 的支配关系；它们最多证明消息曾经合法，不能证明消息已经被退休状态废止。

### 8.9.3 匹配充分条件

为每个节点维护单调 `T_i`，并令状态转移只接受 `(s,T)` 且满足 `T_i <= T`。若 `T` 包含 `Retired(sid,h)`，转移必须删除 `sid` 的旧能力；此后任何消息都不能在更高或相等的 `T_i` 上重新引入该 capability，则所有延迟旧消息都有 `R=emptyset`，原来的 Robust-Hitting 条件继续成立。

这个充分条件不要求全局 epoch，但要求 per-`sid` tombstone 能被验证并随恢复状态传播。未决的真正问题是：在 `Gamma_live` 下，落后节点能否获得足以验证 `T` 的证书，以及传播 tombstone 的状态和通信成本是否低于重新运行全套 DKG。若协议只把 DFPE deny-list 原样复制到每个委员，NR 本身不构成密码学构造贡献；价值应转向“吸收态退休”与异步 quorum/liveness 的联合定理。

### 8.9.4 `B_seed` 黑盒组合裁决（修正版）

此前把 `B_seed` 误读成“对 punctured PE secret key 做 Shamir 分享”。实际基线可以避免这个问题：每个委员 `P_j` 持有独立 PE key；客户端把短 mask key `k_u` 做 Shamir 分享为 `s_{u,j}`，再分别用 `P_j` 的 PE 加密。委员在 `RAW` 状态解密入选客户端的 `s_{u,j}`、本地求和得到聚合分片，随后对这些 ciphertext 的 `sid`/消息标签执行 puncture 并擦除明文分片。

因此，在**不要求 cure 后恢复被穿孔 PE 状态**的模型中，`B_seed` 可以由已有组件直接组合：

| 目标接口 | 组合方式 | 裁决 |
|---|---|---|
| 只释放 `sum_u w_u*x_u`，不释放各 `x_u` 或各 `k_u` | 只公开各委员的聚合 Shamir 分片；重构后只输出 `K=sum_u w_u k_u` | 可由应用层 wrapper 实现，不需要 wBTE |
| 委员独立穿孔并保持门限聚合 | 每个委员使用自己的 PE key；Shamir 只作用于明文 mask 分片 | 可直接组合，避免 share-then-puncture |
| `CC_sid` 绑定唯一聚合上下文 | ACS、域分离、客户端承诺和聚合分片证明 | 需要组合证明，但不是明显新原语 |
| 退休后迟到消息不能恢复旧分片 | 本地 PE puncture + 原子擦除 | 在无状态恢复模型中可直接实现 |

这条裁决关闭了“`B_seed` 本身需要新的 aggregate-only threshold encryption”这一过强叙事。它仍然留下两个不同层次的问题：

1. `B_seed` 的客户端代价是 `O(d+n*kappa)`；把它压到 `O(d+kappa)` 才需要 locally share-compatible puncture 或新的 compact aggregate-only primitive。
2. 若长期移动模型要求被 `Cure` 的委员重新加入未来会话，就必须恢复其当前 PE 状态；任何恢复消息都必须携带支配 `T_i` 的 tombstone，否则 8.9.1--8.9.3 的 `R` 攻击重新出现。

所以当前主线应优先研究 **privacy-finality 与 cure/recovery 的不可兼得边界**，而不是把 `B_seed` 的基础聚合流程包装成新密码学构造。compact 原语只有在能同时解决客户端通信和状态恢复、且不退化为完整 DKG/MPC 时才值得继续。

### 8.9.5 `B_seed` 匹配构造（无状态恢复版本）

为确认 `Robust-Hitting` 不是只给下界，考虑如下基线。每个委员 `P_j` 独立生成 PE 密钥对 `(pk_j,sk_j^0)`；PE 支持对标签 `(sid,u)` 穿孔，并在穿孔后暴露当前 key。对每个客户端 `u`：

```text
k_u <-$ F
p_u(X) = k_u + sum_{r=1}^{q-1} a_{u,r} X^r
send z_u = x_u + G(sid,k_u)
send ct_{u,j} = PE.Enc(pk_j, p_u(j), tag=(sid,u)) for every j
```

`G` 满足加权 key homomorphism。ACS 输出 `S_sid` 和权重，之后每个有能力的委员 `P_j` 在 `RAW` 状态解密 `ct_{u,j}`，计算

```text
r_j = sum_{u in S_sid} w_u * p_u(j),
```

并发布绑定 `CC_sid` 的可验证聚合分片。收集 `q` 个有效 `r_j` 后重构 `K=sum_u w_u*k_u`，只输出

```text
y = sum_{u in S_sid} w_u*z_u - G(sid,K).
```

每个发布者随后对所有 `(sid,u)` 执行 PE puncture，原子擦除其明文分片和未穿孔状态，再签署 `PC_sid`。在 `n=3f+1`、`q=a=2f+1`、每个会话穿孔前最多暴露 `b=f` 个委员时，未来全体当前状态暴露至多得到 `P-A` 的 `f` 个未退休状态和 `B` 的 `f` 个旧分片；其并集大小至多 `2f<q`。一般访问结构版本正好由 Robust-Hitting 条件给出。

这个构造的安全证明只需要已有 PE 的逐服务器穿孔后安全、Shamir 线性隐私和 `G` 的 key homomorphism；它的缺点是每个客户端发送 `n` 个短 ciphertext，通信为 `O(d+n*kappa)`。因此它是 frontier 的匹配基线，不是新的 compact 原语。

该构造刻意不提供“丢失 `sk_j` 后从其他委员恢复当前 PE 状态”。若加入这一活性要求，恢复协议必须传输带 `T_j` 的当前状态；否则延迟的 pre-puncture key/state 消息会产生 `R`，并按 8.9.1--8.9.3 破坏 privacy finality。由此得到清晰分离：`B_seed` 匹配 privacy frontier；cure/recovery 是额外的状态机问题。

### 8.9.6 `Cure--Finality Trilemma`（历史直觉，已收紧）

考虑一个已穿孔委员 `P_j`：未来客户端仍使用稳定的 `pk_j`，`P_j` 被 `Cure` 后必须重新加入未来会话；网络允许旧恢复消息任意延迟，且敌手最终可暴露所有当前状态。早期直觉是：若协议不提供带单调 `T_j` 的状态恢复，则以下三项存在不可兼得张力：

1. `Cure` 后重新加入未来会话的活性；
2. 无全局 epoch 或每次恢复都重新生成密钥的稳定状态语义；
3. 已满足 `PF_sid` 的会话对所有迟到消息保持 no-resurrection。

证明直觉是事件序列的直接组合：放弃第 1 项时，丢失当前 PE 状态的委员不能继续服务；保留第 1、2 项而没有单调 `T_j` 时，8.9.2 的 `E_before/E_after` 调度可能产生 `R`，再由 Robust-Hitting 的匹配条件恢复旧解密集合；若保留第 1、3 项，则恢复消息必须携带并验证支配 tombstone，或者协议必须引入 epoch/rekey 作为新的因果边界。该段不是最终无条件不可能性定理；精确定理见第 12.2 节。

### 8.10 选择性目标会话安全游戏 `G_upm-sa^sel`

第一版先做 selective-`sid`，不追求自适应选择挑战会话；这里的 oracle 只是密码学安全实验接口，不恢复已停止的 adaptive-query/数据库研究线。

1. **Initialize：** 敌手先承诺目标 `sid*`；挑战者运行 `Setup(lambda,n,q)` 并给出 `PK,{VK_i}`。
2. **Concurrent prefix：** 敌手可启动、交错和退休任意其他 `sid`，并控制全部网络调度；各会话的穿孔顺序任意。
3. **Challenge inputs：** 敌手提交同一入选集合上的 `X^0,X^1`，要求腐化客户端输入、公开元数据和授权聚合完全相同，且 `sum X^0=sum X^1`。挑战者取随机位 `b`，为每个受保护客户端采样 `k_u`，返回 `z_u^b=x_u^b+G(sid*,k_u)` 与 `ct_u=EncryptKey(PK,sid*,k_u)`。
4. **Pre-retirement exposure：** 在各节点本地穿孔 `sid*` 前，`Corrupt(P_i)` 返回完整当前 key-share 与会话状态；已腐化节点可永久保留旧状态。原语机密性只要求 `b_sid<q`，但端到端公开退休活性进一步要求 `b_sid<=q-f-1`；在 `n=3f+1,q=2f+1` 时即 `b_sid<=f`。
5. **Authorized release：** `CC_sid*` 固定唯一集合和 `ct_K=EvalAdd({ct_u})`。敌手得到正确节点仅针对该 `ct_K` 发布的可验证部分解密份额及 `K=sum k_u`，从而得到共同聚合值，但不能查询单客户端 ciphertext 的诚实解密份额。
6. **Retirement：** 正确节点收到 `CC_sid*` 后原子执行 `Puncture+Erase` 再确认；形成满足 N4 的 `PC_sid*`。
7. **Total current-state exposure：** 挑战者允许敌手腐化全部节点并返回其当前状态；此前 Byzantine 保留的旧份额仍计入敌手视图。
8. **Guess：** 敌手输出 `b'`。若所有 admissibility 条件成立，则要求 `|Pr[b'=b]-1/2|` 可忽略。

这个游戏显式要求联合模拟 masked updates、授权聚合解密份额、少于 `q` 个旧份额和穿孔后的全部当前状态。单键 PE、单次 adaptive threshold decryption、静态 OPA/Willow 或全局 period forward security 都只覆盖其中一部分。

### 8.11 当前 go/no-go

继续的最小贡献包改为：

1. 把 `Robust-Hitting + 吸收态退休` 写成统一的事件序列 proof，固定 sufficiency、matching attack 和恢复活性的边界；
2. 形式化 `B_seed` 的匹配构造，并把 `Cure` 后稳定状态恢复单独作为接口/活性条件审计；
3. 只有 compact 单 ciphertext 能同时改善 `O(d+n*kappa)` 成本并支持可验证状态恢复时，才继续新原语；否则关闭协议构造叙事。

若第 1 项退化为纯计数、而第 2 项只是现成组件直接组合，则该主线不足顶会。若第 3 项只能通过通用 MPC、`n` 个独立 PE 或直接阈值化现有 PFHE 实现且没有新的局部更新/组合证明，也不作为主贡献。

## 9. 投稿级贡献门槛与关闭条件

### 9.1 达到顶会叙事所需的贡献包

- 一个精确敌手模型：主动 Byzantine 控制、状态暴露、释放/恢复、客户端腐化和擦除接口都可审计。
- 至少一个非平凡的不可兼得定理，最好把全体纳入、异步终结、腐化速度和 past privacy 统一起来。
- 一个与下界匹配的无全局 epoch 协议，支持重叠会话和长期最终全体委员会腐化。
- 一份组合安全证明，而不是逐组件宣称安全。
- 与 epoch-mobile DPSS、静态 multi-round SA、单次 adaptive PVSS/threshold decryption 的同口径比较。
- 实验只验证成本和攻击可达性：消息量、临时状态量、擦除延迟窗口、并发会话吞吐，不把实验当安全证明。

若完成上述组合，安全/隐私方向可考虑 IEEE S&P、USENIX Security、CCS；若主要贡献是紧的不可能性与密码学构造，可进一步按结果形态评估 CRYPTO/EUROCRYPT。当前阶段不能承诺投稿档次。

### 9.2 立即关闭或降级的条件

- 新模型最终等价于“每个会话独立运行一个已有静态/自适应 SA”，跨会话证明只是直接并行组合。
- 正向协议仍需要所有节点同步收到 epoch-close、可信全局时钟或现有 DPSS 的完整 handoff；此时“无全局 epoch”不成立。
- N3 只能复述 FLP 式延迟直觉，无法形成针对状态暴露和纳入语义的严格新定理。
- past privacy 只能通过假设所有相关节点在敌手到达前神谕式擦除来实现，且无法给出可审计的暴露条件。
- 已有工作在相同网络、相同 session concurrency、相同最终全体腐化和相同客户端离线语义下直接给出同一保证。
- 协议需要永久共享解密密钥，或未来腐化可以解密归档的客户端分享。

## 10. 四周执行计划

### 第 1 周：模型和负面结果

- 写出腐化、释放、恢复、擦除、消息延迟的事件语义。
- 完成 N1、N2 的游戏化陈述与最小攻击执行。
- 将 N3 写成 indistinguishability schedule，明确“诚实迟到”和“掉线”两条执行。
- 交付：`model-v0`、三条 theorem statement、每条一页 proof sketch。

### 第 2 周：最强基线和理想功能

- 用统一表格重写 DyCAPS、Shanrang、bDPSS、Flamingo、Aion 的网络与腐化接口。
- 明确 `F_LL-SA` 的 leakage、会话完成、客户端保护和输出交付。
- 构造最强黑盒基线：每会话 adaptive PVSS/AVSS + ACS + verifiable aggregate release。
- 交付：功能 `v0`、基线伪代码、是否只是直接组合的第一次裁决。

### 第 3 周：正向协议与组合证明

- 固定每会话临时密钥、聚合后擦除和迟到消息规则。
- 尝试证明 session privacy、past privacy 和 concurrent composition。
- 记录不能黑盒组合的模拟器状态，并判断是否形成真正的新技术问题。
- 交付：协议 `v0`、混合证明图、明确的 proof gap 列表。

### 第 4 周：成本与 go/no-go

- 只实现最小调度器：复现归档 ciphertext + 未来密钥泄漏、串行移动腐化、迟到诚实客户端三类攻击。
- 计算每会话临时密钥、PVSS 转录、委员会消息和擦除状态峰值。
- 与 epoch-mobile DPSS 和静态 multi-round SA 做同安全口径比较。
- 交付：继续/终止报告；只有理论边界或组合证明留下非平凡结果时才进入完整论文阶段。

## 11. 当前下一步

已完成：

- [x] `F_LL-SA v0.1`、状态生命周期和 `CollapseErase`；
- [x] `B*` 与 Shamir 联合分布模拟检查；
- [x] forward-secure / puncturable encryption 第一轮覆盖审计；
- [x] 用 OPA/Buffalo 修正短种子基线为 `O(d+n*kappa)`；
- [x] `N4` puncture-quorum frontier 的一般公式与选择性目标会话游戏。
- [x] 将 N4 提升为一般访问结构的 `Robust-Hitting Theorem`，并给出阈值结构的 `tau_b(Gamma_q)`。
- [x] 核对 wBTE 原文并完成其逐条解密接口与 aggregate-only SA 的黑盒分离。

下一份具体产物：

1. 将 `Robust-Hitting + 吸收态退休` 写成事件序列 proof，固定 sufficiency、matching attack 和恢复活性的边界；
2. 形式化 `B_seed` 的匹配构造，并审计 `Cure` 后稳定 PE 状态恢复的必要条件；
3. 只有 compact 单 ciphertext 能同时改善 `O(d+n*kappa)` 成本并支持可验证状态恢复时，才尝试新原语。

## 12. 本轮收紧：从三难直觉到可审稿命题

上一版 `Cure--Finality Trilemma` 的方向正确，但“不能同时成立”表述过强：只要允许每个节点维护带认证的单调 tombstone，三项可以同时成立。因此当前不把三难写成无条件 impossibility，而改写为下面两个命题。

### 12.1 模型：会话偏序上的 capability state

对每个节点 `P_i`，令 `F_i` 是它已经确认完成 `Puncture+Erase` 的会话集合，令 `kappa_i(sid)` 表示仍可解密该会话旧 ciphertext 的局部 capability。会话不是全局 epoch；两个 `sid` 可以并发完成、互不先后。网络可任意延迟已经生成的合法消息，但认证不会被伪造。

本节把三个接口条件分开：

- **Stable-key recovery：** `Cure(P_i)` 不改变 `pk_i`，并且在公开转录最终可达时，节点能重新服务未来会话；恢复消息的到达顺序不受保证。
- **No-resurrection：** 若 `sid in F_i`，则 `Cure` 后任何状态转移都不能重新安装 `kappa_i(sid)`。
- **Unfenced legacy acceptance：** 存在一个 `sid` 的合法旧消息 `m_old`，其认证仍依赖稳定 `pk_i`，且接收/恢复规则不检查一个支配 `sid` 终结的单调状态。

这里的“支配”是偏序意义，而不是时间戳：状态 `T'` 支配 `T`，当且仅当 `T'` 至少包含 `T` 已经确认的所有 `(sid, retirement)` 事实。单调状态可以是显式 tombstone，也可以是带证明的可合并 accumulator；不能把它限定为一个全局 epoch。

### 12.2 Causal-Fence Necessity Theorem

**定理（条件版）。** 在完全异步网络中，若协议满足 stable-key recovery 和 unfenced legacy acceptance，则存在一个调度使 no-resurrection 失败。等价地，任何同时满足 stable-key recovery 与 no-resurrection 的协议，都必须让每一条能够安装 `kappa_i(sid)` 的恢复路径携带并验证一个支配 `sid` 终结状态的 causal fence，或者改变 `pk_i`/密钥世代，或者依赖一个等价的可信因果边界。

**事件序列证明。** 在 `E_before` 中，节点处于 `RAW`，攻击者先取得合法的 `m_old`，但网络延迟该消息；节点随后丢失私密状态并请求 `Cure`。为保证 recovery liveness，协议必须存在一条恢复转移 `r`，使节点能在没有 `m_old` 的情况下加入未来会话。在 `E_after` 中，先让另一个诚实执行完成 `PF_sid`，再发送与 `E_before` 相同的恢复可见信息，并最后交付延迟的 `m_old`。如果 `r` 和旧消息都不携带支配 `sid` 的状态，节点在交付 `m_old` 时的本地可见状态与 `E_before` 不可区分，因而必须接受它，重新安装 `kappa_i(sid)`；这正产生 `R`。若拒绝 `m_old`，则同样拒绝 `E_before` 中合法的恢复路径，违反 recovery liveness。

该定理的价值在于精确划分四种代价，而不是宣称普通 forward security 不够：

1. 传输并验证 `T_i`，使退休 capability 在异步恢复中成为吸收态；
2. 引入新的 key generation/epoch，使旧消息在密码学上失效；
3. 放弃丢失状态节点对未来会话的恢复活性；或
4. 引入可信时钟、forward-secure channel、TEE 等等价的外部因果边界。

因此“stable public key + Cure + arbitrary late messages + no resurrection”并非无条件三难；准确说法是：**没有单调 causal fence 或等价密钥世代时，这四项不能同时实现。** 这比前向安全更强的地方，是终结事件按 `sid` 形成偏序，且要求它支配未来状态暴露，而不是只按时间段删除旧密钥。

### 12.3 显式 tombstone 的状态下界与研究出口

若不使用 accumulator、全局排序器或可信 epoch，而要求节点本地显式判断 `M` 个可并发终结会话的任意子集是否已退休，则其 tombstone 状态至少需要区分 `2^M` 个退休集合，即至少 `M` 个二元信息位。这只是显式状态表示的下界，不是对密码学 accumulator 的不可能性结论。

由此得到更有吸引力的构造问题：能否在完全异步、无全局 epoch 下，用可合并的 `O(lambda)` 级 capability state 和短证明表达任意会话退休集合，同时满足：

- `T_i` 的合并满足交换、结合、幂等；
- 迟到的 pre-retirement 消息无法回滚 `T_i`；
- `Cure` 只需恢复 `T_i` 和未来能力，不恢复已退休 `sid` 的私密状态；
- `PC_sid` 仍落在 `H_b(Gamma_dec)`，而不是只证明“收到了若干签名”。

如果只能使用显式 `O(M)` tombstone，该结果仍然可以作为状态/通信下界；若能给出紧凑的可验证合并状态，则它才是区别于普通 puncturable encryption、proactive DKG 和每 epoch refresh 的技术出口。

### 12.4 `B_seed` 匹配安全定理（无 cure 状态恢复）

在不要求 `Cure` 后恢复已穿孔 PE secret state 的模型中，`B_seed` 可以作为 Robust-Hitting frontier 的匹配构造，而不应包装成新密码学原语。其接口为：每个委员 `P_j` 持有独立 PE 密钥；客户端对短 mask `k_u` 做 `q`-out-of-`n` Shamir 分享 `s_{u,j}`，并分别以 `(sid,u)` 为标签加密给 `P_j`。委员只对 ACS 确定的集合求和得到 `S_j=sum_u w_u*s_{u,j}`，发布可验证聚合分片，然后对该 `sid` 下的 ciphertext 做 puncture 并擦除明文分片。

**匹配定理（选择性 `sid`）。** 假设：

- PE 对每个委员满足 puncture 后 key exposure security；
- Shamir 分享的阈值为 `q`，退休集合 `A` 满足 `A in H_b(Gamma_q)`；
- 目标会话穿孔前敌手最多保留 `b` 个委员的旧状态；
- 聚合分片只通过一个已认证的 `(sid,H_sid,ct_sum)` 上下文释放；
- `Cure` 不恢复目标 `sid` 的穿孔前 PE 状态。

则未来暴露所有当前状态后，敌手至多得到 `B union (P-A)` 的旧解密能力。由 `A in H_b(Gamma_q)`，该集合不包含任何 `q` 个解密集合；PE 安全性隐藏未穿孔 ciphertext 的单独 mask，Shamir 线性隐私把 `b` 个逐客户端分片与公开的加权聚合 mask `K=sum_u w_u*k_u` 的联合视图模拟为只泄漏 `K`。因此只释放 `sum_u w_u*x_u`，不释放单客户端 `x_u`。

这个定理明确了正向基线的边界：它证明 Robust-Hitting 可达，但客户端成本仍为 `O(d+n*kappa)`，且 cure/recovery 被刻意排除。若后续构造不能同时把短 ciphertext 压到 `O(d+kappa)` 并恢复 `T_i`/未来状态，协议构造创新应关闭，保留“privacy finality = robust hitting + causal-fence state”作为理论主线。

## 13. 下一步：只做一个可证伪问题

下一轮不再扩展更多功能，而只验证以下命题：

> **是否存在一个无全局 epoch 的、可合并的 `O(lambda)` 级 per-node capability state，使任意并发 `sid` 的退休事实在完全异步迟到消息和 `Cure` 后仍保持 no-resurrection，同时不恢复已退休会话的私密状态？**

执行顺序固定为：

1. 先给出 `T_i` 的抽象接口和合并代数；
2. 对不带 `T_i` 的恢复协议写出上述 indistinguishability attack；
3. 检查 authenticated accumulator、CRDT tombstone 和 hash-chain 方案是否真的支持异步合并，而不是偷偷引入全局序；
4. 只有存在非平凡状态压缩且仍满足 `H_b(Gamma_dec)` 时，才继续具体密码学构造。

### 13.1 初步状态表示审计

| 候选状态 | 并发 `sid` 合并 | 迟到旧消息 | `Cure` 恢复 | 当前判断 |
|---|---|---|---|---|
| 显式 grow-only tombstone / 2P-Set | 交换、结合、幂等 | 直接拒绝已记录 `sid` | 可恢复完整集合 | 正确但状态/同步成本随并发会话数增长 |
| hash-chain / 单调序列号 | 只能表达一个全序 | 分叉或较小序列可被回放 | 恢复短摘要 | 不能表达互不先后的退休事实；强行排序等价于全局 epoch |
| Merkle root / authenticated set | 摘要可合并性不足，需处理并发根 | 旧消息没有退休后的新 proof | 可恢复 root | 只压缩摘要；若旧 capability 不携带可失效 proof，仍无法拒绝回放 |
| 通用动态 accumulator | 理论上可压缩到 `O(lambda)` | 需要 capability 携带可验证的当前成员/非成员证据 | 可恢复 accumulator state | 最有希望，但需要新的 proof-carrying capability 接口；不能直接把 accumulator 当 tombstone |
| 多 accumulator + epoch transition | 用状态切换规避逐 witness 更新 | 旧状态在切换后失效 | 恢复当前 epoch 状态 | 已有撤销基线方向，但明确引入 epoch；不满足本题无全局 epoch 目标 |
| Bloom/filter 类撤销摘要 | 可合并但概率化 | 无假阴性时可拒绝旧 `sid` | 可恢复摘要 | 状态仍随 `M` 增长，假阳性会损害未来会话活性 |

这里的关键障碍可以写成一个接口问题。若旧 capability `m_old` 在退休前生成，节点在退休后只看到 `m_old` 和本地摘要 `T_i'`，则必须存在一个验证规则

```text
Accept(T_i', m_old) = false,
Accept(T_i,  m_old) = true,
```

其中 `T_i'` 只比 `T_i` 多了并发退休事实，且 `m_old` 不会被退休方重新签发。普通 hash/Merkle 摘要没有这个性质；普通 accumulator 也只有在 capability 携带可被后续添加操作失效的成员性证明，或携带可验证的非撤销证明时才可能满足它。后者正是需要单独定义和证明的新密码学接口。

因此下一轮的最小构造目标不是“找一个 accumulator”，而是定义 **revocation-invalidating capability**：

1. 未来 capability 能在稳定 `pk_i` 下验证；
2. 添加 `sid` tombstone 后，旧 `sid` capability 必然失效；
3. 与其他并发 tombstone 的合并满足交换、结合、幂等；
4. 节点只恢复摘要和未来能力，不恢复目标会话的 PE 状态；
5. 失效证明与 `PC_sid`、`H_b(Gamma_dec)` 组合，而不是只保证本地状态机拒绝消息。

若第 2 项要求重新签发所有未退休 capability，则状态压缩只是假象，协议会退化为全局 rekey；这是审计中必须首先排除的伪解。

### 13.2 `Stale-Proof Dilemma`

为避免把 accumulator 的集合压缩能力误当成协议解，定义最小 capability 接口：

```text
Issue(T, sid) -> c_sid
Retire(T, sid, PC_sid) -> (T', Delta_sid)
Update(c_sid, Delta) -> c'_sid
Verify(T, c_sid) -> {0,1}
Merge(T_1,T_2) -> T_1 join T_2
```

至少需要以下性质：

- **Selective invalidation：** `Verify(T,c_sid)=1`，加入 `sid` 的退休事实后，`Verify(T',c_sid)=0`；
- **Non-interference：** 加入 `sid` 不能使另一个未退休 `sid'` 的可更新 capability 失效；
- **Update commutation：** 并发 `Delta_1,Delta_2` 的更新顺序不影响最终验证结果；
- **No re-issue：** 退休 `sid` 不要求重新签发所有其他仍有效的 capability；
- **Recovery：** `Cure` 只需恢复 `T` 和公开更新材料，不恢复已退休会话的 PE 状态。

**Stale-proof dilemma（接口引理）。** 如果 `c_sid` 只包含在旧状态 `T` 下生成的固定 proof，且验证者既看不到 `Delta`/撤销证明，也没有能把旧 proof 更新到新状态的 `Update`，则无法同时满足 selective invalidation 和 non-interference。若退休 `sid` 后直接拒绝所有旧 proof，未退休 capability 也会被同一状态变化误伤；若继续接受旧 proof，则 `sid` 产生 resurrection。

这不是对 accumulator 的一般不可能性结论。动态 universal accumulator 可以通过 non-membership witness、witness update 或 delegated update 规避该引理，但这些更新材料本身必须进入异步协议：

1. `Cure` 节点如何取得所有影响其旧 capability 的 `Delta`；
2. Byzantine 节点能否提供冲突或回滚的更新顺序；
3. 不同 `sid` 的并发更新是否可交换、可验证且不要求全局排序；
4. 迟到旧消息是否携带足以更新/验证 witness 的材料；
5. 更新失败时是拒绝单个 `sid`，还是错误地阻塞未来所有会话。

这正是现有 accumulator 论文与本问题的接口差异。Li--Li--Xue 的 universal accumulator 解决 membership/non-membership proof；Camenisch--Kohlweiss--Soriente 的动态撤销工作则明确把 witness 更新作为撤销系统的核心成本，并讨论向用户或委托方分发更新。它们没有给出异步 Byzantine 委员在 `Cure` 后恢复 `T_i`、合并并发 `PC_sid`、同时保持 `H_b(Gamma_dec)` 的组合定理。

因此当前真正的构造候选应写成：

> **Asynchronous Witness-Update Finality：** 设计一个可合并的退休状态和 proof-update channel，使旧 capability 对其自身 `sid` 的退休必然失效，而对其他并发会话保持可验证；更新材料可迟到、可重放但不可回滚，并与 threshold privacy-finality 证书组合。

若更新材料需要逐个传播所有 tombstone，方案退化为显式 `O(M)` 状态；若需要重新签发未退休 capability，方案退化为 epoch/rekey；若允许在线查询撤销集合，则必须把查询一致性和可用性纳入安全模型，不能再称为纯本地 `Cure`。

### 13.3 最小理想功能 `F_AWF`

为后续构造固定接口，定义 `F_AWF`（Asynchronous Witness-Update Finality）：

```text
Setup() -> T_0
Issue(sid, T) -> cap_sid
Retire(sid, PC_sid) -> (T', Delta_sid)
Merge(T_1, T_2) -> T_1 join T_2
Recover(snapshot, Deltas) -> T
Publish(Q, m) -> public event or reject
Process(Q, m, T_local) -> {accept, reject}
Verify(T, cap_sid) -> {accept, reject}
```

其中功能内部维护退休集合 `R`，但实现只需暴露摘要 `T` 和公开更新材料。功能要求：

1. `Retire` 只有在 `PC_sid` 满足 `A_sid in H_b(Gamma_dec)` 时才会把 `sid` 加入 `R`；
2. `Merge` 对并发更新满足交换、结合、幂等，重复或乱序交付不会回滚 `R`；
3. 若 `sid in R`，所有未来 `Verify(T,cap_sid)` 必须拒绝；若 `sid' not in R` 且其更新材料最终可达，`cap_sid'` 必须最终可验证；
4. `Recover` 可以恢复 `T` 和 `Deltas`，但不能恢复目标 `sid` 的穿孔前 PE 状态；
5. `T` 的大小只依赖安全参数，而不依赖同时存在的会话数 `M`；总更新通信可以依赖 `M`，但不能偷偷改称为无状态恢复；
6. 敌手可以重放、延迟、分叉公开更新，但不能伪造有效 `PC_sid` 或使一个已合并的退休事实回滚；
7. 对公开 `KEYREVEAL`，`Publish` 的 send event 立即把 key、可验证 point 和派生
   recovery material 计入历史暴露视图；
8. 若 `Publish(Q,KEYREVEAL)` 发生在 `Retire(sid,PC_sid)` 之前但 `Process` 在退休后
   才发生，公开事件仍保留在历史视图，而 `Process` 必须拒绝对 `Retired` coordinate
   的新安装或恢复边；若 send event 晚于退休，则功能拒绝该 key-reveal 边。

这个接口刻意把两个成本分开：**本地稳定状态**可以是 `O(lambda)`，但**公开更新日志/证明材料**可能是 `O(M lambda)`。若某构造声称恢复只需一个摘要，却没有解释旧 capability witness 如何从旧摘要过渡到新摘要，则它没有实现 `F_AWF`。若 `Recover` 依赖查询一个在线、强一致的撤销服务，则该服务必须被纳入功能和敌手模型，而不能被隐藏在 accumulator API 后面。

`F_AWF` 与 secure aggregation 的组合条件是：`PC_sid` 只负责把 `sid` 加入退休集合，不释放单客户端 mask；`F_AWF` 只负责 capability 的吸收态，不恢复 `PE` 明文状态；`Robust-Hitting` 负责证明未来状态暴露不能重新获得一个授权解密集合。三者缺一不可，单独的 accumulator correctness 不能替代后两者。

这里的 `Publish/Process` 拆分是模型的一部分，而不是实现细节。它把网络中已经
公开的 capability 与节点状态机是否接受该消息分离，因而覆盖完全异步网络中退休
前发送、退休后到达的 `KEYREVEAL`。没有这个拆分，`F_AWF` 无法表达 Lemma 18
所需的 send-time exposure 语义。

### 13.4 `Cure--Puncture State Separation`

`F_AWF` 只处理公开 capability 的可达性，还没有解决委员私密状态的恢复。设 `sk_i^0` 是委员 `P_i` 在 `sid` 退休前的 PE 状态，`sk_i^{sid}` 是执行 `Puncture(sid)` 后的状态。若 `P_i` 在退休后被 `Cure`，未来客户端仍使用稳定 `pk_i`，则恢复协议必须服务未来 ciphertext，同时不能让未来状态暴露恢复 `sk_i^0` 对目标 `sid` 的解密能力。

**分离引理。** 公开 tombstone 或 accumulator 摘要不能单独实现上述恢复。任何 `Cure` 路径至少落入以下三类之一：

1. 恢复 `sk_i^0`，或恢复一个可由其直接导出的等价状态；则敌手在未来暴露 cured 节点状态时可以解密已归档的 `sid` ciphertext，违反 `PF_sid`；
2. 恢复 `sk_i^{sid}` 或等价的已穿孔状态；则协议必须提供一个与 `Puncture` 兼容的 state-handoff/threshold-transform，使恢复过程不暴露或重建 `sk_i^0`，且其输入受 `T_i` 支配；
3. 生成新的公钥/密钥世代，或放弃该节点对未来稳定 `pk_i` ciphertext 的服务。

证明是直接的状态暴露区分：在执行 `E_before` 中，敌手保存目标 ciphertext；若恢复状态包含旧解密能力，`E_after` 中未来全体状态暴露即可输出旧明文。若恢复状态不包含旧能力，它必须是对 `sk_i^0` 做过不可逆 puncture 的新状态；公开 `T_i` 只能标识应当穿孔哪些 `sid`，不能从公开信息生成该秘密状态。因此 `F_AWF` 解决的是 no-resurrection 的控制面，而不是 data-plane 的 punctured-state recovery。

这也解释了为什么“给 `sk_i^0` 做 Shamir 分享，再让委员本地 puncture”不是现成黑盒：若 `Puncture` 是非线性操作，局部分享上的变换通常提高多项式次数，并需要 degree reduction/refresh；若先重构 `sk_i^0` 再穿孔，恢复瞬间又暴露历史解密能力。该问题已经在 `B_seed` 审计中被分离出来，但现在应提升为主线的第二个必要接口：

```text
RecoverPuncturedState(T_i, distributed_state, PC_frontier)
    -> sk_i^T
```

其要求是：`sk_i^T` 可服务未退休未来会话；对所有已退休 `sid` 不可解密；恢复输入可乱序、可重放但不可回滚；并且未来暴露 `sk_i^T` 不扩大 `Robust-Hitting` 允许的旧能力集合。仅有 accumulator、forward-secure encryption 或普通 proactive DKG 均不自动满足这个接口。

### 13.5 普通 handoff 与 punctured-state recovery 的黑盒分离

设 `Handoff_s` 是标准 VSS/DPSS handoff：输入若干对同一秘密 `s` 的合法份额，输出另一组对**同一个** `s` 的合法份额，并保证正确性、隐私和异步鲁棒性。设 PE 的 `Puncture` 是作用在秘密状态上的一般非线性状态变换。

**黑盒分离定理（条件版）。** 只调用 `Handoff_s`，而不改变 handoff 的秘密接口、不给它 share-compatible `Puncture` 或 key-switching 关系，不能同时实现：

- stable `pk_i` 下未来会话继续可解密；
- `sid` 退休后的 `PF_sid`；
- `Cure` 后恢复新委员状态且不暴露旧 `sk_i^0`。

**证明分情况：**

1. 对 `sk_i^0` 运行 `Handoff_s`，新委员得到旧秘密的份额；未来达到恢复阈值即可重构 `sk_i^0`，违反 `PF_sid`；
2. 先由某个节点重构 `sk_i^0`、再执行 `Puncture`，恢复过程存在旧解密能力的暴露窗口，且在移动腐化下无法把该窗口从敌手视图中删除；
3. 让每个节点直接对其 Shamir share 执行 `Puncture`，只有当 `Puncture` 对分享是局部线性的、次数不增长且可验证时才保持同一阈值结构；一般非线性 puncture 会提高分享多项式次数，连续 `sid` 会累积 degree，必须额外 degree-reduction/refresh；
4. 生成一个全新的秘密并建立新公钥，或者需要 key-switching/functional re-encryption，则已经超出 `Handoff_s` 黑盒，分别落入 rekey 或新密码学原语。

这个定理不声称不存在 `RecoverPuncturedState`；它精确关闭的是“普通 proactive DKG/DPSS + 现成 puncturable encryption”的直接组合。真正需要的新接口是：旧委员或一组分布式状态持有者能在不重构旧状态的情况下，生成并证明 `Puncture(sk_i^0, F_i)` 的新份额，且该生成过程受可合并 `T_i` 支配。其困难同时来自密码学代数和异步 Byzantine handoff，而不只是消息重放。

### 13.6 `Share-Compatible Puncturing` 与 degree-growth barrier

把数据面缺口抽象为一个新原语。令 `Share_t(k)` 是 `t` 次 Shamir 分享，令 `P_x(k)` 是标签 `x` 的穿孔状态变换。一个 share-compatible puncturing 方案应提供：

```text
SPuncture_x(Share_t(k)) -> Share_t(P_x(k)), proof_x
```

并满足：不重构 `k`；对并发标签 `x,y` 可交换或有可验证的 join；`proof_x` 绑定 `T_i`/`PC_x`；输出分享仍保持相同阈值；公开 `Share_t(P_x(k))` 或其未来状态暴露不能恢复 `k` 对 `x` 的解密能力。

**Shamir degree-growth lemma（坐标式变换）。** 若 `SPuncture_x` 只是对每个 Shamir 份额 `p(i)` 独立应用一个代数次数为 `delta` 的非线性映射 `P_x`, 则输出值是多项式 `P_x(p(X))` 在各点的取值，次数至多为 `delta*t`。因此原来的 `t+1` 阈值不再足以重构输出；连续 `m` 次独立非线性穿孔的朴素坐标式变换次数至多增长为 `delta^m*t`。保持固定阈值必须增加 degree reduction/refresh，或要求 `P_x` 在分享坐标上是线性的/具有特殊 share-compatible 代数结构。

这个引理只排除“对 Shamir 份额逐点套现成非线性 `Puncture`”的黑盒方案，不排除使用双线性分享、特殊 key-homomorphic puncturable PRF 或新的阈值状态编码。它把构造选择精确分成三类：

1. **线性兼容穿孔：** 给出新的 share-compatible puncturable state primitive，并证明 `PC_sid`、`F_AWF` 和 `Robust-Hitting` 的组合；
2. **异步 degree reduction：** 每次或批量穿孔后运行可验证的 ACSS/MPC 降阶，承担额外通信、状态和 Byzantine consistency 证明；
3. **密钥世代切换：** 使用 epoch/rekey/key-switching，把问题转化为已有 forward-secure 或 proactive handoff，但放弃本主线的无全局 epoch 目标。

因此，当前构造的真正 go/no-go 判据不是“能否找到 accumulator”，而是能否在第 1 或第 2 类中实现一个不退化为完整通用 MPC、又能支持长期移动腐化的 `SPuncture`。若只能落入第 3 类，主线应保留为 Robust-Hitting、Causal-Fence Necessity 和黑盒分离结果。

### 13.7 WBTE 的近邻但非等价性

WBTE/BEAT-MEV 的确包含一个容易误判为本题答案的步骤：对客户端的 `THE.Enc(K_i)` 做同态求和，得到 `THE.Enc(sum_i K_i)`，再用 key-homomorphic puncturable PRF 处理 batch。它仍不能直接实现当前接口：

1. 标准 WBTE ciphertext 同时携带每个 `K_i*`；聚合 key 与这些逐项 punctured keys 一起用于恢复每个 `m_i`，而不是只释放 `sum_i m_i`；
2. 若删除 `K_i*` 以避免逐客户端泄漏，原文的逐项解密等式不再成立，这已经不是 WBTE 黑盒调用；
3. 即使只保留聚合 ciphertext，标准 WBTE 也没有 `Puncture`/`Erase` threshold decryption state 的接口。未来暴露服务器状态仍可针对归档的客户端 ciphertext 运行旧解密；
4. 它的 weighted construction 还把 THE 与 KH-PPRF 的 CRS 做非黑盒代数耦合，不能把“同态聚合 + puncturable PRF + threshold”分别替换后直接得到 `SPuncture`。

所以 WBTE 提供的是**批量选择性解密**基线，不是 `RecoverPuncturedState`：它解决“哪些消息现在被逐条打开”，而本题还要求“打开聚合后，未来状态暴露不能重新打开任何单客户端 ciphertext”。这条接口分离应在后续论文中作为强基线，而不是把 WBTE 描述成已解决或完全无关。

### 13.8 正式原语：`RPTA`

将所需数据面定义为 **Recoverable Puncturable Threshold Aggregation**（`RPTA`）。该原语只处理短 mask key；FL 梯度仍由 `z_u=x_u+G(sid,k_u)` 承载。第一版固定 selective `sid` 和唯一授权描述符，不提供自适应线性查询接口。

```text
Setup(1^lambda,n,q) -> (pp,PK,{st_i^empty},{VK_i},{C_i^empty})
Enc(PK,sid,k;rho) -> ct
Eval(PK,D,{(w_u,ct_u)}_{u in S}) -> ct_D
PartDec(st_i^T,D,ct_D) -> (sigma_i,pi_i) or reject
Combine(D,ct_D,{(sigma_i,pi_i)}_{i in Q}) -> K_D or reject
Puncture_i(st_i^T,sid,CC_sid) -> (st_i^T',C_i',ack_i)
Contribute(j,i,rid,T_req,st_j) -> (mu_{j->i},pi_j) or reject
Recover_i(rid,T_req,{(mu_{j->i},pi_j)}_{j in L}) -> (st_i^req,omega_i,C_i^req)
CheckInstall_i(T_local,T_req,st_i^req,omega_i,C_i^req) -> {0,1}
VerifyRecovery(PK,i,rid,T_req,C_i^req,pi_pub) -> {0,1}
```

`D=(sid,S,w,H_ct,H_out)` 是由 `CC_sid` 固定的唯一聚合描述符，其中 `H_ct` 承诺规范排序后的客户端标识、权重与 ciphertext multiset，`H_out` 绑定输出接收者和用途。`T` 是 `F_AWF` 认证的单调 frontier，`F(T)` 是它承诺的已退休会话集合。`st_i^T` 是节点 `i` 的私密功能份额，`C_i` 是公开状态承诺。

这里必须区分两种验证。`CheckInstall_i` 是诚实节点内部运行的本地算法，可以读取待安装秘密状态；`VerifyRecovery` 只读取承诺和公开转录，绝不把 `st_i^T` 当公开输入。公开证明最多证明“恢复输出与被认证的 sharing/frontier 一致”，不能证明软件确实擦除了旧内存。

`Recover_i` 只恢复目标节点 `i` 的一个当前功能份额，不输出整组 sharing，更不输出 master secret。贡献者是当前委员会中互异的节点集合 `L in Gamma_live`；每条 `mu_{j->i}` 必须绑定目标身份 `i`、恢复实例 `rid`、请求 frontier `T_req` 和接收者密钥，因而不能跨节点或跨实例拼接。若贡献者的本地 frontier 尚未支配 `T_req`，它必须先合并公开更新、执行缺失穿孔并擦除旧状态，之后才可贡献。

#### 正确性与状态一致性

1. **Authorized aggregate correctness：** 对未穿孔 `sid`、合法 `D` 和任意 `|Q|>=q`，`Combine` 输出 `K_D=sum_{u in S}w_u k_u`。
2. **Context uniqueness：** 诚实节点对同一 `sid` 只接受绑定 `CC_sid` 的一个 `D`；不同集合、权重、接收者或 ciphertext multiset 产生不同上下文。
3. **Cryptographic puncture soundness：** 若 `sid in F(T)`，任何通过本地安装检查或公开承诺检查的当前状态都不能为该 `sid` 产生可接受的部分解密；未来暴露该状态也不能导出旧能力。
4. **Order independence：** 对任意并发退休集合 `F`，不同合法穿孔/合并顺序得到功能等价状态；至少满足相同的 `PartDec` 接受语言。
5. **Recovery correctness：** 若 `L in Gamma_live`、至多 `f` 个贡献者 Byzantine，且诚实消息最终送达，`Recover_i` 最终输出服务所有 `sid notin F(T_req)`、拒绝所有 `sid in F(T_req)` 的单节点份额。
6. **Frontier safety：** 仅当 `T_req` 支配安装时的 `T_local`，且恢复证据绑定同一 `rid/i/T_req`，`CheckInstall_i` 才接受。若恢复期间收到新 `PC_sid`，节点必须把请求提升到 `Join(T_req,PC_sid)` 或取消重启，绝不能安装较旧输出。
7. **No old-capability intermediate：** 任何诚实穿孔或恢复步骤都不产生可由单方读取的 `st_i^empty`、master secret，或能服务 `F(T_req)` 中会话的临时状态。
8. **Erasure accounting：** `ack_i` 只能在诚实节点完成原子状态替换和旧状态擦除后签发；Byzantine 节点可以假确认，其身份必须计入历史暴露集合 `B`。密码学证明不声称验证物理擦除。

#### 最小状态机与腐化边界

```text
Active(T,st_i,C_i)
  -- accept CC_sid --> Retiring(sid,D,T,st_i)
  -- lose/cure -----> Recovering(rid,T_req,C_base)

Retiring(sid,D,T,st_i)
  -- atomic Puncture; swap; erase --> Punctured(sid,T',st_i',C_i')

Punctured(sid,T',st_i',C_i')
  -- emit ack_i only now --> Active(T',st_i',C_i')

Recovering(rid,T_req,C_base)
  -- receive newer PC --> Recovering(rid',Join(T_req,PC),C_base)
  -- valid Recover_i and CheckInstall_i=1; erase transcript --> Active(T_req,st_i^req,C_i^req)
```

不变量是：frontier 只增不减；`ack_i` 的发送点严格晚于擦除点；`PartDec` 只在 `Active` 中执行；任何恢复输出若落后于当前 frontier 就永久不可安装。`Retiring` 与 `Recovering` 竞争时，新 retirement 优先：恢复实例要么吸收新 frontier，要么作废。

敌手可在不同会话和不同恢复实例之间长期移动腐化，并永久保留已读副本。对目标 `sid*`，某节点在其诚实 `ack_i` 前发生的旧能力暴露都累计进入 `B`，不是只计算“同一时刻”腐化数。对单次未完成的 `Recover_i`，暴露任何参与者的易失中间态即视为该实例内腐化该参与者；首版要求每个恢复实例累计至多 `f` 个此类参与者。若只限制同时腐化、却允许敌手在一个无限延迟的恢复实例中依次读取所有参与者，则普通异步 proactive/repair 也无法提供秘密性；该限制必须写成敌手模型，而不能藏在证明里。恢复完成后允许未来暴露所有当前持久状态。

#### 选择性单描述符隐私游戏 `G_RPTA^sel`

该游戏避免自适应查询历史，只验证一个预先固定的目标会话和授权聚合：

1. **Commit：** 敌手先提交 `sid*`、`S*`、权重 `w*` 和两组短 keys `K^0={k_u^0}`、`K^1={k_u^1}`，满足相同公开元数据且

```text
sum_{u in S*} w_u^* k_u^0 = sum_{u in S*} w_u^* k_u^1.
```

2. **Setup/Challenge：** 挑战者运行 `Setup`，取随机位 `beta`，返回目标 ciphertext `ct_u^*=Enc(PK,sid*,k_u^beta)`；其他并发 `sid` 可由环境正常执行，但没有目标会话的第二个授权描述符。
3. **Pre-puncture exposure：** 在各节点穿孔 `sid*` 前，敌手累计读取集合 `B` 的完整状态，要求 `|B|<=b`；读取副本永久保留。
4. **Authorized release：** `CC_sid*` 固定 `D*`，挑战者只给出 `ct_D*`、合法部分解密转录和共同值 `K_D*`。两世界中该值相同。
5. **Retirement：** 实际退休集合 `A` 形成 `PC_sid*`，要求 `A in H_b(Gamma_dec)`；节点先原子 `Puncture+Erase` 再确认。
6. **Cure/Recover：** 敌手任意调度节点释放、治愈和恢复，任意延迟或重放公开更新；恢复遵守上述实例内累计腐化预算。恢复 oracle 可以返回绑定当前 frontier 的贡献，但不存在“恢复目标 pre-puncture state”这一接口。
7. **Total current-state exposure：** 最终敌手取得所有节点当前 `st_i^T`、公开日志和恢复证明，并保留第 3 步旧状态。
8. **Guess：** 敌手输出 `beta'`；要求 `|Pr[beta'=beta]-1/2|` 可忽略。

这个游戏允许敌手看到授权聚合 mask，因而测试的是 aggregate-only 泄漏：两组单项 keys 不同但加权和相同。它不授予目标 `sid*` 的任意第二线性组合、单 ciphertext 部分解密或自适应挑战选择；这些都属于更强扩展，不进入首版论文主线。

#### 恢复安全游戏 `G_RPTA^rec`

单独验证 `Recover_i`，避免把恢复活性藏在隐私游戏的 admissibility 条件里。敌手选择已退休集合 `F*`、目标节点 `i`、恢复实例 `rid` 和一个未退休未来会话 `sid+`：

1. 挑战者生成并穿孔得到分布式状态族 `{st_j^{T*}}`，其中 `F(T*)=F*`；
2. 敌手在该实例累计腐化至多 `f` 个参与者，伪造、延迟、重放或跨实例搬运任意 Byzantine 消息；
3. 若诚实可用集合属于 `Gamma_live` 且消息最终送达，恢复节点必须最终通过 `CheckInstall_i`，公开承诺通过 `VerifyRecovery`；
4. 敌手若使诚实节点安装不支配本地 frontier 的状态、使安装状态服务任一 `sid in F*`，或从恢复转录构造退休会话的有效解密集，则获胜；
5. 安装状态必须正确服务 `sid+`。恢复完成后的全体当前状态暴露仍纳入 `G_RPTA^sel`，不在本游戏中用含糊的“两段历史”重复定义。

`G_RPTA^sel` 负责 past privacy；`G_RPTA^rec` 负责 Byzantine recovery correctness、no-resurrection 和未来服务活性。`RPTA` 是稳定 threshold 公钥下的新 compact 原语目标；`B_seed` 仍只是每委员独立 PE key 的非 compact 匹配基线，两者不能混用同一安全证明。

### 13.9 最小安全定理目标

**组合定理候选。** 若：

- `RPTA` 满足 `G_RPTA^sel` 与 `G_RPTA^rec`；
- `Gamma_cert subseteq H_b(Gamma_dec)`，且对每个 `L in Gamma_live` 存在 `A in Gamma_cert` 满足 `A subseteq L`；
- ACS/BA 固定唯一 `D_sid`，认证不可伪造，`Puncture+Erase` 对诚实节点原子执行；
- mask generator `G` 对 key 加权同态且满足所需伪随机性；

则包装协议实现 selective-`sid` 的长期异步 aggregate-only privacy finality：输出 `sum_u w_u x_u` 后，即使委员会长期移动腐化、节点经历 `Cure/Recover`、最终全部当前状态暴露，敌手仍不能区分任意两组具有相同授权聚合的单客户端更新。

证明至少包含四个模块：替换 mask PRG；调用 `G_RPTA^sel` 替换单项 keys；用 `G_RPTA^rec` 排除 stale install 和恢复转录中的旧能力；用 Robust-Hitting 排除历史副本形成授权解密集。不能预先声称“只需四个 hybrid”：实际构造若要模拟并发状态转换、恢复中间态或恶意客户端一致性证明，必须分别补充 hybrid。

因此当前主线的更准确叙事是：**Privacy Finality is not only revocation; it is recoverable puncture.** 一个会话只有在“公开终结证书 + 吸收态 capability + 可恢复但不复活的穿孔秘密状态”三者同时成立时，才真正实现长期异步隐私终结。

### 13.10 新理论核心：精确穿孔的线性状态下界

抽象一个比具体密码系统窄、但正好覆盖“Shamir 份额本地更新”的模型。设功能密钥状态属于 `d` 维线性空间 `V`。每个可退休标签 `tau in [M]` 对应非零解密能力泛函 `ell_tau in V*`；本地穿孔由线性映射 `P_tau:V->V` 表示，并满足：

```text
exact erasure:       ell_tau o P_tau = 0
non-interference:    ell_sigma o P_tau = ell_sigma,  for every sigma != tau.
```

**线性状态维数下界（条件版）。** 在上述 exact erasure 与 exact non-interference 模型中，`{ell_tau}_{tau in [M]}` 线性无关，因此 `d>=M`。

**证明。** 假设 `sum_tau a_tau ell_tau=0`。对任意 `j`，在等式两侧复合 `P_j`，得到 `sum_{tau != j}a_tau ell_tau=0`。与原式相减得 `a_j ell_j=0`；由 `ell_j` 非零可知 `a_j=0`。对所有 `j` 成立，故这些泛函线性无关。

结合 13.6 的 degree-growth barrier，可得到更清楚的三分结论：对 Shamir 分享逐份额、无交互地执行代数状态更新，若要对所有次数 `t` sharing 保持次数不增长，则更新只能是仿射型；把常数坐标并入状态后仍落入上述线性模型。于是，支持 `M` 个任意、精确、互不干扰标签的本地 share-compatible puncture，需要 `Omega(M)` 个域元素状态。任何声称同时实现“稳定公钥、任意 `sid`、精确穿孔、无交互本地更新、`o(M)` 状态”的方案，至少必须突破其中一个前提。

这不是一般 PE 的无条件黑盒下界，也不排除 obfuscation、非线性编码或交互式 MPC。它精确排除的是当前最诱人的伪出口：“对每个 Shamir share 调一个 compact `Puncture`，阈值和状态大小都自动保持不变”。可行出口只剩四类：允许近似 liveness；使用交互式 degree reduction/MPC；限制标签为有序 epoch；或采用新的非线性 share representation。

### 13.11 最小可行性见证：`BF-RPTA`

Bloom Filter Encryption 已表明“穿孔即删除若干秘密坐标”可以换取高效更新和可控 correctness error。沿这一点可定义一个不依赖一般非线性 `SPuncture` 的阈值聚合见证构造；它暂时是研究基线，不是已确认的新颖构造。

1. 取 `m` 个相互独立、支持加权同态与可验证部分解密的 `q-out-of-n` threshold PKE 实例。节点 `i` 持有每个坐标 `ell in [m]` 的秘密份额 `sk_{ell,i}`。
2. 聚合器先承诺 `sid` 与会话元数据，之后由异步共同随机数或不可偏置 beacon 产生高熵盐 `r_sid`，形成客户端提交前可验证的启动证书 `SC_sid`；最终 `CC_sid` 再承诺 `H(SC_sid)`。令 `I_sid={H_1(r_sid),...,H_k(r_sid)}`。若调度者能在看到盐后反复挑选 `sid`，标准 Bloom-filter 假阳性界会被 grinding 破坏，因此“commit-then-randomize”顺序不是可省略细节。
3. 客户端把同一短 mask key `k_u` 分别加密到 `I_sid` 的 `k` 个公钥下，并附同明文一致性证明；`Eval` 在每个坐标按权重同态聚合。
4. `PartDec` 选择 `I_sid` 中任一尚未删除的坐标，收集该坐标的 `q` 个有效部分解密，恢复唯一授权的 `K_D`。
5. `Puncture_i(sid)` 把 `I_sid` 对应的本地秘密份额设为 `perp` 并擦除，同时把这些位置加入单调 bitset/frontier。Bloom filter 无假阴性，所以已退休 `sid` 的所有坐标必然被删除。
6. `Recover_i(T_req)` 只对 `T_req[ell]=0` 的存活坐标运行批量 Shamir share repair；对 `T_req[ell]=1` 的坐标既不发送恢复贡献，也不接受输出。恢复因此只搬运已经穿孔后的投影状态，不执行非线性 secret transform。

若最多退休 `R` 个会话，取标准 Bloom 参数

```text
m = Theta(R log(1/epsilon)),    k = Theta(log(1/epsilon)).
```

则节点状态和公共参数为 `O(m)` 个 threshold-key 元素，客户端短 key ciphertext 为 `O(k)` 个 PKE ciphertext；privacy-finality safety 无 Bloom 假阴性，未退休会话可能以至多 `epsilon` 概率因碰撞而不可服务。换言之，它把误差放在未来 liveness，而不是历史 privacy。达到容量上限后只能扩容或建立新公钥，这一点必须显式计入系统生命周期。

这个见证与 13.10 形成有用闭环：精确的本地线性穿孔需要 `Omega(M)` 状态；`BF-RPTA` 使用 `Theta(R log(1/epsilon))` 状态并允许 `epsilon` 级近似 liveness。真正值得投稿的后续问题不再是“能否恢复已穿孔状态”，而是：

> **在完全异步、长期移动腐化和稳定公钥下，recoverable puncture 的状态--交互--liveness-error 最优权衡是什么？**

当前最小论文包可以由四项组成：privacy finality/Robust-Hitting 刻画；带恢复竞争的 causal state machine；线性 share-compatible puncture 下界；以及 `BF-RPTA` 的近匹配构造与异步恢复证明。若阈值化 BFE/坐标删除已有直接先例，则保留下界和状态机，构造部分降为基线。

### 13.12 `BF-RPTA` 编译定理：静态数据面与长期状态层必须分开

上一节把“聚合开放安全”和“长期份额恢复”一起塞进 `AO-THE`，导致接口吞掉了真正难点。TACITA 的 modified STE 已经给出静态、one-shot、无 repair 的聚合开放核心：其 Figure 9 让静态敌手选择两组等和消息，看到所有单项 challenge ciphertext、聚合 ciphertext 及其部分解密后仍不能区分。这个游戏与 `G_AO-THE^1` 的静态核心实质一致；因此不能再把“challenge-related aggregate transcript 是否可模拟”写成完全开放问题。

正确的分层是：

```text
Static-AO.Setup/Enc/Eval/PartDec/Combine
    提供一次聚合开放，只泄漏唯一授权和；

RCL.Puncture/Contribute/Recover/CheckInstall
    管理长期 capability state、frontier、移动腐化与 cure。
```

TACITA 直接覆盖无权和；若权重在加密前已固定，可把权重吸收到明文。当前“由 `CC_sid` 晚绑定任意公开权重”的接口仍需额外证明 scalar homomorphism 与同明文一致性，不能由 TACITA 原文自动推出。更重要的是，TACITA 的腐化集合在消息挑战前静态选择，委员会定位为 ephemeral one-shot；原文明确把 adaptive corruption 排除在范围外，也没有 `Puncture`、frontier 或 share repair。因此它解决的是 `Static-AO`，不是 `RCL`。

**修正后的 Bloom 编译定理（条件版）。** 设：

1. 每个坐标使用满足 TACITA-style extended CPA 的 `Static-AO`，并提供上下文绑定和可验证部分解密；
2. `RCL` 能在不恢复退休坐标的条件下修复当前成员状态，并满足 `G_RPTA^rec`；
3. 恶意客户端场景使用 simulation-sound 的同明文一致性证明，保证同一客户端在 `I_sid` 的所有坐标加密同一 `k_u`；
4. `SC_sid` 按 commit-then-randomize 产生独立高熵盐，最多有 `R` 个退休会话；
5. 每个 `PC_sid` 的实际确认集合 `A_sid in H_b(Gamma_q)`，因此恢复状态机保持 `R_sid=emptyset`；

则 `BF-RPTA` 满足 selective single-descriptor privacy finality，并具有：

```text
privacy failure:       negl(lambda)
future liveness error: mu_R <= (1-exp(-(R+1/2)k/(m-1)))^k + negl(lambda)
node secret state:     O(m) coordinate states
client key ciphertext: O(k) Static-AO ciphertexts + one consistency proof.
```

**证明骨架。** 固定目标 `sid*`。Bloom filter 无假阴性，所以 `I_sid*` 中每个坐标都被 `A_sid*` 的节点擦除。对任一目标坐标，敌手可保留的旧 states 属于 `(P-A_sid*) union B`；由 Robust-Hitting，

```text
|(P-A_sid*) union B| < q.
```

因此未来全体当前状态和所有合法恢复都不能补足该坐标的解密访问集。数据面不能
未经证明地逐坐标调用 TACITA-style extended CPA：同一客户端的 mask key 在
`I_sid` 的所有坐标中相同，替换单个 coordinate 会被跨坐标 consistency proof
检测。需要一个联合向量 aggregate-opening 游戏，挑战两组跨坐标一致的 key
vectors 并保持唯一授权聚合相同；一致性证明只能作为该联合游戏中的可模拟语句，
不能替代联合安全性。最后由 `G_RPTA^rec` 排除 stale recovery 安装。对未来未退休
`sid+`，只要 `I_sid+` 至少有一个从未被退休会话占用的坐标，就仍可形成当前解密集；
全部 `k` 个坐标均被占用的概率即上述 Bloom 假阳性界。

因此，`BF-RPTA` 的数据面归约采用联合向量游戏。证明顺序是：先在双模式模拟
CRS 下模拟全部跨坐标一致性证明，再按 coordinate 使用 `Static-AO` 安全性，
最后恢复真实端点证明。该步骤要求模拟器能够处理中间 ciphertext 向量；普通
只支持真实语句模拟的 NIZK 需要替换为满足双模式模拟条件的证明系统，或把
联合向量安全作为独立假设。

一个更小且证明端点闭合的具体关系是：客户端对所有坐标提交一个 batched
simulation-extractable NIZK，statement 和 relation 为：

```text
x_u = (ctx_sid, u, {ek_ell, tag_sid,ell, w_u, ct_u,ell}_{ell in I_sid})

R_eq(x_u; k_u, {rho_u,ell}) iff
  for every ell in I_sid,
    ct_u,ell = Enc_ell(ek_ell, tag_sid,ell, w_u*k_u; rho_u,ell).
```

它直接证明所有坐标使用同一个 `k_u`，不引入需要随 challenge key 一起切换的
commitment。若 `R_eq` 具有双模式模拟，模拟 CRS 可吸收逐坐标 hybrid 中暂时
不一致的 ciphertext；但仍需单独核对 TACITA ciphertext 的随机预言机/群方程能否
有效编码进该关系，并证明 `Static-AO^aux` 的辅助输入嵌入。

该辅助输入条件可以按坐标构造归约，而不是直接假设。对目标坐标 `ell`，归约者
把 `m_u,b=Encode_T(w_u*k_u,b)` 交给 TACITA 的等和 challenge，自行生成其它坐标
的独立参数、密文、聚合密文和 partial-decryption transcript；再用双模式 NIZK 的
`SimProve` 处理包含 challenge ciphertext 的 `R_eq`。若坐标之间共享 hidden setup、
RO 状态、公开线性 opening 或 partial decryption 依赖其它坐标秘密，则该 lifting
失效，`Joint-AO` 只能作为独立联合数据面假设。

在 TACITA 中，令 `ek_ell=(C_ell,Z_ell)`，`A_ell`、`b_ell` 分别为其公开矩阵和
向量；对 witness randomness `sd_u,ell` 令
`s_u,ell=RO(ctx_sid||ell||sd_u,ell)`，则关系的密文方程为：

```text
ct_u,ell = (tag_sid,ell,
            s_u,ell^T * A_ell,
            s_u,ell^T * b_ell + Encode_T(w_u*k_u)).
```

聚合对第二、第三分量逐项相加并要求 tag 一致，部分解密绑定聚合密文的
ciphertext-specific component。故 `R_eq` 需要 ROM-aware NIZK relation；若 NIZK
电路不能查询该随机预言机，必须将 oracle values 纳入 statement，或把 `Joint-AO`
作为独立数据面假设。

还需单独通过 `SE-NIZK compatibility gate`：模拟 CRS 必须与真实 CRS 不可区分，
`SimProve` 必须能对 hybrid 中暂时为假的 `R_eq` statement 生成可验证 proof，
并支持并发多定理 transcript 及 TACITA/NIZK 随机预言机的组合。Choudhuri 等的
`Setup/SimProve` 接口是候选依据，但不能仅凭接口名称推出 arbitrary-statement
simulation；否则保留独立 `Joint-AO` 假设。

TACITA 的 modified STE extended CPA 只直接给出固定 coordinate 的等和消息、
聚合 ciphertext 和聚合 partial decryption 安全；它没有定义跨 coordinate 的
同一 mask key 关系，也没有给出上述双模式证明模拟。因此，TACITA 是
`Static-AO_ell` 的坐标级基线，`Joint-AO` 仍是条件组合定理，不能作为 TACITA
原文的无条件推论。

#### 13.12.1 `Recovery-Lifting Barrier`：普通备份只会把问题递归一层

TACITA-style `Static-AO` 并不能被“给每个 `sk_i` 再做一次 VSS/DPSS 备份”直接提升为长期方案。考虑任意黑盒恢复包装器，它把静态解密状态 `sk_{ell,i}` 编码成长期可见的备份对象 `bk_{ell,i}`，并让某个恢复访问集 `D_rec` 的当前状态可在节点治愈后恢复同一个 `sk_{ell,i}`。若 `bk_{ell,i}` 在坐标 `ell` 退休后仍可取得，且 `D_rec` 的恢复能力没有按 `ell` 穿孔，则未来暴露 `D_rec` 的全部当前状态即可重新运行恢复算法，得到已删除的 `sk_{ell,i}`。对足够多的 `i` 重复后形成旧解密访问集，直接违反 privacy finality。

**Puncture-Recursion Lemma（条件版）。** 对 stable public key、durable backup transcript 和未来 recovery-authority exposure 的黑盒包装，no-resurrection 要求至少满足一项：

1. recovery authority 本身支持按坐标/`sid` 的不可逆穿孔；
2. 每次退休通过带 frontier 的交互使所有旧 backup 在密码学上失效；
3. 使用每坐标独立恢复能力并随坐标删除，承担线性坐标状态；
4. 放弃 stable key、公开归档或未来全体当前状态暴露；
5. 引入 TEE、不可回滚存储等额外信任。

证明是直接的 replay：保存 `bk_{ell,i}`，等待退休和未来暴露，再以未穿孔 recovery authority 调用合法恢复算法。该结果不声称排除所有非黑盒压缩恢复；它精确说明 **static aggregate opening + ordinary DPSS is not a construction**。若用一个全局短恢复密钥压缩 `n*m` 个独立备份，该短密钥本身就成为必须按退休集合穿孔的新 capability，问题没有消失。

#### 13.12.2 `Repair-Closure Characterization`：恢复会改变隐私访问结构

`Puncture-Recursion` 还能提升为一个精确的访问结构刻画。对固定退休标签 `sid`，令 `Gamma_rec(i)` 表示能够从归档 backup 与 helper 当前状态中恢复节点 `i` 的旧 capability 的恢复访问集族。对任意初始旧能力持有者集合 `X`，定义最小恢复闭包：

```text
Cl_rec(X) = least Y such that
            X subseteq Y, and
            if R subseteq Y for some R in Gamma_rec(i), then i in Y.
```

这里允许迭代恢复：新恢复出的状态若又能帮助恢复其他节点，就继续加入闭包。退休集合为 `A`、退休前被保存完整状态的集合为 `B` 时，未来全体当前状态暴露后的初始集合仍是

```text
X_B = (P-A) union B.
```

**Repair-Closure Theorem（条件版）。** 若所有生成旧 capability 的合法路径都由 `Gamma_rec` 覆盖，且底层密码学阻止未授权伪造，则 privacy finality 当且仅当

```text
for every admissible B:
    Cl_rec((P-A) union B) notin Gamma_dec.
```

必要性由 matching attack 给出：敌手按闭包定义依次恢复节点，直到得到某个 `D in Gamma_dec`，再对归档 ciphertext 解密。充分性则由“任何可生成旧 capability 都在闭包内”和底层不可伪造性推出。Robust-Hitting 正是 `Cl_rec(X)=X`，即退休后的恢复边已全部被 tombstone 删除时的特例。

正式化后需要使用 typed capability hypergraph，而不只把节点作为顶点：direct share、recovery-polynomial share、DPRF capability、backup、recovery transcript、channel key 和 handoff output 是不同类型。必要性方向还要求 **Composable Edge Realizability**，即整条闭包 derivation 能在同一 admissible execution 中联合实现；若 edge set 只是保守 over-approximation，则闭包安全仍是充分条件，但不再声称必要。

另一个关键修正是 `CheckInstall` 不足。若退休前生成的 `M_old` 与未来暴露的 receiver/channel state 能离线导出旧 share，则即使正确节点拒绝安装，攻击者也已获得 capability。RCL 必须同时提供 generation authorization、post-finality transcript extraction resistance 和 stale-install rejection。完整定义与证明见 `repair-closure-theorem-draft.md`。

一个重要推论是 **repair amplification**。若任意 `q_rec` 个 helper 的旧恢复状态都能恢复每个目标节点，而数据解密门限为 `q_dec`，令

```text
x = n-a+min(a,b).
```

当 `x>=q_rec` 时，恢复闭包扩张为全体 `P`，无论 `q_dec` 多大都失去隐私；当 `x<q_rec` 时闭包不扩张，仍需 `x<q_dec`。因此精确条件是

```text
n-a+min(a,b) < min(q_dec,q_rec).
```

在有用区间 `a>=b` 中，

```text
a >= n-min(q_dec,q_rec)+b+1.
```

这说明恢复门限若低于解密门限，会把系统的有效隐私门限直接降到 `q_rec`。在 `n=3f+1`、`b=f` 且异步退休活性要求 `a<=2f+1` 时，不仅 `q_dec`，连 `q_rec` 也必须至少为 `2f+1`。因此“用更低门限让 cure 更容易”会与长期 privacy finality 发生紧冲突。对 target-specific 或加权恢复，主定理仍用闭包而非简单的两个门限计数。

#### 13.12.3 无持久备份的交互式恢复：最小正向见证

`Puncture-Recursion` 并非一般不可能性；它指出必须让恢复能力与当前状态一起消失。一个最小逃逸方案是 **current-share-only repair**。要求每个 coordinate `ell` 的 `Static-AO` 解密状态由可验证线性 sharing 持有，并提供安全线性份额修复 `LSR`：目标节点 `i` 的份额只能由某个 `R in Gamma_rec(i)` 使用当前 `ell` 份额和新鲜、事后擦除的临时随机性恢复；系统不保存一个在未来仍可解密 `sk_{ell,i}` 的 durable backup。

在 `BF-RPTA` 中，节点对 `ell in I_sid` 执行退休时必须原子删除：

```text
direct decryption share
+ coordinate-local repair metadata
+ unfinished LSR state
```

恢复节点只对 `T_req[ell]=0` 的坐标启动 `LSR.Repair(rid,i,ell,T_req)`，所有帮助消息绑定 `rid/i/ell/T_req`；`T_req[ell]=1` 的坐标没有恢复接口。若 repair 与 decryption 使用同一 `q`-out-of-`n` 当前份额访问结构，且 `A in H_b(Gamma_q)`，则退休坐标的初始集合 `X_B` 小于 `q`，无法触发任何恢复边，所以 `Cl_rec(X_B)=X_B`；未来坐标仍有至少 `n-f>=q` 个当前份额，因而可以修复。由此得到一个直接的 `RCL` 可行性见证。

该见证的代价不能隐藏：节点长期状态为 `O(m)` 个 coordinate states；修复一个节点需要对所有仍活跃坐标执行或批处理 `LSR`，通信为 `O(m*C_LSR(n))`，而一次退休只本地删除 `k` 个坐标并发送常数个确认。朴素逐坐标 VSSR/AVSS 已足以证明可行性，因此不能作为主要构造创新。值得继续的正向问题只有两个：在实例内累计 `f` 个 adaptive corruptions 下给出完整异步组合证明；或用 packed/batched repair 把恢复通信显著低于逐坐标基线，同时保持 coordinate-local erasure。

#### 13.12.4 条件近最优性：近似 frontier 的空间下界

`BF-RPTA` 的 `Theta(R log(1/epsilon))` 不只是任选参数。将 coordinate-deletion 类方案抽象为一个 one-sided approximate-membership frontier：对至多 `R` 个退休 `sid` 不允许 false negative；对未退休 `sid`，误判为已退休的概率至多 `epsilon`。标准计数下界给出，在标签宇宙足够大时，任何这样的 frontier 表示至少需要

```text
R log_2(1/epsilon) - O(R)
```

bits。Bloom frontier 使用 `Theta(R log(1/epsilon))` bits，因而在该模型内常数因子近最优。若每个 frontier 坐标必须携带一个不可替代的 threshold decryption state，则同样得到 `Omega(R log(1/epsilon))` 个功能坐标；这一步是 coordinate-deletion 模型下界，不是对任意 puncturable encryption 的无条件密钥长度下界。

至此，最窄且有理论深度的研究问题变成：**能否构造一个使退休标签的 repair closure 退化为 identity、同时对未来标签保持异步可恢复的 `RCL`，并在 exact 状态、退休交互和未来 liveness error 三者间达到匹配权衡？** TACITA 可作为数据面基线；逐坐标 `LSR` 是可行性基线，主创新必须落在长期状态定理或低于该基线的恢复复杂度。

### Proof-gap resolution: 主定理与实例化定理分层

本轮审计把缺口从主线构造中隔离出来。`Joint-AO` 的主游戏直接挑战完整的
跨坐标数据面 transcript，因此 `BF-RPTA` 的长期隐私定理不再依赖“逐坐标替换
时可生成假 `R_eq` proof”这一未验证前提。主定理明确采用：

```text
Privacy-Finality(BF-RPTA)
  <= Joint-AO + RCL-Sim/AO + Robust-Hitting + correctness.
```

只有在额外给出 `DM-SE-NIZK^{RO,eq}` 后，才将 `Joint-AO` 进一步归约为：

```text
2*Adv_DM-SE-NIZK^{RO,eq}
  + sum_ell Adv_Static-AO_ell^aux
  + negl(lambda).
```

该接口必须支持模拟 CRS、任意 statement 的可验证 `SimProve`、并发多定理
simulation-extractability，以及与 TACITA programmable RO 的联合安全。Choudhuri
等的 weak SE-NIZK 定义目前只能作为候选，不足以关闭这个 gate。由此形成清晰
的 go/no-go：主线理论可以继续证明；TACITA 的逐坐标具体化单独作为条件结果，
不能反向成为长期移动腐化安全的隐藏前提。

### 13.13 精确路线与近邻能力矩阵

Sun--Sakzad--Steinfeld--Liu--Gu 的 PKC 2020 public-key puncturable KEM 提供另一条重要基线。其 generic puncture 采样新 master component `msk_i`，把 distinguished component 更新为 `msk_0-msk_i`，并追加只与 punctured tag `t_i` 关联的 restricted key。它支持 exact puncture 和当前 punctured-key exposure，但所谓 compact punctured key 仍是 `3(i+1)` 个群元素，即随实际穿孔次数 `i` 线性增长。

若要阈值化这条路线，`msk_i` 必须由异步随机 sharing 产生，各节点只能得到 share；随后还要在不重构 `msk_i` 的条件下生成 tag-restricted key shares。这个过程天然需要交互或预处理相关随机性。更关键的是，该工作是 KEM：它不提供对不同客户端 ciphertext 的 `Eval`，所以不能直接输出唯一加权聚合 key。把它写成“现成 exact RPTA”是不成立的；它只证明 exact puncture 可以通过“每次追加新秘密 component”绕开固定维线性映射下界。

| 工作/原语 | 聚合唯一线性值 | threshold/mobile | puncture 后全状态暴露 | cure/repair | 状态代价 |
|---|---:|---:|---:|---:|---:|
| BFE 2021 | 否 | 否 | 是，单接收者 | 否 | `Theta(R log(1/epsilon))`，有 liveness error |
| PKC 2020 modular PPE | 否，KEM | 否 | 是，单接收者 | 否 | exact，`Theta(R)` punctured-key components |
| DFKHE-based PE | 否 | 否 | 是，单接收者 | 否 | 非线性 trapdoor delegation，非 share-local |
| TACITA modified STE | 是，静态 one-shot 等和游戏 | threshold，静态腐化 | 否 | 否 | 常数 ciphertext/share，不含长期状态 |
| BEAST-MEV | 否，恢复批内每条消息 | 是，静态模型 | 否；穿孔客户端 PRF key | 否 | batch-oriented |
| LightBEAT 2026 | 否，恢复批内每条消息 | 是，full protocol 为静态腐化 | 否；HIDP 穿孔客户端公开 PRF key | 否 | setup/storage `O(N log^2 N)` |
| Silent Setup STE | 否，门限解密消息 | 静态目标委员会；支持 multiverse | FSE 依赖周期更新 | PCS 通过重采样并发布新 `pk/hint` | 不保持稳定公共键 |
| VSSR 2019 | 不处理聚合输出 | 单 commitment 累计 `<k` 暴露/贡献来源 | 否 | 是，恢复原始 share | recovery polynomial + 全局 DPRF；非 proactive |
| WBTE 2026 | 打开选中批次明文，不是 aggregate-only | 是，静态权重模型 | 否 | 否 | batch-oriented |
| APSS/DyCAPS/bDPSS | 不处理客户端聚合隐私 | 是 | 保持同一长期 secret | 是 | epoch/handoff-oriented |
| `BF-RPTA` compiler | 是，条件于 `Static-AO + RCL` | 是 | 是 | 是 | `Theta(R log(1/epsilon))`，误差只在未来 liveness |

截至 2026-09-10，TACITA 已覆盖静态聚合开放核心，LightBEAT 也覆盖 epochless BTE 中的高效客户端 PRF 穿孔，因此不能再写“没有直接近邻”。但 LightBEAT 全文确认它没有穿孔或恢复委员会 threshold state，`Combine` 逐条输出消息，full protocol 只证明 static corruption。当前未发现的是同时覆盖 `aggregate-only + mobile current-state exposure + committee-state puncture + cure/repair + asynchronous frontier` 的构造。这个记录只是覆盖审计，不是新颖性证明。

由此得到更稳定的论文结构：

1. **定义与刻画：** privacy finality、Robust-Hitting、Repair-Closure、retirement-liveness sandwich；
2. **不可能性/下界：** causal-fence necessity、repair amplification、degree growth、固定维 exact local puncture 的 `Omega(M)` 下界；
3. **黑盒分离：** TACITA-style 静态数据面经普通备份提升时出现 Puncture Recursion；
4. **可行性与近最优性：** 从 `Static-AO + RCL` 到 `BF-RPTA` 的 compiler，配合 one-sided approximate-membership 空间下界；
5. **开放的 exact 点：** 将 PKC 2020 式随机 secret splitting 做成 aggregate-compatible、异步可恢复的 threshold primitive。

首篇工作不应重新实现 TACITA，也不应同时承诺 exact puncture。最小闭环是：正式化 `RCL`、证明 Repair-Closure/Puncture Recursion 与空间下界、给出 BF-RPTA 的匹配长期恢复协议。若 `RCL` 最终只能逐坐标调用现成 VSS 且没有新的自适应异步证明或复杂度收益，则保留理论结果，构造降级为可行性见证。

### 13.14 新全文裁决：恢复能力必须进入穿孔边界

VSSR 给出了目前最具体的恢复基线，也暴露了不能忽略的状态边界。对一个 commitment `c`，可恢复状态不只是直接份额 `u_i(c)`，还包括 recovery-polynomial shares、DPRF secret share、公开 nonce `r` 和尚未完成的 recovery transcript。VSSR 的标准安全游戏允许 compromise、contribution 和 recovery query 自适应发生，但对每个 commitment 把可用来源累计限制为 `<k`；这不是跨刷新周期最终腐化全体当前状态的 mobile security。论文也明确说明 VSSR 只处理 share phase，proactive share recovery 留作 future work。

这里不能过强地断言“一个全局 DPRF 必然复活所有坐标”。DPRF share 单独不能重构旧份额；攻击成立需要它与该坐标仍存活的 recovery-polynomial state 或可重放 backup 结合。正确的黑盒分离是：

> **Recovery-State Localization Barrier（条件版）。** 若 ordinary recovery 黑盒对标签 `sid` 的恢复关系可由持久全局状态 `G` 与标签局部状态 `L_sid` 重新生成一个解密 capability，而退休操作只删除 direct share、没有使 `G` 对 `sid` 穿孔，也没有让满足 Robust-Hitting 的节点删除全部 `L_sid`，则未来状态暴露与合法恢复贡献可把 `sid` 加回 recovery closure，因而 wrapper-level tombstone 不足以推出 `PF_sid`。

因此只有三条干净出口：

1. **coordinate-local deletion：** 退休时原子删除 direct share、recovery-polynomial share、未完成恢复状态以及所有 `sid`-local backup；共享 DPRF 可以保留，但必须证明它在缺少这些局部状态时不能扩张 `Cl_rec`；
2. **puncturable recovery authority：** 让共享恢复权本身按无序 `sid` 穿孔，并把其状态安装绑定到单调 frontier；
3. **rekey/epoch：** 生成新恢复世代，使旧材料失效，但这放弃稳定键或无全局 epoch 的目标。

这给论文一个比“VSSR 不支持 mobile adversary”更强的叙事：**任何用于容错的恢复层都必须接受与数据解密层相同的 privacy-finality 审计；删除数据份额而保留可生成它的恢复能力，等价于没有删除。** 其形式化对象仍是 Repair-Closure，而不是再发明一个前向安全定义。

#### 13.14.1 动态委员会：把 handoff 作为恢复边，而不是另起一套协议

首篇定理仍以固定身份委员会中的移动腐化和 crash/cure 为主，避免同时承担完整 membership 协议。动态加入、退出和换届作为严格扩展，通过把跨配置 handoff 加入同一个能力图处理。令 `cfg_0,cfg_1,...` 为配置序列，`E_rec` 是同配置恢复边，`E_ho` 是跨配置 handoff 边，则要求：

```text
Cl_{rec+ho}(X_sid) = closure under E_rec union E_ho

for every retired sid and admissible future corruption B:
Cl_{rec+ho}(X_sid union B) notin Gamma_dec(sid).
```

匹配协议纪律是 `Project(T) -> Handoff(cfg_old,cfg_new,live coordinates only)`：旧委员会先按已认证 frontier 投影并删除退休坐标，再只对 live coordinates 执行 DPSS/ADKR handoff；每条消息绑定 `cfg_old/cfg_new/rid/T_req`，新委员会的 `CheckInstall` 拒绝任何被 frontier 支配的坐标。BEAST-MEV 只笼统指出 committee churn 可组合 proactive secret sharing，这并不证明 project-before-handoff 或跨配置 privacy finality。

动态成员的真正新增定理应是 **Handoff-Closure Preservation**：若旧配置满足 `PF_sid`，且每条 handoff 边只从 projected live state 出发并由目标配置验证同一或更高 frontier，则换届后 `PF_sid` 保持；反之，任一从 pre-projection backup 出发的合法 handoff 边都会进入 `Cl_{rec+ho}`，形成匹配复活攻击。每个未完成 handoff 实例仍必须有累计腐化上界；只限制瞬时腐化数在完全异步网络中不够。

当前优先级因此是：先证明固定委员会的 `Recovery-State Localization + Repair-Closure`，再把 dynamic membership 写成 closure-preserving compiler。若动态部分只需调用现有 DPSS，则作为应用扩展；只有 Handoff-Closure 定理和 project-before-handoff 的必要性/充分性产生新结果时，才提升为主贡献。

### 13.15 本轮执行后的主线裁决：FGSR

本轮 VSSR 与 APSS/DyCAPS/Optimistic-DPSS 对照后，候选正向原语统一命名为 **Frontier-Gated Selective Resharing (FGSR)**。它不是新的 VSS 术语包装，而是对现有 resharing 子协议增加三个必须同时证明的约束：

```text
selective live-coordinate resharing
state-complete repair output
frontier-closed transcript extraction
```

已有工作的分工如下：

| 基线 | 能提供的部分 | 不能直接提供的部分 |
|---|---|---|
| APSS | 异步刷新、旧 share 删除 | mobile、selective `sid` repair |
| DyCAPS | mobile/dynamic handoff、forward-secure channels | 无序 application frontier、future full-state closure |
| Optimistic DPSS | 加密 handoff、验证承诺、工程效率 | retired transcript finality、state-local selective deletion |
| VSSR | 低开销一次性缺份额恢复 | repair closure、state completeness、group transcript safety |

FGSR 的首个证明目标固定为单 coordinate、固定委员会和 `n=3f+2`：

```text
q_dec = q_rec = 2f+1,
target-excluded correct responders = 2f+1,
history budget b = f.
```

这里的 novelty 不是重新发明 bivariate resharing，而是证明：在无序 `sid` retirement 和未来全状态暴露下，只有把 application-level frontier 投影到每条 resharing edge，并让 repair 输出保持 state complete，proactive resharing 才能成为 privacy-final aggregation 的合法状态层。动态委员会留作同一闭包定理的后续扩展。

### 13.16 One-Shot FGSR 的最小审计接口

当前构造不采用 DyCAPS 的四阶段 handoff。对固定委员会中的一个 live
coordinate `ell`，令当前 sharing 为 degree-`d` 多项式 `F`，节点 `h` 持有
`z_h=F(h)`。一次 repair instance `rid` 只执行以下一次 share-to-share
resharing：

```text
Authorize -> Parallel Reshare -> Aggregate/Install/Erase
```

在 `n=3f+2`、`b=f` 的首个参数点，取 `d=2f` 和
`q_dec=q_rec=2f+1`。target 被排除后，仍有恰好 `2f+1` 个正确旧节点，因而
可以形成不依赖 target 的共同 helper 集合 `H`。每个 `h in H` 产生 fresh
degree-`d` 多项式：

```text
f_h(X) = z_h + a_h,1 X + ... + a_h,d X^d.
```

异步 VSS/AVSS 只向 receiver `j` 提供点值 `f_h(j)`；所有节点依据同一个
availability-certified `H` 和 `lambda_h=LagrangeCoeff(H,h,0)` 安装：

```text
z'_j = sum_h lambda_h f_h(j),
F'(X) = sum_h lambda_h f_h(X).
```

因此 `F'(0)=F(0)`，且 `z'_j` 是下一次 repair 可直接使用的普通 current
share。构造的性能目标只是删除不必要的 bivariate/reduced-state 阶段；朴素
实现仍按每个 coordinate 产生 `O(n^2)` 通信，packed/batched VSS 不进入首个
安全定理。

这里的 `H` 不是本地“先到先得”集合。其证书必须同时表明：helper 的旧
share commitment 有效、helper 已完成本次可用的 VSS/AVSS 输入、proposal
绑定同一 `(rid,ell,cfg,T_req,H)`。validated ACS 对这些证书达成唯一结果。
这样 Byzantine helper 即使提交了合法但不完整的本地 proposal，也不能被仅凭
一个 commitment 纳入一个会阻塞 receiver 的 `H`。可用 `AvailCert_h` 表示
`P^-` 中至少 `2f+1` 个 `READY(rid,ell,h,C_h)` 签名，且 READY 只能在本地
deliver 认证点值后产生；底层 AVSS 必须满足一个正确 receiver deliver 后所有
正确 receiver 最终 deliver 同一点值。若协议实例化允许 Byzantine dealer 完成
AVSS，也必须使用该 all-correct-receiver completion/propagation 语义，不能把
“发送 commitment”误作 availability certificate。

一个最小 wrapper 是在 `P^- = P \ {target}` 上运行 validated ACS：
`|P^-|=3f+1`，先输出 `|V|>=2f+1`，再由所有节点按 descriptor 的确定性顺序
取 `H=Canonical_{2f+1}(V)`；AVSS 的 receiver 集仍包含 target。helper 仅
在其 AVSS instance 完成后提交 descriptor。这样 `H` 可以包含 Byzantine
dealer，但每个入选 instance 都必须满足：

```text
AVSS-Complete(h) => every correct receiver eventually obtains
                   an authenticated f_h(j) consistent with C_h.
```

活性来自 `2f+1` 个正确非 target 节点最终完成 AVSS，满足候选 ACS 的
`n'-f=2f+1` 终止条件；target 不参与 ACS 提案，却继续作为 AVSS receiver。
这使 target exclusion 与 Byzantine availability 分离，且不依赖识别诚实
身份。

首个 proof-friendly commitment 选择为 Pedersen 系数承诺加零知识
opening-equality proof：descriptor 证明 `Com_F(h)` 与 `Com_{f_h}(0)` 的消息
相等，但不公开旧 share `z_h`。KZG 仅作为后续压缩方向，需另行补充
zero-knowledge opening-equality 关系证明。

因此 `F'` 的状态生命周期必须写入安全定义：`A_ell` 中已确认节点删除
`F'`，但异步活性允许 `U_ell=P\A_ell` 暂留最新 `F'` 或 pending state；这些
残留状态必须进入 `Cl_rec`。首个参数点要求 `|A_ell|>=n-f=2f+2`、
`|U_ell|<=f`，并与最终 generation interval 的暴露满足
`|U_ell|+|B_{ell,ret}|<=2f<q_rec=2f+1`。此前的 `|B_ell|<=f` 是 session-lifetime
保守基线，不是当前长期移动腐化模型。
若所有节点都保留 `F'`，全体状态暴露可直接得到 `F'(0)=F(0)`；因此主定理
依赖 residual-state closure，不依赖全员同步擦除。

常数项绑定也是独立的安全接口。对每个 helper，VSS commitment 之外必须证明：

```text
f_h(0) = z_h,
z_h is the committed current evaluation of F at h.
```

可用现有 commitment 上的 equality proof（例如同一群上的 Schnorr/关系证明）
实现；本主线不把该证明包装成新密码学原语。只证明 `f_h` 是合法多项式不够，
因为恶意 helper 可以构造一个常数项不同的合法多项式，直接破坏 secret
preservation。

FGSR 的 closure proof 必须沿 typed capabilities 检查，而非只检查安装结果：

```text
receiver sees: one encrypted point f_h(j)
helper retains: no coefficient vector after send/commit/cancel
receiver retains: no plaintext point or ephemeral decryption key after install
retirement: no new generation, extraction, or installation edge for ell
```

对于在 retirement 前已经授权、但尚未安装的 `rid`，instance order 必须由
validated agreement 决定。若 retirement 先于 install，所有 pending plaintext、
helper coefficient 和 receiver ephemeral key 都被擦除，迟到 ciphertext 只能
被拒绝；若 repair 先完成，则安装证书必须携带不低于 `T_req` 的 frontier。单纯
拒绝 stale output 不足以证明隐私，因为尚未安装的 recovery transcript 仍可能
在未来状态暴露后解封旧 share。

因此首个 reduction 分成三个可证伪的引理：

1. **Common-H availability：** ACS 输出唯一 `V`，所有正确节点从同一 `V` 确定性
   截取 `H=Canonical_{2f+1}(V)`，且 `H` 中的每个输入对所有正确 receiver 可用；
   target 排除后在 `n=3f+2` 下仍有活性。
2. **Share-to-share secrecy：** 单个 receiver 的点值、归档密文和未来全状态暴露
   不能合成 retired `F_ell(j)`，除非该信息已由历史 corruption budget `B`
   计入；证明中显式依赖系数/明文/临时密钥擦除。
3. **Retirement closure：** retirement 支配同一 coordinate 的 pending 和迟到
   实例，且新 `F'` 只能从未被 frontier 关闭的 live coordinate 生成；这使
   `Cl_rec` 不再包含 retired coordinate 的授权解密集合。

这三个引理若成立，FGSR 才能作为 `Repair-Closure` 的 state-complete 边；若
第二个引理失败，失败边界将明确落在“现有 VSS + private channel 不能提供
future-state transcript security”，而不是继续用前向安全加密掩盖该缺口。

### 13.17 Cross-Coordinate Affine Coupling 审计

BF-RPTA 的多个 coordinate 若共同编码一个 mask key，单坐标的 transcript-hiding
不能直接推出 aggregate-only 安全。首版采用以下最小隔离接口：每个 coordinate
使用独立 degree-`d_ell` sharing randomness；跨坐标只证明同一明文关系；证明为
zero knowledge，且不公开 share opening 或高阶系数关系。

对坐标 `ell` 和第 `r` 代，令 `E_ell` 覆盖所有未来可见的 direct/subshare
positions，满足 `|E_ell|<=d_ell`，并定义：

```text
L_ell(X) = product_{j in E_ell}(X-j) / product_{j in E_ell}(-j),
F^r_{ell,Delta}(X) = F^r_ell(X) + Delta*L_ell(X),
f^r_{ell,h,Delta}(X) = f^r_{ell,h}(X)
                         + Delta*L_ell(h)*L_ell(X).
```

对所有 coordinate 使用同一个 `Delta`，对每个 coordinate 使用自己的 `L_ell`。
则每个 `E_ell` 上的可见点不变，helper 的 `f(0)=F(h)` 关系不变，且 Lagrange
递归保持每个坐标的秘密统一平移 `Delta`。若各坐标原本共享同一 mask key，
相等关系也保持；这说明跨坐标 consistency proof 在 zero knowledge 且不产生
opening 边时，不会自行消灭 hidden-helper 的模拟自由度。

该审计只覆盖线性 share layer。以下任一项都会产生新的未建模边，不能由本引理
自动排除：共享高阶系数、公开跨坐标线性 opening、非 zero-knowledge consistency
proof，或 Static-AO transcript 能把多个坐标 partial shares 聚合为一个新的
decryption capability。正式主定理必须把这些边分别归入 `Gamma_dec^cap` 或
证明其不可实现；否则只能声称 FGSR 的 coordinate-local closure。

### 13.18 State-layer/data-plane noninterference 审计

`RCL-Sim/AO` 需要把公开视图分解为：

```text
View_b = (DataView_b, StateView, PublicContext).
```

`DataView_b` 包含所有依赖 challenge key vectors 的 ciphertext、aggregate
ciphertext、partial decryption 和 consistency proof，并由 `Joint-AO` 覆盖；
`StateView` 包含 repair、handoff、current-state exposure 和 stale-state
rejection，其分布必须与 challenge bit 无关。`CapSafe` 只保证没有完整的未授权
opening，不能替代这一非干扰条件。

BF-RPTA 的首版坐标化状态满足所需的接口边界：RCL 只存储和修复委员会
threshold decryption shares；客户端 mask key 不进入 repair polynomial、handoff
state 或 frontier metadata。若某个 partial decryption 或 proof 依赖具体客户端
ciphertext，它必须从 `StateView` 移入 `DataView_b`，并在 `Joint-AO` 游戏中一次性
挑战。任何未归类的跨层输出都应视为未建模 capability edge，不能进入主定理。

### 13.19 上下文绑定的因子化要求

`sid`、权重、frontier、generation 和坐标集合属于 pre-challenge context；
`H_ct`、`H_out`、challenge-dependent partial decryption 以及 aggregate certificate
属于 `DataView_b`。因此 `Puncture/Recover/CheckInstall` 只能读取前者；若它们
读取后者，相关输出必须随同数据面 transcript 进入 `Joint-AO`，不能继续假设
`StateView` 与 challenge bit 无关。该拆分关闭了“先用 ciphertext 生成 `CC_sid`，
再把 `CC_sid` 当作独立状态输入”的循环证明路径。

### 13.20 One-Shot FGSR simulator 审计

One-Shot FGSR 的单步 simulator 必须按对象归类，而不是笼统引用 VSS
correctness。固定 repair instance rid、coordinate ell 和 generation r；
simulator 只接收 pre-challenge context、公开承诺、Common-H 证书和 residual
typed state，不接收未暴露的旧 current share。

| 对象 | 必须满足的条件 | 失败含义 |
|---|---|---|
| authorization、Common-H、AvailCert | 只依赖 frontier、generation 和公开证书 | 证书携带秘密或可用性不足 |
| helper commitment、equality/VSS proof | 未暴露 helper 可 hiding/ZK 模拟；常数项 equality 可验证 | simulator 需要旧 share |
| receiver ephemeral key 与 subshare ciphertext | key 与客户端数据独立；擦除后 ciphertext 可 IND-CPA 替换 | 未来状态可解封旧 point |
| exposed plaintext 与 Byzantine helper state | 完整计入 B_{ell,r} 历史视图 | 暴露集合被低估 |
| U_ell 的 pending/live state | 完整进入 residual closure，不得假设已擦除 | closure 漏掉未来可见状态 |
| F'、install、erase、迟到输出 | generation/frontier 绑定，stale output 拒绝 | 旧 transcript 可跨代回滚 |
| partial decryption、H_ct/H_out、aggregate certificate | 统一归入 DataView 并由 Joint-AO 覆盖 | StateView 与 challenge bit 相关 |

单步 hybrid 顺序是 ciphertext replacement、proof simulation、generation-local
affine completion、DataView 联合替换。自适应 B_{ell,r} 由完整前缀视图决定；
终端退休代使用 U_ell union B_{ell,ret}。若出现未归类对象，定义
Adv_Uncovered-Edge；不能把它隐藏在 RCL-Sim/AO 或 CapSafe 中。该审计是
定理稿 19.24 的具体实现入口，也是 19.22 长期组合推论的必要前提。

### 13.21 具体密码学实例化审计

19.25 的首个实例选择 Pedersen 系数承诺、常数项 equality proof、opaque
AVSS、receiver-ephemeral PKE 和原子擦除。审计结论如下：

| 接口 | 可接受条件 | 不能直接推出的性质 |
|---|---|---|
| Pedersen coefficient commitment | commitments 隐藏；equality proof 可零知识模拟 | commitment binding 不等于 proof simulation |
| helper equality | 证明 f_h(0)=F(h)，不公开旧 share | 只证明多项式合法不足以保持 secret |
| AVSS delivery | 公开 transcript 不暴露 point/coefficient；正确 receiver deliver 推动全体正确 receiver deliver | 普通 AVSS agreement 不等于 opaque delivery |
| receiver PKE | ephemeral key 独立于客户端 key；对应 secret 在 commit/cancel/install 后擦除 | IND-CPA 不能覆盖未擦除 receiver |
| state transition | rid、generation、frontier 绑定；stale output 拒绝 | CheckInstall 不能阻止离线 transcript extraction |

满足这些接口后，所有输出都落入 StateView、历史/残余 closure 或 Joint-AO
DataView，Adv_Uncovered-Edge 才能记为零。否则应保留该误差项，不把具体
FGSR 写成已经完成的长期安全实例。

### 13.22 文献接口的最终裁决

APSS/ACSS 的转写文档定义了私有 authenticated channel 上的异步 share
delivery、公共 Feldman polynomial commitment 和所有正确节点最终获得一致
share；但 APSS 的 adversary 是 static Byzantine，协议目标是全局 refresh，
不是本文的 target-excluded selective repair。它可作为 availability 基线，
不能直接关闭长期 generation/frontier 证明。

adaptive PVSS 的转写文档把 transcript 明确写成公开 commitment、每个 receiver
的 public-key encryption 和 NIZK proof，并在模型中明确“不假设 secure erasures”。
因此它适合证明 one-shot adaptive PVSS，却不能覆盖未来暴露 receiver secret
后对历史 ciphertext 的解封。直接替换会使 Adv_Uncovered-Edge 非零。

DyCAPS 提供 forward-secure private channels、移动 epoch 和显式擦除，但其
handoff 依赖 bivariate state 和 epoch-local 过程。当前只提取其 channel/erase
纪律，不复制四阶段 handoff；首个实例仍须单独证明 AVSS-opaque 和
generation-local closure。

最终接口收敛为：APSS-like asynchronous availability、Pedersen/equality
proof、receiver-ephemeral PKE 和 atomic erasure 的组合。任何公开 commitment
若能被后续 recovery 当作 scalar share 使用，都计入新的 capability edge。

## 14. 原文定位与参考材料

- Alexandru et al. 的异步 proactive VSS 定义与不存在性：`/tmp/changing-network-conditions.txt:1174`；延迟消息攻击：`:1259`；拒绝旧消息导致落后节点无法追赶：`:1296`；forward-secure channel / clock 条件：`:1317`。
- DyCAPS 的 local-event epochs、安全擦除、forward-secure channels 和 epoch-mobile 腐化：`/home/yzc/flagg/dycaps_2022_1169.txt:149`。
- bDPSS 的 epoch-start static corruption、旧状态不可访问和 local-clock handoff：`/home/yzc/flagg/optimistic_dpss_2025_880.txt:406`、`:466`。
- APSS 对旧份额删除与异步活性的处理：`/home/yzc/flagg/apss_keyrefresh_2022_1586.txt:531`。
- dynamic PSS 对相邻 epoch 重叠腐化计数的修正：`/home/yzc/flagg/dynamic_pss_2022_619.txt:3158`。
- Flamingo 的静态腐化集合跨所有轮次保持不变：`/tmp/flamingo.txt:157`。
- Aion 的部分同步聚合器网络及按轮恶意集合：`/home/yzc/flagg/Robust and Efficient Multi-Round Single-Mask Secure Aggregation Against Malicious Participants_by_PaddleOCR.md:153`。
- 2026 aggregatable PVSS 的单次 adaptive-total 模型、无安全擦除：`/tmp/apvss-2026-1100.txt:384`。
- Shoup 对 proactive adaptive threshold decryption 的多 epoch 证明仅作预期：`/tmp/adaptive-threshold-decryption.txt:995`。
- Das--Ren--Yang 的 corruption oracle 在整个游戏累计至多 `t`：`/tmp/adaptive-elgamal-2025-1477.txt:312`。
- OPA 的 static malicious 模型与短种子同态 mask：`/home/yzc/flagg/extract_One-shot_Private_Aggregation_with_Single_Client_Interaction.txt:136`、`:466`、`:527`、`:541`。
- Buffalo 的短聚合键与客户端成本分解：`/home/yzc/flagg/Buffalo A Practical Secure Aggregation Protocol for Buffered Asynchronous Federated Learning.pdf_by_PaddleOCR.md:313`、`:400`、`:411`。
- 通用 puncturable encryption 的接口、穿孔后 key exposure 游戏和 DFKHE 含义：`/tmp/generic-puncturable-encryption-2020.txt:247`、`:278`、`:448`。
- Bloom Filter Encryption 的坐标删除构造、假阳性界和 key-size 讨论：`/tmp/bfe-2018-199.txt:727`、`:836`、`:159`；恶意环境下 Bloom filter 的直接基线见 Naor--Yogev 2015。
- PKC 2020 modular PPE 的随机 master-component splitting、线性增长 punctured key 和能力对比：`/tmp/public-key-puncturable-encryption-2020-126.txt:550`、`:1013`、`:1380`。
- TACITA modified STE 的接口、extended CPA 游戏、静态腐化边界和证明：`/tmp/tacita-2025-1579.txt:2505`、`:2528`、`:2557`、`:2576`、`:2610`。
- BEAST-MEV 中被穿孔的是每个客户端 PRF key；委员会聚合解密 `sum_i k_i` 后结合公开 punctured keys 恢复每条 `m_i`：`/tmp/beast-mev-2025-1419.txt:539`、`:604`、`:805`。
- LightBEAT 全文：静态委员会腐化假设见 `LightBEAT_Scalable_Epochless_Batched_Threshold_Encryption_via_Hierarchical_Identity-Based_Puncturing.pdf_by_PaddleOCR-VL-1.6.md:381`；公开 punctured key 见 `:437`；委员会 threshold-ElGamal shares 与逐条 `Combine` 见 `:598`、`:620`、`:722`；HIDP 的 adaptive identity 安全见 `:642`。
- VSSR 的 recovery polynomial/DPRF 构造见 `Efficient Verifiable Secret Sharing with.pdf_by_PaddleOCR-VL-1.6.md:122`、`:132`、`:331`；按 commitment 累计限制 compromise/contribution/recovery 来源见 `:230`；非 proactive 边界见 `:588`。
- Silent Setup 的 FSE/PCS 边界见 `Threshold Encryption with Silent Setup.pdf_by_PaddleOCR-VL-1.6.md:731`：FSE 依赖周期 key update，PCS 通过本地重采样并发布新 `pk/hint`。
- BEAST-MEV 的委员会 churn 仅作为 proactive secret sharing 组合建议，见 `usenixsecurity25-bormet.pdf_by_PaddleOCR-VL-1.6.md:374`；没有 project-before-handoff 或跨配置 privacy-finality 定理。

### 13.23 `Adaptive-Opaque-Repair` 接口桥

`F_AWF` 处理公开 frontier 和 capability 的吸收态，`RPTA` 处理当前状态上的
聚合与穿孔；二者之间的修复 transcript、endpoint state 和自适应暴露被单独抽象
为 `Adaptive-Opaque-Repair`（`AOR`）。对
`Q=(sid,ell,r,rid,i,T_req,C_ctx)`，接口提供
`Publish/Process/Expose/Retire/Recover/CheckInstall`。

`Publish` 在 send event 立即更新 `X_hist`，`Process` 只决定本地状态转移；退休前
腐化可以暴露 endpoint key、plaintext 和 opening，退休后只能暴露 post-erasure
state。模拟器只接收公开标签、承诺、opaque payload、receipt、frontier 和历史
暴露，不接收尚未暴露的 point、临时密钥或 recovery scalar。

`AOR` 的五项必要条件是：因果发布时间语义、opaque delivery、自适应状态一致性、
退休后的 endpoint/buffer 不可恢复旧 capability，以及所有 stale recovery/use
边的 frontier 吸收。由此可以把 `H0 -> H1` 写成

```text
Adv[H0,H1]
  <= sum_r Adv_AOR^mob(r)
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + R*negl(lambda).
```

这不是新的实现组件，而是审计接口。Janus、hbACSS、前向安全加密或普通 AVSS
只有在逐项映射这五个条件后，才能贡献到 `Adv_AOR^mob` 的具体归约；否则保留
对应优势项。

### 13.24 Complaint-Noninterference barrier

若 complaint 的公开内容与保留 ciphertext 一起能够导出 evaluation point 或
recovery scalar，则仅增加 tombstone 不能使该路径成为 opaque repair。退休后发送
的 complaint 必须在 `Publish` 阶段拒绝；退休前发送的 complaint 已经进入
`X_hist`，不能被擦除撤回；读取 challenge-dependent 数据的 complaint 分支必须
进入 `DataView` 和 `Joint-AO^mob`。

因此可接受的路径只有 metadata-only complaint（配 simulation-sound、无 individual
opening 的证明），或 live-only complaint（明确计入 pre-frontier exposure）。
原样 Janus complaint 和 hbACSS `IMPLICATE/RECOVER` 都不满足该接口。

### 13.25 `ZK-Invalidity` candidate

一种可能的正向路线是以 metadata-only 的零知识无效性证明替代公开
`KEYREVEAL`。证明需要同时满足 completeness、soundness、adaptive zero knowledge
和 `Joint-AO^mob` data-plane factorization；普通 NIZK 不能自动提供可验证的
decryption failure、异步 availability 或 challenge-dependent branch simulation。
因此该路线目前只贡献候选项 `Adv_ZK-Invalidity`，不能删除
`Adv_Complaint-Noninterference`。

本地 VSSR、SE-NIZK 和 Silent-Setup 文档都只覆盖恢复贡献验证、密文合法性或
CCA 部分解密绑定；它们没有给出不泄露标量的公开解密失败证明。故
`ZK-Invalidity` 仍是待构造接口，而不是已有原语的别名。

### References

- Alexandru, Blum, Katz, Loss. *State Machine Replication under Changing Network Conditions*. 2022.
- Hu, Zhang, Chen, Zhou, Jiang, Liu. *DyCAPS: Asynchronous Dynamic-committee Proactive Secret Sharing*.
- Yan, Xia, Devadas. *Shanrang: Fully Asynchronous Proactive Secret Sharing with Dynamic Committees*. ePrint 2022/164.
- Hu, Liu, Lu, Tang, Xiang, Zhang. *Optimistic Asynchronous Dynamic-committee Proactive Secret Sharing*. ePrint 2025/880; IEEE S&P 2026.
- Günther, Das, Kokoris-Kogias. *Practical Asynchronous Proactive Secret Sharing and Key Refresh*. ePrint 2022/1586.
- *Flamingo: Multi-Round Single-Server Secure Aggregation with Applications to Private Federated Learning*.
- *Robust and Efficient Multi-Round Single-Mask Secure Aggregation Against Malicious Participants* (Aion).
- Bacho, Chen, Loss. *Adaptively Secure (Aggregatable) PVSS from Standard Assumptions*. ePrint 2026/1100.
- Das, Ren, Yang. *Adaptively Secure Threshold ElGamal Decryption from DDH*. ePrint 2025/1477.
- Shoup. *Back to the Future: Simple Threshold Decryption Secure against Adaptive Corruptions*. IACR Communications in Cryptology, 2026. DOI: `10.62056/anxrxruc2`.
- Karthikeyan, Polychroniadou. *One-shot Private Aggregation with Single Client Interaction*. 2024 preprint; local transcript cited above.
- Taiello, Gritti, Onen, Lorenzi. *Buffalo: A Practical Secure Aggregation Protocol for Buffered Asynchronous Federated Learning*. CODASPY 2025. DOI: `10.1145/3714393.3726498`.
- Libert, Yung. *Adaptively Secure Forward-Secure Non-interactive Threshold Cryptosystems*. Inscrypt 2011 / LNCS 7537, 2012. DOI: `10.1007/978-3-642-34704-7_1`.
- Green, Miers. *Forward Secure Asynchronous Messaging from Puncturable Encryption*. IEEE S&P 2015. DOI: `10.1109/SP.2015.26`.
- Susilo, Duong, Le, Pieprzyk. *Puncturable Encryption: A Generic Construction from Delegatable Fully Key-Homomorphic Encryption*. ESORICS 2020. DOI: `10.1007/978-3-030-59013-0_6`.
- Shen, Chi, Lin. *Puncturable Fully Homomorphic Encryption Based on Bloom Filter*. PeerJ Computer Science, 2026. DOI: `10.7717/peerj-cs.3675`.
- *Dynamic Puncturable Encryption*. ACNS 2026, LNCS 16571. DOI: `10.1007/978-3-032-32560-0_4`. Local transcript: `/tmp/dynamic-puncturable-encryption-2026.txt`; covers dynamic access control, not threshold aggregate-only secure aggregation.
- Agarwal, Babel, Das, Gilakaye, Mondal, Pinkas, Rindal, Yadav. *Weighted Batched Threshold Encryption With Applications to Mempool Privacy*. IEEE S&P 2026; ePrint `2025/2115`. DOI: `10.1109/SP63933.2026.00175`. 已核对原文：逐条输出选中批次消息，静态按权重腐化、广播输入、固定索引/setup；不覆盖 aggregate-only、per-`sid` 退休和未来全体状态暴露。
- Li, Li, Xue. *Universal Accumulators with Efficient Nonmembership Proofs*. 2007. DOI: `10.1007/978-3-540-72738-5_17`。提供通用 accumulator 的 membership/nonmembership proof 基线，不覆盖异步状态恢复。
- Camenisch, Kohlweiss, Soriente. *An Accumulator Based on Bilinear Maps and Efficient Revocation for Anonymous Credentials*. 2009. DOI: `10.1007/978-3-642-00468-1_27`。撤销系统依赖 witness 更新/分发；该更新接口与本问题的异步 `Cure`/no-resurrection 组合尚未解决。
- Mashatan, Vaudenay. *A Fully Dynamic Universal Accumulator*. 2013. OpenAlex/Infoscience record `188657`。讨论动态 membership/nonmembership witness 的构造与更新边界，不覆盖 Byzantine 异步委员会和 threshold privacy finality。
- Schumm, Mukta, Paik. *Efficient Credential Revocation Using Cryptographic Accumulators*. IEEE ICBC 2023. DOI: `10.1109/icbc56567.2023.10174975`；相关 DAPPS 版本 DOI: `10.1109/dapps57946.2023.00025`。摘要声称通过三个 accumulator、epoch 和 state transition 消除持有者 witness update；因此是“无 witness update 但引入 epoch”的直接基线，不覆盖无全局 epoch 的异步 `Cure` 与 `PF_sid`。
- Sun, Steinfeld, Sakzad. *Incremental Symmetric Puncturable Encryption with Support for Unbounded Number of Punctures*. Designs, Codes and Cryptography 2022. DOI: `10.1007/s10623-022-01143-y`。覆盖单密钥、多次 puncture 的效率，不提供 threshold/share-compatible state handoff。
- Derler, Gellert, Jager, Slamanig, Striecks. *Bloom Filter Encryption and Applications to Efficient Forward-Secret 0-RTT Key Exchange*. Journal of Cryptology 2021. DOI: `10.1007/s00145-021-09374-3`。用 Bloom-filter 结构高效更新单个秘密状态，不覆盖异步 Byzantine 委员恢复和 aggregate-only threshold decryption。
- Lovett, Porat. *A Space Lower Bound for Dynamic Approximate Membership Data Structures*. SIAM Journal on Computing 2013. DOI: `10.1137/120867044`。这是一般动态近似成员结构的空间下界基线；13.10 的 exact 结论限定在线性、share-local 功能状态模型，13.12.4 的 approximate 结论限定在 coordinate-deletion frontier。
- Naor, Yogev. *Bloom Filters in Adversarial Environments*. CRYPTO 2015. DOI: `10.1007/978-3-662-48000-7_28`。说明公开哈希下的恶意输入不能直接套用随机输入假阳性分析。
- Sun, Sakzad, Steinfeld, Liu, Gu. *Public-Key Puncturable Encryption: Modular and Compact Constructions*. PKC 2020. DOI: `10.1007/978-3-030-45374-9_11`。支持 exact、unbounded punctures，但 punctured key 随穿孔次数线性增长；不提供 threshold recovery 或 aggregate-only homomorphic evaluation。
- Madathil, Lazzaretti, Liu, Papamanthou. *TACITA: Threshold Aggregation without Client Interaction*. ePrint 2025/1579. Modified STE 的 extended CPA 游戏覆盖静态 one-shot aggregate opening；不覆盖 adaptive/mobile corruption、puncture 或 repair。
- Bormet, Choudhuri, Faust, Garg, Othman, Policharla, Qu, Wang. *BEAST-MEV: Batched Threshold Encryption with Silent Setup for MEV Prevention*. ePrint 2025/1419。穿孔客户端 PRF key 并逐条恢复批消息，不穿孔委员会长期解密状态。
- Oh, Kim, Oh. *LightBEAT: Scalable Epochless Batched Threshold Encryption via Hierarchical Identity-Based Puncturing*. IEEE Access 14 (2026), 68054--68075. DOI: `10.1109/ACCESS.2026.3689882`。强近邻；全文确认其穿孔客户端 PRF key、静态委员会且逐条输出批消息。
- Basu, Tomescu, Abraham, Malkhi, Reiter, Sirer. *Efficient Verifiable Secret Sharing with Share Recovery in BFT Protocols*. ACM CCS 2019. DOI: `10.1145/3319535.3354207`。VSSR 是 share-recovery 基线，不提供 proactive/mobile retirement security。
- Jovanovic, Komatovic, Maffei. *Threshold Encryption with Silent Setup*. 2025 manuscript。FSE/PCS 扩展依赖时间更新或公开键材料更新，不提供稳定键下无序 `sid` 穿孔。
