# 异步联邦学习安全聚合研究追踪

> 建档日期：2026-09-09  
> 最近更新：2026-09-13  
> 研究主题：Asynchronous Federated Learning（AFL）中的 Secure Aggregation（SA）  主题背景：异步拜占庭共识（HoneyBadger、Dumbo）、PVSS、DKG、分布式应用密码学

## 0. 当前判断：输出完成不等于隐私已经终结

### 0.-1 主文瘦身与定位裁决（2026-09-13）

当前材料的理论密度已经超过联邦学习主文能够承载的范围。问题不是证明
数量本身，而是密码学接口和 hybrid 取代了 FL 生命周期问题的叙事中心。
因此首版论文改按以下层级组织：

1. 主问题是异步 FL 中“聚合输出后，单客户端更新何时永久不可恢复”；
2. 主理论是 privacy finality 与 recovery closure 的定义、刻画和攻击；
3. 主协议是面向异步 FL 的退休、聚合打开和 live-state recovery 语义；
4. `Joint-AO^mob`、`PVOD`、`CSO-VE`、`KeyOrigin`、`PECC` 及完整 hybrid
   只作为条件密码学实例化，放在后文或附录。

主文结构、三项核心 claim 和 proof budget 已单独写入
`privacy-finality-manuscript-structure.md`。本追踪文档继续记录研究审计，
不再把每一个新接口自动升级为论文贡献。

本轮暂不写完整主文初稿，改在思路稿中完成引言段落路线和方案总览。引言
先写异步 FL 生命周期、`CC_sid`/`PF_sid` 区分和 delayed-recovery 攻击，
方案再写 descriptor、aggregate-only opening、state-complete retirement 和
live-state-only recovery；`PVOD`、`CSO-VE`、`KeyOrigin`、`PECC` 继续降为
条件实例化层。

本轮完成三项主定理的符号对齐：主文 Theorem 1 对应技术稿 Theorem 44
（`E_sid(B,A)` 的 closure-aware criterion），主文 Proposition 2 对应
技术稿 Proposition 22（recovery-state localization separation），主文
Theorem 3 对应技术稿 Theorem 42（`F_PF^mob` conditional realization）。
主文不再把 closure criterion 写成脱离 capability ledger 的无条件密码学
定理，也不把技术稿中的辅助 hybrid 计为独立贡献。

### 2026-09-13（P56：主文定理前提审计）

完成主文与技术稿的前提审计。发现并修正 `R_sid` 的类型歧义：主文现在
使用 capability-level 的 `E_sid(B,A_sid)=B union R_sid union
 C_old(P-A_sid)`，其中 `R_sid` 对应技术稿的 `R_c`，表示退休后仍可由
合法恢复边导出的旧 capability，而不是节点集合。

同时将主文 Theorem 3 的条件改为与技术稿 Theorem 42 一致：状态定位先
证明 `R_sid=emptyset`，再使用 `A_sid in H_b(Gamma_dec^cap(sid))`；
`EqProof^mob`、`PECC` 等只通过 AOR/底层接口进入优势界。主文明确采用
selective single-descriptor 安全实验，不引入 adaptive-query 数据库接口。

截至 2026-09-09，停止推进 adaptive-query / 分布式数据库式的查询历史准入问题。当前只推进一个更贴合异步协议与分布式密码学背景的候选：

> **When Is an Aggregate Truly Final? Privacy Finality for Long-Lived Asynchronous Secure Aggregation：共识终结只说明“哪个聚合值已经输出”；隐私终结还必须说明“任何未来移动腐化都无法恢复该聚合中的单个更新”。我们定义并刻画异步委员会中的 privacy-finality certificate，证明它与输出证书、前向安全、阈值解密和主动刷新是不同的对象。**

当前密码学实现候选收紧为 `Recovery-Closure-Safe Aggregation`。TACITA 已覆盖静态 one-shot 的聚合开放核心，因此论文不再从零发明 aggregate-only threshold encryption；主问题改为：

```text
在完全异步、重叠会话和长期移动腐化下，如何把一次性的聚合开放
提升为可长期恢复、却永不恢复已退休能力的状态？当 repair 与委员会
handoff 也能生成解密能力时，哪些恢复闭包仍能保持隐私终结？
```

详细模型、基线和四周计划见 `long-lived-adaptive-corruption-audit.md`。

### 0.1 核心叙事

**一句话叙事：** 共识有 finality，隐私也需要 finality；而让密钥能够从故障中恢复的机制，恰恰可能让它从“被遗忘”中恢复。现有异步 SA 证明了结果一致，却通常没有证明“结果输出后，未来腐化和节点治愈不会重新打开历史单项更新”。本课题研究按 `sid`、按访问结构、在异步移动委员会中的不可逆隐私终结。

这条叙事的创新边界必须写清：

- `CC_sid` 是 **computation/consensus certificate**，证明集合、权重和聚合值已确定。
- `PF_sid` 是 **privacy-finality certificate**，证明足够多节点已经完成 `CollapseErase(sid)`，未来状态暴露不能再形成旧解密访问集。
- `FSE` 是时间前缀保护，`PE/DFPE` 是单接收者的标签撤销，`DPSS` 是永久秘密刷新；它们都不是 `PF_sid` 的异步阈值语义。
- `PF_sid` 不声称普通签名能够证明物理擦除。物理擦除仍是模型假设；证书只证明足够多节点执行了受约束的擦除事件，并由暴露下界处理 Byzantine 虚假确认。

本轮 `B_seed` 审计后的关键裁决是：基础短种子方案可以直接由“每委员独立 PE + Shamir mask 分片 + 聚合后穿孔”实现；因此构造贡献不应建立在 `B_seed` 本身。真正的二元边界是：若允许无状态恢复或重新密钥，Robust-Hitting 有直接匹配构造；若要求 `Cure` 后恢复当前状态且保持稳定公钥，则必须付出可验证 tombstone/状态传播代价，或面对 no-resurrection 攻击。

真正值得投稿的结果不是“把几个原语接起来”，而是下面的三层结果：

1. **Privacy-finality frontier：** 对任意解密访问结构 `Gamma_dec`，退休集合 `A_sid` 必须是其解密超图的 `b_sid`-鲁棒横截集：对每个 `D in Gamma_dec`，都有 `|A_sid intersection D|>b_sid`。等价地，对每个暴露集合 `B_sid`，`B_sid union (P-A_sid) not in Gamma_dec`；阈值情形才退化为 `n-a+min(a,b_sid)<q`。
2. **No-resurrection frontier：** 在完全异步的延迟刷新和恢复消息下，证明任何不携带单调退休状态的刷新机制都可能复活已终结 `sid`；随后给出携带 tombstone/capability state 的匹配构造，或证明其通信/状态代价下界。
3. **Recoverable-puncture frontier：** TACITA-style 静态聚合开放经普通 VSS/DPSS 备份提升时，持久备份和未来 recovery-authority exposure 会重新生成已穿孔状态。一般条件不是只对 `Gamma_dec` 做 Robust-Hitting，而是要求恢复闭包 `Cl_rec((P-A) union B)` 仍不属于 `Gamma_dec`；通用门限恢复把有效隐私门限降为 `min(q_dec,q_rec)`。对 one-sided approximate frontier，状态下界为 `Omega(R log(1/epsilon))`，BF-RPTA 在 coordinate-deletion 模型内常数因子近匹配。

这使主线明显区别于普通前向安全：研究对象不是“旧时间段”，而是一个由异步协议产生的、可公开审计且不可复活的**隐私终结事件**。

这不是“给 SA 加 proactive refresh”。通用 PSS 维护一个永久秘密，落后节点必须追赶，因此会受到旧消息延迟与未来腐化组合攻击。SA 的单客户端份额、mask 和会话解密状态是临时秘密；当唯一输入集合已经确定后，节点可以先把单输入份额折叠为聚合份额，再擦除单输入状态，迟到节点也不必恢复永久秘密。

候选技术出口是：

```text
quorum inclusion + stable public key + unordered per-sid puncture
+ aggregate-only threshold decryption + separately certified retirement
+ causal generation-barrier exposure bound
```

其中最后一项不能省略。若只限制任意时刻同时腐化至多 `t` 个节点，却允许敌手在擦除前无限快轮换，敌手可以依次读取 `t+1` 个份额；纯 continuous-mobile 正向安全不成立。

### 0.2 第一版敌手模型

- 完全异步认证网络；Static-AO 数据面可保持 `n=3f+1`，但 FGSR 的首个 reusable-repair 主定理取 `n=3f+2`；任意时刻最多 `f` 个主动 Byzantine 节点。
- 会话用 `sid` 区分，可任意重叠，不形成全局 epoch。
- 对每个 `sid`，敌手在相关敏感状态被节点擦除前累计读取的委员数至多 `t`；不同会话可以读取不同节点，长期并集可以覆盖全体委员会。
- 会话完成后安全擦除单输入状态，并从稳定密钥份额中独立穿孔该 `sid` 的解密能力；未来腐化不应恢复该能力。
- 首版主要保护委员会未来腐化下的客户端更新。未来直接腐化一个仍保留旧更新或原始训练数据的客户端，不属于 SA 能解决的隐私目标。
- 输出只保证 ACS/quorum 确定集合上的聚合，不保证每个诚实但任意延迟的客户端都被纳入。

`n=3f+1` 继续作为无 repair 的聚合/穿孔基线；一旦要求 target-excluded、state-complete
且可重复的 repair，本文主线使用 `n=3f+2`。两者不能在同一段落中混称为 FGSR 参数。

当前模型改称 `causal-generation-bounded mobile adversary`：每个 coordinate generation
interval 从当前状态安装开始，到下一次接受安装或 retirement barrier 结束；该区间
覆盖全部状态暴露，不只覆盖 repair 消息。它不同于全局同步 epoch，也不同于只限制
同时腐化数的无限速 `continuous-mobile`；长期敌手可以跨 interval 最终覆盖全体身份。

### 0.3 目标理论结果

1. **历史密钥暴露不可能性：** 无安全擦除或历史密钥隔离时，未来腐化足够多委员可解密归档 ciphertext 并恢复旧输入份额。
2. **同时阈值不可能性：** 不限制状态生命周期内累计腐化或腐化速度时，`|Corr(tau)|<=t` 不能保证阈值隐私。
3. **纳入/终结边界：** 完全异步且容忍客户端掉线时，“每个诚实提交最终纳入”和“输出集合不可回滚地终结”不可同时保证；终结后的安全擦除因此必须采用 quorum inclusion 或额外故障检测假设。
4. **穿孔 quorum 边界：** 令 `b_sid` 为最终仍可用的旧能力节点上界。对 `q`-out-of-`n` 解密与 `a` 个退休确认，最坏条件为 `n-a+min(a,b_sid)<q`；在可行区间 `a>=b_sid` 内退化为 `n-a+b_sid<q`。完全异步活性要求 `a<=n-f`。在 `n=3f+1,b_sid<=f` 下，最紧的门限点是 `q=a=2f+1`。
5. **正向构造：** 在会话生命周期累计暴露上限下，实现稳定公钥、无序 `sid` 穿孔、只解密授权聚合密文及 post-puncture total exposure security。
6. **隐私终结定理：** 将 `CC_sid` 与 `PF_sid` 分离，并证明只有满足 `B_sid union (P-A_sid) not in Gamma_dec` 才能抵抗退休后的全体当前状态暴露；该定理推广 N4，而不是重复一个固定阈值计数。
7. **反复活不可能性：** 若刷新/治愈可接受不含 `sid` 退休墓碑的旧状态，异步延迟消息可以使已经终结的 `sid` 恢复可解密；因此刷新必须携带可验证的单调 capability state，或放弃无全局 epoch、落后节点恢复、未来全体状态暴露三者之一。
8. **匹配性：** 证明正向模型的关键放松接近必要，而不是把已有 per-epoch 腐化预算重新命名。

### 0.4 投稿门槛与近期执行

- 单独证明“依次腐化 `t+1` 个节点会泄漏”过小；必须与异步终结、诚实纳入和状态生命周期形成紧的不可兼得定理。
- 直接组合 `ACS + adaptive PVSS + fresh session keys` 不自动构成贡献；必须检查多会话、擦除和移动腐化模拟器是否需要新的组合证明。
- 不把“稳定公钥 + puncturable threshold encryption”单独作为贡献：DFPE 已有交错 allow/deny puncture，epochless BTE 已有批量阈值选择性解密；新贡献必须落在 aggregate-only、异步 privacy finality 和吸收态退休的联合边界。
- 不把“公开退休证书”写成普通密码学意义上的 deletion proof；没有可信擦除、TEE 或量子 certified deletion 假设，软件签名只能证明节点声称擦除。
- 若方案仍依赖全局 epoch-close、可信时钟或完整 DPSS handoff，则“without global epochs”不成立。
- 若新模型最终只是每会话独立运行已有协议，且安全性由标准并行组合直接推出，立即降级或关闭。
- 已修正过弱的 `Theta(n*d)` 基线：OPA/Buffalo 式短种子同态 mask 可做到 `O(d+n*kappa)`；真正的紧凑目标只是把 `n` 个短 ciphertext 降为一个，并给出阈值穿孔的组合证明。
- N4 的“输出证书 `CC_sid` / 退休证书 `PC_sid`”门限边界已形式化；下一步验证匹配协议，不先实现完整 FL。

### 当前组件裁决（全文复核）

当前方案不是“秘密共享还是前向安全加密”的二选一，而是最小四层栈：

1. **数据面：** 用 TACITA-style `Static-AO` 或等价 threshold additive/homomorphic encryption 只打开短 mask key 的唯一加权和；梯度维度由 seed-homomorphic PRG/key-homomorphic PRF 承担。
2. **状态面：** 用 current-share-only VSS/AVSS repair 恢复仍活跃坐标；退休时必须删除 direct share、recovery-polynomial share、`sid`-local backup 和 pending recovery state。FSE 只能保护认证/信道或全序世代，不负责无序 `sid` 退休。
3. **控制面：** ACS/异步 BFT 生成唯一 `CC_sid`，随后以 Robust-Hitting 安全集合形成 `PF_sid` 和单调 frontier；恢复输出必须经 `CheckInstall(T_req)`。
4. **证明面：** NIZK 只证明 ciphertext/聚合分片/恢复贡献的一致性和合法性，不声称证明物理擦除。

全文裁决：LightBEAT 的 HIDP 穿孔客户端公开 PRF key，委员会 state 不穿孔；其“adaptive”是 chosen-identity 原语安全，full protocol 仍是 static corruption，且 `Combine` 输出每条明文。VSSR 的 recovery polynomial + DPRF 是最强局部恢复基线，但其安全游戏对每个 commitment 累计限制 `<k` 个来源，并明确不解决 proactive share recovery。Silent Setup 的 FSE 依赖周期更新，PCS 通过重采样和发布新 `pk/hint`，因此不能替代稳定键下无序 `sid` 的 recoverable puncture。

动态节点分三层处理：当前主定理覆盖固定身份委员会内的移动腐化与 crash/cure；完整 join/leave/reconfiguration 暂不塞入首个构造。扩展采用 `Project(T) -> Handoff(cfg_old,cfg_new,live coordinates only)`，并把 DPSS handoff 作为 Repair-Closure 中的跨配置恢复边。真正可主张的新结果是 `Handoff-Closure Preservation`，不是“支持动态委员会”本身。

下一步唯一任务改为：形式化 `Recovery-State Localization Barrier`。证明 ordinary VSSR/DPSS 黑盒若保留能与全局恢复权组合的 `sid`-local recovery state，则未来暴露会把旧 capability 加回 `Cl_rec`；匹配构造必须采用 coordinate-local deletion 或 puncturable recovery authority。先做固定委员会定理，动态 handoff 作为同一定理的推论。

### 0.4.1 当前执行：把 privacy finality 变成可证明边界

本轮修正了 N4 的一个容易被审稿人抓住的缺口：不能把 `n-a+b_sid` 当作所有参数区间的精确式。令：

- `P` 为委员会，`A_sid` 为证书中声称已完成原子 `Puncture+Erase` 的节点集合；
- `B_sid` 为执行结束时敌手仍拥有旧 `sid` 解密能力的节点集合。它包括已被读取并保留旧份额的节点，也包括伪造退休确认但实际未擦除的 Byzantine 节点；
- `|A_sid|=a`，`|B_sid|<=b`，旧解密访问结构为 `Gamma_dec`。

更一般的主定理表述是：令 `Gamma_dec` 看成由授权解密集合组成的超图。对给定实际退休集合 `A_sid` 和暴露上界 `b`，以下两件事等价：

```text
(PF)  对所有 B_sid with |B_sid|<=b，B_sid union (P-A_sid) not in Gamma_dec;
(HIT) 对所有 D in Gamma_dec，|D intersection A_sid| > b.
```

证明只有一行：`D subseteq B_sid union (P-A_sid)` 当且仅当 `D intersection A_sid subseteq B_sid`。因此若某个 `D` 与 `A_sid` 的交集不超过 `b`，取 `B_sid=D intersection A_sid` 即得到 matching attack；反之，若每个交集都大于 `b`，任何大小至多 `b` 的 `B_sid` 都无法覆盖该交集。这个结果把 privacy finality 从固定阈值计数提升为**访问结构上的鲁棒横截性**。

定义 `H_b(Gamma_dec)` 为满足 `(HIT)` 的鲁棒横截族，并令 `tau_b(Gamma_dec)` 为其中最小集合大小。对一般访问结构，`a>=tau_b(Gamma_dec)` 只是任何构造的必要下界；充分条件是协议实际可能产生的退休集合族 `Gamma_ret` 满足 `Gamma_ret subseteq H_b(Gamma_dec)`。只有在阈值访问结构的对称情形下，按大小的条件才同时必要充分。阈值 `q`-out-of-`n` 时：

```text
tau_b(Gamma_q) = n - q + b + 1,
```

这也解释了为什么 `a<=n-f` 的异步活性和 `q<=n-f` 的解密活性共同推出 `b<=n-2f-1`。真正需要证明的不是“签名数量足够”，而是协议产生的退休集合始终落在这个鲁棒横截族中。

该定理还有一个必须保留的加权版本。若节点权重为 `mu(i)`，敌手在会话生命周期内可保留的旧能力预算为 `beta`，则 `(HIT)` 改为：

```text
for every D in Gamma_dec, mu(D intersection A_sid) > beta.
```

这与 WBTE 的 stake-weighted threshold 不是同一个对象：WBTE 的权重决定谁能参与批量解密；这里的权重决定退休集合是否足以切断未来暴露后的解密访问集。二者可以组合，但不能把前者的 weighted correctness 直接当作 privacy finality。

由此得到更适合异步协议的 **retirement-liveness sandwich**。令 `Gamma_cert` 为协议接受的退休证书集合族，`Gamma_live` 为在允许 Byzantine withholding 后可能收到确认的响应集合族，则：

```text
privacy safety:  Gamma_cert subseteq H_b(Gamma_dec)
privacy liveness: for every L in Gamma_live,
                  there exists A in Gamma_cert with A subseteq L
```

第一条防止未来暴露形成旧解密集合；第二条保证异步调度下总能从实际响应者中抽出一个安全退休证书。对称阈值系统中它退化为：

```text
n - q + b + 1 <= a <= n - f,
q <= n - f.
```

因此 `b<=n-2f-1` 不是孤立的份额计数，而是一个同时满足解密活性、退休活性和历史隐私的访问结构可行性条件。

若证书只承诺集合大小而不证明 `A_sid` 与 `B_sid` 的交集，则未来暴露全部当前状态后仍可能形成的旧能力集合是：

```text
D_sid = B_sid union (P - A_sid)
|D_sid| = n - a + |A_sid intersection B_sid|
max_|B_sid|<=b |D_sid| = n - a + min(a,b).
```

因此对 `q`-out-of-`n` 阈值解密，**仅依赖 `a` 个退休确认的最坏情况 privacy-finality 条件**是：

```text
n - a + min(a,b) < q.
```

在可行的有用区间 `a>=b` 内才退化为旧式简洁公式 `n-a+b<q`。如果 `b>=a`，敌手可以让所有确认节点都属于 `B_sid`，退休证书对旧能力不产生任何最坏情况削减，`|D_sid|=n`，说明仅增加签名确认而不证明擦除来源不能解决问题。

若完全异步活性要求 `a<=n-f`，阈值解密要容忍 `f` 个节点 withholding 而要求 `q<=n-f`，则存在可行参数的必要充分条件为：

```text
b <= n - 2f - 1.
```

在 `n=3f+1`、会话生命周期暴露上限 `b=f` 时，唯一的紧点仍是：

```text
q = a = 2f+1.
```

这条结果的研究价值不在计数本身，而在于把四个通常分开处理的约束放进同一个事件序列：输出集合的 ACS 终结、授权聚合解密、节点原子擦除、以及未来全体状态暴露。匹配攻击必须允许 Byzantine 节点确认后继续保留状态，并允许敌手在证书形成后才读取其余节点。

### 0.4.2 吸收态退休与 no-resurrection 定理

旧版本 NR 有一个边界错误：`PC_sid` 形成不等于每个被计入证书的节点都已退休，因此“某个节点没收到证书”不能直接推出 `PF_sid` 失败。正确主线是研究**退休集合在异步状态转移下是否为吸收态**。

令 `A` 是 `PC_sid` 声称已执行 `Puncture+Erase` 的集合，`R subseteq A` 是退休后仍能被延迟旧消息重新安装 `sid` 能力的集合，`B` 是退休前已被敌手保存旧能力的集合。复活轨迹的有效集合为：

```text
B_eff = B union R union (P - A)
```

对固定的暴露集合 `B`，对每个解密授权集合 `D`，真正需要的是：

```text
D is not a subset of B union R union (P - A).
```

若敌手可任意放置至多 `b` 个暴露节点，其最坏情况计数形式为
`|D intersection (A-R)| > b`。`R=emptyset` 时退化为 Robust-Hitting；若存在
`D` 使该计数条件失败，则敌手可结合延迟旧消息、至多 `b` 个已保存能力和退休后
当前状态暴露恢复 `D`。这把 NR 从“单节点复活必然破坏隐私”修正为一个精确的
访问结构条件。

**NR-Event Theorem（条件版）。** 若 `p in A`，存在退休前生成的合法 `m_old`，其认证在退休后仍有效且不受 `T_p >= Retired(sid,h)` 支配，状态机又允许 `m_old` 重新安装旧能力，则完全异步调度可使 `p in R`。若某个 `D in Gamma_dec` 满足 `|D intersection (A-R)|<=b`，则 `PF_sid` 被破坏。证明采用两个执行：退休前交付 `m_old` 保证恢复活性，退休后延迟同一消息；无支配状态时接收者无法区分，故接受并复活。单调 `T_i`、不可回滚 tombstone 或等价的状态转移证明使 `R=emptyset`，是匹配充分条件。

这条结果的投稿级叙事不是“给每个委员加 deny-list”，而是：**privacy finality 是访问结构上的安全横截性，加上异步状态机中的吸收态退休；证书若不能支配所有未来可达状态，就不是隐私终结。** 若实现只复制现有 DFPE deny-list，关闭协议构造叙事，保留该边界作为理论结果。

### 0.4.3 最小协议骨架与真正 proof gap

首版只验证以下骨架，不实现完整 FL：

```text
Submit(u, sid, x_u, w_u):
    sample k_u; send y_u = x_u + PRG(k_u), ct_u = Enc(PK, sid, k_u), pi_u

CC(sid):
    ACS fixes S_sid, weights, recipient, and descriptor H_sid
    ct_sum = EvalAdd({w_u * ct_u : u in S_sid})

Release(sid):
    honest nodes release shares only for (sid, H_sid, ct_sum)
    recipient reconstructs K_sum and outputs sum_u w_u*x_u

CollapseErase(sid):
    after checking CC_sid and release context, locally puncture sid,
    erase raw sid state, then emit signed retirement acknowledgement

PC(sid):
    collect a acknowledgements and publish a monotone tombstone
```

当前真正的 proof gap 只有三个：`(i)` 证明 `B_seed` 的聚合分片、上下文绑定和并发 `sid` 组合不会扩大允许泄漏；`(ii)` 证明 `PC_sid` 在未来全体状态暴露下仍满足上面的集合边界；`(iii)` 证明 cure/刷新状态转移使退休成为吸收态，即携带 tombstone 支配关系并使 `R=emptyset`。若前两项由现有 PVSS/ACS/PE 直接推出，且第三项只能依赖已有 epoch handoff，则关闭协议构造创新，仅保留 Robust-Hitting 与 Cure–Finality Trilemma 理论结果。

### 0.4.3.1 `B_seed` 黑盒组合裁决（修正版）

此前把 `B_seed` 误读成对 punctured PE secret key 做 Shamir 分享。正确基线是：每个委员持有独立 PE key，客户端只把短 mask key `k_u` 的 Shamir 分片分别加密给各委员；委员在 `RAW` 状态解密并求和，随后穿孔对应 ciphertext 标签并擦除明文分片。

因此在不要求 `Cure` 后恢复被穿孔 PE 状态时，`B_seed` 可以直接组合：只公开各委员的聚合 Shamir 分片，重构后只输出 `K=sum_u w_u k_u`；aggregate-only 由应用层 wrapper 实现，不需要 wBTE 或 threshold homomorphic ciphertext。`CC_sid` 绑定、分片证明和原子擦除仍需组合证明，但不明显构成新原语。

真正未决的是：`B_seed` 的客户端代价为 `O(d+n*kappa)`；若压缩到 `O(d+kappa)`，才需要 locally share-compatible puncture 或 compact aggregate-only primitive。更关键的是，若长期移动模型要求 `Cure` 后委员恢复当前 PE 状态，恢复消息必须受 `T_i` tombstone 支配，否则可复活集合 `R` 会破坏 Robust-Hitting。主线因此应聚焦 privacy-finality 与 cure/recovery 的边界，而不是把 `B_seed` 基础流程包装成构造贡献。

匹配基线的具体流程已固定：每委员独立 PE key，客户端将短 mask key 做 `q`-out-of-`n` Shamir 分享并分别加密；委员在 `RAW` 状态对入选分片求和，发布聚合分片后穿孔和擦除；重构 `K=sum_u w_u*k_u`，只释放加权聚合。`n=3f+1,q=a=2f+1,b=f` 时，未来状态暴露最多形成 `2f<q` 个旧分片。该构造匹配 Robust-Hitting，但不支持丢失 PE 状态后的恢复，因此 cure/recovery 必须单独建模。

由此形成早期的 **Cure--Finality Trilemma** 直觉：在稳定 `pk_j`、完全异步迟到消息和未来全体状态暴露下，`Cure` 后重新加入、无全局 epoch/反复 rekey、以及已终结 `sid` 的 no-resurrection 存在状态恢复张力。该直觉已在本轮收紧为条件版 `Causal-Fence Necessity Theorem`：真正不能省略的是支配 `sid` 终结的单调 capability state，或等价的密钥世代/可信因果边界；带 tombstone 的协议并不被该命题排除。

### 0.4.4 本轮外部覆盖检查（2026-09-10）

- `2508.13425`（LTP-FLEO）讨论跨轮模型反演和客户端分组，敌手主要是 curious server/clients，不给出移动 Byzantine、未来全体状态暴露或 per-`sid` 退休证书。
- `2601.04930` 讨论完全异步 Byzantine aggregator、掩码和 DP/公平纳入，不覆盖会话退休后的密钥状态泄露。
- `2606.02958`（Echelon）强调 aggregate-only 的系统审计边界，但摘要层面不提供本问题的阈值隐私终结定理。
- `10.1109/SP63933.2026.00175` / ePrint `2025/2115`（Agarwal et al., IEEE S&P 2026）是新的强基线。其 wBTE 对任意选中批次输出每条消息，底层使用 threshold homomorphic encryption + key-homomorphic puncturable PRF；安全模型是静态按权重腐化，输入通过广播交付，setup 固定最大批次和索引空间。它不提供 SA 所需的 aggregate-only 输出、per-`sid` retirement、长期移动腐化或未来全体当前状态暴露，因此明确提高了批量阈值解密的基线，但没有关闭 PF 主线。
- 新检索到的 ACNS 2026 `Dynamic Puncturable Encryption`（DOI `10.1007/978-3-032-32560-0_4`）研究的是用户/机构控制的撤销、恢复和委托访问；它没有阈值委员会、同态聚合、aggregate-only 解密或长期移动腐化接口，因此不覆盖当前缺口。
- wBTE 原文还明确说明：将阈值同态加密直接替换进 key-homomorphic puncturable PRF 会出现群类型不匹配，修复需要 PRF、阈值密钥和 CRS 的非黑盒代数耦合（`/tmp/wbte-eprint.txt:403-425`）。这支持“当前原语缺口是真实组合障碍”的判断，但不构成不可能性证明。
- 本轮 OpenAlex、Crossref 和 arXiv 关键词检索未发现“privacy finality”作为异步安全聚合的既有密码学定义；该结果只用于检索记录，不构成新颖性证明。

### 0.4.5 WBTE 与 aggregate-only SA 的接口分离

WBTE 的原文接口 `Pi-BDec(mpk,{ct_i},<sk_j>)` 输出选中批次的每个明文 `m_i`。其构造先恢复聚合 PRF key `K=sum_i K_i`，再结合每个 ciphertext 中公开的 punctured key `K_i*`，逐项计算每个 `m_i`。因此它不是当前 `F_LL-SA` 的黑盒实现：

```text
F_wBTE(batch) leaks {m_i : i in batch}
F_agg-only(S,w) leaks only sum_i w_i*m_i
```

当 `|S|>=2` 时，存在大量不同输入向量具有相同加权和；不存在只知道 `F_agg-only` 输出的模拟器能够生成 `F_wBTE` 的逐项明文泄漏。标准 SA 中公开 masked update `y_i` 本身可以是允许的 transcript，因此准确的攻击路径是：若把 `x_i` 直接作为 WBTE 明文，逐条解密立即泄露更新；若把 mask seed `k_i` 作为 WBTE 明文并发送 `y_i=x_i+G(k_i)`，逐条恢复所有 `k_i` 也能逐项还原 `x_i`。若只保留 WBTE 的聚合 key 而删除 `K_i*`，其原文中的逐项正确性等式不再成立；这已经不是标准 WBTE 黑盒调用。故 WBTE 提供的是强批量解密基线，不是 aggregate-only 组件。

这形成一个明确的黑盒分离命题：**任何调用标准 WBTE batch-decryption 接口并允许其输出被协议参与者获取的组合，都不能实现只释放加权和的 SA 理想功能；必须改变解密接口或构造新的 aggregate-only key-recovery primitive。** 这个分离本身不作为唯一贡献，但它关闭了“直接套 WBTE”的伪方案。

### 0.4.6 历史候选：自适应查询安全（已停止）

`Adaptive-Query-Safe Asynchronous Secure Aggregation` 已按用户决定停止推进。其 row-space、查询历史准入和多次精确输出问题属于另一条更接近数据库查询控制的研究线；仅保留为历史记录，不再占用当前执行计划。

### 0.4.7 次级候选：抗选择性中止的异步可验证 DP 释放

`Selective-Abort-Resistant Asynchronous Verifiable DP Release` 继续封存。只有当前长期腐化主线被证伪后，且能相对 VDDP、CCS 2024 secure sampling、Dordis、Willow、Lotto、通用 fully asynchronous MPC 和 2601.04930 给出严格分离，才重新评估。

### 0.5 历史候选：授权恢复与输出释放（已封存）

#### 0.5.1 旧主线记录：从公平纳入转向一致授权与输出释放（已终止）

结合 `/home/yzc/flagg` 中的 `OSDI_AsyncSA_Tracking.md`、`FL_INTERSECTION_PAPER_TRACKING.md`、`OSDI_NOVELTY_REVIEW.md` 和 `NOVELTY_AUDIT.md`，当时主线调整为：

> **在完全异步委员会中，客户端提交后不再参与；委员会成员只持有不一致的局部分享视图。如何对一个明确的输入集合、权重和接收者形成不可冲突的聚合授权，并在拜占庭干扰、晚到分享和恢复过程中只释放一次、只释放被授权的聚合结果？**

暂定题目（研究假设）：`Authorized Function Recovery under Weak Readiness in Asynchronous Secure Aggregation`

### 为什么比“防重放”更强

