# Repair-Closure Characterization

## Formal Definitions, Proof Draft, and Protocol Consequences

> 状态：第一版正式定理稿。  
> 目标：严格区分抽象可达性定理、密码学组合定理和具体 RCL 构造义务。  
> 目标会话：固定一个已经形成 `PF_sid` 的 `sid`，不引入 adaptive-query 历史。

## Role in the Manuscript

本文件是论文的技术附录和定理素材库，不是主文的章节顺序。主文只抽取
以下三组结果：

1. `Privacy-Finality Characterization`：聚合描述符已经确定后，隐私终结
   还需要对未来可达 capability 做闭包约束；
2. `Recovery-State Localization Barrier`：普通恢复状态若仍能与全局恢复
   权组合生成退休 capability，则 future exposure 会复活历史更新；
3. `Conditional FGSR Instantiation`：在 opaque delivery、frontier binding、
   atomic erasure 和 aggregate-only data plane 条件下，协议满足异步 FL 的
   privacy finality、正确性与活性。

其余 typed capability、逐代 hybrid、`PVOD`/`CSO-VE`、`KeyOrigin`、`PECC`
和优势项展开只服务于上述结果。它们应在主文中压缩为接口表和证明路线，
完整证明保留在附录。任何没有产生 FL 生命周期结论的技术引理，不应在主文
中单独包装为贡献。

主文记号 `E_sid(B,A_sid)` 与本稿 `E_c(B,A)` 同义；主文的 `R_sid` 是
本稿 `R_c` 的 capability 集合版本，而不是委员会身份集合。主文 Theorem 1
只抽取 Theorem 44 的 closure criterion，主文 Proposition 2 抽取
Proposition 22，主文 Theorem 3 抽取 Theorem 42。其余编号仍属于技术稿，
不应在主文中形成第二套竞争性的定理层级。

## 0. 本轮结论

`Repair-Closure Characterization` 可以写成一个精确的可达性定理，但必须避免两个过强表述：

1. 闭包条件本身刻画的是**旧解密 capability 是否可重构**；要推出客户端更新不可区分，还需要 aggregate-only 数据面的模拟安全。
2. `CheckInstall` 只能阻止正确节点采用陈旧状态，不能自动阻止攻击者从恢复贡献或归档 transcript 中提取旧 share。所有“生成、传输、解封、安装”旧 capability 的路径都必须进入闭包。

因此，正式结果分为两层：

```text
Layer 1: Capability Reachability
    adversarially obtainable capabilities
    = closure of initially exposed capabilities under legal derivations.

Layer 2: Privacy-Finality Composition
    closure avoids every decryption access set
    + aggregate-only transcript security
    => post-finality individual-update privacy.
```

第二层才是最终论文中的 secure aggregation 定理。

## 1. 固定执行前缀

固定安全参数 `lambda`、目标会话 `sid*` 和一个多项式长度的协议执行前缀 `rho`。在 `rho` 中：

- `CC_sid*` 已固定唯一聚合描述符 `D_sid*`；
- `PF_sid*` 已形成；
- 节点随后可以 crash、cure、repair 或换届；
- 攻击者可以继续移动腐化，并最终获得所有节点的当前状态；
- 攻击者永久保留此前读取到的所有 bitstrings。

先证明固定委员会版本。动态委员会只是在同一个能力图中加入 configuration-indexed capability 和 handoff edge。

选择多项式执行前缀并不限制长期叙事：任意 PPT 攻击者只能在多项式时间内观察有限事件。定理对每个这样的前缀成立，即可用于标准计算安全游戏。

## 2. Typed Capability Universe

### 2.1 能力不是节点身份

对目标会话 `sid*`，定义有限 typed capability universe：

```text
C = C_dec
    union C_share
    union C_rp
    union C_dprf
    union C_backup
    union C_transcript
    union C_channel
    union C_handoff
    union C_state.
```

其中：

- `C_dec`：可以直接参与打开 `sid*` 归档 ciphertext 的部分解密能力；
- `C_share`：能参与线性 repair 的当前或历史 secret shares；
- `C_rp`：VSSR-style recovery-polynomial shares 或等价局部恢复材料；
- `C_dprf`：DPRF secret shares、有效 contribution capability 或可验证派生能力；
- `C_backup`：持久备份 ciphertext、封装 key 或恢复 commitment；
- `C_transcript`：已生成并可归档的 recovery messages、partial decryptions 和证明；
- `C_channel`：能够解封历史私密消息的 channel/receiver secret；
- `C_handoff`：跨配置转换输出与 handoff certificate；
- `C_state`：带 frontier/version 的可安装功能状态。

每个 capability 是一个抽象原子，表示攻击者拥有足够信息执行某种密码学操作。不同类型不能因为属于同一节点而合并计数。

### 2.2 为什么 transcript 必须是 capability

假设恢复贡献 `mu_{j->i}` 在 `PF_sid*` 前已经生成，但网络将其延迟到 `PF_sid*` 后。即使节点 `i` 的 `CheckInstall` 拒绝该输出，攻击者仍可能：

- 直接从公开 contribution 重构目标旧 share；
- 在未来腐化 `i` 后获得接收者长期解密 key，解封归档 contribution；
- 将 contribution 与其他历史恢复消息离线组合；
- 把 contribution 交给另一个不执行正确安装检查的 Byzantine 节点。

因此，安全对象不是“正确节点最终安装了什么”，而是“攻击者最终能够计算出什么”。只要历史 transcript 与未来状态可以导出旧 share，就必须存在一条 derivation edge。

## 3. Initial Exposure Family

对执行前缀 `rho` 和一个满足会话生命周期腐化预算的调度 `B`，定义：

```text
X_0(rho,B)
    = X_pub(rho)
      union X_hist(rho,B)
      union X_cur(rho)
      union X_adv(rho,B).
```

- `X_pub(rho)`：公开 transcript 中本身构成能力的对象；
- `X_hist(rho,B)`：攻击者在 `PF_sid*` 前腐化节点时保存的历史能力；
- `X_cur(rho)`：`PF_sid*` 后最终全体当前状态暴露获得的能力；
- `X_adv(rho,B)`：Byzantine 节点自行保留、复制或生成的合法能力。

所有符合敌手模型的初始集合构成 family：

```text
I_sid* = {X_0(rho,B) : B is admissible for sid*}.
```

使用 `I_sid*` 而不是只用一个节点集合 `B` 有两个好处：

1. 它能表达一次腐化同时泄漏 direct share、DPRF share、pending recovery state 和 channel key；
2. 它允许协议通过原子擦除改变 `X_cur`，而不是假设未来腐化总会得到节点曾经拥有的全部历史状态。

## 4. Legal Derivation Hypergraph

### 4.1 Hyperedge

一条有向超边写为：

```text
e = (U -> c),
```

其中 `U subseteq C`，`c in C`。它表示给定 `U` 中全部能力和公开参数，存在一个 PPT 算法或协议调度，能够以非忽略概率得到 `c`。

典型边包括：

```text
q_dec partial capabilities -> plaintext-opening capability
q_rec current shares -> repaired current share
recovery-polynomial shares + DPRF contributions -> old target share
backup ciphertext + recovery-authority shares -> old target share
archived encrypted contribution + receiver channel key -> old target share
old-config projected shares + handoff certificate -> new-config share.
```

### 4.2 Frontier-sensitive edge

边必须包含版本和 frontier 条件。消息

```text
mu(rid, target, cfg, T_req)
```

与另一个 `T_req'` 下的消息是不同 capability。只有协议在 `PF_sid*` 后仍允许生成、解封或利用的边才进入 post-finality edge set `E_sid*`。

若 helper 已知 `T >= Retired(sid*)` 后必须拒绝旧坐标，则不存在从该 helper 当前 state 到旧 contribution 的边。若旧 contribution 已经在退休前生成并被归档，则它作为 `C_transcript` 中的初始能力进入 `X_pub` 或 `X_hist`；不能通过删除生成边把已经存在的 transcript 从模型中抹去。

### 4.3 Monotone adversarial knowledge

攻击者可以复制所有已知 bitstrings，所以其知识单调增长。协议中的本地状态可以被删除，但攻击者已经获得的能力不会被消费。即使真实恢复协议使用 one-time nonce，也可以把 nonce、版本和实例标识编码到 capability 类型中，使攻击者知识仍由单调闭包表示。

## 5. Recovery Closure

定义算子：

```text
F_E(Y) = Y union {c : exists (U -> c) in E with U subseteq Y}.
```

从 `X` 出发迭代：

```text
Cl_E^0(X) = X,
Cl_E^{r+1}(X) = F_E(Cl_E^r(X)),
Cl_E(X) = union_{r >= 0} Cl_E^r(X).
```

因为 `C` 对固定多项式执行前缀是有限的，迭代至多 `|C|` 次达到最小不动点。下文记：

```text
Cl_rec(X) := Cl_E_sid*(X).
```

闭包满足标准 closure operator 性质：

```text
Extensive:  X subseteq Cl_rec(X)
Monotone:   X subseteq Y implies Cl_rec(X) subseteq Cl_rec(Y)
Idempotent: Cl_rec(Cl_rec(X)) = Cl_rec(X).
```

## 6. Decryption Access Structure

令：

```text
Gamma_dec^cap(sid*) subseteq 2^C
```

为足以打开 `sid*` 单项 ciphertext 或恢复目标客户端 mask key 的最小 capability 集合族。可以只保留 inclusion-minimal authorized sets；其向上闭包给出完整单调访问结构。

定义 capability safety：

```text
CapSafe(sid*) iff
    for every X in I_sid*,
    for every D in Gamma_dec^cap(sid*),
    D is not a subset of Cl_rec(X).
```

`CapSafe` 只声明攻击者不能形成授权旧解密能力，不直接声明 challenge updates 不可区分。

## 7. 抽象正确性假设

### A1. Derivation Soundness

对任意攻击者执行历史，若下一步新获得相关 capability `c`，且 `c` 不属于该执行的 base exposure，则除可忽略概率外，存在一条 `(U->c) in E_sid*`，其全部前件 `U` 在获得 `c` 之前已经由攻击者掌握。

这是局部 one-step 条件，不预先假设全局闭包结论。它要求所有合法生成路径都被 edge set 覆盖，并由底层签名、VSS binding、NIZK soundness、channel security 和 threshold unforgeability 排除未建模伪造。

### A2. Composable Edge Realizability

对任意已经可达的攻击执行历史和一条 `(U->c) in E_sid*`，若攻击者已获得 `U`，则存在一个符合网络和腐化模型的 PPT 调度扩展获得 `c`，并且不撤销此前获得的 capability。该扩展要么以 overwhelming probability 成功，要么可被高效重复直至成功。

该条件用于必要性和 matching attack。它要求 edge 可从任意满足前件的可达历史继续实现，因而强于从初始化状态分别实现每条边：两个 recovery edges 可能竞争同一个不可复制的一次性协议状态，分别可执行但不能在同一执行中联合完成。若 edge set 只是保守 over-approximation，或不同 edges 不能连续实现，则闭包条件仍是充分条件，但不再是必要条件。

### A3. Decoder Adequacy

若攻击者能从归档 transcript 恢复目标单项 mask key 或更新，则除可忽略概率外，它要么：

1. 获得某个 `D in Gamma_dec^cap(sid*)`；
2. 破坏底层 aggregate-only encryption、PRG、commitment 或 proof system。

### A4. Transcript Completeness

凡是已经生成且可能被攻击者保存的恢复、解密、channel 或 handoff transcript，都包含在 `X_pub/X_hist` 或作为 derivation edge 的输出。安全证明不能只建模最终 installed state。

## 8. Capability Reachability Theorem

### Theorem 1: Sound Reachability

对任意 `X in I_sid*`，在 A1 下，PPT 攻击者在 `rho` 后获得的所有相关 capabilities 构成集合 `ViewCap_A(rho,X)`，满足：

```text
ViewCap_A(rho,X) subseteq Cl_rec(X)
```

除可忽略概率外成立。

#### Proof

按攻击者获得 capability 的事件顺序归纳。

基础情形：在 post-finality 执行开始时，攻击者已知的相关能力按定义全部属于 `X`，而 `X subseteq Cl_rec(X)`。

归纳步骤：假设前 `r` 个事件后攻击者已获得的全部能力都属于 `Cl_rec(X)`。第 `r+1` 个新能力 `c` 有两种来源：

1. `c` 是一次新腐化或公开交付直接暴露的能力。按 `I_sid*` 和 Transcript Completeness 的定义，它属于对应执行的初始暴露，或者该暴露由一条显式 corruption/delivery edge 表示。
2. `c` 由本地计算、recovery、解封、安装或 handoff 得到。由 Derivation Soundness，除可忽略概率外，存在 `(U->c) in E_sid*`，且每个 `u in U` 已在前 `r` 个事件中获得。由归纳假设 `U subseteq Cl_rec(X)`；闭包定义给出 `c in Cl_rec(X)`。

对多项式个事件取 union bound，失败概率仍可忽略。

### Theorem 2: Realizable Reachability

在 A2 下，对任意有限集合 `Z subseteq Cl_rec(X)`，存在一个符合模型的 PPT 调度，按闭包层级顺序以非忽略概率联合获得 `Z`。若所有 edge 的实现成功概率为 overwhelming，整个有限 derivation sequence 也以 overwhelming probability 成功。

#### Proof

对 `Z` 中所有 capabilities 取一个按 `rank_X(c)` 排序的有限 derivation DAG，其中 `rank_X(c)` 是使 `c in Cl_E^r(X)` 的最小 `r`。

- `rank=0` 时，`c in X`，攻击者初始已拥有。
- 对 `rank=r+1`，存在 `(U->c)`，且所有 `u in U` 的 rank 至多 `r`。按归纳假设先获得 `U`。Composable Edge Realizability 保证同一个调度可以继续执行该 edge，而不撤销此前获得的能力。

有限能力集合保证归纳终止。若多个 edge 共享一次性真实资源，需要在 capability 类型中区分实例并证明调度可组合；否则 A2 不成立，只能保留 Theorem 1 的充分方向。

## 9. Repair-Closure Characterization

### Theorem 3: Capability-Safety Characterization

在 A1 和 A2 下，以下命题等价：

1. 对每个 `X in I_sid*`，不存在符合模型的 PPT 攻击者使某个 `D in Gamma_dec^cap(sid*)` 满足 `D subseteq ViewCap_A(rho,X)`；
2. `CapSafe(sid*)` 成立，即

```text
for every X in I_sid*,
for every D in Gamma_dec^cap(sid*),
D is not a subset of Cl_rec(X).
```

#### Sufficiency

假设闭包条件成立，但存在攻击者获得某个授权集合 `D`。由 Theorem 1，除可忽略概率外，`D subseteq Cl_rec(X)`，与闭包条件矛盾。

#### Necessity

若闭包条件失败，则存在 `X in I_sid*` 和 `D in Gamma_dec^cap(sid*)` 满足 `D subseteq Cl_rec(X)`。由 Theorem 2，对 `D` 中每个 capability 按共同闭包层级执行 realizable derivations，即可获得完整 `D`。因为 `D` 是授权集合，攻击者可以打开目标旧 ciphertext。

### 定理边界

Theorem 3 的“当且仅当”依赖 A2。对只用于安全证明的 conservative closure，通常只有：

```text
closure-safe => capability-safe.
```

这是合理的工程用法：把所有可能恢复边纳入闭包，即使其中部分边不能同时触发，也不会错误接受不安全协议；只是可能拒绝实际安全的协议。

## 10. 从 Capability Safety 到 Privacy Finality

### Theorem 4: Composition Target

假设：

1. `CapSafe(sid*)` 成立；
2. 静态数据面满足 selective single-descriptor aggregate-only security：两组客户端输入在 `D_sid*` 下聚合相同，则授权输出和 transcript 可模拟；
3. 所有 recovery/handoff transcript 对未进入 `Cl_rec(X)` 的 secret capabilities 满足模拟安全；
4. `CC_sid*` 唯一绑定 `sid*、cfg、S、weights、H_ct、H_out`；
5. challenge 生命周期内的腐化满足 `I_sid*` 的 admissibility 条件。

则形成 `PF_sid*` 后，即使攻击者获得全部当前状态并继续调用所有合法 recovery/handoff 接口，也不能区分任意两组具有相同授权聚合的 challenge updates，除非破坏上述底层原语。

#### Proof Strategy

1. 固定任意 admissible `X`。
2. 由 Theorem 1，所有攻击者可获得的 secret capabilities 位于 `Cl_rec(X)`。
3. 由 `CapSafe`，该闭包不包含任何单项解密授权集合。
4. 使用 recovery/handoff transcript simulator 替换不泄漏 capability 的协议消息。
5. 调用 aggregate-only 数据面安全，把 challenge world 0 替换为 world 1；两世界的唯一授权聚合相同。
6. `CC_sid*` 的唯一性排除对同一 challenge ciphertext 使用另一个集合或权重产生第二个独立输出。

这一定理仍是组合目标。完整证明需要选定 `Static-AO` 与 RCL 实例后，逐项验证 transcript simulator 和并发状态转换。

## 11. Robust-Hitting 是无恢复特例

假设每个节点 `i in P` 对应一个直接旧解密 capability `d_i`，且退休后不存在生成新 `d_i` 的边。令：

```text
A subseteq P: effective retired nodes,
B subseteq P: nodes whose old d_i was saved before retirement,
|B| <= b.
```

未来全体当前状态暴露给出的 direct capability owners 是：

```text
X_B = (P - A) union B.
```

因为无恢复边，`Cl_rec(X_B)=X_B`。对单调节点访问结构 `Gamma_dec`，安全条件为：

```text
for every B with |B| <= b:
X_B notin Gamma_dec.
```

### Corollary 1: Robust-Hitting

上述条件等价于：

```text
for every D in Gamma_dec:
|D intersection A| > b.
```

#### Proof

若存在 `D in Gamma_dec` 且 `|D intersection A|<=b`，选择 `B=D intersection A`。于是：

```text
D subseteq (P-A) union B = X_B,
```

由访问结构单调性，`X_B` 授权，安全失败。

反之，若某个 `B` 使 `X_B` 授权，则取 `D=X_B`，有：

```text
D intersection A subseteq B,
```

所以 `|D intersection A|<=b`，与 Robust-Hitting 条件矛盾。

## 12. Threshold Repair Amplification

假设：

- `Gamma_dec` 是 `q_dec`-out-of-`n`；
- 任意 `q_rec` 个直接旧 share capabilities 可以恢复任意一个缺失旧 share；
- 新恢复 share 可以继续作为后续恢复 helper；
- 退休集合大小为 `a`；
- 攻击者在退休前最多保存 `b` 个节点的旧 share。

初始 direct share 数的最坏值是：

```text
x = n-a+min(a,b).
```

### Lemma 1: Homogeneous Repair Closure

```text
if x < q_rec:
    closure contains exactly the x initial direct shares;

if x >= q_rec:
    closure contains all n direct shares.
```

#### Proof

当 `x<q_rec` 时，没有任何恢复边的全部前件被满足，闭包不扩张。

当 `x>=q_rec` 时，从任意 `q_rec` 个已有 shares 可恢复第一个缺失 share。此后已有 share 数增加一，仍至少为 `q_rec`；重复该过程可恢复所有节点。

### Corollary 2: Effective Privacy Threshold

privacy finality 当且仅当：

```text
n-a+min(a,b) < min(q_dec,q_rec).
```

#### Proof

- 若 `x>=q_dec`，攻击者无需恢复即可解密。
- 若 `x>=q_rec`，由 Lemma 1 恢复全体 shares，随后解密。
- 若 `x<min(q_dec,q_rec)`，闭包不扩张且初始 shares 低于解密门限。

### Example: `n=4,f=1`

取 `q_dec=3`、退休确认 `a=3`、历史暴露 `b=1`。没有恢复时：

```text
x = 4-3+1 = 2 < 3,
```

所以 Robust-Hitting 安全。

若直接采用 `q_rec=f+1=2` 的恢复，则：

```text
x = 2 >= q_rec.
```

攻击者恢复第三个 share，立即达到 `q_dec=3`。因此，一个完全正确的低门限 share-recovery protocol 会击穿一个参数上原本安全的 retirement quorum。

## 13. VSSR Specialization

### 13.1 能力映射

对一个 VSSR commitment `c` 和目标 share owner `i`，相关能力至少包括：

```text
s_j:       original secret/share-polynomial contribution at helper j
rp_j,g:    helper j's share of recovery polynomial g
alpha_j:   helper j's DPRF secret share
mu_j->i:   generated recovery contribution
r,c:       public nonce and commitments
s_i:       recovered target share.
```

一个抽象恢复边为：

```text
{s_j, rp_j,g, alpha_j : j in R} union {r,c}
    -> {mu_j->i : j in R}
    -> s_i,

where |R| >= k.
```

具体实现中，第一步可能拆成每个 helper 的独立 contribution edge，第二步由目标节点组合。typed closure 可以保持这一差异。

### 13.2 VSSR 安全游戏与本文敌手的差异

VSSR 的 hiding definition 对每个 commitment 统计 compromise、direct contribution 和足够多 recovery queries 涉及的 oracle indices，并要求合法攻击者涉及的来源数 `<k`。这证明一次 sharing 在该累计界内隐藏。

本文允许长期移动腐化最终覆盖全体当前状态。因此，若 `c` 的 recovery-polynomial shares 和 DPRF shares 在退休后仍作为当前状态存在，初始 capability set 可能直接满足恢复边前件。这个执行不违反 VSSR 定义，因为它已经超出 VSSR 对该 commitment 的合法查询范围。

### 13.3 安全复用 VSSR 技术的条件

VSSR 只能按以下方式之一进入 RCL：

1. 对每个 retired coordinate，满足 Robust-Hitting 的节点原子删除 direct share、recovery-polynomial share 和 pending contribution；
2. DPRF contribution interface 在 helper 侧验证 frontier，并且不能为 retired coordinate 生成有效 contribution；
3. 已生成 contribution 使用 target-specific ephemeral encryption，receiver secret 在相关 retirement 前安全擦除；
4. `q_rec` 按长期 privacy 参数重新设置，使 repair amplification 不低于 `q_dec`；
5. 恢复只从当前 projected live shares 生成新 share，不保存能重建 pre-projection share 的 durable backup。

其中第 2 条不能只由软件分支实现：未来腐化将读取 DPRF secret share，并可绕过本地判断离线计算。如果同一个 `alpha_j` 能对任意 `(r,i,c)` 生成贡献，就必须依赖 coordinate-local recovery-polynomial state 已被删除，或让 DPRF/recovery authority 在密码学上按 coordinate 穿孔。

## 14. 新发现：Install Fence 不足

### Lemma 2: Contribution-Exposure

设 `M_old` 是 `PF_sid*` 前生成的恢复 transcript，`Z_future` 是未来当前状态暴露得到的能力。若存在 PPT 算法：

```text
Extract(M_old, Z_future) -> d_i(sid*),
```

则 capability graph 必须包含边：

```text
{M_old, Z_future} -> d_i(sid*).
```

即使所有正确节点都拒绝安装 `d_i(sid*)`，只要 `M_old` 可被保存且 `Z_future` 最终暴露，`d_i(sid*)` 仍属于攻击者闭包。

#### Consequence

仅有以下检查不够：

```text
CheckInstall(T_local,T_req,recovered_state) = reject if T_req < T_local.
```

RCL 必须同时满足 **Generate/Extract/Install Fence**：

1. helper 对本地或请求证书中已退休的 coordinate 拒绝生成 contribution；完全异步下尚未获知 `PF_sid*` 的 helper 仍可能合法生成旧 contribution；
2. contribution 只能导出 `Project(T_req,state)`，不能导出 pre-projection share；
3. 退休前已生成但延迟或归档的 contribution 在 `PF_sid*` 后不能被解封为已退休节点的旧 share；
4. target 在安装时再次验证当前 frontier；
5. 若 target 在 contribution 可解封期间被腐化，该暴露计入会话或恢复实例的累计腐化预算。

### 可行的 transcript 保护方式

以下任一方式可以关闭 Contribution-Exposure edge：

- contribution 信息论上只与 projected live share 相关，与旧 share 独立；
- 使用 target-specific ephemeral public key 加密，目标在安装或取消后擦除 secret key；
- 使用带前向安全的 pairwise channel，并证明未来 channel-state exposure 不能解密旧 contribution；
- 每次 frontier 提升后使旧 contribution 的解封 key 在密码学上失效；
- 不生成 per-target share material，而生成只能进入公开承诺状态转换的 MPC output。

其中“消息绑定 `T_req`”只防止跨实例误用，不自动提供 transcript secrecy。正式构造必须选定一种方式。

## 15. Causal-Fence Relation

Contribution-Exposure 与 Causal-Fence Necessity 是两个不同层次：

- causal fence 防止旧状态被正确节点接受；
- transcript protection 防止旧状态被攻击者离线提取。

如果旧 contribution 本身公开泄漏 share，则 causal fence 无法修复。反之，即使 contribution 加密安全，缺少 install fence 仍可能让正确节点把 pre-retirement functional state 装回系统，并在未来正常部分解密时泄漏 capability。

因此 no-resurrection 需要：

```text
no generation after known retirement
+ no post-finality extraction from pre-finality transcripts
+ no stale installation.
```

## 16. Dynamic Committee Extension

为每个 capability 增加配置索引：

```text
c = (type, sid, cfg, owner, frontier, instance).
```

令 `E_rec` 是配置内恢复边，`E_ho` 是跨配置 handoff 边：

```text
Cl_rec+ho(X) = Cl_{E_rec union E_ho}(X).
```

动态委员会的安全条件仍是：

```text
for every X in I_sid*,
for every D in Gamma_dec^cap(sid*),
D is not a subset of Cl_rec+ho(X).
```

### Proposition 1: Handoff-Closure Preservation

设 `Project_T` 删除 `T` 中所有 retired capabilities。若：

1. 每条 handoff edge 都只以 `Project_T` 后的旧配置 state 为 secret input；
2. handoff output 的 frontier `T'` 满足 `T' >= T`；
3. 任意 handoff 产生的 live-only capabilities 在配置内恢复闭包下仍不能导出 retired `sid*` capability；
4. handoff transcript 满足 Transcript Completeness 和 Generate/Extract/Install Fence；

则添加这些 handoff edges 不会把任何 retired `sid*` direct decryption capability加入闭包。

#### Proof

对 handoff edge 的拓扑顺序归纳。每个新 output 要么是 live capability，要么是 frontier/commitment capability；由条件 1 和 3，从这些 outputs 继续执行配置内恢复也不会得到 retired `sid*` capability。条件 2 防止后续配置降低 frontier，条件 4 排除归档 transcript 与未来 key exposure 形成隐藏 edge。因此 handoff 前闭包对 retired `C_dec(sid*)` 的投影保持不变。

### Matching Attack

若存在从 pre-projection backup 或旧 frontier state 到新配置 `d_i(sid*)` 的合法 handoff edge，且其前件可达，则 `d_i(sid*)` 进入 `Cl_rec+ho(X)`。当这些输出补足某个授权集合时，Theorem 3 直接给出跨配置复活攻击。

## 17. 当前证明状态

### 已完成的抽象证明

- typed capability closure 定义；
- Sound Reachability 的事件归纳；
- Composable Edge Realizability 下的 matching derivation；
- Repair-Closure capability-safety iff；
- Robust-Hitting 特例；
- homogeneous threshold repair amplification；
- Contribution-Exposure lemma；
- Handoff-Closure Preservation 的抽象命题。

### 尚需具体实例验证

- `Static-AO` 的 challenge transcript 与 RCL transcript 是否可联合模拟；
- BF-RPTA 每个 coordinate 的 `Gamma_dec^cap` 和 `E_rec` 精确定义；
- current-share-only repair 的 contribution 是否泄漏目标 share；
- target ephemeral channel 在移动腐化下需要哪种擦除和累计腐化条件；
- Byzantine helper 生成 malformed contribution 时的 soundness reduction；
- 并发 retirement/repair 的 edge set 是否满足 Composable Edge Realizability；
- 动态 handoff 是否只处理 live coordinates，还是底层 DPSS 会隐式保持 master state。

## 18. 下一步

下一步不再把 VSSR 当作最终 `LSR`，而是审计一个固定委员会的 one-shot share-to-share、state-complete resharing：

1. 将 helper polynomial、receiver subshare、共同 helper set 和 new-share 消息写成 typed edges；
2. 把 target exclusion 显式加入 live responder family，验证 `n>=2f+b+2` 的必要边界；
3. 检查每次 repair 输出是否仍包含下一次 repair 所需的完整 current state；
4. 将 `(rid, coordinate, config, frontier, receiver)` 绑定到所有 private subshares，并审计延迟 transcript；
5. 证明 retired coordinate 上 `Cl_rec(X) intersection C_dec = X intersection C_dec`；
6. 仅当该 reduction 失败时，才引入更强的 puncturable recovery authority。

在完成这一步前，不进入 BF-RPTA 全编译证明。

## 19. 当前主线修正：从 VSSR Repair 到 Frontier-Gated Resharing

VSSR 的具体审计证明，普通 recovery contribution 并不是合适的长期 `LSR`：它使用 masked polynomial `s+s_g`，一次 transcript 在未来 DPRF 状态暴露后可展开为一组旧 shares；恢复后的状态又只有 direct share，不能继续帮助生成 VSSR contribution。

因此，抽象定理的首个正向实例应改为 **Frontier-Gated Selective Resharing (FGSR)**。FGSR 在 live coordinate 上运行一次 state-complete resharing，在 retired coordinate 上关闭全部 generation、extraction 和 installation edges。它可以复用 DyCAPS/APSS/DPSS 的多项式 resharing 子协议，但必须重新证明：

```text
old current sharing -> fresh current sharing of the same secret
```

输出的完整 current share 可继续参与下一次 repair，且旧 private subshare transcript 在 frontier 提升后不再产生旧 capability。

这一区分将已有技术和本文贡献分开：已有工作提供 resharing correctness/liveness；本文需要提供 selective frontier、recovery closure 和 target-exclusion redundancy 的联合定理。

### 19.1 当前正向见证

固定委员会下的 one-shot share-to-share resharing 提供更贴合本文的 state-complete 见证。取 `n=3f+2,t=f`，把缺份额 target 仅作为新状态接收者，则其他正确旧节点数为 `n-f-1=2f+1`。共同 helper set `H` 中的每个旧节点将其当前 share 作为新随机多项式的常数项，所有接收者用同一组 Lagrange 系数合成 `F'`；因此 target 得到普通完整 current share，且该输出可直接作为下一次 repair 的输入。

这个见证只证明访问结构和状态形状没有立即矛盾，不证明 FGSR 安全。正式实例化仍需证明：

```text
old-share subshares are frontier-bound,
delayed transcripts cannot be extracted after retirement,
retired coordinates cannot start a new handoff,
live repair output is state-complete.
```

因此 Repair-Closure 定理的下一步是把 one-shot resharing 的 helper-polynomial、subshare、共同 helper set、aggregation 和 installation 消息逐类加入 `E_rec`，而不是把 VSSR 的 `mu_{h->i}` edge 继续外推到长期模型。协议必须同时证明所有 live 节点最终切换到同一个 `F'`，而不是只修复 target。

### 19.2 FGSR v0.1 的安全不变量

FGSR 的最小协议结构为：

```text
Authorize(rid, ell, T_req, H)
    -> ParallelReshare({f_h}_{h in H})
    -> AggregateAndInstall(F')
    -> Erase(old state, pending plaintext, ephemeral keys).
```

与 DyCAPS 的四阶段 handoff 不同，FGSR 不维护 reduced/full bivariate state，也不额外生成 zero polynomial。每个 helper 直接以当前 `z_h` 为新 polynomial `f_h` 的常数项；共同 `H` 的 Lagrange 合成同时保持秘密和刷新 sharing。

形式化证明至少需要以下边：

```text
{z_h, fresh randomness, T_req, C_F} -> f_h
{f_h(j), proof_h, receiver key} -> subshare plaintext
{subshare plaintext : h in H} -> F'(j)
{F'(j), install certificate, T_local <= T_req} -> current state
```

并加入反向排除条件：退休证书支配 `T_req` 后，任何 pending `f_h`、subshare 或 `F'` 都不能进入 current state。若 private transcript 的解封依赖已擦除的 receiver key，则未来状态暴露不应产生新的 `C_dec(ell)` capability；否则该路径必须显式加入 `Cl_rec`。

### 19.3 Common-H 的可实例化条件

令 `P^- = P \ {target}`，在 `P^-` 上运行 validated ACS；此时候选者数为
`n'=3f+1`，ACS 输出 `|V|>=n'-f`，然后所有节点按 descriptor 的确定性顺序
取 `H=Canonical_{2f+1}(V)`。每个候选 helper `h` 先运行包含
target 在内的 AVSS instance，只有在以下证书成立后才提交 descriptor：

```text
ValidDesc_h =
  CurrentShareCommit_h
  and EqualityProof_h(f_h(0)=z_h)
  and PVODVectorProof_h
  and AvailCert_h.
```

`AVSSComplete_h` 的接口语义不是 dealer agreement，而是：所有正确 receiver
最终得到一个经认证、与同一 `C_h` 一致的 `f_h(j)`。ACS 的外部有效性只接受
`ValidDesc_h`，输出集合用 `(rid,ell,cfg,T_req)` 的确定性编码绑定。

`PVODVectorProof_h` 公开验证每个 receiver ciphertext 都加密了同一承诺多项式在
对应 index 的 opening。`AvailCert_h` 包含 `P^-` 中至少 `2f+1` 个不同节点对同一
AVID instance 的 `AVAIL(rid,ell,h,C_h)` 签名；正确节点只在完整 PVOD descriptor
验证通过并完成 AVID disperse 后签名。证书至少包含 `f+1` 个正确 AVAIL，触发
AVID availability，因此 target 虽不参与 ACS 提案，仍能取回自己的有效 ciphertext
并得到 `f_h(target)`。证书不依赖任何 signer 的私密解密结果。

于是可加入两条 typed edges：

```text
{ValidDesc_h : h in H} -> CommonH(rid,ell,T_req,H)
{CommonH, PVODVectorProof_h, AvailCert_h : h in H}
    -> {f_h(j) : h in H, j correct}
```

第一条边由 ACS agreement 提供唯一性；第二条边由 `R_ved` soundness 与 AVID
availability 共同提供。`H` 可以包含 Byzantine helper，但不能包含未证明完整 receiver
vector 或缺少可用性证书的 proposal。target 不参加 ACS 提案，因此不会因缺失旧 share
阻塞集合选择；它仍是每个 PVOD instance 的 receiver。

在 `n=3f+2` 下，`P^-` 中的 `2f+1` 个正确节点最终完成诚实 helper 的 PVOD/AVID，满足
`n'-f=2f+1` 的 ACS termination 条件。该条件正是 FGSR liveness reduction
需要的最小接口；不能用“收到前 `2f+1` 个 commitment”替代。

### 19.4 Common-H 两个引理（候选正式表述）

**Lemma 5 (Common-H Agreement).** 若 validated ACS 满足 agreement 和
external validity，且 `Canonical_{2f+1}` 对 descriptor 使用公开、确定性的
排序，则所有正确节点最终计算相同的 `H`；`H` 不含 target，且其中每个
descriptor 满足 `ValidDesc_h`。

**证明草稿。** ACS agreement 给出相同的 `V`。所有正确节点看到相同的上下文
`(rid,ell,cfg,T_req)`、相同的 descriptor bytes 和相同的排序，因此 canonical
截取结果相同。external validity 排除没有 current-share commitment、equality
proof 或 AVSS completion certificate 的 descriptor；target exclusion 是
外部有效性谓词的一部分。

**Lemma 6 (Common-H Availability).** 若 `n=3f+2`、target 正确、至多 `f`
个非 target 节点 Byzantine，且每个正确非 target helper 的 AVSS instance
最终满足 `AVSSComplete_h`，则所有正确节点最终得到 `f_h(j)`（包括 target）
对每个 `h in H`；因此 Gate 2 不等待 Byzantine helper 的直接响应。

**证明草稿。** 非 target 候选者数为 `n'=3f+1`，其中至少 `2f+1=n'-f`
个正确节点完成 AVSS，故 ACS 终止并输出 `|V|>=n'-f`。canonical 截取保留
`2f+1` 个有效 descriptor。对每个保留 descriptor，`AVSSComplete_h` 给出
所有正确 receiver 的最终点值；有限个 `h` 的并集仍最终可获得。Byzantine
dealer 是否在 `H` 中不影响该结论，因为其入选前已通过同一 completion
certificate。

首个 commitment 实例使用 Pedersen 系数承诺和零知识 opening-equality proof，
避免把 `z_h` 公开到 ACS descriptor；KZG 版本需要额外证明该关系，暂不作为
首个正式实例。

### 19.5 单次实例 transcript-hiding（条件引理）

该引理只处理一个 `rid`，不提前声称多次 repair 的组合安全。设 `B_ell` 是
在擦除前读取 coordinate `ell` 敏感状态的节点集合，且所有 Byzantine 节点的
可保留状态均计入 `B_ell`；`|B_ell|<=b=f`。要求：

```text
retired set A_ell erases its F' direct shares and pending state;
residual set U_ell = P \ A_ell is included in X_current;
|U_ell| + |B_ell| < q_rec;
honest helpers erase f_h coefficients after the instance;
honest receivers erase plaintext points and ephemeral keys;
unexposed helper polynomial degree d=2f has at most b observed points.
```

在这些条件下，归档 subshare ciphertext 与未来状态暴露不能在 residual
`X_current(U_ell)` 和 `X_hist(B_ell)` 之外产生新的 `C_share(ell)` capability。
证明采用
三步 hybrid：

1. 对未暴露 receiver，将已擦除 ephemeral secret 下的 ciphertext 替换为随机
   ciphertext，损失由 PKE IND-CPA 界定；
2. 对暴露 receiver，最多 `b<=d` 个 `f_h` evaluations 在 fresh 高阶系数下与
   常数项 `z_h` 独立，故直接采样其历史 plaintext 不增加未计入的旧 share；
3. 用 Pedersen commitment hiding 和 equality/VSS proof 的零知识模拟公开
   commitment/proof，而不暴露未腐化 helper 的 `z_h`。

其中第一条只把已擦除 `A_ell` 节点的密钥对应 ciphertext 替换为随机；
`U_ell` 节点的残留 ciphertext/key/state 必须保留在模拟器输入中。若
`|U_ell|+|B_ell|>=q_rec`，则直接计数已允许重构，协议不满足 `PF_ell`；若
pending state 产生跨 generation 的额外边，也必须显式加入 `Cl_rec`，不能由
transcript simulator 假定其消失。

该引理的输出是：

```text
ArchivedTranscript(rid,ell) union X_current(U_ell)
    adds no new C_dec(ell) capability beyond residual closure.
```

它仍需与多实例 `B_ell` 合并、retirement/install instance order 和
`Composable Edge Realizability` 组合，才能进入 Theorem 4 的长期证明。

### 19.6 串行多次 repair 的组合条件（保守基线）

本节保留一个便于审计的 session-lifetime 版本；它不是本文当前的长期移动
腐化模型。当前模型及其闭包推论见 19.21--19.24。

设同一 `ell` 的 repair instances 按唯一 instance order 串行执行，每个 instance
使用独立的 helper-polynomial randomness、receiver ephemeral keys 和 `rid`。令
`B_ell` 为整个 coordinate 生命周期的暴露节点并集，包含所有 Byzantine 保留
状态的节点。
若整个 `ell` 生命周期中：

```text
the same exposure set B_ell has size <= b=f;
each completed instance erases its old/current temporary state;
no retired instance can be used as a helper input;
the latest F^r state at U_ell is included in residual closure;
|U_ell| + |B_ell| < q_rec;
```

则可按 instance order 归纳应用 Lemma 6 的 hybrid。每一轮至多暴露 `b<=d`
个 evaluation points；fresh coefficients 使本轮 transcript 不增加上一轮未暴露
的 `C_share(ell)`。当 retirement 进入序列时只有两种情况：

1. `retire < install(rid)`：丢弃 `F^r` 和所有 pending materials；
2. `install(rid) < retire`：先把 `F^r` 作为最新 live state 安装，再由 retirement
   原子删除它。

第一种情况要求所有已确认节点删除 pending state；第二种情况先形成 live
`F^r`，再由 retirement 删除已确认节点的副本，未确认节点的残留副本进入
`X_current(U_ell)`。因此这是一个可用于 `Cl_rec` 的**条件组合引理**，但它
依赖 instance serialization、cumulative exposure bound 和 residual quorum
条件；只限制瞬时 Byzantine 数量不足以推出该结论。

### 19.7 Retirement-Closure 定理（累计暴露的保守条件版）

令 `T_ret(ell)` 是已认证 retirement frontier，`A_ell` 是已完成擦除并签发
确认的节点，`U_ell=P\A_ell` 是可能仍保留 live/pending 状态的节点。定义

```text
X_pf(ell) = X_hist(B_ell)
             union X_current(U_ell)
             union ArchivedPreRetirement(ell).
```

假设：

1. `|A_ell|>=n-f`，`|U_ell|+|B_ell|<q_rec`；
   所有 Byzantine 节点或其可保留的旧状态均计入 `B_ell`；
2. `Authorize`、generation、extraction 和 install edges 均要求 frontier 不被
   `T_ret(ell)` 支配；
3. 已确认节点原子擦除 direct share、pending plaintext、helper coefficients
   和 receiver ephemeral keys；`U_ell` 的残留状态完整纳入 `X_current`；
4. 每个 pre-retirement transcript 满足单次/多次 transcript-hiding 条件，且
   不产生超出 residual closure 的新 `C_share(ell)`；
5. stale output 被所有正确节点拒绝，且任何跨配置 handoff 只从 projected
   live state 读取 `ell`。

则：

```text
Cl_FGSR(X_pf(ell)) intersection Gamma_dec^cap(ell) = emptyset
```

只要右侧授权集合需要 `q_rec` 个同一代 direct capabilities，或更一般地，
`Gamma_dec^cap(ell)` 不被 `X_pf(ell)` 的 residual typed closure 覆盖。

**证明路线。** 按 closure edge 的 instance/frontier 顺序归纳。退休后新生成、
解封和安装边因条件 2 无效；退休前生成但迟到的消息已在 `ArchivedPreRetirement`
中，并由条件 4 不能扩张 residual closure；`U_ell` 与 `B_ell` 的直接能力由
条件 1 不足以形成授权集合；跨配置边由条件 5 只能搬运 live state。故不存在
第一条把闭包推进到任意 `D in Gamma_dec^cap(ell)` 的合法边。

这是条件定理，不是当前已完成的安全证明。真正的剩余任务是证明条件 4 对
多个串行 repair、迟到 transcript 和自适应 `B_ell` 联合成立；若该条件失败，
FGSR 只能作为 liveness/state-completeness 基线。

### 19.7.1 FGSR edge audit

对一个已退休 coordinate，所有相关边必须按来源和 frontier 分类：

| edge | `T < T_ret`（退休前生成） | `T >= T_ret`（退休后尝试） |
|---|---|---|
| `current share -> helper polynomial` | 进入 archived/pending closure | 被 `Authorize`/generation gate 拒绝 |
| `helper polynomial -> encrypted subshare` | 进入 transcript simulator | 无有效 `ValidDesc` |
| `ciphertext + receiver key -> plaintext` | `A` 的 key 擦除；`U` 的 key 入 residual closure | frontier/context 校验拒绝 |
| `subshares -> F'` | 只产生该 `rid` 的 pending/live output | stale output 拒绝安装 |
| `F' -> current state` | `install < retire` 时先安装，再由 `A` 删除；`U` 残留入 closure | 被 instance order 拒绝 |
| `q_dec current shares -> decryption` | 仅由 residual/history closure 计数 | retired coordinate 无新授权边 |

这张表的关键不是把退休前消息删除，而是确保每条已存在的边都落入
`ArchivedPreRetirement`、`X_hist(B_ell)` 或 `X_current(U_ell)`；退休后新增边
则必须不可验证或不可安装。任何未落入三者之一的 transcript 都是未建模能力，
不能声称闭包定理成立。

### 19.8 One-hidden-helper residual-cut 引理

单次 repair 下令

```text
E_ell = U_ell union B_ell,
|E_ell| <= 2f,
|H| = q_rec = 2f+1,
degree(f_h) = d = 2f.
```

则存在 `h* in H \ E_ell`。这里假设所有 Byzantine 保留状态均已计入 `B_ell`；
因此 `h*` 是已确认擦除的 honest helper。对该 helper，A 节点已擦除其 `f_{h*}` 系数，B/U
节点最多向攻击者暴露 `|E_ell|<=d` 个 receiver evaluations；即使攻击者利用
其它已知 helper polynomials 和 residual `F'` shares 反推出额外点值，也不会
超过这些 receiver positions。fresh 高阶系数使：

```text
{f_{h*}(j) : j in E_ell} -/-> f_{h*}(0)=F(h*).
```

因此攻击者至多得到 `q_rec-1` 个旧 `F(h)` direct shares；缺失的 `F(h*)`
阻止旧 sharing 的重构。该引理解释紧参数的理论意义：`n=3f+2` 与
`q_rec=2f+1` 不只是 target-exclusion 的计数修补，还留下一个未暴露 helper
作为 transcript 的信息论遮罩。

**信息论证明。** 对任意 `E=E_ell`，定义：

```text
L_E(X) = product_{j in E} (X-j) / product_{j in E} (-j).
```

所有节点索引非零，所以 `L_E(0)=1`；且 `degree(L_E)=|E|<=d`。若 `f` 与
攻击者观察到的 `{f(j):j in E}` 一致，则对任意 `delta`：

```text
f_delta(X) = f(X) + delta * L_E(X)
```

仍是 degree-`d` 多项式，在所有暴露点取相同值，但
`f_delta(0)=f(0)+delta`。因此观察这些点不能区分任意常数项；均匀 fresh
高阶系数把该双射转化为常数项的完美隐藏。该证明要求 `E` 覆盖所有可见
receiver evaluations，且不包含已泄漏的 helper polynomial coefficients。

该结论仍是单个 sharing transition 的引理。多次 repair 若让不同 transition
中的隐藏 helper 互相形成可组合边，单次 One-hidden-helper 不能自动逐轮相乘；
需要一个保持整条 resharing 链视图不变的耦合变换。该变换如下。

### 19.9 Cross-Generation Affine Coupling 引理

设同一 coordinate 的有限 repair 链为：

```text
F^0 -> F^1 -> ... -> F^R,
F^{r+1}(X) = sum_{h in H_r} lambda_{r,h} f^r_h(X),
|H_r|=d+1,
degree(F^r)=degree(f^r_h)=d.
```

每个 `f^r_h(0)=F^r(h)`，且所有 transition 使用同一个暴露包络
`E=U_ell union B_ell`，其中 `|E|<=d`。定义：

```text
L_E(X) = product_{j in E}(X-j) / product_{j in E}(-j).
```

对任意 `Delta`，同时变换每一代：

```text
F^r_Delta(X) = F^r(X) + Delta * L_E(X)
f^r_{h,Delta}(X) = f^r_h(X) + Delta * L_E(h) * L_E(X).
```

则：

1. 对所有 `j in E`，`F^r_Delta(j)=F^r(j)` 且
   `f^r_{h,Delta}(j)=f^r_h(j)`；
2. `f^r_{h,Delta}(0)=F^r_Delta(h)`，所以 equality proof 关系保持；
3. 因为 `degree(L_E)<=d` 且 `|H_r|=d+1`，Lagrange 插值给出
   `sum_h lambda_{r,h}L_E(h)=L_E(0)=1`，故
   `F^{r+1}_Delta=F^{r+1}+Delta L_E`；
4. 每一代的秘密统一改变为
   `F^r_Delta(0)=F^r(0)+Delta`。

如果 `h in E`，则 `L_E(h)=0`，攻击者可能看到的 Byzantine helper
polynomial 完全不变；如果 `h not in E`，它属于已擦除且未被历史读取的状态，
其系数变化由 fresh randomness 吸收。于是所有暴露的 direct shares、receiver
point values 和可见 helper coefficients 都保持不变；未暴露 ciphertext 由
IND-CPA 模拟，Pedersen commitments 由 hiding、关系证明由 zero knowledge 模拟。

该变换可同时作用于任意有限 `R`，所以关闭了**线性 share-to-share 层**的
跨-generation 组合缺口：多次 repair 不会因为每代更换 hidden helper 而泄漏
共同 secret。剩余证明只需处理 `E` 是否覆盖全部可见状态、frontier 是否阻止
额外 edge，以及非线性 aggregate-opening capability 是否由该 share 层完整
模拟；不能把这三个接口缺口混入代数引理。

### 19.10 Cross-coordinate aggregate-opening edge

若 BF-RPTA 用多个 coordinate 编码同一个客户端 mask key，必须额外禁止以下
未建模边：

```text
partial shares from coordinate ell_1
  + partial shares from coordinate ell_2
  + cross-coordinate consistency proof
  -> aggregate-opening capability.
```

首个接口要求每个 coordinate 使用独立 degree-`d` sharing randomness；跨坐标
一致性证明只证明 ciphertext/mask 的同明文关系，且为 zero knowledge，不提供
share opening。于是 `Gamma_dec^cap` 按 coordinate 保留，跨坐标只允许元数据和
公开证明边，不能把各坐标的 residual shares 相加当作同一多项式的 evaluations。

这不是由 Shamir 门限自动推出的：若多个 coordinate 复用同一多项式高阶系数，
跨坐标 partial shares 会产生额外线性方程，可能降低有效门限。该复用在首版
明确禁止；若未来要 packed coordinates，必须重新计算 typed closure 和
`One-Hidden-Helper` 的暴露包络。

### 19.11 Cross-Coordinate Affine Coupling 引理

设坐标集合为 `I`。对每个 `ell in I`，令其第 `r` 代 sharing 为 `F^r_ell`，
degree 为 `d_ell`，暴露位置包络为 `E_ell`，满足 `|E_ell|<=d_ell`。每个
coordinate 的 helper set `H_{r,ell}` 有 `d_ell+1` 个点，且 resharing 递归为：

```text
F^{r+1}_ell(X) = sum_{h in H_{r,ell}}
                    lambda_{r,ell,h} f^r_{ell,h}(X).
```

对每个坐标定义：

```text
L_ell(X) = product_{j in E_ell}(X-j) / product_{j in E_ell}(-j).
```

对同一个 `Delta`，同时变换所有坐标和所有 generation：

```text
F^r_{ell,Delta}(X) = F^r_ell(X) + Delta*L_ell(X)
f^r_{ell,h,Delta}(X) = f^r_{ell,h}(X)
                              + Delta*L_ell(h)*L_ell(X).
```

逐坐标应用 19.9 的插值恒等式，得到：

1. 每个 `E_ell` 上的 direct share 和 subshare point 不变；
2. 每个 helper equality relation 不变；
3. 所有坐标的秘密都平移同一个 `Delta`，所以“各坐标编码同一 mask key”的
   关系保持；
4. 零知识跨坐标 consistency proof 可直接模拟，不能把坐标间关系变成新的
   share opening。

因此，独立 sharing randomness 加 ZK consistency proof 时，跨坐标 partial
shares 不会增加 aggregate-opening capability；攻击者视图仍存在同一个未知
`Delta` 自由度。该结论依赖每个坐标各自的 residual bound `|E_ell|<=d_ell`。
共享高阶系数、公开线性跨坐标 opening 或非零知识 consistency proof 都会破坏
该耦合，必须作为新的 edge 重新审计。

该结论不能直接支持逐坐标的 `Static-AO` hybrid。因为同一客户端的 mask key
在所有坐标上相同，若只替换一个 coordinate 的 ciphertext，跨坐标 consistency
proof 会发现不同明文。数据面需要一个联合向量 aggregate-opening 游戏：挑战两组
跨坐标一致的 key vectors，保持唯一授权聚合和相同，并联合模拟全部坐标的
consistency proofs。只有在这个联合游戏成立后，`Gamma_dec^cap` 才能从坐标内
share closure 推出完整的 aggregate-only privacy；不能把 zero knowledge 证明
本身当作该联合安全性的替代品。

### 19.12 Joint-AO Composition Lemma (Superseded Candidate)

令 `I` 为 coordinate 集合。每个 `Static-AO_ell` 使用独立公共参数和加密
随机性；对每个客户端 `u`，所有坐标加密同一个 `k_u`，并附带跨坐标明文相等
证明。挑战两组 key vectors `K_0,K_1`，要求：

```text
sum_u w_u*k_{u,0} = sum_u w_u*k_{u,1}.
```

一致性证明采用双模式 CRS：真实模式满足 soundness/knowledge soundness，模拟
模式可以对任意跨坐标 ciphertext 向量生成可接受证明，且两种模式及真实/模拟
证明转录计算不可区分。除此之外，RCL 状态与挑战 key vectors 独立，坐标之间
不共享高阶系数、解密秘密或公开线性 opening。

**Lemma.** 若每个 `Static-AO_ell` 满足选择性 aggregate-only 安全，则联合向量
游戏满足：

```text
Adv_Joint-AO
  <= 2*Adv_DualMode-ZK
     + sum_{ell in I} Adv_Static-AO_ell
     + negl(lambda).
```

**Proof sketch.** 首先用双模式零知识性将真实世界 0 的一致性证明替换成模拟
CRS 下的模拟证明。然后按坐标顺序建立 hybrid；第 `ell` 步只替换该坐标的
`K_0` ciphertext、aggregate ciphertext 和部分解密转录。虽然中间 hybrid 的
跨坐标明文关系可能不满足真实语句，模拟 CRS 仍生成可接受证明；同时该坐标的
两组 key vectors 具有相同加权和，因此该步由 `Static-AO_ell` 安全性归约。完成
所有坐标替换后，再用零知识性恢复真实 CRS 和世界 1 的证明。有限坐标集合下，
混合优势按三角不等式相加。

该引理把联合向量安全归约为已有坐标级 `Static-AO` 安全和明确的 proof-system
假设。普通只支持真实语句模拟的 NIZK 不足以支撑中间 hybrid；若实际一致性
证明达不到双模式模拟要求，则应直接采用独立的联合向量 `Static-AO` 假设，
不能声称由坐标级安全自动推出。

**TACITA compatibility audit.** TACITA 的 modified STE extended CPA 确实允许
两组等长、等和消息，并向攻击者公开聚合 ciphertext 与聚合 partial decryption；
因此它可以实例化每个固定 coordinate 的 `Static-AO_ell`。但其游戏没有跨坐标
同一客户端 key 的关系，也没有双模式模拟 CRS 来处理中间不一致 ciphertext
向量；其腐化集合还在挑战消息前固定。故 `Joint-AO` 不是 TACITA extended CPA
的直接推论，而是需要额外的 dual-mode simulation-sound equality proof，或被
明确列为独立数据面假设。

一个具体的关系是：客户端发布隐藏 commitment `Com_u=Com(k_u;r_u)`，并对每个
coordinate 的 ciphertext `ct_{u,ell}` 证明：

```text
exists k_u,r_u,rho_{u,ell}:
  Com_u = Com(k_u;r_u)
  and ct_{u,ell} = Enc_ell(k_u;rho_{u,ell}).
```

真实 CRS 下的 proof of knowledge 保证同一客户端 key 被用于所有坐标；模拟 CRS
下的 `SimProve` 支持 hybrid 中暂时不满足等式的 ciphertext 向量。相关阈值加密
工作采用 simulation-extractable NIZK、`Setup(crs,td)` 和 `SimProve(crs,td,x)`
的标准接口，因此该路线具有现有原语依据，但 TACITA ciphertext 的随机预言机/群
方程仍需单独写出 relation reduction。

### 19.13 Joint-AO 的正式修正（supersedes 19.12 candidate）

上一版的 commitment 方案遗漏了从 `K_0` 到 `K_1` 时 commitment endpoint 的
hybrid。首版证明接口删除 commitment，令 `I_sid` 为坐标集合，`w_u` 为挑战前
固定权重，并定义：

```text
x_u = (ctx_sid, u, {ek_ell, tag_sid,ell, w_u, ct_u,ell}_{ell in I_sid})

R_eq(x_u; k_u, {rho_u,ell}) iff
  for every ell in I_sid,
    ct_u,ell = Enc_ell(ek_ell, tag_sid,ell, w_u*k_u; rho_u,ell).
```

`ctx_sid` 绑定会话、身份、坐标集合、权重编码和门限参数；证明只公开同明文
关系，不公开 key 或 opening。假设每个 `Static-AO_ell` 支持归约者独立生成
其它坐标和 proof transcript 的 auxiliary-input embedding，且 `R_eq` 使用双模式
simulation-sound NIZK：模拟 CRS 可对任意 statement 运行 `SimProve`，真实/模拟
CRS 和多项式数量的 transcript 不可区分。再假设坐标不共享解密秘密、高阶系数或
公开跨坐标线性 opening，且 proof transcript 不产生解密 capability，则：

```text
Adv_Joint-AO
  <= 2*Adv_DualMode-ZK
     + sum_{ell in I_sid} Adv_Static-AO_ell^aux
     + negl(lambda).
```

证明先模拟 CRS 和 proofs，再按坐标替换。对每一步令 `m_u,b=w_u*k_u,b`；挑战
条件 `sum_u w_u*k_u,0=sum_u w_u*k_u,1` 正好是 TACITA 的等和消息条件。其它
坐标由归约者独立生成，模拟 proof 覆盖中间 hybrid 的假 `R_eq`；完成替换后恢复
真实 CRS 和 proofs。`aux` 是必须写出的归约接口；若 TACITA 游戏不允许该嵌入，
则 `Joint-AO` 仍是独立假设。

该修正确定了权重边界：零权重允许，不需要求逆；权重必须在挑战前固定并采用
统一的加法明文编码。动态权重或看到 ciphertext 后的权重调整不在本定理范围内。

### 19.14 `Static-AO^aux` Auxiliary-Input Lifting Lemma

对固定坐标 `ell`，令 `B_ell` 将 Joint-AO distinguisher 嵌入 TACITA extended-CPA
game。`B_ell` 使用 TACITA challenge 提供第 `ell` 个坐标的参数、honest challenge
密文、aggregate ciphertext 和 partial decryption；它自行生成所有其它坐标的
独立参数及其完整 transcript，并按当前 hybrid 选择 `K_0` 或 `K_1`。将消息映射为
`m_u,b=Encode_T(w_u*k_u,b)` 后，两组 message sets 等长且总和相同。

`B_ell` 在模拟 CRS 下对包含 challenge ciphertext 的 `R_eq` statement 运行
`SimProve`，因此中间 hybrid 的假 relation 不影响视图。腐化 client 的目标坐标
ciphertext 及其 message/randomness 原样交给 TACITA 的 extended-CPA extension，
malformed ciphertext 继续由 TACITA 检查。若坐标参数、随机性和 partial-decryption
transcript 独立，则相邻 hybrid 的差异满足：

```text
Adv[H_{ell-1}, H_ell] <= Adv_Static-AO_ell + negl(lambda).
```

这里的 `aux` 因而是可检查的 reduction interface，而非普通 IND-CPA 的口头延伸。
共享 hidden setup、共享 RO 状态、跨坐标公开线性 opening，或依赖其它坐标秘密的
partial decryption 都会破坏该 lifting；这些情形必须改用独立 `Joint-AO` 假设。

**TACITA relation 的具体形状。** 对每个坐标 `ell`，令
`ek_ell=(C_ell,Z_ell)`，并记 TACITA 的公开矩阵、向量为
`A_ell(ek_ell,tag_sid,ell,t)`、`b_ell`。witness 中的随机性为 `sd_u,ell`，
`s_u,ell=RO(ctx_sid||ell||sd_u,ell)`，则：

```text
ct_u,ell = (tag_sid,ell,
            s_u,ell^T * A_ell,
            s_u,ell^T * b_ell + Encode_T(w_u*k_u)).
```

`Aggr` 对第二、第三分量逐项相加并要求 tag 相同；`PartDec` 绑定聚合密文的
ciphertext-specific component。因此 `R_eq` 电路必须能查询 ROM，或将 oracle
values 纳入 statement；否则只能把 `Joint-AO` 保留为独立假设。该条件是具体
实例化义务，不属于 `Repair-Closure` 抽象定理本身。

### 19.15 SE-NIZK compatibility gate

`Joint-AO` 的逐坐标 hybrid 还要求一个比普通 NIZK 更强的接口：真实/模拟 CRS
不可区分；模拟器能对任意 statement（包括暂时不满足 `R_eq` 的 ciphertext
vector）输出可验证 proof；支持并发多定理 transcript；并能在 TACITA 的随机
预言机与 NIZK proof oracle 组合下保持 simulation soundness/extractability。

Choudhuri 等给出的 `Setup(crs,td)`、`Prove`、`Verify`、`SimProve` 和 weak
simulation-extractability 是候选依据，但其可见定义不足以自动推出上述
arbitrary-statement simulation 和 oracle 组合。若无法补齐这一 gate，当前论文
应把 `Joint-AO` 写成独立联合数据面假设。

### 19.16 Proof-gap resolution: unconditional core and conditional lifting

The proof obligation is separated at the theorem boundary. The main
`Repair-Closure` and privacy-finality theorem assumes `Joint-AO^mob` for the full
cross-coordinate transcript. Its challenge includes all coordinate ciphertexts,
aggregate ciphertexts, partial decryptions, and public consistency data; the only
message relation is:

```text
sum_u w_u*k_u,0 = sum_u w_u*k_u,1.
```

This formulation does not run a coordinate-by-coordinate hybrid and therefore
does not require a proof for an intermediate false `R_eq` statement. The main
theorem has the form:

```text
Privacy-Finality(BF-RPTA)
  <= Joint-AO^mob + RCL-Sim/AO + Robust-Hitting + correctness.
```

The TACITA lifting is a separate conditional theorem. It is valid only under a
`DM-SE-NIZK^{RO,eq}` whose simulated CRS is indistinguishable from the real CRS,
whose `SimProve` accepts arbitrary public statements, and whose concurrent
simulation-extractability is defined jointly with the TACITA programmable random
oracle. Under the independence conditions in 19.14:

```text
Adv_Joint-AO
  <= 2*Adv_DM-SE-NIZK^{RO,eq}
     + sum_ell Adv_Static-AO_ell^aux
     + negl(lambda).
```

The current Choudhuri interface establishes a candidate `Setup/Prove/Verify/SimProve`
API and weak simulation-extractability, but the transcribed definition does not
establish arbitrary-statement simulation or the required joint-oracle theorem.
It therefore cannot be cited as a completed instantiation. The paper should
present `Joint-AO^mob` as the explicit data-plane assumption in the main result,
retain `Joint-AO` as the static baseline, and list the TACITA reduction as an
instantiation theorem conditional on the adaptive gate.
This closes the proof bookkeeping gap without hiding a cryptographic assumption
inside the `Repair-Closure` abstraction. Section 19.17 remains the static
`Joint-AO` baseline; the long-lived theorem uses the adaptive extension in 19.50.

### 19.17 Formal `Joint-AO` game

The main theorem uses the following joint data-plane game rather than a sequence
of coordinate-local games. Let `I_sid` be the fixed coordinate set for the session,
`U` the accepted client set, `C` a static corruption set, and `H=U-C`. The
pre-challenge context fixes the participant set, coordinate set, weights, encoding,
threshold parameters, and all tags. Any digest of challenge ciphertexts or outputs,
such as `H_ct` or `H_out`, is generated inside the challenge and is part of the
challenge-dependent data view.

1. **Setup.** The challenger samples independent coordinate parameters and
   threshold decryption shares for every `ell in I_sid`. It gives the public
   parameters and the corruption interface to the adversary.
2. **Challenge.** The adversary supplies two key vectors
   `K_0=(k_{u,0})_{u in H}` and `K_1=(k_{u,1})_{u in H}`, together with a
   challenge-independent auxiliary
   transcript `z`. The vectors have the same domain encoding and satisfy

   ```text
   sum_{u in H} w_u*k_{u,0} = sum_{u in H} w_u*k_{u,1}.
   ```

   For the selected bit `b`, the challenger sets, for every accepted honest
   client and every coordinate,

   ```text
   m_{u,ell,b} = Encode_T(w_u*k_{u,b}).
   ```

   It samples the coordinate ciphertexts, all cross-coordinate consistency
   transcripts, aggregate ciphertexts, valid partial decryptions, all
   challenge-dependent context digests, and the unique aggregate-opening
   certificate. The adversary supplies one fixed valid corruption-side transcript;
   it is used in both worlds. The released aggregate value is the same in both
   worlds because the weighted sums agree.
3. **View.** The adversary receives the complete public transcript, including all
   coordinate ciphertexts, aggregate ciphertexts, partial decryptions, proofs,
   certificates, `z`, and the common aggregate output, but no individual opening.
   It outputs a bit `b'`.

Define

```text
Adv_Joint-AO(A)
  = |Pr[b'=0 in Exp_Joint-AO(0)]
      - Pr[b'=1 in Exp_Joint-AO(1)]|.
```

The game is selective in `C`, `U`, `I_sid`, weights, and context. It is aggregate-only:
the challenge transcript may contain every ciphertext and partial decryption, but
the interface exposes only the common weighted aggregate. The consistency proof is
part of the challenge transcript, not an independently simulated side channel.
This definition is deliberately stronger than a list of per-coordinate IND-CPA
games and is the static data-plane baseline. The long-lived theorem consumes the
adaptive extension `Joint-AO^mob` in Section 19.50.

### 19.18 Main composition theorem

Let `X_pf(sid)` be the complete current, historical, and archived state view
allowed by the asynchronous corruption experiment. Assume:

1. `RCL-Sim/AO`: recovery and handoff transcripts for `X_pf(sid)` admit a
   simulator whose output is independent of the challenge bit, conditioned on
   `PublicContext_pre` and the common authorized aggregate; every state-dependent
   data-plane output is included in the `Joint-AO^mob` transcript;
2. `CapSafe`: the same simulator produces no capability outside
   `Cl_rec(X_pf(sid))`, and `Cl_rec(X_pf(sid))` contains no member of
   `Gamma_dec^cap(sid)`;
3. the data plane satisfies `Joint-AO^mob` for the adaptive prefix and accepted set;
4. context binding makes `sid`, coordinates, weights, aggregate certificate, and
   output unique, and the key-homomorphic mask is correct for the common weighted
   key.

Then for any two accepted honest update vectors with the same authorized
aggregate,

```text
Adv_Privacy-Finality(A)
  <= Adv_RCL-Sim/AO(A)
     + Adv_Joint-AO^mob(A')
     + Adv_Context/Correctness(A'')
     + negl(lambda).
```

**Proof.** In `H_0`, run the real asynchronous protocol and expose all states and
legal recovery/handoff messages allowed by the experiment. In `H_1`, replace those
messages with `RCL-Sim/AO`. The first term bounds this transition. By `CapSafe`, the
simulator cannot output an individual decryption capability, so the residual view
contains only the data-plane transcript and the capabilities already accounted for
in `X_pf`.

In `H_2`, invoke `Joint-AO^mob` on the complete coordinate vector. The challenge
condition preserves the unique weighted aggregate, so every ciphertext, proof,
aggregate ciphertext, partial decryption, and public certificate in the view is
covered by one game. This transition contributes the second term. Finally, context
binding and mask correctness imply that the released aggregate and all accepted
control decisions are identical in the two worlds; a difference is therefore a
correctness or binding failure. This gives the third term. The argument does not
perform a coordinate-local hybrid and consequently never asks a NIZK simulator to
prove an intermediate false statement.

`Joint-AO^mob` is the explicit data-plane assumption for the long-lived theorem,
while 19.17 remains the static baseline. A TACITA reduction may replace
`Adv_Joint-AO^mob` only after the adaptive lifting gate in 19.50 is separately
proved.

### 19.19 BF-RPTA state-factorization lemma

The intended BF-RPTA separation satisfies `RCL-Sim/AO` under the following
checkable conditions:

1. all threshold decryption shares and repair randomness are sampled independently
   of `K_0,K_1`;
2. `Puncture`, `Contribute`, `Recover`, and `CheckInstall` consume only the
   pre-challenge context, frontier/generation metadata, and current committee
   shares, not an individual client key or individual coordinate plaintext;
3. any partial decryption, certificate, or metadata digest that consumes a
   challenge ciphertext is placed in `DataView_b` and challenged jointly by
   `Joint-AO`;
4. current-share-only repair and atomic erasure satisfy the transcript-hiding and
   closure conditions of Sections 19.5, 19.21, 19.22, and 19.24.

Under these conditions, the exposed view factors as

```text
View_b = (DataView_b, StateView, PublicContext_pre),
```

where `StateView` has a common distribution in both worlds and its reachable
capabilities are contained in `Cl_rec(X_pf(sid))`. Consequently,

```text
Adv_RCL-Sim/AO
  <= Adv_Transcript-Hiding
     + Adv_State-Commitment
     + negl(lambda).
```

`Adv_State-Commitment` covers only binding/context failures in the state layer;
it does not cover a digest or certificate that directly encodes a challenge
ciphertext. Such an object belongs to `DataView_b`. The lemma therefore reduces
the cross-layer proof to the existing one-coordinate transcript-hiding and
retirement-closure obligations, while preventing `H_ct`/`H_out` from silently
entering the supposedly challenge-independent state view.

### 19.20 State-layer/data-plane noninterference gate

`RCL-Sim/AO` is stronger than ordinary repair transcript hiding. It is required
because a view can distinguish `K_0` from `K_1` without containing a complete
decryption set. The condition is the following factorization of the exposed view:

```text
View_b = (DataView_b, StateView, PublicContext_pre),
```

where `DataView_b` is exactly the transcript covered by `Joint-AO`, and `StateView`
has the same distribution for both challenge worlds. In particular, repair,
handoff, current-state exposure, and stale-state rejection may depend on session
metadata and threshold state, but may not expose an unmodeled function of an
individual `k_{u,b}` or of an individual coordinate plaintext. If a state-dependent
partial decryption or proof depends on the challenge ciphertext, it belongs in
`DataView_b` and must be included in the `Joint-AO` game.

This gate is satisfied by the intended separation where RCL stores and repairs
committee decryption shares, while client mask keys appear only in the data-plane
ciphertexts and the common aggregate opening. It is not implied by `CapSafe` alone:
capability safety prevents a full unauthorized opening, whereas state-layer
noninterference prevents a smaller residual leakage from distinguishing the two
challenge vectors. The main theorem must cite both conditions.

### 19.21 Instance-local adaptive composition

The lifetime condition `|union_r B_{ell,r}|<=f` used by the conservative version of
19.6 is sufficient but too strong for a long-lived mobile adversary. For repair
generation `r`, define a causal generation interval from the installation of
`F^r` until the next accepted installation or retirement barrier. `B_{ell,r}`
contains every node whose current share, helper polynomial, receiver plaintext, or
ephemeral decryption state is exposed anywhere in that interval, not merely during
the repair messages. If no next barrier occurs, the interval extends to retirement.
Let `B_{ell,ret}` be the final interval's exposure set and let `U_ell` be the nodes
whose residual state survives retirement. Require:

```text
|B_{ell,r}| <= f,
|U_ell| <= f,
|U_ell union B_{ell,ret}| <= 2f < q_rec.
```

Each instance additionally uses fresh helper-polynomial coefficients and receiver
ephemeral keys; `Authorize`, extraction, and installation are generation-tagged;
completed instances erase helper coefficients, plaintext evaluations, and receiver
ephemeral keys; and the next current sharing is fresh conditioned on the complete
prior view, with its unexposed helper points remaining fresh relative to
`B_{ell,r}`.

**Conditional composition lemma.** If the one-step simulator satisfies 19.5, then
for any polynomial number `R` of causally ordered repairs, even when
`B_{ell,r}` is chosen adaptively from the prior view,

```text
Adv_Transcript-Hiding^R
  <= sum_{r=1}^R Adv_Sim_r
     + Adv_Generation-Binding
     + R*negl(lambda).
```

Define hybrids by the first instance whose transcript is simulated. At instance
`r`, the adaptive exposure set is fixed by the preceding view, while fresh
coefficients and ephemeral keys remain uniform. The affine coupling with
`L_{B_{ell,r}}` preserves all exposed points and the current secret in a live
generation, leaving a hidden helper; at the retirement barrier the terminal coupling
uses `L_{U_ell union B_{ell,ret}}`. Generation binding and erasure prevent the hidden
shift or stale transcript from becoming a new edge in later instances. Induction
gives the bound. A failure to reject an old-generation input is charged to
`Adv_Generation-Binding`.

This permits the adversary to corrupt every identity across different generation
intervals, while limiting each interval's relevant state to the stated bound. The
causal barrier is essential: if old shares remain valid helper inputs, plaintext
contributions persist, or the adversary can read all current shares before the next
barrier, the local composition claim fails and the cumulative/session-lifetime
exposure bound must be restored.

### 19.22 Local-to-global Retirement-Closure corollary

This corollary is the current composition statement. Let `r=0,...,R` index the
generation intervals of coordinate `ell`, with `r=R` the final interval ending at
retirement. Every direct share, helper polynomial, pending output, and recovery
certificate carries its generation tag. Define the generation-separated residual view:

```text
X_pf^loc(ell) = union_{r=0}^R X_hist^r(B_{ell,r})
                 union X_current(U_ell)
                 union ArchivedPreRetirement^tagged(ell).
```

Assume:

1. `|B_{ell,r}|<=f` for every interval, `|U_ell|<=f`, and
   `|U_ell union B_{ell,R}|<=2f<q_rec`;
2. each accepted installation uses fresh helper-polynomial coefficients and
   receiver ephemeral keys conditioned on the complete preceding view;
3. `Cross-Generation Affine Coupling` preserves every exposed point and equality
   relation while propagating a common affine shift across generations; it is a
   distributional coupling, not a legal protocol transition. Generation binding makes
   a share or transcript from generation `r`
   invalid as an input to generation `r+1` except through the accepted installation
   edge;
4. completed instances erase helper coefficients, plaintext evaluations, and
   receiver ephemeral keys, and the one-step simulator of 19.5 covers every typed
   pre-retirement transcript;
5. the retirement frontier disables generation, extraction, installation, and
   decryption edges for `ell`; stale outputs are rejected; and handoff projects only
   live coordinates;
6. no cross-coordinate or aggregate-opening transcript creates a capability outside
   the generation-tagged current-share closure.

Then, except with the sum of the one-step simulation, generation-binding, state
commitment, and correctness errors,

```text
Cl_FGSR(X_pf^loc(ell)) intersection Gamma_dec^cap(ell) = emptyset.
```

**Proof.** Use a prefix hybrid over the causally ordered intervals. At interval `r`,
the adaptive set `B_{ell,r}` is fixed by the preceding view and has size at most
`f`; fresh coefficients allow the affine shift determined by `L_{B_{ell,r}}`, so all
exposed points and equality relations are preserved while the coupled secret moves
within the admissible affine family. The hidden share is tagged with `r`, hence it cannot be
combined with a point from another generation. At the final retirement interval use
`L_{U_ell union B_{ell,R}}`; its degree is at most `2f`, while the helper set has
`q_rec=2f+1` members, leaving one helper outside the terminal residual set.

The only permitted cross-generation transition is the accepted installation edge,
which preserves the secret but creates fresh generation-tagged shares. Erasure removes
the temporary inputs to all other transition edges. After retirement, frontier
dominance and stale-output rejection remove every new edge for `ell`; condition 6
removes the remaining nonlinear data-plane alternatives. Thus no first legal edge
can extend the residual closure to an authorized decryption set. The prefix hybrid
adds at most `sum_r Adv_Sim_r + Adv_Generation-Binding + R*negl(lambda)` plus the
state and correctness terms.

The corollary does not derive the one-step simulator or condition 6 from ordinary
VSS correctness. Those are separate construction obligations; failure of either is
an explicit boundary of FGSR rather than a claim of long-lived security.

### 19.23 Necessity of a causal generation barrier

The interval condition is not a terminology change for an instantaneous corruption
bound. Consider any protocol in which a coordinate has a valid `q_dec`-out-of-`n`
sharing `F^r` and, between two state-changing barriers, a corrupted node's share
remains a valid direct capability. Assume the asynchronous scheduler may delay all
messages that would install a fresh sharing or complete erasure. If

```text
q_dec <= n
```

then an adversary maintaining at most `f` active corruptions can expose the shares
of `q_dec` distinct nodes sequentially before the barrier. It stores each share,
releases the node, and continues; the scheduler keeps the sharing at generation `r`.
The stored shares reconstruct `F^r(0)` and therefore the retired coordinate's
decryption capability. The attack succeeds even though the instantaneous Byzantine
set never exceeds `f`.

**Barrier necessity lemma.** Any theorem claiming long-lived privacy under only an
instantaneous corruption bound must provide, between exposure intervals, an event
that simultaneously (i) installs a sharing statistically fresh with respect to the
previous exposed view, (ii) makes old shares invalid for all future recovery edges,
and (iii) erases the old share before the adversary can expose the next interval.
Otherwise the scheduler realizes the sequential-share attack above. This lemma is
independent of the encryption primitive and applies to Shamir, threshold PKE shares,
and any capability representation with a reconstructible same-generation access
set.

### 19.24 Concrete one-step simulator and typed edge coverage

This section instantiates the one-step simulator required by 19.5. Fix a repair
instance rid for coordinate ell and generation r. The simulator receives the
pre-challenge context, public commitments, the certified helper set H, and the
residual typed state. It does not receive the unexposed current evaluations
z_h=F^r(h). Partition receivers according to the state that survives the
instance:

```text
A_r = receivers that erase the instance state before later exposure;
B_{ell,r} = receivers exposed during the generation interval;
U_ell = receivers whose state survives retirement.
```

The simulator must cover every output of Authorize, Parallel Reshare, and
Aggregate/Install/Erase as follows:

| object | simulator action | closure destination |
|---|---|---|
| authorization tuple (rid,ell,generation,frontier,H) | replay authenticated public context | StateView |
| ValidDesc_h, AvailCert_h, and Common-H result | replay the certified descriptor or simulate only zero-knowledge proof material | StateView |
| Com_F(h), Com_{f_h}, equality proof, and VSS proof | use commitment hiding and proof simulation for unexposed helpers; retain real exposed objects | StateView or X_hist^r(B_{ell,r}) |
| receiver ephemeral public key | sample honestly, independently of data-plane keys | StateView |
| subshare ciphertext sent to A_r | replace after the corresponding ephemeral secret is erased by PKE IND-CPA | simulated transcript |
| subshare plaintext sent to B_{ell,r} | retain the exposed evaluation | historical closure |
| subshare plaintext or pending state retained by U_ell | retain the complete residual object | X_current(U_ell) |
| F', install certificate, and erase event | replay only the generation/frontier-bound state transition | StateView or X_current(U_ell) |
| pre-retirement late message | preserve its rid and generation tag and apply the same receiver partition | archived transcript or residual closure |
| partial decryption, H_ct, H_out, or challenge-dependent aggregate certificate | generate as part of the joint data-plane challenge | DataView_b |
| any individual-key or individual-plaintext object absent above | reject the claimed simulator | uncovered edge |

For an unexposed helper h, the simulator samples conditional point values using
the affine coupling from 19.9. During a live generation it uses L_{B_{ell,r}};
at retirement it uses L_{U_ell union B_{ell,ret}}. The coupling keeps all exposed
evaluations and equality relations fixed while moving the hidden constant term
inside the admissible affine family. It is a distributional completion of the
view, not a claim that the real protocol changes its secret. For h in B_{ell,r},
the helper polynomial and every exposed evaluation are already part of the
historical state. For h outside that set, the unexposed coefficient vector is
never released after the instance and its commitment/proof is simulated.

The hybrid has four transitions:

1. Replace ciphertexts whose receiver secrets are erased with random ciphertexts;
   charge PKE IND-CPA.
2. Replace unexposed-helper commitments, equality proofs, and VSS proofs with
   their hiding and zero-knowledge simulations; charge proof-simulation and
   Adv_State-Commitment.
3. Apply the affine completion to the remaining unexposed point values. The
   adaptive B_{ell,r} is fixed by the preceding view, and the terminal set is
   U_ell union B_{ell,ret}; charge Adv_Affine-Coupling if the conditional
   distributions differ.
4. Move every challenge-dependent partial decryption or digest into DataView_b
   and invoke Joint-AO; generation-tag failures are charged to
   Adv_Generation-Binding.

A sufficient one-step interface is:

```text
Adv_Transcript-Hiding^(1)
  <= Adv_PKE-INDCPA
     + Adv_Proof-Simulation
     + Adv_Affine-Coupling
     + Adv_State-Commitment
     + Adv_Generation-Binding
     + Adv_Uncovered-Edge
     + negl(lambda).
```

Adv_Uncovered-Edge is zero only after the typed table is exhaustive. The
simulator cannot hide an aggregate-opening object by placing it in the state
layer, cannot erase a receiver object that remains in U_ell, and cannot treat a
stale ciphertext as harmless merely because CheckInstall rejects it. This gives
a checkable proof obligation for the concrete FGSR instance and supplies the
one-step premise used by 19.22.

### 19.25 Concrete FGSR instantiation ledger

The one-step interface becomes checkable with the following proof-friendly
instantiation. Let G be a prime-order group with independent generators g and h.
For a degree-d current polynomial F, publish Pedersen coefficient commitments
to its coefficients. Helper h0 creates

```text
f_h0(X) = z_h0 + sum_{k=1}^d a_h0,k X^k,
z_h0 = F(h0),
```

and publishes coefficient commitments for f_h0. The descriptor contains a
zero-knowledge equality proof that the message in the constant commitment of
f_h0 equals the message in the evaluated commitment of F at h0. It does not
open either message. This proof is the only binding interface needed to derive
F'(0)=F(0); KZG is not required by this instantiation.

The AVSS interface is required to be opaque with respect to the polynomial
coefficients: public AVSS messages contain commitments, validity proofs, READY
certificates, and protocol metadata, while the point f_h0(j) is delivered to
receiver j through its authenticated private channel. A correct receiver
delivery must imply eventual delivery of the same authenticated point to every
correct receiver. This is the AVSS-Complete property used by Common-H. An AVSS
implementation that broadcasts point values or exposes reconstructible
coefficient information does not satisfy this ledger.

For each receiver j, generate an independent ephemeral key pair and encrypt
the authenticated point f_h0(j) under a label containing rid, ell, generation,
helper, receiver, and frontier. The label is checked by the receiver together
with the signed descriptor; it is not a source of secrecy. After commit or
cancel, the helper erases its coefficient vector. After install or cancel, a
correct receiver erases the plaintext point and ephemeral secret key. A
retirement-confirmed receiver erases all remaining coordinate-local state.

The resulting output classification is exhaustive:

| concrete output | reason it is covered | destination |
|---|---|---|
| ACS, READY, descriptor, frontier, and generation metadata | independent of client mask keys and bound by authenticated context | StateView |
| Pedersen commitments | hiding; exposed commitments are retained in the prefix view | StateView or historical closure |
| equality, VSS, and AVSS validity proofs | zero-knowledge simulation plus binding/soundness | StateView |
| ephemeral public keys | independently sampled and public | StateView |
| encrypted f_h0(j) for an erased receiver | PKE IND-CPA after secret-key erasure | simulated transcript |
| plaintext f_h0(j) for an exposed receiver | already returned by the corruption oracle | X_hist^r(B_{ell,r}) |
| plaintext or pending state retained by U_ell | explicitly returned in final state exposure | X_current(U_ell) |
| F', install certificate, and erase event | deterministic from the same H, frontier, and accepted points | StateView or X_current(U_ell) |
| stale or duplicate output | rejected by rid, generation, frontier, and certificate binding | no new edge |
| partial decryption, H_ct, H_out, and aggregate certificate | depends on challenge ciphertext or output | DataView_b and Joint-AO |

The simulator first replays the authenticated context and Common-H result. It
then simulates commitments and proofs for unexposed helpers, replaces
erased-receiver ciphertexts, and samples the remaining conditional point values
through the affine coupling. Exposed helper and receiver state is copied
exactly into the historical view; U_ell state is copied exactly into the
residual view. The final data-plane objects are generated only by the Joint-AO
challenge.

Under the opaque AVSS, equality-proof, PKE, erasure, generation-binding, and
state-commitment assumptions, every concrete output is in the table. Therefore

```text
Adv_Uncovered-Edge = 0,
```

and the one-step bound of 19.24 reduces to the stated primitive advantages and
the affine-coupling error. This is a conditional instantiation result: ordinary
AVSS agreement alone does not imply opaque point delivery, and ordinary
commitment binding alone does not provide equality-proof simulation.

### 19.26 Cross-coordinate nonlinear isolation as a typed capability lemma

The remaining condition in 19.22 is a capability-closure condition, not a claim that
independent randomness alone prevents cross-coordinate leakage. Tag every secret-bearing
object by `(sid,coordinate,generation)` and distinguish:

```text
Share(ell,r,i), RepairShare(ell,r,h,i), AggregateKey(sid), ProofMeta(sid,I).
```

`Interpolate_{ell,r}` and `PartDec_{ell,r}` accept only objects with the same
coordinate and generation tag. `Repair_{ell,r -> r+1}` accepts only source objects
with coordinate `ell` and generation `r`, and outputs a fresh `Share(ell,r+1,i)`;
it has no cross-coordinate secret input. Cross-coordinate consistency proofs are zero
knowledge and their verification output is only `ProofMeta`; it cannot be used as a
scalar share, a decryption share, or a witness to a later recovery step. Coordinate
parameters, sharing randomness, and receiver-ephemeral keys are independent, and no
public cross-coordinate linear opening or cross-coordinate-dependent partial
decryption is exposed.

Proof verification may affect only public acceptance metadata or a data-plane
selection already declared in the fixed `Joint-AO` context. It may not select an
individual ciphertext, partial decryption, or recovery branch in a way that depends
on a hidden witness. We call this the proof-noninterference condition; any data-plane
selection outside the declared context is a new `DataView` edge.

Let `TypedCl(T)` be the closure of these typed objects and operations in a transcript
and state view `T`. Let `Cap_ell(T)` be the scalar opening capabilities derivable using
only coordinate `ell`, and let `Cap_AO(T)` be the single aggregate-only output allowed
by `Joint-AO`.

**Typed capability isolation lemma.** Under multi-theorem zero knowledge for the
consistency proof and the interface conditions above,

```text
Cap(T) subseteq union_ell Cap_ell(T) union Cap_AO(T).
```

Every shortest derivation of an individual-key capability can be normalized to a
derivation whose secret-bearing operations use one coordinate only. The proof is by
induction on the last operation. A final `Interpolate`, `Repair`, or `PartDec` has,
by the typed transition rules, only same-coordinate secret inputs and therefore belongs
to some `Cap_ell`. A proof verification returns only `ProofMeta` and cannot be the final
step of an individual-key derivation. If proof metadata controls a public acceptance
decision or a declared data-plane selection, that influence is already in the fixed
context or in `Cap_AO`; proof-noninterference excludes any other path to a
secret-bearing operation. The only cross-coordinate secret-bearing operation is the
authorized aggregate output, which belongs to `Cap_AO`; all remaining metadata carries
no secret equation. This proves the inclusion.

Consequently, if `Cl_rec(T) intersection Cap_ell(T) = emptyset` for every coordinate
and `Cap_AO` reveals only the authorized aggregate, then:

```text
Cl_rec(T) intersection Gamma_dec^cap = emptyset.
```

The lemma is not implied by ordinary NIZK soundness or by independent ciphertext
randomness. An implementation that multiplies partial decryptions across coordinates,
treats a commitment as a scalar share, or lets proof verification influence recovery
creates a new typed edge and must charge it to `Adv_Uncovered-Edge`. Thus 19.26 is a
separate construction obligation and supplies the missing condition 6 in 19.22.

### 19.27 Opaque-delivery audit of existing VSS interfaces

`AVSS-opaque` is an interface defined for this construction, not a property that
follows from the name AVSS. We require five separate conditions:

```text
(OD1) public messages contain no scalar point/evaluation or reconstructible coefficient;
(OD2) each receiver obtains its point through an authenticated receiver-specific channel;
(OD3) the receiver plaintext and ephemeral decryption state are erased at the barrier;
(OD4) recovery responses do not expose a new public scalar opening edge;
(OD5) validity and availability imply eventual consistent delivery to every correct receiver.
```

The local APSS construction is a plausible source for (OD2) and (OD5), and its
commitment-revelation phase publishes group elements `g^{p(i)}` with a DLEq proof rather
than the scalar `p(i)`. This can satisfy the scalar-free part of (OD1) under the relevant
discrete-log assumption. It does not, however, prove the FGSR interface as a black box:
its secrecy definition is for a static corruption set and excludes executions in which
an honest node has started reconstruction; it also addresses global refresh rather than
target-excluded selective repair and retirement. Its own discussion of future corruption
and secure erasure is therefore a model premise to be adapted, not a proof of
`RCL-Sim/AO`.

VSSR supplies a different warning. Its recovery contribution contains a blinded share
of the original polynomial together with a DPRF contribution, and a recovering replica
reconstructs a polynomial before subtracting the masking value. This is a valid share
recovery interface, but it is precisely a new recovery edge. The VSSR secrecy statement
does not cover a node after reconstruction has begun, so invoking VSSR after retirement
would invalidate (OD4) unless the recovery contribution is redesigned and bound to the
retirement frontier.

DyCAPS demonstrates that private channels, mobile corruption bounds, and explicit
erasure can coexist in an asynchronous committee protocol. Its guarantee is tied to
the high-threshold handoff state and its four-stage protocol, however; it does not give
the per-coordinate, unordered retirement interface used by FGSR. We therefore reuse its
channel and erasure assumptions only as evidence that the required system model is
meaningful, not as a black-box proof of opaque delivery.

The first instantiation consequently has a precise go/no-go rule: an ACSS/AVSS candidate
may implement `AVSS-opaque` only after its public transcript, corruption oracle,
reconstruction behavior, and erasure timing jointly establish (OD1)--(OD5). If any
recovery message contains a scalar share, or if future state exposure can decrypt an
archived point, the candidate remains outside the concrete theorem and the error is
charged to `Adv_Uncovered-Edge`; ordinary AVSS agreement and availability are not enough.

### 19.28 Black-box private-channel lemma for `AVSS-opaque`

The usable part of APSS is its complete-sharing transport, not the full global
refresh protocol. Let `C` be an ACSS-style sharing layer for a helper polynomial
`f_h`. We require the following interface properties:

```text
(PC1) C delivers one scalar evaluation f_h(j) to receiver j through a private channel;
(PC2) its public transcript contains only a binding commitment, validity metadata,
      and availability evidence, with no scalar evaluation or scalar-reconstructible
      coefficient;
(PC3) validity/availability imply eventual delivery of the same committed evaluation
      to every correct receiver;
(PC4) a receiver's delivered point can be checked against the commitment without
      opening any other receiver's point.
```

Construct `Eph(C)` by keeping `f_h(j)` exclusively on the receiver-specific private
channel. After checking the point against the commitment, the receiver publishes only
an authenticated `READY` receipt containing `(rid,ell,generation,h,j,frontier)` and a
commitment identifier; the receipt contains no point value. The receiver erases its
plaintext and channel endpoint state at commit, cancel, or retirement, and the helper
erases its polynomial coefficients after the instance. No post-barrier recovery
response is accepted.

**Conditional transport proposition.** If `C` satisfies (PC1)--(PC4), the private
channel provides confidentiality against later endpoint exposure after the prescribed
erase event, and `READY` receipts are authenticated and frontier-bound, then `Eph(C)`
satisfies (OD1)--(OD5).

The proof is direct. (PC2), together with the fact that `READY` contains only metadata,
establishes (OD1). (PC1) establishes (OD2), and (PC3) establishes (OD5). Endpoint and
buffer erasure gives (OD3): after the barrier, the corruption oracle has no channel
state from which to recover the point. Since `Eph(C)` has no post-barrier recovery
response and every receipt is frontier-bound, it contributes no public scalar opening
edge, giving (OD4). Authentication and label checking ensure that a delayed receipt
cannot install a point for another generation.

This proposition remains valid as a black-box lemma when (PC3) is supplied independently.
Proposition 61 shows that local receiver receipts do not instantiate (PC3) for a Byzantine
helper in target-excluded repair. The current first construction therefore uses PVOD from
19.101: every encrypted evaluation has a public `R_ved` proof, and `AVAIL` certifies AVID
storage rather than private decryption. The remaining private-channel route would need a
separate complete-delivery functionality with no scalar recovery transcript.
The APSS global-refresh theorem, its static corruption game, and VSSR recovery
procedure are not invoked by this proposition. Consequently, the transport layer can
enter the FGSR theorem only after these three obligations are proved; otherwise the
result remains the abstract `AVSS-opaque` conditional theorem.

### 19.29 Channel security is distinct from forward secrecy

The channel premise used by 19.28 should be stated as a separate interface. For an
endpoint instance `e`, let `View_ch^e(tau+)` contain every public or corruption-readable
object after the receiver's local barrier `tau`: an in-flight ciphertext, archived network
state, receive buffers, and residual plaintext/key state. We say that a channel has
**post-erasure confidentiality (PECC)** if, for an endpoint uncorrupted before `tau`, the
distribution of `View_ch^e(tau+)` is indistinguishable for any two equal-length valid
payloads. This is a property of the channel-plus-endpoint state transition, not merely of
an encryption algorithm.

PECC does not require the network to delete or rewind an in-flight ciphertext. The network
may retain and deliver the ciphertext after `tau`; confidentiality requires that the
post-barrier endpoint state cannot turn that ciphertext into a scalar capability. The
barrier is local to the receiver that acknowledges retirement. Endpoints that have not
acknowledged retirement remain in the residual set `U_ell` and are accounted for by
`X_current(U_ell)` rather than treated as erased.

An ordinary private authenticated channel gives confidentiality while both endpoints
are honest. It does not by itself protect a delayed message or a buffered plaintext
that the corruption oracle reveals later. A forward-secure encryption channel protects
recorded ciphertexts after compromise of a later long-term key, but it also does not
erase a plaintext already retained at the receiver or a pending ciphertext/key in a
local buffer. Thus:

```text
forward-secure channel + retained plaintext/key state       -> insufficient;
plaintext erasure + ciphertext decryptable by a surviving key -> insufficient;
ephemeral PKE + state-complete absorbing barrier             -> PECC for OD3.
```

The primary `Eph(C)` route assumes PECC directly and keeps point values out of the
public transcript. Receiver-ephemeral encryption is an implementation route for PECC
when the channel or its buffers expose ciphertext to the adversary; its secret key and
plaintext must still be included in the atomic erase event, and a retired label cannot
register a replacement endpoint key. This separation prevents the proof from claiming
that forward secrecy alone supplies retirement finality.

**Channel failure lemma.** If a channel implementation leaves either a decryptable
in-flight ciphertext or the delivered scalar in a corruption-visible buffer after the
barrier, then an adversary corrupting that receiver immediately after the barrier
recovers the scalar without violating the instantaneous corruption bound. Hence (OD3)
and the `RCL-Sim/AO` theorem fail independently of the sharing or aggregate-encryption
primitive.

### 19.30 APSS/ACSS interface verdict

The APSS paper separates its ACSS sharing API from the later public
commitment-revelation step. Its ACSS definition gives every correct receiver a scalar
share and a Feldman commitment, while its `GenZeroPoly` protocol additionally reveals
group encodings of evaluations and DLEq proofs. The distinction matters for FGSR.

| condition | APSS/ACSS evidence | verdict for `Eph(C)` |
|---|---|---|
| PC1 | pairwise private authenticated channels and local scalar delivery | reusable, subject to ephemeral endpoint protection |
| PC2 | public Feldman coefficient commitments; `GenZeroPoly` also has a public evaluation-revelation mode | conditional: use ACSS only, suppress scalar/evaluation revelation, and keep commitments verification-only |
| PC3 | ACSS completeness makes every correct receiver eventually hold the same committed share | reusable |
| PC4 | each receiver verifies its own share against the public commitment | reusable |
| long-lived adaptive privacy | APSS uses a static corruption game and excludes reconstruction-started executions | not reusable as an FGSR security theorem |

Thus the concrete candidate is not the APSS protocol as published. It is the
APSS-style ACSS transport with the public evaluation-revelation mode removed, wrapped
by `Eph(C)`, and used only for a single frontier-bound helper polynomial. This keeps
the group-valued commitment as a verification object; it does not turn `g^{f_h(j)}`
into a scalar recovery share. The candidate passes the interface audit only if the
implementation and proof expose no alternate public evaluation encoding and the
corruption oracle includes channel buffers and endpoint state.

This verdict also fixes the role of APSS in the paper: APSS supplies a plausible
availability and local verification substrate, while `Eph(C)` supplies the transcript
and erasure interface needed by `RCL-Sim/AO`. The generation-local adaptive composition,
retirement closure, and cross-coordinate isolation remain separate theorems; none is
inherited from APSS's static secrecy lemma.

### 19.31 Conditional BF-RPTA instantiation theorem

We can now state the first complete conditional instantiation without claiming that
an existing ACSS paper already proves FGSR. Let `FGSR-PVOD(C)` use the PVOD/AVID layer
`C` for each frontier-bound helper instance, public-validity `AVAIL` receipts, and the
BF-RPTA state transition rules. Assume:

1. `Common-H` is complete and available for every accepted descriptor. Its output,
   interpolation set, and Lagrange coefficients are uniquely determined by the
   pre-challenge context and the authenticated frontier.
2. `C` satisfies `D1`--`D6`, and Theorem 63 bounds its opaque-delivery error in
   generation `r` by `Adv_ACSS-opaque^r`.
3. The helper equality proof that binds `f_h(0)` to `F^r(h)` is sound and has a
   simulator with distinguishing error `Adv_Eq-Simulation^r`. The proof is used only
   to validate the helper relation; it does not reveal an evaluation.
4. The private channel and all corruption-visible channel buffers satisfy `PECC`,
   with error `Adv_PECC^r`, and plaintext, ephemeral keys, helper coefficients, and
   pending endpoint state are erased atomically at the prescribed barrier.
5. Every installed share and receipt is bound to `(sid,ell,generation,frontier)`;
   stale messages cannot install a share or reopen a retired instance. A violation
   is charged to `Adv_Generation-Binding`.
6. Proof metadata satisfies the proof-noninterference condition of 19.26, and the
   typed capability isolation condition of that section holds. Thus cross-coordinate
   operations can produce only `ProofMeta` or data-plane objects already declared in
   the `Joint-AO^mob` context.
7. The complete data plane satisfies `Joint-AO^mob` for the accepted update vectors and
   the adaptive prefix context. State-layer failures are bounded by
   `Adv_State-Commitment`, affine-coupling failures by `Adv_Affine-Coupling`, and
   context or correctness failures by `Adv_Context/Correctness`.
8. The retired-coordinate state satisfies the three localization conditions of 19.52:
   no retired-local recovery material remains in future `StateView` (`L1`), retained
   global recovery authority cannot reconstruct it (`L2`), and every surviving
   `Use/PartDec` path performs a frontier-bound retired-label check (`L3`). Violations
   are bounded by `Adv_Recovery-Localization` and `Adv_Frontier-Use`.

**Theorem (conditional BF-RPTA instantiation).** Under the above assumptions, for
every causal generation-bounded mobile adversary and every polynomial number `R` of
helper generations,

```text
Adv_Privacy-Finality(FGSR-PVOD(C))
  <= Adv_Joint-AO^mob
     + Adv_Affine-Coupling
     + Adv_State-Commitment
     + Adv_Generation-Binding
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + Adv_Context/Correctness
     + sum_{r=1}^R (
         Adv_ACSS-opaque^r
         + Adv_Eq-Simulation^r
         + Adv_PECC^r
       )
     + R*negl(lambda).
```

**Proof sketch.** Apply the local-to-global Retirement-Closure corollary (19.22)
to each causal generation interval. The one-step simulator of 19.24 replaces the
ACSS transcript, equality proof, receipts, and endpoint exposure by their
challenge-independent state view; the three per-generation interface terms bound
these replacements. Generation binding prevents a delayed transcript from crossing
an installation or retirement barrier. The atomic erase event and PECC remove the
only receiver-local point-value edge after the barrier, while Common-H and typed
capability isolation prevent repair and cross-coordinate control flow from creating
another scalar opening edge. The remaining accepted data-plane objects are
challenged once, jointly, by `Joint-AO^mob`; affine coupling handles the terminal
retirement relation. A hybrid over the `R` generations gives the stated sum and the
negligible accumulation term.

The `L1--L3` conditions remove the two wrapper-level resurrection paths isolated by
Propositions 22--23. If a candidate cannot establish them, the corresponding
`Adv_Recovery-Localization` or `Adv_Frontier-Use` term remains in the theorem and the
candidate cannot claim privacy finality. The theorem is therefore conditional in three
cryptographic interfaces (opaque ACSS delivery, helper-proof simulation, and
post-erasure channel confidentiality) and two state/data interfaces (`L1--L3`). It does
not invoke the APSS global-refresh theorem, its static corruption game, or its
reconstruction secrecy claim. Hence 19.31 is a sound bridge from the abstract FGSR
theorem to a candidate implementation, not a claim that APSS alone already realizes
long-term privacy finality.

### 19.32 Formal FGSR wrapper and state-complete resharing

This section fixes the first protocol-level witness used by the conditional theorem.
It separates algebraic correctness from the opaque-transport assumptions of
19.28--19.31.

Let `c=(sid,ell)` be a live coordinate at generation `r`. The current sharing is a
polynomial `F^r` of degree at most `2f`, with secret `s=F^r(0)` and local state
`z_j=F^r(j)` at committee member `j`. A repair request for target `u` carries the
authenticated context

```text
Q=(rid,c,cfg,r,T_req,C_F^r,u).
```

`C_F^r` binds the current sharing and `T_req` is the frontier snapshot at which the
request was authorized. The request is rejected if `c` is already retired or if its
generation is not locally current.

The wrapper has four logical operations:

```text
1. Authorize(Q):
     run validated ACS among P^- = P \ {u};
     V <- ACS(Q, {ValidDesc_h});
     H <- Canonical_{2f+1}(V).

2. ParallelReshare(Q,H):
     each h in H defines f_h(X)=z_h + sum_{k=1}^{2f} a_{h,k} X^k;
     prove, without revealing z_h, that f_h(0)=F^r(h);
     deliver f_h(j) to receiver j through the opaque ACSS interface.

3. ReshareAggregate(Q,H):
     lambda_h <- Lagrange coefficient of h at zero over H;
     z'_j <- sum_{h in H} lambda_h f_h(j).

4. Install(Q):
     install (F', r+1, C_F^{r+1}, T_req) only if the local frontier does not
     dominate T_req and all required authenticated receipts are present;
     otherwise discard the pending output. Erase old shares, coefficients,
     plaintext subshares, and endpoint state atomically at the barrier.
```

The public transcript of `ParallelReshare` contains only commitments, proof metadata,
availability evidence, and frontier-bound receipts. It contains neither `z_h` nor any
receiver evaluation. The protocol may retain `C_F^{r+1}` and the new local evaluation,
but it does not retain the old helper polynomial or a recovery polynomial. A retirement
frontier that dominates `T_req` prevents both `Install` and any later interpretation
of the pending transcript as current state.

For the recovery path, publication and processing are separate events. A public
`KEYREVEAL` is charged to the adversarial view when it is sent into the transcript. A
receiver may later reject the same message because the coordinate has become `Retired`,
but that rejection does not erase the already published key or any point derivable from
it. Conversely, a `KEYREVEAL` whose send event occurs after the retirement frontier is
not a valid recovery edge and is not published as an accepted protocol message. This is
the protocol-level realization of the `F_AWF` `Publish/Process` interface.

For the hiding-commitment variant, a receiver also needs a local way to check its
evaluation. If the coefficient commitments are

```text
C_k = g^{a_k} h^{rho_k},
```

then the evaluation commitment at receiver `j` is

```text
C_F(j) = product_k C_k^{j^k}
       = g^{F(j)} h^{R(j)},
R(j)   = sum_k rho_k j^k.
```

The ACSS delivery therefore includes either the opening pair `(F(j),R(j))` over the
receiver-specific private channel or a receiver-local proof of knowledge of `R(j)` for
the claimed `F(j)`. Neither object is published in `READY`; both are erased with the
pending subshare. A public evaluation opening would violate the opaque-transcript
condition.

**Lemma 7 (algebraic state completeness).** Suppose `|H|=2f+1`, every accepted
descriptor binds `f_h(0)=F^r(h)`, and every correct receiver obtains the same committed
evaluation `f_h(j)` for every `h in H`. Then all correct receivers compute evaluations
of one polynomial `F^{r+1}` of degree at most `2f`, and

```text
F^{r+1}(0) = F^r(0).
```

The resulting local state is sufficient for a subsequent repair instance with the
same interface: it consists of one evaluation of a degree-`2f` sharing, its binding
commitment, the current generation, and the frontier metadata. No coefficient of an
earlier `f_h` is needed.

**Proof.** Let `lambda_h` be the Lagrange coefficient at zero for `h` in `H`, and
define

```text
F^{r+1}(X) = sum_{h in H} lambda_h f_h(X).
```

Each `f_h` has degree at most `2f`, so the same holds for `F^{r+1}`. Since the
coefficients interpolate at zero,

```text
F^{r+1}(0)
  = sum_{h in H} lambda_h f_h(0)
  = sum_{h in H} lambda_h F^r(h)
  = F^r(0).
```

The common descriptor set and deterministic coefficients give every correct receiver
the same polynomial, while opaque delivery supplies its local evaluation. The new
evaluation and commitment have exactly the input shape required by the next helper
instance; the erased coefficients are not part of that interface. Atomic installation
prevents a receiver from exposing a mixed tuple containing an old generation and a
new evaluation. Hence the output is state-complete. QED

**Lemma 8 (conditional FGSR liveness).** Under the `Common-H Agreement` and
`Common-H Availability` lemmas, and assuming the frontier does not dominate `T_req`
before installation, every correct receiver eventually obtains the inputs needed for
`ReshareAggregate(Q,H)` and can install the same state-complete sharing. This remains true
when the target is the only receiver missing its old share and up to `f` non-target
members withhold messages.

**Proof.** Removing the target leaves `3f+1` ACS participants, of which at least
`2f+1` are correct. The availability certificate and ACSS completion condition make
each accepted helper evaluation eventually available to every correct receiver,
including the target. By Common-H agreement, all correct receivers use the same
`H` and hence the same interpolation coefficients. They therefore compute the same
`F^{r+1}` and install it whenever the frontier guard remains open. The proof uses
availability of the selected instances, not a claim that Byzantine helpers are
honest; a Byzantine descriptor without the required completion evidence is excluded
by `ValidDesc_h`. QED

These two lemmas close the algebraic and availability part of the first FGSR witness.
They do not close privacy finality: delayed transcript exclusion, atomic erasure, and
multi-generation recovery closure remain governed by 19.18--19.31.

### 19.32.1 Evaluation verification and availability-certificate lemmas

**Lemma 10 (local verification under hiding commitments).** Let `C_k` be the
coefficient commitments above and let a receiver obtain `(y,R_j)` privately. If

```text
product_k C_k^{j^k} = g^y h^{R_j},
```

then `y=F(j)` except with the binding failure probability. The receiver can verify
this relation locally without revealing `y` or `R_j` to any other receiver. The same
conclusion holds when `(y,R_j)` is replaced by a sound receiver-local proof of the
relation.

**Proof.** The left side is a commitment to `F(j)` with opening `R(j)`. An accepted
different `y` gives two openings of the same binding commitment with distinct messages,
which yields the commitment binding failure. The check is receiver-local, and the
opening pair or proof is erased with the pending subshare. QED

This lemma changes the implementation interface but not the public protocol transcript:
Pedersen hiding requires private evaluation-opening material, whereas Feldman allows a
public exponent check. The opening material is therefore part of the PECC/atomic-erase
state and must be included in the one-step simulator's receiver endpoint partition.

**Lemma 11 (black-box propagation certificate).** Let an accepted helper instance have
an `AvailCert_h` containing `2f+1` signatures from distinct non-target members of
`P^-`. Suppose an honest member signs `READY(rid,ell,generation,h,C_h)` only after
locally verifying its private evaluation opening/proof against `C_h`, and the ACSS
interface satisfies: if one correct receiver completes the instance, every correct
receiver eventually obtains the same committed evaluation. Then `AvailCert_h` implies
`AVSSComplete_h`, including delivery to the correct target.

**Proof.** At most `f` signers in the certificate are Byzantine, so at least `f+1`
signatures are honest and at least one honest receiver completed the instance before
signing. Signature unforgeability prevents the adversary from manufacturing that
honest completion evidence. ACSS propagation then gives every correct receiver the
same committed evaluation, including the target, which participates as a receiver
even though it is excluded from the ACS proposal set. The context and frontier fields
in the signed message prevent the certificate from being transferred to another
helper, generation, or repair request. QED

The lemma is conditional on an independently proved ACSS propagation property. A certificate of
`2f+1` commitments without honest receiver signatures does not imply `AVSSComplete_h`;
neither does a signature produced before local evaluation verification.

Proposition 61 later shows that local `READY` signatures plus AVID availability cannot
establish this propagation property after scalar complaint and recovery are removed. The active
candidate replaces Lemma 11 with public `R_ved` validity and AVID storage acknowledgements.

**Proposition 12 (private-channel transcript reduction).** Assume the modified
`C_APSS^opaque` transport has an ACSS transcript simulator for commitment metadata and
authenticated propagation, the hiding commitment is simulatable and binding, local
evaluation proofs are sound, and `READY` signatures satisfy the condition of Lemma 11.
Then its opaque transcript advantage satisfies

```text
Adv_ACSS-opaque(C_APSS^opaque)
  <= Adv_ACSS-Transcript-Sim
     + Adv_Commitment-Hiding
     + Adv_Evaluation-Proof
     + Adv_READY/Label-Soundness
     + Adv_Public-Evaluation-Leakage
     + negl(lambda).
```

**Proof sketch.** First replace the ACSS public metadata by its simulator output.
Replace commitments and receiver-local evaluation proofs using hiding and proof
simulation, retaining the exact state of receivers exposed before the barrier. Apply
Lemma 11 to replace each accepted certificate by the same propagation event in the
simulated execution. The only public point-bearing artifact left would be an evaluation
message; by construction it is private, and its post-barrier exposure is charged to
PECC rather than this transcript game. Any invalid context or forged receipt is charged
to the corresponding soundness term. The hybrid is valid for concurrent instances
because every simulated object is labelled by the full context. QED

This proposition is the first concrete bridge from the APSS-style skeleton to
`Adv_ACSS-opaque`; it still does not prove the existence of the required ACSS
transcript simulator for a particular implementation.

### 19.33 APSS/ACSS audit for the first FGSR instantiation

The local APSS specification and its ACSS definition provide useful evidence, but
they do not discharge the FGSR theorem. The interface audit is:

| FGSR obligation | Evidence in APSS/ACSS | Decision for `FGSR-Eph` |
|---|---|---|
| private delivery of `f_h(j)` | ACSS delivers a scalar share to each receiver and publishes a polynomial commitment | reusable only with receiver endpoint protection |
| receiver availability | ACSS termination/completeness propagate a committed share after a valid instance completes | candidate for `AVSSComplete_h`; the target-excluded wrapper must prove its certificate implies this condition |
| commitment verification | Feldman coefficient commitment lets a receiver verify its own evaluation | reusable as verification metadata |
| no public scalar opening | base ACSS keeps scalar shares local | reusable only if the later public evaluation phase is disabled |
| helper equality `f_h(0)=F^r(h)` | APSS has commitment and DLEq tools, but its zero-polynomial check is not this two-commitment relation | new proof obligation; do not claim APSS supplies it unchanged |
| post-erasure confidentiality | APSS assumes private authenticated channels and discusses deletion of old shares | not supplied; `PECC` and atomic endpoint erasure remain separate |
| long-lived adaptive composition | APSS security is stated for a static adversary and excludes reconstruction-started executions | not reusable as privacy-finality security |

Two APSS details are especially important. First, the base ACSS interface is different
from `GenZeroPoly`'s commitment-revelation phase: the latter publishes group encodings
of evaluations and DLEq proofs. Those encodings are verification objects in APSS, but
for FGSR they would be public evaluation artifacts and must be removed from the first
instantiation. Second, APSS's validity proof that an honest node has completed a share
is a plausible source for `AvailCert_h`; it becomes a FGSR certificate only after it is
bound to `(rid,cfg,sid,ell,generation,frontier)` and shown to imply delivery to the
target and every other correct receiver.

The resulting implementation decision is narrow:

```text
use APSS-style ACSS transport as C
disable public evaluation revelation
add a frontier-bound helper equality proof
assume or prove PECC for every receiver endpoint and buffer
```

If any public transcript still contains a scalar evaluation or a scalar-reconstructible
combination, it must be added to `E_rec` and the current opaque-transport theorem no
longer applies. If endpoint state remains visible after the erase barrier, the channel
failure lemma of 19.29 gives an immediate attack. If the adaptive security game cannot
be strengthened, the result must remain a conditional `FGSR-Eph(C)` theorem rather than
an APSS implementation claim.

This audit closes the question of whether an existing APSS theorem can be cited as the
missing proof: it cannot. APSS is a transport and availability candidate; the new
proof work is the frontier-bound relation, post-erasure interface, and long-lived
composition.

### 19.34 FGSR-specific Retirement-Closure theorem

We now connect the concrete four-operation wrapper of 19.32 to the abstract corollary
of 19.22. Let `c=(sid,ell)` be retired at frontier `T*`, and let
`Cap_old(c)` denote every scalar capability that can open the individual contribution
at `c`. Assume the following FGSR conditions:

1. Every descriptor, subshare, receipt, pending output, and installed state is bound
   to `(rid,c,cfg,generation,frontier)`; a local frontier dominating a request makes
   `Authorize`, `ReshareAggregate`, and `Install` reject that request.
2. A subshare is delivered only through the opaque ACSS interface. Its public
   transcript contains no scalar evaluation or scalar-reconstructible coefficient,
   and PECC covers the in-flight message, receiver buffer, plaintext, and ephemeral
   decryption state at the erase barrier.
3. `Install` is the only transition from a pending `F'` to current state. It is
   atomic with erasure of the old share, helper coefficients, pending plaintext,
   and endpoint state. A receipt or output that fails the frontier or generation
   check has no installation edge.
4. After `T*`, the retirement state machine creates no generation, extraction,
   repair, or decryption edge for `c`; handoff, if present, projects only live
   coordinates.
5. The generation-local exposure bounds and the typed capability isolation condition
   of 19.21--19.26 hold. In particular, interpolation and repair accept only equal
   coordinate and generation tags, while `Joint-AO` is the only cross-coordinate
   data-plane output.
6. At the terminal generation, the residual current state and terminal exposure
   satisfy `|U_ell union B_{ell,ret}| < q_rec`; for the first parameter point this is
   `|U_ell union B_{ell,ret}| <= 2f < 2f+1=q_rec`.

**Theorem 9 (FGSR Retirement-Closure).** Under conditions 1--6, for every admissible
post-retirement exposure set `X` and every polynomial execution prefix,

```text
Cl_FGSR(X) intersection Cap_old(c)
  = X intersection Cap_old(c)
```

except with the sum of the opaque-delivery, equality-proof, PECC, generation-binding,
state-commitment, affine-coupling, and correctness errors. Consequently, if the
pre-retirement residual view does not already contain an authorized individual
opening set, `Cl_FGSR(X)` contains no member of `Gamma_dec^cap(c)`.

**Proof.** Consider the first post-retirement derivation step that would produce a
capability in `Cap_old(c)` not already in `X`. By typed closure soundness, the step
must use one of the following final edges.

| candidate final edge | FGSR reason it cannot create a new old capability |
|---|---|
| old descriptor or `AvailCert` to a new helper instance | generation/frontier binding rejects a request dominated by `T*`; a pre-existing descriptor is already in the archived transcript |
| ciphertext or receiver endpoint to a scalar subshare | opaque delivery and PECC prevent post-barrier extraction; any scalar exposed before the barrier belongs to `X_hist` |
| pending `F'` to current state | `Install` is the only edge and its frontier guard rejects a stale request; an accepted pre-retirement install is already represented by the fresh generation state |
| residual current state to a new repair or decryption share | condition 4 removes every such edge for `c`; the residual state is exposure, not a legal post-retirement transition |
| objects from another generation or coordinate | typed tags reject interpolation/repair, and proof-noninterference plus `Joint-AO` excludes an individual opening edge |

The only remaining possible source is direct exposure by the corruption oracle, which
is part of `X` by definition. Therefore no first post-retirement edge can enlarge
`X intersection Cap_old(c)`. Induction over the finite derivation prefix gives the
equality. The terminal bound in condition 6 prevents the residual current state from
forming a `q_rec`-sized recovery set even in an implementation that exposes all
surviving state; the generation tags prevent shares from other intervals being
combined as if they belonged to one polynomial. The listed advantage terms account
for violations of the corresponding interface assumptions. Finally, applying the
Repair-Closure characterization to every authorized set yields the stated privacy
consequence. QED

The theorem identifies the exact remaining implementation burden. The frontier and
state-machine cases are closed by FGSR's wrapper; the cryptographic cases are not
inherited from APSS and must establish the three interfaces audited in 19.33.

### 19.35 Three cryptographic interfaces as explicit security games

The names `AVSS-opaque`, `EqualityProof`, and `PECC` are not interchangeable
assumptions. The following games fix what each one hides, what the adversary may
observe, and which failure is charged to the conditional theorem.

#### 19.35.1 Opaque ACSS game

For one helper instance with context
`ctx=(rid,sid,ell,cfg,generation,frontier,h)`, define two view experiments.
`G_O^real` runs the ACSS protocol honestly for the correct receivers and lets the
adversary control the asynchronous schedule and up to `f` Byzantine parties. The
corruption oracle returns a receiver's scalar point if that receiver is corrupted
before its instance erase barrier. At or after the barrier it returns only the state
that the protocol specifies as surviving. The adversary sees all public messages,
including commitments, validity metadata, availability certificates, and receipts.

`G_O^sim` gives a simulator the same public context, public commitments, the states
explicitly exposed before the barrier, and the prescribed residual state. The simulator
does not receive any unexposed receiver evaluation. It produces the public transcript,
receipts, and post-barrier corruption responses. The experiments use the same
adversarial schedule and the same authenticated validity decisions. Define

```text
Adv_ACSS-opaque(C) =
  max_S | Pr[S(View_O^real)=1] - Pr[S(View_O^sim)=1] |.
```

The game includes the following functional predicates, which are not themselves
indistinguishability claims:

```text
O1  public transcript contains no scalar evaluation or reconstructible coefficient;
O2  each receiver obtains only its own committed evaluation through its channel;
O3  one valid completion implies eventual consistent delivery to every correct receiver;
O4  a receiver can verify its point without opening another receiver's point;
O5  after the barrier no recovery operation returns a new public scalar opening edge.
```

`O1`--`O5` must hold for every accepted descriptor, including a Byzantine helper that
passes the external validity predicate. A protocol satisfying only agreement and
availability but exposing `g^{f_h(j)}` or a reconstructible coefficient fails this
interface even if its ordinary ACSS theorem remains true.

#### 19.35.2 Helper equality-proof game

Let `C_F(h)` commit to the current evaluation `z_h=F^r(h)` and let `C_f(0)` commit
to the constant term of helper polynomial `f_h`. For a Pedersen-style commitment,
the relation is

```text
R_eq((C_F(h),C_f(0),ctx); z,r_F,r_f)
  iff C_F(h)=Com(z;r_F) and C_f(0)=Com(z;r_f).
```

The proof system must provide three separately recorded properties:

```text
Eq-Sound:       a false R_eq statement is accepted only with negligible probability;
Eq-MultiSim:    concurrent, adaptively labelled true transcripts are simulatable
                without the hidden z and opening randomness;
Eq-Noninterference: verification returns only proof metadata and cannot select an
                    undeclared individual ciphertext, partial decryption, or repair edge.
```

`G_E^real` samples a valid helper relation and runs the real prover. `G_E^sim` uses
the simulation setup and `SimProve` on the same public context and commitments, while
the hidden evaluation and openings remain unavailable to the simulator. Both games
allow polynomially many concurrent instances and preserve the same frontier labels.
Define

```text
Adv_Eq-Simulation =
  max_S | Pr[S(Transcript_E^real)=1]
           - Pr[S(Transcript_E^sim)=1] |.
```

`Eq-Sound` is charged to `Adv_State-Commitment` or a separate soundness term; it is
not hidden inside `Adv_Eq-Simulation`. If the simulator needs to produce proofs for
false statements during the hybrid, the construction must use a dual-mode/simulation
CRS whose indistinguishability is added explicitly. Ordinary honest-statement
zero-knowledge is not enough to justify that hybrid.

#### 19.35.3 Post-erasure channel game

Let `e=(Q,h,j)` be one receiver endpoint with label
`L=(rid,sid,ell,generation,frontier,h,j)`, and let `tau_j` be the local linearization point
at which receiver `j` accepts the ordered installation or retirement barrier. In
`G_P^b(e)`, the adversary chooses equal-length valid payloads `m_0,m_1`, the challenger
sends `m_b`, and the adversary controls delivery order, delay, and public network
observations. The challenge endpoint must remain uncorrupted before `tau_j`; if it is
corrupted, the game aborts with a random output and the outer AOR experiment records the
real endpoint state in `X_hist` instead.

At `tau_j`, the endpoint performs the prescribed local erase. After `tau_j`, the
corruption oracle reveals the complete residual endpoint state, including the in-flight
network state, archived ciphertext, receiver buffer, plaintext workspace, decryption
state, and verification workspace that actually remain. The adversary may continue to
deliver the archived ciphertext. Key registration, decryption, recovery, and installation
for `L` are rejected after the barrier by the state machine. The adversary outputs a guess
for `b`.

```text
Adv_PECC(Ch) =
  max_A | Pr[A(G_P^0)=1] - Pr[A(G_P^1)=1] |.
```

The game treats endpoint state as part of the channel while leaving public network bytes
intact. Thus a recorded ciphertext that remains decryptable after `tau_j`, a buffered
plaintext, a regenerated endpoint key, or an erased-key failure is a direct PECC failure.
Authentication and label integrity are separate properties: they prevent cross-instance
installation but do not by themselves hide a scalar after the barrier. PECC covers only
an endpoint that reaches its barrier without prior corruption. A pre-barrier endpoint
corruption is recorded in `X_hist`; helper polynomial state is handled by the generation
exposure budget and state-complete helper erasure. This partition lets PECC use a standard
encryption reduction without claiming a simulator that can later open the challenge
ciphertext under a pre-barrier corruption.

#### 19.35.4 Per-generation composition

For a generation `r`, the one-step transcript transition can now be charged as

```text
Adv_Transcript-Hiding^r
  <= Adv_ACSS-opaque^r
     + Adv_Eq-Simulation^r
     + Adv_PECC^r
     + Adv_State-Commitment^r
     + Adv_Generation-Binding^r
     + Adv_Affine-Coupling^r
     + Adv_Uncovered-Edge^r
     + negl(lambda).
```

The first three terms correspond to the three games above. `Adv_Uncovered-Edge` is
zero only after the public-output table of 19.24/19.25 is exhaustive and the typed
isolation lemma of 19.26 applies. A hybrid over causally ordered generations sums
these terms; it does not turn static APSS secrecy into adaptive long-lived secrecy.

This game separation gives a concrete audit rule. A candidate implementation may claim
the conditional FGSR theorem only after it supplies a reduction or standard theorem
for each game and a functional proof of `O1`--`O5`. Failing one game narrows the claim
to the abstract theorem; it does not justify replacing the missing interface with
forward-secure encryption alone.

### 19.36 APSS-style ACSS candidate reduction ledger

The first concrete candidate is not the APSS protocol verbatim. Denote by
`C_APSS^opaque` the ACSS delivery and propagation skeleton exposed by APSS, with its
global `GenZeroPoly` commitment-revelation phase removed, its public commitment layer
replaced by a simulation-friendly hiding commitment where needed, and its output
wrapped in the frontier-bound `READY` interface.

| FGSR condition | APSS evidence | Reduction to the candidate | Remaining obligation |
|---|---|---|---|
| `PC1` / `O2` | ACSS delivers a scalar share to a receiver over a private authenticated channel | direct functionality mapping from `share_h(0,d)` to `f_h(j)` | prove endpoint and buffer treatment separately; private-channel syntax alone is not PECC |
| `PC2` / `O1` | base ACSS publishes Feldman coefficient commitments; `GenZeroPoly` later reveals group evaluations | disable the revelation phase; expose only commitment metadata and certificates | show no alternate implementation message contains a scalar or reconstructible coefficient |
| `PC3` / `O3` | ACSS completeness says that a completed valid instance propagates one committed polynomial to every correct receiver | `READY` from a valid completed instance implies `AVSSComplete_h` and hence target availability | prove the certificate-to-propagation reduction for Byzantine dealers and target-excluded ACS |
| `PC4` / `O4` | Feldman commitments allow local evaluation checking | direct local verification mapping | if hiding simulation needs Pedersen commitments, prove the modified commitment preserves binding and local checking |
| helper equality | APSS DLEq proves a different exponent relation in `GenZeroPoly` | no direct reduction | prove the two-opening message-equality relation for `C_F(h)` and `C_f(0)` |
| public-transcript simulation | APSS states static secrecy but does not give the FGSR simulator | use commitment hiding plus ACSS transcript simulation | establish `Adv_ACSS-Transcript-Sim` under adaptive labels and concurrent instances |

The distinction between Feldman and Pedersen commitments is substantive. Feldman
commitments are useful for local verification and may be scalar-free under a discrete
logarithm assumption, but their public values cannot automatically be replaced by a
simulator that does not know the committed evaluation. If the one-step hybrid needs
such a replacement, the first candidate must use a hiding commitment (for example,
Pedersen coefficient commitments) and prove that its evaluation commitment remains
binding and locally verifiable. This is a modification of the commitment layer, not a
claim inherited from APSS.

**Conditional ACSS bridge.** Suppose `C_APSS^opaque` has APSS-style termination,
completeness, and authenticated propagation; its public transcript has no evaluation
revelation; its commitment/proof transcript is simulatable without unexposed scalar
values; and the `READY` certificate is sound and frontier-bound. Then

```text
Adv_ACSS-opaque(C_APSS^opaque)
  <= Adv_ACSS-Transcript-Sim
     + Adv_Commitment-Hiding
     + Adv_READY/Label-Soundness
     + Adv_Public-Evaluation-Leakage
     + negl(lambda).
```

For a construction that literally removes every public evaluation message,
`Adv_Public-Evaluation-Leakage=0`; it must not be silently replaced by the APSS
`GenZeroPoly` revelation proof. The bridge is functional for Byzantine helpers only
when a valid `READY` certificate implies that one honest receiver completed the same
ACSS instance and ACSS propagation then reaches all correct receivers. A certificate
that merely counts commitments does not satisfy the bridge.

This ledger fixes the first implementation decision: use APSS as evidence for the
asynchronous delivery/propagation skeleton, but introduce a hiding commitment and a
new equality-proof relation if the simulator requires them. Until the four remaining
advantages in the bound are reduced, `C_APSS^opaque` remains a candidate interface,
not a concrete instantiation of the BF-RPTA theorem.

### 19.38 Concrete candidate audit: `hbACSS0 + hbPolyCommit`

The local `hbACSS` and Haven++ specifications expose a stronger candidate for the
first proof than APSS alone. We select the univariate `hbACSS0` path, not the packed
Haven++ path, because the first FGSR theorem forbids shared higher-degree coefficients
and packed cross-coordinate state.

Define

```text
C_hb0^opaque =
    hbACSS0 delivery and READY amplification
  + hbPolyCommit evaluation proofs
  + receiver-ephemeral encryption
  + frontier-bound labels and no post-frontier share recovery.
```

The candidate audit is:

| FGSR interface | `hbACSS0` evidence | Required adaptation |
|---|---|---|
| `PC1` / `O2` | encrypted per-receiver payloads are dispersed and decrypted locally | replace long-term receiver keys by per-instance ephemeral keys, or prove the key state is included in PECC |
| `PC2` / `O1` | public polynomial commitments and AVID metadata; scalar payloads are encrypted | exclude any public evaluation-revelation phase and audit AVID metadata for scalar-reconstructible data |
| `PC3` / `O3` | `OK`/`READY` amplification and `2f+1` READY completion imply enough correct receivers possess valid shares | bind READY to the full FGSR context and use Lemma 11 for target availability |
| `PC4` / `O4` | `hbPolyCommit` supplies evaluation proofs and strong evaluation binding | prove the receiver-local verification transcript is simulatable and does not publish an evaluation |
| transcript simulation | hbACSS gives an explicit honest-dealer simulator based on corrupted shares and commitment hiding | strengthen from static key exposure to generation-local exposure and concurrent frontier labels |
| recovery | share recovery reconstructs missing shares after an implication proof and may reveal receiver keys | forbid recovery after a dominating frontier; a pre-frontier recovery must finish or be erased before retirement |

The recovery row is not a minor implementation detail. In the original hbACSS protocol,
an implication proof can trigger key disclosure so that other parties decrypt a valid
payload and reconstruct a missing share. If that key-disclosure path remains valid after
`T*`, an old AVID ciphertext becomes a post-retirement scalar-opening edge and violates
`OD4`. The FGSR wrapper therefore accepts recovery only under
`T_local <= T_req` and rejects all implication, key-reveal, and recovery messages once
the retirement frontier dominates the instance. This converts the original recovery
mechanism into a live-coordinate operation covered by `Cl_rec`, while retired
coordinates have no recovery edge.

**Candidate bridge.** Under the hbACSS transcript simulator, computational hiding and
binding of `hbPolyCommit`, sound evaluation proofs, semantically secure ephemeral
encryption, and the frontier recovery gate,

```text
Adv_ACSS-opaque(C_hb0^opaque)
  <= Adv_hbACSS-Transcript-Sim
     + Adv_hbPolyCommit-ZK/Binding
     + Adv_Ephemeral-PKE-INDCPA
     + Adv_Recovery-Gate
     + Adv_READY/Label-Soundness
     + Adv_Public-Evaluation-Leakage
     + negl(lambda).
```

This is a candidate-specific bridge, not a claim that the hbACSS theorem already
handles adaptive mobile corruption or post-erasure exposure. The original proof's
static corrupted-key simulator supplies a starting reduction only; the missing work is
to replace its static corrupted-key set by the causal generation exposure partition
and to prove that all revealed recovery keys are erased or included in the pre-barrier
view. Haven++ remains a component and packing reference, not the first FGSR instance.

### 19.39 Frontier-gated hbACSS recovery

The original hbACSS recovery path is represented by the following abstract messages
for a context `Q=(rid,cfg,sid,ell,generation,T_req,h)`:

```text
IMPLICATE(Q,j,evidence)       // claims that receiver j cannot validate its payload
KEYREVEAL(Q,j,K_j)             // discloses the key needed to inspect j's payload
RECOVER(Q,j,share_j,proof_j)   // supplies or reconstructs j's missing share
```

The unmodified protocol accepts these messages during share recovery after an
implication proof. FGSR replaces that rule by the monotone predicate

```text
AcceptRecovery(Q,m,state) iff
    state.coordinate == (sid,ell)
    and state.generation == generation
    and state.frontier <= T_req
    and state.mode in {Live, Recoverable}
    and VerifyContext(Q,m) = 1.
```

The retirement transition is an absorbing state transition:

```text
Retire(c,T*) atomically:
    state.mode <- Retired;
    state.frontier <- max(state.frontier,T*);
    erase receiver ephemeral keys, pending plaintext, and helper recovery state;
    reject all later IMPLICATE, KEYREVEAL, and RECOVER messages for c.
```

An implication or key-reveal message created before `T*` but delivered after `T*` is
not accepted merely because its signature and payload were valid before retirement.
If its key was already publicly revealed before `T*`, the resulting capability belongs
to the pre-retirement view `X` and is charged to the generation exposure budget; if it
was not revealed, the post-frontier gate prevents it from becoming a new derivation
edge. This is the precise distinction between delayed transcript exposure and stale
state installation.

**Lemma 13 (live-coordinate recovery).** If `state.mode` is `Live` or `Recoverable`,
`T_req` is not dominated by the local frontier, and the hbACSS implication evidence
is valid, the original share-recovery liveness argument remains available. In
particular, valid shares from at least `f+1` correct receivers can be used to recover a
missing receiver evaluation, subject to the underlying hbACSS availability and
evaluation-binding assumptions.

**Proof.** The gate does not change the original hbACSS `OK`/`READY` or recovery
transition while the context remains live. The original availability argument gives
at least `f+1` correct valid-share holders after a valid implication event; evaluation
binding makes their recovered polynomial consistent with the public commitment. The
frontier and generation checks only reject messages from a different instance. QED

**Lemma 14 (retired-coordinate recovery exclusion).** If `state.mode=Retired` with
frontier `T*`, then no accepted `IMPLICATE`, `KEYREVEAL`, or `RECOVER` message creates
an edge from a pre-retirement AVID ciphertext or pending payload to a new scalar
capability for `c`.

**Proof.** Every such message fails `state.frontier <= T_req` or the mode check once
`T*` dominates its request. A message accepted before retirement is already part of
the pre-retirement view or the installed fresh generation; a message delayed across
the barrier is rejected. The only remaining route is corruption of receiver state,
which returns either a state explicitly retained in `X` or no erased key/plaintext by
PECC. Thus the gate adds no post-retirement recovery edge. QED

**Theorem 10 (frontier-gated hbACSS recovery).** Assume hbACSS0's agreement,
availability, and evaluation-binding properties; authenticated context labels; PECC
for receiver-ephemeral payloads; and atomic retirement erasure. Replacing its recovery
rule by `AcceptRecovery` preserves live-coordinate recovery liveness and gives

```text
E_rec^{hb0}(c, post-T*) intersection Cap_old(c)
  subseteq X intersection Cap_old(c),
```

for every retired coordinate `c`, except with
`Adv_Recovery-Gate + Adv_READY/Label-Soundness + Adv_PECC + Adv_Evaluation-Proof`.

**Proof sketch.** Apply Lemma 13 before the retirement barrier. At the barrier, apply
Lemma 14 to every pending implication, key-reveal, and recovery message, including
messages already signed but not yet delivered. PECC removes receiver-side plaintext
and ephemeral-key edges; the gate rejects all other old-payload transitions. The
remaining pre-barrier public keys or recovered shares are already in `X` and are not
newly generated by the post-barrier execution. Induction over the post-retirement
event prefix yields the inclusion. QED

The theorem does not claim that hbACSS's original long-term-key variant is secure. It
requires per-instance endpoint protection or an equivalent PECC implementation, and it
turns share recovery into a live-coordinate-only operation. This is the exact wrapper
needed before using hbACSS's transcript simulator in the FGSR Retirement-Closure proof.

### 19.40 Generation-local hbACSS simulator

The hbACSS proof simulator is stated for a static set of corrupted decryption keys.
FGSR needs a conditional lifting to a causal generation interval. Let
`B_r=B_{ell,r}` be the set of parties whose current share, helper state, receiver
plaintext, ephemeral key, or accepted recovery key is exposed before the next barrier
in generation `r`. Let `U` be the state surviving the final retirement barrier. The
generation-local simulator receives only

```text
(PublicContext_r, B_r-state, X_hist^r(B_r), X_current(U), previous simulated view).
```

It does not receive unexposed helper coefficients, receiver plaintexts, or ephemeral
keys. It executes the following conditional hybrid:

```text
1. Fix B_r from the preceding simulated prefix and check |B_r| <= f.
2. Run the hbACSS static simulator with B_r as the exposed-key set, preserving
   all shares and recovery keys that the real corruption oracle would reveal there.
3. Replace unexposed public commitments, evaluation proofs, and ciphertexts using
   hbPolyCommit hiding/ZK and ephemeral-PKE simulation.
4. Include every pre-frontier accepted KEYREVEAL in X_hist^r(B_r); reject every
   delayed key-reveal or recovery message after a dominating frontier.
5. Erase simulated receiver endpoint state and helper coefficients at the barrier,
   then hand only generation-tagged current state to the next interval.
6. Apply the cross-generation affine coupling while preserving all exposed points,
   equality relations, and the accepted F' transition.
```

The lifting requires an identity-agnostic simulator: it must work for any adaptive
choice of `B_r` made from the prior view, not only for a fixed first set of parties.
It must also simulate concurrent instances whose labels differ in `rid`, coordinate,
generation, and frontier. A static simulator that hard-codes the first `f` keys is not
enough, because a mobile adversary may expose a different set in every interval.

**Proposition 15 (conditional generation-local simulation).** Suppose the hbACSS
simulator remains valid for every pre-barrier exposed set of size at most `f`, its
commitment/evaluation proofs support concurrent labelled simulation, receiver-ephemeral
PKE satisfies the pre-barrier transcript hybrid, and the recovery gate of Theorem 10
is sound. Then for `R` causally ordered generations,

```text
Adv_hb0-GenSim^R
  <= sum_{r=1}^R (
         Adv_hbACSS-StaticSim^r
       + Adv_hbPolyCommit-ZK^r
       + Adv_Ephemeral-PKE^r
       + Adv_Recovery-Gate^r
       + Adv_PECC^r
       )
     + Adv_Generation-Binding
     + Adv_Affine-Coupling
     + R*negl(lambda).
```

**Proof sketch.** Define a prefix hybrid at the first generation whose view is
simulated. At generation `r`, the preceding simulated view fixes the adaptive set
`B_r`; the assumed identity-agnostic hbACSS simulator then preserves the view of all
objects exposed to that set. Hiding and zero knowledge replace unexposed commitment
and evaluation-proof witnesses, while ephemeral-PKE security replaces ciphertexts
whose receiver keys are erased before later exposure. The recovery gate places
pre-frontier key disclosures in `X_hist^r(B_r)` and rejects all post-frontier
disclosures. PECC removes endpoint state at the barrier. The affine coupling gives the
next current sharing with the same exposed points and equality relations, and fresh
generation labels prevent the adversary from combining objects from two intervals.
Induction over `r` gives the sum. A stale label, inconsistent install, or failed gate
is charged to the corresponding error term. QED

The proposition is the exact strengthening needed from hbACSS, but it is not implied
by its original theorem. In particular, the following are open implementation-level
proof obligations: adaptive identity selection, concurrent label separation, simulation
of the AVID transcript, and erasure of every key that could trigger share recovery.
Until these are proved, `Adv_hb0-GenSim^R` remains an explicit assumption rather than a
hidden use of hbACSS's static secrecy result.

### 19.41 Typed-edge ledger for the `C_hb0^opaque` P1 audit

The static hbACSS simulator does not fail only because its corruption set is written as
```
{P_1,...,P_t}
```
instead of an adaptive set. Its simulation order also assumes that the keys used to
encrypt honest receivers can be replaced by random public strings after the corrupted
key set is known. In a mobile execution, public keys and AVID ciphertexts are already
visible before the adversary chooses the next party to expose. A generation-local
lifting therefore needs an adaptive-key interface, not just a different notation for
`B_r`.

For one repair instance `Q=(rid,sid,ell,cfg,r,T_req,h)`, define the typed objects

```text
Pub_Q      = (SP, public receiver keys, C, AVID metadata, OK/READY metadata)
Payload_i  = (Z_i, encrypted evaluation point, evaluation proof)
Point_i    = (F^r(i), R^r(i))
Key_i      = receiver secret or ephemeral decryption key for Q
Rec_i      = recovery contribution, recovery proof, or recovered Point_i
Install    = (F', generation+1, frontier update)
```

`Pub_Q` may be public, but it is not automatically a scalar capability. `Point_i`,
`Key_i`, and a valid `Rec_i` are capability-bearing objects because they can enter a
polynomial interpolation or a later recovery edge. The following ledger is the exact
partition required by the P1 reduction.

| edge | source -> target | allowed phase | simulator treatment | failure term |
|---|---|---|---|---|
| E1 | secret polynomial -> `C` | all | use commitment hiding/binding; no scalar opening in `Pub_Q` | `Adv_hbPolyCommit-Hide/Bind` |
| E2 | `Point_i` -> `Payload_i` | pre-frontier | encrypt under an instance key; if `Point_i` is exposed, place it in `X_hist^r(B_r)` | `Adv_Ephemeral-PKE` |
| E3 | `Payload_i` + `Key_i` -> `Point_i` | pre-frontier only | expose the point only when the corruption/recovery oracle exposes the key or local plaintext | `Adv_PECC` plus exposure accounting |
| E4 | `Point_i` + `C` + proof -> `READY_i` | pre-frontier | publish metadata-only receipt; `READY_i` cannot carry a scalar evaluation | `Adv_READY/Label-Soundness` |
| E5 | `IMPLICATE_i` -> `Key_i` | pre-frontier and valid implication only | charge a revealed key and its decrypted point to `X_hist^r(B_r)` | `Adv_Recovery-Gate` |
| E6 | `Key_i` + `Payload_i` -> `Rec_i` | live/recoverable only | simulate or expose recovery contribution; no edge exists after a dominating frontier | `Adv_Recovery-Gate + Adv_PECC` |
| E7 | `Rec_H` -> `Install` | live/recoverable only | accept only one Common-H and one generation/frontier context; stale output is rejected | `Adv_Generation-Binding` |
| E8 | `Install` + erase -> next current state | live transition only | apply affine coupling and pass only generation-tagged current state forward | `Adv_Affine-Coupling` |
| E9 | public proof metadata -> branch selection | all | require proof-noninterference: hidden witnesses cannot select a scalar-bearing branch | `Adv_Uncovered-Edge` |
| E10 | other coordinates -> `Point_i` or `Rec_i` | never in the first instance | forbid packed/shared-coefficient openings; route aggregate ciphertext objects to `Joint-AO` | `Adv_Cross-Coordinate` |

The ledger gives two distinct adaptive-key obligations. First, before the adversary
chooses `B_r`, the simulator must generate public keys and ciphertexts in a way that it
can later answer a corruption of any party outside the current exposed set. Second, if
that party is exposed after its frontier barrier, the simulator must not provide a key
that decrypts an old `Payload_i`. Ordinary IND-CPA for a long-term receiver key solves
neither obligation: the later key exposure directly decrypts the archived ciphertext.
The first candidate therefore requires one of the following explicit interfaces:

```text
(AK1) adaptive key generation with an extraction/erasure interface, or
(AK2) per-instance ephemeral keys plus PECC and a proof that no post-barrier key
      material can decrypt the old payload, or
(AK3) a separate adaptive threshold-encryption theorem that already covers the
      receiver-key exposure schedule and the AVID ciphertext transcript.
```

The long-term-key optimization in the hbACSS paper is not an instance of AK1--AK3:
its shared symmetric key can be recovered from a later exposed receiver secret, so it
must remain outside the FGSR theorem unless a new post-erasure channel proof is given.

**Lemma 16 (typed-edge simulation criterion).** Fix a generation-local exposure set
`B_r` with `|B_r|<=f` and a final residual state `U`. Suppose:

1. the simulator can answer public-key and AVID setup before the adaptive choice of
   `B_r` under AK1, AK2, or AK3;
2. every pre-frontier `E3`, `E5`, and `E6` output is included in
   `X_hist^r(B_r)`, while every post-frontier instance of those edges is rejected or
   covered by PECC;
3. `E4` and `E9` are metadata-only and proof-noninterfering;
4. `E7` and `E8` are bound to one generation and the affine-coupling hypothesis; and
5. no `E10` edge is available outside the already challenged `Joint-AO` view.

Then the real and simulated generation views differ by at most

```text
Adv_hb0-EdgeSim^r
  <= Adv_hbPolyCommit-Hide/Bind^r
     + Adv_Ephemeral-PKE^r
     + Adv_PECC^r
     + Adv_Recovery-Gate^r
     + Adv_READY/Label-Soundness^r
     + Adv_Generation-Binding^r
     + Adv_Affine-Coupling^r
     + Adv_Cross-Coordinate^r
     + Adv_Uncovered-Edge^r
     + negl(lambda).
```

**Proof.** Replace E1--E2 objects first, exposing the values prescribed by
`X_hist^r(B_r)` and using commitment/PKE security for the remaining objects. E3--E6
are then partitioned by whether their source key or plaintext was exposed before the
frontier. The former are already in the history view; the latter are rejected or
replaced by the PECC hybrid. E4 and E9 cannot create a scalar edge by their
metadata-only and noninterference assumptions. E7--E8 are replaced by the coupled
fresh sharing and stale-output rejection. Any object not covered by this partition is
exactly an E10 or an uncovered edge and is charged explicitly. A union bound gives the
displayed expression. QED

Lemma 16 is an audit criterion, not yet a concrete hbACSS theorem. In particular,
hbACSS's original static simulator establishes neither AK1--AK3 nor E9 for concurrent
frontier labels. Thus the first concrete go/no-go question is now: can the chosen
receiver-key and AVID realization satisfy AK2 without leaving a decryptable old
ciphertext in post-barrier state? If not, `C_hb0^opaque` must be removed as a concrete
long-term instance while the abstract FGSR theorem remains valid.

### 19.42 AK2 interface: per-instance keys and the PECC game

The only concrete key interface retained for the first candidate is AK2. It is a
per-repair-instance interface, not a long-term PKI optimization. For each context
`Q=(rid,sid,ell,cfg,r,T_req,h)` and receiver `i`, the receiver runs

```text
(pk_Q,i, sk_Q,i) <- EphKeyGen(Q,i)
Publish(pk_Q,i,Q)
```

The dealer or AVID dispersal layer creates

```text
Payload_Q,i = (Point_Q,i, EvalProof_Q,i)
ct_Q,i      = Enc(pk_Q,i, Payload_Q,i; Q)
```

where `Q` is authenticated context, not a secret input. Publicly retained AVID state
may contain `ct_Q,i`, delivery metadata, and availability evidence. It may not contain
`Point_Q,i`, `sk_Q,i`, an evaluation opening, or a recovery-complete scalar. A `READY`
receipt contains only the context and acceptance metadata.

The endpoint state machine is defined by the following transitions:

```text
Absent(Q,i) -> Prepared(Q,i)
    only after Q is ordered, its frontier is live, and pk_Q,i is registered;

Prepared(Q,i) -> Delivered(Q,i)
    after local decryption and evaluation verification;

Prepared/Delivered(Q,i) -> Recoverable(Q,i)
    only after a valid pre-frontier implication and a live recovery context;

Absent/Prepared/Delivered/Recoverable(Q,i) -> Retired(Q,i,T*)
    atomically when the coordinate accepts T*.
```

The retirement transition performs the semantic operation

```text
mode <- Retired
frontier <- max(frontier,T*)
erase(sk_Q,i, pending plaintext, local evaluation opening,
      unreleased recovery key material, and endpoint buffers)
```

`Retired` is absorbing. In particular, an endpoint that was still `Absent` at the barrier
cannot run `EphKeyGen` or register a public key for the retired label afterward.

The AVID store is allowed to retain `ct_Q,i`; retaining the ciphertext is not itself a
privacy violation. The required property is that no legal post-frontier edge can use
the retained ciphertext to obtain `Point_Q,i` or a recovery contribution. A key reveal
that is accepted before `T*` is different: its key, decrypted point, and all resulting
recovery material enter `X_hist^r(B_r)` and are never removed from the adversary view.

**PECC game.** In the post-erasure channel game for `Q`, the adversary receives all
public commitments, AVID metadata, ciphertexts, receipts, and messages. The challenge
endpoint remains uncorrupted until its local barrier; an earlier corruption moves that
endpoint to the real `X_hist` branch of the outer AOR game. A corruption after the barrier
receives the complete actual post-erasure state, including retained ciphertext and buffers,
but no erased `sk_Q,i`, plaintext, or verification opening. The challenger rejects endpoint
registration, key reveal, decryption, and recovery after `Retired(Q,T*)`.

For every payload whose key and plaintext were not exposed before `T*`, the challenger
replaces the encrypted payload by an equal-shape simulated payload while preserving
public context and metadata. Endpoints exposed before their barrier remain real. The PECC
advantage is the distinguishing advantage of the replacement over the surviving challenge
endpoints. Evaluation-proof simulation is a separate term; PECC does not claim that a
proof containing a hidden witness is automatically simulatable.

**Lemma 17 (AK2 post-frontier edge exclusion).** Suppose `EphKeyGen` uses a fresh key
for every `Q`, the PECC game is secure under the stated adaptive corruption schedule,
all valid pre-frontier key reveals are included in `X_hist^r(B_r)`, and
`IMPLICATE/KEYREVEAL/RECOVER` are accepted only in `Live/Recoverable` mode. Then for
every retired coordinate `c`,

```text
Cl_rec(X_hist^r(B_r) union State_after(T*)) intersection Cap_old(c)
  = X_hist^r(B_r) intersection Cap_old(c),
```

except with advantage `Adv_PECC + Adv_Recovery-Gate + Adv_Evaluation-Proof`.

**Proof.** Consider a derivation of an old capability after `T*`. If its last edge is
an accepted implication, key reveal, or recovery operation, the mode/frontier check
rejects it, contributing `Adv_Recovery-Gate`. If its last edge uses a public proof or
metadata, evaluation-proof simulation and the metadata-only receipt condition remove
the scalar witness. Otherwise it must use a retained AVID ciphertext together with a
post-barrier endpoint state. The endpoint state contains no `sk_Q,i` or plaintext, so
the PECC replacement removes this edge. If the endpoint was still `Absent` at the barrier,
absorption prevents later key registration; if it was `Prepared`, the registered secret key
is erased. Any key or point exposed before `T*` was already in `X_hist^r(B_r)`, and
therefore does not enlarge the closure. Induction over the derivation length proves the
equality. QED

Lemma 17 is deliberately narrower than a full adaptive hbACSS theorem. It closes the
specific receiver-key resurrection edge under AK2; it does not prove adaptive AVID
simulation, concurrent proof simulation, or aggregate-only `Joint-AO`. Those remain
separate terms in Lemma 16 and Proposition 15. Standard IND-CPA with a persistent
receiver key, including the long-term-key optimization in the hbACSS paper, does not
satisfy the premise of Lemma 17.

### 19.43 Adaptive AVID and commitment barrier

The hbACSS AVID interface is not a privacy primitive. Its definition guarantees
termination, agreement, availability, and correctness of the dispersed value; the
hbACSS secrecy proof explicitly allows the adversary to see every AVID message. This is
compatible with opaque ciphertexts, but it does not by itself provide an adaptive
transcript simulator.

There are two separate adaptive issues.

**(A) Adaptive receiver exposure.** If a receiver is exposed before the frontier, the
simulator must reveal a state consistent with the already published commitment `C`, its
public key, the AVID ciphertext, and every prior receipt. If the receiver is exposed
after the frontier, AK2/PECC must reveal a state in which the old key and point are
absent. A simulator that chooses the polynomial only after seeing the corrupted set, as
in the original hbACSS proof, cannot answer a later exposure after `C` and the AVID
transcript have already been published.

**(B) Adaptive recovery exposure.** A pre-frontier `KEYREVEAL` makes a ciphertext
decryptable to every party observing the transcript. It therefore has to be treated as
a public exposure event, not as an internal recovery message. A simulator that hides
this event inside the AVID or PKE hybrid underestimates `X_hist^r(B_r)` and can claim a
false privacy bound.

The first issue yields the following interface requirements for a concrete adaptive
instantiation:

```text
AC1  The commitment layer supports adaptive opening consistency, or the simulator
     receives an equivalent trapdoor/ideal share oracle. Public C is fixed before B_r.

AC2  A payload whose receiver is corrupted before the barrier has a non-committing
     or otherwise adaptively simulatable encryption state, including the state later
     revealed by the corruption oracle.

AC3  A payload whose receiver is corrupted after the barrier is covered by AK2/PECC;
     post-erasure state contains no decryption key or plaintext.

AC4  AVID communication is transparent with respect to scalar capability: its blocks,
     receipts, and reconstruction metadata are derived from ciphertext and public
     metadata only. Any public scalar reconstruction value is an uncovered edge.

AC5  Every accepted pre-frontier implication and key reveal is inserted into the
     history view before the next adaptive choice; delayed post-frontier messages are
     rejected by the frontier gate.
```

**Proposition 18 (adaptive opaque-delivery barrier).** An `AVID-opaque` reduction for
`C_hb0^opaque` under full adaptive state exposure requires AC1--AC5. Under these
conditions, the AVID layer can be treated as a public transport for `ct_Q,i`, and its
additional contribution is bounded by transport correctness plus the commitment,
non-committing-encryption, PECC, and recovery-gate terms. If AC1 or AC2 is absent,
the original hbACSS static simulator cannot be lifted to `Adv_hb0-GenSim^R` under
adaptive corruption; the resulting gap is not an AVID availability error but an
adaptive-state simulation failure.

**Proof sketch.** By AC4, AVID messages are deterministic or simulatable functions of
public metadata and opaque ciphertexts, so they do not add a scalar edge. AC1 fixes a
commitment-compatible sharing view before the adaptive set is selected. AC2 supplies
the state that can be revealed for a pre-frontier corruption without changing that
view. AC3 handles later corruption after key erasure. AC5 partitions every recovery
key into the history view or a rejected stale message. The remaining hybrids are
exactly the terms already listed in Lemma 16. Without AC1, a later share opening need
not be consistent with the earlier binding commitment; without AC2, an exposed secret
key can distinguish a simulated zero payload from the real payload. QED

This proposition changes the concrete go/no-go boundary. Per-instance ephemeral keys
solve the post-erasure resurrection edge, but they do not solve pre-frontier adaptive
simulation. A proof-friendly `C_hb0^opaque` instance therefore needs an explicit
equivocal/adaptive commitment and non-committing encryption argument, or it must state
adaptive opaque delivery as an independent assumption. Static hbACSS plus ordinary
Pedersen hiding and IND-CPA is insufficient for the full mobile-adversary claim.

### 19.44 Janus-style adaptive transport as an existing interface

The local Janus DKG specification provides a relevant prior-art interface for AC1 and
AC2. Its simulator publishes perfectly hiding Pedersen commitments, replaces honest-to-
honest ciphertexts by values prepared for later equivocation, and uses erasure together
with a programmable encryption primitive to reveal a state consistent with a party
corrupted in the middle of the protocol. This is materially stronger than the static
hbACSS simulator and confirms that the adaptive-key gap is a known cryptographic
interface rather than an AVID availability problem.

Janus does not close the FGSR problem as a black box. Its object is DKG/key sharing, its
public complaint path can deliberately make a ciphertext decryptable, and its theorem
does not provide frontier-dominated per-coordinate recovery or aggregate-only opening.
The following interface separation must therefore remain explicit:

| property | Janus-style transport | FGSR obligation |
|---|---|---|
| adaptive state equivocation | provided under its commitment/encryption/erasure assumptions | reuse only for the local delivery view |
| public complaint/decryption | allowed to identify a faulty sender | allowed only before the coordinate frontier and charged to history exposure |
| async delivery | authenticated/reliable broadcast and protocol-specific delivery | Common-H, `READY`, and target-excluded recovery |
| retirement | ordinary protocol completion/refresh | absorbing `Retired` state and no post-frontier recovery edge |
| output | shared key or share state | aggregate-only `Joint-AO` output |

**Proposition 19 (transport substitution boundary).** Suppose a Janus-style encrypted
sharing transport satisfies AC1--AC3 for each FGSR repair context, and its public
complaint and decryption messages are wrapped by AC4--AC5. Replacing the plain
`EphKeyGen/Enc` layer in Lemma 17 by that transport preserves the AK2 post-frontier
edge-exclusion conclusion. It does not remove the need to prove Common-H availability,
hbPolyCommit evaluation binding, cross-coordinate isolation, or `Joint-AO`.

**Proof sketch.** The transport substitution changes only the E2--E6 edges in the
typed ledger. AC1--AC3 provide the pre-frontier state simulation and post-frontier
erasure required by Lemma 17; AC4--AC5 prevent its public complaint path from becoming
a new retired-coordinate edge. All E7--E10 edges are outside the transport and remain
covered by their original assumptions. QED

This gives the concrete construction a disciplined fallback: either instantiate the
opaque delivery layer with a Janus-style adaptive transport and state the exact hybrid
assumptions, or keep `C_hb0^opaque` abstract. Reusing that transport is not itself a
contribution. The contribution remains the frontier-gated recovery-closure theorem,
its robust-hitting characterization, and the no-resurrection boundary for asynchronous
secure aggregation.

### 19.45 Frontier-safe public complaint semantics

Janus-style transport exposes an additional timing issue. A complaint or decryption
proof may be sent before retirement and delivered after retirement. For a public
`KEYREVEAL`, the capability exposure time is the time at which the key enters the
public transcript, not the later time at which a receiver accepts the message. The
FGSR wrapper must therefore distinguish public exposure from state transition:

```text
if PublicSend(Q, KEYREVEAL) < T*:
    charge the key, decrypted point, and derived recovery material to X_hist;
if Receive(Q, m) >= T* and state.mode == Retired:
    reject the derivation edge, even if m was valid before T*;
if PublicSend(Q, KEYREVEAL) >= T*:
    do not publish or accept the key-reveal edge.
```

For a private complaint, the corresponding exposure event is the first endpoint or
channel state that can be read by the adversary; PECC must cover any ciphertext retained
after that event. A protocol cannot classify a public key reveal as private merely
because the receiver processes it asynchronously.

**Lemma 18 (frontier-safe public complaint).** Suppose `KEYREVEAL` is a public,
context-bound message, its send event is included in the adversarial view, and every
post-frontier receive and recovery transition is checked against the absorbing
`Retired` state. Then a Janus-style complaint path adds no new post-retirement edge to
`Cap_old(c)`: every valid key reveal is either already in `X_hist` or is rejected by the
frontier gate.

**Proof.** Partition the first public `KEYREVEAL` for `c` by its send event. If it is
before `T*`, the key and every point derivable from it are already part of the history
view, regardless of delivery order. If it is after `T*`, the wrapper forbids its
publication or marks it invalid. A message sent before `T*` but received after `T*`
cannot create a new edge because the receiver is retired; it can only repeat an edge
already charged to `X_hist`. The same partition applies to the subsequent recovery
message. QED

The lemma is a necessary wrapper condition, not a new encryption assumption. If a
candidate requires post-retirement complaint processing for liveness, it is incompatible
with the first FGSR theorem; liveness must instead be established while the coordinate
is `Live/Recoverable`, before the retirement certificate dominates the instance.

### 19.46 Complaint/data-plane factorization for `Joint-AO`

The public complaint transcript cannot be classified as `StateView` merely because it
is generated by the recovery component. Partition it according to the inputs read by
the complaint and recovery branch:

```text
Comp_state = messages determined by Q, frontier, generation, helper validity,
             current-share state, and the authenticated recovery schedule;

Comp_data  = messages or branch decisions that read client ciphertexts, weights,
             H_ct, H_out, aggregate ciphertexts, partial decryptions, or output state.
```

`KEYREVEAL` and a recovery proof may be present in `Comp_state`, but their scalar
capability is still charged to `X_hist` when publicly sent. `Comp_state` is allowed in
`StateView` only if its distribution is independent of the challenge key vectors after
conditioning on that history. Every `Comp_data` object, including the control decision
that caused it to be emitted, belongs to `DataView_b` and must be covered by the single
`Joint-AO^mob` challenge.

**Proposition 20 (complaint/data-plane factorization).** Suppose:

1. the complaint predicate reads only `Comp_state` inputs until it has committed to a
   fixed recovery context;
2. any public `KEYREVEAL` follows Lemma 18 and its exposed capability is included in
   `X_hist` before the next adaptive choice;
3. no `Comp_state` proof or receipt selects an individual client ciphertext, weight,
   partial decryption, or output branch; and
4. every `Comp_data` message and branch is included in `Joint-AO^mob` under the same
   adaptive prefix
   context and accepted client set.

Then adding the public complaint/recovery transcript to the main composition theorem
changes its bound by at most

```text
Adv_Complaint-Noninterference
  + Adv_Joint-AO^mob,
```

where the first term is zero when conditions 1--3 hold by construction. If a candidate
does not provide this factorization, `Adv_Complaint-Noninterference` must remain an
explicit error term and `RCL-Sim/AO` cannot be claimed from ordinary state-layer
simulation.

**Proof sketch.** In the state hybrid, replace `Comp_state` using the recovery/state
simulator while retaining all pre-frontier exposed keys and points in `X_hist`. By
condition 3, this replacement cannot choose an individual data-plane object, so it is
independent of the challenge bit except for the explicitly charged history. Move
`Comp_data` and its branch decision into `DataView_b`; the one joint challenge then
covers it together with the ciphertexts, partial decryptions, certificates, and common
aggregate. Any remaining challenge-dependent branch violates condition 3 and is exactly
`Adv_Complaint-Noninterference`. QED

This proposition closes a common bookkeeping error: a public recovery transcript can be
state-layer metadata for capability safety and simultaneously be data-plane leakage if
it observes client ciphertexts. The first FGSR instance must enforce the former by a
typed API rather than infer it from the module name `recovery`.

### 19.47 Concrete `R_eq` and aggregate-opening audit

For the TACITA-style data plane, the factorization can be checked at the object level.
The following classification is mandatory for the first FGSR instance:

| object | inputs read | view destination | required condition |
|---|---|---|---|
| `R_eq` statement/proof for `(u,ell)` | `ctx`, `w_u`, `ct_{u,ell}`, encryption key material, proof randomness | `DataView_b` | statement is fixed by the challenge context; proof reveals no witness or scalar opening |
| aggregate certificate `(S,w,tag,H_ct,H_out,certificate)` | accepted client set, weights, ciphertext multiset, output context | `DataView_b` | one certificate is bound to one exact aggregate descriptor and cannot be reused for another subset |
| `PartDec(sk_j,ct_D,tag)` and its proof | committee share, aggregate ciphertext, tag | `DataView_b` | partial decryption is ciphertext-specific and is challenged jointly with `ct_D` |
| helper `IMPLICATE/KEYREVEAL/RECOVER` | `Q`, frontier, generation, helper validity, current share state | `StateView` plus `X_hist` | branch does not read client ciphertexts or select a data-plane object |
| invalid-aggregate/data-plane complaint | aggregate ciphertext, `R_eq`, certificate, or partial decryption | `DataView_b` | complaint control flow is included in `Joint-AO` |
| ACSS `READY`/availability receipt | authenticated repair context and local delivery status | `StateView` | receipt contains no scalar evaluation and no data-plane selection |

The table has two consequences. First, the `R_eq` proof is not a state-layer proof even
when its verifier is run by a committee member: its statement contains challenge
ciphertexts and the witness contains client mask material. Second, a partial decryption
is not harmless metadata merely because it does not reveal an individual plaintext by
itself; its ciphertext-specific component can distinguish two key vectors and therefore
belongs to the same `Joint-AO` experiment as the aggregate ciphertext.

**Lemma 19 (concrete data-plane factorization).** Suppose the six rows above satisfy
their required conditions, the accepted descriptor is unique, and `R_eq` has soundness,
concurrent simulation, and proof-noninterference. Then all challenge-dependent public
objects produced by the data plane are contained in `DataView_b`, while all recovery
objects outside `X_hist` are challenge-independent `StateView` objects. Consequently,
the complaint factorization of Proposition 20 introduces no additional term beyond
`Adv_Complaint-Noninterference`; under the stated typed API that term is zero by
construction.

**Proof.** The first three rows explicitly consume challenge ciphertexts or their
aggregate and are generated inside `Joint-AO`. The fifth row has the same dependency
and is moved with the same challenge, including the branch that emits it. The fourth
and sixth rows read only pre-challenge repair context and state; by proof-
noninterference they cannot select a hidden client object, and by the send-time rule
their exposed capability is already accounted for in `X_hist`. No remaining public
object has a challenge-dependent input. QED

This is an interface lemma, not a TACITA instantiation claim. TACITA's extended CPA
game supports ciphertext-specific aggregate decryption, but the current local evidence
does not by itself establish the required auxiliary-input, concurrent `R_eq`, and
complaint-branch simulation. Until those conditions are separately proven, the main
theorem must retain `Joint-AO` as an explicit assumption.

### 19.48 TACITA Static-AO separation for long-lived FGSR

TACITA's extended CPA game fixes the corrupted set `Cor` before the challenge messages
and ciphertexts are generated. Its guarantee is therefore a static, one-shot aggregate
opening guarantee. It does not model an adversary that first observes a public
generation transcript, then adaptively corrupts different committee members across
generations, retains their exposed state, and finally obtains all current state after a
coordinate has retired.

This distinction is semantic rather than terminological. Let `Static-AO` denote the
TACITA-style game and let `Joint-AO^mob` denote the data-plane game needed by FGSR. In
`Joint-AO^mob`, the adversary may choose the next corruption and the next recovery
context as a function of the complete prior transcript; the challenge includes all
coordinates, aggregate certificates, `R_eq` proofs, ciphertext-specific partial
decryptions, and the state exposure allowed by the frontier game. Then:

```text
Static-AO  +  ordinary share repair  !=  Joint-AO^mob.
```

The gap is witnessed by two independent failure paths. First, a static aggregate
opening proof may be simulatable for a fixed `Cor` while a later corruption reveals the
receiver secret needed to open an earlier ciphertext. Second, a repair wrapper may
preserve the static aggregate game while retaining a coordinate-local recovery object
that reconstructs an already retired decryption share. Neither failure is detected by
TACITA's fixed-set challenge.

**Proposition 21 (static boundary).** A TACITA-style `Static-AO` theorem cannot by
itself imply `Joint-AO^mob` or privacy finality. Any such implication must additionally
provide all of the following:

1. an adaptive-key and transcript simulation for the generation-local receiver state;
2. a `PECC`/erasure argument showing that a post-frontier exposure cannot open a retained
   old ciphertext;
3. a joint challenge for all coordinates and all ciphertext-specific partial
   decryptions under one accepted aggregate descriptor;
4. concurrent simulation and noninterference for `R_eq` and invalid-aggregate branches;
5. a recovery-state localization theorem showing that repair cannot recreate a retired
   coordinate capability.

**Proof sketch.** Items 1--2 are absent from the static challenge because its corruption
set is fixed before the challenge and it has no frontier or repair oracle. Items 3--4
are stronger than a coordinate-wise call to `Static-AO`, since a proof or partial
decryption may correlate coordinates or select a ciphertext-dependent branch. Item 5 is
an independent state-layer condition: even an ideal aggregate-opening oracle does not
prevent a retained recovery object from reconstructing an old key. Thus a reduction from
the static game must introduce new assumptions or a new adaptive primitive at each item;
the static theorem alone cannot supply them. QED

The proposition gives the current go/no-go rule. `TACITA` remains the coordinate-level
aggregate-opening baseline and can support a concrete theorem only through an explicit
`Joint-AO^mob` lifting lemma. `TDH2a` and adaptive threshold ElGamal are candidate
ingredients for item 1, but they do not presently provide the aggregate-only,
equal-sum, ciphertext-specific, multi-coordinate interface required by items 3--4.
Until those interfaces are proved, the paper claims the abstract FGSR theorem and a
conditional data-plane composition theorem, not a completed TACITA construction.

### 19.49 Proof program after the experiment phase

The next theoretical work is deliberately ordered as a proof dependency chain:

```text
P0  Freeze Joint-AO^mob: game, transcript, exposure, and accepted descriptor.
P1  Prove the static-boundary proposition and the recovery-state localization attack.
P2  Prove the FGSR composition theorem assuming Joint-AO^mob and opaque adaptive repair.
P3  Attempt one concrete lifting route using adaptive threshold decryption plus
    simulation-sound R_eq; record every unproved interface as an explicit term.
P4  Decide the paper form: concrete construction if all terms close, or an abstract
    theorem plus a sharp separation/conditional instantiation if one term remains.
```

No dynamic committee theorem belongs before P2. A handoff can only be added after it is
shown to preserve the same recovery closure; otherwise it changes the access structure
and obscures the main result. The experiments validate the attack and liveness surfaces
after this proof chain is fixed; they do not replace any step in it.

### 19.50 Adaptive extension of the `Joint-AO` game

Section 19.17 is the static data-plane baseline. The long-lived FGSR theorem requires
the following adaptive extension rather than silently reusing that baseline. The
extension uses one challenge bit for a polynomial batch of concurrent descriptors, so
cross-coordinate and cross-session correlations remain visible to the adversary.

Let `A` interact with the challenger through a pre-challenge prefix oracle. The prefix
oracle exposes public setup, authenticated metadata, `Publish/Process` events, and all
legal corruption, recovery, and retirement operations. At every corruption event, the
challenger returns the node's currently readable state and all previously published
history; erased material is unavailable, while material exposed before an erase remains
in `X_hist`. The next corruption, recovery context, and retirement request may depend on
the complete prefix view.

At a single `Challenge` query, `A` fixes a polynomial batch

```text
J = {(D_s, U_s, I_s, w_s, tag_s)}_{s in S_ch}
```

and supplies two key-vector families `K_0` and `K_1`. The challenge is accepted only if
the descriptors, accepted client sets, domains, weights, and all public context are the
same in both worlds, and for every `s in S_ch`,

```text
sum_{u in U_s} w_{s,u} * k_{s,u,0}
  =
sum_{u in U_s} w_{s,u} * k_{s,u,1}.
```

The challenger samples the selected world `b` and generates, for every `s` and every
coordinate in `I_s`, all of the following using the same protocol distribution:

```text
client ciphertexts,
R_eq and consistency proofs,
aggregate ciphertexts and certificates,
ciphertext-specific partial decryptions,
invalid-aggregate branches, and
the common aggregate-only outputs.
```

Every object whose distribution depends on `K_b`, including the control decision that
caused the object to be published, is placed in `DataView_b`. The challenger then
continues answering every protocol-valid adaptive corruption, recovery, retirement, and
`Publish/Process` query. The only admissibility conditions are external to the privacy
claim: the instantaneous corruption bound, the published causal-generation exposure
budget, and the syntactic validity of labels and frontiers. The game does not reject a
query because its answer might contain an individual-opening capability. If a real
corruption or recovery response exposes such a capability, the object remains in the
adversary's view and the protocol loses the privacy-finality experiment; it is not
removed by an admissibility rule. `CapSafe` and `Recovery-Closure` are proof obligations
or explicit advantage terms, not filters on the adversary's legal queries.

The residual view must factor as

```text
View_b = (DataView_b, StateView, PublicContext_pre, X_hist),
```

where the right-hand side is the factorization sought by the simulator. Before a
factorization proof, `View_b` is the complete real transcript, including any state or
recovery object returned by a legal query. A recovery or complaint branch that reads a
client ciphertext, an aggregate ciphertext, a weight, `R_eq`, a partial decryption, or
an output descriptor must be placed in `DataView_b`; a branch that exposes a scalar
outside the declared history is an uncovered edge and is charged explicitly rather than
silently assigned to `StateView`.

The adaptive game is

```text
Exp_Joint-AO^mob(b): run the prefix, answer Challenge with K_b,
                     continue all protocol-valid adaptive queries subject only to
                     the external exposure budget and label/frontier syntax, and
                     return A's bit;

Adv_Joint-AO^mob(A)
  = |Pr[Exp_Joint-AO^mob(0)=1]
      - Pr[Exp_Joint-AO^mob(1)=1]|.
```

The static game of 19.17 is recovered by fixing the corruption set before `Challenge`,
removing the post-challenge state oracle, using one descriptor, and requiring a static
`StateView`. Thus `Joint-AO^mob` is strictly the stronger interface consumed by the
long-lived theorem; `Adv_Joint-AO` may replace it only under an independently proved
adaptive lifting theorem.

**Lemma 20 (view-factorization requirement).** Suppose a candidate data plane satisfies
the adaptive game above and its recovery API obeys typed capability isolation. Then the
only challenge-dependent public objects outside `X_hist` are those covered by
`DataView_b`; all remaining adaptive corruption and recovery output can be simulated as
`StateView` without knowing `b`. Consequently, the state/data composition contributes
no unlisted challenge-dependent branch.

**Proof.** Process the adaptive transcript in causal order. At each event, classify the
event by the inputs read by its generating branch. A branch reading only frontier,
generation, helper validity, and current-share state is state-layer output and has the
same distribution in both worlds by the state simulator. A branch reading any listed
data-plane object is generated inside `DataView_b`, including its publication decision.
Public key reveals are charged to `X_hist` at send time and are not reclassified by a
later receive event. Typed capability isolation excludes every remaining route from a
state-layer event to an individual opening. Induction over the causal transcript yields
the stated factorization. QED

This definition makes the next concrete proof target precise: either construct an
adaptive lifting from TACITA-style coordinate games to `Joint-AO^mob`, or prove that a
candidate's transcript/state interface violates Lemma 20. A static extended-CPA proof
alone is insufficient evidence for either conclusion.

### 19.51 Recovery-State Localization Barrier

The data-plane separation has a state-layer counterpart. Let `c=(sid,ell)` be a
coordinate and let an ordinary recovery wrapper represent its post-repair state as

```text
State_i = (G, L_c, d_i(c), T),
```

where `G` is persistent recovery authority shared across coordinates, `L_c` is
coordinate-local recovery material, `d_i(c)` is the direct capability of node `i`, and
`T` is the public frontier/tombstone. Assume the wrapper's retirement operation removes
`d_i(c)` but leaves `G` unchanged and leaves enough `L_c` material for its ordinary
recovery relation to remain complete. Assume also that the recovery relation and the
data-plane `Use_c` operation are label-oblivious in the following precise sense:

```text
Recover_i(c, G, L_c, helpers) -> d_i(c)'
Use_c(d_i(c)', old_client_ciphertext) -> accepted individual opening
```

still hold for a retired label whenever the same inputs would have been accepted before
retirement. A tombstone checked only by `CheckInstall` does not change this condition:
it prevents a state transition, but does not prevent an offline capability derivation or
its use against a retained old ciphertext.

**Proposition 22 (recovery-state localization separation).** Suppose a retired
coordinate `c` has a decryption set `D in Gamma_dec^cap(c)` such that, after the
retirement operation, the residual current state together with legal recovery
contributions can derive every capability in `D`. If the derivation is accepted by
`Use_c` without a frontier check that is cryptographically bound to the capability,
then `PF_c` is impossible under future full-state exposure, even when:

1. every direct share deletion is correctly acknowledged;
2. all public frontier/tombstone messages are authenticated and monotone; and
3. the underlying sharing and threshold-decryption primitives remain secure in their
   original games.

**Proof.** Let `X_ret` be the state exposed after retirement and let `B` be the
historically retained capabilities. By hypothesis, the legal recovery edges from
`X_ret` derive every element of `D`; hence `D subseteq Cl_rec(X_ret union B)`. The
adversary invokes those recovery edges using the exposed `G`, the surviving `L_c`, and
valid helper contributions, then applies `Use_c` to the retained old descriptor. The
frontier check at `CheckInstall` is irrelevant because no installation is needed: the
adversary derives the old individual-opening capabilities directly. Since `D` is an
authorized decryption set for `Gamma_dec^cap(c)`, the adversary recovers an old client
mask key. Equivalently, choose two key-vector worlds with the same authorized aggregate
but different individual keys; the recovered old opening distinguishes them. The attack
uses only legal recovery and state exposure, so it does not contradict the underlying
primitive games. QED

**Corollary 22.1 (ordinary VSSR/DPSS black-box limit).** An ordinary VSSR/DPSS wrapper
cannot establish `PF_c` by deleting only direct shares and adding a tombstone when its
recovery-complete state still contains a reusable `G,L_c` relation for `c`. To enter
FGSR, the wrapper must satisfy at least one of these conditions:

1. retirement deletes or punctures all `c`-local recovery material needed by the
   relation, while proving that the retained global state cannot reconstruct it;
2. the recovery authority and `Use_c` are frontier-bound, so a capability derived for a
   retired label is rejected cryptographically rather than only at installation; or
3. the system changes the decryption/recovery generation so that old capabilities are
   invalid under a new authenticated key context.

This is a black-box separation, not a claim that VSSR or DPSS is intrinsically
insecure. Their original correctness goals preserve a share or a long-lived secret;
FGSR requires the stronger property that the recovery closure of a retired label is
absorbing. The distinction is exactly the `Cl_rec` condition in the privacy-finality
definition. If a candidate can recover only the same authorized aggregate and cannot
derive an individual opening or a second independent aggregate descriptor, this
proposition is not by itself a privacy distinguisher; the capability universe and the
privacy claim must then state that weaker target explicitly.

### 19.52 Static-AO wrapper separation

Proposition 22 can be turned into a direct separation from TACITA's static game. Let
`W` be a wrapper that uses a TACITA-style `Static-AO` data plane for coordinate `ell`
and adds recovery/state exposure. Assume the static primitive is secure for every
corruption set fixed before its challenge. Suppose that `W` additionally has:

1. a challenge descriptor containing a client ciphertext `ct_{u,ell}` whose individual
   mask key is in the target capability universe;
2. a post-retirement state exposure and legal recovery schedule satisfying Proposition
   22 for some `D in Gamma_dec^cap(sid)`; and
3. a `Use_c` operation that accepts the recovered capability for `ct_{u,ell}` without
   a cryptographically bound retired-frontier check.

**Proposition 23 (static-to-mobile wrapper separation).** Under these conditions, there
is an adversary `A_W` with a fixed pre-challenge corruption set in the TACITA game but
an adaptive post-challenge corruption schedule in the wrapper experiment such that

```text
Adv_Joint-AO^mob(A_W)
  >= 1 - 2*(epsilon_recovery + epsilon_use) - negl(lambda),
```

where `epsilon_recovery` and `epsilon_use` are the failure probabilities of the legal
recovery and individual opening operations. This holds even if
`Adv_Static-AO` is negligible.

**Proof.** `A_W` chooses two key-vector families that have the same authorized weighted
aggregate but differ in the key `k_u` for one client `u`. It submits them to the static
TACITA challenge and receives the complete static ciphertext and proof transcript. It
then follows a legal wrapper schedule: retire `sid`, expose the current states that
contain the reusable global and local recovery material, and invoke the recovery edges
from Proposition 22. By the recovery and use correctness assumptions, `A_W` obtains an
opening of `ct_{u,ell}` with probability at least
`1-epsilon_recovery-epsilon_use`. It compares the recovered key with `k_{u,0}` and
`k_{u,1}` and outputs the matching world. Thus its success probability is at least
`1-epsilon_recovery-epsilon_use`, which gives the stated distinguishing advantage.
The static TACITA challenge is never broken: the distinguishing information comes from
the wrapper's post-challenge state and recovery interfaces, which are absent from the
static game. QED

The proposition is a black-box impossibility for this wrapper shape, not for all
aggregate-only data planes. If an implementation never exposes an individual opening,
then its capability universe must remove that capability and its `Use` interface must
be restricted to the single authorized aggregate or an explicitly authorized family of
descriptors. In that weaker model, the relevant separation target is a second aggregate
descriptor or another data-dependent branch, and it must be included in `DataView_b`.

The FGSR audit therefore has three concrete obligations after retirement:

```text
L1  no retired-coordinate local recovery material remains in future StateView;
L2  retained global recovery authority cannot derive that material by itself;
L3  every surviving Use/PartDec path rejects a retired capability by a frontier-bound
    check, not only by a local installation guard.
```

These obligations are stronger than deleting direct shares and are exactly the missing
conditions that ordinary VSSR/DPSS wrappers leave unspecified.

### 19.53 FGSR localization lemma

The abstract FGSR wrapper can satisfy the localization interface without adding a new
cryptographic primitive. Let `Retire(c,T*)` perform state-complete erasure and leave only

```text
State_after(T*) = (frontier >= T*, retired(c), metadata, live-coordinate states).
```

In particular, the state contains no `Share(c,r)`, `RepairShare(c,r,*,*)`, recovery
polynomial share, DPRF contribution, pending endpoint secret, or `sid`-local backup for
any retired generation. Define the wrapper operations so that:

```text
Recover(c,T_req,...)  -> reject       if c is retired under T_req;
Use_c/PartDec(...)    -> reject       if the authenticated frontier retires c;
Recover/Use for live c -> require the current generation and frontier label.
```

**Lemma 24 (FGSR localization).** Under the state shape and operation guards above, and
assuming the public transcript contains no scalar recovery material, the abstract FGSR
wrapper satisfies `L1--L3` with

```text
Adv_Recovery-Localization = 0,
Adv_Frontier-Use = 0.
```

The concrete implementation may replace these zeros only by the explicit erasure,
transcript, or label-binding failure terms already present in the composition theorem.

**Proof.** `L1` follows from the state shape: after `Retire(c,T*)`, no retained local
object is an input to a recovery edge for `c`. The remaining public commitment, frontier,
receipt, and metadata are not scalar capabilities by the opaque-transcript premise. For
`L2`, the abstract FGSR state has no global recovery authority whose input alone derives
the deleted local material; every live-coordinate recovery edge requires a current,
frontier-matching share, while a retired coordinate is rejected. For `L3`, every
`Use_c/PartDec` edge checks the authenticated frontier before consuming a capability, so
a capability tagged by a retired coordinate cannot be used even if it was obtained before
the barrier. Any violation must therefore be an erased-state exposure, a scalar-bearing
transcript, or a forged/stale label, charged respectively to `Adv_PECC`,
`Adv_ACSS-opaque`/`Adv_Eq-Simulation`, or `Adv_Frontier-Use`/`Adv_Generation-Binding`.
QED

Lemma 24 is an interface result, not a physical-erasure theorem. It closes the state
layer of P2 only after a concrete ACSS/channel implementation proves that its actual
buffers and endpoint state have the abstract shape above.

### 19.54 P2 composition hybrid

The conditional BF-RPTA theorem can now be organized into four hybrids without mixing
the state and data games.

```text
H0  real FGSR execution, including adaptive corruption and all legal recovery;
H1  replace each generation's ACSS delivery, equality proof, receipt, and endpoint
    exposure by the challenge-independent StateView, retaining DataView_b;
H2  replace the complete retained DataView_0 by DataView_1 using one Joint-AO^mob
    challenge for all descriptors, coordinates, certificates, and branches;
H3  replace the remaining context and affine-coupling artifacts, charging correctness,
    binding, and coupling failures.
```

**Lemma 25 (P2 hybrid bound).** Under `L1--L3`, typed capability isolation, and the
`Joint-AO^mob` view factorization, the four hybrids satisfy

```text
Adv[H0,H3]
  <= Adv_Joint-AO^mob
     + Adv_Affine-Coupling
     + Adv_State-Commitment
     + Adv_Generation-Binding
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + Adv_Context/Correctness
     + sum_{r=1}^R(
         Adv_ACSS-opaque^r
         + Adv_Eq-Simulation^r
         + Adv_PECC^r)
     + R*negl(lambda).
```

**Proof.** For `H0 -> H1`, process generations in causal order. Proposition 20 and
Lemma 24 classify every recovery event as either challenge-independent `StateView` or
challenge-dependent `DataView_b`. The generation-local simulators replace the former;
their errors sum over `r`, while a stale installation or an exposed endpoint is charged
to generation binding, PECC, or the corresponding localization term. Since no simulated
state object is an individual opening capability, the adaptive corruption choices remain
valid in the next prefix.

For `H1 -> H2`, use the single `Joint-AO^mob` challenge on the complete batch. It covers
all coordinates, `R_eq`, aggregate certificates, partial decryptions, invalid-data
branches, and the decisions that publish them. No coordinate-local hybrid is used, so no
intermediate false relation must be proved. The common weighted aggregates make the
authorized output identical in both worlds.

For `H2 -> H3`, context uniqueness and mask correctness make accepted descriptors and
authorized outputs equal. Cross-generation affine coupling preserves the exposed helper
points and equality relations while changing only the hidden challenge world; failure is
`Adv_Affine-Coupling`. The remaining differences are exactly the listed correctness,
commitment, and binding terms. A union bound over the polynomial number of generations
gives the displayed expression. QED

This hybrid is the current P2 proof skeleton. A concrete construction may set a term to
negligible only after proving its corresponding interface; it may not remove a term merely
because the underlying module is called `VSS`, `AVSS`, or `threshold encryption`.

### 19.55 `C_hb0^opaque`/Janus AC1--AC5 evidence audit

The current concrete-candidate question is narrower than whether hbACSS or Janus is
"adaptive-secure" in its own setting. The relevant question is whether either work
supplies every interface consumed by `H0 -> H1` for a long-lived FGSR coordinate.
The audit uses the following five obligations:

| Interface | Janus-style transport | hbACSS | Current verdict |
|---|---|---|---|
| AC1 adaptive commitment consistency | Local support through hiding/equivocal commitment and adaptive encryption; not a per-coordinate FGSR theorem | Static honest-dealer simulator and commitment hiding do not cover a later adaptive key/state exposure | Conditional; retain `Adv_Adaptive-Commitment` and `Adv_hbACSS-StaticSim` |
| AC2 pre-frontier adaptive payload state | DKG-lifecycle support is relevant, but does not establish concurrent repair-context and AVID-payload simulation | Original simulator is parameterized by a preselected corrupted-key set | Unclosed; requires an adaptive opaque-delivery interface |
| AC3 post-frontier PECC | Secure erasure is a useful local mechanism, but endpoint, buffer, and frontier semantics remain separate obligations | The long-term-key optimization permits later opening of old payloads and is excluded | Unclosed; retain `Adv_PECC` |
| AC4 AVID scalar-capability isolation | Complaint/decryption paths can expose material and need an FGSR wrapper | AVID is not secret; `IMPLICATE`, key reveal, and recovery can expose scalar capability | Unclosed; retain `Adv_Complaint-Noninterference` |
| AC5 send-time history and frontier gate | Not supplied for retired FGSR coordinates | Not supplied | Must be proved by the FGSR wrapper; retain `Adv_Generation-Binding` |

The audit gives a precise go/no-go result.

1. The abstract FGSR `Recovery-Closure` and `Joint-AO^mob` composition theorem
   remains valid and is the main theoretical result.
2. A Janus-style transport may replace the typed ledger's local delivery edges only
   under AC1--AC3, with its public complaint/decryption behavior separately wrapped
   by AC4--AC5.
3. Existing Janus or hbACSS statements do not, by themselves, instantiate
   `C_hb0^opaque`. The paper must call that result conditional until the five
   interfaces are proved for the chosen transport.
4. The hbACSS long-term-key optimization is not an admissible first-instance route:
   it conflicts with post-frontier recovery closure even if ordinary ACSS agreement
   and availability hold.

Thus the concrete-candidate advantage ledger remains

```text
Adv_Adaptive-Commitment
+ Adv_hbACSS-StaticSim
+ Adv_PECC
+ Adv_Complaint-Noninterference
+ Adv_Generation-Binding
```

These terms are separate falsifiable proof obligations. Removing one requires a
transport theorem or wrapper lemma that explicitly covers its corresponding edge.

**Post-audit proof order.** First define a standalone `Adaptive-Opaque-Repair`
interface with `Publish`, `Process`, corruption, erasure, and recovery views. Then
prove the FGSR wrapper reduction from that interface to `H0 -> H1`. In parallel,
prove the asynchronous no-resurrection necessity attack and its matching absorbing-
retirement lemma. Only after those two pieces are stable should the manuscript add a
conditional instantiation section for Janus-style or hbACSS-derived transport.
Dynamic committees remain a corollary target, not a next construction.

### 19.56 `Adaptive-Opaque-Repair` as the state-layer interface

`F_AWF` specifies public frontier evolution, while `RPTA` specifies the data-plane
operations that use a current committee state. The missing interface between them is
the repair transcript and endpoint state seen by a long-lived adaptive adversary. We
factor it as `AOR` rather than attributing this property to an ordinary AVSS or VSS
module.

For a repair context

```text
Q = (sid, ell, r, rid, i, T_req, C_ctx),
```

where `r` is the generation, `rid` the repair instance, `i` the target receiver, and
`C_ctx` the authenticated public context, an `AOR` interface exposes

```text
Publish(Q, m) -> public event or reject
Process_i(Q, m, T_local) -> {accept, reject}
Expose_i(t) -> readable endpoint state
Retire_i(c, T*) -> state transition and public receipt
Recover_i(Q, L) -> candidate state and recovery evidence
CheckInstall_i(T_local, Q, candidate) -> {0, 1}
```

`Publish` is the only operation that adds a public capability event to `X_hist`; a
later `Process` event only decides whether a node changes its local state. The
interface therefore inherits the send-time semantics of `F_AWF`: a pre-frontier
`KEYREVEAL` is historical exposure even if it arrives after retirement, while a
post-frontier reveal is rejected.

The interface has two views. `PublicView` contains authenticated labels, commitments,
opaque payloads, receipts, availability evidence, frontier updates, and process
outcomes. `HiddenState` contains point values, ephemeral decryption keys, evaluation
openings, pending plaintext, and recovery scalars. A valid `AOR` simulator receives
`PublicView`, the already exposed `X_hist`, and the current frontier, but no
unexposed element of `HiddenState`.

#### `G_AOR^mob` security game

The challenger samples a bit `b`. In world `b=0` it runs the real repair transport;
in world `b=1` it runs an adaptive simulator `S_AOR` with only the permitted public
inputs. The adversary may adaptively issue `Publish`, `Process`, `Retire`, `Recover`,
and `Corrupt` queries. A `Corrupt(i,t)` query returns the state readable at time `t`:

1. before the relevant retirement barrier, it may reveal the endpoint key, plaintext,
   or opening material, and those values are permanently added to `X_hist`;
2. after the barrier, it returns the post-erasure state and any public ciphertext or
   metadata, but not erased endpoint material;
3. a public `KEYREVEAL` is charged at its send event, before the next adaptive query.

The simulator must preserve the distribution of all public labels, receipts, and
accept/reject outcomes. It may use an equivocal commitment or non-committing
encryption interface supplied by the candidate construction, but it may not obtain a
hidden scalar merely because a later corruption query is legal.

Define

```text
Adv_AOR^mob(S_AOR)
  = |Pr[G_AOR^mob(0)=1] - Pr[G_AOR^mob(1)=1]|.
```

The game is parameterized by a causal exposure budget. Any value exposed before a
barrier remains in `X_hist`; any value not exposed before the barrier must be absent
from every later endpoint state, pending buffer, recovery response, and public scalar
opening. This is a temporal exposure rule, not a claim that software erasure can be
verified by a public proof.

#### Required AOR properties

An `AOR` interface is admissible for FGSR only if it satisfies the following properties
in addition to `G_AOR^mob` indistinguishability:

| Property | Requirement | Failure term |
|---|---|---|
| AOR-1 causal publication | `Publish` records every public capability at send time and `Process` cannot retroactively create history | `Adv_Exposure-Timing` |
| AOR-2 opaque delivery | public transport and availability evidence do not reveal an unexposed scalar or reconstructible opening | `Adv_ACSS-opaque` |
| AOR-3 adaptive state consistency | a state exposed after public commitments are fixed is consistent with the prior transcript | `Adv_Adaptive-Commitment` + `Adv_hbACSS-StaticSim` |
| AOR-4 post-frontier opacity | endpoint, buffer, and recovery state after retirement cannot derive old point capability | `Adv_PECC` |
| AOR-5 frontier absorption | stale `Install`, `Use`, `PartDec`, `KEYREVEAL`, and `Recover` edges are rejected | `Adv_Generation-Binding` + `Adv_Frontier-Use` |

Complaint branches that inspect a client ciphertext, weight, aggregate ciphertext,
`R_eq`, or partial decryption are not `PublicView`-only branches. They must be passed
to `Joint-AO^mob`; otherwise the candidate incurs
`Adv_Complaint-Noninterference`.

**Proposition 26 (AOR lifting to the state hybrid).** Assume each generation's repair
transport satisfies `G_AOR^mob`, AOR-1--AOR-5, typed capability isolation, and the
`L1--L3` localization conditions. Then the first hybrid of Lemma 25 obeys

```text
Adv[H0,H1]
  <= sum_{r=1}^R Adv_AOR^mob(r)
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + R*negl(lambda).
```

If a concrete candidate proves the following reduction,

```text
Adv_AOR^mob(r)
  <= Adv_Adaptive-Commitment^r
     + Adv_hbACSS-StaticSim^r
     + Adv_PECC^r
     + Adv_Complaint-Noninterference^r
     + Adv_Generation-Binding^r
     + negl(lambda),
```

then Lemma 25 follows with the lower-level interface terms shown explicitly in its
advantage bound. If any term is not reduced, the result remains a valid conditional
FGSR theorem but is not a concrete long-lived construction theorem.

**Proof.** Simulate generations in causal order. For each repair context, replace the
real transport and endpoint exposure by `S_AOR`; AOR-1 accounts for all public
send-time history, AOR-2 and AOR-3 preserve public delivery and adaptive consistency,
and AOR-4 removes every post-frontier endpoint edge. AOR-5 and `L1--L3` exclude stale
installation and recovery edges. The residual view contains only `StateView`,
`X_hist`, or objects explicitly assigned to `DataView_b`. A union bound over the
generations gives the displayed `H0 -> H1` term. The `H1 -> H2` and `H2 -> H3` steps
are exactly those of Lemma 25. QED

This factoring is the paper's concrete stopping rule: ordinary AVSS correctness,
forward-secure encryption, or a tombstone may discharge at most one AOR property. They
cannot be substituted for the complete interface without a reduction for the missing
edges.

### 19.57 AOR-5 is the no-resurrection boundary

The frontier condition in AOR-5 is not an arbitrary protocol check. It is exactly the
state-layer condition needed to turn the access-structure bound into privacy finality.
Let `A` be the set of nodes whose retirement evidence is included in `PC_sid`, let
`R` be the subset of `A` whose old capability can be reinstalled by a delayed legal
message after retirement, and let `B` be the set of old capabilities exposed before
the retirement barrier. In the homogeneous threshold model, the effective old
capability set after retirement is

```text
B_eff = B union R union (P - A).
```

The term `P-A` represents nodes not covered by the retirement evidence whose current
state may later be exposed. The `R` term is the exact contribution of resurrection;
it is absent only when the state machine makes retirement absorbing.

**Proposition 27 (AOR-5 / robust-hitting correspondence).** Assume that every old
capability is either pre-exposed, held by a node outside `A`, or created by a legal
post-retirement recovery edge. For a fixed exposed set `B`, the target coordinate has
privacy finality exactly when, for every decryption set `D` in `Gamma_dec`,

```text
D is not a subset of B union R union (P - A).
```

If the adversary may place an arbitrary exposed set of size at most `b`, the equivalent
worst-case count condition is

```text
|D intersection (A - R)| > b.
```

In particular, if AOR-5 holds, `R = emptyset` and the condition reduces to the
`Robust-Hitting` requirement

```text
|D intersection A| > b.
```

If AOR-5 fails and a delayed legal message can make `R` nonempty, the same retirement
certificate may satisfy ordinary robust hitting while failing this stronger condition.

**Proof.** A decryption set `D` remains usable after retirement precisely when it is
contained in the union of capabilities already exposed, capabilities resurrected by
`R`, and current states outside `A`. This is the set condition above. Under an
adversarial budget `|B|<=b`, the worst placement of `B` covers at most `b` members of
`D intersection (A-R)`, yielding the count condition. If the count fails, expose the
`B` members, use the delayed recovery edges for `R`, and expose the uncovered current
states; the resulting set reaches `D`. If it holds, every `D` retains a member in
`A-R` outside the exposure budget, so the threshold reconstruction edge is
unavailable. The `Recovery-Closure` theorem handles all other legal derivation edges.
AOR-5 makes `R` empty by rejecting every stale `Install`, `Use`, `PartDec`, `Recover`,
and `KEYREVEAL` edge. QED

**Causal-fence necessity.** Suppose a valid old message remains authenticated after
retirement and the receiver accepts it without checking a state that dominates
`Retire(sid)`. An asynchronous scheduler can deliver that message before retirement
in one execution and delay it until after retirement in another execution, while
keeping the receiver's local view identical at the decision point. Recovery liveness
forces acceptance in the first execution; indistinguishability forces acceptance in
the second, so `R` is nonempty. Therefore any stable-key, late-message, cure-capable
protocol satisfying privacy finality must implement AOR-5, change the key generation,
or introduce an equivalent trusted causal boundary.

This proposition gives the paper a clean separation: `Robust-Hitting` is the access-
structure condition, while AOR-5 is its asynchronous state-machine realization. A
deny-list, forward-secure key update, or ordinary repair certificate is relevant only
when it proves the same correspondence.

### 19.58 P4 evidence audit for `Adv_AOR^mob`

The candidate interfaces can now be checked against the source protocols rather than
against their names. The relevant evidence is as follows.

| AOR obligation | Source evidence | What it proves | Remaining gap |
|---|---|---|---|
| AOR-1 / AC5 causal publication | Janus separates public complaint broadcast from local processing and makes the disputed ciphertext publicly decryptable (`/home/yzc/flagg/adaptive_dkg_2026_892.txt:464-470`); hbACSS publishes `IMPLICATE,SK_i` and recovery messages (`/home/yzc/flagg/extract_hbACSS.txt:819-830`) | Public exposure can be identified as a transcript event | Neither source has FGSR retired-label send/receive semantics; the wrapper must define `Publish` and frontier rejection |
| AOR-2 opaque delivery | hbACSS encrypts evaluation payloads but explicitly gives the adversary every AVID message and public ciphertext (`/home/yzc/flagg/extract_hbACSS.txt:1010-1017`) | AVID agreement/availability is compatible with transport, not secrecy | A scalar-capability isolation theorem is still required |
| AOR-3 adaptive state consistency | Janus erases the sharing polynomial and uses equivocable hashed-ElGamal ciphertexts to answer mid-protocol corruption (`/home/yzc/flagg/adaptive_dkg_2026_892.txt:445-462`); its simulator programs state after adaptive corruption (`:908-911`) | A strong local reference for adaptive commitment/state simulation | Janus proves a DKG functionality, not concurrent FGSR repair contexts or aggregate-only views |
| AOR-4 post-frontier opacity | Janus assumes erasure and leaves only selected state after broadcast (`/home/yzc/flagg/adaptive_dkg_2026_892.txt:519-545`); hbACSS offers no equivalent guarantee for a persistent receiver key | Erasure can support a local post-exposure hybrid | No source proves endpoint/buffer PECC under an FGSR retirement frontier; hbACSS long-term-key optimization is incompatible (`/home/yzc/flagg/extract_hbACSS.txt:972-996`) |
| AOR-5 frontier absorption | Neither protocol carries a per-coordinate monotone frontier through recovery or stale installation | At most, ordinary protocol labels and epochs | Must be supplied by FGSR; no existing theorem closes this edge |

The audit therefore yields the following reduction status:

```text
Janus-style transport -> candidate support for AC1/AC2, not AOR-1--AOR-5
hbACSS              -> availability/evaluation correctness, not adaptive AOR
FGSR wrapper        -> supplies AOR-1/AOR-5 only after its own proof
Joint-AO^mob        -> supplies the challenge-dependent data plane
```

In particular, Janus cannot be inserted unchanged into the repair path: its
identifiable-abort mechanism intentionally creates a public decryption capability.
Likewise, hbACSS's long-term-key optimization cannot be repaired by merely adding a
tombstone, because the old payload remains decryptable from a later exposed key. The
first concrete theorem therefore remains conditional:

```text
Adv_AOR^mob(r)
  <= Adv_Adaptive-Commitment^r
     + Adv_hbACSS-StaticSim^r
     + Adv_PECC^r
     + Adv_Complaint-Noninterference^r
     + Adv_Generation-Binding^r
     + negl(lambda).
```

The next proof target is not another literature component. It is a wrapper lemma that
converts a Janus-style adaptive transport into an `AOR` instance while replacing its
public complaint/decryption branch with a frontier-safe, metadata-only branch. If that
replacement cannot be proved without revealing an old scalar, the paper should retain
`AOR` as an explicit conditional interface and present the source protocols only as
nearby partial instantiations.

### 19.59 Complaint noninterference barrier

The Janus identifiable-abort path exposes a capability by design: a public complaint
contains enough information to decrypt a disputed ciphertext and compare the result
with a public commitment. This behavior cannot be converted into AOR-2 merely by
adding a retired-label check at the receiver.

**Proposition 28 (public complaint separation).** Let `Q` be a repair context and let
`Comp(Q)` be a complaint event whose public contents, together with the retained
ciphertext `ct_Q`, derive an evaluation point or a recovery scalar. If `Comp(Q)` can
be sent after the retirement frontier, then AOR-4 or AOR-5 fails: a future adversary
can read the public complaint and derive an old capability without consulting the
retired receiver state. If `Comp(Q)` is sent before the frontier, its derived point,
key, and recovery material belong to `X_hist` and cannot be removed by later erasure.

Consequently, a frontier-safe complaint wrapper requires all three conditions:

1. post-frontier `Comp(Q)` is rejected at `Publish`, not merely at `Process`;
2. a pre-frontier complaint is charged to `X_hist` and, when its branch reads a
   challenge-dependent ciphertext or point, to `DataView_b` and `Joint-AO^mob`;
3. any complaint accepted without such historical exposure is metadata-only and has
   a simulation-sound proof whose statement does not reveal an individual opening.

**Proof.** In the first case, the public complaint is a legal post-frontier derivation
edge to an old capability, contradicting AOR-4/AOR-5. In the second case, the
capability was already exposed at the complaint send event, so erasure cannot reduce
`X_hist`; omitting it from the data-plane challenge would undercount the adversary's
view. The third case is the only branch that can remain in `PublicView`, and its
simulation-soundness and noninterference are exactly the required proof obligations.
QED

This proposition rules out a black-box Janus-to-FGSR wrapper that preserves the
original public-decryption complaint semantics. The admissible routes are either a
metadata-only complaint proof, or a live-only complaint whose pre-frontier scalar
exposure is explicitly accounted for. Neither route is supplied by the current Janus
or hbACSS theorem, so `Adv_Complaint-Noninterference` remains non-negligible until a
separate construction is proved.

### 19.60 Candidate route: zero-knowledge invalidity blame

A possible positive route is to replace public key disclosure by a metadata-only
invalidity proof. This is a new interface obligation, not a claim that an ordinary
NIZK already supplies it. For a context `Q`, ciphertext `ct_Q`, and public evaluation
commitment `C_Q`, define

```text
ProveInvalid(Q, ct_Q, C_Q, st_i) -> pi_bad or reject
VerifyInvalid(Q, ct_Q, C_Q, pi_bad) -> {0, 1}
```

The proof statement asserts that the receiver knows a valid local decryption witness
and an evaluation witness whose decoded payload fails the authenticated validity
relation, or that the ciphertext satisfies a separately defined publicly verifiable
decryption-failure relation. The proof reveals neither the receiver secret key, the
decoded point, nor an evaluation opening.

The required `ZK-Invalidity` interface has four properties:

1. **Completeness:** every dealer fault that would otherwise require `KEYREVEAL` has a
   witness accepted by `VerifyInvalid`;
2. **Soundness:** an honest payload cannot be turned into a recovery trigger by a
   malicious receiver;
3. **Adaptive zero knowledge:** the proof and receiver state remain simulatable after
   commitments and ciphertexts have been published and the receiver is corrupted;
4. **Data-plane factorization:** the proof is scalar-free, while any branch depending
   on `ct_Q`, weights, `R_eq`, or partial decryption is generated inside the same
   `Joint-AO^mob` challenge.

**Proposition 29 (conditional complaint closure).** If `ZK-Invalidity` satisfies the
four properties, `Publish` rejects every post-frontier complaint, and live complaints
are bound to `(rid,sid,ell,r,T_req,i)`, then

```text
Adv_Complaint-Noninterference = negl(lambda)
```

and the AOR reduction becomes

```text
Adv_AOR^mob(r)
  <= Adv_Adaptive-Commitment^r
     + Adv_hbACSS-StaticSim^r
     + Adv_PECC^r
     + Adv_ZK-Invalidity^r
     + Adv_Generation-Binding^r
     + negl(lambda).
```

**Proof.** Replace a valid `pi_bad` with its zero-knowledge simulation inside the
joint data-plane challenge. Completeness and soundness preserve the recovery control
flow; adaptive zero knowledge prevents a later corruption from extracting the hidden
decryption witness; context binding and the frontier gate exclude stale complaints.
No public complaint edge remains that derives an individual scalar, so the only
remaining differences are the listed interface terms. QED

This route has a sharp limitation. A generic NIZK for a relation involving
`Dec_sk(ct)` does not by itself prove decryption failure, preserve asynchronous
availability, or simulate a proof whose publication branch depends on challenge data.
Those requirements must be specified and proved by the chosen encryption/argument
system. Until then, `ZK-Invalidity` is a conditional candidate rather than a closed
construction.

### 19.61 Local literature audit for `ZK-Invalidity`

The local papers provide nearby proof components, but none supplies the complete
invalidity-blame interface.

| Candidate | What the source actually provides | Why it does not close `ZK-Invalidity` |
|---|---|---|
| VSSR | `vssRecoverVerify*` checks a recovery contribution and `vssRecover*` reconstructs a missing share (`Efficient Verifiable Secret Sharing with.pdf_by_PaddleOCR-VL-1.6.md:216-228`, `:274-285`) | It authenticates recovery data; it does not publicly prove decryption failure without revealing a recovery share or scalar |
| Choudhuri et al. | `Setup/Prove/Verify/SimProve` and weak simulation-extractability for well-formed ciphertext/PPE statements (`usenixsecurity25-choudhuri.pdf_by_PaddleOCR-VL-1.6.md:211-241`, `:302-328`) | The relation proves correct ciphertext construction and selected-batch decryption, not a zero-knowledge statement of invalid decryption in an adaptive repair transcript |
| Threshold Encryption with Silent Setup | A simulation-extractable NIZK binds ciphertext components and proves knowledge of an encryption witness (`Threshold Encryption with Silent Setup.pdf_by_PaddleOCR-VL-1.6.md:677-683`) | The proof prevents CCA malleability; it does not prove that a receiver's decryption failed or isolate a retired recovery capability |
| Janus | A verifiable complaint makes a disputed ciphertext publicly decryptable (`/home/yzc/flagg/adaptive_dkg_2026_892.txt:464-470`) | This is the opposite of metadata-only complaint noninterference |

The evidence supports a negative but useful conclusion: `ZK-Invalidity` is not a
renaming of VSSR recovery verification, SE-NIZK, or verifiable decryption. A concrete
instantiation must define the failure relation, prove its completeness and soundness,
and show adaptive simulation under the same `Joint-AO^mob` publication branch. Until
then, `Adv_ZK-Invalidity` remains an explicit candidate term.

### 19.62 Complaint-free publicly verifiable resharing candidate

The previous candidate used a public complaint path to explain how a receiver rejects
an invalid evaluation. That path is exactly where Janus and hbACSS expose a key or a
recoverable point. Local rejection alone is also insufficient: a Byzantine helper can
send valid ciphertexts to every receipt signer and an invalid ciphertext to the repair
target. The first construction therefore makes ciphertext validity publicly verifiable
while keeping the evaluation hidden. The protocol publishes neither a decryption key,
an evaluation opening, nor a scalar blame object.

This is a candidate interface, not an existing APSS/hbACSS theorem. It makes the
availability obligation explicit instead of hiding it inside a complaint protocol.
Fix `P` with `n=3f+2`, a sharing degree `2f`, and a live coordinate
`c=(sid,ell)`. At generation `r`, member `j` stores

```text
State_j(c,r) = (z_j^r, rho_j^r, C^r, r, T_j),
z_j^r = F^r(j),    deg(F^r) <= 2f.
```

Here `rho_j^r` is the private evaluation opening in the Pedersen instantiation, such that

```text
E_j^r = product_k (C_k^r)^{j^k} = Com(z_j^r; rho_j^r).
```

This opening is hidden state, not public metadata. It is retained only until the next
state-complete installation or retirement and is included in the erase/`PECC` view.

For a refresh or a repair request, the target is optional: a refresh targets all
correct members, while a repair request names a member whose old local state is
missing. Both use the same state-complete transition:

```text
CSR(Q=(rid,c,r,T_req,C^r,u)):

1. Select:
   validated ACS selects H subseteq P \ {u}, |H|=2f+1,
   using only labelled descriptors and metadata.

2. Contribute:
   each h in H samples
       f_h(X) = z_h^r + sum_{k=1}^{2f} a_{h,k} X^k,
   publishes coefficient commitments and a zero-knowledge equality proof
       f_h(0) = F^r(h),
   for every receiver j samples (y_{h,j},rho^D_{h,j},rho^M_{h,j}), publishes
       M_{h,j}=Com(y_{h,j};rho^M_{h,j}), encrypts the tuple under its registered
       instance key, and proves publicly that D_h, M_{h,j}, and the ciphertext
       contain the same evaluation opening at j;
   disperses the complete ciphertext/proof vector through AVID.

3. Accept:
   a non-target member signs AVAIL(Q,h) only after public verification of every
       ciphertext relation and completion of the AVID disperse instance.
   The acknowledgement depends only on public validity and storage completion.

4. Install:
   receiver j retrieves and decrypts its own payload and checks its opening;
   lambda_h = Lagrange_h(0; H),
   z_j^{r+1} = sum_{h in H} lambda_h f_h(j),
   install generation r+1 only after the frontier and Common-H checks pass.

5. Erase:
   atomically erase z_j^r, rho_j^r, all f_h coefficients, private evaluation openings,
   pending plaintexts, and endpoint keys; retain only the new evaluation,
   C^{r+1}, r+1, and frontier metadata.
```

The new sharing is

```text
F^{r+1}(X) = sum_{h in H} lambda_h f_h(X).
```

The equality proof is between the constant-term commitment of `f_h` and the public
evaluation commitment `C^r(h)`. It proves the required relation without publishing
`z_h^r`. For each receiver `j`, the public verifiable-encryption relation is

```text
R_ved((Q,D_h,pk_Q,j,M_h,j,ct_h,j,j);
      y,rho^D,rho^M,omega):
    EvalOpen(D_h,j;y,rho^D)=1
    and M_h,j=Com(y;rho^M)
    and ct_h,j=Enc(pk_Q,j,(y,rho^D,rho^M);omega,Q,h,j).
```

The receiver-local check repeats both opening tests after decryption; the openings are erased
with the pending subshare. The public transcript contains coefficient commitments,
equality proofs, ciphertexts, `R_ved` proofs, availability acknowledgements, and frontier
labels. None of these objects contains a scalar evaluation.

The key protocol choice is the treatment of invalidity. A malformed receiver ciphertext
causes public descriptor rejection before selection. A receiver does not publish `BAD`,
`KEYREVEAL`, or a recovery point. An accepted proof followed by an invalid decryption is
a verifiable-encryption soundness or encryption-correctness failure. The selection layer
must therefore have the following property:

```text
Common-H: every correct member eventually selects the same H of 2f+1 helpers,
and every selected helper delivers one binding-consistent evaluation to every
correct receiver, including the repair target.
```

If a proposed implementation needs public scalar blame to establish this property,
it is outside the complaint-free candidate. This gives a clean go/no-go test for
opaque ACSS rather than treating public complaint as an unavoidable implementation
detail.

**Lemma 30 (refresh/repair algebra).** Assume `Common-H`, sound equality proofs, and
binding-consistent evaluation delivery. Then every correct receiver computes the same
degree-`2f` polynomial `F^{r+1}` and

```text
F^{r+1}(0) = F^r(0).
```

If at least one honest helper contributes an erased fresh coefficient vector in the
generation interval, the installed sharing is a fresh sharing of the same secret;
the repair target and the non-target receivers enter the same next-generation state.

**Proof.** The first equality follows from Lagrange interpolation and the equality
proof for each selected constant term:

```text
F^{r+1}(0)
  = sum_h lambda_h f_h(0)
  = sum_h lambda_h F^r(h)
  = F^r(0).
```

Common-H gives one coefficient vector `lambda` and one committed evaluation for every
correct receiver. At most `f` selected helpers are Byzantine, so `H` contains an
honest helper. Its fresh coefficients are hidden before installation and erased with
the pending state; the generation-local exposure game accounts for any corruption
before that erase. The result is a state-complete next sharing, not a durable recovery
polynomial. QED

**Proposition 31 (syntactic complaint noninterference).** In the complaint-free
candidate, if `AVAIL` depends only on public descriptor validity and AVID completion,
and a receiver emits no scalar-bearing invalidity message, then the protocol layer creates no public
complaint-to-scalar edge. Consequently,

```text
Adv_Complaint-Noninterference = 0
```

at the wrapper layer; the remaining differences are charged to
`Adv_Opaque-ACSS`, `Adv_EqualityProof`, `Adv_PECC`, `Adv_Common-H`, and
`Adv_Generation-Binding`.

**Proof.** `R_ved` verification is a public predicate over the descriptor. Its accept or
reject result therefore reveals no decryption-dependent branch. `AVAIL` records only that
this public predicate accepted and that AVID dispersal completed. The descriptor and
frontier labels bind every acknowledgement to `Q`; a stale descriptor cannot become an
accepted next-generation state. Thus no public object derives a scalar from the
invalidity event. Any failure of agreement, delivery, proof soundness, or endpoint
erasure is represented by one of the displayed interface terms. QED

The proposition does not prove `Common-H`. It separates the obligations: availability
and agreement must be supplied by an opaque ACSS/ACS transport, while scalar
noninterference follows from the protocol syntax. This is preferable to a public
complaint construction only when the transport can terminate with `2f+1` honest
helpers despite up to `f` withholding members.

**State transition table.**

| State | Accepted input | Public output | Hidden state after transition |
|---|---|---|---|
| `Live(r)` | labelled CSR request below current frontier | descriptor, `R_ved` proofs, availability metadata | old share plus helper temporary state |
| `Pending(r,r+1)` | `Common-H`, retrieval, and local verification | process metadata only | old share, new evaluation, endpoint material |
| `Installed(r+1)` | frontier check and complete receipts | install certificate and new commitment | new share only; old material erased |
| `Retired(T*)` | any old refresh, repair, use, or reveal | rejection metadata only | tombstone/frontier and public metadata |

The table gives the candidate its central invariant:

```text
Retired(c,T*) => no accepted transition has a scalar-bearing target in Cap_old(c).
```

The invariant still requires the `AOR-5` state-machine proof. In particular, a
delayed `READY`, a delayed evaluation, or a pending `F^{r+1}` must not be interpreted
as an install after `T*`. The candidate removes the public complaint edge; it does not
remove the need for frontier absorption or PECC.

**Concrete go/no-go obligations.** The first fixed-committee construction is closed
only if the following four interfaces can be proved for this candidate:

1. publicly verifiable encrypted evaluations and AVID availability give every correct
   receiver the same binding-consistent helper payload under asynchronous withholding;
2. the helper equality proof and `R_ved` proofs are adaptively simulatable and expose no
   scalar evaluation;
3. selective-opening verifiable encryption covers endpoints corrupted before the barrier,
   while `PECC` covers every endpoint corrupted afterward;
4. proactive resharing and repair share one causal generation bound, so cumulative
   mobile exposure never combines evaluations from different installed polynomials.

If these obligations hold, the AOR reduction replaces the previous complaint term by

```text
Adv_AOR^mob(r)
  <= Adv_Opaque-ACSS^r
     + Adv_EqualityProof^r
     + Adv_PECC^r
     + Adv_Common-H^r
     + Adv_Generation-Binding^r
     + negl(lambda).
```

If any obligation requires `KEYREVEAL` or a durable `sid`-local recovery polynomial,
the candidate fails the fixed-committee closure test. The paper then retains the
abstract FGSR theorem and the conditional AOR interface rather than presenting this
route as an unconditional construction. Dynamic committee handoff remains outside
the first theorem.

### 19.63 APSS/hbACSS evidence for the complaint-free candidate

The local source audit gives a narrow, useful mapping for `Common-H`.

APSS defines ACSS so that a completed instance gives every honest node a share of one
degree-`d` polynomial and a polynomial commitment; its termination clause says that
if one honest node terminates, every other honest node eventually terminates, and its
completeness clause gives all honest nodes consistent evaluations
(`/home/yzc/flagg/apss_keyrefresh_2022_1586.txt:290-312`). This is the right local
property for the `f_h` delivery part of `Common-H`. APSS also uses VABA agreement over
a set of validated polynomial proposals (`:394-419`), which is a plausible source for
the common helper-set decision.

The mapping stops there. APSS `GenZeroPoly` publishes the point commitments

```text
w = [g^{p(1)}, ..., g^{p(n)}]
```

and its commitment-revelation phase sends `REVEAL(g^{p(i)}, pi_i)` to all nodes
(`/home/yzc/flagg/apss_keyrefresh_2022_1586.txt:332-355`, `:405-419`). Those objects
are public evaluation artifacts. They cannot be silently classified as harmless
metadata in the first FGSR instance: the typed-edge audit must decide whether they
can participate in a future scalar or aggregate-opening derivation. The complaint-free
candidate therefore reuses the base ACSS/validated-ACS shape only after removing this
public evaluation-revelation phase and adding the helper equality proof
`f_h(0)=F^r(h)`.

APSS does contain a relevant erasure observation: after installing a refreshed share,
a node deletes its old share and the underlying generation protocol must support
graceful exit (`/home/yzc/flagg/apss_keyrefresh_2022_1586.txt:517-558`). This supports
the state-machine direction, but it is not a PECC theorem and its secrecy argument is
static. It does not establish adaptive endpoint exposure, frontier labels, or
retired-coordinate recovery closure.

hbACSS provides the same availability shape in a different interface: its ACSS
protocol broadcasts commitments, privately encrypts evaluations, and uses `OK/READY`
to ensure that a party outputting a share implies enough correct parties hold valid
shares (`/home/yzc/flagg/extract_hbACSS.txt:772-831`, `:1090-1119`). Its actual invalidity
path is public `IMPLICATE` followed by receiver-key revelation, however. That is exactly
the scalar-bearing edge excluded by the complaint-free candidate. The original theorem
also exposes AVID ciphertexts and `t` decryption keys to its simulator
(`/home/yzc/flagg/extract_hbACSS.txt:997-1076`), so it cannot close PECC or adaptive
post-frontier opacity by itself.

Neither source justifies the earlier local-receipt inference. In hbACSS, `OK/READY`
amplification is coupled to implication and share recovery; removing those branches while
keeping only the receipts removes the mechanism that repairs a Byzantine dealer's invalid
target ciphertext. APSS obtains completeness from its full ACSS abstraction, not from a
certificate that a subset of receivers locally verified their own evaluations. The
complaint-free candidate must therefore add public validity for every receiver ciphertext.

**Proposition 32 (source-level Common-H verdict).** APSS-style ACSS plus a validated
ACS can be used as a *conditional transport mapping* for `Common-H` if the adapted
instance satisfies:

1. one accepted helper descriptor implies ACSS completion at every correct receiver,
   including the repair target;
2. the ACS output is one common `H` of `2f+1` descriptors;
3. every receiver ciphertext has a public proof of the committed evaluation relation;
4. availability acknowledgements depend only on public validity and AVID completion;
5. no public evaluation, decryption key, or recovery point is sent; and
6. the adapted transcript has an adaptive, generation-labelled simulator.

The source papers establish nearby functionality for (1)--(2), but do not establish
(3)--(5) for the FGSR corruption game. Hence the current status is:

```text
APSS ACSS/VABA -> Common-H candidate evidence
APSS GenZeroPoly as written -> rejected for opaque FGSR
hbACSS as written -> rejected for complaint-free AOR
```

This is a sharper construction boundary than treating either paper as a black-box
repair primitive. The next proof task is to instantiate the adapted `C_CSR^opaque`
interface and prove its adaptive, scalar-free transcript simulation; no additional
FL baseline or dynamic-committee mechanism is needed for that task.

### 19.64 Formal `C_CSR^opaque` interface and Common-H theorem

The previous audit can be reduced to a small transport interface. For a request
`Q=(rid,c,r,T_req,C^r,u,O_c)`, an instance for helper `h` exposes:

```text
Desc_h(Q) = (Q, D_h, pi_eq,h,
             {pk_Q,j,M_h,j,ct_h,j,pi_ved,h,j}_j, AvailCert_h)
Retrieve_h(j) -> (y_{h,j},rho^D_{h,j},rho^M_{h,j}) [private after decryption]
Avail_h(a)    -> AVAIL(Q,h,a)                 [public storage metadata]
```

The order context is

```text
O_c = (prefix_c, rank_c(rid), parent_c, T_req, OrderCert_c)
```

where `OrderCert_c` is a non-forgeable agreement certificate for the unique position
of `rid` in the coordinate-local instance order. A retirement certificate is another
ordered event in the same `prefix_c`; it dominates every pending instance that does
not precede it. Correct nodes accept only a certificate extending their local prefix,
and two accepted certificates for the same rank must have the same context or expose an
agreement failure.

The interface is accepted only if the following conditions hold.

| Condition | Required meaning |
|---|---|
| `D1` | `Desc_h` is bound to the complete `Q`, `O_c`, the helper identity, one generation, and the unique `OrderCert_c` position |
| `D2` | `pi_eq,h` proves `f_h(0)=F^r(h)` without exposing either scalar |
| `D3` | for every receiver `j`, `pi_ved,h,j` publicly proves `R_ved`; an accepted descriptor binds `M_{h,j}` and every ciphertext to the unique committed evaluation at `j` |
| `D4` | `AvailCert_h` contains `2f+1` non-target `AVAIL` signatures; each honest signer verified the complete public descriptor and completed the AVID disperse instance |
| `D5` | `AVAIL` depends only on public validity and storage completion, and the public transcript contains no evaluation, decryption key, recovery point, or scalar-reconstructible combination |
| `D6` | private evaluations, openings, buffers, endpoint keys, and every pending instance not preceding retirement are covered by one atomic `CancelOrRetire`/generation erase barrier and `PECC` |

Let `ACS^-` run over `P^- = P \ {u}` and return a common set `V` of valid helper
descriptors. Define

```text
H = Canonical_{2f+1}(V).
```

The canonical rule is deterministic and depends only on public labelled descriptors;
it never depends on a hidden evaluation. A valid `AvailCert_h` is an authenticated
statement that at least `f+1` correct parties completed the same publicly valid AVID
dispersal; its interpretation is supplied by `D3`--`D4`, not by the mere existence of a
commitment.

**Theorem 33 (conditional Common-H for `C_CSR^opaque`).** Assume:

1. `ACS^-` satisfies agreement, validity, and termination against at most `f`
   Byzantine participants;
2. every honest helper can generate a valid `Desc_h` and an opaque instance satisfying
   `D1`--`D6`;
3. a valid descriptor accepted by `ACS^-` carries public `R_ved` proofs satisfying `D3`
   and an `AvailCert_h` satisfying `D4`;
4. the underlying AVID satisfies correctness and availability once `f+1` correct parties
   complete dispersal, and the encryption and local opening checks are correct; and
5. `|P^-|=3f+1`, while the target `u` is a correct receiver for a repair request.

Then:

```text
Common-H Agreement: all correct receivers compute the same H;
Common-H Availability: every h in H eventually delivers one binding-consistent
evaluation to every correct receiver, including u;
```

and the probability of failure is bounded by

```text
Adv_Common-H^r
  <= Adv_ACS-Agreement^r
     + Adv_ACS-Validity^r
     + Adv_ACS-Termination^r
     + Adv_AVID-Correctness/Availability^r
     + Adv_Rved-Soundness^r
     + Adv_Label-Binding^r
     + negl(lambda).
```

**Proof.** ACS agreement makes every correct receiver obtain the same valid descriptor
set `V`; the deterministic canonical rule therefore gives the same `H`. Since
`|P^-|=3f+1` and at most `f` participants are Byzantine, at least `2f+1` honest
helpers can produce valid descriptors. ACS validity excludes a descriptor that lacks
the required availability evidence, and termination eventually decides from the
honest proposals.

For each `h in H`, an `AvailCert_h` contains `2f+1` non-target `AVAIL` signatures.
At most `f` signers are Byzantine, so at least `f+1` correct signers completed the same
AVID disperse instance. AVID availability therefore lets every correct receiver,
including the target, retrieve its ciphertext from the unique dispersed vector. Public
`R_ved` soundness binds that ciphertext to the unique opening of `D_h` at the receiver's
index; encryption correctness and the local opening check return that evaluation. `D1`
and label binding prevent a certificate or ciphertext proof from moving between requests
or generations. A violation is charged to the corresponding term in the displayed bound.
QED

The theorem deliberately separates `Common-H` from privacy. It proves that the
selected helper set and private evaluations are available; selective-opening simulation,
`D5`, and `D6` keep the publicly verifiable ciphertext vector from becoming a future
opening capability. APSS supplies nearby ACSS/VABA functionality, but its public
`REVEAL` phase does not satisfy `D5`. The first concrete implementation must therefore
prove `C_CSR^opaque` after adapting, not merely cite the APSS theorem.

The `OrderCert_c` requirement is part of the transport interface rather than an
implementation detail. Without it, `D1` binds a repair to a label but not to a unique
position relative to retirement, and `D6` cannot determine which pending outputs must be
erased. In that case Lemma 47 remains an unproved state-machine assumption.

**Corollary 34 (complaint-free AOR reduction).** If `C_CSR^opaque` additionally
satisfies the FGSR frontier guard and atomic installation/erase conditions, then the
wrapper contributes no public complaint-to-scalar edge, and the per-generation AOR
advantage is bounded by

```text
Adv_AOR^mob(r)
  <= Adv_C_CSR^opaque^r
     + Adv_Frontier-Use^r
     + Adv_Recovery-Localization^r
     + Adv_Joint-AO^mob(r)
     + negl(lambda).
```

This is the current concrete proof target. It is stronger than reusing a standard
ACSS correctness theorem and narrower than claiming that APSS or hbACSS already
realizes long-lived privacy finality.

### 19.65 Pedersen equality proof and opening-state obligation

The `D2` equality proof requires a precise hidden witness. Let the current sharing
commitment be `C^r=(C_0^r,...,C_{2f}^r)` with

```text
C_k^r = Com(a_k^r; alpha_k^r),
E_h^r = product_k (C_k^r)^{h^k}
      = Com(F^r(h); rho_h^r).
```

Helper `h` chooses `f_h(X)=z_h^r+sum_{k=1}^{2f}a_{h,k}X^k` and its coefficient
commitments `D_{h,k}=Com(a_{h,k}; beta_{h,k})`. The helper equality relation is

```text
R_eq(E_h^r, D_{h,0}; z, rho, beta_0):
    E_h^r   = Com(z; rho)
    D_{h,0} = Com(z; beta_0).
```

The helper proves `R_eq` in zero knowledge using the current local witness
`(z_h^r,rho_h^r)` and the new constant-term randomness `beta_{h,0}`. The proof reveals
neither `z_h^r` nor either opening. Each receiver obtains its private evaluation
opening `(y_{h,j},sigma_{h,j})` and checks

```text
EvalOpen(D_h,j;y_{h,j},rho^D_{h,j}) = 1
and M_{h,j} = Com(y_{h,j};rho^M_{h,j}).
```

This relation explains why `rho_h^r` must be part of the current state in the Pedersen
version. A node that stores only `z_h^r` can either reveal the share, use a public
Feldman-style evaluation artifact, or assume an unprovided proof witness. Each option
violates one of the first-instance opaque-state conditions. Thus the state ledger must
contain `rho_j^r` and erase it together with `z_j^r` at installation and retirement.

**Lemma 35 (local opening consistency).** If the commitment scheme is binding and the
evaluation proof for `R_eq`, the public `R_ved` proof, and the receiver-local opening check
verify, then every accepted `Retrieve_h(j)` is bound to the same `f_h` and to a unique evaluation
`f_h(j)`, except with the commitment/proof soundness advantage.

**Proof.** The `R_eq` proof binds the constant message of `D_{h,0}` to the message in
`E_h^r`, hence to `F^r(h)`. The evaluation equation is a valid opening of the committed
polynomial at `j`; a second accepted message gives two openings of one binding
commitment. Therefore the accepted value is unique, and the local opening remains
private until the receiver's erase event. QED

The lemma closes the algebraic meaning of `D2`, but it does not close adaptive proof
simulation. The remaining simulator must answer a later corruption of `h` with a state
consistent with all published commitments while withholding `rho_h^r` after the erase
barrier. That obligation remains part of `Adv_EqualityProof` and `Adv_PECC`; it is not
provided by ordinary Pedersen hiding alone.

### 19.66 The `EqProof^mob` game

The previous obligation is now isolated as a state-layer game. For each labelled
context `Q`, the challenger exposes the public statements

```text
(E_h^r, D_{h,0}, C^r, C_h, Q)
```

and lets the adversary adaptively choose corruption, delivery, installation, and
retirement events. Before the generation barrier, corruption of helper `h` returns
`(z_h^r,rho_h^r)` and any pending new-polynomial witness that the real endpoint holds.
After the barrier, it returns the installed next-generation state or the retirement
tombstone, but no erased opening.

An `EqProof^mob` interface must satisfy four properties:

1. **Statement consistency:** every accepted `pi_eq,h` is bound to the same
   `(Q,E_h^r,D_{h,0})` and cannot be replayed across helper, coordinate, or generation;
2. **Adaptive simulation:** after the public commitments are fixed, the simulator can
   produce a proof for an unexposed witness and later answer either a pre-barrier
   corruption with a consistent witness or a post-barrier corruption without the
   erased witness;
3. **Extraction/soundness:** an accepted proof yields the two-opening relation, so a
   helper cannot install a constant term different from `F^r(h)`;
4. **Branch noninterference:** proof verification and `AVAIL` selection do not use a
   hidden witness to select a scalar-bearing public branch.

Define

```text
Adv_EqProof^mob
  = |Pr[Real_EqProof^mob=1] - Pr[Sim_EqProof^mob=1]|.
```

If a dual-mode/equivocal commitment and a simulation-extractable proof system provide
these four properties under one labelled CRS, then the `C_CSR^opaque` reduction may
charge the equality layer as `Adv_EqProof^mob` plus the commitment and proof-system
advantages. Ordinary commitment hiding only hides a fixed commitment; it does not
answer a later corruption with an opening that matches the published relation, and
ordinary proof zero knowledge does not automatically provide post-erase state
consistency. Those gaps remain explicit until a chosen proof system supplies them.

**Corollary 36 (state-aware `D2`).** Replacing `D2` by `EqProof^mob` and adding the
opening `rho_j^r` to the `PECC` state yields the per-generation bound

```text
Adv_C_CSR^opaque^r
  <= Adv_AVID-Correctness/Availability^r
     + Adv_ACS^r
     + Adv_EqProof^mob(r)
     + Adv_CSO-VE^r
     + Adv_PECC^r
     + Adv_Rved-Soundness^r
     + Adv_Label-Binding^r
     + negl(lambda).
```

This is the next concrete proof target. The main FGSR theorem remains independent of
the choice of proof system; a failed `EqProof^mob` instantiation leaves the conditional
interface in place and does not invalidate `Robust-Hitting`, `AOR-5`, or
`Recovery-Closure`.

### 19.67 Local evidence for `EqProof^mob`

The local papers provide adjacent proof mechanisms but no direct instantiation of the
game above.

| Source | Reusable interface | Missing property for `EqProof^mob` |
|---|---|---|
| Choudhuri et al. | `Setup`, `Prove`, `Verify`, `SimProve`, weak simulation-extractability, and straight-line extraction (`usenixsecurity25-choudhuri.pdf_by_PaddleOCR-VL-1.6.md:211-243`) | The protocol theorem is for a static adversary and ciphertext/PPE statements (`:302-308`); it does not expose or erase Pedersen opening state after adaptive corruption |
| Threshold Encryption with Silent Setup | simulation-extractable proof material for ciphertext components and CCA partial decryption | the relation is not the two-opening current-share relation, and periodic key/CRS state does not define FGSR generation-local erasure |
| VSSR | Pedersen commitment binding/hiding, private share witnesses, and local recovery verification (`Efficient Verifiable Secret Sharing with.pdf_by_PaddleOCR-VL-1.6.md:99-105`, `:276-279`) | its hiding game uses `compromise`/`contrib` queries with a per-commitment legitimacy bound (`:200-206`), not a monotone frontier or post-erase corruption oracle |

The correct conclusion is conditional rather than negative: Choudhuri's `SimProve`
could be a proof-system component if its relation is instantiated as `R_eq` and its
CRS/trapdoor is integrated with the adaptive commitment and erasure game. The source
does not supply that integration. VSSR supplies the commitment/evaluation algebra, but
its recovery security cannot be relabelled as `EqProof^mob`.

The current concrete go/no-go test is therefore:

```text
DM-SE-NIZK^{R_eq,adaptive} + adaptive commitment state + PECC
    -> EqProof^mob
```

Until the left side is proved as one joint interface, `Adv_EqProof^mob` remains an
explicit term in `Adv_C_CSR^opaque`; the abstract FGSR theorem is unaffected.

### 19.68 Conditional hybrid for `EqProof^mob`

Assume a dual-mode commitment/proof setup with a real mode and a simulation mode.
For `R` causally ordered repair generations, define the following hybrids. All
contexts, labels, ACS outputs, `AVAIL` decisions, and frontier transitions are kept
identical across the hybrids.

```text
H0  Real commitments, real R_eq proofs, real private endpoint state.
H1  Replace the real labelled CRS by the simulation/equivocation CRS.
H2  Replace every R_eq proof by SimProve on the same public statement.
H3  Use equivocation to assign unexposed commitment openings after the public
    statements are fixed; answer each pre-barrier corruption with a consistent
    witness and each post-barrier corruption without the erased witness.
H4  Replace post-barrier private endpoint and buffer state by the PECC simulator,
    retaining only the installed next-generation state or the tombstone.
H5  Reject any proof or receipt whose context, generation, or frontier label is
    inconsistent; charge a successful bypass to soundness or label binding.
```

The adaptive-opening step in `H3` is a separate interface. Define
`Adv_Equivocal-Opening^mob` as the distinguishing advantage of an adversary that sees
the public commitment before choosing the corruption schedule and then distinguishes
real openings from openings produced by the equivocation simulator. The simulator is
required to answer only openings that the real state oracle would reveal; an erased
`rho_j^r` is never reopened.

**Proposition 37 (conditional `EqProof^mob` lifting).** If the labelled CRS switch is
indistinguishable, `SimProve` supports polynomially many concurrent adaptive
statements, the commitment supports `Adv_Equivocal-Opening^mob`, and the endpoint
channel satisfies `PECC`, then

```text
Adv_EqProof^mob(R)
  <= R * (Adv_CRS-Mode
          + Adv_SE-NIZK-Simulation
          + Adv_Equivocal-Opening^mob
          + Adv_PECC
          + Adv_Eq-Soundness
          + Adv_Label-Binding)
     + R*negl(lambda).
```

**Proof sketch.** `H0 -> H1` uses the CRS-mode indistinguishability. In `H1 -> H2`,
the simulation trapdoor replaces each equality proof while preserving the complete
public statement and its label; concurrency and adaptive statement selection are
covered by the assumed multi-simulation property. In `H2 -> H3`, the equivocal
commitment simulator fixes hidden openings consistently with all statements already
published and answers a corruption oracle according to the barrier time. A pre-barrier
answer contains the matching `(z,rho)` witness; a post-barrier answer omits it. The
opening game charges the difference. `H3 -> H4` removes endpoint ciphertexts,
plaintexts, and pending openings at the prescribed erase event by PECC. Finally,
`H4 -> H5` rejects stale or cross-context branches; a successful invalid proof or
label transfer is charged to extraction/soundness or label binding. Apply the hybrid
for each causally ordered generation and take a union bound. QED

The proposition does not claim that a static SE-NIZK theorem supplies the bound. It
requires adaptive, concurrent simulation and a commitment state game coupled to PECC.
It also covers only the state-layer equality relation: any proof branch that reads
client ciphertexts, aggregate descriptors, or partial decryptions must remain in
`Joint-AO^mob` rather than being absorbed into `EqProof^mob`.

### 19.69 Janus mapping for `Adv_Equivocal-Opening^mob`

Janus supplies the closest local evidence for the `H1`--`H3` portion of the hybrid.
Its backbone uses perfectly hiding Pedersen VSS commitments, encrypts evaluations to
recipients, and erases each sharing polynomial after the values needed later have been
sent (`/home/yzc/flagg/adaptive_dkg_2026_892.txt:417-462`). Its simulator programs the
random oracle so that dummy ciphertexts can later decrypt to the state returned after
adaptive corruption (`:896-911`). The formal protocol assumes secure erasure,
adaptively secure public-key encryption, authenticated/reliable broadcast, and
straight-line extractable NIZK PoK (`:518-545`).

The mapping to the `EqProof^mob` hybrids is:

| Hybrid/interface | Janus evidence | FGSR status |
|---|---|---|
| `H1` CRS/commitment mode | Pedersen hiding and simulator-selected first honest contribution | candidate local support, not a labelled `R_eq` CRS theorem |
| `H2` proof simulation | simulated key/share consistency proofs in the ideal execution | requires a proof for the exact two-opening `R_eq` relation |
| `H3` adaptive opening | erased sharing polynomial plus programmable hashed-ElGamal equivocation | candidate support for delivery state, subject to endpoint labels and corruption timing |
| `H4` PECC | secure-erasure and adaptive-PKE assumptions | does not cover FGSR receiver buffers, pending evaluations, or retired `sid` state |
| `H5` frontier absorption | none in the DKG functionality | must be supplied by the FGSR wrapper |

Janus therefore reduces the uncertainty around `Adv_Equivocal-Opening^mob`, but does
not set it to zero. To use it, the wrapper must prove that a Janus-style ciphertext
and commitment state can be labelled by `(rid,sid,ell,r,T_req,h,j)`, that every
pre-frontier corruption is inserted into `X_hist`, and that all post-frontier
decryption, complaint, and recovery edges are rejected. Janus's identifiable-abort
mechanism deliberately makes a disputed ciphertext publicly decryptable
(`/home/yzc/flagg/adaptive_dkg_2026_892.txt:464-470`), so it remains outside the
complaint-free `C_CSR^opaque` path unless that event is removed or charged before the
frontier.

**Proposition 38 (local Janus substitution).** Suppose a Janus-style transport is
restricted to the no-complaint branch and satisfies the labelled endpoint and frontier
conditions above. Then it can replace the commitment/encryption state layer in
`H1`--`H4`, yielding

```text
Adv_Equivocal-Opening^mob
  <= Adv_Janus-Equivocation
     + Adv_Janus-PKE
     + Adv_Janus-Erasure
     + Adv_R_eq-Simulation
     + Adv_Label-Binding
     + Adv_PECC
     + negl(lambda).
```

The proposition is a transport substitution, not a concrete FGSR theorem. It leaves
`Common-H`, `AOR-5`, `Joint-AO^mob`, and recovery-state localization unchanged. In
particular, the Janus result is evidence that the adaptive opening interface is
plausible; it is not evidence that the full privacy-finality construction is closed.

### 19.70 Main theorem proof matrix and paper-level go/no-go

The proof should now be organized as a single auditable chain rather than as a
collection of protocol features. The relevant statement is privacy finality for
aggregate-only asynchronous secure aggregation; the resharing mechanism is only one
way to satisfy the state-layer premises.

| Claim | Required object | What must be shown | Current status | Failure consequence |
|---|---|---|---|---|
| `C_FGSR` is correct | `Common-H` and target-excluded availability | Correct nodes install the same next-generation sharing state, and a target is not needed for helper progress | conditional on ACS, PVOD public validity, AVID availability, and `R_ved` soundness | no usable repair protocol |
| Retirement is absorbing | frontier gate, generation labels, tombstone, atomic erase | A post-frontier message cannot create a new recovery or installation edge | abstractly isolated by `AOR-5`; concrete transport pending | no-resurrection attack applies |
| Recovery is localized | typed edge ledger and `RCL` | Every scalar recovery path is historical exposure, current-share closure, or an explicitly charged data-plane edge | abstract theorem complete; concrete opaque repair conditional | hidden recovery edge remains |
| State transcript is simulatable | `RCL-Sim/AO`, `EqProof^mob`, `PECC` | Adaptive corruption after commitment publication does not reveal an erased witness, endpoint key, evaluation, or buffer that enlarges closure | explicit advantage terms retained | conditional result only |
| Aggregate opening is noninterfering | `Joint-AO^mob` | Multi-coordinate proofs, certificates, and partial decryptions cannot become an individual-key opening oracle | game frozen; lifting not closed | data-plane term cannot be absorbed into `RCL` |
| Privacy finality holds | `F_PF^mob` and composition hybrid | After the retirement frontier, the challenged individual update is indistinguishable while aggregate correctness remains available | conditional main theorem below | paper must state a conditional theorem |

The intended composition is therefore:

```text
Common-H correctness
  + Frontier absorption / AOR-5
  + Recovery-State Localization
  + RCL-Sim/AO
  + Joint-AO^mob
  + PECC and EqProof^mob
  => Privacy-Finality for aggregate-only asynchronous secure aggregation.
```

**Theorem 39 (conditional BF-RPTA composition).** Fix a committee with
`n=3f+2`, `q_dec=q_rec=2f+1`, a fully asynchronous authenticated network, and a
causal-generation-bounded mobile adversary. Suppose every repair context satisfies
`Common-H`, the frontier is absorbing, the state is complete, and the interfaces
`RCL-Sim/AO`, `Joint-AO^mob`, `EqProof^mob`, and `PECC` hold for all concurrent
contexts. Then the distinguishing advantage in the aggregate-only
`F_PF^mob` game is bounded by

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
     + negl(lambda).
```

The proof is ordered by capability type. First, `Common-H` and ACSS correctness
replace the real repair transcript with a common next-generation state. Second,
frontier absorption removes all post-retirement install, reveal, and recovery edges.
Third, `RCL-Sim/AO` simulates the remaining state-layer edges and charges every
unclassified scalar path to its explicit advantage. Fourth, `Joint-AO^mob` replaces
the aggregate data-plane view while preserving all authorized aggregate outputs.
Finally, `EqProof^mob` and `PECC` justify the adaptive commitment and endpoint-state
hybrids. The localization lemma ensures that no edge is used by two hybrids under
different types; this is the point at which ordinary forward secrecy would be
insufficient.

This theorem is deliberately conditional. In particular, `Adv_ACSS-opaque`,
`Adv_EqProof^mob`, and `Adv_Joint-AO^mob` cannot be set to zero merely by citing
hbACSS, Janus, Pedersen hiding, or a static aggregate-encryption theorem. A concrete
paper instantiation is publishable only after each term is either reduced to a stated
primitive assumption or retained as an explicit interface. The first concrete audit
is consequently the pair `(R_eq, Joint-AO^mob)`, not dynamic membership or another
FL workload.

The matrix also fixes the paper-level go/no-go rule. If a public complaint,
evaluation, partial decryption, or proof-controlled branch yields an individual-key
capability, the corresponding term remains outside `RCL-Sim/AO`; the construction is
then a conditional framework with a sharp separation result, not an unconditional
FGSR instantiation. This is a theorem boundary, not an implementation detail.

### 19.71 `R_eq` notation audit: share relation versus aggregate relation

The current proof uses the name `R_eq` for two algebraically different relations.
They must be separated before any concrete lifting is attempted. Otherwise a proof for
the helper's current-share consistency can be incorrectly counted as a proof for the
client data plane.

| notation | statement and witness | public objects | view / interface |
|---|---|---|---|
| `R_eq^share(Q,h)` | `(E_h^r,D_{h,0},Q)` with witness `(z_h^r,rho_h^r,beta_{h,0})` | helper equality proof, coefficient commitments, public-validity `AVAIL` | `StateView`; requires `EqProof^mob`, `CSO-VE`, `PECC`, and generation binding |
| `R_eq^agg(s,u)` | aggregate context, client ciphertext, weight and encryption relation with witness containing the client mask/key material | client consistency proof, aggregate certificate, ciphertext-specific partial decryption | `DataView_b`; requires the single joint `Joint-AO^mob` challenge |

The first relation is the one formalized in Sections 19.65--19.69. It binds a helper's
new polynomial constant to its old current share without revealing that share. Its
statement is state-only only when `Q` is independent of challenge-dependent client
objects and when proof verification cannot select a scalar-bearing data branch.

The second relation is the object-level relation classified in Section 19.47. Its
statement reads challenge ciphertexts, weights, aggregate descriptors, or their
encryption context. Even if the proof is zero knowledge and even if a partial
decryption does not reveal a plaintext, the transcript is challenge-dependent and can
distinguish two equal-sum key vectors. It therefore belongs to `DataView_b` and cannot
be discharged by `EqProof^mob` or `RCL-Sim/AO`.

**Lemma 40 (typed equality separation).** Assume `R_eq^share` is label-bound and
adaptively simulatable with post-erase `PECC`, and assume every `R_eq^agg` proof,
certificate, partial decryption, and publication branch is generated inside one
`Joint-AO^mob` challenge. Then the two equality layers compose without creating a new
cross-layer recovery edge:

```text
Adv_equality
  <= Adv_EqProof^share,mob
     + Adv_Joint-AO^mob
     + Adv_Label-Binding
     + Adv_PECC
     + negl(lambda).
```

**Proof sketch.** Simulate `R_eq^share` while exposing only the labelled repair state;
its witness is either in the pre-barrier history or unavailable after erasure. Next,
replace the complete `R_eq^agg` and aggregate transcript with the one joint data-plane
challenge. The proof-noninterference condition prevents the state-layer simulator from
choosing a client ciphertext, partial decryption, or aggregate branch. A violation of
that condition is a new data-plane edge and is charged to `Adv_Joint-AO^mob`, not hidden
inside the equality-proof term. Label binding prevents either relation from being
replayed across coordinate, generation, or repair context. QED

This audit changes the concrete go/no-go test. A candidate may reuse the same proof
system for both relations, but it must prove two different simulation interfaces:
adaptive post-erase simulation for `R_eq^share`, and concurrent challenge-dependent
simulation under `Joint-AO^mob` for `R_eq^agg`. A static `SimProve` theorem for one
relation does not close the other. Until both interfaces are supplied, the main result
remains the conditional BF-RPTA theorem of Section 19.70.

### 19.72 Local literature verdict for `R_eq^agg` and `Joint-AO^mob`

The local evidence does not close the aggregate relation. TACITA's modified STE
extended-CPA game lets the adversary choose the corrupted set after the CRS but before
the honest keys, challenge messages, and aggregate ciphertext are generated
(`/tmp/tacita-2025-1579.txt:2529-2565`). It supports ciphertext-specific partial
decryptions and equal-sum challenge vectors, which is useful evidence for the
aggregate-only data plane. However, the source explicitly notes that the stronger game
with adaptive corruption is not discussed and is outside its scope
(`/tmp/tacita-2025-1579.txt:2565-2577`). The game has no repair oracle, frontier,
post-challenge endpoint exposure, or erased-state return.

Choudhuri et al. define `Setup/Prove/Verify/SimProve` and weak
simulation-extractability for well-formed batched-threshold ciphertext statements
(`usenixsecurity25-choudhuri.pdf_by_PaddleOCR-VL-1.6.md:211-241`). Their main theorem
is for a static PPT adversary in the dealer model (`:302-308`), and the simulator
extracts corrupt ciphertext witnesses and programs a random oracle for honest
ciphertexts (`:699-779`). This is a valid local component for proof soundness and
static ciphertext simulation, but it does not define adaptive corruption after a
published statement, post-erase endpoint state, or the `R_eq^agg` publication branch
inside a long-lived joint challenge.

The resulting audit table is:

| source | supports | missing for `R_eq^agg` / `Joint-AO^mob` |
|---|---|---|
| TACITA modified STE | equal-sum aggregate challenge; ciphertext-bound partial decryption; adaptively chosen adversarial ciphertexts | adaptive committee corruption, repair/retirement oracle, future state exposure, concurrent proof branch simulation |
| Choudhuri et al. SE-NIZK | static `SimProve`, extraction, well-formed ciphertext/PPE statements | adaptive post-publication state consistency, erased endpoint state, FGSR labels, joint mobile challenge |
| ordinary Pedersen hiding | hiding of a fixed commitment | no adaptive opening consistency and no data-plane noninterference |
| Janus transport | local adaptive equivocation and erasure evidence | aggregate-only output, `R_eq^agg`, frontier absorption, and complaint-free recovery |

Thus no cited source justifies the substitution

```text
TACITA Static-AO + Choudhuri SimProve
    -> Joint-AO^mob
```

without a new lifting theorem. The first concrete construction is therefore at a
go/no-go boundary: either prove an adaptive threshold-encryption/argument lifting that
adds the missing state and branch interfaces, or present `Joint-AO^mob` as an explicit
assumption and make the sharp separation from static aggregate opening a central
theoretical result. The latter remains a coherent paper result; it must not be written
as an unconditional concrete instantiation.

### 19.73 Sharp separation attack: static aggregate opening does not imply finality

The previous audit gives a semantic separation. The following construction gives a
matching attack and shows that no black-box reduction from static aggregate opening to
`Joint-AO^mob` can exist without an additional state/exposure premise.

Consider a threshold aggregate-encryption protocol with a fixed public key and
committee shares `sk_1,...,sk_n`. Clients encrypt individual mask keys
`k_1,...,k_m`, while the protocol reveals only the decryption of the aggregate
`K=sum_u k_u`. Assume the protocol is correct and satisfies a TACITA-style static
aggregate-opening game for every corruption set of size at most `f`.

The mobile adversary proceeds as follows:

1. Before the challenge, it chooses an admissible corruption set of at most `f` and
   observes the public ciphertexts and aggregate context.
2. It submits two key-vector families `K_0,K_1` with the same aggregate but different
   target component `k_{u*,0} != k_{u*,1}`. Static aggregate opening gives the same
   authorized aggregate output in both worlds.
3. After the challenge, it corrupts three disjoint groups `B_1,B_2,B_3` of sizes
   `f,f,1` in three successive corruption intervals, releasing each group before
   moving to the next. This respects the instantaneous bound and exposes exactly
   `2f+1=q_dec` shares. Since `n=3f+2`, the three groups fit in the committee. If no
   state-complete refresh occurs, the adversary retains all exposed shares of the fixed
   key.
4. It reconstructs `sk`, decrypts the target ciphertext, and compares the recovered
   component with `k_{u*,0}` and `k_{u*,1}`.

The instantaneous corruption bound is respected at every step. The attack succeeds
because the static game ends before the post-challenge corruption oracle and therefore
does not charge the accumulated shares. The same attack applies to a refreshed protocol
if a retired coordinate retains a recovery object that can reconstruct an old share;
the adversary waits until the object is exposed, invokes it, and performs the same
individual decryption.

**Theorem 41 (black-box separation).** There exists a protocol that is correct and
secure in the static aggregate-opening game, but fails `Privacy-Finality` against a
causal-generation-bounded mobile adversary. Therefore a reduction of the form

```text
Static-AO + correctness -> Joint-AO^mob / Privacy-Finality
```

is impossible without at least one of the following additional premises:

```text
state-complete proactive refresh + frontier erasure
or an adaptive aggregate-opening theorem with post-challenge exposure
or an equivalent recovery-state localization condition.
```

**Proof.** In the static game, the corrupted set is fixed before the challenge and
contains fewer than the decryption threshold, so the adversary sees only the equal
aggregate output and cannot recover the target component. In the mobile execution,
the adversary's accumulated exposure contains enough shares to reconstruct the fixed
secret key, or enough retained recovery state to reconstruct an old share. The target
ciphertext is then individually opened, distinguishing the two equal-sum worlds with
overwhelming probability. The execution satisfies the instantaneous corruption bound,
so the distinguishing event is permitted by the mobile model but absent from the
static game. Hence static aggregate security does not imply privacy finality. QED

The theorem is deliberately primitive-independent. It does not claim that every
concrete threshold-encryption scheme suffers this attack; it identifies the missing
premise that a concrete scheme must prove. `Joint-AO^mob` is precisely the interface
that adds this premise to the data-plane game, while `Recovery-Closure` adds it to the
repair/state layer.

### 19.74 Formal ideal functionality `F_PF^mob`

The lower bound and the composition theorem use one fixed target session and one
authorized aggregate descriptor. This is a selective single-descriptor security game;
it does not give the adversary an adaptive database-query oracle. Adaptive behavior is
limited to corruption, message scheduling, recovery, and state exposure.

For a session `sid`, let

```text
D_sid = (S_sid, w_sid, H_ct, H_out, tag_sid)
```

be the unique aggregate descriptor. `F_PF^mob` maintains
`phase_sid in {Open, Closed, Retired}`, a monotone frontier `T_sid`, the accepted
descriptor, the authorized aggregate, and the send-time history `X_hist`. Its commands
are:

```text
Bind(sid, D_sid) -> CC_sid or reject
Submit(sid, u, x_u) -> accept or reject
OpenAggregate(sid, CC_sid) -> y_sid or reject
Retire(sid, PC_sid) -> PF_sid or reject
Publish(Q, m) -> public event or reject
Process(Q, m, T_local) -> accept or reject
Recover(rid, target, T_req, opaque_state) -> receipt or reject
Corrupt(i, t) -> Leak_i(t)
```

The functionality enforces the following semantics:

1. `Bind` accepts only one descriptor for `sid`; a conflicting set, weight vector,
   ciphertext digest, tag, or output context is rejected permanently.
2. `Submit` accepts client updates only before `CC_sid` is fixed. `OpenAggregate`
   returns exactly

   ```text
   y_sid = sum_{u in S_sid} w_u * x_u
   ```

   and never returns an individual update, mask key, share, or individual decryption
   result.
3. `Retire` accepts only a valid privacy-finality certificate whose retirement set
   satisfies `A_sid in H_b(Gamma_dec)`. It changes `phase_sid` monotonically to
   `Retired`, joins the frontier, and returns `PF_sid`; it never releases additional
   client-dependent data.
4. `Publish` records a legal public capability at its send event. A key, point, or
   recovery material published before retirement remains in `X_hist` even if its
   receive event occurs later. A post-retirement publication that would carry an old
   capability is rejected.
5. `Process` and `Recover` may accept only messages whose labels and frontier dominate
   the local state. They may produce a current state for live coordinates, but no
   accepted transition can produce a capability for a coordinate already in
   `Retired`.
6. `Corrupt(i,t)` returns only the leakage allowed at that point: pre-frontier
   readable state and previously exposed history before retirement; after retirement,
   the current generation state, public frontier metadata, and tombstone, but no erased
   old share, opening, endpoint key, pending plaintext, or recovery-complete old state.

The ideal functionality does not claim that software erasure is physically observable.
It specifies the security contract: any object that remains readable after the erase
event is part of `Leak_i(t)` and must be covered by `RCL-Sim/AO` or `PECC`. Likewise,
`CC_sid` and `PF_sid` are different outputs: the former certifies which aggregate was
opened, while the latter certifies that the old recovery closure is no longer allowed.

#### `Exp_PF^mob` and ideal leakage

To define privacy, the challenger first fixes `sid`, `D_sid`, the accepted client set,
the weight encoding, and the complete pre-challenge public context. The adversary then
submits two update families `X_0,X_1` satisfying

```text
sum_{u in S_sid} w_u*x_{u,0}
  = sum_{u in S_sid} w_u*x_{u,1}.
```

The challenger samples `b`, runs `F_PF^mob` with `X_b`, and answers every
protocol-valid corruption, scheduling, `Publish/Process`, retirement, and recovery
event that satisfies only the external exposure budget and label/frontier syntax. The
game does not reject a query because its response might reveal an
individual-opening capability. Such a response remains in the view and is evidence
against privacy finality; `CapSafe` is a theorem obligation, not an admissibility rule.
The adversary receives

```text
View_b = (PublicContext, CC_sid, y_sid, PF_sid,
          X_hist, CurrentStateAfterErase, RecoveryTranscript),
```

with data-dependent ciphertexts, consistency proofs, certificates, and partial
decryptions generated under the single `Joint-AO^mob` challenge. It outputs `b'`, and

```text
Adv_PF^mob(A)
  = |Pr[b'=1 in Exp_PF^mob(1)]
      - Pr[b'=1 in Exp_PF^mob(0)]|.
```

`F_AWF` is the control-plane projection of this functionality: it specifies monotone
frontier merging and capability absorption but does not define client updates or the
aggregate-only output. `F_PF^mob` adds the data-plane confidentiality contract and the
future-state exposure view. Consequently, proving `F_AWF` or ordinary forward secrecy
alone does not realize `F_PF^mob`.

**Definition boundary.** `CC_sid` guarantees aggregate correctness and uniqueness;
`PF_sid` guarantees that every legal future recovery path is closed for the retired
coordinate. A protocol that produces `CC_sid` but cannot satisfy the `Retire`,
`Publish`, `Process`, and `Corrupt` semantics above realizes aggregate correctness but
not privacy finality.

### 19.75 FGSR-to-`F_PF^mob` realization map

The FGSR wrapper is a state-layer protocol and does not itself define the client
aggregate. In particular, its operation named `ReshareAggregate(Q,H)` combines helper
polynomials; it must not be confused with `F_PF^mob`'s `OpenAggregate`, which releases
the authorized weighted sum of client updates. The realization map is:

| `F_PF^mob` interface | FGSR/data-plane operation | proof obligation |
|---|---|---|
| `Bind(sid,D_sid)` | ACS context binding and unique `CC_sid` | one accepted set, weight vector, tag, ciphertext digest, and output context |
| `Submit(sid,u,x_u)` | client encoding and `Joint-AO^mob` challenge input | no individual update enters a public recovery transcript |
| `OpenAggregate(sid,CC_sid)` | aggregate ciphertext and authorized partial decryption | only the common weighted aggregate is released; this is not FGSR `ReshareAggregate` |
| `Retire(sid,PC_sid)` | `Retire(c,T*)`, atomic puncture/erase, acknowledgements | `A_sid in H_b(Gamma_dec)` and `PF_sid` is monotone |
| `Publish(Q,m)` | AOR `Publish`, including `KEYREVEAL` send event | pre-frontier public capability enters `X_hist`; post-frontier old reveal is rejected |
| `Process(Q,m,T_local)` | AOR `Process_i` and FGSR frontier checks | stale generation/frontier cannot alter local state |
| `Recover(rid,target,T_req,...)` | `Authorize -> ParallelReshare -> ReshareAggregate -> Install` | opaque delivery, Common-H, state completeness, no retired-coordinate edge |
| `Corrupt(i,t)` | AOR `Expose_i` plus the mobile corruption oracle | pre-erase state is charged; post-erase state contains no old recovery-complete capability |

The operation `ReshareAggregate` is used here to rename the fourth row of the FGSR
wrapper. This is only a notation change, but it prevents an incorrect proof step in
which algebraic resharing correctness is treated as aggregate-only privacy.

**Theorem 42 (conditional FGSR realization).** Suppose the data plane satisfies
`Joint-AO^mob`, the ACS context satisfies unique `CC_sid` binding, and every FGSR
repair context satisfies `Common-H`, AOR-1--AOR-5, typed capability isolation, and
state-complete erasure. Suppose further that the retirement certificate satisfies
`A_sid in H_b(Gamma_dec)` and that all challenge-dependent recovery branches are
generated inside the same `Joint-AO^mob` experiment. Then the composed protocol
realizes the `F_PF^mob` interface up to

```text
Adv_realize(F_PF^mob)
  <= Adv_Joint-AO^mob
     + sum_r Adv_AOR^mob(r)
     + Adv_Common-H/Correctness
     + Adv_Recovery-Localization
     + Adv_Frontier-Use
     + Adv_Context/Binding
     + Adv_Uncovered-Edge
     + negl(lambda).
```

**Proof sketch.** Bind and submit events are fixed before the challenge and are
identical in both worlds. The aggregate opening is replaced by the single
`Joint-AO^mob` challenge, which preserves the common weighted sum. AOR simulation then
replaces repair, publication, recovery, and corruption views generation by generation.
The typed ledger and `Recovery-Closure` ensure that the simulator introduces no
individual-opening edge. `AOR-5` and the retirement certificate make the retired phase
absorbing, while `Publish` accounts for all pre-retirement public capabilities in
`X_hist`. The remaining differences are exactly the listed correctness, localization,
frontier, context-binding, and uncovered-edge terms. QED

The theorem is a wrapper result, not a concrete cryptographic instantiation. In the
current state, `Adv_Joint-AO^mob` and `Adv_AOR^mob` remain explicit. This is the precise
boundary between the characterization/separation results and a future adaptive
opaque-transport construction.

### 19.76 Result hierarchy for the manuscript

The paper should present the results in the following order. This ordering separates
claims that hold for the abstract access structure from claims that depend on a
cryptographic transport.

1. **Unconditional access-structure result.** Under the capability-edge realizability
   assumptions, `Robust-Hitting` characterizes the retirement sets that can remain
   private after bounded pre-frontier exposure and future current-state exposure.
2. **Unconditional asynchronous lower bound.** Without a causal frontier and an
   absorbing retirement state, a pre-retirement recovery message can be delayed and
   installed after retirement. Without state-complete erasure, future corruption can
   recover the same capability from retained endpoint or repair state.
3. **Unconditional static-data-plane separation.** `Static-AO` plus correctness and
   an instantaneous corruption bound does not imply `Joint-AO^mob` or finality; the
   three-wave `f,f,1` attack supplies the matching counterexample.
4. **Conditional protocol theorem.** `F_PF^mob` is realized by FGSR when
   `Joint-AO^mob`, AOR-1--AOR-5, `Common-H`, state completeness, and typed capability
   isolation hold. The full advantage bound is Theorem 42.
5. **Concrete cryptographic status.** TACITA, Choudhuri, Janus, hbACSS, and ordinary
   Pedersen hiding provide local components only. The paper must retain
   `Adv_Joint-AO^mob` and `Adv_AOR^mob` until an adaptive opaque transport theorem is
   actually proved.

This hierarchy preserves a publishable core even if the final concrete lifting is not
closed. It also prevents the conditional FGSR wrapper from being presented as an
already implemented asynchronous federated-learning system.

### 19.77 Non-circular admissibility and exposure accounting

The privacy game must not encode its conclusion in the query interface. Define an
external schedule budget for each coordinate `ell` and generation `r`:

```text
|B_{ell,r}| <= f,
|U_ell| <= f,
|U_ell union B_{ell,ret}| < q_rec,
```

where `B_{ell,r}` is the set of parties whose readable current or pending state is
exposed before the next accepted installation/retirement barrier, `U_ell` is the
post-frontier residual exposure set, and `B_{ell,ret}` is the final pre-retirement
interval exposure. The scheduler may choose each set from the complete preceding view;
it may delay, reorder, and replay messages subject only to the asynchronous network and
the protocol's label checks. The schedule is not required to satisfy `CapSafe`.

Every output of `Corrupt`, `Recover`, `Publish`, or `Process` is classified after it is
generated:

```text
pre-frontier readable scalar/state -> X_hist^r(B_{ell,r})
post-frontier retained state       -> X_current(U_ell)
challenge-dependent output         -> DataView_b
unclassified capability edge       -> Adv_Uncovered-Edge
```

If a legal query returns an old share, endpoint key, evaluation opening, or recovery
object not covered by these classes, the execution is still part of the real game and
the corresponding `Adv_Uncovered-Edge` is nonzero. The proof may then fail, but the game
does not become vacuous by rejecting the query. Conversely, if AOR and the typed ledger
prove that every legal output falls into the first three classes and the terminal
closure contains no authorized individual-opening set, `Adv_Uncovered-Edge` is zero by
the reduction.

**Lemma 43 (non-circular exposure accounting).** Suppose the scheduler satisfies only
the external budget above and all protocol-valid queries are answered. If AOR-1--AOR-5,
typed capability isolation, and `Joint-AO^mob` hold, then any successful privacy
distinguishing execution must either (i) use a capability already in `X_hist`, (ii)
break the aggregate data-plane game, or (iii) create an uncovered edge. In particular,
`CapSafe` is derived from the reduction and is not an assumption hidden in query
admissibility.

**Proof sketch.** Process the complete real transcript in causal order. The external
budget bounds which state exposures may occur but does not classify their contents.
AOR-1--AOR-4 classify pre/post-barrier endpoint outputs, and AOR-5 removes stale
protocol transitions. Typed isolation sends every challenge-dependent branch to the
joint data-plane view. The only remaining output is an edge absent from the ledger,
which is exactly `Adv_Uncovered-Edge`. If no such edge exists, `Recovery-Closure` and
the robust-hitting condition exclude an authorized individual-opening set. QED

### 19.78 Closure-aware retirement theorem

The retirement certificate must be evaluated against the recovery closure, not only
against the direct capability set. Fix a coordinate `c`, a retirement certificate
covering `A`, a pre-frontier exposed capability set `B`, and let `R_c` be the set of
members of `A` whose old capabilities can still be derived or reinstalled by a legal
post-retirement recovery edge from the residual state and retained public history. The
effective old capability set is

```text
E_c(B,A) = B union R_c union (P - A).
```

The `P-A` term covers current states not included in the retirement certificate. The
`R_c` term covers resurrection and may contain capabilities that were not readable at
the retirement barrier.

**Theorem 44 (closure-aware retirement criterion).** Assume that the capability ledger
is complete for coordinate `c`, and that every individual opening requires an authorized
set `D in Gamma_dec^cap(c)`. Under the exposure budget `|B|<=b`, `c` has privacy
finality exactly when

```text
for every D in Gamma_dec^cap(c),
    D is not a subset of E_c(B,A).
```

For worst-case placement of `B`, this is equivalent to

```text
|D intersection (A - R_c)| > b
for every D in Gamma_dec^cap(c).
```

Consequently, the ordinary `Robust-Hitting` condition is sufficient only when
`R_c=emptyset`. A retirement certificate may satisfy ordinary robust hitting while
failing privacy finality if a legal post-retirement recovery edge makes `R_c` nonempty.

**Proof.** By completeness of the ledger, the old capabilities available after
retirement are exactly those already exposed in `B`, those held by nodes outside `A`,
and those created or reinstalled through `R_c`. Thus an authorized individual opening
is possible exactly when some `D` is contained in `E_c(B,A)`. For the worst-case budget,
the adversary can cover at most `b` members of `D intersection (A-R_c)` using `B`; the
remaining members are protected only if their count exceeds `b`. If the count is at most
`b`, expose those members, use the legal recovery edges for `R_c`, and expose the
uncertified current states. If it exceeds `b`, every authorized `D` retains an
uncovered member after all permitted exposure and recovery edges, so the ledger has no
complete individual-opening set. QED

**Corollary 44.1 (certificate-only retirement is insufficient).** A monotone tombstone,
atomic deletion of direct shares, and a certificate satisfying `Robust-Hitting` do not
imply privacy finality when the residual state contains a reusable coordinate-local
recovery relation or a global recovery authority that reconstructs it. Such a wrapper
can satisfy correctness and its underlying static sharing or aggregate-opening game
while failing `F_PF^mob`.

**Corollary 44.2 (AOR-5 as the asynchronous realization).** If `AOR-5` rejects every
post-frontier `Recover`, `Install`, `Use`, `PartDec`, and `KEYREVEAL` edge for `c`, and
state-complete erasure removes every retired-coordinate recovery input, then
`R_c=emptyset`. The criterion reduces to `Robust-Hitting`, and the remaining privacy
obligations are the data-plane and exposure terms in Theorem 42. Conversely, if a
delayed authenticated message or a retained recovery object creates a member of `R_c`,
the ordinary certificate is not sufficient; the failure is charged to
`Adv_Frontier-Use`, `Adv_Recovery-Localization`, or `Adv_Uncovered-Edge` according to
the edge that produced it.

This theorem is the formal boundary between access-structure reasoning and protocol
state reasoning. It also gives the black-box VSSR/DPSS audit a single target: either
their wrapper proves `R_c=emptyset` for retired coordinates, or it cannot be used as a
drop-in realization of FGSR privacy finality.

### 19.79 Retirement-closure edge matrix

The condition `R_c=emptyset` is discharged edge by edge. The following matrix fixes the
minimal interface responsible for each possible post-retirement route to an old
capability:

| residual object or event | possible edge to `R_c` | closing interface | failure term |
|---|---|---|---|
| retired direct share or recovery polynomial share | future corruption reads old scalar | state-complete erasure and `PECC` | `Adv_Recovery-Localization` / `Adv_PECC` |
| pending repair payload or channel buffer | future endpoint exposure decrypts old point | `AVSS-opaque` and post-erasure channel confidentiality | `Adv_ACSS-opaque` / `Adv_PECC` |
| delayed `Recover` or `Install` message | stale message recreates old current state | AOR-5, generation binding, frontier-bound install | `Adv_Frontier-Use` / `Adv_Generation-Binding` |
| persistent global recovery authority | exposed authority regenerates retired local state | coordinate puncture or recovery-state localization | `Adv_Recovery-Localization` |
| public proof or receipt metadata | hidden witness selects a scalar-bearing branch | typed capability isolation and proof noninterference | `Adv_Uncovered-Edge` |
| aggregate ciphertext or partial decryption | data-plane object opens an individual client value | one `Joint-AO^mob` challenge | `Adv_Joint-AO^mob` |
| pre-frontier public reveal | capability was already sent before retirement | `X_hist` accounting at `Publish` time | no new failure; counted leakage |

**Lemma 45 (edge-complete closure).** Suppose every row above is discharged by its
listed interface, and every cross-coordinate conversion is rejected or covered by the
same `Joint-AO^mob` challenge. Then no post-retirement legal execution creates a new
member of `R_c`, and `Adv_Uncovered-Edge=0` for the first-instance capability universe.

**Proof sketch.** Process a legal execution in causal order. The first four rows cover
all state and recovery inputs that can directly recreate an old capability. The fifth
row covers control-flow conversions from public metadata. The sixth row removes
challenge-dependent data objects from the state simulator, while the final row records
already exposed material rather than treating it as newly recovered. Any remaining
edge would be a capability conversion not present in the typed ledger, which is exactly
the event charged to `Adv_Uncovered-Edge`. Hence the ledger is closed and `R_c` is empty.
QED

Lemma 45 is the concrete proof checklist for Theorem 44. It does not claim that
ordinary AVSS, NIZK, forward-secure encryption, or a tombstone discharges a row without
the corresponding state and transcript argument.

### 19.80 Candidate closure status

Applying Lemma 45 to the current candidates gives the following conservative status:

| interface row | strongest local evidence | current conclusion |
|---|---|---|
| `AVSS-opaque` | APSS/hbACSS-style private delivery and asynchronous availability | conditional only; public recovery and evaluation objects still require scalar-capability isolation |
| `PECC` | Janus-style erasure and ephemeral encrypted transport | local transport evidence only; endpoint buffers and pending repair state remain unclosed |
| `EqProof^mob` | Janus equivocation and Choudhuri SE-NIZK simulation/extraction | no direct proof for post-publication corruption, labelled repair state, and post-erase consistency |
| frontier-bound `Use/PartDec` | abstract FGSR guards | valid at the wrapper level; a concrete implementation must bind the frontier to every accepted capability |
| coordinate-local recovery authority | FGSR state shape and puncture requirement | no existing candidate closes this black-box; retained global authority keeps `Adv_Recovery-Localization` explicit |
| `Joint-AO^mob` | TACITA static aggregate opening | static separation established, adaptive post-challenge data-plane lifting remains open |

Accordingly, the first concrete candidate is a conditional `C_CSR^opaque` transport
with explicit `PECC`, `EqProof^mob`, coordinate-local retirement, and frontier-bound
data-plane use. APSS, hbACSS, Janus, and TACITA supply reduction targets or local
components, not a completed instantiation. Theorem 42 must retain every row whose
status is conditional.

### 19.81 Concrete state mapping for the first `C_CSR^opaque` candidate

The first candidate uses one independent coordinate `c=(sid,ell)` and the following
state partition. This is a protocol-state specification for the proof, not a claim that
an existing ACSS implementation already realizes it.

```text
PersistentLive_i(c) = (T_i(c), z_i(c), C_i(c), instance_i(c))
PublicRepair(Q)    = (Q, H, {D_h}, {pi_eq,h}, {ct_h,j,pi_ved,h,j}_{h,j},
                      AVAIL, AvailCert)
Endpoint_i(Q)      = (mode_i, ek_i, sk_i, plaintext_i, opening_i,
                      receive_buffer_i, verified_i)
HelperTemp_i(Q)    = (helper_coefficients_i, payloads_i, encryption_randomness_i,
                      send_buffers_i, unreleased_recovery_i)
Network(Q)         = (ciphertexts, delivery_metadata, public_receipts)
Retired_i(c)       = (T_i(c), C_i(c), tombstone_i(c))
```

`PersistentLive` contains only the current share and its commitment. `PublicRepair`
contains commitments, labels, proofs, and availability metadata, but no evaluation
point, decryption key, recovery polynomial, or scalar-reconstructible combination.
`Endpoint` and `HelperTemp` contain every secret-bearing object that can exist between
authorization and either `Install` or cancellation. `Network` may survive retirement and
may deliver archived ciphertexts later. `Retired` contains no endpoint registration, key,
plaintext, helper coefficient, private buffer, or other input accepted by a recovery
relation for `c`.

The state transitions are:

```text
Authorize(Q)       -> accept only if Q.T_req dominates T_i(c) and c is live
RegisterEndpoint(Q)-> create a fresh endpoint only while Q is ordered and c is live
DeliverVerify(Q)   -> update Endpoint_i(Q) after label, R_ved, decryption, and opening checks
Install(Q)         -> set z_i(c)=sum_h lambda_h(H,0)*f_h(i), update C_i(c),
                      erase old PersistentLive share, Endpoint, and HelperTemp state
CancelOrRetire(Q)  -> erase Endpoint and HelperTemp state; if retired, keep only
                      Network(Q) and Retired_i(c)
Process/Recover    -> reject if Q is stale, retired, or not in the agreed instance order
Use/PartDec        -> require the authenticated current frontier and live coordinate
```

The transition checks occur at authorization, delivery, installation, and use; a check
only at `Authorize` is insufficient because retirement may be concurrent with delivery.
For a retired coordinate, `CancelOrRetire` is absorbing: no later message can recreate
`PersistentLive` or `Pending` state, and no data-plane operation accepts a capability
labelled by the retired frontier.

Under this mapping, Lemma 45 discharges as follows:

| closure edge | state mapping | required proof |
|---|---|---|
| old direct/recovery share | removed from `PersistentLive` at the barrier | state-complete erasure and `PECC` |
| pending repair payload | confined to `Endpoint`, then erased on install/cancel/retirement | PVOD opaque delivery plus endpoint/buffer `PECC` |
| stale recovery or installation | rejected by `T_req`, instance order, and frontier checks | AOR-5 and generation binding |
| persistent recovery authority | absent from `Retired`; no cross-coordinate recovery input | coordinate-local authority or puncture proof |
| proof-controlled scalar branch | `PublicRepair` contains ciphertexts and zero-knowledge metadata but no scalar | `EqProof^mob`, `CSO-VE`, and typed noninterference |
| aggregate-opening branch | never consumed by state transitions | one `Joint-AO^mob` challenge |

If all rows are proved, this state mapping yields `R_c=emptyset` and
`Adv_Uncovered-Edge=0` for the first independent-coordinate capability universe. It
does not by itself prove any row: in particular, the `Pending` abstraction requires a
real channel/ACSS theorem, and the absence of a persistent recovery authority must be
verified against the implementation rather than inferred from the interface name.

### 19.82 One-step `C_CSR^opaque` simulation

For one live repair context `Q`, fix the common helper set `H`, the preceding exposed
set `B_r`, and the local frontier. The real one-step experiment contains the public
descriptors, PVOD vectors, `AVAIL` metadata, installation, and either completion,
cancellation, or retirement. The simulator receives only

```text
(Q, H, public commitments, B_r-state, X_hist^r(B_r), X_current(U), frontier)
```

and follows the causal hybrid:

```text
S0  real labelled C_CSR execution;
S1  replace R_eq^share proofs by EqProof^mob simulation;
S2  replace unexposed Retrieve_h(j) payloads and endpoint state by the PVOD/CSO-VE
    simulator, while returning the real value only for a corruption allowed by B_r;
S3  replace post-barrier Pending state by the PECC simulator and retain only the
    installed next-generation state or the retirement tombstone;
S4  preserve AVAIL/AvailCert metadata and the Common-H decision, using affine coupling
    for the installed current share;
S5  reject stale or retired Process/Recover/Install/Use/PartDec events and charge any
    undeclared scalar-bearing branch to Adv_Uncovered-Edge.
```

The simulator never needs an unexposed `y_{h,j}`, `rho^D_{h,j}`, `rho^M_{h,j}`, `rho_h^r`, endpoint key,
or helper polynomial coefficient. A pre-barrier corruption that legitimately reveals
one of these objects is copied into `X_hist^r(B_r)`; a post-barrier query receives only
the state permitted by `PECC` and the state mapping of 19.81.

**Proposition 46 (conditional one-step C_CSR simulation).** Suppose `D1`--`D6`,
`EqProof^mob`, `AVSS-opaque`, `PECC`, common instance order, generation binding,
frontier-bound use, and affine coupling hold for `Q`. Then

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

**Proof sketch.** `S0 -> S1` uses the labelled equality-proof game and leaves all
public statements unchanged. `S1 -> S2` uses the opaque delivery game; the simulator
answers only the receiver state that the exposure budget permits, while `D5` prevents
the public transcript from distinguishing the replacement. `S2 -> S3` invokes PECC at
the atomic erase barrier. `S3 -> S4` uses the Common-H decision and affine coupling to
produce the same installed sharing relation and aggregate-independent public metadata.
`S4 -> S5` applies the common instance order plus frontier and generation checks to every late event. Any branch that
reads a challenge-dependent data object is outside this state hybrid and must be
generated by `Joint-AO^mob`; any remaining scalar branch is exactly an uncovered edge.
The union bound gives the expression. QED

Proposition 46 is the first concrete reduction target for the candidate. It does not
claim that APSS, hbACSS, Janus, or ordinary Pedersen proofs already satisfy its premises.
Until one candidate proves the proposition for all concurrent contexts, the main result
remains the conditional Theorem 42/39 hierarchy.

### 19.83 Pending cancellation and retirement ordering

The one-step simulator also needs a precise rule for a repair that overlaps retirement.
For each coordinate `c`, let `prec_c` be the common instance order produced by the
validated agreement layer. An instance `rid` carries its position in `prec_c`; local
delivery order is irrelevant. The abstract transition rule is:

```text
Install(rid) is effective only if rid precedes Retire(c,T*) in prec_c;
CancelOrRetire(c,T*) erases every pending rid not already effective;
after Retire(c,T*), no pending rid may transition to PersistentLive(c).
```

If an install is effective before retirement, its output is a newly labelled current
generation and is itself included in the subsequent retirement transition. If retirement
precedes the install in `prec_c`, the output is discarded and its receiver key,
plaintext, and verification buffer are erased. A message that is locally received in a
different order follows the common `prec_c`, rather than creating a second local order.

**Lemma 47 (pending-closure under ordered cancellation).** Assume common instance order,
atomic `CancelOrRetire`, the state mapping of 19.81, and the frontier/generation checks
of 19.82. Then a pending repair instance contributes no new old capability after the
retirement barrier, except with

```text
Adv_Pending-Order
  + Adv_Frontier-Use
  + Adv_Generation-Binding
  + Adv_PECC
  + Adv_Uncovered-Edge.
```

**Proof sketch.** Consider the first pending event after the retirement barrier. If its
instance precedes retirement, it can only complete as the authenticated next-generation
state and is immediately subject to the retirement transition; it cannot restore the
pre-repair state. If retirement precedes the instance, the instance is erased and the
install edge is rejected. If local delivery order disagrees with `prec_c`, agreement
selects the same case at every correct receiver; a disagreement is `Adv_Pending-Order`.
PECC removes receiver-side plaintext, keys, and buffers, while the frontier and label
checks reject stale transitions. Any remaining scalar-bearing output is an uncovered
edge. Induction over pending events gives the claim. QED

Lemma 47 is the cancellation/retirement component missing from a proof that checks the
frontier only at `Authorize`. It is a state-machine condition; the cryptographic
implementation must still prove the ordering certificate, atomic erase, and PECC.

### 19.84 Sequence agreement for `OrderCert_c`

The set-valued `ACS^-` used to choose `H` does not by itself order a repair relative to
retirement. The first candidate therefore needs a separate coordinate-local sequence
interface, denoted `SeqACS_c`, whose events are repair and retirement descriptors:

```text
e = (c, kind, rid, Q_digest, T_req, parent_c)
SeqACS_c.propose(e) -> append-only prefix or reject
```

An accepted prefix position `k` is certified by

```text
OrderCert_c = (c, parent_c, k, e_digest, quorum_signature)
```

where the quorum size satisfies the usual honest-intersection condition; for the
target-excluded participant set of size `3f+1`, the first candidate uses `2f+1`.
Correct parties sign at most one event for a given `(c,parent_c,k)` and only extend a
prefix they have accepted.

`SeqACS_c` must provide four properties distinct from helper-set ACS:

| property | required meaning |
|---|---|
| sequence agreement | correct parties output the same event at each accepted rank |
| prefix consistency | accepted prefixes are comparable by extension; no forked parent is accepted |
| validity | an accepted event was proposed with a valid `Q_digest`, frontier, and kind |
| termination | every non-Byzantine event that satisfies the liveness rule is eventually ordered or explicitly rejected |

**Lemma 48 (OrderCert soundness).** Suppose `SeqACS_c` has the four properties above,
quorum signatures are unforgeable, and correct parties follow the one-signature-per-rank
rule. Then all accepted `OrderCert_c` values for a coordinate form one append-only
sequence, and a valid certificate cannot place a repair after a retirement event that
precedes it in the sequence, except with

```text
Adv_Order-Agreement
  + Adv_Order-Prefix
  + Adv_Order-Validity
  + Adv_Order-Termination
  + Adv_Order-Certificate-Soundness.
```

**Proof.** Two valid certificates for the same rank either contain the same event by
sequence agreement, or their signer quorums intersect in an honest party. That party
cannot have signed two different events for the same parent and rank, so the second
case is a certificate-soundness or honest-signing violation. Prefix consistency then
inductively prevents a later event from attaching to a forked parent. Validity binds
the certificate to the complete request and frontier context; termination supplies an
eventual decision for every accepted live request. Thus `prec_c` is common to all
correct parties, and Lemma 47 applies. QED

The distinction is essential: Theorem 33 proves agreement on `H`, but does not prove
agreement on the relative order of `Install(rid)` and `Retire(c,T*)`. A concrete
implementation must therefore either instantiate `SeqACS_c` or supply an equivalent
ordering proof; ordinary helper-set ACS agreement is insufficient for `D1`/`D6`.

### 19.85 Set-valued ACS cannot supply the required event order

The gap in Lemma 48 is semantic, not a missing deterministic tie-breaker. Let a set-valued
ACS expose only a common set `S` of event descriptors satisfying agreement, validity and
termination. Suppose `S` contains a repair descriptor `e_R` and a retirement descriptor
`e_T`, but the interface exposes neither a parent relation nor the point at which either
event became accepted relative to the retirement frontier.

For clarity, write the two interfaces as follows. A set interface has the observable form

```text
SetACS_c(proposals) -> S subset of E_c
```

and exposes only the common set, public event descriptors, and their validity evidence. Its
agreement, validity, and termination properties do not identify an accepted prefix or the
causal position of one event relative to another. The required sequence interface instead
has the form

```text
SeqACS_c.propose(e, parent_c) -> (prefix_c, OrderCert_c)
```

where `OrderCert_c` binds the event to `parent_c`, its rank, its complete request digest, and
the frontier context. It must support both of the following semantic properties:

```text
Install-before-retire: a valid repair effective before retirement is not discarded as stale;
No-install-after-retire: a repair accepted after retirement cannot become live state.
```

These are not implied by set agreement. They are the exact interface obligations used by D1
and D6.

Consider two admissible asynchronous executions with the same decided set `S`. In the first,
`e_R` is accepted before `e_T`; in the second, `e_T` becomes effective before the delayed
acceptance of `e_R`. The ACS transcript visible to a wrapper is identical up to the unordered
set `S`, while the first execution requires the repair to remain effective and the second
requires the pending repair to be cancelled. A wrapper that sorts `S` by an event digest
produces the same result in both executions and therefore violates one of these requirements.

**Proposition 49 (set-to-sequence insufficiency).** Under the D1/D6 semantics above, a
set-valued ACS without causal acceptance, parent, and frontier-binding information cannot be
used as a sound `SeqACS_c` implementation by deterministic post-processing alone. Any valid
construction must expose an ordering certificate with equivalent information, or weaken the
retirement semantics so that pending events are never distinguished by their effective order.

**Proof.** The two executions have the same ACS output and hence induce the same output for
any wrapper whose input is only `S` and public event descriptors. In the first execution,
`Install-before-retire` requires `e_R` to be effective; in the second,
`No-install-after-retire` requires its pending instance to be erased. The wrapper cannot make
different decisions on identical inputs. Digest sorting only chooses a fixed presentation
order and does not certify which event was accepted before the frontier. Thus it fails either
repair validity or retirement completeness. A parent-bound prefix certificate supplies the
missing observable distinction. QED

This proposition is the boundary for the literature mapping: Juno AVC, APSS/hbACSS ACS
layers, and DyCAPS MVBA handoff outputs remain useful transport or availability components,
but none of them instantiates `OrderCert_c` for the first paper. The next proof obligation is
therefore to define the smallest asynchronous prefix certificate and reduce the one-step
`C_CSR^opaque` simulator to it; adding another set-valued ACS would not close the gap.

### 19.86 Ordered one-step reduction

The `Adv_Pending-Order` term in Proposition 46 can now be decomposed. Assume that every
repair and retirement descriptor in the one-step context carries a valid `OrderCert_c`, and
that `SeqACS_c` satisfies sequence agreement, prefix consistency, validity, termination, and
certificate soundness. Also assume that `CancelOrRetire` and generation erasure share one
atomic barrier. Then the conditional bound becomes

```text
Adv_OneStep-C_CSR^r
  <= Adv_EqProof^mob(r)
     + Adv_ACSS-opaque^r
     + Adv_PECC^r
     + Adv_Common-H/Correctness^r
     + Adv_Order-Agreement^r
     + Adv_Order-Prefix^r
     + Adv_Order-Validity^r
     + Adv_Order-Termination^r
     + Adv_Order-Certificate-Soundness^r
     + Adv_Atomic-CancelOrRetire^r
     + Adv_Generation-Binding^r
     + Adv_Frontier-Use^r
     + Adv_Uncovered-Edge^r
     + negl(lambda).
```

**Proposition 50 (ordered one-step `C_CSR^opaque` simulation).** Under the premises above,
the simulator of Proposition 46 can answer a concurrent repair/retirement context using only
the allowed exposure state, public commitments, `Common-H`, and the certified coordinate
prefix. Its output is indistinguishable from the real context up to the displayed bound.

**Proof sketch.** First verify the certificate chain and bind every descriptor to its parent,
rank, complete request, generation, and frontier. A disagreement, fork, invalid descriptor,
missing live decision, or forged certificate is charged to the five `SeqACS_c` terms. The
`EqProof^mob`, opaque-delivery, and `PECC` hybrids then replace equality proofs, unexposed
delivery state, and post-barrier buffers as in Proposition 46. At the barrier, the certified
prefix selects exactly one of `Install` and `CancelOrRetire`; a failure to erase every
non-preceding pending instance is `Adv_Atomic-CancelOrRetire`. Generation and frontier checks
reject all later stale transitions. Any remaining scalar-bearing branch is an uncovered edge.
The hybrid union bound yields the expression. QED

Proposition 50 is still conditional: it isolates the precise proof obligations but does not
instantiate `SeqACS_c`, `PECC`, or `Joint-AO^mob`. Its purpose is to prevent the ordering
problem from being hidden inside the cryptographic simulation and to make the next construction
or impossibility result independently falsifiable.

### 19.87 Turritopsis as the closest ordering candidate

The local Turritopsis source is the closest existing construction to the missing ordering
interface. It runs sequential ACS instances `ACS[c,r]`, treats each common ACS output as a
block, and obtains an ordered transaction sequence within a configuration
(`/home/yzc/flagg/consensus/Gao 等 - 2025 - Turritopsis Practical Dynamic Asynchronous BFT.pdf_by_PaddleOCR.md:305-311`,
`:546-598`). This is stronger than one-shot set-valued ACS and gives a useful design pattern:
the rank is supplied by the sequential instance, while the block hash can serve as a parent
context.

It is not a direct `SeqACS_c` instantiation for this paper. Turritopsis authenticates a
checkpoint after a prescribed group of ACS blocks, rather than exposing a coordinate-local
`OrderCert_c` for every repair/retirement event. Its ACS is also defined in a hybrid model
with Byzantine and departing nodes (`:227-243`), and its long-term mobile corruption model is
tied to configuration changes and ADKR (`:650-664`). Those assumptions do not prove security
for a fixed committee under the present causal-generation-bounded mobile adversary. In
particular, threshold-key refresh between configurations does not establish the required
post-frontier signer-state opacity for a committee that remains fixed.

The correct status is therefore:

```text
Turritopsis sequential ACS + checkpoints -> SeqACS^slot candidate evidence
Turritopsis as written                         -> not a C_CSR^opaque instantiation
```

The candidate is valuable because it identifies a concrete route that adds ordering evidence
without introducing a global epoch. It must still be specialized and reproved for the fixed
committee, coordinate-local frontier, and mobile exposure game.

### 19.88 Minimal `SeqACS^slot` construction target

The next construction target is a coordinate-local sequence of ACS slots. Let `P_0` be a
coordinate genesis prefix. For each rank `k`, all correct parties invoke an ACS instance with
the parent digest of `P_{k-1}` in every proposal, obtain a common set `S_k`, and apply one
public canonicalization rule to produce an event batch `E_k`:

```text
P_k = P_{k-1} || E_k
OrderCert_c(k) = (c, k, parent_digest, event_digest, frontier_context, quorum_signature)
```

This is not ordinary ACS post-processing: the parent is an input to the next slot, slots do
not advance after a missing parent, and the certificate is issued only for the common slot
decision. The candidate must prove:

1. slot agreement and prefix consistency;
2. event validity, duplicate suppression, and generation binding;
3. termination without a skipped slot under the asynchronous liveness condition;
4. certificate soundness against the mobile signer exposure game; and
5. a deterministic rule for a slot containing both repair and retirement events.

The fifth item is essential. The protocol must define whether a same-slot repair precedes
retirement in `P_k`, or whether retirement dominates it and cancels it. That choice becomes
the formal `Install-before-retire`/`No-install-after-retire` semantics; network arrival order
cannot decide it. A successful `SeqACS^slot` proof would instantiate the ordering part of
Proposition 50, but would still leave `PECC`, opaque delivery, and `Joint-AO^mob` to prove.

### 19.89 Conditional `SeqACS^slot` theorem

The slot construction can be stated as a separate conditional theorem rather than hidden in
the `C_CSR^opaque` proof. Assume a slot ACS with agreement, validity, termination, and a slot
admission rule that eventually includes every live event in a slot or returns an authenticated
rejection. Assume further that every accepted proposal binds the coordinate, rank, parent
context, complete request, generation, and event kind; canonicalization is deterministic and
duplicate-free; and a correct signer issues at most one certificate for a given
`(c,k,parent_context)`.

If the certificate mechanism remains sound when the adversary accumulates mobile signer state,
then the resulting `SeqACS^slot` satisfies sequence agreement, prefix consistency, validity,
and termination except with probability bounded by

```text
Adv_SeqACS^slot
  <= Adv_SlotACS-Agreement
     + Adv_SlotACS-Validity
     + Adv_SlotACS-Termination
     + Adv_Slot-Admission
     + Adv_Canonicalization
     + Adv_Parent-Binding
     + Adv_Certificate-Soundness
     + Adv_Mobile-Signer-Exposure
     + negl(lambda).
```

The theorem is intentionally conditional. `Adv_Slot-Admission` is not supplied by ordinary
ACS validity: it is the obligation that a retirement event cannot be indefinitely omitted or
silently replaced by an unrelated event. `Adv_Mobile-Signer-Exposure` is also separate from
ordinary threshold-signature unforgeability, because a long-lived fixed committee may expose
signing state across generations. Once this theorem is instantiated, its first four sequence
properties replace the single `Adv_Pending-Order` term in Proposition 46; the remaining
cryptographic rows of Proposition 50 are unchanged.

### 19.90 Forward-secure certificates cover only the ordering layer

The local forward-secure threshold literature gives a possible implementation direction for
`Adv_Mobile-Signer-Exposure`, but only for the certificate layer. Libert--Yung define an
explicit logical period, a local `Update`, and adaptive corruption queries that reveal the
current share; their challenge condition limits the number of shares exposed for the target
period to below the decryption threshold (`/tmp/libert-yung-forward-threshold.txt:576-607`).
They also identify adaptively secure threshold signatures as a related construction
(`/tmp/libert-yung-forward-threshold.txt:925-934`).

For the present candidate, the coordinate-local slot rank could act as the logical period of a
forward-secure threshold signing layer:

```text
FSig_c.Update(k) -> erase signing state for ranks < k
FSig_c.Sign(k, parent_context, event_descriptor) -> sigma_k
OrderCert_c(k) -> threshold-combine sigma_k
```

This mapping is valid only if asynchronous laggards reject old-rank signing requests, correct
parties erase old signing state after the prefix barrier, and the mobile exposure game limits
the shares revealed before the rank transition in the same way as the underlying forward-secure
game. A standard long-lived threshold signature does not meet these conditions.

Even a successful `FSig_c` mapping proves only that an old `OrderCert_c` cannot be forged or
extended after its logical rank is closed. It does not erase repair evaluations, endpoint keys,
recovery authority, or aggregate-opening capability. Consequently:

```text
forward-secure threshold signing -> candidate for Adv_Mobile-Signer-Exposure
forward-secure signing alone     -> not PECC, AOR-5, or Joint-AO^mob
```

This separation prevents the paper from rebranding forward-secure encryption or signatures as
the privacy-finality construction. They authenticate the frontier; they do not close the
recovery closure behind it.

### 19.91 Ordinary ACS does not provide slot admission

The `Adv_Slot-Admission` term cannot be removed by citing ACS agreement, validity, and
termination. Consider a slot in which a correct party proposes a valid retirement event
`e_T`, while the remaining parties propose other valid descriptors. A standard ACS may output
the same valid set at every correct party, terminate in every slot, and include the required
number of correct proposals while omitting `e_T`. In a sequential construction, the adversary
can keep supplying fresh valid non-retirement descriptors or no-op events, so the same omission
can occur in every later slot without violating any ordinary ACS property.

**Proposition 52 (retirement-admission separation).** Standard set-valued ACS properties do
not imply that a particular live retirement event is eventually included, rejected, or otherwise
given a terminal status. Hence ordinary ACS cannot by itself discharge `Adv_Slot-Admission`.

**Proof.** Agreement is preserved because all correct parties decide the same set. Validity is
preserved because the decided set has the required size and contains the required number of
correct proposals. Termination is preserved because every slot decides. Since none of these
properties requires inclusion of a particular correct proposal, an execution can omit `e_T`
while deciding other valid proposals forever. A no-op/renewal proposal pool supplies fresh
alternatives for each slot. QED

The `SeqACS^slot` candidate therefore needs a stronger admission interface. One possible
minimal form is:

```text
Admit_c(e) -> AdmissionCert_c(e)
SlotACS_c(k, parent, AdmissionCerts) -> E_k or RejectCert_c(e, reason)
```

The interface must guarantee that a valid retirement certificate is included at a finite slot,
or receives a transferable rejection certificate that prevents the request from remaining
pending. An endorsement quorum alone is insufficient unless the slot decision rule treats that
quorum as a priority constraint. This is the precise role of `Adv_Slot-Admission`; it is an
ordering/liveness primitive, not a cryptographic validity check.

### 19.92 Static threshold signing fails under cumulative mobile exposure

The signer layer has an independent lower bound. Let `q_sig=2f+1` be the quorum needed for an
`OrderCert_c`, and suppose every committee member holds a long-lived signing share for the same
verification key. The protocol may limit active Byzantine nodes to `f` at every moment, but it
does not erase or evolve the signing shares by coordinate rank.

**Proposition 53 (certificate forgery under static signer state).** If the mobile adversary may
expose at most `t` fresh signer shares in each generation interval, with `t>0`, then after

```text
m = ceil(q_sig / t)
```

intervals it can collect `q_sig` distinct shares and forge a valid certificate for an arbitrary
old coordinate rank, while respecting the instantaneous corruption bound. The certificate
soundness advantage is therefore non-negligible, and becomes overwhelming for an unforgeable
threshold signature once the shares are collected.

**Proof.** Corrupt `t` previously unexposed members in each interval, copy their persistent
signing shares, and release them before the next interval. After `m` intervals the adversary
holds `q_sig` shares for the same verification key. It combines them on any old
`(c,k,parent_context,event_descriptor)` without interacting with current correct nodes. The
result verifies under the unchanged public key, even though no interval contained more than
`t` active corruptions. QED

This attack is independent of the confidentiality of repair payloads. It only forges the
ordering certificate that D1/D6 use to authorize or cancel state transitions. A rank-specific
forward-secure signer can avoid this exact attack only if old shares are erased before later
exposure and the asynchronous mixed-rank state is itself sound. Thus `FSig_c` is a necessary
candidate for the ordering layer, not an automatic reduction from ordinary threshold signing.

### 19.93 Mixed-rank `FSig_c` condition

Forward-secure periods are globally ordered in the standard primitive, whereas a fully
asynchronous committee has no simultaneous rank transition. For a coordinate `c`, let a correct
signer state be `(r_i, sk_i^{r_i}, P_i)` where `P_i` is its accepted prefix. The candidate
signer transition must obey:

```text
Sign_i(k,e)       -> allowed only when k=r_i and e extends P_i
Accept_i(C_k)     -> allowed only when C_k extends P_i and has rank >= r_i
Update_i(k)       -> atomically install C_k, set r_i=k+1, erase sk_i^j for j<=k
LateCert_i(C_j)   -> reject if j<r_i and C_j is not already in P_i
```

The mixed-rank invariant is that every certificate accepted by a correct signer either extends
its current prefix or is a certified catch-up prefix; no local state transition moves to a
forked parent. Define `E_{c,k}` as the set of signer states for rank `k` exposed before the
corresponding local erase, and require the causal-generation bound

```text
|E_{c,k}| <= t < q_sig
```

for every rank that is used by the security game. This bound is about local erase completion,
not wall-clock time; an asynchronous node that never updates cannot be silently counted as
updated.

**Proposition 54 (conditional mixed-rank signer soundness).** Suppose `FSig_c` is forward
secure for rank-indexed shares, correct signers obey the four transitions above, catch-up
prefixes are eventually delivered, and `|E_{c,k}|<q_sig` for every rank. Then a correct node
never accepts two conflicting certificates for one rank, and a late certificate cannot reopen a
closed prefix, except with advantage bounded by

```text
Adv_MixedRank-FSig
  <= Adv_FSig-Soundness
     + Adv_Parent-Binding
     + Adv_Rank-Transition
     + Adv_Rank-CatchUp
     + Adv_Late-Certificate-Rejection
     + Adv_Mobile-Signer-Exposure
     + negl(lambda).
```

**Proof sketch.** A conflicting pair accepted at the same rank either violates parent binding,
causes an honest signer to sign twice, or yields two valid certificates from disjointly
exposed old states. The first two cases are charged to the corresponding transition terms; the
last case requires `q_sig` rank shares and is excluded by the exposure bound or `FSig_c`
soundness. A certificate for an earlier rank is rejected after the local prefix advances unless
it is already a certified ancestor. Catch-up only installs a prefix extending the local one,
so it cannot create a fork. QED

The proposition exposes the remaining model cost: a rank cannot be treated as closed merely
because one node advanced. The proof needs either the per-rank exposure bound as an explicit
adversary condition or a stronger collective erase certificate. This is where the ordering
layer meets the same privacy-finality boundary as the repair state.

### 19.94 State-relative acceptance removes timeless certificate security from the first paper

Propositions 53--54 apply when `OrderCert_c` is treated as a timeless, independently verifiable
authorization: a party with only the public key may accept an old certificate after the signer
shares are exposed. That interface is stronger than the first paper requires. The fixed
committee already maintains a monotone coordinate prefix and frontier, so certificate acceptance
can be state-relative:

```text
AcceptOrder_i(C_k) = 1 only if
  Verify(C_k)=1,
  C_k.parent = Head_i(c),
  C_k.rank = Rank_i(c)+1,
  Frontier_i(c) is live for C_k.event,
  and C_k does not cross an accepted retirement event.
```

Once a node has accepted retirement for `c`, no certificate rooted at an earlier parent is an
authorization at that node, even if its signature is cryptographically valid. Nodes whose old
state was not closed remain in `P-A` in the closure theorem; their capabilities are already
counted in `E_c(B,A)`. Thus future signer-share exposure does not create a new edge unless it
causes a node in `A` to accept a stale transition, which is exactly an AOR-5/frontier-use failure.

**Lemma 55 (acceptance-relative order soundness).** Let `A` be the nodes that completed the
retirement transition, and suppose live-rank certificate forgery is negligible while the
causal-generation exposure bound is active. If every node in `A` uses `AcceptOrder_i` and AOR-5
is absorbing, then exposing enough signing shares after retirement to forge an old
`OrderCert_c` does not enlarge the retirement exposure closure. More precisely,

```text
Adv_Order-Use^post(c)
  <= Adv_Parent-Binding(c)
     + Adv_Frontier-Use(c)
     + Adv_AOR-5(c)
     + Adv_State-Recovery-Rollback(c)
     + negl(lambda).
```

**Proof.** A forged certificate with an old parent fails the head/rank test at every node in
`A`. A certificate attached after retirement fails the frontier test. A node outside `A` is
already represented by `P-A`; no new capability is added to the closure expression. The only
remaining cases require rollback of an accepted prefix, acceptance across the frontier, or
resurrection during state recovery, charged to the displayed terms. QED

Consequently, forward-secure threshold signing is not a premise of the first fixed-committee
privacy-finality theorem. Ordinary authenticated quorum evidence is sufficient during a live
rank under the existing exposure bound; after retirement, monotone state makes old evidence
inert. `FSig_c` remains relevant only for a stronger extension with stateless verifiers, dynamic
members, or timeless public auditability. Proposition 53 remains the separation explaining why
that stronger interface needs additional machinery.

This correction also removes the apparent collective-erasure circularity from the first
construction. The protocol needs collective closure of repair capabilities, not a publicly
certified erasure of every signing share. The ordering evidence is control metadata governed by
the current frontier; it is not itself a persistent recovery capability.

### 19.95 Sticky retirement admission from repeated ACS

Proposition 52 rules out obtaining retirement admission from one ACS invocation alone. It does
not require a new agreement primitive. The sequential wrapper can impose a sticky-input rule:

```text
upon receiving a valid live Retire(c,T*):
  add Retire(c,T*) to PendingRet_i(c)
while Retire(c,T*) is pending:
  include it in every proposal for the next coordinate slot
remove it only after a decided slot contains it or the current prefix proves it terminal
```

Let `UnionValid(S_k,P_{k-1})` collect every valid event appearing in the proposal batches
selected by slot `k`. Assume authenticated eventual diffusion of a valid retirement event,
sequential slot invocation, ACS termination, and the standard ACS property that every decided
set contains at least one correct proposal.

**Theorem 56 (sticky retirement admission).** Every valid live retirement event is eventually
included in a decided coordinate slot or becomes terminal because an equivalent retirement was
already decided. In particular,

```text
Adv_Slot-Admission
  <= Adv_Retire-Diffusion
     + Adv_SlotACS-Termination
     + Adv_Correct-Proposal-Inclusion
     + Adv_Retire-Validity-Stability
     + Adv_UnionValid
     + negl(lambda).
```

**Proof.** Eventual diffusion gives a point after which every correct party keeps the retirement
in its pending set. Sequential ACS termination implies that there is a later slot proposed by
all correct parties. Every correct proposal for that slot contains the retirement. Since the
decided ACS set contains at least one correct proposal, `UnionValid` contains the retirement.
The event remains valid unless an equivalent retirement has already made it terminal. QED

This theorem removes `AdmissionCert_c` from the first construction. Authentication of the
retirement descriptor and the ordinary slot decision evidence are sufficient; no additional
timeless certificate is needed.

**Corollary 56.1 (repair admission or retirement cancellation).** Apply the same sticky-input
rule to every valid live repair descriptor. A repair is eventually included in a decided slot,
or a retirement event becomes terminal first and gives the repair an authenticated cancellation
reason. Thus sequence termination does not require every repair to install after its coordinate
has retired.

### 19.96 Same-slot retirement dominance

The canonicalization rule for one coordinate is fixed as follows:

```text
if UnionValid(S_k,P_{k-1}) contains the unique valid Retire(c,T*):
  E_k = [Retire(c,T*)]
  cancel every repair descriptor for c selected in slot k
else:
  E_k = CanonicalRepairs(UnionValid(S_k,P_{k-1}))
```

Repairs in `P_{k-1}` are already effective and remain subject to the retirement transition.
Repairs merely proposed or delivered in slot `k` have not yet become effective, so cancelling
them preserves repair validity while enforcing `No-install-after-retire`.

**Lemma 57 (retirement-dominant canonicalization).** If the slot input has a unique valid
retirement event and `UnionValid` is common to all correct parties, then every correct party
derives the same `E_k`; no same-slot repair enters `PersistentLive`, and every earlier installed
repair is closed by the retirement barrier.

The rule does not use message arrival order and does not assign an arbitrary digest order to
conflicting state transitions. It gives retirement a semantic priority derived from privacy
finality: once aggregate output authorizes retirement, preserving a not-yet-effective repair has
no liveness value that can outweigh closure.

### 19.97 Fixed-committee ordering instantiation

Combine sequential ACS slots, sticky event proposals, `UnionValid`, retirement-dominant
canonicalization, live-rank quorum authentication, and state-relative certificate acceptance.
No forward-secure threshold signature or independent admission certificate is used.

**Theorem 58 (state-relative `SeqACS^slot`).** Suppose:

1. each slot ACS has agreement, external validity, termination, and includes at least one
   correct proposal;
2. valid events are eventually diffused and remain sticky until decided or terminal;
3. slots are invoked sequentially from one common parent context;
4. `UnionValid`, repair canonicalization, and retirement dominance are deterministic;
5. quorum authentication is sound while its rank is live under the causal-generation exposure
   bound; and
6. every correct node applies `AcceptOrder_i`, AOR-5, and rollback-safe state recovery.

Then the fixed-committee wrapper realizes sequence agreement, prefix consistency, event
validity, and termination for repair/retirement events. Its ordering failure is bounded by

```text
Adv_Order-FGSR
  <= Adv_SlotACS-Agreement
     + Adv_SlotACS-Validity
     + Adv_SlotACS-Termination
     + Adv_Correct-Proposal-Inclusion
     + Adv_Event-Diffusion
     + Adv_Event-Validity-Stability
     + Adv_UnionValid
     + Adv_Canonicalization
     + Adv_LiveRank-Authentication
     + Adv_Parent-Binding
     + Adv_Frontier-Use
     + Adv_AOR-5
     + Adv_State-Recovery-Rollback
     + negl(lambda).
```

**Proof sketch.** Induct on the slot rank. ACS agreement gives every correct party the same
selected proposal set; deterministic `UnionValid` and canonicalization give the same `E_k`.
Sequential invocation binds `E_k` to the unique common parent, so accepted prefixes remain
comparable. External validity and local validation exclude malformed or stale events. Sticky
proposal plus Corollary 56.1 gives eventual decision or terminal cancellation. Lemma 57 resolves
same-slot repair/retirement races identically at every party. Live-rank authentication prevents
a forged decision before the state transition; Lemma 55 makes certificates forged after
retirement inert. A violation is charged to one displayed term. QED

Theorem 58 instantiates the ordering premise of Proposition 50 for the first paper. The
remaining one-step proof obligations are now `EqProof^mob`, opaque ACSS delivery, `PECC`,
`Common-H`, generation binding, and the uncovered-edge audit. Timeless public audit and dynamic
membership remain outside this theorem.

### 19.98 Ephemeral-PKE realization of PECC

PECC is a residual-state property, but it does not require a new encryption primitive. Fix an
endpoint `e=(Q,h,i)` that remains uncorrupted until its local barrier `tau_i`. Instantiate the
endpoint with a fresh public-key pair used only for `e`, bind the complete label `L` as associated
context, and retain only the public ciphertext after `tau_i`. Assume either IND-CCA security, or
IND-CPA security together with authenticated unique-ciphertext delivery and a message-independent
processing outcome for the two valid challenge payloads.

**Proposition 59 (ephemeral-PKE PECC).** If endpoint registration is permitted only while `Q` is
ordered and live, `CancelOrRetire` erases the endpoint secret key, plaintext, verification
workspace, and private receive buffers at `tau_i`, and every post-barrier registration,
decryption, recovery, and installation transition for `L` is rejected, then

```text
Adv_PECC^e
  <= Adv_PKE^e
     + Adv_Label-Authentication^e
     + negl(lambda).
```

Here `Adv_PKE` denotes the selected IND-CCA realization, or the IND-CPA realization under the
authenticated unique-ciphertext condition. Erasure and absorption are state-transition premises;
their failure is charged to `Adv_Atomic-CancelOrRetire` in Proposition 50.

**Proof.** Embed the PKE challenge as the ciphertext for `e`. Before `tau_i`, the PECC game does
not issue a corruption of the challenge endpoint. At `tau_i`, the real and simulated executions
retain the same public key, ciphertext shape, label, delivery metadata, and retirement state,
while the secret key and all plaintext-bearing local state are erased. After `tau_i`, delayed
delivery returns the already visible ciphertext and the absorbing state rejects every operation
that could invoke decryption. The post-barrier corruption response is therefore independent of
the challenge bit except through the PKE ciphertext. A ciphertext or label accepted outside this
embedding gives the authentication term. The PKE reduction gives the bound. QED

This proposition separates two adaptive obligations. A receiver corrupted before its barrier is
answered with real state and contributes to `X_hist`; consistency of that state with earlier
commitments belongs to `AVSS-opaque` and AOR-3. A receiver corrupted only after its barrier is the
PECC case and needs no non-committing opening of the erased endpoint key.

### 19.99 Barrier-complete closure of delayed repair state

For a retired coordinate `c`, let `A_c` be the parties whose retirement acknowledgements enter
the privacy-finality certificate and let `U_c=P-A_c`. Each `i in A_c` has a local barrier
`tau_i` at the retirement rank supplied by Theorem 58. Define the secret-bearing state erased at
that barrier as

```text
Secret_i(c) = old current shares
              union endpoint secret keys and plaintext evaluations
              union evaluation openings and verification randomness
              union private receive/send buffers and interpolation accumulators
              union helper polynomial coefficients and per-receiver payloads
              union encryption randomness and unreleased recovery responses.
```

Public ciphertexts, commitments, receipts, availability evidence, and order certificates form
`PublicResidual(c)` and may remain forever. Define

```text
X_base(c) = X_hist(c) union X_current(U_c) union X_adv(c) union PublicMeta(c),
```

where every pre-barrier corruption and every value retained by a Byzantine party is included in
the first three terms. Let `Cap_old^{A_c}(c)` contain old capabilities whose final missing edge
uses endpoint or helper state at a party in `A_c`.

**Theorem 60 (barrier-complete delayed-state closure).** Assume Theorem 58, state-complete local
`CancelOrRetire` for every `i in A_c`, Proposition 59 for every challenge endpoint, a scalar-free
public repair transcript, generation/frontier binding, and complete exposure accounting. Then

```text
(Cl_rec(X_base(c) union PublicResidual(c)) - Cl_rec(X_base(c)))
  intersection Cap_old^{A_c}(c)
  = emptyset,
```

except with advantage

```text
Adv_Order-FGSR
  + Adv_Atomic-CancelOrRetire
  + sum_e (Adv_PKE^e + Adv_Label-Authentication^e)
  + Adv_Generation-Binding
  + Adv_Frontier-Use
  + Adv_Uncovered-Edge
  + negl(lambda).
```

**Proof.** Fix the first derivation of a capability in the displayed set and inspect the state
of its endpoint at `tau_i`. If no key was registered, the absorbing retirement state prevents a
key from being created for the retired label. If a key was registered while its ciphertext was
still in flight, `CancelOrRetire` erases the key and Proposition 59 makes the retained ciphertext
useless for deriving its payload. If delivery occurred but processing or installation remained
pending, the same transition erases the plaintext, opening, buffers, and interpolation state. If
installation precedes retirement in the common prefix, it creates the uniquely labelled current
generation and the retirement transition erases that installed share. If retirement precedes
installation, Theorem 58 and AOR-5 reject the install before it creates live state. Helper
coefficients, payload copies, encryption randomness, and unreleased recovery responses are either
erased at an acknowledged helper barrier or already included in `X_hist`, `X_current(U_c)`, or
`X_adv`.

These cases cover ciphertexts sent before the barrier and delivered afterward, ciphertexts that
arrive concurrently with the barrier, endpoints that never registered a key, and both ordered
outcomes of the install/retire race. The network is allowed to retain every public ciphertext;
only its scalar derivation edge is removed. Any remaining first derivation violates ordering,
atomic state completeness, PKE/label security, generation/frontier binding, or the edge ledger,
yielding the stated bound. QED

**Corollary 60.1 (concrete pending-state term in Proposition 50).** Under Theorem 60, the
`Adv_PECC^r + Adv_Atomic-CancelOrRetire^r` portion of the ordered one-step reduction is discharged
by per-endpoint PKE and label-authentication advantages plus the single state-complete barrier
event. Consequently, delayed network delivery adds no member to `R_c` for the acknowledged set
`A_c`; all residual risk is already represented by `X_hist`, `X_current(U_c)`, and `X_adv`.

### 19.100 Local receipt certificates do not imply target delivery

The earlier complaint-free candidate attached `2f+1` receipts to a helper descriptor, with each
signer attesting only that its own private evaluation was valid. This certificate is insufficient
for target-excluded repair. Let `u` be the repair target and let a Byzantine helper distribute
valid committed evaluations to a set `S subseteq P-{u}` of `2f+1` receipt signers. The helper can
simultaneously encrypt an invalid value for `u`. Every party in `S` has the same local acceptance
behavior as in an all-valid execution, while `u` cannot install the helper contribution.

**Proposition 61 (local-receipt separation).** Suppose validity of the ciphertext addressed to
`u` is visible only after decryption by `u`, the availability certificate excludes `u`, and the
protocol has no recovery or scalar-revealing complaint branch. Then a certificate containing
`2f+1` locally verified receipts does not imply that `u` can obtain a binding-consistent
evaluation, even when the ciphertext vector is available through AVID.

**Proof.** Compare two executions in which the helper sends the same valid payloads to all
members of `S`. In the first execution the ciphertext for `u` encrypts the committed evaluation;
in the second it encrypts an invalid value. Ciphertext privacy makes the certificate-bearing
public views indistinguishable to parties without `u`'s endpoint key, and every signer in `S`
issues the same receipt. AVID availability reconstructs the selected ciphertext in both
executions; it does not establish that its plaintext satisfies the polynomial relation. The
target accepts only in the first execution. Hence the receipt certificate cannot imply target
delivery. QED

This proposition identifies the exact functionality supplied by hbACSS implication and share
recovery: it converts partial local success into complete delivery. Removing that path requires
public validity for every encrypted receiver evaluation, rather than a larger local-receipt
threshold.

### 19.101 Publicly Verifiable Opaque Delivery

Define **Publicly Verifiable Opaque Delivery (PVOD)** for one helper `h` as follows. The helper
commits to `f_h`, registers the complete context `Q`, and forms

```text
V_h(Q) = { (pk_Q,j, M_h,j, ct_h,j, pi_ved,h,j) : j in P },
```

where `pi_ved,h,j` proves `R_ved` from 19.62. `VerifyPVOD(Q,D_h,V_h)` accepts only if every
receiver entry verifies under the same helper, coordinate, generation, frontier, and order
position. The complete vector is dispersed through AVID. A party signs `AVAIL(Q,h)` after
`VerifyPVOD` accepts and its AVID disperse instance completes; it does not decrypt a receiver
payload before issuing this acknowledgement.

The privacy interface needed for this vector is commitment-assisted selective-opening verifiable
encryption, denoted `CSO-VE[R_ved]`. Its real experiment publishes valid commitment/ciphertext/
proof tuples and permits
the adversary to corrupt up to `f` receiver endpoints before their generation barrier. The
simulation experiment receives the public context and the evaluations legitimately exposed by
those corruptions, but no unopened evaluation. It must produce the same public vector and answer
every corruption with a key and plaintext state consistent with the already published pair.
Endpoints reaching the barrier before corruption are handled by PECC rather than reopened.

`CSO-VE[R_ved]` is a composed interface, not the name of an existing primitive. A candidate
instantiation needs a selective-opening or non-committing encryption layer, an equivocatable or
uniform-preimage-sampleable commitment layer for `M_h,j`, and a concurrently simulatable,
simulation-sound proof for `R_ved`. Ordinary IND-CPA and ordinary RIND-SO are insufficient by
themselves: the plaintexts are correlated Shamir evaluations, while the adversary chooses the
endpoints to open after seeing the complete vector. The public commitments are required to bind
the real ciphertexts to those evaluations without requiring the simulator to know every unopened
value.

**Lemma 62 (transport and acknowledgement transparency).** Conditioned on one PVOD vector,
the public AVID trace and all honest `AVAIL` decisions are PPT functions of that vector, public
protocol randomness, the asynchronous schedule, and public verification outcomes. Replacing the
PVOD vector by an indistinguishable simulated vector therefore preserves the joint distribution
of AVID blocks, retrieval metadata, acknowledgements, and `AvailCert_h`. No separate AVID privacy
assumption is required.

**Proof.** AVID disperses and reconstructs the ciphertext/proof vector without interpreting its
plaintext. Each honest acknowledgement checks `VerifyPVOD` and AVID completion, both public
events. Apply closure of computational indistinguishability under PPT post-processing while
using the same schedule and public coins in both worlds. QED

**Theorem 63 (opaque-delivery factorization).** For one generation, suppose:

1. the helper-polynomial commitment view admits the generation-local affine coupling while
   preserving every pre-existing exposed share;
2. `CSO-VE[R_ved]` securely simulates all endpoints corrupted before their barrier;
3. Proposition 59 covers endpoints corrupted only after their barrier;
4. `R_ved` is sound, every label is bound to the complete ordered context, and the public
   transcript has no scalar recovery branch; and
5. AVID satisfies correctness and availability.

Then the PVOD-based delivery layer satisfies the opaque ACSS game of 19.35.1 with

```text
Adv_ACSS-opaque^r
  <= Adv_Affine-Coupling^r
     + Adv_D-Commitment-Hiding^r
     + Adv_CSO-VE^r
     + sum_e Adv_PECC^e
     + Adv_Rved-Soundness^r
     + Adv_Label-Binding^r
     + Adv_Uncovered-Edge^r
     + negl(lambda).
```

**Proof sketch.** First replace the honest helper polynomial and its hiding commitment by the
generation-local coupled polynomial, preserving all state already exposed at the start of the
interval. Next invoke `CSO-VE` on the receiver vector. Every endpoint corrupted before its barrier
opens consistently with the published ciphertext and proof; unopened evaluations remain absent
from the simulator input. Lemma 62 carries this replacement through the complete AVID transcript,
`AVAIL` pattern, and availability certificate without another privacy hybrid. At each local
barrier, Proposition 59 replaces the residual endpoint state while retaining all archived
ciphertexts. `R_ved` soundness and label binding make every accepted ciphertext an encryption of
the unique committed evaluation for its receiver and context. A scalar-bearing public or recovery
branch lies outside PVOD and is charged to `Adv_Uncovered-Edge`. QED

Theorem 33 and Theorem 63 now separate correctness from privacy cleanly. Theorem 33 derives
`Common-H` from public validity plus AVID availability; Theorem 63 derives opaque delivery from
`CSO-VE` plus PECC. Their shared `AvailCert_h` leaks only public storage and validity events.

The local literature supplies each neighboring component but not this composition. hbACSS places
the evaluation proof inside the encrypted payload and relies on implication/recovery for a bad
receiver ciphertext (`/home/yzc/flagg/extract_hbACSS.txt:802-831`). Illusi gives publicly
verifiable encrypted shares and adaptive PVSS security from standard assumptions
(`/tmp/apvss-2026-1100.txt:420-460`, `:461-596`), but its decrypted shares and reconstructed
secret are group elements rather than the scalar shares required by FGSR repair
(`:108-134`, `:705-727`). Janus supplies adaptive ciphertext/state equivocation but permits a
complaint to make a disputed ciphertext publicly decryptable
(`/home/yzc/flagg/adaptive_dkg_2026_892.txt:445-470`). PVOD therefore remains a concrete
construction obligation rather than a renamed invocation of any one source theorem.

### 19.102 Commitment-assisted selective-opening verifiable encryption

The `SO-VE[R_ved]` shorthand is too weak for the PVOD proof. Replace it with the following
explicit interface. For a fixed labelled context `Q` and helper commitment vector `D_h`, the
real experiment publishes

```text
V_h = {(M_h,j,ct_h,j,pi_ved,h,j) : j in P},
```

where each tuple is generated from a witness
`(y_{h,j},rho^D_{h,j},rho^M_{h,j},omega_{h,j})` satisfying `R_ved`. An adaptive adversary may
corrupt receiver endpoints before their local generation barrier, subject to the mobile bound.
Such a corruption returns the endpoint key and the witness for that endpoint. It may later
corrupt a different endpoint, but a retired endpoint returns only its retired state. The public
view includes the complete vector, all simulated or real proofs, the corruption transcript, and
all public `AVAIL` metadata.

The experiment must also declare the origin of the receiver keys. In the main fixed-committee
setting, `pk_Q,j` is an externally registered key that exists before the repair instance and is
visible to the adversary; the repair simulator does not learn its secret key merely because it
creates the PVOD vector. A variant in which the simulator generates every receiver key and keeps
all corresponding secrets is a separate trusted-setup experiment. It may use ordinary encryption
for that local proof, but it does not establish the stable-key, adaptive-corruption claim of the
main setting.

`CSO-VE[R_ved]` requires a simulator that receives `Q`, `D_h`, the public setup, and only the
witnesses legitimately exposed by the corruption schedule. It must produce the public vector
before future endpoint choices are known, and then answer every pre-barrier corruption with a key
and witness consistent with the already published `(M_h,j,ct_h,j,pi_ved,h,j)`. It receives no
unopened evaluation. Its output must remain indistinguishable even when the adversary chooses
the opened endpoints after inspecting the entire correlated vector and its public proofs.

This definition has four independent obligations:

1. **Correlated-message simulation:** the unopened plaintext vector remains a valid evaluation
   vector of the committed polynomial; sampling unrelated messages with the same marginal
   distribution is not sufficient.
2. **Commitment equivocation or preimage sampling:** a simulated `M_h,j` can later be opened to
   the value required by the exposed evaluation without leaking a setup trapdoor.
3. **Proof consistency:** a simulated `pi_ved,h,j` remains compatible with the later key and
   witness opening, while extraction or soundness prevents a real accepted tuple from binding to
   two different evaluations.
4. **Frontier-aware state closure:** after a local barrier, key, plaintext, both openings, and
   decryption workspace are covered by `PECC`; delayed ciphertext delivery is public network
   state and is not treated as a deletion assumption.

The interface deliberately places the correlated-message condition inside the security game.
It is therefore stronger than ordinary IND-CPA and stronger than a selective-opening statement
that only supports independently sampled or identically distributed plaintexts.

### 19.103 RIND-SO is not a black-box instantiation

**Proposition 64 (correlated-vector separation).** A RIND-SO guarantee for a public-key
encryption scheme does not, by itself, imply `CSO-VE[R_ved]` for Shamir evaluation vectors.

**Reason.** RIND-SO can replace unopened ciphertext plaintexts only when the replacement follows
the distribution required by its game. In PVOD, the vector is constrained by a hidden polynomial
constant and by the public evaluation commitments. A simulator that does not know that constant
cannot simply sample a fresh valid polynomial vector and claim equal distribution; doing so would
change the joint relation between the already exposed evaluations and the unopened coordinates.
The APSS analysis identifies exactly this limitation for PVSS: late adaptive key opening is
handled by RIND-SO, but the unknown-secret correlated plaintext vector needs additional
commitments and a separate simulation argument (`/home/yzc/flagg/dynamic_pss_2022_619.txt:2446-2466`).

Consequently, the proof of Theorem 63 may cite a concrete scheme only after it supplies all of
the following in one labelled experiment: arbitrary correlated Shamir plaintexts, adaptive key
opening, public commitment consistency, proof simulation, and post-barrier state closure. A
claim based only on IND-CPA, RIND-SO, or NIZK zero knowledge leaves the central pre-barrier
simulation gap open.

### 19.104 Instantiation boundary for the main theorem

The first concrete instantiation should treat `CSO-VE[R_ved]` as a joint primitive assembled from
four layers rather than as a property of encryption alone:

```text
generation-local affine coupling
  + public hiding commitment M_h,j
  + selective-opening/non-committing encryption of (y,rho^D,rho^M)
  + simulation-sound, concurrently simulatable proof of R_ved
  + PECC for the endpoint state after the frontier
```

The public commitment is not an extra scalar disclosure: it is the object that lets the proof
bind a ciphertext to a receiver evaluation while keeping that evaluation opaque. Its hiding,
equivocation, or uniform-preimage-sampling property must be proved jointly with the encryption
and proof transcript. In particular, revealing a commitment opening at a later corruption is
part of the security experiment, not an informal simulator convenience.

This closes the present proof obligation at the interface level without claiming a concrete
standard-model construction. The remaining go/no-go question is narrow: whether one can realize
the joint `CSO-VE[R_ved]` game with an available dual-mode commitment, adaptive selective-opening
encryption, and simulation-sound proof system while preserving scalar Shamir repair. If that
composition cannot be proved, the paper retains Theorem 63 as a conditional main theorem and
reports the missing primitive as an explicit construction barrier.

### 19.105 Candidate construction and go/no-go test

A concrete candidate for `CSO-VE[R_ved]` is a proof-carrying encrypted opening with the following
algorithms. For every receiver `j`, the helper computes

```text
(y,rho^D) <- EvalOpenSample(D_h,j)
rho^M <-$ Com.Randomness
M <- Com(y;rho^M)
ct <- Enc(pk_Q,j,(y,rho^D,rho^M);omega,L(Q,h,j))
pi <- Prove(R_ved,(Q,D_h,pk_Q,j,M,ct,j),(y,rho^D,rho^M,omega))
```

The receiver runs `Dec`, checks `EvalOpen(D_h,j;y,rho^D)=1` and
`M=Com(y;rho^M)`, and erases the complete opening state at its local barrier. The public
descriptor contains only `(M,ct,pi)`. This construction is syntactically minimal: the public
commitment is needed for binding, the encrypted tuple is needed for private scalar recovery, and
the proof is needed for target-excluded public validity.

The construction is accepted as an instantiation only if its proof supplies one joint adaptive
game with the following properties:

1. `Com` is hiding in the real setup and either equivocable or uniformly preimage-sampleable in
   the simulation setup; later openings of `M` have the real distribution.
2. `Enc` supports late adaptive opening of externally registered endpoint secret keys while the
   public ciphertext vector is already fixed. The guarantee must hold for arbitrary correlated payloads generated
   by one Shamir polynomial, not merely independently sampled messages.
3. The proof system is simulation-sound and concurrently simulatable for `R_ved`; a simulated
   proof remains compatible with the later key and opening returned by the adaptive corruption
   oracle.
4. The state-erasure game covers endpoint keys, plaintexts, `rho^D`, `rho^M`, encryption
   randomness, proof randomness, and all decryption buffers. `PECC` is invoked only after the
   barrier and does not assume that network ciphertexts disappear.

Under these four conditions, the hybrid for Theorem 63 is well typed: affine coupling handles
`D_h`, the joint selective-opening game handles the complete `(M,ct,pi)` vector, and `PECC`
handles post-barrier exposure. The required assumption should be named an
**adaptive correlated-key-opening encryption game**, rather than abbreviated as RIND-SO, until a
published primitive is shown to satisfy it.

The local candidates now have a precise status. APSS Section 7.3 supplies the public commitment
and encrypted-opening syntax, but its own unknown-secret warning prevents a direct security
instantiation (`/home/yzc/flagg/dynamic_pss_2022_619.txt:1442-1460`, `:2446-2466`). Janus
supplies adaptive commitment/encryption state equivocation, but its complaint-to-public-decryption
branch violates `D5`; deleting that branch recreates the target delivery obligation solved by PVOD
(`/home/yzc/flagg/adaptive_dkg_2026_892.txt:432-470`). Illusi supplies public encrypted-share
validity, but its group-valued share interface does not recover the scalar required by Shamir repair
(`/tmp/apvss-2026-1100.txt:420-596`, `:600-727`). Libert--Yung supplies global-period forward
security rather than per-coordinate opaque delivery (`/tmp/libert-yung-forward-threshold.txt:522-610`).
None of these works alone closes `CSO-VE[R_ved]`.

The candidate comparison is therefore:

| Candidate | Supplies | Fails for `CSO-VE[R_ved]` |
|---|---|---|
| Libert--Yung forward-secure threshold encryption | externally visible public key, adaptive corruption game, local key update and past-period confidentiality | uses a globally ordered period, does not prove a ciphertext encrypts a scalar Shamir opening committed by `D_h`, and has no target-excluded public delivery condition |
| Janus-style adaptive DKG transport | Pedersen state hiding, erasure-based adaptive state equivocation, encrypted receiver openings and NIZK consistency | complaint verification makes a disputed ciphertext publicly decryptable; removing that branch requires the PVOD public-validity proof that Janus does not supply |
| APSS Section 7.3 | commitments to subshares, encrypted decommitments and a proof-of-knowledge syntax | its RIND-SO route does not simulate an unknown-secret correlated PVSS vector; it is not a frontier-aware state game |
| Illusi adaptive PVSS | public validity and adaptive PVSS security for group-valued shares | its share interface does not directly recover scalar Shamir openings needed by FGSR repair |

This table is a construction triage, not a claim that the listed schemes are insecure in their
own models. It fixes the exact adaptation required before any of them can be cited as an
end-to-end instantiation.

The immediate go/no-go test is therefore concrete: instantiate the above algorithms with one
candidate adaptive PKE and write the late-key-opening hybrid for a vector whose plaintexts are
evaluations of a hidden degree-`2f` polynomial. If the simulator needs the hidden constant or
must reveal a scalar-bearing complaint, the candidate is rejected for the main theorem. If it
answers all openings from the joint game and leaves `AVAIL` public-only, it becomes the first
 complete construction target for `FGSR-PVOD`.

### 19.106 Receiver-SO literature boundary: HPW15

Hazay, Patra, and Warinschi study the receiver-side selective-opening setting: a sender encrypts a
vector of messages under independently generated receiver public keys, and the adversary obtains the
secret keys for a selected subset after seeing the complete ciphertext vector
(`/tmp/hpw15.txt:298-312`). Their `rind-so` experiment captures the late exposure event relevant to
this paper: the exposed object is a receiver decryption key rather than sender encryption randomness.
Their `rsim-so` notion is stronger and is obtained from receiver non-committing encryption (NCER);
Theorem 4.4 constructs the ideal-world simulator by generating the public/secret key pairs itself,
publishing fake ciphertexts, and using the NCER opening algorithm when selected messages are returned
(`/tmp/hpw15.txt:962-1018`).

This result is a correct receiver-opening starting point, but it does not instantiate
`CSO-VE[R_ved]`:

1. **Key origin.** HPW15 controls the key-generation experiment and its simulator retains the
   matching secret keys. The present theorem requires an external-key model in which `pk_{Q,j}` is
   registered before repair and the repair simulator does not obtain `sk_{Q,j}`. Simulator-generated
   keys describe a different trusted-setup experiment.
2. **Correlated hidden payloads.** HPW15 permits efficiently resamplable joint message distributions,
   but its NCER hybrid does not prove a joint simulation for a vector constrained by a hidden Shamir
   polynomial, its evaluation-opening randomness, and the public descriptor `M_{h,j}`. The required
   relation is receiver-key opening together with a hidden algebraic witness.
3. **Public proof composition.** HPW15 has no `R_ved` statement, AVID availability event, or
   concurrent proof transcript. Adding a commitment and a NIZK requires a new joint simulation
   theorem showing that a later key opening remains consistent with the already published proof,
   without making the scalar or decryption witness public.

Pan--Wagner--Zeng's compact `SIM-SO-CCA` constructions are complementary but concern sender-side
opening of plaintext/encryption-randomness information; they do not replace HPW15's receiver-key
opening game (`/tmp/pan-sim-so-cca.txt:82-114`, `:641-698`). The missing result is a composable
external-key variant with correlated algebraic payloads and `R_ved` simulation. Until that variant
is proved, HPW15 supports only the selective-opening sublemma, not the concrete instantiation of
Theorem 63. The next proof obligation is to formulate this game and test one NCER/dual-mode
candidate: the simulator receives no endpoint secret key, answers late openings consistently with
one hidden degree-`2f` polynomial, and preserves proof validity.

### 19.107 What HPW15 key simulation does and does not provide

The key-simulatable PKE of HPW15 must be separated from the stronger interface required here.
Its `ksim` experiment compares an honestly generated public key with an obliviously generated
public key together with the public-key sampling explanation (`/tmp/hpw15.txt:530-569`). This
closes a public-key distribution hybrid. It does not provide an algorithm that, after a ciphertext
has been published, produces a decryption-capable secret key for an externally registered public
key and a selected plaintext.

The distinction is visible in the receiver-SO constructions. HPW15's NCER opening has the form
`nOpen(sk,e*,t,m)`, and the tweaked variant has the form `tOpen(sk,pk,e*,m)`; both algorithms take
the original secret key as input (`/tmp/hpw15.txt:452-524`, `:1450-1535`). Thus their hybrids can
replace a ciphertext and later derive an alternative exposed key because the simulator generated
and retained the original key. This is exactly the information unavailable in the external-key
model.

The `KeyOrigin` interface needed by this paper is stronger and should be stated explicitly. A
simulator-side setup must provide

```text
SimKeyGen -> (pk,tau)             without sk
SimKeyOpen(tau,ct,m,public-state) -> sk_star
```

with the following properties: `pk` is indistinguishable from an externally registered public key;
`sk_star` is a valid key for `pk` and decrypts the already published simulated ciphertext `ct` to
`m`; and the complete opened state is indistinguishable from the state returned by corruption of a
real endpoint. The interface must also compose with the later `R_ved` witness opening. Public-key
indistinguishability alone is not enough.

HPW15's extended key-simulatable construction deliberately allows oblivious public keys that may
have no matching secret key (`/tmp/hpw15.txt:530-569`, `:1450-1510`). Such keys are useful for
separating security notions, but they cannot be installed as receiver endpoints that must decrypt
real payloads. Consequently, HPW15 supplies evidence for the public-key part of `H1`, while the
external secret-key opening part remains a new primitive requirement.

The corrected audit is therefore:

| HPW15 component | Current role | Missing for `H1` |
|---|---|---|
| `ksim` | public-key distribution hybrid | a decryption-capable late key opening for an external key |
| NCER / tweaked NCER | ciphertext equivocation after key generation | operation without the original secret key |
| extended key-simulatable PKE | public keys outside the valid-key set | endpoint correctness for every installed key |

The next construction task is to define and instantiate `KeyOrigin` before attempting the
correlated-NCER hybrid. A candidate that only changes public-key generation, or that depends on
the original `sk`, remains a partial selective-opening component and cannot be cited as the
external-key instantiation of Theorem 63.

### 19.108 Key-origin subgame and the only valid hybrid order

The external-key requirement creates a separate issue before message privacy. In the real execution,
`pk_{Q,j}` is registered before the PVOD vector is published, while the matching `sk_{Q,j}` is held
by the endpoint and is returned if that endpoint is corrupted before its barrier. An ideal simulator
that receives only the public key and no key-generation witness cannot generally return a secret key
that is distributed as the registered key and decrypts the already published ciphertext. This is an
interface obstruction, not an NCER reduction loss.

Define `KeyOrigin` as the experiment that samples or accepts the registered public-key vector before
the repair instance and then exposes selected secret keys after the public vector is fixed. The
external-key version of `CSO-VE` is meaningful only if one of the following is part of the primitive:

1. an oblivious or dual-mode public-key generation algorithm that produces a public key together
   with a simulator-side explanation and a later valid secret-key opening; or
2. a sanctioned key-opening oracle in the ideal experiment whose output is the real registered key,
   with the oracle's information explicitly excluded from unopened evaluations.

Ordinary unique-secret-key public-key encryption supplies neither interface. Treating the simulator
as the endpoint key owner silently changes the model back to the HPW15-style key-generation setting.
HPW15's key-simulatable PKE direction is therefore a useful candidate for `KeyOrigin`, but its
published receiver-SO theorem still leaves the correlated Shamir payload and `R_ved` composition
to be proved.

The candidate hybrid must consequently be written in this order:

```text
H0  externally registered keys, real correlated Shamir payloads and real R_ved proofs
H1  replace KeyOrigin by an oblivious/dual-mode key explanation
H2  replace each unopened endpoint ciphertext by a non-committing ciphertext
    and answer a pre-barrier opening with a key/witness consistent with that endpoint
H3  equivocate M and simulate R_ved while preserving one hidden polynomial relation
H4  apply PECC only after each endpoint barrier
```

The corresponding proof ledger is

```text
Adv <= Adv_KeyOrigin
    + Adv_Correlated-NCER
    + Adv_Commitment/R_ved
    + sum_j Adv_PECC,j
    + Adv_Rved-Soundness
    + Adv_Uncovered-Edge
```

The HPW15/NCER candidate closes only the local `H2` payload transition in the key-generated model.
It does not close `H1`, and its theorem contains no argument for `H3`. The research target is thus
sharper than “use receiver-SO encryption”: construct or rule out an external-key correlated
receiver-opening primitive whose key-origin explanation, algebraic witness consistency, and public
proof simulation compose under the asynchronous barrier schedule. This is the next theorem-level
task for the paper; no protocol or experiment expansion is required before it is settled.

### 19.109 Formal `KeyOrigin` game

The required key interface can be stated as an external-key non-committing game. For each labelled
endpoint, the real and simulated experiments expose the same public key before the repair payload
is fixed:

```text
RealKeyGen(1^lambda) -> (pk,sk)
SimKeyGen(1^lambda)  -> (pk,tau)
SimEnc(pk, public-context) -> (ct,sigma)
SimKeyOpen(tau,sigma,m,public-state) -> sk_star
```

The public key output of `SimKeyGen` must be indistinguishable from the registered real key. The
simulated ciphertext must be indistinguishable from an encryption under the real key, including
when the adversary sees the complete vector of endpoint ciphertexts and public proofs. After that
vector is fixed, an adaptive pre-barrier corruption supplies a target plaintext `m` from the ideal
functionality to `SimKeyOpen`; the resulting `sk_star` must be a valid secret key for `pk` and
decrypt `ct` to `m`. The simulator receives no unopened evaluation and no real `sk`.

The game compares the joint transcript, not isolated algorithms:

```text
Real: (pk,sk) <- RealKeyGen; ct <- Enc_pk(y); corruption -> (sk,y,state)
Ideal: (pk,tau) <- SimKeyGen; (ct,sigma) <- SimEnc_pk;
       corruption(y) -> (SimKeyOpen(tau,sigma,y,state), y, state_star)
```

The comparison is quantified over an adaptive corruption schedule that respects the mobile bound,
over all public contexts, and over correlated vectors
`(y_j)_j = (D_h(alpha_j))_j` generated by one hidden degree-`2f` polynomial. For a post-barrier
corruption, the ideal interface returns the erasure state and retained public ciphertext, while
`PECC` proves that no erased key or plaintext is reconstructed. The `R_ved` proof is included in
`public-state`; its simulated transcript must remain accepting for every later `SimKeyOpen`.

This definition exposes the exact relation among the layers. `KeyOrigin` supplies a valid
decryption-capable explanation for an external public key; correlated-NCER supplies vector-level
indistinguishability; commitment equivocation supplies the `M_{h,j}` opening; `R_ved` supplies
public binding; and `PECC` handles post-barrier state. A key-simulatable PKE satisfying only
public-key indistinguishability supplies none of the `SimKeyOpen` guarantee and therefore does not
close this game.

The first construction theorem should be conditional on this explicitly stated game, with the
advantage decomposed as

```text
Adv_EK-CRO <= Adv_KeyOrigin
            + Adv_Correlated-NCER
            + Adv_Commitment/R_ved
            + sum_j Adv_PECC,j
            + Adv_Rved-Soundness
            + Adv_Uncovered-Edge.
```

This is the smallest theorem-level object that bridges HPW15 to the asynchronous protocol. It
also gives a decisive audit rule: any candidate whose simulator calls `SimKeyOpen` with the real
secret key, or whose public proof must be regenerated after a corruption, does not satisfy the
external-key game.

### 19.110 Joint commitment/proof lemma for the hidden polynomial

The remaining `H2 -> H3` step is a relation-preservation problem, not another encryption
assumption. Let `D_h` be the public coefficient-commitment vector, let
`y_j = Eval(D_h,j)` denote the value selected by the coupled hidden polynomial, and let
`M_j = Com(y_j;rho^M_j)`. The candidate requires a commitment mode with the following two
properties:

```text
Real:  M_j <- Com(y_j; uniform rho^M_j)
Sim:   M_j <- SimCom(); later OpenSim(M_j,y_j) -> rho^M_j
```

The public distribution of `SimCom()` must be indistinguishable from the real commitment for
every value selected by `D_h`, and `OpenSim` must preserve the distribution of the opening state
returned at corruption. Perfectly hiding Pedersen commitments with a simulation trapdoor are a
canonical conditional instance: a simulated group element is uniform, and the trapdoor computes
an opening to any later scalar. The commitment trapdoor is never published and is not given to an
endpoint.

**Lemma 66 (joint `D_h`/`M`/`R_ved` simulation, conditional form).** Assume (i) the affine-coupling
simulator samples a degree-`2f` polynomial consistent with all exposed evaluations and the public
`D_h` view, (ii) `M_j` has the simulation interface above, and (iii) `R_ved` has a simulated CRS
whose `SimProve` output is accepting for arbitrary statements and is indistinguishable from a
real proof on true statements. Then the public tuple
`(D_h,(M_j,ct_j,pi_j)_j)` has a simulator that does not know any unopened evaluation and that
answers every pre-barrier corruption with a state consistent with the same coupled polynomial.

**Proof sketch.** Start with real `R_ved` proofs on true statements. First switch the proof CRS and
proofs to `SimProve` while the statements are true; this is the NIZK zero-knowledge transition.
Because the proofs are now simulated, replace each `M_j` by `SimCom()` before changing its
underlying value. Commitment hiding bounds this transition, and `OpenSim` later recovers the
opening for the value supplied by the affine-coupling simulator. The simulated proof depends only
on the public statement, so it does not reintroduce the relation between `M_j` and the hidden
`y_j`. Next apply Lemma 65 to replace `ct_j` by the YLH20 malformed vector. At a corruption, the
ideal functionality supplies `y_j`; the simulator opens `M_j` to `y_j` and invokes YLH20 `S3` on
the encoded payload. The resulting key and opening state pass all local checks. The polynomial
relation is preserved by affine coupling, while no unopened value is delivered. `PECC` then
removes the endpoint state after its barrier.

The order is essential. If `M_j` is made independent before proof simulation, a real proof would
require a witness for a statement whose commitment no longer opens to the real evaluation. If
malformed ciphertexts are introduced before proof simulation, the same issue occurs for the
encryption witness. Thus `SimProve` is the gate that permits both public objects to become
opaque while the hidden polynomial relation is retained only in the ideal state.

The lemma leaves three explicit obligations for a concrete instantiation: affine coupling must
work with the actual `D_h` commitment distribution; `OpenSim` must produce the endpoint's full
opening state rather than only a scalar; and the simulated proof must remain accepting under every
later key opening. A construction satisfying only commitment hiding or only NIZK zero knowledge
does not close the joint lemma.

### 19.111 YLH20 supplies a conditional `KeyOrigin` route

The audit must include Yang, Lai, Huang, Au, Xu, and Susilo's multi-challenge receiver-selective
opening construction. They define `SIM-RSO_k-CPA`, in which each public key may encrypt `k`
challenge messages, and prove a DDH-based construction with secret-key length `k + log(q)` for
bit messages (`/tmp/ylh20.txt:903-951`). The simulator first publishes public keys and malformed
ciphertexts, then receives the messages for the corrupted receivers and constructs secret keys
that decrypt the already published ciphertexts to those messages (`/tmp/ylh20.txt:1000-1060`).
It therefore does not need the original endpoint secret key when producing the simulated opening.

This is stronger evidence for `KeyOrigin` than HPW15's `ksim` alone. In particular, the YLH20
simulator has the shape

```text
S1 -> (PP, pk, simulation state)
S2 -> malformed ciphertext vector
S3(opened messages) -> compatible secret keys
```

and the construction deliberately keeps enough secret-key degrees of freedom to satisfy each
opened message. For a payload larger than one bit, the construction must be extended or repeated;
the paper's lower bound shows that receiver-SO simulation inherently incurs payload-dependent
secret-key entropy when multiple ciphertexts share a key (`/tmp/ylh20.txt:165-183`, `:604-613`).

The model boundary remains essential. YLH20's simulator controls the public-key generation phase
through `S1`; it does not receive an arbitrary public key fixed by an independent registry and
then explain that exact key without a registration-side simulation interface. Thus there are two
valid interpretations of `KeyOrigin`:

```text
protocol-managed registration:
  receiver keys use the YLH20-style special distribution;
  simulated registration may use S1 and later S3 openings.

strict external registration:
  an arbitrary stable pk is fixed before repair and hidden from the simulator's key state;
  YLH20 does not by itself provide an exact-key explanation API.
```

The first interpretation gives a concrete `H1` candidate for the paper, while the second still
requires the stronger `SimKeyGen/SimKeyOpen` interface stated in 19.109. Neither interpretation
closes `H3`: YLH20 has no `M_{h,j}`, hidden Shamir witness relation, `R_ved` proof, or PECC
composition. The updated construction strategy is therefore to use YLH20 as the key-origin and
receiver-SO layer only if key registration is explicitly protocol-managed, then prove the joint
commitment/proof hybrid separately. If the stable-key theorem must allow arbitrary pre-registered
keys, YLH20 remains a related-work boundary rather than an instantiation.

### 19.112 YLH20-to-PVOD lifting target

YLH20 can be mapped to the PVOD payload without forcing a scalar plaintext into a single
bit-message encryption. Let `L` be the encoded length of
`(y_{h,j},rho^D_{h,j},rho^M_{h,j})`. For each receiver `j`, use one YLH20 public key and publish
`L` bit ciphertexts under that key. The receiver secret key contains the shared field component
and one binary branch component per bit. The YLH20 simulator's `S2` publishes all malformed
ciphertexts before the corruption set is known; `S3`, given the opened payload bits, adjusts the
secret-key components so that every opened ciphertext decrypts to the prescribed bit vector
(`/tmp/ylh20.txt:1000-1060`).

The PVOD lift has a precise proof shape. In the real branch, each bit ciphertext is honestly
generated and `R_ved` proves the encoded payload, its openings, and encryption randomness. In the
simulation branch, the YLH20 ciphertext vector is malformed, so it need not have an honest
encryption witness. The simulator therefore uses the simulated CRS and a simulated proof for the
false public relation, while commitment equivocation makes `M_{h,j}` open to the payload returned
at corruption. Simulation-soundness is used only to prevent the adversary from turning the
simulated proof oracle into a new accepted false statement; it does not assert that the simulated
ciphertext has a real encryption witness.

This yields a conditional lifting lemma:

> **YLH20-PVOD lifting target.** Assume DDH, a dual-mode commitment with a statistically hiding
> simulation mode, and a concurrently simulation-sound NIZK for `R_ved`. Under protocol-managed
> YLH20 key registration, the pre-barrier endpoint view for an arbitrary correlated payload vector
> is simulatable from the public `D_h` and the payloads of corrupted endpoints, subject to the
> `KeyOrigin` game. The simulator publishes the complete descriptor before seeing future
> corruption choices and returns a key/witness state consistent with every opened endpoint.

The lemma remains conditional because the NIZK statement must include the bit-encoded YLH20
ciphertext vector and the exact `D_h` relation, while the commitment simulator must open all
`M_{h,j}` values consistently. It also incurs a concrete encoding cost: for an `L`-bit payload,
one endpoint carries `L` YLH20 ciphertexts and a key with `L` binary branch components, before any
proof batching. This is acceptable as a theory candidate but should be reported as the price of
receiver-SO key equivocation, not hidden inside an asymptotic `Enc` notation.

The main theorem can now use the following disciplined status. YLH20 closes the key-origin and
receiver-opening layer for the protocol-managed registration branch, conditional on the lifting
lemma. It does not close arbitrary externally fixed public keys, and it does not by itself prove
the commitment, correlated polynomial, public-proof, or post-barrier PECC layers. The next proof
task is to write this lifting lemma for one labelled generation and verify that no simulated
malformed ciphertext enters an unproved public edge.

### 19.113 Single-generation YLH20-PVOD hybrid audit

Fix one labelled generation `Q` and receiver `j`. Let `L_Q` be the bit length of the private
endpoint payload `(y_{Q,j},rho^D_{Q,j},rho^M_{Q,j})`. The encryption randomness used by `R_ved`
remains only a proof witness and is not sent as an endpoint payload. The candidate uses one YLH20
public key for `L_Q` bit ciphertexts. The hybrid for the
pre-barrier view is:

```text
H0  real protocol-managed YLH20 key, honest encoded ciphertexts, real M and R_ved proofs
H1  YLH20 S1 key/public-parameter view, with no endpoint secret key retained by the simulator
H2  simulated R_ved proofs while the public statements are still true
H3  equivocable commitment mode, with M independent of unopened payloads
H4  YLH20 S2 malformed ciphertext vector, obtained by the per-bit DDH hybrids
H5  after corruption, YLH20 S3-compatible key plus the ideal payload opening
H6  after the local barrier, the PECC-erased endpoint state
```

`H0 -> H1` is the key-registration transition. It is valid only when the protocol itself owns
the YLH20-style registration interface; it is not a reduction for an arbitrary public key supplied
by an independent registry. `H1 -> H2` switches the NIZK proof to simulation while every public
statement remains true, using zero knowledge and a simulated CRS. `H2 -> H3` switches the
commitment to its equivocable simulation mode; the proof is already simulated, so the simulator
does not need an unopened payload to produce it. `H3 -> H4` is the YLH20 multi-challenge hybrid
and costs one DDH hybrid per encoded bit and endpoint. The malformed ciphertexts now need no
honest encryption randomness because the simulated `R_ved` proof is generated for the resulting
false statement. `H4 -> H5` uses `S3` to choose the binary secret-key components after the ideal
functionality supplies the opened payload; its equations preserve the same public key and decrypt
every encoded ciphertext to that payload. `H5 -> H6` is the existing `PECC` transition and is
invoked only after the endpoint frontier.

For one generation, the resulting conditional bound has the form

```text
Adv_view(Q) <= L_Q * n * Adv_DDH
             + Adv_KeyRegistration
             + Adv_Rved-ZeroKnowledge
             + Adv_Commitment-Simulation
             + Adv_Rved-Simulation/Soundness
             + sum_j Adv_PECC,j
             + Adv_Uncovered-Edge.
```

The hidden Shamir correlation does not enter the YLH20 DDH hybrids: all unopened payload bits are
removed by `H4`, while the opened values are supplied only at `H5`. It enters through the affine
coupling and the requirement that the commitment/proof simulator keep every opened value
consistent with the same `D_h`-constrained polynomial. This is the precise point at which a
standard RSO theorem must be lifted to PVOD rather than cited verbatim.

The candidate also has a long-term-use boundary. YLH20's parameter `k` bounds the number of
challenge ciphertexts under one public key, and its lower bound requires secret-key entropy that
grows with the number and length of opened messages (`/tmp/ylh20.txt:165-183`, `:604-613`).
Consequently, the construction must either register a fresh YLH20 key for every labelled
`(Q,j)` and keep `L_Q` finite, or announce a finite lifetime bound and provision the corresponding
key entropy. Reusing one YLH20 key across an unbounded sequence of generations is outside its
theorem and cannot be hidden behind `PECC`.

This audit changes the concrete claim precisely: YLH20 can be a single-generation
`KeyOrigin`/receiver-SO layer for a protocol-managed, context-keyed PVOD construction. The full
paper theorem still requires the commitment/proof lifting and the frontier composition. The strict
arbitrary-external-key and unbounded-key-reuse variants remain separate impossibility or extension
questions.

### 19.114 Conditional DDH lifting lemma for `H3 -> H4`

The central pre-barrier transition can now be isolated from the polynomial simulator.

> **Lemma 65 (YLH20 DDH lifting, conditional form).** Fix a generation `Q` after the NIZK
> proof has been switched to `SimProve` and every public commitment has entered its equivocable
> simulation mode. Suppose the encoded endpoint payloads form any efficiently sampleable joint
> distribution, possibly generated by one hidden Shamir polynomial, and suppose the public
> context and `D_h` state are independent of the DDH challenge used for one encoded bit. Then the
> vector of honest YLH20 ciphertexts can be replaced by the YLH20 malformed ciphertext vector
> before any corruption choice, with distinguishing advantage at most
> `O(|P| L_Q) * Adv_DDH`.

**Proof sketch.** Order the endpoint/bit pairs. For one pair, use the DDH tuple to replace the
correlated YLH20 coordinate `g_j^{w}` by a uniform group element, then multiply it by the public
`h^{alpha}` factor used by `S2`; the remaining coordinates and the final ciphertext component
are computed from the simulator's binary key state. This is the same two-step DDH replacement as
YLH20's Games 2--5 (`/tmp/ylh20.txt:1230-1305`). The reduction does not need the hidden polynomial
constant: it carries the joint payload and all public `D_h` data as auxiliary state, while the
simulated proof is generated from the resulting public statement using the NIZK simulation
trapdoor. Since the proof is already simulated, no witness for the malformed ciphertext is needed.
Summing over `|P|L_Q` pairs gives the bound.

After the replacement, YLH20's exact algebraic identity supplies `H4 -> H5`. For an opened
payload bit `m`, `S3` chooses the corresponding binary secret-key component and adjusts the shared
field component so that the public-key equation is preserved; the resulting key decrypts the
malformed ciphertext to `m` (`/tmp/ylh20.txt:1305-1405`). Applying this independently to all
bits yields a key that decrypts the complete encoded payload. The only information supplied at
this point is the payload of the corrupted endpoint, so the same polynomial correlation is
preserved by the affine-coupling simulator rather than reconstructed by YLH20.

The lemma has three explicit preconditions. First, `SimProve` must generate an accepting proof
for the false statement produced by the malformed ciphertext. Second, the public proof must not
be regenerated after corruption. Third, no public recovery or complaint path may invoke a
decryption oracle on the malformed ciphertext. If any condition fails, the DDH reduction does
not imply PVOD security; the corresponding edge remains charged to `Adv_Uncovered-Edge`.

This lemma closes the previously informal `H3 -> H4 -> H5` step for the protocol-managed,
context-keyed branch, subject to the joint commitment/proof and affine-coupling assumptions. It
does not alter the strict arbitrary-external-key or unbounded key-reuse boundaries.