- 授权描述符、上下文绑定和 `single-consumption` 是必要安全接口，不是新颖性主张；Willow 已处理动态 one-shot 聚合中的至多一次纳入。
- 不把“公平随机抽样”当作主贡献；随机纳入作为后续扩展。
- 可能的新点只在弱就绪条件下的函数级恢复、故障轨迹和端到端成本。
- FL 只在客户端 one-shot、模型版本、权重、掉线或高维向量改变协议成本时作为应用载体；否则应转为密码学论文叙事。

### 第一篇论文的最小边界

只研究以下场景：固定委员会 `n=3f+1`，静态拜占庭委员会，客户端 honest-but-curious 且提交后离线；输入向量使用可验证秘密分享；聚合函数为公开权重的线性和。

不同时研究：恶意客户端投毒、公平抽样、动态委员会、移动腐化、长期 DP、非线性鲁棒聚合、通用 MPC。

### 核心理论目标

1. 定义规范化聚合描述符 `D=(task, committee_epoch, recipient, model_rule, [(sid_j, commitment_j, weight_j)])`。
2. 证明 `D` 的授权不可冲突：正确节点不会接受两个不同的已授权描述符作为同一逻辑请求。
3. 证明 `single-consumption`：同一输入对象 `sid_j` 不能被两个冲突授权或两个输出上下文重复消费。
4. 证明 `authorized release`：输出只对应已授权集合与权重，不因晚到份额、修复路径或视图切换扩大集合。
5. 研究函数级恢复是否能消除“先逐输入修复、再聚合、再释放”的额外关键路径；若不能证明严格优势，则终止该候选。

### 关键发表风险

该方向不能把“恢复多项式”“批量 ACSS”“集合承诺”本身宣称为新贡献；这些已有先例。真正需要证明的是：**在客户端已离线、委员会持有异构份额、授权集合已固定的执行中，授权后的输出释放是否存在可消除的恢复跳、重复工作或状态物化成本，并且该差异不被更强基线直接覆盖。**

### 历史：旧主线的基线锁定与证伪检查

### 强基线 B0

给定同一个已最终授权的 `D`，先固定可用性语义。不能同时假设 `ACSS-complete` 和“正确委员缺少份额”。B0 分成两个合法口径：

**B0-complete：** `ACSS-complete(j)` 表示分享阶段完成后所有正确委员都持有 `sid_j` 的有效份额。此时正常路径没有逐输入修复：

1. 委员会验证 `D` 引用的完成证据；
2. 每个委员本地计算 `z_i(D)=Σ_j w_j s_{i,j}`；
3. 委员会发送聚合份额和释放证明；
4. 接收者用阈值份额重构 `y_D`。

**B0-recovery：** 若采用较弱的 `LocalReady/EventualReady`，允许正确委员在授权时缺少部分份额，则必须把传播或逐输入私密修复计入：

1. 逐输入验证可恢复证据；
2. 对每个缺失对 `(i,j)` 执行私密修复或继续传播；
3. 委员会计算 `z_i(D)`；
4. 发送聚合份额、释放证明并重构 `y_D`。

`B0-complete` 和 `B0-recovery` 不是同一个起点；B1 必须分别比较。

### 候选路径 B1

1. `D` 授权时固定输入清单、权重、接收者和恢复上下文；
2. 在同一 `LocalReady/EventualReady` 证据下，不恢复每个缺失输入的完整份额；
3. 生成与 `D` 对应的线性函数响应，并用一次函数级编码/盲化响应重构 `y_D`；
4. 释放证明同时绑定 `D`、响应集合、输入承诺和输出承诺。

目前 B1 只是研究假设。Haven++ 的单 dealer 打包/批处理、OPA/Willow 的 one-shot 机制和已有线性秘密共享都可能覆盖它的组成部分。

### 必须证明的真实差异

| 检查项 | B0 | B1 候选 | 只有满足什么才算贡献 |
|---|---|---|---|
| 输入集合 | 已授权 `D` | 同一个 `D` | 不得通过改变集合换取更快 |
| 输出 | 同一个 `y_D` | 同一个 `y_D` | 精确等价，不接受近似结果 |
| 隐私 | 中间修复不泄漏 | 函数响应不泄漏 | 同一模拟器泄漏口径 |
| 故障 | 同一 `f`、同一晚到轨迹 | 同一 `f`、同一晚到轨迹 | 不降低活性条件 |
| 关键路径 | 逐输入修复 → 聚合 → 释放 | 函数响应 → 释放 | 至少消除一个数据依赖阶段 |
| 额外成本 | 每输入修复/验证 | 函数响应证明/验证 | 总成本或关键路径存在正区间优势 |

### 成本公式（只比较增量）

参数：`N` 为任务客户端数，`m=|D|` 为本次聚合输入数，`d` 为每个输入的向量域元素数，`n=3f+1` 为委员会规模，`b` 为每个 dealer 的打包容量，`q` 为重构所需响应数，`pi` 为单个向量响应证明字节数。

令 `C_share(D)` 表示客户端上传、ACSS dispersal、承诺和完成证据的已付成本；`C_auth(D)` 表示授权日志成本。只有 B0 与 B1 使用相同分享表示和相同 `D` 时，这两项才能从差值中抵消。

```text
C_B0_complete = C_share + C_auth
                 + q * (d * field_bytes + pi_release)

C_B0_recovery = C_share + C_auth
                 + sum_{(i,j) in Missing(D)} C_private_repair(i,j)
                 + q * (d * field_bytes + pi_release)

C_B1 = C_share + C_auth
        + C_function_response(D, readiness, faults)
        + C_release_verification(D)
        + C_preprocessing(D)
```

`C_preprocessing` 不能默认为零；若函数响应需要预先生成零分享、恢复多项式、DPRF 或额外承诺，就必须摊销到明确的聚合次数。关键路径也不能用消息轮数替代墙钟时间：

```text
L_B0_recovery = L_authorize + L_repair_dependency(D) + L_release
L_B1          = L_authorize + L_function_response(D) + L_release
```

只有在相同 readiness、故障和隐私条件下，证明 `L_B1 < L_B0_recovery` 或 `C_B1 < C_B0_recovery`，候选才有继续价值。`B0-complete` 上没有修复阶段，不能拿 B1 与它比较出“省掉修复”的结论。

### 证伪条件

出现以下任一结果，立即放弃 B1 作为主贡献：

- B1 只是把逐输入修复搬到隐藏的批处理阶段，总通信和关键路径不降；
- B1 需要比 B0 更强的 `CommonReady`、更少的故障或更强的信任假设；
- B1 的函数响应在公开权重下等价于已有线性秘密共享聚合，无法给出新的协议能力；
- B1 只能改善 toy 参数，无法在 `N ≫ n` 或高维模型模式下形成正区间；
- Haven++、Aion、Dumbo-MPC 或其他多源 VSS 基线已直接提供相同的授权后输出语义。

### 本轮交付物

- 一张 B0/B1 消息级对照表；
- 一个 `F_authorized-release` 理想功能；
- 两个最小反例：异构持有者视图、晚到份额导致的恢复分叉；
- 一个成本公式：分别统计委员会消息、向量载荷、证明字节和授权到输出的串行阶段；
- 一份继续/终止裁决，不先实现完整系统。

### `F_authorized-release` 初版

对任务 `task` 和委员会 epoch `ce`，功能维护：

```text
Authorize(rid, D)
Respond(sid, share_evidence, response_context)
Release(rid, response_set, proof)
```

其中规范化描述符：

```text
D = (task, ce, recipient, policy, model_rule,
     [(sid_j, input_commitment_j, model_commitment_j, weight_j)]_canonical)
```

功能行为：

1. `Authorize(rid, D)` 仅接受规范化、无重复 `sid`、权重明确且授权状态未冲突的描述符；接受后将 `rid` 和 `D` 写入不可回滚的消费状态。
2. `Respond` 只接受绑定 `rid`、`D`、`sid` 和 `response_context` 的有效响应；晚到或上下文不一致的响应不改变 `D`。
3. `Release` 仅当响应集合满足恢复阈值、承诺验证通过且证明绑定同一个 `D` 时输出：

   ```text
   (rid, D_digest, y_D = Σ_j weight_j · x_j, release_certificate)
   ```

4. 同一 `rid` 至多成功 `Release` 一次；任何后续请求必须返回同一个释放记录，不能以新 epoch、重试编号或替代恢复上下文重新消费输入。
5. 功能不向委员会或接收者输出单个 `x_j`、未授权子集合和中间修复值；允许泄漏仅限于公开元数据、腐化方已有视图及授权的 `y_D`。该条只有在额外参数固定后才有意义：最小聚合规模 `rho`、委员会合谋上限、接收者可发起的重叠查询策略和多次输出的隐私定义。

**必须保留的边界**：该功能不保证 `D` 的选择公平，也不判断 `x_j` 是否是良性梯度；它只保证授权描述符到输出释放的完整性、唯一性和隐私边界。若未固定 `rho`、合谋和查询模型，不能声称一般意义上的单输入隐私。

### 历史：旧主线的已读文献覆盖检查

| 方案 | 已直接覆盖的能力 | 对当前候选的限制 | 当前判断 |
|---|---|---|---|
| Haven++ | ACSS 完成、所有正确方持有份额、单 dealer 打包、批量证明、单个/全部秘密的双门限重构 | 以单 dealer 的分享状态为基本对象；没有直接给出外部多 dealer 的授权日志与 FL 聚合函数恢复 | 必须作为 ACSS/批处理基线，不能把 packing/batching 重新命名为创新 |
| Willow | one-shot 客户端、动态参与、上下文绑定、恶意服务器下的至多一次纳入验证、输出功能 `F^Agg` | single-server；解密器/验证器与服务器有非串谋假设，不是本候选的多源异构份额恢复 | 直接覆盖 `single-consumption`、aggregation ID 和部分输出一致性叙事 |
| OPA | 客户端和委员会一次交互、掉线容忍、动态参与、残余攻击防护、客户端输入上下文绑定 | 主要是单服务器密码聚合/PRF；不等价于异步委员会 ACSS 的授权后函数恢复 | 覆盖 one-shot 和 replay/context 组件 |
| BASA/Buffalo | buffered async SA、动态 buffer、assistant、聚合完整性、恶意服务器集合一致性防护 | 不提供本候选的多 dealer ACSS 异构恢复接口；Buffalo 的 assistant/PKI/设置假设需单独计费 | 覆盖 FL 异步场景和完整性基线 |
| NFSA | 两层秘密共享、批量输入编码、FL 中的通信/计算优化 | 主要是 semi-honest single-server；不覆盖完全异步 Byzantine 委员会 | 作为批量秘密共享和通信基线 |

### 覆盖后的唯一待核验差异

当前不能声称“授权、一次性消费、上下文绑定、批处理、one-shot”是新贡献。唯一仍值得核验的是组合问题：

> 多个独立客户端分别作为 dealer；每个客户端完成一次分享后永久离线；授权时只有 `LocalReady/EventualReady` 证据；正确委员对不同输入持有不同份额；在不恢复单个输入、不改变 `D` 的前提下，是否存在安全的函数级恢复协议，并在同口径 B0-recovery 上减少关键路径或总成本？

这只是开放问题。若将 `ACSS-complete` 作为授权前提，则 B0-complete 已能直接聚合，B1 的主要优势消失；若放宽为 `LocalReady/EventualReady`，必须补齐该证据如何生成、如何保证隐私、如何抵抗 Byzantine withholding，以及为什么现有 Haven++/OPA/Willow 组合不能直接实现。

### 两个最小反例

**反例 A：异构持有者视图。** `D={sid_1,sid_2}` 已授权。正确委员 `H_1` 持有 `sid_1`、`H_2` 持有 `sid_2`，拜占庭委员同时持有两者。若协议先让每个委员独立修复“自己缺失的输入”，再由接收者拼接响应，攻击者可能把来自不同恢复上下文的响应组合成一个未被共同授权的输出。B1 必须让每个响应绑定同一个 `D_digest` 和 `response_context`。

**反例 B：晚到份额导致的恢复分叉。** `D` 已授权后，`sid_2` 的有效份额晚到。部分委员先按 `D` 生成响应，另一部分委员把 `sid_2` 标记为不可用并尝试释放子集合。若没有不可回滚授权状态，两个结果都可能携带看似有效的局部证明。B1 必须拒绝改变 `D`，并让晚到份额只能完成原 `D` 的响应，不能创建新输出语义。

### 历史候选：可验证公平纳入

### 异步安全聚合中的可验证公平纳入

**研究问题**：在完全异步网络中，消息延迟可被对手操纵、客户端不知道未来 inclusion set、聚合器可能 equivocate 的情况下，如何让客户端更新被不可伪造、不可重复、可验证且延迟公平地纳入安全聚合，同时不暴露单个更新？

这个叙事比单独防重放更强：

- **核心对象**：inclusion policy，而不是某个 nonce 或签名格式。
- **理论问题**：异步延迟、隐私阈值、可验证一致性、纳入公平性之间是否存在不可兼得的边界？
- **密码学问题**：如何用 PVSS/DKG、阈值签名和异步随机性证明 inclusion set 未被聚合器操纵。
- **系统问题**：不对高维模型向量运行共识，只对元数据和集合摘要达成可验证结果。
- **防重放**：降为必要子性质，作为 `at-most-once inclusion` 证明的一部分。

**历史候选题目（已降级）**：`FairAsyncAgg: Verifiable Fair Inclusion for Asynchronous Secure Aggregation`

**核心理论目标**：

1. 给出 arrival-order inclusion 的公平性/隐私风险下界。
2. 构造基于异步阈值随机性的公平纳入协议，不依赖单一服务器决定集合。
3. 证明 `at-most-once inclusion`、`certificate consistency`、`inclusion fairness` 和 `liveness`。
4. 明确边界：对任意无限延迟客户端不能保证及时纳入，只能保证满足参与/送达条件后的概率或长期频率公平。

**最小实验**：低维向量 + 异步消息调度器，比较 arrival-order、固定 buffer、随机公平纳入三种策略；注入 duplicate、replay、delayed-old-message、equivocation、aggregator crash 五类攻击，测量纳入偏差、隐私预算不平衡、错误接受率、消息量和延迟。

### 第一版理想功能：`F_fair-async-SA`

对每个模型版本 `v` 和逻辑 epoch `e`，功能接收客户端提交：

```text
Submit(i, v, e, nonce, x_i)
```

功能维护唯一状态键 `K = (i, v, e)`：

1. `K` 首次提交且格式有效：记录 `x_i`，返回 `accepted`。
2. `K` 再次提交：不新增输入，返回 `duplicate`。
3. `v` 或 `e` 已关闭：拒绝提交，返回 `stale`。
4. 达到策略要求的最小集合大小 `rho`：冻结集合 `S(v,e)`，输出
   `y = Σ(i ∈ S(v,e)) w_i x_i` 与证书摘要。
5. 集合冻结后，任何新提交不得改变该 epoch 的输出。

理想功能不暴露单个 `x_i`，只向授权客户端输出 `(v, e, S_digest, y, certificate)`。第一版可把 `y` 视为理想功能输出；密码学实现再用 PVSS mask removal 逼近该接口。

### 第一版协议消息流

```text
Client i -> Aggregators:
  COMMIT(v, e, nonce, C_i, PVSSProof_i, Sig_i)

Aggregators -> Aggregators:
  ECHO(i, v, e, nonce, digest(COMMIT))

Aggregators -> Aggregators:
  INCLUDE(v, e, {K_i}, quorum-signature)

Aggregators -> Aggregators:
  SHARE-SUM(v, e, Σ shares_i, proof)

Aggregators -> Client:
  RESULT(v, e, aggregate, certificate)
```

证书至少绑定：`v`、`e`、排序后的唯一键集合 `{K_i}`、集合摘要、聚合承诺。验证器拒绝：重复 `K_i`、版本过期、epoch 不匹配、集合摘要不一致、签名 quorum 不足的结果。

### 首要证明性质

- **At-most-once inclusion**：对任意正确聚合器接受的证书，任意 `K=(i,v,e)` 至多出现一次；重放不会增加聚合权重。
- **Certificate consistency**：任意两个正确客户端接受的同一 `(v,e)` 证书，要么证书相同，要么至少一个验证失败；因此不存在两个都有效的冲突 inclusion set。
- **Inclusion fairness**：满足参与条件的客户端不能被正确聚合器永久排除；在随机纳入版本中，长期纳入频率与策略分布一致，误差由明确参数界定。

暂不证明学习收敛、DP、恶意客户端更新质量；这些属于后续层。

## 1. 已有材料归档

| 文档 | 主要问题 | 可借鉴机制 | 明显缺口 |
|---|---|---|---|
| `Buffalo A Practical Secure Aggregation Protocol for Buffered Asynchronous Federated Learning_by_PaddleOCR.md` | Buffered AsyncFL 下的 SA | LWE 掩码、assistant、客户端验证聚合完整性 | 主要面向缓冲异步；与强拜占庭共识/通用动态聚合集合的结合仍可深化 |
| `Privacy-Preserving Federated Averaging with Byzantine Aggregators in Asynchronous Networks_by_PaddleOCR.md` | 完全异步网络、拜占庭聚合器、隐私与公平纳入 | 多聚合器、LWE 掩码、阈值签名、可验证 shuffle、公平 inclusion | 协议复杂；可研究更清晰的共识抽象、更强的可组合安全定义与更低通信 |
| `Catalyst_Asynchronous_Byzantine-Robust_Federated_Learning.pdf_by_PaddleOCR-VL-1.6.md` | 异步训练中的 Byzantine model poisoning | 对最快更新聚类、处理慢客户端 | 服务器可信；不是密码学 SA，不能防梯度泄露/恶意服务器 |
| `Byzantine-Robust_Asynchronous_Federated_Learning_via_Feature_Fingerprinting.pdf_by_PaddleOCR.md` | 无可信 IID 公共数据时识别恶意模型 | feature fingerprint、恶意更新过滤 | 依赖模型可分性/公共知识；不是 SA，不能解决聚合可验证性 |

## 2. 外部文献入口

### 2.1 直接相关，优先精读

1. **BASA — Buffered Asynchronous Secure Aggregation for Cross-Device Federated Learning**  
   arXiv: `2406.03516`。核心是 buffer 化异步聚合、客户端只与服务器进行一轮通信、不依赖客户端同步交互。重点看：buffer 形成、掉线处理、一次通信假设、对传统 SecAgg 的改造边界。
2. **Buffalo — A Practical Secure Aggregation Protocol for Buffered Asynchronous Federated Learning**  
   CODASPY 2025，DOI: `10.1145/3714393.3726498`。重点看：assistant 角色、LWE-based masking、聚合完整性证明、工程性能。
3. **Privacy-Preserving Federated Averaging with Byzantine Aggregators in Asynchronous Networks**  
   arXiv: `2601.04930`。重点看：完全异步网络、`n_a > 3t_a`、公平 inclusion、聚合器阈值签名、客户端无交互设计。这是与你的 HoneyBadger/Dumbo 背景最直接的交叉点。
4. **Quantized and Asynchronous Federated Learning**  
   arXiv: `2410.00242`。重点看：buffer、量化误差与 staleness 的耦合、与 SA 的兼容性。适合连接密码学通信开销与学习收敛分析。
5. **Asynchronous Federated Stochastic Optimization for Heterogeneous Objectives Under Arbitrary Delays**  
   arXiv: `2405.10123`。重点看：异步延迟与非 IID 偏差、residual/memory 机制、可兼容 SA 的优化抽象。

### 2.2 用于攻击面与对照实验

- Catalyst：异步 Byzantine-robust FL；可作为“训练鲁棒性但无 SA”的对照。
- BELISA：feature fingerprinting；可作为“服务器侧检测但依赖公共知识”的对照。
- SecureAFL：异步投毒检测与 Byzantine-robust aggregation；需核查其密码学隐私假设，避免把“安全”与“隐私”混为一谈。
- LATTEO：TEE + obfuscation 的异步隐私聚合；可作为 TEE 路线对照，但不建议作为主线，除非已有可信硬件条件。

## 3. 问题拆解

## 3.1 三篇直接相关工作的协议对照

| 项目 | BASA | Buffalo | Byzantine-aggregator 异步协议 |
|---|---|---|---|
| 异步层次 | buffered asynchronous；buffer 满后更新 | buffered asynchronous；面向工程落地 | fully asynchronous network；聚合器持续协作 |
| 主要参与方 | 客户端、服务器、辅助方 | 客户端、服务器、assistant | 客户端、多个 coordinator/aggregator |
| 客户端交互 | 目标为 one-shot、避免客户端两两交互 | one-shot；assistant 帮助构造聚合密钥 | 无 client-to-client communication |
| 隐私机制 | 加密/掩码聚合，重点解决 buffer 异步 | LWE-based masking；利用稀疏/哈希优化 | LWE masking；mask components 分布到 aggregators |
| 掉线处理 | 兼容异步 buffer，但需核对具体重构条件 | 通过 assistant 与异步密钥构造降低掉线依赖 | 客户端 crash-stop；聚合器也可 omission/halting |
| 恶意服务器/聚合器 | 重点不在 fully Byzantine aggregator | 客户端验证 aggregate integrity，防 model inconsistency | 明确容忍 fully Byzantine aggregators；要求 `n_a > 3t_a` |
| 聚合集合保证 | buffer 集合是系统状态，需重点核对是否有独立证书 | 证明更新被正确纳入全局模型 | inclusion、assignment、certification、threshold signature |
| 公平/去偏 | 主要处理 straggler 与 buffer | 主要处理可用性和完整性 | 处理快客户端偏置、慢客户端纳入、聚合器 inclusion fraud |
| 最接近的缺口 | 未充分利用异步共识处理集合一致性 | assistant 仍是额外信任/通信角色 | 机制完整但复杂；可重构为 ACS + PVSS/DKG 的模块化协议 |

**结论**：BASA/Buffalo 解决“异步时如何做隐私聚合”；第三篇进一步解决“聚合器也可能 Byzantine”。你的新颖性不能只停留在换成 PVSS，而应落在 **ACS 决定 inclusion set，PVSS/DKG 保护输入与重构，证书绑定集合和结果**。

### 3.1 安全目标必须分层

不要只写“安全聚合”。明确区分：

1. **输入隐私**：单个客户端更新对服务器、聚合器联盟、其他客户端不可见。
2. **聚合集合隐私**：聚合集合过小时，不能通过差分或重复查询反推出单个更新。
3. **聚合正确性**：输出确实对应一个被授权的客户端集合及其加权和。
4. **一致性**：诚实客户端不会收到不同的全局模型/不同的聚合历史。
5. **唯一计数**：同一客户端同一逻辑 epoch 至多被计入一次。
6. **活性**：拜占庭聚合器停止、延迟、分叉或发送不一致消息时，协议仍能继续。
7. **公平性**：快客户端不能无限重复贡献，慢客户端不能被系统性排除。
8. **学习鲁棒性**：密码学正确的恶意更新仍可能投毒；这是独立于 SA 的目标。

### 3.2 异步特有难点

- 无全局 round boundary，`epoch / buffer / inclusion set` 必须可证明地定义。
- 消息任意延迟，不能用同步超时直接判断客户端失效。
- 客户端可能重复上传、重放旧模型、跨 epoch 提交。
- 若先解密再做 Byzantine filtering，会暴露单个更新；若全程密文过滤，需可验证密文计算/承诺/证明。
- 异步更新天然带来 stale update 与 arrival bias；隐私公平不等于优化公平。
- Byzantine 聚合器可能对不同客户端发送不同集合和不同模型，需共识或 quorum certificate 阻断 equivocation。

## 4. 历史推荐主线（已废止）

### 方向 A：异步可验证安全聚合（首选）

**目标**：设计一个多聚合器协议，使客户端只需一次上行交互，聚合器在完全异步网络中完成：

- 客户端更新掩码与 PVSS/VSS 分发；
- 聚合集合的异步确认；
- 掩码和/聚合和的可验证重构；
- 对客户端掉线和聚合器拜占庭的容错；
- 由阈值签名或共识证书绑定 `(model_version, epoch, inclusion_set, aggregate_commitment)`。

**你的差异化点**：

- 用 HoneyBadger/Dumbo 风格的 asynchronous reliable broadcast / binary agreement / ACS 思想处理 inclusion set，而不是只依赖中心服务器的 buffer 状态。
- 用 DKG 生成聚合器阈值密钥，避免单一 setup dealer。
- 用 PVSS 让 mask shares、重构资格和可用性具备公开可验证性。
- 用 certificate 绑定聚合结果，防止 equivocation、重复计数和跨版本重放。
- 将“隐私安全”和“共识安全”写成可组合模块，给出清晰 adversary composition。

### 方向 B：低通信异步 PVSS 聚合

目标是保留 A 的安全目标，但减少全互联 share 分发：

- 聚合器数量 `m = O(log n)` 或小常数；
- 客户端只上传一个压缩密文/掩码和少量 PVSS 证明；
- 聚合器通过 share-sum 与阈值重构得到聚合掩码；
- 只对 commitment、集合摘要和模型版本做共识，不对高维模型向量做共识。

适合做系统型论文；关键指标是 client uplink、aggregator traffic、proof size、重构延迟。

### 方向 C：密码学 SA + Byzantine-robust 学习（第二阶段）

先完成输入隐私和可验证聚合，再研究密文状态下的鲁棒聚合：

- secure clipping / norm proof；
- 对坐标中位数、trimmed mean、Krum 类规则的可验证近似；
- 或采用“先 SA 得到至少 `rho` 个更新的 DP/noisy aggregate，再做集合级鲁棒性”的折中。

不建议第一篇就同时解决通用密文鲁棒聚合、完全异步共识、DP 和收敛；问题面会失控。

## 5. 历史协议骨架（已废止）

设客户端数 `n_c`，聚合器数 `n_a`，最多 `t_a` 个 Byzantine 聚合器，要求 `n_a > 3t_a`。

1. **DKG setup**：聚合器运行异步 DKG，得到阈值解密/重构密钥与验证密钥。
2. **Client commit**：客户端收到模型版本 `v`，本地计算更新 `g_i`，裁剪后生成随机 mask `r_i`，发送 `Enc(g_i + r_i)`、承诺和 PVSS proof。
3. **Reliable broadcast**：聚合器可靠广播客户端提交摘要，过滤版本错误、重复 nonce、证明无效的提交。
4. **Async inclusion**：通过 ACS/异步二值协议决定本次 inclusion set `S_v`，要求 `|S_v| >= rho`，并输出集合证书。
5. **Aggregate shares**：聚合器对 `S_v` 的密文/承诺做加法，异步交换 share-sum 与 proof。
6. **Reconstruct**：达到 quorum 后重构 `sum_{i in S_v} r_i`，解除总 mask；任何单个 `g_i` 不被重构。
7. **Certificate**：生成 `Cert(v, S_v, C_sum, aggregate)`，其中 `C_sum` 是聚合承诺/摘要，阈值签名绑定全部元数据。
8. **Model update**：客户端只接受带有效证书且版本单调递增的全局模型。
9. **Replay/duplication guard**：客户端身份、版本、nonce、集合证书纳入唯一性检查。

## 6. 历史安全模型（已废止）

### 6.0 冻结版第一阶段模型

第一阶段只证明以下模型，不加入额外假设：

| 项目 | 冻结设定 |
|---|---|
| 网络 | 完全异步、可靠、消息最终送达；无已知延迟上界 |
| 聚合器 | `n_a` 个；最多 `t_a` 个 fully Byzantine；`n_a >= 3t_a + 1` |
| 客户端 | honest-but-curious；最多 `t_c` 个 crash-stop；第一阶段不允许 Byzantine client |
| 密钥 | 聚合器通过 DKG 生成阈值密钥；不信任单一 dealer |
| 输入 | 每个客户端每个 `(model_version, epoch, nonce)` 至多一次有效提交 |
| 聚合 | 加法聚合/加权和；不做密文排序、中位数、Krum 或其他鲁棒统计 |
| 输出 | 只有满足最小集合大小 `rho` 且有有效 certificate 的聚合结果可被接受 |
| 证书 | 绑定 `model_version`、`epoch`、`inclusion_set_digest`、`aggregate_commitment` |
| 安全目标 | 隐私、正确性、一致性、唯一计数、活性；学习收敛单独分析 |

### 6.1 第一阶段明确不保证

- 不保证抵抗恶意客户端投毒；第二阶段再接入 Catalyst/BELISA 类鲁棒过滤。
- 不保证任意非 IID 到达分布下的统计公平；第一阶段只保证协议层可验证 inclusion 和无重复计数。
- 不把 DP 写进核心安全定理；先把 DP 作为可插拔的集合级输出保护。
- 不要求共识节点对高维模型向量运行 ACS；共识只处理集合摘要和协议元数据。

### 网络

- 完全异步、可靠但无已知延迟上界；
- 正确消息最终送达；
- 客户端可 crash-stop；聚合器可 Byzantine，包括 equivocation、omission、replay、premature halt。

### 隐私敌手

分别分析：

- 单个诚实但好奇聚合器；
- 不超过 `t_a` 个聚合器串谋；
- 恶意服务器与聚合器串谋；
- 恶意客户端与聚合器串谋；
- 自适应敌手是否能在提交后腐化参与者。

### 不要默认的假设

- 不要默认服务器可信；
- 不要把 TLS 当作 SA；
- 不要把 Byzantine-robust aggregation 当作输入隐私；
- 不要把 DP 当作聚合正确性证明；
- 不要把最终模型一致性当作客户端更新未泄露的证明。

## 7. 历史评估矩阵（已废止）

| 维度 | 必测对象 | 建议指标 |
|---|---|---|
| 隐私 | 单客户端更新、少量集合、重复查询 | 模拟器视角下不可区分性/泄露实验、最小集合阈值 |
| 正确性 | 篡改集合、篡改 share、篡改 aggregate | 验证成功率、错误输出拒绝率 |
| 一致性 | equivocation、不同客户端不同模型 | 分叉率、证书冲突检测时间 |
| 活性 | `t_a` 聚合器停止、消息任意延迟 | 完成率、最坏消息轮数/异步阶段数 |
| 公平 | 快慢客户端、非 IID 到达率 | inclusion frequency、贡献偏差、隐私预算偏差 |
| 效率 | 模型维度、客户端数、聚合器数 | client/server CPU、通信字节、proof size、wall-clock |
| 学习 | IID/non-IID、staleness、投毒 | accuracy、loss、收敛速度、攻击成功率 |

对照组至少包括：明文 AsyncFL、BASA、Buffalo、同步 SecAgg、无密码学 Byzantine-robust AFL。若实现成本允许，再加多服务器/TEE 方案。

## 8. 旧主线工作清单（已封存）

- [x] 精读 BASA：记录其 honest-but-curious 范围、一次通信和掉线条件。
- [x] 精读 Buffalo：整理 assistant、LWE mask、aggregation integrity 的消息流程。
- [x] 精读 Haven++：记录 ACSS-complete、单 dealer packing、batch proof、双门限 reconstruction。
- [x] 精读 Willow/OPA：记录 one-shot、动态参与、aggregation ID、residual attack 和至多一次纳入。
- [x] 精读 NFSA：记录两层 SS、CRT packing 和 semi-honest 限制。
- [ ] 精读 arXiv:2601.04930：把其 inclusion/certification 与 HoneyBadger/Dumbo 的 ACS 对照。
- [x] 建立三篇直接相关协议对照表。
- [x] 冻结第一阶段最小安全模型。
- [x] 修正 B0：区分 `B0-complete` 与 `B0-recovery`，不再把 ACSS-complete 和缺失份额同时作为前提。
- [x] 写出 B0/B1 第一版增量成本公式。
- [x] 完成 Haven++/Willow/OPA/BASA/Buffalo/NFSA 覆盖检查。
- [ ] 建立“安全目标—协议组件—可证明性质—实验指标”四列表。
- [x] 改写 ideal functionality：`F_fair-async-SA` 作为历史版本；新主线改用一致授权与输出释放接口。
- [ ] 证明最低门槛：隐私、唯一计数、聚合一致性、活性；暂不加入密文 Byzantine filtering。
- [ ] 实现 toy protocol：小维度向量、异步消息调度、聚合器 crash/Byzantine 注入。
- [ ] 记录通信复杂度：客户端上行是否 `O(1)` 条消息，聚合器间通信是否随模型维度线性增长。
- [ ] 评估“共识只处理元数据，密码学聚合处理向量”是否足以支撑完整性证明。
- [x] 将重复计数/重放降为 `single-consumption` 安全性质，不单独作为论文主问题。
- [x] 锁定 B0：区分 ACSS-complete 的直接聚合路径与弱就绪条件下的逐输入恢复路径。
- [x] 锁定 B1：已授权 `D` 下的函数级响应与直接释放。
- [x] 完成 B0/B1 增量消息、字节量、关键路径公式的第一版。
- [x] 写 `F_authorized-release`，明确允许输出与禁止中间泄漏。
- [x] 完成两类反例；继续/终止裁决待成本公式完成后执行。
- [x] 将唯一键、上下文绑定和 `at-most-once inclusion` 标记为已有安全基线，不再作为新颖性主张。
- [ ] 证明弱就绪证据的可生成性、函数响应隐私和 B1 的故障条件。
- [ ] 对比 B1 与 Haven++/OPA/Willow 的组合是否产生新的功能能力，而非组件拼接。

## 9. 旧论文问题候选（已封存）

1. **Asynchronous Verifiable Secure Aggregation with Byzantine Aggregators**：完全异步、无客户端间通信、可验证 inclusion 与 aggregate certificate。
2. **ACS-SecAgg**：把 HoneyBadger/Dumbo 的 ACS 作为异步聚合集合层，PVSS 作为输入隐私层。
3. **Fair and Replay-Resistant Secure Aggregation for Asynchronous FL**：聚焦重复计数、快客户端偏置、慢客户端公平纳入。
4. **Composable Security for Asynchronous Secure Aggregation**：给出 `F_async-SA`，组合 DKG/PVSS/ACS/threshold signature，并做实现评估。

该候选已封存。新的待证伪题目见本文件 §0.2；在最强基线核查完成前，不定投稿题目。

## 10. 旧主线关键风险（已封存）

- **范围过大**：完全异步 + Byzantine clients + Byzantine aggregators + DP + 密文鲁棒统计，第一版不应全做。
- **安全目标混杂**：SA 保护输入隐私；Byzantine-robust FL 保护训练效果；两者必须分别定义。
- **PVSS 成本过高**：先做低维 toy benchmark 和通信量公式，再决定是否上高维 packed/LWE。
- **异步共识不等于学习收敛**：需要单独处理 staleness、arrival bias、非 IID 与公平 inclusion。
- **论文新颖性误判**：先对照 BASA、Buffalo、arXiv:2601.04930 的协议假设与保证，避免只换密码学组件。
- **现有能力重复**：Willow 已覆盖 one-shot 动态参与、aggregation ID 和至多一次纳入；OPA 已覆盖上下文绑定与 residual attack 防护；这些不能再作为主贡献。
- **可用性谓词偷换**：`ACSS-complete`、`LocalReady`、`EventualReady` 必须分别定义，不能用较弱谓词给 B1 创造优势后与较强 B0 比较。

## 11. 追踪日志

### 2026-09-09

- 确认研究入口：异步安全聚合，而非泛化的异步拜占庭鲁棒训练。
- 已有材料覆盖：BASA/Buffalo 类隐私聚合、多聚合器拜占庭聚合、Catalyst/BELISA 类训练鲁棒性。
- 初步主线：`ACS/inclusion consensus + PVSS/DKG + verifiable aggregate certificate`。
- 下一步：完成 3 篇直接相关论文的协议级对照表，随后冻结最小安全模型。
- 已完成：协议级对照表与第一阶段模型冻结。
- 新的下一步：定义 `F_async-SA` 理想功能，并画出 ACS、PVSS、DKG、certificate 的消息时序。
- 研究范围收窄：优先攻克重复计数/重放攻击，不再把完整异步安全聚合作为第一篇目标。
- 主线再次调整：以一致聚合授权与输出释放为主线；公平纳入降为扩展，重放防护降为 `single-consumption` 性质。
- 已完成：B0/B1 第一版对齐、`F_authorized-release` 初版、异构持有者与晚到份额两个最小反例。
- 下一步：填写成本公式，判断函数级恢复是否存在真实正区间；若无，终止 B1 主线。
- 已完成：阅读 Haven++、Willow、OPA、BASA、Buffalo、NFSA 转写并完成能力覆盖矩阵。
- 已修正：B0 分为 `B0-complete` 与 `B0-recovery`；成本公式改为同一 readiness 下的增量比较。
- 已确认：`single-consumption`、context binding、one-shot 和批处理均有直接先例，不再作为新颖性主张。
- 新的硬门槛：证明弱就绪证据可生成、B1 函数响应隐私成立，并在相同分享成本下严格优于 B0-recovery；否则终止候选。
- 详细复核 `/home/yzc/flagg/NOVELTY_AUDIT.md` §30–§36：A、B2、FairSample 均终止；其中“整个交集无创新空间”的结论过度外推，只关闭了具体候选。
- 核对 `/home/yzc/flagg/DIRECTION_1_PROACTIVE_ADKG.md` 与 `PROACTIVE_DKG_ANALYSIS.md`：主动异步 DKG/刷新原语本身也已有覆盖，不能直接作为新题目。
- 精读 `apss_keyrefresh_2022_1586.txt`：APSS 解决异步主动刷新，但把应用组合与安全证明留作 future work；由此形成新的待证伪主线“客户端离线的多客户端掩码份额批量刷新”。
- 精读 `Achieving Long-Term Privacy_by_PaddleOCR.md`、`Non-Forward Secure Aggregation via Two-Layer SS_by_PaddleOCR.md`：前者是 honest-but-curious 的应用层分组，后者明确不是前向安全；两者均不能直接覆盖新主线。
- 确认 graft：`/home/yzc/flagg/graft` wiring graph 检查通过；论文 Markdown 不在代码图中，因此本轮对转写文档采用直接阅读，未把“无 graft 命中”误判为文献不存在。
- 本轮修正：根据“允许放松假设、改变网络或增强敌手模型”的研究要求，不再把同模型的 bDPSS 覆盖外推为整个前向安全交集终止。
- 历史记录（后续已停止）：首要主线曾改为 `Adaptive-Query-Safe Asynchronous Secure Aggregation`；核心是跨多次精确输出的自适应查询历史、Byzantine 消息调度与可组合隐私/活性的边界。
- 本轮边界：row-space、single-consumption、context binding 和 ACS/PVSS 仅作为已知基础或构造材料；主贡献必须是新的异步安全边界或严格资源分离。
- 本轮工具核验：`graft check /home/yzc/flagg` 通过；Graft 查询定位了现有聚合释放验证程序。论文转写文档不在 wiring graph 中，相关文献结论继续以直接阅读和外部来源核对为准。
- 用户明确停止 adaptive-query / 分布式数据库式查询历史方向；该候选仅作为历史记录保留。
- 当前主线切换为 `Long-Lived Mobile-Adaptive Secure Aggregation without Global Epochs`，重点研究长期最终全体腐化、重叠会话、会话级状态消费与 past-update forward privacy。
- 已区分 `adaptive-total`、`epoch-mobile`、`continuous-mobile` 和 `session-lifetime-bounded mobile`；不再把“单次 adaptive”或“每 epoch mobile”误写为长期连续移动安全。
- 已建立三条候选下界：历史密钥暴露、仅同时腐化阈值不足、全体诚实纳入与有限擦除不可兼得。
- 已新建 `long-lived-adaptive-corruption-audit.md`，记录基线矩阵、ABKL 攻击适用边界、最小正向协议、关闭条件和四周计划。
- 已完成 N2/N3 的 `v0` 形式化：给出异步腐化事件模型、即时串行腐化轨迹、crash/delay 成对执行及随机化扩展。
- 已确认：`session-lifetime-bounded` 是敌手执行的可接受性条件，纯异步协议本身不能在两个诚实步骤之间阻止敌手连续腐化多个节点。
- 已确认：N2 不需要 epoch/reshare，N3 使用 SA 的客户端纳入与集合终结语义；二者都不是 ABKL Theorem 6 的直接实例。
- 当前裁决：N1/N2/N3 只够作为论文引理；下一主门槛是 Exposure--Finalization Frontier 及匹配构造，否则主线关闭。
- 已补充移动 Byzantine 恢复语义：`Release` 不自动恢复可信状态；`Cure` 后节点不追赶旧会话私密状态，只以新密钥加入未来会话。
- 已识别可用性对偶攻击：无限速移动敌手可逐个删除未输出份额；每会话累计暴露预算同时约束隐私泄漏与状态破坏。
- 已完成 `F_LL-SA v0.1`：定义 `RAW/COLLAPSED/PUBLISHED/CURED` 生命周期、原子 `CollapseErase`、腐化返回值和条件输出交付。
- 已构造最强黑盒基线 `B* = per-session keys + adaptive PVSS/AVSS + RBC + ACS/MVBA + verifiable aggregate shares + erasure`。
- 新风险：未来全体腐化会泄漏普通长期认证键并允许伪造旧 `sid` 消息；长期一致性需要会话认证键隔离、前向安全签名、不可回滚日志或理想认证之一。
- 当前覆盖判断：Willow/OPA 已覆盖 one-shot 与迟到排除，Aion 已覆盖“固定集合后聚合份额释放”，协议流程本身不是贡献。
- 下一唯一门槛：检查 pre-close 原始份额与 post-close 全部聚合份额的联合模拟能否由现有 adaptive PVSS 直接组合；若可以，关闭协议创新叙事。
- 已完成联合分布检查：用 `L_E(X)=product_{i in E}(X-i)/(-i)` 构造输入平移；当 `|E|<=t` 时，全部 pre-close 暴露份额和完整 post-close 聚合多项式逐值保持不变。
- 该映射是随机系数空间双射，可按会话独立应用到任意重叠 `sid`；分享层组合属于标准 Shamir 线性隐私，不构成主定理。
- 已关闭“aggregate-then-erase 需要新代数证明技术”的叙事。剩余门槛只在 adaptive PVSS 在线重编程、无 epoch 会话键生命周期和低成本 post-compromise recovery。
- 新增强基线：Libert--Yung 2012 已实现稳定公钥、非交互本地更新和 adaptive forward-secure threshold encryption，但依赖全局有序 period，且不提供同态聚合。
- 新增强基线：Green--Miers 2015 已用 puncturable encryption 解决单接收者异步消息的无序退休；2026 puncturable FHE 已覆盖单键同态穿孔线索。
- 当前唯一候选收敛为 unordered-session puncturable threshold aggregation：稳定公钥、加法同态、授权聚合部分解密、按 `sid` 无序穿孔、穿孔后全体当前密钥暴露。
- 已否定 `Omega(n*d)` 是最强简单基线：OPA/Buffalo 式短种子同态 mask 配合 `n` 个独立 puncturable PKE，可把客户端成本降为 `O(d+n*kappa)`，且委员工作与 `d` 无关。
- 当前主叙事升级为“输出完成不等于安全退休”：`CC_sid` 固定聚合输出，`PC_sid` 单独认证足够多本地穿孔；对最终旧能力上界 `b_sid`、`q`-out-of-`n` 门限和 `a` 个确认，精确最坏条件修正为 `n-a+min(a,b_sid)<q`，可行区间内才是 `n-a+b_sid<q`。
- 在完全异步活性 `a<=n-f` 与解密抗 withholding `q<=n-f` 下，可行性要求 `b_sid<=n-2f-1`；在 `n=3f+1,b_sid=f` 时最紧点为 `q=a=2f+1`。常见 `q=f+1` 要求全体 `n` 确认，无法容忍一个 Byzantine 沉默。
- 已写选择性目标会话游戏 `G_upm-sa^sel`：同聚合挑战输入、少于 `q` 个穿孔前旧份额、授权聚合解密转录、满足门限的退休证书及穿孔后全体当前状态暴露。
- 密码学对象收窄为短 mask key 的紧凑无序穿孔阈值加法同态加密，不再追求对 `d` 维梯度做 puncturable FHE；若不能将 `n` 个短 ciphertext 降为一个或给出新组合证明，则不作为主贡献。

### 2026-09-10

- 使用 Graft 检查当前目录，图同步通过；论文 Markdown 不进入代码 wiring graph，因此继续直接阅读与外部元数据核验。
- 将 N4 提升为 `Robust-Hitting Theorem`：`PF(A,b)` 等价于每个解密集合 `D` 满足 `|A intersection D|>b`，阈值访问结构的最小退休集合为 `tau_b(Gamma_q)=n-q+b+1`。
- 外部检索发现新的强基线：Agarwal et al., IEEE S&P 2026, `10.1109/SP63933.2026.00175`。在取得全文前，禁止把加权批量阈值解密或 aggregate-only batching 写成创新。
- 已取得并阅读 ePrint `2025/2115` 原文：wBTE 输出选中批次的逐条明文，使用聚合 PRF key 加每个 `K_i*` 修复点；因此与 aggregate-only SA 存在接口级黑盒分离，不能直接组合。
- 将 privacy-finality 扩展为加权访问结构版本：每个授权解密集合与退休集合的交集权重必须超过会话暴露预算。
- 修正 NR 的逻辑边界：`PC_sid` 形成不等于每个节点都已退休；引入可复活集合 `R`，得到有效集合 `B_eff=B union R union (P-A)`，并把安全条件改为对 `A-R` 的 Robust-Hitting。
- 将主叙事升级为“吸收态退休”：`PF_sid` 不是一次性证书属性，而是要求所有异步可达状态都不能重新引入已退休 `sid` capability。
- 当前裁决：`B_seed` 已确认是可行匹配基线，但不作为构造创新；理论主线继续聚焦 Robust-Hitting、吸收态退休和 cure/recovery 边界。compact 单 ciphertext 只有在能同时降低 `O(d+n*kappa)` 成本并支持可验证状态恢复时才继续。
- 本轮精读确认：DPE 2026 不覆盖阈值聚合；wBTE 的最近邻构造本身依赖非黑盒代数耦合，不能被当作现成黑盒组合。
- 本轮检索新增证据：ACNS 2026 DPE 仅扩展用户/机构撤销、恢复和委托；wBTE 则在阈值 PRF 结合处需要非黑盒 CRS 耦合。两者均提高基线审计质量，但没有关闭 `F_agg-only + per-sid puncture + long-lived mobile` 的联合缺口。
- 对 cure/recovery 基线的核对：ABKL 明确以延迟旧 reshare 消息和后续腐化攻击；APSS 要求新份额生成后删除旧份额，并指出这会与异步 handoff 活性耦合；DyCAPS/bDPSS 则使用 local epoch、handoff、forward-secure channel 或每 epoch setup/旧状态隔离。它们没有直接给出无全局 epoch、稳定 PE 状态恢复和 `PF_sid` 的联合定理。
- 本轮收紧 `Cure--Finality Trilemma`：原先的“无条件三难”过强，因为带单调 tombstone 的协议可以同时支持 `Cure`、稳定公钥和 no-resurrection。现在改写为 `Causal-Fence Necessity Theorem`：在稳定公钥、完全异步迟到消息和恢复活性下，若恢复路径不携带支配 `sid` 终结的单调 capability state，也不改变密钥世代，则延迟旧消息可按 `E_before/E_after` 不可区分执行重新安装旧能力。
- 新的主叙事命名为 **Privacy Finality as Causal Revocation**：`PF_sid` 不是时间窗口内的 forward secrecy，而是会话偏序上的 capability revocation；`PC_sid` 必须同时满足 `Robust-Hitting` 和吸收态状态转移。普通 forward-secure encryption 只解决 key generation 的世代顺序，不能替代异步 `sid` 终结事实的合并与恢复传播。
- 增加了显式 tombstone 的表示下界：若不使用 accumulator、全局排序器或可信 epoch，并要求表示 `M` 个可并发会话的任意退休子集，则显式状态需区分 `2^M` 种集合，即至少 `M` 位。该下界不外推到密码学 accumulator；真正的构造出口是无全局序的可合并 `O(lambda)` capability state 及其短证明。
- `B_seed` 已被正式定位为匹配构造：在不要求 `Cure` 恢复已穿孔 PE 状态时，由独立委员 PE、Shamir mask 分片、聚合分片和 puncture/erase 直接组合；它证明 Robust-Hitting 的上界可达，但不是新的原语。后续只有同时实现 `O(d+kappa)` 客户端短 ciphertext、可验证 `T_i` 恢复和 `PF_sid` 组合证明，才继续协议构造。
- 当前唯一可证伪问题：是否存在无全局 epoch、可交换/结合/幂等合并的 `O(lambda)` 级 per-node capability state，使任意并发 `sid` 的退休在 `Cure` 后保持 no-resurrection，且不恢复已退休会话的私密状态。下一轮先做抽象接口、无 fence 攻击和 accumulator/CRDT/hash-chain 三类方案审计。
- 初步状态表示审计：显式 CRDT tombstone 正确但状态随并发会话数增长；hash-chain 只能表达全序；Merkle root 只压缩摘要且旧 capability 没有退休后的新证明；动态 accumulator 只有结合“可被后续添加失效”的 proof-carrying capability 才可能解决问题。后续构造目标因此改名为 `revocation-invalidating capability`，并明确排除“重新签发所有未退休 capability”的伪压缩方案。
- accumulator 基线复核：Li--Li--Xue 2007 已覆盖 membership/nonmembership proof，Camenisch--Kohlweiss--Soriente 2009 明确把撤销时的 witness update/distribution 作为核心成本，Mashatan--Vaudenay 2013 讨论 fully dynamic universal accumulator。因此创新不能是“使用 accumulator 压缩 tombstone”，而必须解决异步 Byzantine `Cure` 后的 witness-update finality。
- 新增强基线：Schumm--Mukta--Paik 2023 的 accumulator 撤销方案声称通过三个 accumulator、epoch 和 state transition 消除 witness update。它不能直接关闭当前问题，反而明确了对照边界：本主线禁止把 epoch/state transition 作为隐藏的全局因果序，且还要求 Byzantine 异步 `Cure`、并发 `PC_sid` 合并和 `Robust-Hitting`。
- 新增 `Stale-Proof Dilemma` 接口引理：固定旧 proof 若没有 `Delta`/撤销证明或可交换的 `Update`，就无法同时实现 selective invalidation 与 non-interference；直接拒绝全部旧 proof 会误伤未退休会话，继续接受则产生 resurrection。当前构造候选正式改名为 **Asynchronous Witness-Update Finality**。
- 当前审计问题进一步收窄为：更新材料是否能迟到、重放但不可回滚；并发 `PC_sid` 是否可交换合并；`Cure` 是否只需恢复 `T_i` 与公开更新材料；以及该状态是否仍满足 `A_sid in H_b(Gamma_dec)`。若必须逐 tombstone 更新或重新签发 capability，则分别退化为显式 `O(M)` 状态或 epoch/rekey。
- 固定最小理想功能 `F_AWF`：本地摘要 `T` 允许 `O(lambda)`，公开更新材料可按会话数增长；`Merge` 必须交换/结合/幂等，`Recover` 不得恢复目标 PE 状态，且 `PC_sid`、`F_AWF`、`Robust-Hitting` 分别承担证书、吸收态和未来暴露安全。后续所有候选方案按该接口审计，不再接受隐藏在线撤销查询的黑盒论证。
- 发现更关键的控制面/数据面分离：`F_AWF`/accumulator 只能阻止旧消息重新安装 capability，不能恢复委员的已穿孔 PE 状态。若 `Cure` 恢复 `sk_i^0`，未来状态暴露立即破坏 `PF_sid`；若恢复 `sk_i^{sid}`，则需要新的 `RecoverPuncturedState(T_i, distributed_state, PC_frontier)`，其输入必须受 tombstone 支配且不能先重构旧密钥。
- 主线叙事进一步收紧为 **Privacy Finality is Recoverable Puncture**：真正的新技术接口不是单独的 accumulator，而是公开吸收态状态与 threshold/share-compatible punctured-state handoff 的组合。普通 forward-secure encryption、proactive DKG 和 `F_AWF` 均只覆盖其中一部分。
- 新增条件版黑盒分离定理：标准 VSS/DPSS handoff 只保持同一个秘密 `s`，因此 handoff `sk_i^0` 会恢复历史解密能力；先重构再 puncture 暴露旧状态；直接对 Shamir share 做一般非线性 puncture 会产生 degree growth。只有 share-compatible puncture、key-switching 或新的分布式状态变换能实现 `RecoverPuncturedState`，所以“普通 DKG + 现成 PE”不是答案。
- 将数据面缺口形式化为 `Share-Compatible Puncturing`：`SPuncture_x(Share_t(k)) -> Share_t(P_x(k))`，不重构旧秘密、保持固定阈值并绑定 `PC_x/T_i`。新增 Shamir degree-growth barrier：对份额逐点应用次数 `delta>1` 的非线性 puncture 会把次数提高至 `delta*t`，连续穿孔继续增长；固定阈值只能依赖线性兼容状态、异步 degree reduction，或退化到 epoch/rekey。
- 当前 go/no-go 判据进一步明确：只有第 1 类 share-compatible primitive 或第 2 类非通用、可验证异步 degree reduction 值得继续构造；若只能使用第 3 类 key generation/epoch，则保留理论边界，不包装成新的协议构造。
- WBTE 近邻复核：它通过 `THE.Enc(K_i)` 的同态求和得到聚合 key，但依赖公开 `K_i*` 与聚合 key 逐条恢复 batch 明文；删除 `K_i*` 后标准正确性不成立。它也没有 threshold decryption state 的 `Puncture/Erase`，未来暴露仍可处理归档客户端 ciphertext，因此是批量选择性解密基线，不是 `RecoverPuncturedState`。
- 新颖性复核补充：Sun--Steinfeld--Sakzad 2022 的 incremental symmetric puncturable encryption 与 Derler 等 2021 的 Bloom Filter Encryption 都是单密钥、多次 puncture/高效状态更新基线；没有直接覆盖 threshold/share-compatible punctured-state handoff。该检索只作为覆盖审计，不作为新颖性证明。
- 正式定义新原语 `RPTA`（Recoverable Puncturable Threshold Aggregation）：短 mask key 的 `Enc/Eval/PartDec/Combine/Puncture/Contribute/Recover`，绑定唯一 `D=(sid,S,w,H_ct,H_out)`，不直接加密梯度。
- 安全定义拆为两个游戏：`G_RPTA^sel` 固定单目标 `sid` 和唯一授权聚合，两组 challenge keys 具有相同加权和；`G_RPTA^rec` 单独验证 Byzantine `Cure/Recover`、已退休会话拒绝和未来会话服务。首版明确不研究自适应挑战或多线性查询历史。
- 固定组合定理目标：`RPTA + retirement-liveness sandwich + unique CC context + atomic Puncture/Erase + key-homomorphic mask` 推出长期移动腐化与最终全体当前状态暴露下的 selective aggregate-only privacy finality。下一步只需审计该定义是否可由某个最小构造满足。
- RPTA 接口审计完成：删除把秘密 `SK_i^T` 交给公开 `VerifyState` 的错误接口，拆为本地 `CheckInstall_i` 与只看承诺的 `VerifyRecovery`；恢复被明确为“互异贡献者集合为目标节点恢复一个当前份额”，所有消息绑定 `rid/i/T_req`。
- 明确擦除边界：公开证明只能验证状态转换/承诺关系，不能证明物理擦除；诚实节点在原子替换和擦除后才签 `ack_i`，Byzantine 假确认和诚实节点退休前旧状态暴露均累计计入历史集合 `B`。
- 加入正式状态机 `Active -> Retiring -> Punctured -> Active` 与 `Active -> Recovering -> Active`。恢复期间若收到更新的 `PC_sid`，只能提升 frontier 或取消重启；落后恢复输出永久不能安装，从接口上关闭 delayed-recovery resurrection。
- 收紧长期移动腐化模型：敌手可跨会话、跨恢复实例长期移动并保留所有副本，但单个未完成恢复实例内的易失状态暴露累计至多 `f` 个参与者。仅限制“同时腐化”在完全异步无限延迟下不足以支持 proactive repair，这一必要限制必须显式出现。
- 新增条件下界：在线性功能状态模型中，若本地穿孔映射 `P_tau` 精确杀死 `ell_tau` 且完全保持所有 `ell_sigma (sigma!=tau)`，则所有 capability 泛函线性无关，状态维数至少为可独立退休标签数 `M`。结合 Shamir degree-growth，精确、任意标签、无交互、share-compatible 的 compact puncture 不可能靠逐份额仿射更新获得。
- 新增最小见证 `BF-RPTA`：用 `m` 个独立 threshold PKE 坐标，客户端把同一 mask key 加密到会话的 `k` 个 Bloom 坐标；穿孔只删除坐标份额，恢复只 repair 未删除坐标。它不需要非线性 `SPuncture`，privacy 无假阴性，但以 `epsilon` 级未来会话 liveness error 换取 `m=Theta(R log(1/epsilon))` 状态。
- BF-RPTA 增加恶意标签边界：标准假阳性界不能用于攻击者看见公开哈希后反复 grinding 的 `sid`；协议必须先承诺 `sid`/元数据，再产生不可偏置高熵盐并形成客户端提交前的 `SC_sid`，最终由 `CC_sid` 承诺 `H(SC_sid)`。该问题只影响未来 liveness，不放松退休会话 privacy。
- 当前投稿叙事升级为 **Recoverable Puncture Tradeoff**：研究稳定公钥、完全异步移动腐化下，状态大小、穿孔交互和未来 liveness error 的最优权衡。最小论文包是 Robust-Hitting 刻画、恢复竞争状态机、线性状态下界和 BF-RPTA 近匹配构造；阈值化坐标删除若已有直接先例，则构造降为基线而不影响理论主线。
- 修正 BF-RPTA 的隐藏假设：普通 threshold IND-CPA 不自动覆盖 challenge-related 聚合解密转录；但 TACITA modified STE 的 extended CPA 游戏已经覆盖静态、one-shot、等和消息的 aggregate-opening 核心。此前“优先实例化 `AO-THE`”的结论已过时。
- 将编译器输入拆为 `Static-AO + RCL`：TACITA 可作为静态数据面基线；真正新增组件是长期 `Puncture/Contribute/Recover/CheckInstall` 状态层。TACITA 使用静态腐化并明确排除 adaptive corruption，也没有 puncture、frontier 或 repair。
- 新增 `Puncture-Recursion Lemma`：若把静态解密 key 放进持久备份，而 recovery authority 未按退休标签穿孔，则未来暴露恢复访问集即可重放备份并复活旧能力。因此 `TACITA + ordinary VSS/DPSS backup` 不是长期构造；压缩为一个全局恢复密钥只会把同一问题递归到恢复层。
- 新增 `Repair-Closure Characterization`：令 `Cl_rec(X)` 为从旧能力集合 `X` 经所有合法恢复边反复扩张得到的闭包，则 privacy finality 精确要求对每个 admissible `B` 都有 `Cl_rec((P-A) union B) notin Gamma_dec`。Robust-Hitting 只是退休标签没有任何恢复边时的特例。
- 得到 repair-amplification 推论：若任意 `q_rec` 个 helper 可恢复任意目标旧份额，而数据解密门限为 `q_dec`，则最坏条件为 `n-a+min(a,b)<min(q_dec,q_rec)`。在 `n=3f+1,b=f,a<=2f+1` 下，`q_rec` 与 `q_dec` 都必须至少为 `2f+1`；低门限 cure 会直接破坏长期隐私。
- 给出最小正向见证 `current-share-only repair`：不保存可重放 backup，只从当前坐标份额用新鲜、事后擦除的异步线性修复恢复未来坐标；退休时同时删除 direct share、coordinate-local repair metadata 和未完成恢复状态。Robust-Hitting 使退休坐标的 recovery closure 不扩张，而未来坐标仍有 `n-f>=q_rec` 个帮助者。
- 明确构造门槛：朴素逐坐标 VSSR/AVSS 已能实现上述见证，代价为修复一个节点时 `O(m*C_LSR(n))` 通信，不能单独作为顶会贡献。正向结果必须给出实例内累计自适应腐化的完整异步组合证明，或通过 packed/batched repair 严格改善逐坐标恢复复杂度。
- 新增条件空间下界：把 coordinate-deletion frontier 看成无 false negative、false positive 至多 `epsilon` 的 approximate-membership 表示，存储至多 `R` 个退休标签需要 `R log_2(1/epsilon)-O(R)` bits；BF frontier 的 `Theta(R log(1/epsilon))` 在该模型内常数因子近最优。
- PKC 2020 modular PPE 精读裁决：其 exact puncture 每次采样并拆出新 master component，punctured key 大小为 `Theta(R)`；这绕开固定维线性映射下界，但阈值化需要异步共享随机 component，且原语是 KEM、没有客户端 ciphertext 的 homomorphic `Eval`，不能直接视为 RPTA。
- BEAST-MEV 原文复核：穿孔的是每个客户端 PRF key，委员会聚合解密 `sum_i k_i` 后结合逐项 punctured keys 恢复全部批消息；它不退休委员会 threshold state，因此是强批处理基线而非 RPTA。
- LightBEAT 全文裁决完成：HIDP 穿孔的是客户端公开 PRF key；委员会仍持有普通 threshold-ElGamal shares，`Combine` 恢复批内每条消息。其 HIDP adaptive security 是 chosen punctured identity 的 ROM 安全，full protocol 明确为 static corruption；不覆盖 committee-state puncture、mobile exposure 或 cure/repair。
- VSSR 全文裁决完成：recovery polynomial + DPRF 可作为逐坐标 `LSR` 基线，但标准游戏按 commitment 累计限制 `<k` 个 compromise/contribution/recovery 来源，且 proactive share recovery 明确留作 future work。退休必须删除 recovery-complete local state，而不只是 direct share；全局 DPRF 单独存在不自动导致复活，必须检查它与残留 coordinate state 的联合闭包。
- Silent Setup 全文裁决完成：FSE 依赖周期 key update；PCS 通过本地重采样并发布新 `pk/hint`。它说明“前向安全能保护时间前缀”，但不能保持稳定公共键并处理并发无序 `sid`。
- 动态委员会边界收紧：BEAST-MEV 只建议组合 proactive secret sharing 支持 churn。当前扩展定义为 `Project(T) -> Handoff(live coordinates only)`，并以跨配置 `Cl_{rec+ho}` 判断旧 capability 是否复活；动态 membership 不作为首篇工作的独立卖点。
- 当前最窄的下一步：证明 `Recovery-State Localization Barrier` 与 matching current-share-only protocol；然后把 `Handoff-Closure Preservation` 写成动态委员会推论。若仍只是逐坐标调用 VSSR 且没有新的组合安全或复杂度结果，则只保留理论刻画与下界。
- `Repair-Closure Characterization` 第一版正式证明已写入 `repair-closure-theorem-draft.md`：用 typed capabilities 和 derivation hyperedges 证明 Sound Reachability，并在 Composable Edge Realizability 下得到 matching attack；Robust-Hitting 与 `min(q_dec,q_rec)` 门限式均作为推论导出。
- 本轮发现并修正 `CheckInstall` 缺口：拒绝安装 stale state 不等于攻击者没有得到旧 share。若退休前 recovery contribution 可由未来 receiver/channel state 解封，旧 capability 已进入闭包。因此 RCL 接口升级为 generation authorization + post-finality transcript extraction resistance + stale-install rejection。
- 当前唯一下一步改为具体 `LSR` 审计：写出 VSSR/AVSS helper contribution 的代数式，判断归档 transcript 与未来状态能否恢复退休 share，再决定使用 target-ephemeral channel、forward-secure channel、coordinate-local metadata deletion 或 puncturable DPRF。

### 2026-09-10（resharing 基线审计后的主线修正）

- **VSSR 裁决：** 原生 `k=f+1` 触发 repair amplification；提高到 `2f+1` 在 `n=3f+1` 下又因 target exclusion 失去活性；masked-polynomial transcript 还会在未来 DPRF 暴露后展开为一组旧 shares；恢复状态不 state-complete。因此 VSSR 降级为具体反例和一次性恢复基线。
- **APSS 裁决：** 有异步 refresh 和删除旧 share 的机制，但采用静态腐化模型，目标是全局刷新而非缺份额 repair；不直接支持无序 per-`sid` retirement。
- **DyCAPS 裁决：** 最接近移动腐化、动态委员会和 forward-secure channel，但依赖 local-event epoch、相邻 handoff 和前一 handoff 的全员有效状态；不能直接推出本文的 future full-state exposure 下的 recovery closure。
- **Optimistic DPSS 裁决：** 可作为高效加密 handoff 基线，但 epoch/committee 接口和 ciphertext transcript 仍需重新绑定 application-level frontier。
- **主线名称更新：** `Frontier-Gated Selective Resharing (FGSR)`；live coordinate 执行 state-complete resharing，retired coordinate 关闭 generation/extraction/installation 全部边。
- **新最小参数：** homogeneous reusable repair 需 `n>=2f+b+2`；自然 `b=f` 时研究 `n=3f+2,q_dec=q_rec=2f+1`，不再把 `n=3f+1,q_rec=2f+1` 当作可行修复参数。
- **下一步唯一任务：** 设计固定委员会、单 coordinate 的 one-shot share-to-share FGSR；不复制 DyCAPS 四阶段 handoff，而验证共同 helper set、target-excluded liveness、state completeness、frontier transcript finality 和 recovery closure；未完成前不扩展到完整 FL compiler。
- **本轮执行结果：** 单 coordinate 的计数适配可行：`n=3f+2,t=f` 时，缺失 target 后仍有 `2f+1` 个正确旧节点，可共同生成新 sharing；resharing 本身同时完成 repair/refresh，并输出可继续 repair 的普通 current share。当前未证明的只剩共同 helper set、frontier transcript security 和 retired-coordinate closure 三个 reduction。
- **下一步收敛：** 不再复制 DyCAPS 四阶段；直接审计 one-shot share-to-share FGSR。若通过，再接入 `Static-AO`；若失败，记录精确失败边界。
- **构造修正：** FGSR v0.1 采用 `Authorize -> Parallel Reshare -> Aggregate/Install/Erase` 三道本文特有门控；每个 helper 以当前 share 为新 polynomial 常数项，resharing 同时完成 repair 和 refresh。必须由 availability-certified ACS 统一 `H`，并证明 `f_h(0)=z_h`。
- **安全不变量：** 所有 live 节点最终切换到同一 `F'`；target 只得到普通 current share；retirement 与 repair 按每 coordinate instance order 冲突解决；旧 subshare 的 plaintext、helper polynomial 和 receiver ephemeral key 在 commit/cancel/retirement 后擦除。
- **明确优化边界：** 暂不复制 DyCAPS 的 bivariate zero-polynomial 和四阶段 handoff；朴素 FGSR 通信仍为 `O(n^2)`，packed/batched AVSS 只在安全主定理完成后研究。
- **本轮文档同步：** `lsr-construction-audit.md` 第 21 节已标记为 superseded；`long-lived-adaptive-corruption-audit.md` 新增 One-Shot FGSR 审计接口；`privacy-finality-paper-idea-draft.md` 新增 `Common-H Agreement/Availability` 证明切口、证书语义和失败判据。下一步只做这三个 reduction 的固定委员会审计，不扩展完整动态 handoff。
- **Common-H 细化：** `lsr-construction-audit.md` 已将第一项拆为 `Agreement` 与 `Availability` 两个引理；“helper 已广播 commitment”不再被视为可用性证明，必须要求 AVSS-complete input 对所有正确 receiver 可获得。
- **Common-H wrapper：** 候选集合改为 `P^- = P \ {target}` 上的 `n'=3f+1` validated ACS，先输出 `|V|>=n'-f`，再确定性截取 `H=Canonical_{2f+1}(V)`；target 不提案但仍是 AVSS receiver。`H` 可包含 Byzantine dealer，前提是每个入选 AVSS instance 对所有正确 receiver 最终可恢复。

- **定理稿同步：** `repair-closure-theorem-draft.md` 已将 `ValidDesc_h`、`CommonH` 和 `AVSSComplete_h` 写成 typed edges；后续 reduction 从该接口进入 `Cl_rec`，不再把 ACS quorum 当作隐含可用性证明。
- **ACS 细节修正：** 标准 ACS 只保证输出 `|V|>=n'-f`；FGSR 由确定性 descriptor 顺序取 `H=Canonical_{2f+1}(V)`，避免把“至少”误写成“恰好”。
- **密码学接口收紧：** 首个 proof-friendly 实例采用 Pedersen 系数承诺与零知识 opening-equality proof；`f_h(0)=z_h` 不公开旧 share。KZG 版本暂不进入首个主定理，除非补齐 zero-knowledge opening-equality 证明。
- **Transcript reduction：** 思路稿与定理稿新增单次 repair 的条件 transcript-hiding 引理；`A_ell` 已确认节点擦除，`U_ell` 残留状态进入 `Cl_rec`，不再错误要求全员删除 `F'`。
- **组合边界：** 已补充串行多次 repair 的条件引理；必须同时假设累计 `|B_ell|<=f`、独立每轮随机性、实例序列化和 `|U_ell|+|B_ell|<q_rec`。仅限制瞬时 Byzantine 数量不够。
- **模型修正：** “退休后所有节点删除 `F'`”过强且不符合异步 quorum；改为 `A_ell` 已确认节点擦除、`U_ell=P\A_ell` 残留状态入 `Cl_rec`，并要求紧参数下 `|U_ell|+|B_ell|<q_rec`。
- **Retirement-Closure：** 定理稿与思路稿新增条件版退休闭包定理；`Cross-Generation Affine Coupling` 关闭线性 share 层的多代组合，剩余主缺口收敛为可见状态覆盖、迟到 transcript 和 aggregate-opening 非线性恢复边。
- **理论切口：** 新增 `One-Hidden-Helper Residual Cut` 与 `Cross-Generation Affine Coupling`：`|U_ell|+|B_ell|<=2f`、`|H|=2f+1` 时每次 transition 留下未暴露 helper；`L_E` 同时扰动整条 sharing 链，关闭线性 share-to-share 层的跨代组合缺口。
- **当前证明顺序：** `AvailCert_h`/Common-H 先证可用性；再用 affine coupling 证线性多代 residual cut；最后审计 frontier、擦除和 aggregate-opening 的额外边。任何一步失败都记录为精确边界，不用前向安全加密掩盖。
- **新增剩余接口：** `Cross-Coordinate Nonlinear Isolation`；BF-RPTA 的独立坐标 sharing 与 zero-knowledge 同明文证明必须不能把不同坐标 partial shares 组合成额外 aggregate-opening capability。packed/共享高阶系数暂禁用。
- **Edge audit：** 定理稿与思路稿已按 `share->polynomial`、`polynomial->subshare`、`subshare->F'`、`F'->state` 和 `state->decryption` 分类退休前后边；未归入历史、残留或被 frontier 拒绝的边，均视为未建模能力。
- **Availability certificate：** `AvailCert_h` 定义为 `P^-` 中至少 `2f+1` 个 AVSS `READY` 签名；READY 需在本地 deliver 后产生，并依赖 AVSS 的 deliver-propagation 语义，解决“helper 本地完成但 target 永远收不到”的缺口。

### 2026-09-11（跨坐标耦合与组合边界）

- **Cross-Coordinate Affine Coupling：** 对每个 coordinate 使用独立 `L_ell` 与独立高阶随机性，但所有 coordinate/generation 使用同一个未知 `Delta`；保持各坐标可见点、helper equality relation、resharing recursion 以及“编码同一 mask key”的关系不变。
- **理论边界：** 该引理只覆盖线性 share-to-share 层，不等价于 `Static-AO` aggregate-only 安全。跨坐标 consistency proof 必须是 zero knowledge 且不提供 share opening；否则新增边必须进入 `Gamma_dec^cap` 审计。
- **主线叙事更新：** 研究核心进一步表述为“跨 generation、跨 coordinate 的全局模拟不变量”，而不是前向安全加密、重复计数或简单 replay 防护；单坐标 hidden-helper residual cut 是该不变量的局部基础。
- **当前构造约束：** 首版禁止共享高阶系数、公开跨坐标线性 opening 和 packed coordinates；先闭合独立坐标 + `Static-AO` challenge transcript 的 reduction，再考虑优化。
- **下一步：** 审计 `Gamma_dec^cap` 是否只由每坐标 current-share closure 生成，并补齐联合向量 `Static-AO` aggregate-opening simulator；由于同一 mask key 的跨坐标证明会阻止逐坐标 hybrid，若出现跨坐标非线性恢复边，记录精确失败边界，不把引理升级成完整主定理。
- **联合归约（历史候选记录）：** 原候选界未标注 auxiliary-input 条件；现已由下一条正式修正覆盖，不再作为当前定理表述。

### 2026-09-11（FGSR 协议层形式化与 APSS 接口审计）

- **协议层已形式化：** `repair-closure-theorem-draft.md:2001` 新增正式 FGSR wrapper，固定 `Authorize -> ParallelReshare -> Aggregate -> Install/Erase` 四个逻辑操作；状态和消息均绑定 `(rid,sid,ell,cfg,generation,frontier)`。
- **State-complete resharing 引理：** `Lemma 7` 证明 `|H|=2f+1` 且 `f_h(0)=F^r(h)` 时，`F^{r+1}(0)=F^r(0)`，输出仍是 degree-`2f` 的普通 current sharing，下一轮 repair 不依赖旧 helper polynomial 或 recovery polynomial。
- **条件活性引理：** `Lemma 8` 在 Common-H agreement/availability 和 frontier 未关闭的条件下，证明 target-excluded repair 能让所有正确 receiver 得到同一 `F'`；这只关闭代数正确性与可用性，不等于 privacy-finality 已证明。
- **APSS 接口审计：** `repair-closure-theorem-draft.md:2118` 与 `privacy-finality-paper-idea-draft.md:2278` 明确 APSS 只能作为 ACSS transport/availability 候选。必须关闭 `GenZeroPoly` 的 public evaluation revelation，不能继承 APSS 的 static-corruption 或 reconstruction-exclusion 安全结论。
- **密码学 go/no-go：** 首个候选固定为“APSS-style ACSS transport + frontier-bound helper equality proof + metadata-only receipt + PECC + atomic endpoint erasure”。若公开 transcript 含 scalar evaluation，或擦除后 channel buffer/endpoint 可被读取，则 `AVSS-opaque` 条件失败；若无法补强自适应组合，只保留条件 `FGSR-Eph(C)` 定理。
- **当前证明状态：** 已完成 Common-H 的条件协议接口和 state completeness；未完成 retired-coordinate `Cl_rec` closure、迟到 transcript exclusion、helper equality proof simulation、PECC 具体化，以及与 `Joint-AO` 的最终组合。
- **当前唯一主线：** 先完成固定委员会 FGSR 的 `Retirement-Closure` 实例化和三个密码学接口，不扩展动态委员会、packed repair、exact puncture，也不再引入前向安全加密作为主线替代物。
- **FGSR 专用闭包定理：** `repair-closure-theorem-draft.md:2155` 新增 `Theorem 9`，逐类排除旧 descriptor、迟到 subshare、pending `F'`、残留 current state、跨代和跨坐标对象形成新旧能力边；结论为 `Cl_FGSR(X) intersection Cap_old(c) = X intersection Cap_old(c)`。
- **证明边界再次明确：** 该定理已经闭合协议状态机和 capability edge 分类，但仍以 opaque ACSS、helper equality-proof simulation、PECC、generation binding、state commitment 和 `Joint-AO` 为条件；不能把它写成 APSS 无条件安全性。
- **接口游戏已形式化：** `repair-closure-theorem-draft.md:2238` 新增 `Adv_ACSS-opaque`、`Adv_Eq-Simulation` 和 `Adv_PECC` 三个安全游戏，分别覆盖未暴露点值的 transcript simulation、helper 两承诺相等性证明模拟、以及擦除后在途消息/buffer/endpoint state 暴露。
- **组合边界：** 每代 transcript-hiding 误差为三项接口优势加上 state commitment、generation binding、affine coupling 和 uncovered-edge 项；普通 APSS static secrecy 或 forward-secure channel 不能替代其中任一项。
- **候选实例化裁决：** 首个候选改称 `C_APSS^opaque`，只复用 APSS 的 ACSS 交付/传播骨架，关闭 `GenZeroPoly` public evaluation revelation；若模拟需要，则将 Feldman commitment layer 替换为 hiding commitment，并重新证明本地点值验证。
- **ACSS reduction ledger：** `repair-closure-theorem-draft.md:2359` 给出 `Adv_ACSS-opaque <= Adv_ACSS-Transcript-Sim + Adv_Commitment-Hiding + Adv_READY/Label-Soundness + Adv_Public-Evaluation-Leakage + negl(lambda)`。APSS 的 DLEq proof 不直接满足 helper 两承诺相等性关系。
- **Pedersen 验证缺口已补齐：** `repair-closure-theorem-draft.md:2131` 新增 `Lemma 10/11` 与 `Proposition 12`；隐藏承诺版本必须私下交付 evaluation opening 或 receiver-local opening proof，且 `2f+1` 个本地验证 `READY` 才能在 propagation 条件下推出 `AVSSComplete_h`。
- **当前新的具体门槛：** 需要为 `C_APSS^opaque` 找到或证明 ACSS public-metadata transcript simulator；Pedersen evaluation opening、READY 传播和 PECC 的状态擦除都不能通过 APSS 的普通 Feldman/静态安全结论自动获得。
- **候选升级：** 本地 `hbACSS/Haven++` 转写显示，`hbACSS0 + hbPolyCommit` 有明确的 `OK/READY` amplification、evaluation proof 和 transcript simulator，优于直接引用 APSS；首个具体候选更新为 `C_hb0^opaque`。
- **关键否决条件：** hbACSS 的 implication/share-recovery 路径会披露 receiver key；该路径必须绑定 frontier，并在退休后完全关闭，否则旧 AVID ciphertext 产生新的 recovery edge。Haven++ packed/bivariate 版本暂不进入首个定理。
- **恢复门控已形式化：** `repair-closure-theorem-draft.md:2568` 新增 `Lemma 13/14` 与 `Theorem 10`，规定 `IMPLICATE/KEYREVEAL/RECOVER` 只对 `Live/Recoverable` 坐标有效，`Retired` 坐标对所有迟到恢复消息进入吸收态。
- **generation-local simulator 已形式化：** `repair-closure-theorem-draft.md:2670` 新增 `Proposition 15`，按 `B_{ell,r}` 暴露集合逐代模拟 hbACSS transcript，并显式计入 static-simulator、PKE、PECC、recovery-gate、generation-binding 和 affine-coupling 误差。
- **原论文边界：** hbACSS 原证明只覆盖固定静态 corrupted-key set；自适应身份选择、并发 frontier labels、AVID transcript simulation 和 key-erasure recovery separation 仍是本文必须新证的接口。
- **待核对条件：** 需要确认 TACITA-style `Static-AO` 的具体加密方程、随机预言机调用和 `R_eq` 电路可实现，并完成 `Static-AO^aux` 归约。
- **当前状态：** 联合归约已形成条件正式定理；仍需核对 TACITA 的 auxiliary-input 嵌入与双模式一致性证明假设是否相容。
- **TACITA 审计结论：** TACITA extended CPA 覆盖坐标级等和消息、聚合 ciphertext 和聚合 partial decryption，可作为 `Static-AO_ell` 基线；它不覆盖跨坐标同 key 关系、双模式证明模拟或长期移动腐化，因此 `Joint-AO` 仍是额外条件组合定理。
- **go/no-go：** 已采用双模式 simulation-sound `R_eq` 路线继续证明；若 TACITA 无法支持 auxiliary-input 嵌入，则将 `Joint-AO` 明确列为独立假设。
- **本轮正式修正：** 原 commitment 版本遗漏了从 `K_0` 到 `K_1` 的 commitment endpoint；首版改用 commitment-free batched `R_eq`，statement 为 `(ctx_sid,u,{ek_ell,tag_sid,ell,w_u,ct_u,ell})`，witness 为 `(k_u,{rho_u,ell})`。
- **固定权重归约：** 令 `m_u=w_u*k_u`，TACITA 的等长、等和 challenge 直接覆盖 `sum_u w_u*k_u,0=sum_u w_u*k_u,1`；零权重和不可逆权重允许，但权重、参与集合和域编码必须在挑战前固定。
- **正式条件界：** `Adv_Joint-AO <= 2*Adv_DualMode-ZK + sum_ell Adv_Static-AO_ell^aux + negl(lambda)`；`aux` 要求归约者能独立生成其它坐标、公开参数和 proof transcript。普通 IND-CPA 不自动提供该接口。
- **证明状态更新：** `Joint-AO` 已从“候选证明”升级为条件正式定理；仍需具体化 TACITA 加密方程、随机预言机调用、`R_eq` 电路及 `Static-AO^aux`。若接口无法满足，保留独立联合数据面假设。
- **方程审计完成：** TACITA 坐标密文可写为 `ct=(tag,s^T*A_ell,s^T*b_ell+Encode_T(w_u*k_u))`，其中 `s=RO(ctx_sid||ell||sd)`；`Aggr` 逐项相加且要求 tag 一致，`PartDec` 绑定聚合密文的 ciphertext-specific component。
- **实例化边界：** `R_eq` 必须是 ROM-aware relation，能够验证 `s=RO(ctx_sid||ell||sd)`；若 NIZK 电路不支持 RO query，则须将 oracle values 纳入 statement，或把 `Joint-AO` 保留为独立数据面假设。
- **Auxiliary-input lifting：** 对目标坐标 `ell`，归约者可自行生成其它独立坐标的完整 transcript，将 `m_u=w_u*k_u` 嵌入 TACITA 等和 challenge，并用模拟 CRS 的 `SimProve` 处理含 challenge ciphertext 的 `R_eq`；因此 `Static-AO^aux` 是可检查的归约义务。
- **Lifting 失败边界：** 共享 hidden setup、共享 RO 状态、跨坐标公开线性 opening，或 partial decryption 依赖其它坐标秘密时，不能从 TACITA 坐标级安全推出 `Joint-AO`，必须保留独立联合数据面假设。
- **SE-NIZK compatibility gate：** 还必须证明真实/模拟 CRS 不可区分、`SimProve` 可对 hybrid 中暂时为假的 `R_eq` statement 生成可验证 proof、支持并发多定理 transcript，以及 TACITA/NIZK 随机预言机的组合。
- **文献边界：** Choudhuri 等提供 `Setup/Prove/Verify/SimProve` 与 weak simulation-extractability 接口，但不能仅凭接口名称推出 arbitrary-statement simulation；若 gate 无法关闭，`Joint-AO` 保留为独立假设。
- **证明缺口已分层处理：** 主线 `Privacy-Finality(BF-RPTA)` 直接假设完整跨坐标 `Joint-AO`，不再依赖逐坐标 hybrid 对假 `R_eq` statement 的模拟；TACITA lifting 作为满足 `DM-SE-NIZK^{RO,eq}` 后的条件实例化定理。
- **主定理边界：** `Privacy-Finality <= Joint-AO + RCL-Sim/AO + Robust-Hitting + correctness`。这保持长期异步移动腐化、退休闭包和聚合开放安全在同一理论主线上，未把未核实的 NIZK 组合性质藏入 `RCL`。
- **实例化边界：** 只有同时证明 arbitrary-statement `SimProve`、并发 simulation-extractability 和 TACITA/NIZK programmable-RO 组合，才能使用 `Adv_Joint-AO <= 2*Adv_DM-SE-NIZK^{RO,eq} + sum_ell Adv_Static-AO_ell^aux + negl(lambda)`；Choudhuri 的 weak SE-NIZK 当前不足以直接完成该实例化。
- **联合游戏已正式化：** `Joint-AO` 一次性挑战完整跨坐标 ciphertext、consistency transcript、aggregate ciphertext、partial decryption 和唯一 aggregate output；两组 key vectors 只需满足相同加权和，避免 coordinate-local hybrid 的假 statement 问题。
- **主组合定理已正式化：** `Adv_Privacy-Finality <= Adv_RCL-Sim/AO + Adv_Joint-AO + Adv_Context/Correctness + negl(lambda)`。证明顺序为恢复/迟到 transcript 模拟、`CapSafe` 闭包隔离、联合数据面切换、上下文绑定与聚合正确性。
- **新增跨层非干扰门：** `RCL-Sim` 必须升级为 `RCL-Sim/AO`：`View_b=(DataView_b,StateView,PublicContext)`，只有 `DataView_b` 可依赖 challenge vectors 且由 `Joint-AO` 覆盖；repair/handoff/current-state exposure 不得泄露未建模的 individual-key 函数。`CapSafe` 与该非干扰条件分别承担“无完整 opening”和“无残余区分泄漏”。
- **修正主界：** `Adv_Privacy-Finality <= Adv_RCL-Sim/AO + Adv_Joint-AO + Adv_Context/Correctness + negl(lambda)`；首版 BF-RPTA 通过让 RCL 只处理委员会 decryption shares、让 client mask keys 只进入数据面来满足该分层。
- **上下文循环已拆开：** `sid/weights/frontier/generation` 属于 pre-challenge context；`H_ct/H_out`、challenge-dependent partial decryption 和 aggregate certificate 属于 `DataView_b`，不能同时作为 challenge-independent `StateView` 输入。BF-RPTA 的 `Puncture/Recover/CheckInstall` 只读取前者。
- **BF-RPTA 状态因子化引理：** 在独立 threshold shares、current-share-only repair、原子擦除以及 19.5、19.21、19.22、19.24 的 transcript-hiding/closure 条件成立时，`Adv_RCL-Sim/AO <= Adv_Transcript-Hiding + Adv_State-Commitment + negl(lambda)`；未分类的跨层输出视为新 capability edge。
- **长期自适应腐化推进：** 将全生命周期预算候选放宽为因果 generation interval 预算：`B_{ell,r}` 覆盖从安装 `F^r` 到下一次安装或 retirement barrier 的全部暴露；要求 `|B_{ell,r}|<=f`、`|U_ell|<=f`、`|U_ell union B_{ell,ret}|<q_rec`。
- **实例局部组合引理：** 在 fresh resharing/ephemeral randomness、代际绑定、完成后擦除和 stale transcript 不可回滚成立时，即使不同 interval 的 `B_{ell,r}` 根据历史视图自适应变化，也有 `Adv_Transcript-Hiding^R <= sum_r Adv_Sim_r + Adv_Generation-Binding + R*negl(lambda)`；若无屏障前可读完全部当前份额，则退回累计预算模型。
- **代际屏障必要性：** 若同一代 `q_dec`-out-of-`n` 份额在两个状态变化屏障之间持续有效，异步调度器可在保持瞬时 `f` 个腐化的情况下顺序读取 `q_dec` 个节点并重构旧 capability；因此屏障必须同时完成 fresh install、旧边失效和擦除。
- **证明缺口修正：** `repair-closure-theorem-draft.md` 新增 19.22 的 generation-local 到 Retirement-Closure 正式推论；历史各代使用带 generation tag 的 `X_hist^r(B_{ell,r})`，最终 retirement interval 单独使用 `U_ell union B_{ell,ret}` 的 terminal affine coupling。19.6--19.7 的累计 `B_ell` 版本明确降级为保守基线。
- **当前剩余义务：** 19.22 仍是条件推论；必须继续给出 one-step transcript simulator 的完整 typed edge 覆盖，以及跨 coordinate/aggregate-opening 不产生额外 capability 的独立证明，不能用“fresh randomness”一句话替代。
- **One-step simulator 已具体化：** 定理稿新增 19.24，按 authorization/Common-H、commitment/proof、ephemeral ciphertext、exposed plaintext、U_ell residual state、install/erase、迟到消息和 challenge-dependent data objects 逐类归属；未归类对象定义为 Adv_Uncovered-Edge。下一步只需把该接口绑定到具体 AVSS/Pedersen/PKE 实例，不再扩大模型。
- **具体实例化已收敛：** 定理稿新增 19.25，选择 Pedersen 系数承诺、常数项 equality proof、opaque AVSS 点值交付、receiver-ephemeral PKE 和原子擦除，并给出对象级归属。当前不再声称普通 AVSS correctness 足以令 Adv_Uncovered-Edge=0；必须验证 opaque delivery 与跨坐标 nonlinear isolation。
- **文献接口裁决：** APSS/ACSS 可复用私有点值交付和异步 availability，但其 static-Byzantine/global-refresh 语义不足以直接实现 selective repair；DyCAPS 的 forward-secure channel/erase 可借鉴但不复制其 epoch/bivariate handoff；adaptive PVSS 明确不假设 secure erasure，不能覆盖未来暴露后历史 ciphertext 的 transcript finality。
- **当前实例接口：** 将 AVSS-opaque 定义为公开 transcript 只含 commitment、proof、availability certificate 和元数据，点值经 receiver-ephemeral channel 交付并在完成后擦除。若公开 commitment 能作为 scalar recovery share 使用，则计入 Adv_Uncovered-Edge，不能继续声称具体实例闭合。
- **跨坐标隔离已形式化：** 新增定理稿 19.26 与思路稿 28.22--28.23。对 `Share(ell,r,i)`、`RepairShare(ell,r,h,i)`、`AggregateKey`、`ProofMeta` 进行类型标注；`Interpolate_{ell,r}`/`PartDec_{ell,r}` 只接受同坐标同代对象，`Repair_{ell,r -> r+1}` 是唯一显式代际转换，跨坐标 proof 只能输出零知识元数据，不能参与 scalar recovery。于是 `Cap(T) <= union_ell Cap_ell(T) union Cap_AO(T)`，在 `CapSafe` 与 `Joint-AO` 成立时关闭跨坐标 `Gamma_dec^cap` 新边，并将 `Adv_Uncovered-Edge` 归零。该结论是独立的构造义务，不由普通 NIZK soundness 或独立随机性自动推出；packed/shared-coefficient/跨坐标 partial decryption 仍排除在首版之外。
- **类型隔离边界进一步收紧：** 19.26/28.22 增加 proof-noninterference 条件：`ProofMeta` 只能影响公开 acceptance，或影响已在固定 `Joint-AO` context 中声明的数据面选择；不能根据隐藏 witness 选择单项 ciphertext、partial decryption 或 recovery branch。否则该控制流必须进入 `DataView` 并重新计算 `Gamma_dec^cap`，不能用“proof 不含标量”略过。
- **opaque delivery 文献审计已完成：** 新增定理稿 19.27 与思路稿 28.24，明确 `AVSS-opaque` 由 (OD1)--(OD5) 五项组成：公开 transcript 无标量点值/可重构系数、receiver-specific 私密交付、barrier 擦除、恢复响应无新公开 scalar opening edge、以及异步 availability/一致交付。APSS 只能作为 (OD2)/(OD5) 候选，静态 secrecy 且 reconstruction 后不再覆盖；VSSR 的恢复响应本身产生 recovery edge；DyCAPS 的移动腐化与擦除语义依赖其 handoff，不能作为本文 per-coordinate retirement 黑盒。go/no-go 已收紧：任一候选未证明五项接口，就保留抽象 `RCL-Sim/AO` 并计入 `Adv_Uncovered-Edge`，不把普通 AVSS agreement 当作 opaque delivery。
- **APSS 传输层转换已简化并收紧：** 19.28/28.25 将私密通道 + metadata-only `READY` receipt 设为首版主路线，不再引入公开密文和 `EncEq`。复用 APSS 底层 ACSS 需要满足 (PC1)--(PC4)，再证明私密通道在 barrier 擦除后抵抗未来 endpoint 暴露、receipt/availability certificate 支撑 Common-H，即可推出 (OD1)--(OD5)。公开 relay 的加密点值若未来采用，必须另行承担 simulation-sound/dual-mode proof；该变体不进入首个定理。
- **信道安全已独立形式化：** 新增定理稿 19.29 与思路稿 28.26，定义 `PECC`（post-erasure channel confidentiality）。普通私密通道只保护传输期，前向安全只保护未来长期密钥暴露下的历史密文；二者任一缺少端点/缓冲区原子擦除都不足以支持 `OD3`。首版直接假设 `PECC`，receiver-ephemeral encryption 仅作为在途密文可被暴露时的实现路线；由此明确前向安全不是 privacy finality 本身。
- **APSS/ACSS 具体裁决已完成：** 新增定理稿 19.30 与思路稿 28.27。底层 ACSS 可候选满足 `PC1/PC3/PC4`；`PC2` 仅在关闭 `GenZeroPoly` 公开 evaluation revelation、且禁止把群值承诺当 scalar recovery share 时成立。原样 APSS 的 static corruption 与 reconstruction 排除条件不能进入 FGSR 长期定理。首个候选固定为“APSS-style ACSS transport + `Eph(C)`”，并要求腐化 oracle 覆盖 channel buffer/endpoint state。
- **完整条件实例化已统一：** 新增 19.31/28.28 的 BF-RPTA 条件实例化定理。其组合界为 `Adv_Joint-AO + Adv_Affine-Coupling + Adv_State-Commitment + Adv_Generation-Binding + Adv_Context/Correctness + sum_r(Adv_ACSS-opaque^r + Adv_Eq-Simulation^r + Adv_PECC^r) + R*negl(lambda)`。首版不需要公开密文或 `EncEq`；首要证明义务收敛为 opaque ACSS、helper equality proof simulation、`PECC` 与原子擦除。公开 relay 加密点值保留为未来扩展，不能进入首个定理。
- **实验交付物已分层：** 新增 `experiments/EXPERIMENT_PLAN.md`，明确后续设备的完整 FL 执行方案与开源基线矩阵。Buffalo 是必选主端到端比较，PPFA-BAA 在 artifact 可访问且复现成功后加入；Flower SecAgg+、FLSim 是 FL/异步控制；APSS、DyCAPS、NFSA、Google Federated Compute 只承担组件或工业实现参照，不混入端到端准确率排名。方案固定了 `S0`--`S7` 场景、`n=3f+2` 的 FGSR 参数点、指标和复现顺序。
- **首轮机制实验已校正：** `experiments/privacy_finality_sim.py` 使用每个 trial 共享的延迟/withholding 场景配对所有基线；固定种子 200 次运行得到 violation rate `0/1/1/0`，前三个即时机制平均 finality time 约 `20.6`，epoch baseline 约 `40`。该结果只验证理论攻击与安全性—延迟分离，不替代 19.31 的 ACSS、helper proof 和 `PECC` 证明。
- **开源基线已锁定：** 端到端必选主比较为 Buffalo（`https://github.com/rtaiello/buffalo`）；PPFA-BAA 仅在原文提供的 4open.science artifact 可访问且成功复现后加入。Flower SecAgg+（`https://github.com/flwrlabs/flower/tree/main/examples/flower-secure-aggregation`）作为标准 FL secure-aggregation 控制，FLSim（`https://github.com/facebookresearch/FLSim`，已归档）作为异步调度控制。APSS（`https://github.com/ISTA-SPiDerS/apss`）、DyCAPS（`https://github.com/DyCAPSTeam/DyCAPS`）和 NFSA-TLSS（`https://github.com/pahjastia/NFSA-with-TLSS`）仅进入组件/状态成本实验。完整参数、场景、指标、复现顺序和 artifact 目录见 `experiments/EXPERIMENT_PLAN.md`。

### 0.4.8 实验之外的下一阶段：从候选协议到可投稿定理

实验已经转移到其他设备。本机后续工作的目标不是继续堆叠 FL 场景，而是把当前条件候选压缩成一组审稿人可以逐项检查的定义、攻击和定理。执行顺序固定如下。

#### P0：冻结论文承诺和模型边界

先冻结首篇论文只声称以下结果：固定委员会、完全异步认证网络、`n=3f+2`、`q_dec=q_rec=2f+1`、按 coordinate 的 causal-generation-bounded mobile adversary，以及 `aggregate-only` 输出。动态加入/退出、packed repair、exact puncture 和恶意梯度不进入首个主定理。

必须同时写出不能声称的性质：不证明软件证书等价于物理擦除；不把普通 forward secrecy 当作 privacy finality；不声称仅有瞬时腐化上界就能抵抗无限快的连续移动腐化；不声称原始 hbACSS 论文已经给出本文所需的自适应长期安全。

**Go/no-go：** 如果无法在这一边界下给出单一的安全游戏和主定理，暂停协议扩展，先修正模型。

#### P1：完成 `C_hb0^opaque` 的固定委员会实例化审计

这是当前最重要、也最可能否决构造的工作。需要逐项完成：

1. 把 hbACSS 的 static simulator 改写成 generation-local simulator，明确自适应 `B_{ell,r}`、并发 `rid`、`sid`、frontier 标签以及预退休 `KEYREVEAL` 进入模拟输入的方式。
2. 证明公开 AVID/ACSS transcript 只包含 metadata、commitment、proof 和 availability certificate；任何 scalar evaluation、receiver key 或可重构点值都不能由公开 transcript 或恢复响应导出。
3. 证明 `IMPLICATE -> KEYREVEAL -> RECOVER` 只对 `Live/Recoverable` coordinate 有效；`Retired` coordinate 的迟到消息、重放消息和恢复请求形成吸收态，而不是仅在安装时拒绝。
4. 给出 helper equality proof、Pedersen evaluation opening、receiver-ephemeral channel 和 post-erasure channel confidentiality 的统一 hybrid；剩余项必须显式写成安全优势，不能用“fresh randomness”概括。

**Go/no-go：** 若仍需把旧 scalar evaluation、receiver secret key 或可重放 recovery polynomial 放进退休后可见状态，则 `C_hb0^opaque` 不能作为长期安全实例，只保留抽象 `RCL-Sim/AO` 定理和攻击边界。

#### P2：完成跨坐标数据面归约，或明确保留抽象假设

在 P1 之后审计 `Joint-AO`：证明同一 mask key 被多个 coordinate 编码时，跨坐标 proof metadata、partial decryption 和 aggregate certificate 不会生成新的 individual-key capability。目标是得到

```text
Adv_Privacy-Finality
  <= Adv_RCL-Sim/AO + Adv_Joint-AO + Adv_Context/Correctness + negl(lambda)
```

TACITA 只作为坐标级 `Static-AO` 基线，不能直接代替 `Joint-AO`。如果其 auxiliary-input、双模式 NIZK 或 programmable-RO 条件无法逐项验证，论文应诚实地把 `Joint-AO` 作为独立数据面假设，而不是伪装成已完成的具体构造。

#### P3：把 no-resurrection 写成必要性结果

在固定委员会协议之后，给出一个最小异步攻击：旧 recovery transcript 在退休后迟到；若状态转移没有单调 frontier/tombstone 支配它，则它重新安装旧 capability。再证明带 `CheckInstall(T_req)`、不可回滚 tombstone 和 state-complete erasure 时，退休 coordinate 的 `Cl_rec` 不再增长。

这一部分是叙事的理论核心：`privacy finality` 不是一个签名数量，而是“访问结构上的 robust hitting + 异步状态机中的吸收态退休”。普通 deny-list 或前向安全密钥更新只有在能够证明同一闭包性质时才可作为实现细节。

#### P4：把动态节点降为推论

只有 P1--P3 闭合后，才研究 `Project(T) -> Handoff(config_old, config_new, live coordinates only)`。动态委员会不另起一套协议，而是证明 handoff 只增加跨配置 recovery edges，并且不把 retired coordinate 放回 `Cl_{rec+ho}`。若该推论需要完整 DPSS handoff、全局 epoch 或额外可信时钟，就从首篇论文删除，而不是扩大模型掩盖缺口。

#### P5：形成论文而非工程设计文档

实验之外的最终交付物只有五类：

1. 一个正式 ideal functionality：公开 `CC_sid`，区分 aggregate correctness 和 `PF_sid`，并明确允许的暴露视图。
2. 一个固定委员会 FGSR 协议描述：消息、状态、frontier、擦除事件和恢复接口均带类型与 generation。
3. 一组主结果：`Robust-Hitting` 刻画、`Recovery-Closure` 定理、no-resurrection 必要性定理，以及条件的 `C_hb0^opaque` 实例化定理。
4. 一个匹配攻击/下界部分：无状态屏障、低恢复门限、公开 scalar transcript 或可回滚 handoff 分别如何破坏隐私终结。
5. 一张相关工作分离表：前向安全、proactive secret sharing、VSSR/APSS、DyCAPS、TACITA、WBTE、Buffalo 分别覆盖什么，不能覆盖什么。

当前不做：继续搜索更多 FL 论文、增加更多基线、实现动态委员会、优化 packed 通信、把四阶段 handoff 重新包装为 FGSR，或把条件假设写成无条件安全。

### 0.4.9 当前执行任务

P1 的 typed-edge ledger、AK2/PECC 状态机、adaptive AVID/commitment barrier 和
Janus-style transport 边界已经写入定理稿与思路稿。当前唯一首要任务改为：

1. 把公开 `KEYREVEAL` 的 send/receive 时间语义写入 `F_AWF` 与 FGSR 协议定义；
2. 审计公开 complaint/recovery transcript 是否会进入 `Joint-AO` 并产生单项输出；
3. 根据审计结果决定 `C_hb0^opaque` 是条件实例，还是需要引入 Janus-style adaptive
   transport 作为具体底层接口。

完成这三项前不写摘要、不扩展动态节点、不优化 packed repair，也不把实验结果写入
理论结论。

### 2026-09-12（P1：从静态 simulator 收紧到 adaptive-key 接口）

- **P1 已前进一层：** 定理稿新增 `19.41`，把 `C_hb0^opaque` 的关键对象划分为 `E1--E10` typed edges，并给出 `Lemma 16 (typed-edge simulation criterion)`。这不是把条件候选误写成完成实例，而是把每个未覆盖边显式计入优势界。
- **核心缺口修正：** hbACSS 原 simulator 的问题不只是 static `t` 换成自适应 `B_{ell,r}`。它依赖“先知道 corrupted-key set，再生成其他公开密钥和零密文”；长期移动腐化要求公开密钥/AVID ciphertext 先固定，敌手之后才选择暴露节点。
- **新增 adaptive-key 三分法：** 具体实例必须满足 `AK1` 可安全擦除的自适应密钥生成、`AK2` per-instance ephemeral key + `PECC`，或 `AK3` 覆盖 receiver-key schedule 与 AVID transcript 的现成自适应门限加密定理。原 hbACSS long-term-key optimization 不满足三者。
- **当前 go/no-go：** 只继续审计 `AK2`。若 barrier 后暴露 receiver state 仍可解封旧 AVID payload，或公开 transcript/channel buffer 能导出 scalar evaluation，则 `C_hb0^opaque` 从具体实例降级为条件候选；抽象 FGSR `Recovery-Closure` 主定理仍保留。
- **下一步：** 写出 `AK2` 的具体状态机和 corruption oracle，逐项核对 receiver ephemeral key、AVID ciphertext、buffer、`IMPLICATE/KEYREVEAL/RECOVER` 与 `PECC` 的时间关系；完成前不扩展动态委员会或 packed repair。

### 2026-09-12（P1：AK2 状态机与 PECC 边界）

- **AK2 已形式化：** 定理稿新增 `19.42`，为每个 repair context 使用一次性 receiver key；公开 AVID ciphertext 可以保留，但 endpoint secret、plaintext、opening、recovery material 和 buffer 必须在退休屏障原子擦除。
- **PECC 边界：** 退休前已经发生的 `KEYREVEAL` 及其解密点值进入历史暴露视图，不能被擦除“撤销”；退休后的 `KEYREVEAL/RECOVER` 必须被 frontier gate 拒绝。
- **新增 Lemma 17：** 在 PECC、recovery gate 和 evaluation-proof simulation 成立时，保留的旧 ciphertext 不会扩大退休 coordinate 的 recovery closure。该引理只关闭 receiver-key resurrection edge，不等价于完整 hbACSS 自适应安全。
- **当前剩余三项：** 自适应 AVID transcript simulation、并发 hbPolyCommit proof simulation、跨坐标 `Joint-AO`。这三项仍需独立证明或显式保留为条件假设。
- **当前 go/no-go：** 原 hbACSS long-term-key optimization 排除在首个实例之外；若具体 ephemeral-key/AVID 实现无法满足 PECC，则 `C_hb0^opaque` 降级为条件候选，不修改抽象 FGSR 主定理。

### 2026-09-12（P1：自适应 AVID 与 commitment barrier）

- **AVID 边界核对：** hbACSS 的 AVID 只提供 termination/agreement/availability/correctness，原 secrecy proof 允许敌手看到全部 AVID 消息；因此 AVID 本身不是 adaptive transcript simulator。
- **新增 Proposition 18：** 定理稿 `19.43` 将具体自适应实例化拆为 AC1--AC5：自适应 commitment consistency、barrier 前 payload state 模拟、barrier 后 PECC、AVID scalar-capability 隔离，以及 pre-frontier `KEYREVEAL` 的历史计账。
- **理论裁决：** AK2 只解决退休后旧密文复活，不解决公开 `C` 之后才选择腐化集合的事后一致开口问题。原 hbACSS static simulator + 普通 Pedersen hiding + IND-CPA 不足以推出长期移动安全。
- **主线调整：** 继续保留抽象 FGSR `Recovery-Closure` 主定理；`C_hb0^opaque` 目前只能作为条件实例。若要升级为具体构造，必须补充 equivocal/adaptive commitment 与 non-committing encryption，或找到覆盖 AC1--AC5 的现成定理。
- **下一步：** 审计是否能在不引入完整新密码学原语的情况下，把安全模型收紧为 generation-local selective exposure；若不能，保留当前长期自适应模型，并把具体构造明确标为条件结果。

### 2026-09-12（P1：Janus-style adaptive transport 对照）

- **已有组件确认：** 本地 Janus DKG 文档通过 hiding commitment、可模拟 ciphertext、可编程加密接口和 secure erasure 处理事后自适应腐化，能够作为 AC1/AC2 的强参考。
- **不能直接替换：** Janus 的目标是 DKG/key sharing；其 complaint/decryption 路径、普通完成语义和输出接口不满足 FGSR 的 per-coordinate frontier、退休 recovery closure 和 aggregate-only `Joint-AO`。
- **新增定理边界：** 定理稿 `19.44` 的 Proposition 19 只允许将 Janus-style transport 替换 typed ledger 的 E2--E6；Common-H、evaluation binding、跨坐标隔离和 `Joint-AO` 仍需独立证明。
- **主线叙事保持：** 自适应加密不是本文贡献，而是局部交付接口；本文贡献是 `Robust-Hitting + Recovery-Closure + absorbing retirement` 对异步安全聚合的统一刻画。
- **下一步：** 审计 Janus-style transport 的公开 complaint/decryption 是否能被 frontier gate 约束且不公开退休 scalar；若不能，保留抽象 `AVID-opaque` 条件实例，不把 `hbACSS0 + 普通 PKE` 写成具体构造。

### 2026-09-12（P1：公开 complaint 的发送时刻语义）

- **新增 Lemma 18：** 定理稿 `19.45` 明确 `KEYREVEAL` 的暴露时刻是进入公共 transcript 的 send event，而不是异步 receive event；退休前发送的材料必须进入 `X_hist`，退休后接收只能被拒绝。
- **安全效果：** 退休前发送、退休后到达的 complaint/recovery 消息不会形成新的旧 capability，只会重复历史视图中已经存在的能力；这正是 Janus-style complaint 路径接入 FGSR 的必要包装条件。
- **活性边界：** 若实现需要退休后继续处理 complaint 才能完成恢复，则不能满足首个 FGSR 定理；恢复活性必须在 `Live/Recoverable` 阶段结束。
- **下一步：** 把该 send/receive 时间语义写入 `F_AWF`/FGSR ideal functionality 和主协议伪代码，再审计 `Joint-AO` 是否会把公开 complaint transcript 转化为单项输出。

### 2026-09-12（P1：F_AWF Publish/Process 语义落地）

- **理想功能已更新：** `long-lived-adaptive-corruption-audit.md:1095` 的 `F_AWF` 新增 `Publish(Q,m)` 与 `Process(Q,m,T_local)`，明确公开事件和状态机接受是两个不同操作。
- **协议定义已同步：** FGSR wrapper 现在规定公开 `KEYREVEAL` 在 send event 进入历史暴露视图；退休后 receive 可以拒绝，但不能撤销此前公开的 key/point 能力。
- **论文叙事已同步：** 思路稿新增 `28.42`，使 `F_AWF`、Lemma 18 和 `Recovery-Closure` 使用同一 send-time exposure 语义。
- **当前首要任务：** 审计公开 complaint/recovery transcript 与 `Joint-AO` 的接口，确认它只能提供已授权 aggregate context，不能成为新的 individual-key opening oracle。

### 2026-09-12（P2：complaint transcript 与 Joint-AO 因子化）

- **新增 Proposition 20：** 定理稿 `19.46` 将公开 complaint/recovery transcript 分成 `Comp_state` 与 `Comp_data`；前者只可读取 frontier/current-share 状态，后者读取客户端 ciphertext、权重、`H_ct/H_out` 或 partial decryption。
- **接口结论：** `Comp_state` 可留在 `StateView`，但公开 `KEYREVEAL` 仍按 send event 进入 `X_hist`；任何 `Comp_data` 及其控制分支必须整体进入 `DataView_b` 并由一次 `Joint-AO` challenge 覆盖。
- **新增失败项：** 若 recovery proof/receipt 能根据单个客户端数据选择 complaint 或解密分支，则产生 `Adv_Complaint-Noninterference`，不能从普通 `RCL-Sim/AO` 推出 privacy finality。
- **当前下一步：** 将 FGSR recovery API 限制为只处理委员会 share capability，再检查 `R_eq`、aggregate certificate 和 partial decryption 是否满足同一因子化；若不满足，保留该优势项并降级具体实例。

### 2026-09-12（P2：TACITA 数据面对象级裁决）

- **新增 Lemma 19：** 定理稿 `19.47` 对 `R_eq`、aggregate certificate、ciphertext-specific partial decryption、helper recovery、invalid-aggregate complaint 和 ACSS receipt 逐项分类。
- **分类结果：** `R_eq`、aggregate certificate、partial decryption 及其控制分支全部进入 `DataView_b`；只有不读取客户端 ciphertext 的 helper recovery 和 metadata-only `READY` 才能留在 `StateView`。
- **安全含义：** partial decryption 即使不能单独恢复明文，也可能区分等和 key vectors，不能用普通状态层模拟覆盖；`R_eq` 的 witness hiding、并发模拟和 proof-noninterference 必须单独证明。
- **当前结论：** TACITA extended CPA 仍只是坐标级依据；auxiliary-input、并发 `R_eq` 和 complaint-branch simulation 尚未闭合，主定理继续显式保留 `Joint-AO`。
- **下一步：** 固定 `R_eq` 的完整 statement/witness/verification transcript，逐项检查是否需要对暂时为假的 statement 进行模拟；若需要而现有 NIZK 不支持，则记录为具体实例的最终 go/no-go 边界。

### 2026-09-12（实验之外的下一阶段：Static-AO 到 Joint-AO^mob）

当前实验基线已在其他设备运行，本地工作转入理论闭合，不再增加实验协议或数据集。

**已确认的边界：** TACITA 的 extended CPA 在 challenge 前固定腐化集合 `Cor`，
是静态、one-shot、坐标级 aggregate-opening 基线。它不包含长期自适应腐化、frontier
退休、repair oracle、未来全状态暴露，也不覆盖多坐标 `R_eq`/partial decryption
的联合模拟。因此不能把 `TACITA Static-AO + ordinary repair` 写成本文的长期安全
构造。

**下一条主证明链：**

```text
P0  冻结 Joint-AO^mob 游戏、完整 transcript 和 exposure 视图；
P1  写出 TACITA Static-AO separation 以及 recovery-state localization attack；
P2  在 Joint-AO^mob、opaque adaptive repair、PECC 下完成 FGSR composition theorem；
P3  审计 adaptive threshold decryption + simulation-sound R_eq 的具体 lifting；
P4  若仍有未闭合接口，保留“抽象主定理 + sharp separation + conditional instance”，
    不把条件假设包装成完成构造。
```

**Go/no-go：** 若 P3 不能同时覆盖 adaptive receiver exposure、等和 aggregate-only
opening、ciphertext-specific partial decryption、并发 `R_eq` 和 recovery closure，
则首篇论文仍有价值，但应以 FGSR 的访问结构刻画、异步 no-resurrection 必要性和
条件数据面组合为主，不声称完成 TACITA 的长期自适应提升。

**范围冻结：** P2 完成前不扩展动态委员会、不重写 DyCAPS handoff、不增加 packed
repair，也不把实验结果反向写成理论安全结论。动态 handoff 只有在证明不扩大退休
坐标 `Cl_rec` 后，才作为同一 Recovery-Closure 定理的推论。

### 2026-09-12（P0 完成：`Joint-AO^mob` 游戏冻结）

P0 已落地。定理稿 `19.50` 和思路稿 `28.47` 现在明确区分：

| 游戏 | 腐化/状态暴露 | 数据面视图 | 作用 |
|---|---|---|---|
| `Joint-AO` | challenge 前固定腐化集合，无 post-challenge state oracle | 静态联合 ciphertext/partial-decryption transcript | TACITA 坐标级基线及静态组合 |
| `Joint-AO^mob` | prefix 后可自适应腐化、恢复、退休和未来状态暴露 | 同一 challenge bit 下的全坐标、证明、证书、partial decryption 和分支 | FGSR 长期主定理接口 |

`Joint-AO^mob` 的关键约束是：挑战相关对象及其发布分支进入 `DataView_b`；只读
frontier/generation/current-share 的对象才进入 `StateView`；公开 `KEYREVEAL` 按
send event 计入 `X_hist`。这使 `R_eq`、aggregate certificate 和 partial decryption
不能再被普通 repair simulator 隐式覆盖。

**下一步已具体化为 P1：** 对 TACITA `Static-AO` 和 `Joint-AO^mob` 写出同一候选
包装器下的区分攻击，优先检查两条路径：未来 receiver-state 暴露解封旧 ciphertext，
以及残留 recovery object 重建退休坐标 capability。该攻击稿完成后，再进入 P2 的
FGSR composition proof；不先审计新的动态委员会或实验结果。

### 2026-09-12（P1 完成第一项：Recovery-State Localization Barrier）

P1 的状态面攻击已形式化为定理稿 `19.51` 的 Proposition 22 和 Corollary 22.1，
思路稿对应 `28.48`。结论是：若退休只删除 direct share、写入 monotone tombstone，
但保留可由全局恢复权 `G` 与 `sid`-local 状态 `L_sid` 组合出的 ordinary recovery
关系，则未来全状态暴露能够重新生成旧 individual-opening capability；仅阻止
`CheckInstall` 不足以阻止离线 partial opening。

该结论的适用范围已收紧：如果恢复机制只能再次输出同一个授权 aggregate，不能恢复
individual mask key，也不能生成第二个独立 aggregate descriptor，则它本身不构成
本文 indistinguishability 游戏中的区分攻击；安全定义必须明确是否禁止这种较弱的
重复输出。

这给出 VSSR/DPSS 的准确黑盒边界：它们并非原始安全性错误，而是其 recovery
correctness 不包含 retired-label 的 `Cl_rec` closure。FGSR 必须证明 coordinate-local
recovery state 被删除/穿孔，或让 recovery authority 与 `Use_sid` 同时接受 frontier
绑定，或切换恢复/解密世代。

**P1 剩余任务：** 将同一攻击写成 TACITA `Static-AO` 包装器的完整区分实验，并把
FGSR current-share-only repair 的状态删除条件逐项映射到 Proposition 22 的前提。

### 2026-09-12（P1 完成：Static-AO wrapper separation）

P1 的两条攻击路径已完成形式化：

1. 定理稿 `19.51` 的 Proposition 22：残留 `G + L_sid` recovery relation 可在
   退休后重建 individual-opening capability；`CheckInstall` 单独无法阻断离线使用。
2. 定理稿 `19.52` 的 Proposition 23：即使 TACITA `Static-AO` 对固定腐化集合安全，
   外接未穿孔 recovery wrapper 后，post-challenge state exposure 仍可近乎完美地区分
   两组等和 key vectors，因此不能推出 `Joint-AO^mob`。

P1 对 FGSR 的正向接口要求已收敛为 `L1--L3`：退休后 `StateView` 不保留坐标局部
恢复材料；全局恢复权单独不能重建该材料；所有 surviving `Use/PartDec` 路径都
执行 frontier-bound retired-label check。若目标模型只允许重复同一个 aggregate，
则必须另行定义第二 descriptor/数据相关分支的攻击，不能套用 individual-opening
版本。

**下一步 P2：** 在 `Joint-AO^mob`、`L1--L3`、opaque adaptive repair 和 `PECC` 下，
完成 FGSR 的主组合定理，并把每一个未满足条件保留为显式优势项。

### 2026-09-12（P2 开始：L1--L3 接入组合定理）

定理稿 `19.31` 已将 `L1--L3` 接入 BF-RPTA 条件实例化定理：

- `L1`：未来 `StateView` 不保留退休坐标的 local recovery material；
- `L2`：retained global recovery authority 单独不能重建该 material；
- `L3`：所有 `Use/PartDec` 路径都执行 frontier-bound retired-label check。

违反 `L1/L2` 的概率记为 `Adv_Recovery-Localization`，违反 `L3` 的概率记为
`Adv_Frontier-Use`，两项已加入 privacy-finality 优势界。这样 Proposition 22--23
不再只是反例，而成为主定理中的显式证明义务。

**P2 当前任务：** 对 FGSR 的 `current-share-only` 状态机逐项证明 `L1--L3`，并将
opaque ACSS、helper equality-proof simulation、PECC 和 `Joint-AO^mob` 的 hybrid
顺序写成完整 proof sketch；在此之前不宣称具体 TACITA lifting 已完成。

### 2026-09-12（P2 第一项完成：FGSR localization lemma）

定理稿 `19.53` 的 Lemma 24 已证明抽象 FGSR 状态机满足 `L1--L3`：退休后仅保留
frontier、tombstone、公开 metadata 和 live-coordinate state；`Recover` 与
`Use/PartDec` 对 retired label 拒绝；live recovery 必须绑定当前 generation 和
frontier。因此抽象层有：

```text
Adv_Recovery-Localization = 0,
Adv_Frontier-Use = 0.
```

这不是物理擦除结论。具体实例仍须用 `PECC`、opaque transcript simulation 和
generation-binding 证明 endpoint/buffer、公开 proof 和迟到标签都符合抽象状态形状。

**P2 下一项：** 将 Lemma 24 与 19.22 的跨代 `Retirement-Closure` proof 合并，写出
完整的 `H_0 -> H_1 -> H_2` 组合顺序，并核对 `Joint-AO^mob` 是否覆盖所有
challenge-dependent branch。

### 2026-09-12（P2 第二项完成：四阶段组合混合）

定理稿 `19.54` 的 Lemma 25 已固定 P2 的证明骨架：

```text
H0  real FGSR execution;
H1  generation-local StateView replacement;
H2  one Joint-AO^mob replacement for the complete DataView;
H3  context/correctness/affine-coupling cleanup.
```

优势界显式包含 `Adv_Joint-AO^mob`、`Adv_Recovery-Localization`、
`Adv_Frontier-Use`、`Adv_ACSS-opaque`、`Adv_Eq-Simulation`、`Adv_PECC`、
generation-binding、state-commitment 和 affine-coupling 项。H2 不进行逐坐标 hybrid，
因此不会要求证明中间 false `R_eq` statement；所有 challenge-dependent branch 必须
随同一次 `Joint-AO^mob` challenge 生成。

**P2 当前剩余任务：** 具体核对 `C_hb0^opaque`/Janus-style transport 是否能满足 H1
所需的 adaptive AVID transcript、endpoint exposure 和 helper-proof simulation；若
任一项失败，保留相应优势项并停止在条件实例化。

### 2026-09-12（实验转移后的工作裁决：接口审计优先）

实验基线已经在其他设备启动。本机不再扩展 FL 场景、基线数量或动态委员会，而
是完成理论结果与具体密码学接口的可审计闭环。

本轮完成了 `C_hb0^opaque`/Janus-style transport 的 AC1--AC5 证据审计：

| 接口 | 现有文献能提供的部分 | 对本文的裁决 |
|---|---|---|
| AC1 adaptive commitment consistency | Janus 有局部的 hiding/equivocation 与自适应加密机制；hbACSS 主要是静态 simulator | 条件，保留 `Adv_Adaptive-Commitment` 与 `Adv_hbACSS-StaticSim` |
| AC2 pre-frontier adaptive payload state | Janus 的 DKG 生命周期语义可作参考；两者都未给出并发 FGSR repair-context 的完整模拟 | 未闭合 |
| AC3 post-frontier PECC | Janus 的 secure erasure 是机制参考；hbACSS long-term-key 路径明确不满足 | 未闭合，保留 `Adv_PECC` |
| AC4 AVID scalar-capability isolation | hbACSS 的 AVID 不提供 secrecy，complaint/recovery 可公开标量能力；Janus complaint 也需包装 | 未闭合，保留 `Adv_Complaint-Noninterference` |
| AC5 send-time history/frontier gate | 现有工作未提供 retired-coordinate 的 send/receive 分离与吸收态 frontier | 由 FGSR wrapper 自己证明，保留 `Adv_Generation-Binding` |

**当前 go/no-go：** 抽象 FGSR 主定理继续成立；Janus-style transport 只能在
AC1--AC3 得到独立证明、并用 FGSR wrapper 补齐 AC4--AC5 时替换 typed ledger 的
局部交付边。现有 Janus 或 hbACSS 论文不能直接作为 `C_hb0^opaque` 的无条件
实例。hbACSS long-term-key optimization 排除在首版之外。

**下一步的三个交付物：**

1. 在定理稿中定义独立的 `Adaptive-Opaque-Repair` 接口，并把
   `Publish/Process`、send-time `KEYREVEAL`、endpoint/buffer 暴露和原子擦除写成
   安全游戏，而不是实现说明。
2. 证明 FGSR wrapper 的 `L1--L3`、no-resurrection 必要性攻击和 absorbing-retirement
   充分条件，形成抽象主定理之外的匹配下界/必要性部分。
3. 完成一张具体实例证据矩阵：每个 AC1--AC5 映射到定理、假设或剩余优势；矩阵
   未闭合前，论文只声称条件实例化，不写无条件具体构造或动态委员会扩展。

这意味着实验之外的近期目标已经从“设计更多协议功能”收敛为“证明访问结构
闭包，并诚实划分抽象定理与条件实例”。

### 2026-09-12（P2：`Adaptive-Opaque-Repair` 接口完成）

本轮没有新增协议组件，而是把已有的 `F_AWF` 控制面和 `RPTA` 数据面之间的
证明缺口单独命名为 `Adaptive-Opaque-Repair`（`AOR`）。

`AOR` 对每个
`Q=(sid,ell,r,rid,i,T_req,C_ctx)` 定义 `Publish/Process/Expose/Retire/Recover/
CheckInstall`，并明确：公开 `KEYREVEAL` 在 send event 进入 `X_hist`；退休前
腐化可以暴露 endpoint key、明文和 opening；退休后腐化只能读取擦除后的状态。
其模拟器只得到 `PublicView`、`X_hist` 和 frontier，不能得到未暴露的 scalar
`HiddenState`。

定理稿新增 Proposition 26，将第一阶段混合压缩为：

```text
Adv[H0,H1]
  <= sum_r Adv_AOR^mob(r)
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + R*negl(lambda).
```

这一步的意义是把 AC1--AC5 从“候选协议描述”提升为可归约接口：

- AOR-1：send-time exposure；
- AOR-2：opaque delivery；
- AOR-3：adaptive state consistency；
- AOR-4：post-frontier opacity；
- AOR-5：frontier absorption。

**当前状态：** P2 的抽象状态层归约已完成；具体实例仍需证明
`Adv_AOR^mob` 的下界分解。下一项转为 P3：把 no-resurrection 必要性攻击和
absorbing-retirement 充分条件写成一对正式命题，并明确它们与 `AOR-5` 的关系。

### 2026-09-12（P3：`AOR-5` 与 no-resurrection 合并）

定理稿新增 Proposition 27，将已有的 `NR-Event Theorem` 与新 AOR 接口合并。
若 `A` 是退休证书覆盖的节点，`R` 是可被迟到合法消息复活的节点，`B` 是
退休前已暴露能力，则：

```text
B_eff = B union R union (P - A)
```

privacy finality 在齐次阈值模型中要求且在对应闭包假设下等价于：

```text
D is not a subset of B union R union (P - A),  for every D in Gamma_dec.
```

若敌手可任意放置至多 `b` 个暴露节点，其最坏情况计数形式为
`|D intersection (A - R)| > b`。`AOR-5` 使 `R=emptyset`，从而恢复原始
`Robust-Hitting` 条件；没有 `AOR-5`
时，普通退休证书可能仍满足 Robust-Hitting，却因迟到恢复边产生 `R` 并失效。

这一步把论文最重要的叙事拆成两个不可替代的理论对象：

- `Robust-Hitting`：访问结构层面必须永久穿孔哪些节点；
- `AOR-5`：异步状态机层面禁止哪些旧能力重新进入闭包。

稳定公钥、任意迟到消息和恢复活性同时存在时，缺少支配退休事实的单调状态
就会触发前后执行攻击。因此 no-resurrection 不是 forward secrecy 的换名，
而是对恢复访问结构的必要状态条件。

**P3 状态：** 已完成。`NR-Event Theorem`、Proposition 27 和 `AOR-5` 现在共享
同一个集合覆盖定义；计数式只在敌手可任意放置至多 `b` 个暴露节点时使用。

**下一步 P4：** 对 `Adv_AOR^mob` 做具体归约审计，顺序为 AC1/AC2 的自适应承诺
与 pre-frontier 状态一致性、AC3 的 PECC、AC4 的 complaint/AVID scalar isolation、
AC5 的 FGSR frontier wrapper。任何一项不能从 Janus/hbACSS 或候选密码学接口
推出，就保留为条件优势，不扩展协议功能。

### 2026-09-12（P4：Janus/hbACSS 原文证据裁决）

本轮完成了 P4 的原文级核对，并把判断从“组件名称”提升为具体证据：

- **Janus AC1/AC2：** 原文说明公开承诺后擦除 sharing polynomial，并使用可后开口
  的 hashed-ElGamal ciphertext 回答中途自适应腐化（`/home/yzc/flagg/adaptive_dkg_2026_892.txt:445-462`）。这支持自适应状态模拟的局部路线，但目标是 DKG，不是并发 FGSR repair。
- **Janus AC4：** complaint 会让争议 ciphertext 对公众可解密（同文件 `:464-470`），因此必须经过 frontier-safe wrapper，不能直接作为 opaque recovery transport。
- **hbACSS AC2/AC4：** 原文明确 AVID 不提供 secrecy，敌手可看到所有 AVID 消息、公开密文和部分解密密钥（`/home/yzc/flagg/extract_hbACSS.txt:1010-1017`）；`IMPLICATE` 和 share recovery 会公开 receiver key（`:819-830`）。
- **hbACSS AC3：** long-term-key optimization 仍依赖可重复使用的长期密钥（`:972-996`），不能满足退休后的 PECC。

**P4 裁决：** Janus 只作为 AC1/AC2 的局部密码学参考，hbACSS 只作为异步
availability/evaluation correctness 参考；两者都不能直接实例化 `AOR`。具体
归约继续保留 `Adv_Adaptive-Commitment`、`Adv_hbACSS-StaticSim`、`Adv_PECC`、
`Adv_Complaint-Noninterference` 和 `Adv_Generation-Binding`。

下一项不是继续添加文献，而是证明一个 wrapper lemma：将 complaint/decryption
分支替换为 metadata-only、frontier-safe 分支。如果不能在不公开旧 scalar 的
前提下完成，论文保持“抽象主定理 + 条件 AOR 实例”，不声称具体长期安全构造。

### 2026-09-12（P4：Complaint-Noninterference barrier）

定理稿新增 Proposition 28：如果 complaint 的公开内容与保留 ciphertext 一起
能够导出 evaluation point 或 recovery scalar，则仅增加 tombstone 不能使其成为
opaque repair。

- 退休后发送的 complaint 必须在 `Publish` 阶段拒绝；仅在 `Process` 阶段拒绝不够。
- 退休前发送的 complaint 已经进入 `X_hist`，不能被后续擦除撤回。
- 若 complaint 分支读取 challenge-dependent ciphertext、权重或 partial decryption，
  必须进入同一次 `Joint-AO^mob` 的 `DataView`。
- 留在 `PublicView` 的唯一可接受形式是 metadata-only complaint，并配有不泄露
  individual opening 的 simulation-sound proof。

这正式否定了“原样 Janus complaint + FGSR tombstone”的黑盒实例化路线，也说明
`Adv_Complaint-Noninterference` 是独立的具体构造义务。下一步继续审计能否构造
metadata-only complaint；在此之前不把 `C_hb0^opaque` 升级为具体无条件实例。

### 2026-09-12（P4：`ZK-Invalidity` 正向候选）

为处理 complaint 缺口，定理稿新增 Proposition 29，提出用 metadata-only 的
零知识无效性证明替代公开 `KEYREVEAL`。候选接口必须同时满足：

- completeness：所有真实 dealer fault 都能产生证明；
- soundness：诚实 payload 不能被恶意 receiver 伪造为 recovery trigger；
- adaptive zero knowledge：公开 commitment/ciphertext 后仍能模拟腐化状态；
- data-plane factorization：challenge-dependent 分支进入同一次 `Joint-AO^mob`。

若这些条件成立，则 `Adv_Complaint-Noninterference` 可替换为
`Adv_ZK-Invalidity`；但普通 NIZK 不自动提供 decryption-failure proof、异步
availability 或 challenge-dependent publication 的联合模拟。

**当前裁决：** `ZK-Invalidity` 是下一条具体构造路线，不是已完成组件。先审计
是否存在满足这四项条件的现成可验证解密/无效性证明；若没有，保留 AOR 条件
接口，不为首篇论文引入完整新密码学系统。

### 2026-09-12（P4：`ZK-Invalidity` 文献审计）

本地材料没有找到可直接替换 complaint 的现成接口：

- VSSR 的 `vssRecoverVerify*` 只验证恢复贡献，`vssRecover*` 重构缺失 share；
- Choudhuri 的 SE-NIZK 证明密文/PPE 合法性和选定批次解密；
- Silent-Setup 的 NIZK 绑定密文部件、支持 CCA 部分解密模拟；
- Janus complaint 明确把争议 ciphertext 变成公开可解密对象。

因此普通 SE-NIZK、VSSR recovery proof 和 verifiable decryption 都不能直接
关闭 `ZK-Invalidity`。下一步若继续具体化，必须定义独立 failure relation，证明
completeness/soundness/adaptive zero knowledge，并把 publication branch 接入
`Joint-AO^mob`；否则保留 `Adv_ZK-Invalidity`，不引入未经证明的新密码学系统。

### 0.4.10 实验转移后的下一步：完成构造闭合测试

实验已经在其他设备执行，本机工作进入论文的决定性阶段。当前论文仍然是异步联邦学习安全聚合，但首要贡献应落在长期移动腐化下的隐私终结，而不是再增加一个 FL 工程实现。当前成果的准确定位是：抽象 FGSR 主定理已经形成，具体数据面仍是条件实例；因此下一步必须完成一个固定委员会构造闭合测试。

#### A. 先冻结可投稿的安全对象

补齐一个正式的 `F_PF-SA` 理想功能和固定委员会协议描述，明确以下事件的先后关系：

```text
submit -> aggregate certificate -> aggregate opening -> retirement barrier
       -> local erase -> future corruption/recovery
```

每个事件都要标出公开视图、历史暴露视图和隐藏状态。特别是要区分：`CC_sid` 只证明聚合集合和值已经确定，`PF_sid` 还要证明退休集合切断了未来恢复闭包。没有这份功能和状态机，主定理仍像设计原则，不能作为论文定理。

#### B. 选择一个真正可闭合的 repair 路线

下一步只比较两条路线，不再并行扩展更多原语：

1. **首选：私有、可验证、无公开 scalar 的 current-share repair。** 节点通过承诺验证收到的恢复份额；无效响应在本地丢弃，公开 transcript 只留下 receipt/availability metadata。刷新和恢复状态均按 `sid`、coordinate、generation 定位，并由 `PECC` 与原子擦除保护。需要证明它在异步 withholding 下仍能形成 Common-H，且不引入新的 `Cl_rec` 边。
2. **备选：metadata-only `ZK-Invalidity`。** 只有在第一条无法同时保证活性和可验证性时，才定义并证明“解密/评价无效但不公开 scalar”的关系。普通 NIZK、VSSR recovery proof 和 Janus complaint 都不能直接填充该接口。

构造闭合测试的输出不是代码，而是一张 typed-edge ledger：每条 `Share`、`RepairShare`、`RecoveryAuthority`、`PartDec`、`KEYREVEAL` 和 proof edge 都必须标出产生时间、可见对象、擦除时间和退休后的接受条件。

#### C. 按依赖关系完成四个证明

```text
Lemma 1  current-share repair 满足 AOR-1--AOR-5
Lemma 2  opaque repair + Joint-AO^mob 满足 L1--L3
Theorem 1 Robust-Hitting 刻画 PF_sid 的充要访问结构条件
Theorem 2 没有 absorbing frontier 时存在 no-resurrection 攻击
Theorem 3 Recovery-Closure 与 aggregate-only 数据面的组合安全性
```

其中 Lemma 1 是当前真正的 go/no-go 点。若它只能依赖“公开投诉后揭示密钥”，就应停止把 Janus/hbACSS 写成具体长期安全实例；论文改写为抽象主定理、sharp separation 和条件实例化。若它闭合，再将动态委员会写成 Recovery-Closure 的推论，而不是另起一套 handoff 协议。

#### D. 形成论文正文

证明闭合后再整理五个正文模块：问题与反例、FGSR 状态机、Robust-Hitting/Recovery-Closure 主结果、固定委员会构造与安全证明、实验与相关工作。动态节点、packed repair、恶意梯度和新的 FL 基线在此之前全部冻结。这样论文的叙事是“异步安全聚合需要 privacy finality”，而不是“为 FL 拼接前向安全、VSS 和异步 BFT”。

**当前结论：** 下一步不是开始新的实验，也不是继续扩大文献范围，而是完成 `current-share repair -> AOR -> Joint-AO^mob` 的具体闭合；这一步决定论文能否从有价值的抽象边界上升为可投稿的密码学构造。

### 2026-09-12（P5：投诉自由 current-share resharing 候选）

本轮将具体构造从“公开 complaint + 后续擦除”改写为投诉自由的
`current-share resharing` 候选。修复和主动刷新统一为一个状态完整的代际转换：
helper 以当前份额作为新随机多项式的常数项，evaluation 通过 opaque ACSS 私有交付，
接收者本地验证成功后才发布 metadata-only `READY`。无效 evaluation 只导致缺少
`READY`，不触发 `KEYREVEAL`、scalar blame 或公开 recovery point。

新增的关键判断：

- 代数正确性由 `F^{r+1}(X)=sum_h lambda_h f_h(X)` 和
  `F^{r+1}(0)=F^r(0)` 给出；修复目标和其他正确节点安装同一个下一代分享。
- 真正的新接口是 `Common-H`：所有正确节点选择同一组 `2f+1` helper，并获得绑定
  一致的 evaluation；异步 withholding 下至少 `f+1` 个诚实 helper 必须足以形成该集合。
- 若协议语法禁止 scalar-bearing complaint，则 wrapper 层的
  `Adv_Complaint-Noninterference` 为零；剩余义务是 opaque-ACSS、equality-proof、
  `PECC`、Common-H 和 generation binding。
- 若某个底层实现必须公开 scalar blame 才能完成 Common-H，原样 Janus/hbACSS
  不能成为长期安全实例；论文退回抽象主定理 + 条件 AOR 实例化。

定理稿新增 `19.62`，思路稿新增 `28.61`。下一步不再寻找新的 complaint 原语，
而是逐项证明该候选的 Common-H、异步活性和 generation-local exposure；固定委员会
闭合前继续冻结动态 handoff 和新的实验扩展。

### 2026-09-12（P6：APSS/hbACSS 的 Common-H 证据裁决）

完成了对 APSS 与 hbACSS 原文的针对性审计：

- APSS ACSS 的 termination/completeness 保证一个已完成实例最终向所有正确节点
  交付一致份额；其 VABA 选择经过验证的 polynomial proposals，可作为 `Common-H`
  的局部证据。
- APSS `GenZeroPoly` 的 `REVEAL(g^{p(i)},pi_i)` 和公开 evaluation commitment
  不满足本文的 opaque transcript 要求；只能复用 base ACSS/VABA 的形状，移除该
  revelation 阶段，并加入 helper equality proof。
- APSS 删除旧份额和 graceful exit 的讨论支持状态生命周期设计，但其安全证明仍
  是静态模型，不能直接关闭 `PECC` 或长期自适应暴露。
- hbACSS 的 `OK/READY` 机制支持常规 ACSS availability，但原样使用公开
  `IMPLICATE -> SK -> recovery`；这条 scalar-bearing 路径排除其作为投诉自由
  `AOR` 实例。其静态 simulator 也不能直接回答移动腐化后的 endpoint 暴露。

当前底层状态正式更新为：`APSS base ACSS/VABA` 是 Common-H 的条件证据，
`APSS GenZeroPoly` 与原样 hbACSS 都不是可直接接入的长期安全构造。下一步是定义
并审计 `C_CSR^opaque`：适配后的 ACSS 必须同时提供共同 helper、全体正确接收者
evaluation 可用性、无公开 scalar 和自适应 generation-labelled transcript simulation。

### 2026-09-12（P7：`C_CSR^opaque` 与 Common-H 定理冻结）

已将投诉自由路线收敛为正式接口 `C_CSR^opaque`，并在定理稿 `19.64` 写出条件
`Common-H` 定理：

```text
ACS Agreement/Validity/Termination
  + per-helper opaque ACSS completeness
  + local READY soundness
  => common H of 2f+1 helpers and binding-consistent evaluations
```

该定理明确区分了三个层次：ACS 负责共同选择，`2f+1` 个 `READY` 签名证明至少一个
诚实接收者完成，ACSS completeness 再推出全体正确接收者的 evaluation 可用性，
而 `D5/D6` 负责 transcript 不产生 scalar capability 以及 barrier 后端点状态
不可恢复。APSS 的 base ACSS/VABA 只能作为前两项的条件证据；其 `GenZeroPoly`
公开 evaluation revelation 被排除在 `D5` 之外。

当前 P7 产物不是完整密码学实现，而是可逐项审计的 reduction interface。下一步将
检查 `D3` 的 availability certificate 是否能由现有 ACSS/READY 机制产生，同时检查
`D5/D6` 是否能在 adaptive generation-local simulator 中闭合；若不能，保留条件
`C_CSR^opaque` 实例化，不扩展动态节点。

### 2026-09-12（P8：Pedersen opening state 补全）

本轮发现并修正了 `C_CSR^opaque` 的一个状态缺口：Pedersen 版本的 helper equality
proof 不能只依赖当前 scalar `z_j^r`，还需要当前 evaluation commitment 的隐藏
opening `rho_j^r`。因此当前状态正式改为

```text
State_j(c,r)=(z_j^r,rho_j^r,C^r,r,T_j).
```

`rho_j^r` 只用于证明当前 evaluation commitment 与新 helper 多项式常数项承诺
包含同一个消息；它不进入公开 transcript，并在安装下一代状态或退休时与旧份额
一起擦除。定理稿新增 `19.65` 的 `R_eq` 关系和本地 opening consistency lemma。

这一步把 `D2` 的代数含义与 `D6/PECC` 的状态语义接上，但没有关闭 adaptive
simulation：后续仍需证明在 commitment 已公开、helper 之后被腐化的情况下，模拟器
能提供一致状态，同时不重新提供已擦除的 `rho_j^r`。当前优势项继续保留为
`Adv_EqualityProof + Adv_PECC`，不把 Pedersen hiding 单独当作完整证明。

### 2026-09-12（P9：`EqProof^mob` 游戏冻结）

将 helper equality proof 的自适应缺口单独形式化为 `EqProof^mob`：

- barrier 前腐化返回与公开 commitments 一致的 `(z_h^r,rho_h^r)`；
- barrier 后腐化返回下一代状态或 tombstone，不返回旧 `rho_h^r`；
- proof 必须满足 statement binding、adaptive simulation、关系 soundness 和 branch
  noninterference；
- 普通 Pedersen hiding 与普通 NIZK 不足以自动满足这四项。

定理稿新增 `19.66` 和 Corollary 36，思路稿新增 `28.64`。当前最小具体证明义务
变为：为同一 labelled CRS 找到或构造满足 `EqProof^mob` 的 dual-mode/equivocal
commitment + simulation-extractable proof 组合，并把它与 `PECC` 的 endpoint 状态
暴露严格分离。若该组合无法闭合，论文继续采用抽象主定理 + 条件 `C_CSR^opaque`
实例化，不扩展协议边界。

### 2026-09-12（P10：`EqProof^mob` 文献 go/no-go）

完成了本地候选证明系统审计：

- Choudhuri 的 SE-NIZK 提供 `SimProve`、weak simulation-extractability 和直线提取，
  但定理针对静态敌手与 ciphertext/PPE statement，未覆盖 commitment 公开后的
  自适应腐化和擦除状态。
- VSSR 提供 Pedersen evaluation witness 与本地 recovery verification，但其
  `compromise/contrib` 隐藏游戏按每个 commitment 的查询数限制，不包含 frontier、
  generation barrier 或 post-erase corruption。
- Silent-Setup 的证明组件针对密文部件与 CCA partial decryption，不直接是
  current-share 的两 opening 关系。

因此 `EqProof^mob` 仍是可以由现有组件组合、但尚未由任何本地论文直接提供的接口。
下一步是把 `R_eq` 的 dual-mode commitment、SE-NIZK 和 `PECC` 接成一个联合 game；
若无法完成，保留显式 `Adv_EqProof^mob`，不继续扩展协议功能。

### 2026-09-12（P11：`EqProof^mob` 条件 hybrid）

定理稿新增 `19.68` 和 Proposition 37，明确 equality 层的混合顺序：

```text
真实 CRS
 -> simulation/equivocation CRS
 -> SimProve
 -> adaptive hidden-opening consistency
 -> PECC endpoint erasure
 -> frontier/label soundness
```

新增独立优势项 `Adv_Equivocal-Opening^mob`，用于表达“公开 commitment 后再选择
腐化时间”的状态一致性。它不能由普通 Pedersen hiding 或静态 NIZK 自动消除。
最终界按 generation 累加 `Adv_CRS-Mode`、`Adv_SE-NIZK-Simulation`、
`Adv_Equivocal-Opening^mob`、`Adv_PECC`、soundness 和 label binding。

当前下一步是对这条 hybrid 的每一项寻找标准假设实例；若某项只能依赖独立的
adaptive commitment/erasure 假设，则保留该项并继续验证它与 `Joint-AO^mob` 的
数据面边界。

### 2026-09-12（P12：Janus 对 `EqProof^mob` 的局部映射）

完成 Janus 原文级映射：

- Pedersen hiding、分享多项式擦除、可编程 hashed-ElGamal 和自适应腐化模拟，
  支持 `EqProof^mob` hybrid 的 `H1/H3` 局部路线；
- Janus 的 NIZK/一致性证明只能作为 `R_eq` 的候选证明组件，尚未证明本文的
  两-opening relation、generation label 和并发 repair context；
- Janus 假设 secure erasure 和 adaptive PKE，但没有定义 FGSR 的 pending evaluation、
  endpoint buffer、退休 `sid` 状态或 `AOR-5`；
- Janus complaint 会公开争议 ciphertext，因此不能直接进入投诉自由
  `C_CSR^opaque`。

定理稿新增 `19.69` 和 Proposition 38，结论是：Janus 可作为
`Adv_Equivocal-Opening^mob` 的条件 transport substitution，但不能令该项自动为零，
也不能替代 `Common-H`、`PECC`、`AOR-5` 或 `Joint-AO^mob`。下一步是把 Janus
状态改写为本文的 labelled endpoint game，并审计无 complaint 分支的 `D5/D6`。

### 2026-09-12（主定理证明矩阵冻结）

实验基线已在其他设备运行，本地工作转入理论闭合。定理稿新增 `19.70`，思路稿
新增 `28.68`，将当前工作整理为一条可审计的主证明链：

```text
Common-H correctness
  -> frontier absorption / AOR-5
  -> Recovery-State Localization
  -> RCL-Sim/AO
  -> Joint-AO^mob
  -> EqProof^mob + PECC
  -> aggregate-only Privacy-Finality.
```

本轮明确了三个研究边界：

- 主定理可以先以显式优势项形式成立；不能把 hbACSS、Janus、Pedersen hiding 或
  static aggregate encryption 自动提升为本文的长期自适应安全实例。
- 公开 complaint、scalar evaluation、partial decryption 和 proof-controlled branch
  若生成 individual-key capability，必须进入 `Joint-AO^mob` 或单独优势项。
- 动态委员会、packed repair 和额外 FL 场景暂不扩展；它们只有在固定委员会的
  `Recovery-Closure` 定理闭合后才作为推论审计。

**下一步唯一任务：** 完成 `R_eq` 与 `Joint-AO^mob` 的联合审计，逐项固定 statement、
witness、transcript、corruption oracle 和 data-dependent branch，并据此对
`C_CSR^opaque` 做具体实例化的 go/no-go 裁决。

### 2026-09-12（`R_eq` 双层关系审计）

联合审计发现并修正一个重要记号边界：

- `R_eq^share` 证明 helper 的 current-share 等式，属于状态层，需要
  `EqProof^mob`、`PECC`、generation binding 和 post-erase adaptive simulation；
- `R_eq^agg` 证明客户端密文、mask/key、权重和 aggregate descriptor 的一致性，
  属于数据层，必须与 aggregate certificate、partial decryption 和控制分支一起
  进入同一个 `Joint-AO^mob` challenge。

因此，同一个 NIZK 系统可以实现两种关系，但不能用一个静态 `SimProve` 结论同时
替代两种安全证明。定理稿新增 `19.71` 的 typed equality separation lemma，思路稿
新增 `28.69`。当前具体实例化的 go/no-go 条件收敛为：

```text
R_eq^share -> adaptive post-erase simulation + label binding + PECC
R_eq^agg   -> concurrent challenge-dependent simulation + Joint-AO^mob
```

下一步继续固定 `R_eq^agg` 的完整 statement/witness 和 publication branch，并核对
TACITA/Choudhuri 的 `SimProve` 接口是否覆盖 auxiliary input、并发证明和自适应
状态暴露；在此之前不把静态 aggregate-opening 结果提升为长期安全结论。

### 2026-09-12（数据面文献 go/no-go 裁决）

已核对本地 TACITA 与 Choudhuri 转写文档：

- TACITA modified STE 的 extended CPA 允许自适应选择附加密文和等和挑战，但
  `Cor` 在挑战前固定；原文脚注明确将自适应腐化版本排除在范围外
  (`/tmp/tacita-2025-1579.txt:2565-2577`)。
- Choudhuri 的 `SimProve`/SE-NIZK 提供静态 ciphertext/PPE 证明和提取，但其主定理
  针对 static PPT adversary (`usenixsecurity25-choudhuri.pdf_by_PaddleOCR-VL-1.6.md:302-308`)。
- 两者均未定义 FGSR 的 repair oracle、retirement frontier、post-erase endpoint
  exposure 或 `R_eq^agg` 的并发 publication branch。

因此当前不能写出 `TACITA Static-AO + Choudhuri SimProve => Joint-AO^mob`。路线已经
收敛为：先完成“静态 aggregate opening 与长期 privacy finality 的严格分离”作为理论
结果，再决定是否为具体构造引入新的 adaptive lifting。`Joint-AO^mob` 在此之前继续
作为显式接口，不被已有文献自动归零。

### 2026-09-12（Static-AO 到 Privacy-Finality 的匹配攻击）

定理稿新增 `19.73`，思路稿新增 `28.71`。攻击固定一个正确但只具备静态聚合安全
的 threshold-encryption 协议：敌手先提交等和但目标分量不同的挑战向量，随后在
三个 corruption interval 中依次腐化大小为 `f,f,1` 的不相交节点集，累计得到
`2f+1=q_dec` 个旧份额；缺少 state-complete refresh、frontier 擦除或
recovery-state localization 时，最终可重构旧解密钥并打开单个客户端密文。

该攻击严格遵守瞬时腐化上界，说明：

```text
Static-AO + correctness + instantaneous corruption bound
    != Privacy-Finality
```

这把 `Joint-AO^mob` 与 `Recovery-Closure` 的必要性从定义差异提升为匹配分离结果。
下一步不再继续寻找静态 aggregate-opening 论文，而是把该攻击与 frontier/no-
resurrection 必要性整理成论文的 lower-bound/separation 部分。

### 2026-09-12（`F_PF^mob` 理想功能落地）

定理稿新增 `19.74`，思路稿新增 `28.72`，正式区分：

- `CC_sid`：固定参与集合、权重、ciphertext digest 和授权 aggregate；
- `PF_sid`：固定不可回滚的退休 frontier，并关闭该 coordinate 的全部未来恢复路径；
- `X_hist`：按 `Publish` send event 记录已经公开的 key、point 和 recovery material；
- `Corrupt`：退休后只返回当前代状态、frontier metadata 和 tombstone；
- `Joint-AO^mob`：统一生成 challenge-dependent ciphertext、proof、certificate 和
  partial decryption；
- `Recovery-Closure`：排除任何未授权 individual-opening capability。

该功能是一个固定单会话、单描述符的 selective challenge，不提供任意历史数据的
adaptive-query oracle。它把 `F_AWF` 从控制面投影提升为完整的 aggregate-only
privacy-finality 接口，补齐了 lower-bound、主组合定理和论文叙事之间的定义缺口。

下一步应基于 `F_PF^mob` 逐条检查 FGSR wrapper 的 `Bind/Submit/OpenAggregate/
Retire/Publish/Process/Recover/Corrupt` 映射，并把每个不匹配项归入
`Adv_RCL-Sim/AO`、`Adv_Joint-AO^mob` 或 `Adv_Context/Correctness`，不再新增协议功能。

### 2026-09-12（FGSR 到 `F_PF^mob` 的映射闭合）

定理稿新增 `19.75`、Theorem 42，思路稿新增 `28.73`。本轮修正了一个容易造成
证明偷换的同名操作：FGSR 的 `Aggregate(Q,H)` 是 helper polynomial resharing，
现在统一称为 `ReshareAggregate`；`F_PF^mob` 的 `OpenAggregate` 才是客户端更新
的授权加权和释放。

当前 wrapper realization 误差项固定为：

```text
Adv_Joint-AO^mob
  + sum_r Adv_AOR^mob(r)
  + Adv_Common-H/Correctness
  + Adv_Recovery-Localization
  + Adv_Frontier-Use
  + Adv_Context/Binding
  + negl(lambda).
```

这一步闭合了理想功能、lower-bound 和 FGSR wrapper 之间的接口关系，但没有把
`Adv_Joint-AO^mob` 或 `Adv_AOR^mob` 误写为零。下一步是整理论文正文的结果层次：
无条件的访问结构/分离定理、条件的 FGSR 主定理、以及尚未完成的具体密码学实例化。

### 2026-09-12（论文结果层次冻结）

定理稿新增 `19.76`、思路稿新增 `28.74`，现阶段论文结果分为五层：

1. `Robust-Hitting` 的访问结构刻画；
2. `Recovery-Closure`、causal frontier 和 no-resurrection 下界；
3. `Static-AO` 到长期 privacy finality 的三波移动腐化分离攻击；
4. 在 `Joint-AO^mob`、AOR 和 Common-H 下的 FGSR 条件组合定理；
5. TACITA、SE-NIZK、Janus、hbACSS 的具体密码学接口审计。

这一区分意味着当前论文已有不依赖具体新原语的理论核心，但仍未完成具体
adaptive opaque transport 的无条件实例化。后续正文整理必须保持这五层边界，不能
用局部文献结果替换未证明的 `Adv_Joint-AO^mob` 或 `Adv_AOR^mob`。

### 2026-09-12（修正安全游戏的循环 admissibility）

主定理审计发现，旧版 `Joint-AO^mob`/`F_PF^mob` 曾把“query 不得暴露
individual-opening capability”写进 admissibility，这会预先假设待证明的
`CapSafe`。定理稿新增 `19.77`、Lemma 43，现改为：

- query 只受瞬时腐化上界、generation-local `B_{ell,r}`、终端 residual-set 预算和
  协议语法约束；
- 真实 `Corrupt/Recover/Publish/Process` 返回的旧 capability 不被过滤，必须进入
  `X_hist`、`DataView_b` 或 `Adv_Uncovered-Edge`；
- `CapSafe` 和 `Recovery-Closure` 是证明结果或显式优势项，不是游戏入口条件。

这一修正使安全定义非循环：若协议真的暴露退休坐标的旧 capability，实验会显示
该失败；若 AOR、typed ledger、Joint-AO 和 Robust-Hitting 排除所有此类边，才可在
归约中将 `Adv_Uncovered-Edge` 置为零。

### 2026-09-12（P13：证明边界收紧与实验后工作顺序）

实验基线已转移到其他设备后，本地工作不再扩展数据集、模型或端到端基线，转入
论文理论闭合。修正内容如下：

- `Joint-AO^mob` 的 challenge 后查询明确为所有满足外生 exposure budget 和
  label/frontier 语法的 protocol-valid queries；不再使用会暗含 `CapSafe` 的
  `admissible queries` 表述。
- `Adv_Uncovered-Edge` 已加入 Theorem 42 和思路稿的主优势界。若 typed ledger、
  opaque delivery、跨坐标能力隔离和 `PECC` 均被具体证明，可再由归约将该项置零。
- 论文后续按三项交付推进：先完成 `R_eq^share`/`R_eq^agg`、`AOR` 和
  `Joint-AO^mob` 的 typed proof matrix；再做固定委员会 FGSR 的完整安全证明；
  最后把五层结果压缩为正文定理、分离攻击和限制条件。

当前不做动态委员会、packed repair、恶意梯度，也不把现有静态加密或普通 AVSS
直接写成长期自适应安全实例。

### 2026-09-12（P14：恢复闭包感知的退休判据）

定理稿新增 `19.78 Theorem 44`，思路稿新增 `28.75`。本轮把此前分开的
`Robust-Hitting`、`AOR-5` 和 `Recovery-State Localization` 合并为一个正式判据：

```text
E_c(B,A) = B union R_c union (P - A)
privacy finality iff
for every D in Gamma_dec^cap(c), D is not a subset of E_c(B,A)
```

其中 `R_c` 表示退休后仍可由合法恢复边重新生成的旧 capability。由此得到：

- 普通 `Robust-Hitting` 只有在 `R_c=emptyset` 时才足够；
- 删除 direct share、单调 tombstone 和退休证书不能自动关闭恢复闭包；
- `AOR-5` 加 state-complete erasure 的正式作用是令 `R_c=emptyset`；
- ordinary VSSR/DPSS 要成为 FGSR 实例，必须证明该条件，而不是只证明恢复正确性。

这一步把 VSSR/DPSS 的黑盒限制从工程性审计提升为可引用的理论分离。下一步固定
为：将 Theorem 44 的 `R_c=emptyset` 条件逐边映射到具体 `C_CSR^opaque`、
`PECC`、equality proof 和 frontier-bound `Use/PartDec` 接口，并更新 Theorem 42
的证明矩阵；不再增加新的协议功能。

### 2026-09-12（P15：退休闭包接口矩阵）

定理稿新增 `19.79` 和 Lemma 45，思路稿新增 `28.76`。`R_c=emptyset` 现在按七类
边逐项审计：旧 share、pending repair payload、迟到恢复/安装、持久恢复权、公开
proof metadata、aggregate data objects，以及退休前已经发送的 capability。

当前归约边界固定为：

```text
state/buffer edge       -> state-complete erasure + PECC
stale transition edge   -> AOR-5 + generation binding
global recovery edge    -> coordinate puncture/localization
proof-control edge      -> typed isolation + Adv_Uncovered-Edge
data-plane edge         -> Joint-AO^mob
pre-frontier exposure   -> X_hist at Publish time
```

只有全部边被相应接口覆盖后，才能在 Theorem 42 中将
`Adv_Recovery-Localization`、`Adv_Frontier-Use` 或 `Adv_Uncovered-Edge` 置为零；
普通 AVSS、NIZK、前向安全加密和 tombstone 均不能替代这张矩阵。下一步是把该矩阵
逐项绑定到首版 `C_CSR^opaque` 候选的具体算法状态，而不是继续增加新的基线。

### 2026-09-12（P16：候选组件的保守实例化裁决）

已将 Lemma 45 的七类边映射到当前候选组件。结论保持保守：

- APSS/hbACSS 只能提供 `AVSS-opaque` 的私有交付和 availability 候选，不能自动关闭 scalar-capability edge；
- Janus 可提供局部 adaptive equivocation/erasure 证据，但不能直接给出 `PECC`、`EqProof^mob` 或 AOR-5；
- Choudhuri SE-NIZK 只能作为 equality/data-plane simulation 的静态组件；
- TACITA 只能作为 `Static-AO` 基线，不能替代 `Joint-AO^mob`；
- coordinate-local recovery authority、frontier-bound `Use/PartDec` 仍需由 FGSR wrapper 自己证明。

因此首版具体路线固定为条件 `C_CSR^opaque` transport，显式保留
`PECC`、`EqProof^mob`、coordinate-local retirement、frontier-bound data-plane use
和 `Joint-AO^mob`。后续不再把局部文献接口拼接成无条件实例化。

### 2026-09-12（P17：首版 `C_CSR^opaque` 状态映射）

已将 `lsr-construction-audit.md` 的 FGSR v0.1 三道门控正式接入定理稿 `19.81` 和
思路稿 `28.77`。首版状态划分为：

```text
PersistentLive / PublicRepair / Pending / Retired
```

并固定以下状态边界：

- `PersistentLive` 只保留 current share、commitment 和 instance order；
- `PublicRepair` 只含公开标签、承诺、证明和 availability metadata；
- `Pending` 只存在于 receiver 的交付到 install/cancel 窗口，并受 `PECC`；
- `Retired` 只保留 frontier、commitment 和 tombstone；
- authorize、delivery、install、use 四个阶段都检查 frontier 和 generation。

这使 Theorem 44 的 `R_c=emptyset` 有了明确的算法状态目标，但尚未关闭任何底层
密码学项。下一步是为 `Pending -> Install/CancelOrRetire` 写出单次 repair 的
transcript simulator，并逐项证明其满足 `D1`--`D6`、`EqProof^mob` 和 `PECC`；不再
继续扩展动态委员会或新的 FL 基线。

### 2026-09-12（P18：`OneStep-C_CSR` 模拟命题）

定理稿新增 `19.82 Proposition 46`，思路稿新增 `28.78`。单次 repair 的模拟混合
固定为：

```text
real C_CSR
 -> EqProof^mob simulation
 -> AVSS-opaque delivery simulation
 -> PECC post-barrier state simulation
 -> Common-H/affine-coupled installation
 -> frontier/generation rejection
```

对应的误差项为：

```text
Adv_EqProof^mob
+ Adv_ACSS-opaque
+ Adv_PECC
+ Adv_Common-H/Correctness
+ Adv_Pending-Order
+ Adv_Generation-Binding
+ Adv_Frontier-Use
+ Adv_Uncovered-Edge
```

该命题明确了下一项可证伪工作：为 `Pending -> Install/CancelOrRetire` 的真实
channel/ACSS 状态证明上述混合，而不是继续增加抽象接口或 FL 基线。当前仍未声称
任何现有 APSS、hbACSS、Janus 或 Pedersen 实现已经满足 Proposition 46。

### 2026-09-12（P19：pending 取消与退休顺序）

定理稿新增 `19.83 Lemma 47`，思路稿新增 `28.79`。同一 coordinate 的 repair 与
retirement 现在必须共享由 validated agreement 产生的 `prec_c` 实例序：

- `Install` 只有在共同序中先于 `Retire` 时才有效；
- retirement 会擦除所有尚未生效的 pending instance；
- 退休后 pending instance 不得转移到 `PersistentLive`；
- 本地消息到达顺序不能改变共同实例序。

新增显式失败项 `Adv_Pending-Order`，并与 `Adv_Frontier-Use`、
`Adv_Generation-Binding`、`Adv_PECC` 和 `Adv_Uncovered-Edge` 一起进入 pending
closure 证明。下一步是把 `prec_c` 的 certificate 和 `CancelOrRetire` 的原子语义
接入 `C_CSR^opaque` 的 `D1`/`D6`，而不是把并发行为隐藏在“frontier check”一句话中。

### 2026-09-12（P20：`OrderCert_c` 接入 `D1`/`D6`）

已将 coordinate-local 实例序证书正式加入 `C_CSR^opaque`：

```text
O_c = (prefix_c, rank_c(rid), parent_c, T_req, OrderCert_c)
```

现在：

- `D1` 要求 descriptor 绑定完整 `O_c` 和唯一实例序位置；
- `D6` 要求 `CancelOrRetire` 与 generation erase 使用同一个原子屏障，并覆盖所有
  不先于 retirement 生效的 pending instance；
- retirement certificate 是同一 coordinate 序列中的有序事件，不是全局 epoch；
- 没有 `OrderCert_c` 时，`D1` 无法确定 repair 与 retirement 的相对位置，`D6` 也
  无法确定应擦除哪些 pending 输出。

这使 Lemma 47 的共同实例序从证明假设变成了接口输入，但其 agreement、不可伪造
性和原子擦除仍是待证明的具体密码学/异步协议条件。

### 2026-09-12（P21：helper-set ACS 与实例序的严格分离）

本轮确认 `ACS^-` 只产生共同 helper 集合 `H`，不能自动产生 repair/retirement 的
相对顺序。定理稿新增 `19.84 Lemma 48`，思路稿新增 `28.80`，引入独立的
coordinate-local `SeqACS_c`：

```text
e = (c, kind, rid, Q_digest, T_req, parent_c)
OrderCert_c = (c, parent_c, rank, e_digest, quorum_signature)
```

其必要性质为 sequence agreement、prefix consistency、validity 和 termination；
`3f+1` 个 target-excluded 参与者使用 `2f+1` quorum 时，正确节点对同一 rank 至多
签署一个 event。`OrderCert_c` 的失败项明确为：

```text
Adv_Order-Agreement
+ Adv_Order-Prefix
+ Adv_Order-Validity
+ Adv_Order-Termination
+ Adv_Order-Certificate-Soundness
```

这一步避免把 set-valued ACS 错当成 instance-order proof。下一步是审计现有异步
ACS/VABA 是否能提供 `SeqACS_c`，或者在不引入全局 epoch 的前提下给出等价的序列
一致性转换；在此之前 `D1/D6` 仍只能条件化。

### 2026-09-12（P22：现有 ACS/VABA 不能直接实例化 `SeqACS_c`）

完成了对 Juno、APSS、hbACSS 和 DyCAPS 的窄问题审计：它们都没有直接提供
“同一 coordinate 下 repair 与 retirement 事件的可转移前缀证书”。

- Juno 的 AVC 输出聚合后的向量，并以此实现 ACS；它解决的是每个向量位置的共同取值，
  不是带 parent/rank 的 append-only event prefix。
- APSS 的 ACSS/VABA 保证共享完成、共同的候选集合和刷新后的 share 一致性；其
  `REVEAL`/公开 evaluation 阶段也不能直接满足 `D5` 的 opaque transcript 约束。
- hbACSS 的 `READY`/`OK` 证明可用性和一致交付；`IMPLICATE`、密钥揭示和 AVID
  交付对象仍不是退休顺序证书。
- DyCAPS 的 MVBA 排序服务于相邻 epoch 的 committee handoff；它没有在固定
  committee 中为任意并发 coordinate-local repair/retirement 事件提供本稿所需的
  `OrderCert_c`。

因此，普通 ACS/VABA 只能实例化 `Common-H`，不能被声明为 `SeqACS_c`。本稿保留
`SeqACS_c` 作为显式条件接口，并新增一个待证明的集合到序列边界：若 ACS 只输出
无序事件集合，且没有绑定 causal acceptance、parent 和 retirement frontier 的信息，
则任何只对集合做确定性排序的 wrapper 都无法同时保持 D1 的事件语义和 D6 的 pending
擦除语义。具体构造必须引入独立的 prefix certificate，或证明等价的 ordering
mechanism；不能把 digest 排序当成该机制。

### 2026-09-12（P23：实验之外的下一阶段交付）

实验基线在其他设备运行后，本研究的主工作转入三个理论交付，顺序固定如下：

1. **集合到序列的边界定理。** 正式定义 `SetACS` 与 `SeqACS_c` 的观察接口，证明
   无 parent/frontier 绑定的 set-valued 输出不足以支持 `Install/Retire` 的语义序；
   再给出带 `OrderCert_c` 的最小充分条件。
2. **单次 repair 的密码学归约。** 针对 `C_CSR^opaque` 完成
   `EqProof^mob`、opaque ACSS、`PECC`、generation binding 和 frontier-bound use
   的 hybrid，明确每一项失败优势和所需假设。这个结果决定 FGSR 是条件框架还是
   可实例化协议。
3. **长期组合定理与论文结构。** 将单次归约沿 coordinate-local 序列组合到
   `Recovery-Closure`，证明 `R_c=emptyset` 后再连接 `F_PF^mob`；正文只保留主定理、
   集合到序列分离、移动腐化攻击和限制条件，工程状态机细节留在证明附录。

当前不新增动态委员会、packed repair、恶意梯度或自适应查询数据库模型。下一次研究
动作应直接写出第 1 项的正式定义和反例执行，再据此决定 `SeqACS_c` 是构造目标还是
论文中的独立 impossibility boundary。

### 2026-09-12（P24：集合到序列分离命题完成形式化）

已在定理稿 `19.85` 和思路稿 `28.82` 中固定两个观察接口：`SetACS_c` 只输出无序
共同事件集合，`SeqACS_c` 输出带 parent/rank/frontier 绑定的 `OrderCert_c`。分离
命题现在同时要求两项语义：

- `Install-before-retire`：退休前已经生效的合法 repair 必须保留；
- `No-install-after-retire`：退休后才被接受的 repair 必须被取消，不能进入 live state。

两个异步执行都输出同一集合 `{e_R,e_T}`，但一个先完成 repair、另一个先完成
retirement。任何只观察集合的 deterministic wrapper 都无法在两次执行中做出不同
决定，因此 digest 排序不能替代 causal prefix certificate。这解决了原命题可能被
“固定排序仍然是一个序列”反驳的漏洞：论文要求的是保留有效修复与拒绝迟到修复同时
成立，而不是仅仅输出一个列表。

下一步从接口分离转入单次 `C_CSR^opaque` 归约：先明确 `OrderCert_c` 如何进入
`D1/D6`，再逐项处理 `EqProof^mob`、opaque ACSS、`PECC`、generation binding 和
frontier-bound `Use/PartDec`。在这一步完成前，不宣称已有 ACS/VABA 是完整实例。

### 2026-09-12（P25：有序单次归约的失败项拆分）

定理稿新增 `19.86 Proposition 50`，将原来的 `Adv_Pending-Order` 拆成完整的
`SeqACS_c` 证书链失败项和原子退休屏障失败项：

```text
Adv_Order-Agreement
+ Adv_Order-Prefix
+ Adv_Order-Validity
+ Adv_Order-Termination
+ Adv_Order-Certificate-Soundness
+ Adv_Atomic-CancelOrRetire
```

因此单次 `C_CSR^opaque` 归约现在区分两类问题：前五项属于异步事件序列与证书，
最后一项属于 pending 状态、generation erase 和退休屏障的密码学/状态安全。它们
不能继续合并为一个抽象的 frontier check。

下一步固定为 Proposition 50 的局部证明：先证明 `OrderCert_c` 的 certificate chain
不会分叉，再证明 barrier 后 simulator 不需要未暴露的 evaluation、endpoint key 或
helper polynomial。完成这两步后，才把单步结果组合到 `Recovery-Closure`；当前不
把任何现有 ACS/VABA 宣称为完整 `SeqACS_c` 实例。

### 2026-09-12（P26：Turritopsis 是最近候选，但不是直接实例）

补审 Turritopsis 后，文献裁决进行了收紧。它连续执行 `ACS[c,r]`，把共同输出作为
block，并通过 block/checkpoint 链形成配置内的有序交易序列；因此它提供了
`SeqACS^slot` 的路线证据，而不只是普通 set-valued ACS。

但它仍不能直接实例化本文的 `OrderCert_c`：

- checkpoint 按一组 ACS block 生成，不是每个 coordinate-local event 的可转移证书；
- 顺序语义绑定配置内的连续 ACS 和动态 handoff，不是固定委员会的独立 coordinate
  prefix；
- 移动腐化受配置更替、离开配额和 ADKR 条件约束，没有给出本稿固定委员会下
  `Joint-AO^mob`、`PECC` 和 signer-state opacity 的归约。

因此不再使用“现有工作完全没有序列机制”的表述，改为：现有工作提供了顺序化路线，
但没有提供本稿安全游戏所需的完整 `SeqACS_c`。

### 2026-09-12（P27：确定 `SeqACS^slot` 构造路线）

下一步构造目标固定为 coordinate-local 的连续 ACS slot：每个 slot 将前一 prefix
digest 作为 parent 输入，只有共同 ACS 决定后才形成 `E_k` 并签发
`OrderCert_c(k)`。需要独立证明 slot agreement、prefix consistency、event validity、
generation binding、无跳 slot 终止、移动 signer exposure 下的 certificate soundness，
以及同一 slot 同时包含 repair/retirement 时的确定性语义。

这条路线不会把 Turritopsis 当作黑盒复用，而是将其顺序化思想改造成固定委员会、
coordinate-local、frontier-bound 的候选。若 `SeqACS^slot` 证明失败，失败原因本身
将成为论文的 ordering boundary；若成功，则接着完成 Proposition 50 的密码学归约。

### 2026-09-12（P28：`SeqACS^slot` 条件定理骨架）

定理稿新增 `19.89`，把 `SeqACS^slot` 单独条件化。除 slot ACS 的 agreement、
validity、termination 外，还必须证明：

- 每个 live event 最终进入某个 slot，或得到认证拒绝（`Adv_Slot-Admission`）；
- proposal 绑定 coordinate、rank、parent、完整 request、generation 和 kind；
- canonicalization 确定且去重；
- 移动 signer state 累积暴露时，`OrderCert_c` 仍不可伪造。

该条件定理给出 `Adv_SeqACS^slot` 的失败项，并明确两个不能被普通 ACS 或普通
threshold signature 自动覆盖的缺口：slot admission 和 mobile signer exposure。
下一步应优先证明这两个缺口，随后才进入 `PECC` 与 opaque delivery 的具体归约。

### 2026-09-12（P29：前向安全签名只覆盖排序证书）

核对 Libert--Yung 后，前向安全阈值机制可作为 `Adv_Mobile-Signer-Exposure` 的候选
组件：logical period 对应 coordinate-local slot rank，`Update(k)` 后擦除旧 rank
的 signing state，旧 rank 的签名请求被拒绝。

但其安全前提必须重新映射到异步 rank 推进和移动腐化暴露；普通长期阈值签名不能
直接使用。更重要的是，即使 `FSig_c` 成功，结论也只覆盖旧 `OrderCert_c` 不可伪造，
不覆盖 repair evaluation、endpoint key、recovery authority 或 aggregate-only
opening。因此密码学分工固定为：

```text
FSig_c       -> ordering certificate
PECC         -> retired-state exposure
Joint-AO^mob -> aggregate-only data plane
```

下一步先证明 slot admission 和 rank-signing state 的异步安全，再回到 Proposition 50
的 opaque delivery；不把 forward-secure encryption/signature 写成完整 privacy-finality
方案。

### 2026-09-12（P30：普通 ACS 不提供 retirement admission）

定理稿新增 `19.91 Proposition 52`，正式分离 `Adv_Slot-Admission`：标准 ACS 的
agreement、validity、termination 可以全部成立，但某个合法 retirement event 仍被
其他合法 descriptor 或 no-op event 永久遗漏。

因此 `SeqACS^slot` 需要额外的：

```text
Admit_c(e) -> AdmissionCert_c(e)
SlotACS_c(k,parent,AdmissionCerts) -> E_k or RejectCert_c(e,reason)
```

该接口要求 retirement 在有限 slot 内被纳入，或获得可转移的 terminal rejection；
endorsement quorum 只有在 slot 决策规则将其升级为 priority constraint 时才足够。
这一步把 slot admission 从“ACS validity 的自然结果”改正为独立的 ordering/liveness
贡献，也是当前构造路线最明确的新协议接口。

下一步转向 `Adv_Mobile-Signer-Exposure`：证明长期阈值签名在累计移动腐化下的失败，
并给出 `FSig_c` 作为 logical-rank signing 的条件替代。

### 2026-09-12（P31：普通阈值签名的累计移动腐化攻击）

定理稿新增 `19.92 Proposition 53`：若 `OrderCert_c` 使用 `q_sig=2f+1` 的长期
阈值签名，且每个 interval 暴露 `t>0` 个新 signer state，经过
`ceil(q_sig/t)` 个 interval 后，敌手即可累计足够 shares 伪造任意旧 rank 的证书，
同时始终满足瞬时腐化上限。

该攻击只破坏 D1/D6 的排序、安装和取消授权，不需要恢复 repair 明文，因此独立于
`PECC` 和 `Joint-AO^mob`。它证明普通 threshold signature 不能用于
`Adv_Mobile-Signer-Exposure`；后续必须分析 rank-specific `FSig_c` 的异步混合状态、
旧 share 擦除和晚到证书拒绝，而不能把前向安全假设直接当作完成证明。

### 2026-09-12（P32：`FSig_c` 的 mixed-rank 条件）

定理稿新增 `19.93 Proposition 54`。由于异步节点不会同时推进 rank，`FSig_c` 必须
满足四个本地状态规则：只签当前 rank、只接受扩展当前 prefix 的证书、原子更新并擦除
旧 share、拒绝不在已认证 prefix 中的晚到旧证书。

安全条件还必须定义 `E_{c,k}`：rank `k` 的 signer state 在本地擦除前被读取的节点
集合，并要求 `|E_{c,k}|<q_sig`。这可以作为当前 causal-generation-bounded 模型
对排序层的明确约束；若不想把它写进敌手模型，就必须构造 collective erase certificate。

下一步将检查这个条件与 `Slot-Admission` 是否形成循环：若关闭 rank 需要 collective
erase，而 erase certificate 又依赖该 rank 的 ordering，则需要一个独立的 barrier
协议，而不是把 `FSig_c.Update` 当作现成解决方案。

### 2026-09-13（P33：`FSig_c` 从首篇主线降为扩展）

完成循环审计后修正了构造边界。`Proposition 53` 的累计腐化攻击针对 timeless、
stateless acceptance：未来验证者只凭公钥接受旧 `OrderCert_c`。首篇固定委员会可用
state-relative acceptance，要求证书扩展本地 current head、位于下一 rank、满足当前
frontier，且不能跨越已接受的 retirement。

定理稿新增 `19.94 Lemma 55`：节点进入退休集合 `A` 后，未来伪造旧排序证书不会扩大
`E_c(B,A)`；旧 parent/frontier 被确定性拒绝。未完成退休的节点已经属于 `P-A`。只有
prefix rollback、frontier-use 或 state recovery resurrection 才会产生新边，分别计入
`Adv_Parent-Binding`、`Adv_Frontier-Use`、`Adv_AOR-5` 和
`Adv_State-Recovery-Rollback`。

因此 `FSig_c` 不再是首篇定理前提，只保留为动态成员、无状态验证或 timeless public
audit 的扩展。主线使用 live-rank quorum authentication 加 monotone prefix/AOR-5，
消除了 collective signer erasure 与 ordering certificate 互相依赖的循环。

下一步回到真正未闭合的协议项：用 repeated/sticky proposal 证明 retirement 的
slot admission，并规定同一 slot 中 retirement 对 repair 的支配规则。

### 2026-09-13（P34：sticky admission 关闭 `Adv_Slot-Admission`）

定理稿新增 `19.95 Theorem 56`。正确节点收到合法 retirement 后，在每个后续 slot
持续提议它，直到共同 prefix 已包含它或证明其 terminal。在最终扩散、顺序 slot、ACS
termination 和决定集合包含至少一个正确提案的条件下，某个后续 slot 必然通过
`UnionValid` 纳入 retirement。

因此首篇不需要独立 `AdmissionCert_c`；`Adv_Slot-Admission` 可归约到
`Adv_Retire-Diffusion`、`Adv_SlotACS-Termination`、
`Adv_Correct-Proposal-Inclusion`、`Adv_Retire-Validity-Stability` 和
`Adv_UnionValid`。`Proposition 52` 仍作为单次 ACS 不足性的分离结果。

### 2026-09-13（P35：同 slot 的 retirement-dominates）

定理稿新增 `19.96 Lemma 57`。一个 slot 同时选中 repair 与唯一合法 retirement 时，
canonicalization 只输出 retirement，并取消同 slot repair；前一 prefix 中已经安装的
repair 由退休屏障统一关闭。该规则直接由状态语义决定，不使用消息到达顺序或任意
digest 排序。

至此 ordering 层剩余条件缩减为：连续 slot/prefix agreement、live-rank quorum
authentication 和 state-relative stale rejection。下一步应把 Theorem 56、Lemma 57
与 Proposition 50 合并，给出不依赖 `FSig_c`/`AdmissionCert_c` 的首篇 ordering
实例化定理。

### 2026-09-13（P36：首篇 ordering 层完成条件实例化）

定理稿新增 `19.97 Theorem 58`，组合连续 ACS slot、sticky event proposal、
`UnionValid`、retirement-dominates、live-rank quorum authentication 和
state-relative acceptance。合法 repair 与 retirement 都持续重提；repair 最终被决定，
或因 retirement 先终结而得到认证取消。

Theorem 58 按 slot rank 归纳证明 sequence agreement、prefix consistency、event
validity 和 termination，并将 ordering 失败界展开为 ACS、diffusion、canonicalization、
live-rank authentication、parent/frontier、AOR-5 和 rollback-safe recovery 项。

该结果不依赖 `FSig_c` 或 `AdmissionCert_c`，已经填充 Proposition 50 的 ordering
前提。下一步转入单次 repair 的密码学核心：优先处理 `PECC` 与 opaque ACSS delivery
的 post-barrier 模拟，然后再接 `EqProof^mob` 和 `Common-H`。

### 2026-09-13（P37：PECC 从网络删除语义修正为能力排除）

重新审计 `19.29`、`19.35.3` 和 `19.42` 后，修正了 PECC 的挑战边界。异步网络允许
永久保留和迟到交付密文；PECC 要求的是已确认退休的 endpoint 残留状态不能把该密文
转化为旧 scalar capability。barrier 改为节点接受共同 retirement rank 的本地线性化点，
未确认节点进入 `U_c` 和 `X_current(U_c)`，不再隐含全网同步擦除。

PECC challenge 只作用于 barrier 前未腐化的 endpoint。pre-barrier 腐化返回真实 key、
plaintext 和 opening 并进入 `X_hist`；post-barrier 腐化返回完整 residual queue/buffer，
但 retired label 的 key registration、decryption、recovery 和 install 全部关闭。这一分区
避免 PECC 错误承担完整 adaptive equivocation；后者仍属于 `AVSS-opaque/AOR-3`。

### 2026-09-13（P38：临时 PKE 归约与 delayed-state closure）

定理稿新增 `19.98 Proposition 59`：fresh per-instance receiver key、完整 label 绑定、
本地 state-complete erasure 和 absorbing retirement 下，PECC 可归约到 IND-CCA PKE；在
authenticated unique-ciphertext delivery 下可降为 IND-CPA。forward-secure 或 puncturable
encryption 不是该局部性质的必要组件。

新增 `19.99 Theorem 60`，逐项覆盖六类状态：endpoint key、plaintext evaluation、
opening/verification randomness、receiver/send buffer、helper polynomial coefficients、
undelivered recovery response。证明分别处理未注册 endpoint、在途密文、已交付未安装、
install-before-retire、retire-before-install 和 helper-side residual state。公开网络密文
保留不影响结论。

该定理将 Proposition 50 的 `Adv_PECC + Adv_Atomic-CancelOrRetire` 具体化为 PKE、label
authentication 和单一 state-complete barrier，并证明迟到网络状态不会为已确认集合
`A_c` 增加 `R_c`。下一步进入 opaque ACSS delivery 的联合 transcript simulation，重点
核对 availability certificate、receiver verification 与 pre-barrier adaptive exposure。

### 2026-09-13（P39：发现 local-READY completeness 反例）

对 `C_CSR^opaque` 的 `AvailCert_h` 进行 target-excluded 审计后发现：`2f+1` 个 receiver
仅验证各自 evaluation 的 READY，不能推出 repair target 的 ciphertext 有效。Byzantine
helper 可向全部 signer 发送有效 payload，同时向 target 发送无效 payload；证书与 AVID
availability 均成立，但 target 无法安装。

定理稿新增 `19.100 Proposition 61`。该结果表明 hbACSS 的 implication/share-recovery
路径不是可直接删除的附属机制；删除 scalar complaint 后，必须用“所有 receiver
ciphertext 可公开验证”替代。单纯提高 READY 门限仍受 Byzantine withholding 限制。

### 2026-09-13（P40：候选 transport 改为 PVOD）

`19.62` 与 `19.64` 已从 local-decryption READY 改为 Publicly Verifiable Opaque Delivery。
每个 helper 对完整 receiver vector 发布 `R_ved` proofs，证明 ciphertext 加密了 committed
polynomial 在对应 index 的 opening。向量经 AVID dispersal；`AVAIL` 只证明 public
verification 和 dispersal completion，不依赖 receiver 私密解密结果。

`2f+1` 个 non-target AVAIL 至少含 `f+1` 个正确 AVID-completion 节点，足以触发 AVID
availability；`R_ved` soundness 再保证 target 取回的密文解密为唯一 committed evaluation。
因此 Common-H 的 correctness 与 complaint-free privacy 被分离：前者来自 public validity
+ availability，后者进入 selective-opening simulation。

### 2026-09-13（P41：opaque-delivery factorization）

定理稿新增 `19.101 Lemma 62/Theorem 63`。Lemma 62 证明 AVID trace、AVAIL pattern 和
AvailCert 都是 PVOD public vector 与调度的 PPT 后处理，不产生独立 privacy loss。

Theorem 63 将 `Adv_ACSS-opaque` 归约到 generation-local affine coupling、hiding
commitment、`SO-VE[R_ved]`、post-barrier PECC、`R_ved` soundness、label binding 和
uncovered-edge audit。`SO-VE` 明确处理 adversary 看到整组相关 Shamir ciphertext 后再
自适应选择至多 `f` 个 endpoint 打开的 selective-opening 问题；普通 IND-CPA 不足。

文献裁决同步更新：hbACSS 缺少全 receiver 公共 ciphertext validity；Janus 的 adaptive
equivocation 伴随公开 complaint；Illusi 的 adaptive PVSS 最接近 public-verifiability 与
adaptive-security 组合，但输出 group-valued share，不能直接执行 scalar Shamir repair。
下一步具体实例化 `SO-VE[R_ved]`，不再扩展 ordering 或实验基线。

### 2026-09-13（P42：统一主线证书语义）

一致性审计发现早期章节仍把 metadata-only `READY` 当作 active candidate 的 target
delivery 证据。现已区分：相关工作中的 hbACSS/APSS `READY` 保留原名；本文
`FGSR-PVOD` 只使用 `AVAIL`，其含义是逐 receiver `R_ved` 公共验证通过并完成 AVID
dispersal。`Common-H` 的 target delivery 由 AVID availability 加 `R_ved` soundness
推出，不能由 local decryption receipt 推出。

旧 `READY` 路线现在明确标记为 Proposition 61 的分离候选，不再进入 Theorem 33、
Theorem 42 或 Proposition 50 的 active instantiation。下一步审计 `SO-VE[R_ved]` 是否
能够在标准模型中由 selective-opening/non-committing encryption 与 simulation-sound
NIZK 组合，重点检查 adaptive corruption 与相关 Shamir evaluations 的联合分布。

### 2026-09-13（P43：将 `SO-VE` 收紧为 `CSO-VE`）

本轮完成了 opaque delivery 证明缺口的接口级修正。原来的 `SO-VE[R_ved]` 只写明“密文
可选择打开”，没有明确公开子份额承诺、相关 Shamir 明文、后期开口和 proof transcript
必须在同一个 game 中保持一致。定理稿 `19.102`--`19.104` 现在将主线接口改为
**Commitment-Assisted Selective-Opening Verifiable Encryption (`CSO-VE[R_ved]`)**。

每个 receiver 的公开对象固定为

```text
M_{h,j}=Com(y_{h,j};rho^M_{h,j})
ct_{h,j}=Enc(pk_{Q,j},(y_{h,j},rho^D_{h,j},rho^M_{h,j});omega_{h,j},Q,h,j)
pi_{ved,h,j}: R_{ved}
```

其中 `rho^D` 是多项式 evaluation opening，`rho^M` 是公开子份额承诺 opening。这样
`R_ved` 同时绑定 `D_h`、`M_{h,j}` 和 `ct_{h,j}`，而 receiver 在解密后只进行本地
一致性检查，不把标量或 opening 写入公开 transcript。

新增的 Proposition 64 明确记录：普通 IND-CPA、普通 RIND-SO 或静态 NIZK zero knowledge
均不能单独推出本文接口。Dynamic-PSS/APSS 已指出，RIND-SO 可以处理晚期 key opening，
但未知 PVSS secret 诱导的相关 plaintext vector 仍需要 public commitments 和独立的
simulation argument（`/home/yzc/flagg/dynamic_pss_2022_619.txt:2446-2466`）。因此
本文不再把 RIND-SO 写成黑盒实例化。

当前证明义务被固定为四项：相关 Shamir 明文模拟、承诺 equivocation 或 uniform
preimage sampling、与后期开口一致的 simulation-sound `R_ved` proof、以及 barrier 后
由 `PECC` 完成 endpoint 状态闭合。PVOD、Theorem 63 和思路稿 `28.97`--`28.100` 已
同步更新。创新边界也随之明确：贡献不是重新发明 selective-opening encryption，而是
把“相关标量 Shamir repair 的自适应透明交付”定义为异步 FGSR 的必要接口，并证明它
如何进入 frontier-gated retirement、Recovery-Closure 和 aggregate-only finality。

下一步只做一件事：对一个候选 dual-mode commitment、adaptive selective-opening PKE 和
simulation-sound NIZK 组合写出 `CSO-VE[R_ved]` 的具体构造与 hybrid proof。若无法在标量
Shamir repair 下闭合，则保留 Theorem 63 的条件主定理，并把该失败记录为明确的构造障碍，
不再扩展 dynamic committee、packed repair 或新的实验变量。

### 2026-09-13（P44：具体 `CSO-VE` 构造筛选）

本轮把接口级目标进一步收缩为一个可执行的构造审计。候选协议对每个 receiver `j` 生成

```text
(y,rho^D) <- EvalOpenSample(D_h,j)
M <- Com(y;rho^M)
ct <- Enc(pk_{Q,j},(y,rho^D,rho^M);L(Q,h,j))
pi <- Prove(R_ved,(Q,D_h,pk_{Q,j},M,ct,j),(y,rho^D,rho^M,omega))
```

receiver 本地解密并检查两个 opening，随后由 frontier barrier 擦除完整 endpoint
状态。公开对象只有 `(M,ct,pi)` 和 AVID 元数据。

构造只有在一个联合 game 中同时满足以下四点时才进入主定理：

1. `M` 支持模拟后的 equivocation 或 uniform preimage-sampling；
2. 加密支持发布完整密文向量后的自适应 key opening，并保留隐藏 degree-`2f` 多项式
   产生的相关明文关系；
3. `R_ved` proof 支持并发模拟、simulation soundness 和后期开口一致性；
4. `PECC` 覆盖 key、明文、两个 opening、随机性和解密缓冲区，而不假设网络删除迟到密文。

另加 key-origin 条件：首篇固定委员会模型中的 receiver public keys 在 repair 前已经
注册，repair simulator 不拥有对应 secret keys。若模拟器自己生成全部 keys，只能得到
trusted-setup 变体，不能作为 stable-key 下长期自适应腐化的证明。

组件筛选结论已经固定：APSS Section 7.3 提供语法但其 RIND-SO 警告排除直接黑盒使用；
Janus 提供 adaptive commitment/encryption state equivocation，但 complaint/reveal 分支
违反本文的 scalar-free `D5`；Illusi 提供公开可验证 PVSS，却不能直接输出 scalar
Shamir repair。下一步只审计一个候选 PKE 的 late-key-opening hybrid；无法处理隐藏常数、
后期开口或必须公开 scalar complaint 的候选立即退出主线。

### 2026-09-13（P45：候选 PKE 的最终边界）

完成候选原语的逐项裁决。Libert--Yung 前向安全非交互阈值加密提供外部 public key、
自适应腐化和全局 period 的历史保密，但不提供 per-coordinate frontier、`D_h` 约束下
的 scalar Shamir evaluation validity，也不解决 target-excluded delivery；因此只能作为
forward-security 对照。Janus 提供 Pedersen commitment、encrypted opening、erasure 和
adaptive state equivocation，但其 complaint 会公开 disputed ciphertext 的解封能力；
删除该分支后，必须另行提供 PVOD 的全 receiver public validity。APSS Section 7.3 的
commitment-to-subshare 变体最接近本文的对象语法，但其 RIND-SO 分析明确指出未知 secret
相关 PVSS vector 仍需独立 simulation argument。Illusi 的 adaptive PVSS 虽然公开可验证，
却返回 group-valued share，不能直接恢复 scalar Shamir repair。

因此当前不存在可直接引用的端到端实例。下一轮的唯一技术任务是选择一个支持外部公钥
late-key-opening 的候选，针对隐藏 degree-`2f` polynomial 的完整 evaluation vector 写出
联合 hybrid；若仍需隐藏常数、无法回答后期开口或引入 scalar complaint，则将其正式记录
为构造障碍，保留 Theorem 63 的条件主定理。

### 2026-09-13（P46：HPW15 receiver-SO 边界裁决）

完成 Hazay--Patra--Warinschi（HPW15）原文核对。该工作研究 receiver-side selective
opening：攻击者看到完整密文向量后选择 receiver，并获得相应解密私钥
(`/tmp/hpw15.txt:298-312`)；其 `rind-so` 与 `rsim-so` 分别对应不可区分和模拟安全，且
Theorem 4.4 说明 NCER 可以给出 receiver-SO 模拟 (`/tmp/hpw15.txt:962-1018`)。这确认
HPW15 是本文 key-exposure 层的正确理论起点，不是 sender-opening SO。

HPW15 仍不能直接实例化本文接口：其证明中的模拟器自行生成并持有所有公钥对应的私钥；
本文要求外部预注册公钥下的 late opening。其消息分布可相关且可重采样，但没有证明隐藏
Shamir polynomial 诱导的 evaluation、opening randomness、公开 commitment 与 `R_ved`
proof 的联合模拟，也没有异步 AVID/erasure 状态的并发组合定理。Pan--Wagner--Zeng 的
`SIM-SO-CCA` 则属于 sender-opening `(m_i,r_i)` 模型，不能替代 receiver-key opening。

当前密码学接口正式命名为：

```text
external-key correlated receiver-opening with publicly verifiable opaque delivery
```

P46 的结论是：HPW15 可作为 receiver-key opening 子层的安全依据，但不能作为 Theorem 63
的黑盒实例。下一步只做一个构造审计：在不让模拟器获得 endpoint secret key 的条件下，
为完整密文向量写出同一隐藏 degree-`2f` polynomial 的 late-key-opening hybrid，并检查
`R_ved` 是否能在后期开钥后保持一致。若不能，则保留条件主定理并将该联合接口记录为明确
的构造障碍；不扩展 dynamic committee、packed repair 或新实验变量。

### 2026-09-13（P47：Key-Origin 子游戏与 hybrid 顺序）

本轮确认一个先于 NCER 的理论缺口：外部预注册 `pk_{Q,j}` 后，真实 endpoint 持有对应
`sk_{Q,j}`；若 repair simulator 只获得公钥而没有 key-generation witness，就不能一般性
地产生一把既服从注册分布、又能解开已发布密文的私钥。让 simulator 自行生成全部 key 会
回到 HPW15 的 key-generated 模型，不能支撑 stable-key 移动腐化。

因此 `CSO-VE` 新增 `KeyOrigin` 子游戏。它必须提供 oblivious/dual-mode key explanation，
或提供受限的真实 key-opening oracle，并明确不交付未开启 evaluation。普通唯一私钥 PKE
不自动满足该接口；HPW15 的 key-simulatable PKE 只能作为 `KeyOrigin` 候选，仍需与相关
Shamir payload、承诺和 `R_ved` 联合证明。

后续证明顺序固定为：

```text
H0  外部注册 key、相关 Shamir payload、真实 R_ved
H1  KeyOrigin：oblivious/dual-mode key explanation
H2  NCER：未开启 endpoint 的假密文与 barrier 前 key opening
H3  Commitment/R_ved：保持同一隐藏多项式关系并模拟公开 proof
H4  PECC：仅在 endpoint barrier 后消除本地状态
```

P47 的执行任务是只审计 HPW15 key-simulatable 路线能否关闭 `H1`。关闭前不扩展协议层、
动态委员会、packed repair 或实验变量。

### 2026-09-13（P48：HPW15 `ksim` 不等于 Key-Origin）

完成 HPW15 key-simulatable 路线的细化审计。其 `ksim` 只比较真实公钥与 oblivious 公钥
的分布；HPW15 的 `nOpen`/`tOpen` 仍以原始 secret key 为输入
(`/tmp/hpw15.txt:452-524`, `:530-569`, `:1450-1535`)。因此它能支持 public-key
distribution hybrid，但不能在模拟器没有外部注册 `sk_{Q,j}` 时，针对已发布密文产生可
解密且与指定 evaluation 一致的 late key opening。

本文所需接口具体化为：

```text
SimKeyGen  -> (pk,tau)       不产生 endpoint sk
SimKeyOpen -> sk_star        密文发布后开启到指定 plaintext
```

其中 `pk` 必须与外部注册公钥不可区分，`sk_star` 必须满足 endpoint correctness，且其
完整状态要能继续通过 `R_ved` 和相关 Shamir witness 的联合模拟。HPW15 的 extended
key-simulatable PKE 允许 oblivious 公钥没有合法私钥，不能直接作为必须解密真实 payload
的 endpoint。

P48 将候选状态更新为：HPW15 是 receiver-SO 与 public-key simulation 的理论基座，但
尚未关闭 `H1`。下一步先完成 `KeyOrigin` 的安全实验和候选构造；在此之前不把 HPW15
写成本文的具体实例化。

### 2026-09-13（P49：形式化 `KeyOrigin` 安全游戏）

将 `KeyOrigin` 具体化为外部密钥非承诺式接口：

```text
RealKeyGen(1^lambda) -> (pk,sk)
SimKeyGen(1^lambda)  -> (pk,tau)
SimEnc(pk, public-context) -> (ct,sigma)
SimKeyOpen(tau,sigma,m,public-state) -> sk_star
```

模拟器先发布与外部注册公钥不可区分的 `pk` 和完整 `(ct,proof)` 向量；只有 endpoint 在
barrier 前被腐化时，理想功能才交付该 endpoint 的 `m`，随后 `SimKeyOpen` 必须返回可解密
既有密文的 `sk_star` 及一致状态。模拟器不获得未开启 evaluation 或真实 `sk`。

该游戏同时量化于移动腐化时序和同一个隐藏 degree-`2f` polynomial 产生的相关 evaluation
向量，`R_ved` proof 也属于联合 transcript。由此，HPW15 `ksim` 只覆盖公钥分布层，
HPW15 `nOpen/tOpen` 依赖原始 `sk`，两者均不能单独关闭 `H1`。

P49 固定证明顺序：先证明 `KeyOrigin`，再证明相关 NCER 与 `Commitment/R_ved` 联合模拟，
最后接入 `PECC`。下一轮只进行该接口的候选构造审计。

### 2026-09-13（P50：YLH20 提供有条件的 Key-Origin 候选）

核对 Yang、Lai、Huang、Au、Xu、Susilo 的 multi-challenge receiver-SO 工作。其
`SIM-RSO_k-CPA` 允许同一公钥承载 `k` 个密文；模拟器先发布 public keys 和 malformed
ciphertexts，收到开启消息后再构造能够解密既有密文的 secret key
(`/tmp/ylh20.txt:903-951`, `:1000-1060`)。这比 HPW15 的 `ksim` 更接近本文的
`SimKeyOpen`，因为它不需要原始 endpoint secret key。

候选仍然是有条件的：YLH20 的 simulator 控制 `S1` 的 key generation，不是解释独立
registry 已固定的任意 public key；基本构造以 bit message 为单位，payload 扩展需要与
消息长度匹配的 secret-key entropy；同时没有 `M`、隐藏 Shamir witness、`R_ved` 和
`PECC` 的联合定理。

因此新增两条模型路线：

```text
协议管理的 key registration -> YLH20 可作为 H1 候选
任意外部固定 public key      -> YLH20 仍不足以关闭 H1
```

P50 将下一步从“继续寻找普通 NCER”改为：先在协议管理注册版本中写出 YLH20 的
`KeyOrigin` 归约，再检查其与相关 scalar Shamir opaque delivery 的组合；不改变固定
委员会、移动腐化和 aggregate-only 的主研究范围。

### 2026-09-13（P51：YLH20-PVOD lifting 目标）

形成具体候选映射：将每个 endpoint payload 编码为 `L` 个 bit ciphertext，共用一个
YLH20 receiver key。`S2` 先发布全部 malformed ciphertext，`S3` 在收到被开启 payload
后构造一致 secret key，因此可作为协议管理 key registration 下的 `KeyOrigin` 层。

PVOD 组合的关键是：malformed ciphertext 没有真实 encryption randomness，模拟器必须在
simulation CRS 下生成 `R_ved` proof，并通过 commitment equivocation 让 `M_{h,j}` 在
后期开启时与 Shamir evaluation 一致。不能把模拟 proof 当作真实 encryption witness。

新增条件 lifting lemma 的假设为 DDH、dual-mode hiding commitment 和 concurrently
simulation-sound NIZK。其已知代价是每个 `L`-bit payload 需要 `L` 个 ciphertext 和
`L` 个 branch components；这属于 receiver-SO equivocation 的理论成本。

P51 的下一步是对单个 generation 写出完整 YLH20-PVOD hybrid，并逐项检查 malformed
ciphertext、模拟 proof、承诺开口和 `PECC` 之间是否产生未覆盖的公开边。严格任意外部
固定公钥模型继续单独保留。

### 2026-09-13（P52：单 generation hybrid 与 key reuse 下界）

完成 YLH20-PVOD 的单 generation 审计。令 `L_Q` 为 endpoint payload
`(y_{Q,j},rho^D_{Q,j},rho^M_{Q,j})` 的编码长度；`R_ved` 的 encryption randomness
只作为 proof witness。候选 hybrid 固定为：

```text
H0  真实 YLH20 key、真实密文、承诺和 R_ved
H1  模拟 key registration
H2  在 statement 仍为真时切换 simulated R_ved
H3  切换到可 equivocate commitment
H4  S2 malformed ciphertext vector
H5  S3 按开启 payload 构造一致 secret key
H6  barrier 后由 PECC 替换为擦除状态
```

malformed ciphertext 没有真实 encryption witness，不能先完成密文替换再生成真实 `R_ved`
proof。应先完成真实 statement 上的 simulated proof 和可 equivocate commitment，再用
YLH20 DDH hybrid 替换密文；`H4 -> H5` 才处理后期开钥与相关 Shamir evaluation 的一致性。
单 generation 下，YLH20 可作为协议管理
注册版本的 `KeyOrigin` 候选，代价约为每个 endpoint `L_Q` 个 bit ciphertext 和对应
branch components。

同时确认长期边界：YLH20 的 `k` 预先界定同一公钥的 challenge 数，私钥 entropy 随
challenge 数和消息长度增长。因而构造应为每个 `(Q,j)` 注册 fresh context key；同一
公钥跨无界 generation 复用不属于该定理，也不能由 `PECC` 隐藏。

### 2026-09-13（P53：修正 YLH20-PVOD proof order）

发现并修正原 hybrid 顺序中的证明缺口：malformed ciphertext 没有真实 encryption witness，
因此不能先替换密文、再生成真实 `R_ved` proof。正确顺序为：

```text
真实 statement -> simulated R_ved -> equivocable commitment -> YLH20 DDH malformed ciphertext
-> S3 late key opening -> PECC post-barrier erasure
```

`R_ved` 的 simulated proof 只在 simulation CRS 下接受假 statement；simulation-soundness
用于限制攻击者产生新的无效公开 statement。该修正已同步理论稿 `19.113` 和思路稿
`28.108`，不改变固定委员会、移动腐化或 aggregate-only 范围。

### 2026-09-13（P54：YLH20 `H3 -> H4 -> H5` lifting lemma）

把单 generation 的核心步骤隔离为条件 lemma：在 simulated `R_ved` 和 equivocable
commitment 已完成后，YLH20 的逐 endpoint/bit DDH hybrid 不需要隐藏 Shamir 常数，代价为
`O(|P| L_Q) * Adv_DDH`。随后 `S3` 按开启 payload 调整 binary branch 和共享 field
component，保持 public-key equation 并解密 malformed ciphertext。

该归约依赖三个条件：`SimProve` 可为 false statement 生成 accepting proof；公开 proof
不因腐化重发；不存在对 malformed ciphertext 的 public decryption 或 complaint edge。
P54 已同步理论稿 `19.114`、思路稿 `28.107` 和对应 lifting lemma。严格任意外部公钥及无界 key
reuse 继续排除在该候选外。

### 2026-09-13（P55：主文初稿抽取与三项主定理对齐）

完成主文结构瘦身。新增 `privacy-finality-main-paper-draft.md`，按“异步 FL
生命周期 -> privacy finality -> recovery-closure -> 协议语义 -> 条件实现
定理 -> FL 评价”组织全文。

主文只保留三项核心结果：技术稿 Theorem 44 的 closure-aware retirement
criterion、Proposition 22 的 recovery-state localization separation，以及
Theorem 42 的 `F_PF^mob` conditional realization。`PVOD`、`CSO-VE`、
`KeyOrigin`、`PECC` 和逐步 hybrid 降为 AOR/密码学实例化层；主文不再把
它们写成独立贡献，也不把条件接口包装成已完成的具体构造。

### 2026-09-13（P57：撤回完整初稿，转为引言与方案思路）

根据篇幅和论文定位要求，撤回先前生成的完整主文初稿，不把它作为当前
写作交付物。新增思路稿“引言思路与方案总览”：用六段引言路线说明异步
FL、长期恢复攻击、`CC_sid`/`PF_sid` 区分和三项结果；用四步生命周期给出
`D_sid`、aggregate-only opening、state-complete retirement、live-state-only
recovery 的方案语义。

正文证明预算固定为三个单元：closure-aware criterion、recovery-state
localization separation、conditional realization。安全性证明的逐代 hybrid
和底层密码学组件不再提前写入主文，只有最终闭合的实例化才进入附录。

### 2026-09-13（P59：anti-defensive-writing 与 ARS 风格审计）

检查思路稿新版引言和方案区块。主线已采用正向发布式结构：异步 FL 场景、
现有 SA 的基础、长期运行场景、核心问题、两个递进 challenge/solution、
贡献和方案总览。描述以适用范围、机制和结果组织，数学中的补集关系与
必要性命题保留为形式化表达；过程性复盘和逐项自我削弱句式归入历史素材。

方案区块已包含 `D_sid`、`CC_sid`、`PF_sid`、`z_u`、`K_sid`、`Y_sid`、
`E_sid(B,A_sid)`、`R_sid=emptyset`、整体四阶段伪代码和正文证明预算，
满足当前思路稿阶段的表达要求。完整正文写作继续延后。

### 2026-09-13（P60：OSDI 应用叙事重排）

按 OSDI 系统论文的写法重排思路稿开头。Challenge 1 改为异步训练窗口的
可执行封存点：窗口大小、迟到更新、重复提交和缓冲区处理共同决定训练吞吐
与单项更新的保留时间，并明确 FedBuff、Buffalo 与 ACS/共识各自覆盖的范围。
对应方案把 `CC_sid` 与 `PF_sid` 绑定到同一训练窗口，令已输出的模型更新获得
明确的 privacy frontier。

Challenge 2 改为故障恢复对已封存训练窗口的历史状态引用。对应方案用
`Recovery-Closure` 统合 direct share、修复份额、transcript、信道状态和交接
状态，并把运行路径重写为 `Accept -> Aggregate -> Seal -> Repair`。伪代码
改用训练窗口、模型输出、状态封存和 live-state repair 等系统动作，避免把
DyCAPS 的 handoff 流程直接移植为本文协议。

同步更新 `privacy-finality-manuscript-structure.md`：主文定位为 OSDI 导向的
异步 FL 系统论文，要求明确模型服务器、委员会、客户端与恢复路径，并以客户
端纳入/陈旧度、输出与封存延迟、故障恢复延迟、状态/通信代价和模型质量作为
系统证据。正文仍保持三个理论单元，详细密码学证明进入附录。

### 2026-09-13（P61：humanizer 审校与下一步收敛）

对当前思路稿的引言与方案区块进行 humanizer 审校。删去“数据面、控制面、
状态面、事件语义”等容易把论文写成系统设计说明的词，改用训练窗口、模型
输出、状态封存和故障修复来描述同一条研究主线。Challenge 1 现在从窗口大小、
迟到更新和训练吞吐出发，Challenge 2 由此自然进入封存后的历史状态引用。

下一步先冻结系统模型和攻击轨迹，不扩展密码学组件。具体写清客户端更新何时
进入窗口、何时生成模型输出、哪些迟到消息仍可处理、委员会在何处完成封存，
以及移动敌手如何通过后续修复尝试打开历史更新。随后用这一条轨迹校验
privacy-finality 定义、Recovery-Closure 条件和三项主文定理之间的对应关系。
这一步完成后，再选择最小的可实现密码学接口并接入外部设备的实验结果。

### 2026-09-13（P62：冻结系统模型与 delayed-repair 轨迹）

依据现有模拟器的参数和事件顺序，冻结论文的首个系统模型：固定委员会
`n=3f+2`，`q_dec=q_rec=2f+1`，网络完全异步，敌手保持 `f` 个同时腐化节点并
允许长期移动读取。一次训练窗口依次经历 `t_in <= t_cc <= t_out <= t_seal`，
其中 `t_out` 发布模型更新，`t_seal` 发布 `PF_sid`。

冻结 canonical delayed-repair attack：修复材料在模型输出前发送，部分消息在
封存后到达；普通恢复路径安装旧 generation，敌手再跨时间读取节点状态并形成
`Gamma_dec^cap(sid)` 的授权能力集合。方案在同一轨迹中先吸收 frontier，再只
生成 live state，使 `R_sid=emptyset` 成为可检验的协议条件。

下一步交付物是把这条轨迹分别写成 privacy-finality 定义、Recovery-Closure
判据和条件实现定理的前提与结论。证明先围绕固定委员会完成，动态委员会与
具体密码学组件继续保持在后续扩展位置。

### 2026-09-13（P64：完成固定委员会主文定义）

完成思路稿第 8 节的正式化。`CC_sid` 现在固定 computation finality，
`E_sid(B_sid,A_sid)` 通过 `Cl_rec` 统一描述历史暴露、封存后残留旧能力和迟到
修复边，`PF_sid` 的能力层判据明确为闭包避开 `Gamma_dec^cap(sid)` 的所有
授权集合。

三项主文结果与技术稿完成对应：主文定理 1 对应 Theorem 44，主文命题 2 对应
Proposition 22，主文定理 3 对应 Theorem 42。新增内容保留了 aggregate-only
transcript security 这一组合前提，并把 `R_sid=emptyset` 写成 live-state
repair 的结果条件，而不是单独的密码学假设。

下一步检查三个结果在固定委员会参数 `n=3f+2`、`q_dec=q_rec=2f+1` 下的证明
细节，重点核对 `A_sid in H_b(Gamma_dec)`、移动腐化预算和恢复活性之间是否
存在额外条件。该检查完成后再决定最小密码学实例化。

### 2026-09-13（P65：固定参数边界审计）

完成固定委员会参数审计。对 `q`-out-of-`n` 访问结构，封存前暴露预算为 `b`
时，安全所需的最小封存集合为

```text
tau_b(Gamma_q) = n - q + b + 1.
```

因此在 `n=3f+2`、`q_dec=q_rec=2f+1`、`b=f` 下，
`tau_b=2f+2=n-f`。这组参数可行，但封存证书处在活性紧边界：最坏情况下必须
等待所有正确节点完成封存。`n=3f+2` 的另一项作用独立于 privacy finality，
即排除 repair target 后，剩余 `3f+1` 个节点中仍有 `2f+1` 个正确 helper。

已将这两个参数作用写入思路稿第 7 节和第 8.6 节。后续证明必须分别核对
`|A_sid|>=2f+2` 的封存证书条件与每次 live repair 的 `2f+1` 个共同 helper，
不能用 repair liveness 代替 privacy finality，也不能把 `q_rec` 直接当作封存
集合规模。

### 2026-09-13（P66：封存协议与移动暴露预算）

完成 `Seal` 条件审计。长期移动敌手可以跨训练窗口移动，但对目标 `sid` 在
`t_seal` 前能够永久保留的旧 capability 必须有预算 `b`，首个参数点取 `b=f`。
封存证书集合 `A_sid` 与暴露集合 `B_sid` 分工明确：正确确认者先完成原子清除，
Byzantine 虚假确认的旧能力计入 `B_sid`，安全条件仍写为
`|A_sid|>=n-f` 且 `A_sid in H_b(Gamma_dec)`。

新增封存协议条件：节点先记录待封存标记，再清除 `sid` 局部材料，最后确认；
封存中途崩溃时，恢复先完成待封存记录，再处理旧修复消息。`PF_sid` 收集至少
`2f+2` 个确认，live repair 则独立使用 target-excluded 的 `2f+1` 个共同
helper。这样固定参数下的隐私安全、封存活性和修复活性各有明确证明前提。

下一步检查移动腐化预算 `b` 与现有 generation-local 模型的关系，特别是同一
客户端更新跨越 `t_out`、`t_seal` 和后续 repair 时，哪些读取应计入 `B_sid`，
哪些只属于当前 live state。完成后再写正式的 `Privacy-Finality` 安全游戏。

### 2026-09-13（P67：完成移动暴露预算记账）

完成 `b` 与 generation-local 模型的对齐。`b` 现在明确表示目标 `sid` 在
`t_seal` 前被敌手永久保留的旧 capability 预算；它允许敌手跨训练窗口移动，
但不构成全局腐化上限，也不引入任意解密查询。`t_out` 后、`t_seal` 前的读取
仍计入 `B_sid`，因为模型输出已经发生而旧 capability 尚未封存。

`t_seal` 后到达的旧修复消息归入 `R_sid` 或对应的 `Cl_rec` 恢复边；当前
generation 的 live state 通过坐标和 generation 标签单独记账。思路稿新增
`B_sid` 记账表，并把模拟器的 `retained_capabilities`、`post_finality_openings`
和 `stale_repair_accepts` 对应到预算、闭包扩张和迟到恢复边。

至此，固定委员会的安全参数和敌手视图已经闭合。下一步写正式的
`Privacy-Finality` 安全游戏，明确挑战更新、聚合输出、封存证书、未来状态暴露
和最终区分事件；该游戏继续使用合法协议操作，不引入自适应查询接口。

### 2026-09-13（P68：完成主文版 `Privacy-Finality` 安全游戏）

在思路稿第 8.9 节加入选择性的单描述符安全游戏。挑战者选择两组诚实客户端
更新 `X_0,X_1`，要求授权加权聚合相同；挑战者生成同一授权描述符、共同模型输出
和共同封存语义。实现中若 `CC_sid` 含有 ciphertext digest，则该摘要进入
`DataView_beta`，由 `Joint-AO^mob` 处理，而不是错误地要求两个世界逐字相同。

挑战后敌手只执行真实协议允许的 `Corrupt/Release/Publish/Process/Recover/Retire`
和最终当前状态暴露。瞬时腐化保持不超过 `f`，目标窗口封存前永久保留的旧能力
保持 `|B_sid|<=b`；发送时已经暴露的 key/point 立即计入历史集合，迟到修复边
进入 `R_sid` 和 `Cl_rec`。游戏不提供任意解密 oracle，也不通过操作准入预先排除
会破坏安全性的恢复结果。

最终视图分为 `DataView_beta`、`StateView`、`PublicContext` 和 `X_hist`。安全目标
同时包含 `PF_sid` 后不存在 `OpenOne(sid)`，以及相同授权聚合的两个世界在完整
长期视图下不可区分。主文优势界与既有 Theorem 44/42 对齐：

```text
Adv_Privacy-Finality
  <= Adv_RCL-Sim/AO
     + Adv_Joint-AO^mob
     + Adv_Context/Correctness
     + Adv_Uncovered-Edge
     + negl(lambda).
```

动态委员会暂不进入首版固定委员会实验；未来成员交接统一作为带
`sid/generation/frontier` 标签的 `Cl_rec` 恢复边处理。只有交接不能生成已封存
窗口的旧能力时，动态扩展才复用同一个安全游戏。

### 2026-09-13（P69：重新确立 OSDI 的系统论文重心）

重新审视当前稿件后，确认前几轮把 `Privacy-Finality` 安全游戏、
`Joint-AO^mob` 和恢复闭包证明推进得过深，主线逐渐接近密码学论文。首版
应把异步 FL 服务的完整性放在前面：客户端如何进入窗口，服务器何时推进模型，
委员会如何完成聚合和封存，迟到更新如何处理，节点崩溃后如何恢复，以及这些
选择对陈旧度、延迟、通信、持久状态和模型质量的影响。

新的主文顺序是：服务目标与故障场景 -> 系统模型 -> 端到端协议设计 -> 实现
细节 -> 安全模型与一项条件端到端定理 -> FL 评估。安全性保留三个必要对象：
`CC_sid` 说明模型推进使用了哪些客户端，`PF_sid` 说明窗口何时完成隐私封存，
`Recovery-Closure` 说明后续恢复不能重新生成旧能力；它们服务于系统保证，
不再作为引言的主要结构。

思路稿新增“系统设计与实现蓝图”，要求后续实现章节具体交代客户端/模型服务器、
聚合委员会、封存与迟到处理、崩溃恢复四条路径。评估重点从“是否满足安全游戏”
扩展为客户端纳入率、更新陈旧度、模型推进延迟、封存延迟、恢复延迟、通信与
持久状态成本、模型质量，以及同一 delayed-repair 故障轨迹下的服务行为。

因此后续工作不再新增安全接口或优势项。下一步应细化系统 API、数据结构、故障
处理和基线集成，再用已有安全定义检查这些设计选择是否满足 privacy finality。

### 2026-09-13（P63：完成模型冻结，进入定理对齐）

系统模型和 canonical delayed-repair 轨迹已经写入思路稿第 7 节，包含参与者、
时间顺序、异步消息、移动腐化、门限和固定委员会参数。攻击轨迹把普通恢复路径
安装迟到旧状态作为基线，把 frontier 先行吸收和 live-state repair 作为方案
行为；两者共享同一条消息调度和后续状态暴露过程。

当前工作从“寻找新的密码学组件”转为“让一个攻击轨迹支撑三个理论结论”：
`t_out` 对应 computation finality，`t_seal` 对应 privacy finality，迟到修复
边进入 `Recovery-Closure`。下一步写出正式的前提、挑战者视图和定理结论，先
完成固定委员会版本，再把动态委员会作为同一判据的扩展。

### 2026-09-13（P58：重排引言路线并补齐方案表达）

按“前三段背景与攻击 -> 核心问题 -> Challenge 1/Solution 1 -> Challenge
2/Solution 2 -> Our Contributions”的顺序重写思路稿开头。两项 challenge
形成递进关系：第一项处理异步输出与隐私终结的事件语义，第二项处理退休后
恢复活性与历史 capability 生命周期的冲突。

在同一节补充整体方案概述、`D_sid`/`CC_sid`/`PF_sid` 生命周期公式、短种子
aggregate-only 数据面公式、四阶段协议伪代码，以及正文三单元证明预算。旧
版引言与方案保留为素材档案并明确降级，当前写作只依据新版路线。

## References

- Wang, Yang, Li. *Buffered Asynchronous Secure Aggregation for Cross-Device Federated Learning*. arXiv:2406.03516.
- Taiello, Gritti, Önen, Lorenzi. *Buffalo: A Practical Secure Aggregation Protocol for Buffered Asynchronous Federated Learning*. CODASPY 2025. DOI:10.1145/3714393.3726498.
- Del Pozzo et al. *Privacy-Preserving Federated Averaging with Byzantine Aggregators in Asynchronous Networks*. arXiv:2601.04930.
- Ortega, Jafarkhani. *Quantized and Asynchronous Federated Learning*. arXiv:2410.00242.
- Iakovidou, Kim. *Asynchronous Federated Stochastic Optimization for Heterogeneous Objectives Under Arbitrary Delays*. arXiv:2405.10123.
- Günther, Das, Kokoris-Kogias. *Practical Asynchronous Proactive Secret Sharing and Key Refresh*. ePrint 2022/1586. 本地：`/home/yzc/flagg/apss_keyrefresh_2022_1586.txt`。
- Zhou. *NFSA: Non-Forward Secure Aggregation with One Server via Two-Layer Secret Sharing*. CCS 2026. 本地：`/home/yzc/flagg/Non-Forward Secure Aggregation via Two-Layer SS_by_PaddleOCR.md`。
- *When Secure Aggregation Falls Short: Achieving Long-Term Privacy in Asynchronous Federated Learning for LEO Satellite Networks*. 本地：`/home/yzc/flagg/Achieving Long-Term Privacy_by_PaddleOCR.md`。
- *Robust and Efficient Multi-Round Single-Mask Secure Aggregation Against Malicious Participants* (Aion). 本地：`/home/yzc/flagg/Robust and Efficient Multi-Round Single-Mask Secure Aggregation Against Malicious Participants_by_PaddleOCR.md`。
- Yurek, Luo, Fairoze, Kate, Miller. *hbACSS: How to Robustly Share Many Secrets*. 本地：`/home/yzc/flagg/extract_hbACSS.txt`；代码：`https://github.com/tyurek/hbACSS`。
- Alhaddad, Varia, Yang. *Haven++: Batched and Packed Dual-Threshold Asynchronous Complete Secret Sharing with Applications*. 本地：`/home/yzc/flagg/extract_Batched_and_Packed_Dual-Threshold_ACSS.txt`；代码：`https://github.com/nicolas3355/AMPC`。
- Alexandru, Blum, Katz, Loss. *State Machine Replication under Changing Network Conditions*. 2022. 本地文本：`/tmp/changing-network-conditions.txt`。
- Hu, Zhang, Chen, Zhou, Jiang, Liu. *DyCAPS: Asynchronous Dynamic-committee Proactive Secret Sharing*. 本地：`/home/yzc/flagg/dycaps_2022_1169.txt`。
- Yan, Xia, Devadas. *Shanrang: Fully Asynchronous Proactive Secret Sharing with Dynamic Committees*. ePrint 2022/164. 本地：`/home/yzc/flagg/shanrang_2022_164.txt`。
- Hu, Liu, Lu, Tang, Xiang, Zhang. *Optimistic Asynchronous Dynamic-committee Proactive Secret Sharing*. ePrint 2025/880; IEEE S&P 2026. 本地：`/home/yzc/flagg/optimistic_dpss_2025_880.txt`。
- *Flamingo: Multi-Round Single-Server Secure Aggregation with Applications to Private Federated Learning*. 腐化模型核对文本：`/tmp/flamingo.txt`。
- Bacho, Chen, Loss. *Adaptively Secure (Aggregatable) PVSS from Standard Assumptions*. ePrint 2026/1100. 本地文本：`/tmp/apvss-2026-1100.txt`。
- Das, Ren, Yang. *Adaptively Secure Threshold ElGamal Decryption from DDH*. ePrint 2025/1477. 本地文本：`/tmp/adaptive-elgamal-2025-1477.txt`。
- Shoup. *Back to the Future: Simple Threshold Decryption Secure against Adaptive Corruptions*. IACR Communications in Cryptology, 2026. DOI: `10.62056/anxrxruc2`。本地文本：`/tmp/adaptive-threshold-decryption.txt`。
- Libert, Yung. *Adaptively Secure Forward-Secure Non-interactive Threshold Cryptosystems*. Inscrypt 2011 / LNCS 7537, 2012. DOI: `10.1007/978-3-642-34704-7_1`。本地文本：`/tmp/libert-yung-forward-threshold.txt`。
- Green, Miers. *Forward Secure Asynchronous Messaging from Puncturable Encryption*. IEEE S&P 2015. DOI: `10.1109/SP.2015.26`。
- Susilo, Duong, Le, Pieprzyk. *Puncturable Encryption: A Generic Construction from Delegatable Fully Key-Homomorphic Encryption*. 2020. DOI: `10.1007/978-3-030-59013-0_6`。
- Shen, Chi, Lin. *Puncturable Fully Homomorphic Encryption Based on Bloom Filter*. PeerJ Computer Science, 2026. DOI: `10.7717/peerj-cs.3675`。
- *Dynamic Puncturable Encryption*. ACNS 2026, LNCS 16571. DOI: `10.1007/978-3-032-32560-0_4`。本地：`/tmp/dynamic-puncturable-encryption-2026.txt`；覆盖动态访问撤销/恢复/委托，不覆盖阈值聚合或长期移动腐化。
- Agarwal, Babel, Das, Gilakaye, Mondal, Pinkas, Rindal, Yadav. *Weighted Batched Threshold Encryption With Applications to Mempool Privacy*. IEEE S&P 2026; ePrint `2025/2115`. DOI: `10.1109/SP63933.2026.00175`。已核对原文：逐条输出选中批次消息，静态按权重腐化、广播输入、固定索引/setup；不覆盖 aggregate-only、per-`sid` 退休和未来全体状态暴露。
- Madathil, Lazzaretti, Liu, Papamanthou. *TACITA: Threshold Aggregation without Client Interaction*. ePrint 2025/1579。本地：`/tmp/tacita-2025-1579.txt`。
- Choudhuri, Garg, Policharla, Wang. *Practical Mempool Privacy via One-time Setup Batched Threshold Encryption*. USENIX Security 2025。本地：`usenixsecurity25-choudhuri.pdf_by_PaddleOCR-VL-1.6.md:211`，提供 `Setup(crs,td)`、`Prove`、`Verify`、`SimProve` 接口；本文仍需补 dual-mode 和 `R_eq` 实例化条件。
- Baecker, Gerhart, Jarecki, Nazarian, Rausch, Schröder. *Adaptive Distributed Key Generation for Discrete-Log Cryptosystems*. 本地：`/home/yzc/flagg/adaptive_dkg_2026_892.txt`。Janus 的 adaptive commitment/encryption/erasure 可作为 AC1--AC3 参考，但不提供 FGSR frontier、退休 recovery closure 或 aggregate-only `Joint-AO`。
- Hazay, Patra, Warinschi. *Selective Opening Security for Receivers*. ASIACRYPT 2015 extended version. 本地：`/tmp/hpw15.txt`。提供 receiver-key selective opening、`rind-so`/`rsim-so` 与 NCER 关系；不直接覆盖外部预注册公钥、相关 Shamir witness 与 `R_ved` 联合模拟。
- Pan, Wagner, Zeng. *Generic Constructions of Compact and Tightly Selective-Opening Secure Public-key Encryption Schemes*. ASIACRYPT 2022 / ePrint 2023/1321. 本地：`/tmp/pan-sim-so-cca.txt`。提供 sender-side `SIM-SO-CCA`，其 opening 暴露 plaintext 与 encryption randomness，不是本文需要的 receiver-key opening。
- Yang, Lai, Huang, Au, Xu, Susilo. *Possibility and Impossibility Results for Receiver Selective Opening Secure PKE in the Multi-challenge Setting*. ASIACRYPT 2020. 本地：`/tmp/ylh20.txt`。提供 `SIM-RSO_k-CPA` 与 DDH-based malformed-ciphertext/key-opening 构造；可作为协议管理 key registration 下的 `KeyOrigin` 候选，但不直接覆盖任意外部公钥、相关 Shamir witness 或 `R_ved`/`PECC` 联合模拟。
- Bormet, Choudhuri, Faust, Garg, Othman, Policharla, Qu, Wang. *BEAST-MEV: Batched Threshold Encryption with Silent Setup for MEV Prevention*. ePrint 2025/1419。本地：`/tmp/beast-mev-2025-1419.txt`。
- Oh, Kim, Oh. *LightBEAT: Scalable Epochless Batched Threshold Encryption via Hierarchical Identity-Based Puncturing*. IEEE Access 14 (2026), 68054--68075. DOI: `10.1109/ACCESS.2026.3689882`。全文已核：静态委员会，客户端 HIDP puncture，逐条输出批消息，无 committee-state repair。
- Basu, Tomescu, Abraham, Malkhi, Reiter, Sirer. *Efficient Verifiable Secret Sharing with Share Recovery in BFT Protocols*. ACM CCS 2019. DOI: `10.1145/3319535.3354207`。VSSR 可作恢复基线，但不是 proactive/mobile retirement protocol。
- Jovanovic, Komatovic, Maffei. *Threshold Encryption with Silent Setup*. 2025 manuscript。FSE/PCS 扩展依赖周期更新或公开键材料更新。
- Karthikeyan, Polychroniadou. *One-shot Private Aggregation with Single Client Interaction*. 2024 preprint. 本地文本：`/home/yzc/flagg/extract_One-shot_Private_Aggregation_with_Single_Client_Interaction.txt`。
