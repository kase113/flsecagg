# Long-Lived Share Repair Construction Audit

## VSSR 代数、恢复闭包反例与最小可行参数

> 日期：2026-09-10  
> 目标：判断 VSSR 能否作为 `BF-RPTA/RCL` 的最小长期恢复实例，并给出下一步只需证明的构造目标。  
> 当前裁决：**原生 VSSR、`VSSR + ephemeral PKE`、以及在 `n=3f+1` 下把门限改为 `2f+1` 的版本都不能直接作为长期 RCL。** 最小可行出口是先证明一个一般的恢复冗余边界，再在 `n>=3f+2` 下构造只以当前 direct shares 为持久秘密状态、恢复后仍可继续帮助恢复的 frontier-closed resharing。

## 1. 为什么需要重新审计

此前的候选路线是把 VSSR 按 coordinate 独立部署，并做三项修改：

1. 退休时删除 direct share 与 recovery-polynomial shares；
2. 把恢复门限从典型的 `f+1` 提高到 `2f+1`；
3. 用 target-specific ephemeral encryption 保护恢复贡献，安装或取消后擦除接收者密钥。

这条路线解决了两个真实问题：低门限 repair amplification，以及诚实接收者擦除密钥后的被动 transcript 归档。但是，精确展开 VSSR 代数后还存在三个独立缺口：

- 在 `n=3f+1` 下，缺失份额的 target 不能帮助自己，最多只有 `n-f-1=2f` 个必然响应的正确 helper，因而 `q_rec=2f+1` 不活；
- 一份恢复 transcript 重构的是整个 masked polynomial `s+s_g`。若共享 DPRF 状态在未来暴露，该 transcript 可展开同组最多 `k-1` 个旧 direct shares，而不只是 target 的一个 share；
- VSSR 恢复后的状态把 recovery-polynomial components 置为 `bot`，只能恢复 direct share，不能恢复下一次帮助别人所需的 recovery-complete state。

因此，ephemeral PKE 是必要的 transcript 防护之一，但不是完整修复。

## 2. 原文网络与安全边界

VSSR 的密码学构造自称独立于底层网络模型；PBFT 集成只明确假设消息带发送者签名或 authenticated communication。恢复流程是 target 广播 request，其他副本返回 `vssRecoverContrib*`，target 验证并保存有效响应，凑够门限后恢复。

原文没有给出以下任一性质：

- recovery response 的机密信道；
- receiver key 擦除后的 transcript forward secrecy；
- 针对未来 channel-state exposure 的恢复消息不可解封性。

因此，在本文模型中不能把 VSSR response 默认视为秘密 transcript。若外层协议需要这项性质，必须显式增加 target-ephemeral encryption 或等价机制，并在安全游戏中计入接收者被腐化的窗口。

原文依据：

- 一般恢复接口与 `k` 个有效贡献：`Efficient Verifiable Secret Sharing with.pdf_by_PaddleOCR-VL-1.6.md:216`；
- PBFT 网络只明确签名来源：同文件 `:349`；
- 恢复 request、验证和保存 response：同文件 `:404`；
- hiding game 对单 commitment 累计限制来源数 `<k`：同文件 `:230`。

## 3. VSSR 的精确代数

固定一个 VSSR commitment `c*`。令：

```text
s(X)       : 原始 degree-(k-1) secret polynomial
s_g(X)     : 第 g 个 degree-(k-1) recovery polynomial
G_g        : recovery polynomial g 编码的 target 集合，|G_g| <= k-1
r          : 该 sharing 的公开 nonce
alpha_h    : helper h 的 DPRF secret share
u_h*[0]    = s(h)
u_h*[g]    = s_g(h)
```

对 target `i in G_g`，dealer 令：

```text
s_g(i) = F_alpha(<r,i>).
```

helper `h` 生成的恢复贡献是：

```text
a_{h,g} = u_h*[0] + u_h*[g]
        = s(h) + s_g(h),

d_{h,i} = DPRF.Contrib(alpha_h, <r,i>),

mu_{h->i} = (a_{h,g}, witness_{h,g}, d_{h,i}, proof_{h,i}).
```

target 从集合 `R` 收集 `|R|>=k` 个通过 `vssRecoverVerify*` 的贡献。然后：

```text
P_g(X) = Interpolate({(h,a_{h,g}) : h in R})
       = s(X) + s_g(X),

y_i    = DPRF.Eval(<r,i>, {d_{h,i} : h in R})
       = s_g(i),

s(i)   = P_g(i) - y_i.
```

验证可以剔除 malformed Byzantine contribution：DPRF contribution 有公开验证，`a_{h,g}` 也按组合 commitment `c(s)+c(s_g)` 验证。只要存在 `k` 个会响应的正确、recovery-capable helper，target 最终能收集 `k` 个有效值。

这里最重要的语义不是“target 得到一个 share”，而是：

```text
k 个 a-contributions公开确定整个 P_g = s+s_g。
```

## 4. Typed Capability Edges

对 coordinate `ell`，定义：

```text
D_{ell,h}       : direct share s_ell(h)
R_{ell,h,g}     : recovery-polynomial share s_{ell,g}(h)
A_{ell,h}       : coordinate-local DPRF share
A_h^global      : 跨 coordinate 持久 DPRF share
M_{ell,h->i}    : plaintext recovery contribution
C_{ell,h->i}    : encrypted recovery contribution
E_{ell,i}       : target ephemeral decryption key
P_{ell,g}       : reconstructed masked polynomial
Y_{ell,i}       : DPRF output for target i
```

helper generation edge：

```text
{D_{ell,h}, R_{ell,h,g}, A_{ell,h}, r_ell, c_ell, T_req}
    -> M_{ell,h->i}.
```

若使用 target-ephemeral encryption：

```text
M_{ell,h->i} -> C_{ell,h->i},
{C_{ell,h->i}, E_{ell,i}} -> M_{ell,h->i}.
```

组合 edge：

```text
{M_{ell,h->i} : h in R, |R|>=k} -> P_{ell,g}, Y_{ell,i}, D_{ell,i}.
```

若 DPRF authority 跨 coordinate 保留并在未来完整暴露，还存在：

```text
{A_h^global : h in K, |K|>=k} -> Y_{ell,j} for every old (r_ell,j),

{P_{ell,g}, Y_{ell,j}} -> D_{ell,j} for every j in G_g.
```

后两条 edge 正是只看 target output 时容易漏掉的 group amplification。

## 5. 反例一：`k=f+1` 的普通 Repair Amplification

取典型参数：

```text
n = 3f+1,
a = 2f+1,
b = f,
q_dec = 2f+1.
```

退休后的最坏初始旧 direct shares 数是：

```text
x = n-a+b = 2f.
```

若 VSSR 保持 `q_rec=k=f+1`，则 `x>=q_rec`。同一批旧 helper capabilities 可以恢复新的 target share，新 share 又可加入后续恢复；在 homogeneous repair 模型中闭包扩张到全部节点。因此普通 VSSR 门限直接把有效历史隐私门限从 `2f+1` 降到 `f+1`。

## 6. 新定理：Target-Exclusion Recovery Gap

仅把 `q_rec` 提高到 `2f+1` 仍不成立，因为恢复 target 已经丢失了自己的 helper capability。

### Theorem 1: Homogeneous Recovery Feasibility Bound

假设：

1. 每次恢复一个正确 target `i`，`i` 不能为自己的恢复提供缺失 capability；
2. 最多 `f` 个其他节点 Byzantine 并永久 withholding；
3. 任意 `q_rec` 个同质 helper capabilities 可以恢复任意 target；
4. 退休证书最多等待 `a<=n-f` 个确认；
5. 生命周期内至多 `b` 个退休节点的旧 capability 被攻击者保存；
6. `a>=b`。

则同时满足恢复活性与 privacy finality 必须有：

```text
f+b < q_rec <= n-f-1.
```

因此必要条件为：

```text
n >= 2f+b+2.
```

当 `b=f` 时：

```text
n >= 3f+2.
```

### Proof

为保证恢复活性，target 之外最多只有 `n-f-1` 个必然正确响应者，所以 `q_rec<=n-f-1`。

另一方面，退休证书至多取 `a=n-f`。未来全体当前状态暴露并合并至多 `b` 个退休前保存的旧状态后，最坏初始能力数至少为：

```text
x = n-a+b >= f+b.
```

homogeneous repair 的 privacy finality 要求 `x<q_rec`，所以 `f+b<q_rec`。合并两式即得：

```text
f+b+1 <= n-f-1,
```

等价于 `n>=2f+b+2`。

### Corollary 1: One-Replica Gap

在自然预算 `b=f` 下，最小异步 BFT 配置 `n=3f+1` 无法同时满足：

- 等待至多全部正确节点的退休活性；
- 一个丢失本地份额的正确节点的恢复活性；
- homogeneous reusable repair 下的 privacy finality。

矛盾恰好差一个节点：

```text
privacy requires q_rec >= 2f+1,
recovery permits q_rec <= 2f.
```

在 `n=3f+2` 时可取：

```text
a = 2f+2,
x = 2f,
q_rec = q_dec = 2f+1,
n-f-1 = 2f+1.
```

这只是访问结构可行性，不自动给出 transcript-safe、可验证且可重复的具体协议。

## 7. 反例二：VSSR Group-Transcript Amplification

考虑 target `i in G_g` 在退休前完成一次恢复并保存 plaintext transcript。`k` 个有效 `a_{h,g}` 允许它重构：

```text
P_g(X)=s(X)+s_g(X).
```

此时它只从 transcript 中得到 `Y_i=s_g(i)`，所以立即恢复的是 `D_i=s(i)`。但是，如果 DPRF shares 是跨 coordinate 的持久状态，未来全体当前状态暴露会给出至少 `k` 个 `alpha_h`，于是攻击者可对同一旧 nonce `r` 计算：

```text
Y_j = F_alpha(<r,j>) = s_g(j)
```

对每个 `j in G_g` 都成立。因此：

```text
D_j = P_g(j)-Y_j, for every j in G_g.
```

一份历史 target transcript 因而可以扩张为最多 `k-1` 个 direct shares。对 `k=2f+1`，一次 transcript 最多展开 `2f` 个旧 share。

### 为什么 ephemeral PKE 不足

target-ephemeral encryption 可以阻止以下攻击：被动保存 ciphertext，等未来暴露普通 channel state 后解密。

但它不能阻止 Byzantine target：target 在合法恢复窗口拥有 `esk`，可以保存 plaintext `P_g`。若未来全局 DPRF authority 暴露，组展开仍然发生。因此，不能把“腐化一个 target 并保存 transcript”只记作一个 direct share，除非另外满足至少一项：

1. DPRF shares 也是 coordinate-local，并由 Robust-Hitting 退休集合删除到少于 `k`；
2. DPRF authority 支持按 coordinate 的真正 puncture；
3. 恢复协议只向 target 泄漏 `P_g(i)`，而不泄漏整个 `P_g`；
4. 每个 recovery polynomial 只编码一个 target，从而放弃 VSSR 的分组压缩。

最小的 VSSR 补丁是第 1 条，而不是“共享 DPRF 可以无条件保留”。

## 8. 反例三：VSSR 恢复状态不闭合

VSSR 原文明确规定，恢复出的 `u_i*` 只有 `u_i*[0]` 是原始 direct share；其余 recovery-polynomial components 为 `bot`，验证时也跳过这些 components。也就是说：

```text
Recover VSSR state of i
    -> direct share D_i
    -/-> recovery-polynomial shares R_{i,g}.
```

因此，恢复后的节点可以参与原秘密重构，却不能完整执行未来的 `vssRecoverContrib*`。这对“初始 sharing 中少数节点漏收 share”足够，但不满足长期 crash/cure：节点依次崩溃并恢复后，recovery-capable helper 集合会单调缩小。

在 `n=3f+2,k=2f+1` 的紧参数下，第一次恢复已经需要 target 之外全部 `2f+1` 个正确 helper。若该 target 只恢复 direct share，下一次恢复时最坏只剩 `2f` 个正确 recovery-complete helper，立即失去活性。

用 VSS 再备份 recovery-polynomial shares 只会把同一问题递归一层；除非恢复输出重新成为完整 helper capability，否则它不是长期 RCL。

原文也把 proactive share recovery 明确留作 future work，见同文件 `:588`。

## 9. Retired-Coordinate Closure：什么条件才够

对 retired coordinate `ell`，若仍想把 VSSR 作为一次性子程序，至少需要：

1. `D_{ell,h}`、全部 `R_{ell,h,g}`、`A_{ell,h}` 和 helper plaintext 在同一 retirement transition 中删除；
2. target contribution 使用绑定 `(rid,ell,target,T_req,epk_target)` 的临时加密；
3. 正确 target 在 install、cancel 或 retirement 时删除 `esk_target` 与 plaintext；
4. 被腐化 target 保存的 plaintext transcript 显式进入 `X_hist`；
5. 退休后存活的 coordinate-local DPRF shares 少于 `k`；
6. 所有 pre-finality transcript 只能恢复已计入 `B` 的 target share，不能经共享 authority 展开为额外 shares。

在这些条件和 `x<k` 下，攻击者不能形成新的 helper contribution，也不能从历史 transcript 计算新 target 的 `Y_j`。于是才可证明：

```text
Cl_rec(X_ell) intersection C_dec
= X_ell intersection C_dec.
```

但是，这个结论仍不解决 live coordinate 的可重复恢复；它只说明退休闭包如何关闭。

## 10. Live-Coordinate Liveness：必须区分两种状态

### 10.1 Direct state

节点参与门限解密所需的份额：

```text
D_{ell,h}.
```

### 10.2 Recovery-complete state

节点生成未来恢复贡献所需的全部秘密状态：

```text
H_{ell,h} = D_{ell,h}
          + local recovery metadata
          + any local recovery-authority share.
```

长期 cure 的正确性不能只证明 `Recover -> D_{ell,i}`，而必须证明下列二者之一：

```text
state-complete repair: Recover -> H_{ell,i};

or

direct-share-only helper: future contributions require only D_{ell,i}
                         and fresh erasable randomness.
```

VSSR 两者都不满足：它恢复不到 `R_{ell,i,g}`，而生成 contribution 又必须使用这些 RP shares。

## 11. 候选路线比较

| 路线 | 退休闭包 | 单次恢复 | 可重复 cure | 主要代价 | 裁决 |
|---|---:|---:|---:|---:|---|
| 原生 VSSR，`k=f+1` | 失败 | 是 | 否 | 低 | No-go |
| VSSR，`k=2f+1,n=3f+1` | 条件安全 | 不活 | 否 | 低 | No-go |
| VSSR + ephemeral PKE | 仍受全局 DPRF 组展开影响 | 条件 | 否 | 低 | No-go |
| `n=3f+2` + coordinate-local DPRF VSSR | 可关闭 | 一次可活 | 否 | 每 coordinate DPRF | 仅一次性见证 |
| 每 target 独立 RP | 可避免组展开 | 条件 | 否 | `Theta(n)` RP/coordinate | 不推荐 |
| pairwise zero-sum masked LSR | 可设计为 direct-share-only | 可活 | 可活 | `Theta(n^2)` mask 交互与证明 | 可行但证明重 |
| frontier-closed verifiable resharing | 可设计为只保留 current share | 可活 | 可活 | AVSS/ACS 或 PVSS resharing | 推荐基线 |

## 12. 最小可行主线

当前最窄、同时具备理论深度和可构造性的主线是：

> **Privacy-Final Repair under Minimal Redundancy.** 刻画长期移动腐化和未来全体当前状态暴露下，退休、恢复和 Byzantine withholding 三者的精确可行区间；证明 `n=3f+1,b=f` 对 homogeneous reusable repair 存在 target-exclusion impossibility，并在紧参数 `n=3f+2,q=2f+1` 下构造 frontier-closed、transcript-hiding、direct-share-only 的异步可验证 resharing。

这个叙事比“给 VSSR 加删除”更强，因为它包含：

1. 一个访问结构上的必要充分条件；
2. 一个最小 BFT 配置下恰差一个节点的紧不可能性；
3. 一个达到 `3f+2` 下界的正向协议；
4. VSSR group transcript 和 state-incomplete recovery 两个具体黑盒分离；
5. 对动态委员会的自然扩展：handoff 同样必须保持 frontier-closed state completeness。

## 13. 推荐正向原语：Frontier-Closed Resharing

下一步不应继续给 VSSR 打补丁，而应只定义并实例化以下最小接口：

```text
FCR.Repair(rid, ell, target, T_req)
```

要求：

1. **Current-share-only persistence**：每个 coordinate 的持久秘密恢复状态就是当前 direct share；不保存 RP、backup seed 或跨 coordinate 可重放 authority；
2. **Target exclusion tightness**：在 `n=3f+2` 下，从 target 之外 `2f+1` 个有效 helper 完成恢复；
3. **State completeness**：恢复出的 share 可立即作为后续恢复 helper；
4. **Verifiability**：Byzantine helper 不能令不同正确节点安装不一致或无效 share；
5. **Contribution privacy**：target 只学习自己的恢复 share，不学习 helper direct shares 或可在未来展开为其他 shares 的 masked polynomial；
6. **Transcript finality**：历史 ciphertext 与未来 current-state exposure 不能恢复 retired coordinate；
7. **Frontier monotonicity**：generation、extraction、installation 三处都受同一 `T_req` 和本地 frontier 支配；
8. **Asynchronous liveness**：不等待 Byzantine helper，在 eventual delivery 下由全部 `n-f-1=2f+1` 个其他正确节点完成。

最保守的实例化方向是复用已有 AVSS/PVSS resharing：先由异步一致机制确定有效 helper set，再把旧 sharing 转换为同一 secret 的新 sharing，并显式加入 old-share consistency proof。这里的创新不应声称“发明 resharing”，而是证明现有 resharing在 future-exposure 模型下还必须满足 transcript finality、frontier closure 和最小冗余边界。

## 14. Go / No-Go

### No-Go

- 不再把 `q_rec=q_dec=2f+1`、`n=3f+1` 写成可行参数；
- 不再声称共享 DPRF 在 coordinate-local RP 删除后可以无条件保留；
- 不再把 VSSR 视为可重复 cure 的 current-share-only repair；
- 不把 ephemeral PKE 单独写成恢复闭包充分条件。

### Go

- 把 Target-Exclusion Recovery Gap 提升为正式定理；
- 以 `n>=2f+b+2` 为 homogeneous reusable repair 的最小冗余边界；
- 对自然 `b=f` 参数研究紧点 `n=3f+2,q=2f+1`；
- 把 VSSR 作为 matching counterexample 和一次性恢复基线；
- 下一轮只审计一个现有 asynchronous resharing/DPSS 协议能否满足 `FCR` 八项接口。

## 15. 下一步证明清单

1. 将 Theorem 1 推广到一般访问结构：恢复访问集必须避开 retirement 后能力集合，同时完全包含于 target-excluded live responder family；
2. 明确 `b` 是每 coordinate 生命周期累计腐化预算，而不是瞬时腐化数；
3. 从本地 APSS、DyCAPS、bDPSS 文档中选一个最小 resharing 流程，写出输入/输出和 transcript；
4. 检查 resharing 是否恢复 direct-share-only helper state，还是隐含持久 backup；
5. 检查不同正确节点是否需要 ACS/BA 来统一 helper set；
6. 检查 private subshares 在 receiver 未来腐化时是否需要 forward-secure/ephemeral channels；
7. 若现有协议无法直接满足，确定最小修改，而不是另造完整 DPSS。

## 16. 当前最终判断

VSSR 审计没有否定整条 privacy-finality 主线，反而找到了更清晰的理论中心：**长期恢复不是在原有 `3f+1` BFT 参数上免费添加的功能。target 自身不能参与恢复这一事实，与退休后的历史能力下界共同产生一个紧的最小冗余门槛。**

VSSR 最有价值的角色也因此改变：它不再是候选最终构造，而是展示三个组合陷阱的最佳具体基线：低门限 repair amplification、masked-polynomial transcript amplification，以及 state-incomplete recovery。正向协议应从 state-complete current-share resharing 出发，在 `3f+2` 紧参数上证明恢复闭包、异步活性和 transcript finality。

## 17. APSS / DyCAPS / DPSS 审计

### 17.1 APSS：删除旧份额，但不是本文的 repair

APSS 通过共同生成零常数项多项式 `p`，令每个节点更新：

```text
sk'_i = sk_i + p(i),   p(0)=0,
```

并明确要求节点删除 `sk_i`。这是有价值的两个基线：它证明异步 refresh 可以把旧 direct share 从诚实节点状态中删除，也暴露了删除与协议终止之间的耦合，因为节点过早删除旧 share 可能无法继续参与 VABA。

但 APSS 的模型是静态 Byzantine adversary；它刷新整个长期 secret，而不是为一个已丢失的 coordinate share 提供 target-excluded repair。它没有处理并发、无序的 per-`sid` retirement，也没有把历史 recovery transcript 纳入 privacy-finality。故 APSS 不能直接实现 `FCR`，只能提供“刷新并擦除”子程序的参考实现。

原文依据：`/home/yzc/flagg/apss_keyrefresh_2022_1586.txt:238`（静态腐化和私密认证信道）、`:513`（刷新公式）、`:536`（删除旧 share 的活性问题）。

### 17.2 DyCAPS：最近邻，但依赖 epoch 语义

DyCAPS 更接近目标：它支持 mobile adversary、动态委员会、forward-secure private channels 和旧状态擦除。其 handoff 先把旧 full share 转成 reduced share，再生成零多项式刷新，最后恢复新委员会的 full share；正常状态使用 `t+1` 阈值，handoff 中暂时提高到 `2t+1`，正好体现了 target exclusion 和移动腐化的访问结构变化。

然而，它的安全边界不能直接移植到本文：

1. handoff 依赖相邻 epoch，且假设前一次 sharing/handoff 已使每个 honest 节点获得有效 share；
2. 旧节点在 local epoch 结束时擦除，forward-secure channel 依赖 epoch/local-event 规则；
3. handoff 的目标是把同一个 secret 交给下一委员会，不是只对一个无序 `sid` 关闭恢复能力；
4. 原协议没有证明任意一个 pre-finality、被延迟的 handoff transcript 在未来全状态暴露下不能重新生成 retired coordinate capability。

所以 DyCAPS 是 **FCR 正向构造的最佳技术基线**，但需要把 global/local epoch 替换为每个 coordinate 的 authenticated frontier，并重新证明 transcript extraction 与并发 handoff 闭包。

原文依据：`/home/yzc/flagg/dycaps_2022_1169.txt:149`--`:176`（epoch、擦除、forward-secure channel 和 mobile adversary）、`:314`--`:356`（handoff phases 和 threshold switch）。

### 17.3 Optimistic DPSS：高效 handoff，不解决 selective finality

Optimistic DPSS 同样采用旧委员会向新委员会加密分发 share、公开承诺和验证证明，并在 handoff 后删除旧私密状态。这种流程可用作 `FCR.Repair` 的工程基线：把“新委员会”暂时设为同一委员会，把缺份额节点当作新节点，把 live coordinate 的 handoff 作为一次 state-complete repair。

但它仍然以 epoch/committee handoff 为接口，且安全证明围绕每个 epoch 的 corruption budget 和委员会切换，不围绕任意并发 `sid` 的 retirement frontier。尤其是，加密旧 share 的 ciphertext 不是自动的 transcript finality；必须说明接收者解密密钥、旧节点私钥和 handoff proof 在 frontier 提升后如何失效或被擦除。

原文依据：`/home/yzc/flagg/optimistic_dpss_2025_880.txt:489`--`:505`（handoff 入口）、`:1023`（删除旧私密状态）、`:1721`--`:1757`（加密 share、证明与接收者解密）。

## 18. 正向构造的重新表述

真正需要的不是“VSSR 的 target-specific 加密版”，而是一个 **Frontier-Gated Selective Resharing (FGSR)**：

```text
FGSR.Repair(rid, ell, target, T_req)
```

在 live coordinate 上，它对当前 sharing 执行一次 state-complete resharing：

```text
old current sharing
    -> target-excluded asynchronous handoff
    -> fresh sharing of the same coordinate secret
    -> every correct node holds a complete current share.
```

在 retired coordinate 上，`T_req[ell]=1` 使所有 generation、decryption 和 installation edge 失效。与 VSSR 的差别是：FGSR 不把一个 masked polynomial transcript 交给 target，也不保存独立 recovery polynomial；它把完整新 sharing 作为唯一持久恢复状态，旧 sharing 在已认证 frontier 后统一退出。

### 最小消息语义

每条 private subshare message 至少绑定：

```text
(rid, ell, cfg_old, cfg_new, T_req, receiver, share-commitment).
```

发送者只在本地 frontier 允许时生成；接收者只安装不被本地 frontier 支配的输出；旧 receiver secret 和 plaintext 在 handoff 完成、取消或 retirement 时擦除。历史 ciphertext 仍可公开保存，但不能在未来 current-state exposure 下解密为旧 coordinate share。

### 关键差异与创新点

已有 APSS/DyCAPS/DPSS 已经有 resharing 技术，因此论文不能把“异步 resharing”本身作为贡献。可发表的差异应是：

1. **Selective**：只对 live coordinates 执行，退休 coordinate 永久吸收；
2. **Epoch-free at the application layer**：底层可复用 handoff，但安全语义由无序 `sid` frontier 决定，而非假设一个全局轮次；
3. **Closure-aware**：证明旧 handoff transcript、未来全状态暴露和再次 repair 的联合闭包安全；
4. **Minimal redundancy**：证明 target exclusion 导致 `n>=2f+b+2`，并在 `b=f` 的紧点 `n=3f+2,q=2f+1` 给出正向参数；
5. **State completeness**：每次 repair 输出可继续帮助下一次 repair，避免 VSSR 恢复后只剩 `u_i[0]` 的状态退化。

## 19. 目前可验证的最小协议目标

下一步只需对 DyCAPS-style handoff 做一个固定委员会、单 coordinate 的 reduction：

```text
n = 3f+2,
normal threshold = q_dec = 2f+1,
repair threshold = q_rec = 2f+1,
one target may be missing its current share,
at most f Byzantine helpers withhold or equivocate.
```

成功标准不是先做完整联邦学习系统，而是证明以下五个性质：

1. `2f+1` 个 target 之外的正确 helper 足以完成 state-complete repair；
2. Byzantine helper 不能让两个正确节点安装不同的 share polynomial；
3. repair 完成后，每个正确节点都拥有下一次 repair 所需的完整 current state；
4. retired coordinate 的 `Cl_rec` 不因迟到 handoff transcript 或 future exposure 扩张；
5. live coordinate 在 eventual delivery 下继续可修复。

若该 reduction 失败，失败原因会精确落在三类之一：target-exclusion 计数、旧 transcript 可提取、或 handoff 输出不 state-complete。三者均比继续堆叠密码学组件更适合作为理论结果。

## 20. 更新后的裁决

```text
VSSR       = concrete counterexample and one-shot recovery baseline
APSS       = asynchronous erase/refresh baseline, static corruption
DyCAPS     = closest mobile/dynamic resharing baseline, epoch-dependent
Optimistic DPSS = efficient handoff baseline, epoch and committee dependent
FGSR       = proposed selective, frontier-gated, state-complete wrapper
```

当前主线不再声称已有 APSS/DyCAPS 可以直接满足 privacy finality。论文的核心问题是：**能否把已有异步 resharing 的正确性，提升为无序选择性退休下的 recovery-closure safety，并达到 target exclusion 给出的最小冗余边界？**

## 21. DyCAPS-Style 单坐标正向见证

> **状态：SUPERSEDED（历史候选，不是当前构造）。** 本节保留用于记录为什么
> bivariate handoff 曾被考虑，以及它留下的 transcript 风险。当前方案改用第 23
> 节的 One-Shot Share-to-Share FGSR；不要把本节的四阶段 handoff 当作 FGSR
> 协议或主张。

### 21.1 适配方式

固定一个 live coordinate `ell`，把一次 repair 看成同委员会 handoff：旧状态属于 `C_old`，新状态属于 `C_new`，两者成员身份可以相同，但缺份额 target `i` 只作为新节点参加。旧节点将当前 sharing 的 bivariate representation 转为 reduced share；新委员会生成零常数项随机 bivariate polynomial；最后将 refreshed reduced share 转回完整 current share。

在最小参数下：

```text
n = 3f+2,
t = f,
q_dec = q_rec = 2f+1.
```

若 target `i` 丢失旧 share 但不是 Byzantine helper，则旧委员会仍有：

```text
n - f - 1 = 2f+1
```

个其他正确节点。它们足以向每个新节点发送 `Reduce`，满足 `2t+1` 个有效旧输入；新节点据此插值 reduced share。随后 `GenBivariateZeroPoly` 生成 `Q(0,0)=0` 的刷新多项式，`ShareDist` 从 `2t+1` 个有效新输入恢复完整 refreshed share。故计数上满足：

```text
target-excluded liveness: q_rec <= n-f-1,
privacy against b=f history: n-a+b < q_rec,
```

在最大退休证书 `a=n-f` 时，两式同时取紧点 `q_rec=2f+1`。

### 21.2 为什么它比 VSSR 更适合 FCR

DyCAPS-style handoff 的输出不是一个只含 `u_i[0]` 的 VSSR recovered state，而是新的完整 bivariate current state。节点可以继续参加下一次 `Reduce`、`Proactivize` 和 `ShareDist`。因此它满足 FCR 所需的 state completeness 方向，并避免 VSSR 的 masked-polynomial group transcript 作为 target 的最终恢复材料。

这仍不等于安全定理。resharing 消息本身携带旧 share 的函数，若被公开归档或由未来暴露的 receiver key 解密，仍必须进入 `Cl_rec`。所以 FCR 需要把 DyCAPS 的 private channels 改成显式的 frontier-gated transcript interface，而不是仅引用原论文的 channel 假设。

### 21.3 三个必须完成的 reduction

1. **Crash-compatible liveness：** 形式化“一个正确 target 缺失旧 share”是否可视为旧委员会中的 non-responding node，并逐条重做 `ShareReduce` 和 `ShareDist` 的响应计数；
2. **Frontier transcript security：** 证明所有旧 share subshares 都绑定 `(rid,ell,cfg_old,cfg_new,T_req,receiver)`，并在 retirement/cancel/handoff completion 时擦除可解封状态；
3. **Closure preservation：** 对 retired `ell` 禁止启动 handoff；对已经启动的实例证明其迟到消息不能产生未被历史预算 `B` 计入的 `D_{ell,j}`，对 live `ell` 证明新输出仍是 complete current state。

如果第 1 项成立而第 2 或第 3 项失败，失败不是 DyCAPS 的普通正确性问题，而是本文的 privacy-finality 新边界；这正是该基线适合承载论文创新的原因。

## 22. 当前执行结论

```text
Combinatorial feasibility : GO at n=3f+2
State completeness         : plausible via bivariate handoff
Original DyCAPS security   : insufficient for arbitrary sid finality
FGSR reduction             : next concrete proof task
```

因此暂不引入 pairwise zero-sum masks，也不重新设计完整 AVSS。下一步改为设计一个单次 share-to-share resharing：resharing 同时完成 repair 和 refresh，不复制 DyCAPS 的四阶段结构；只有在该最小流程无法满足 transcript security 时，才考虑 puncturable recovery authority。

## 23. 更适配本文的构造：One-Shot Share-to-Share FGSR

### 23.1 设计原则

本文需要的是“一个 coordinate 的当前份额丢失后恢复并立即进入新状态”，而不是两个委员会之间搬运完整 bivariate state。因此采用标准 resharing 的最小代数：每个有效旧 helper 将自己的当前份额作为新随机多项式的常数项，通过 VSS/AVSS 分发；所有新节点对同一 helper 集合使用相同的 Lagrange 系数线性合成。

这一步同时完成三件事：

```text
repair target share
refresh all current shares
make the repaired share usable for the next repair
```

它不需要 VSSR 的 recovery polynomial、全局 DPRF，也不需要 DyCAPS 的 `ShareReduce -> Proactivize -> ShareDist` 三次状态变换。保留的只有异步 VSS/ACS 所必需的验证和共同 helper-set 选择。

### 23.2 代数

固定 live coordinate `ell`。当前 sharing 是 degree-`d` polynomial `F(X)`，每个节点 `h` 持有：

```text
z_h = F(h),
```

其中 `d=q_rec-1=2f`。对一个 repair instance `rid`，ACS 输出 `V` 并确定
`H=Canonical_{2f+1}(V)`；每个 `h in H` 必须通过当前 commitment、equality
proof 和 `AvailCert_h` 验证。

每个 helper 独立采样 fresh degree-`d` polynomial：

```text
f_h(X) = z_h + a_{h,1}X + ... + a_{h,d}X^d.
```

helper 通过可验证异步 sharing 向每个新节点 `j` 提供 `f_h(j)` 及证明。令：

```text
lambda_h = LagrangeCoeff(H, h, 0).
```

每个新节点计算：

```text
F'(j) = sum_{h in H} lambda_h * f_h(j),

F'(X) = sum_{h in H} lambda_h * f_h(X).
```

因为 `f_h(0)=F(h)`，所以：

```text
F'(0) = sum_{h in H} lambda_h F(h) = F(0).
```

`F'` 是由 fresh coefficients 形成的新 degree-`d` sharing。target 即使没有旧的 `F(target)`，也可以直接安装 `F'(target)`；它得到的是一个普通 current share，而不是 VSSR 的 masked polynomial。

### 23.3 为什么需要共同 helper set

不同节点若使用不同的 `H`，会得到不同的常数项或不同的 sharing polynomial，后续 threshold decryption 可能不一致。因此 `H` 不是本地超时选择，而是由异步 ACS/validated agreement 共同确定，并且每个 helper 的旧 share commitment、resharing commitment 和 frontier 都绑定到同一个：

```text
(rid, ell, cfg, T_req, H).
```

如果 Byzantine helper 不响应或没有 `AvailCert_h`，它不能进入 `H`；如果 Byzantine helper 提供了通过 commitment 和 AVSS completion 的有效 polynomial，则其贡献可以安全纳入，因为它仍然是同一旧 `F` 的合法 evaluation。不能用“收到的前 q 条消息”替代共同集合。

### 23.4 这个流程相对于 DyCAPS 的优化

| 目标 | DyCAPS-style handoff | One-Shot FGSR |
|---|---|---|
| 修复对象 | 新委员会完整 state | 一个 coordinate 的 current sharing |
| 刷新方式 | reduced share、零多项式、full share 三阶段 | resharing polynomial 本身完成刷新 |
| target 输出 | bivariate/full-state material | 一个普通 `F'(target)` |
| 全局 epoch | 相邻 epoch handoff | `rid/ell/T_req` 应用层实例 |
| 额外密码学 | KZG bivariate commitments、threshold switch | 单层 VSS/AVSS commitment |
| 状态闭合 | 需证明 bivariate state 可继续 handoff | scalar current share 直接可继续 resharing |
| 适用范围 | committee transfer | selective repair + refresh |

这不是声称 One-Shot FGSR 在通信上自动优于所有 DyCAPS 实例：朴素 VSS resharing 仍可能需要 `O(n^2)` 通信。优化点是删除与本文问题无关的 bivariate state 和阶段切换，减少安全证明中可形成 recovery edge 的对象。

### 23.5 Transcript 与移动腐化处理

helper 到 receiver 的 `f_h(j)` 不是公开消息。每个 subshare 使用 receiver-specific ephemeral key 加密，并携带：

```text
(rid, ell, cfg, T_req, H, h, j, commitment-to-f_h).
```

正确 receiver 只在安装 `F'(j)` 前保留待合成的 plaintext；安装、取消或 retirement 后擦除 plaintext 和 ephemeral secret。helper 在发送后擦除 `f_h` 的系数和未发送缓存。若某节点在该 repair instance 的解封窗口内被腐化，其所见 subshares 进入该实例的历史 corruption budget，不能再被错误地当作普通 future state。

这里的证明目标是：

```text
future full-state exposure + archived ciphertexts
    -/-> old F_ell(j) for retired ell,
```

除非攻击者在退休前已经获得足够多的 helper polynomials/subshares；这种情况必须由 `B` 和 recovery closure 明确计数。对 retired `ell`，frontier 一旦被 ACS 认证，新的 resharing instance 不得启动；已启动实例只能安装 `T_req` 仍允许的 live output。

这里的硬不变量不是“所有节点都已删除 `F'`”，因为异步 retirement 只要求
一个满足活性的确认集合。令 `A_ell` 为已确认并擦除的节点，`U_ell=P\A_ell`
为残留节点；`U_ell` 的 `F'`/pending state 必须显式进入 recovery closure。
在紧参数下要求 `|A_ell|>=n-f=2f+2`、`|U_ell|<=f`，并与历史暴露满足
`|U_ell|+|B_ell|<q_rec=2f+1`。若所有节点都保留 `F'`，全体状态暴露可重构
`F'(0)=F(0)`；因此安全依赖 residual-state closure，而不是假设全员擦除。

### 23.6 正确性与 state completeness

若 `H` 中所有使用的旧 evaluations 与 `F` 的 commitment 一致，则新节点的输出是同一个 `F'` 的 evaluations。因为所有 `f_h` 都是 degree `d`，线性合成仍是 degree `d`；因为 `F'(0)=F(0)`，秘密不变；因为至少一个 honest helper 的高阶系数保持 fresh，新的 sharing 对未来未腐化节点独立于旧 sharing。

最关键的是：

```text
FGSR.Repair -> F'(j)
```

输出格式与正常 current share 完全相同。下一次 repair 重新把 `F'(j)` 作为 `f_j(0)` 输入即可，不需要保存 recovery polynomial、DPRF share 或 handoff-only metadata。这直接修复 VSSR 的 state-incomplete 问题。

### 23.7 当前仍需证明的边界

One-Shot FGSR 仍不是已完成协议，必须逐项验证：

1. `n=3f+2` 下，target 排除后仍能由 `2f+1` 个正确 helper 完成共同 `H`；
2. ACS/validated VSS 不会因 Byzantine helper 的不一致 proposal 让正确节点选择不同 `H`；
3. `E_ell=U_ell union B_ell` 覆盖所有可见 point/evaluation，且 affine coupling 能阻止线性层跨 generation 形成旧解密集合；
4. retirement 与已经启动的 resharing 并发时，旧 output 不能被安装或继续作为 helper input；
5. 已确认擦除集合 `A_ell` 的旧/当前缓存被擦除，未确认集合 `U_ell` 的残留状态完整进入 closure；
6. 若要把每个 coordinate 的 VSS resharing 从 `O(n^2)` 降低，需要额外的 packed/ batched proof，但这属于性能优化，不应先混入安全主定理。

线性 share-to-share 层已有一个跨代耦合候选：令 `E=U_ell union B_ell`，
`L_E(0)=1` 且 `L_E` 在 `E` 上为零。对每一代同时取
`F^r_Delta=F^r+Delta L_E` 和
`f^r_{h,Delta}=f^r_h+Delta L_E(h)L_E`；当 `|H_r|=degree(L_E)+1` 时，
Lagrange 合成仍满足同一递归，所有 `E` 上可见点值不变而秘密平移 `Delta`。
这关闭线性层的跨 generation 组合泄漏；剩余缺口是承诺/证明/信道模拟以及
aggregate-opening 的额外非线性能力边。

### 23.8 当前裁决

```text
Use DyCAPS ideas:     mobile resharing, verifiable polynomials, erasure
Do not copy:           four-phase handoff, bivariate state, epoch barrier
Core FGSR mechanism:   one-shot share-to-share resharing
Core proof object:     frontier-gated recovery closure
```

这条路线更贴合本文的实际研究问题：不是发明新的 proactive sharing，而是把已有 share-to-share resharing 改造成可选择退休、无序实例、可重复 repair 且可证明 transcript-final 的状态层。

## 24. FGSR v0.1：面向本文的协议流程

### 24.1 持久状态

每个 live coordinate `ell` 的持久状态只有：

```text
T_ell                 : 单调 frontier bit/version
z_ell,j = F_ell(j)    : 当前 direct share
C_ell                 : F_ell 的可验证 commitment
```

不持久保存 recovery polynomial、DPRF seed、旧 resharing polynomial 或可重放 backup。`rid` 只标识一次 repair，不构成全局 epoch；不同 coordinate 可以并发执行不同 `rid`。退休后，已确认擦除集合 `A_ell` 的节点只保留 frontier/commitment 元数据；尚未确认集合 `U_ell=P\A_ell` 的残留 direct/pending state 必须显式计入 recovery closure。

### 24.2 三道本文特有的门控

#### Gate 1: Authorize

target `i` 提交：

```text
Req = (rid, ell, target=i, T_req, C_ell).
```

异步 validated agreement 只在 `T_req[ell]=0` 且 `T_req` 不低于本地 frontier 时接受请求。ACS 先输出 `V`，随后所有节点按 descriptor 的确定性顺序取 `H=Canonical_{2f+1}(V)`，形成 **availability-certified helper set**：

```text
|H| = q_rec = 2f+1,
H excludes target,
each h in H has a valid current-share proof,
each h in H has AvailCert_h for the resharing instance.
```

`H` 的证书必须证明 helper 已经完成对应 VSS/AVSS 输入，而不是只证明它发送过一个 commitment。可用 `AvailCert_h` 表示：`P^-` 中至少 `2f+1` 个节点对同一 AVSS instance 签署 `READY(rid,ell,h,C_h)`，且 READY 只能在本地 deliver 认证点值后产生。底层 AVSS 还必须保证一个正确 receiver deliver 后所有正确 receiver 最终 deliver 同一点值。否则 Byzantine helper 可以被选入 `H` 后停止发送 subshares，导致 target 永久无法安装新 share。

#### Gate 2: Parallel Reshare

每个 `h in H` 选择 fresh degree-`d` polynomial：

```text
f_h(X) = z_ell,h + a_h,1 X + ... + a_h,d X^d,
```

并执行一次带承诺的异步 secret sharing。必须附带一个 zero-knowledge/equality proof，证明：

```text
f_h(0) = z_ell,h,
```

而不是仅证明 `f_h` 自身是合法多项式。每个 receiver `j` 收到唯一的 `f_h(j)`，不收到 `f_h` 的完整系数；subshare 绑定：

```text
(rid, ell, cfg, T_req, H, h, j, C_h).
```

#### Gate 3: Aggregate, Install, Erase

所有仍处于 live 状态的节点对相同 `H` 计算：

```text
z'_ell,j = sum_{h in H} lambda_h(H,0) * f_h(j).
```

新的 commitment 是：

```text
C'_ell = sum_{h in H} lambda_h(H,0) * C_h.
```

节点在验证全部 `H` 的 subshare 和同一 `C'_ell` 后安装 `z'_ell,j`。安装完成后擦除旧 `z_ell,j`、`f_h` 系数、plaintext subshares 和临时解密密钥。若在安装前 `T_ell` 提升到 retired，则该实例只能丢弃输出并擦除所有临时材料，不能把旧 output 安装回去。若 retirement 只被部分节点观察到，未确认节点可暂留 `z'_ell,j`；该残留状态归入 `X_current(U_ell)`，不得在闭包证明中假设其已经消失。

这三道门控不是 DyCAPS 四阶段的替代命名，而是为本文的 selective retirement 和 closure proof 服务的最小协议结构。

### 24.3 三个必要的并发规则

1. **每坐标实例序列化：** 同一 `ell` 的 repair 和 retirement 必须由 validated agreement 给出一致的 instance order；不同 `ell` 无需等待彼此。
2. **输出不可跨 frontier：** `T_req` 被退休证书支配时，所有 receiver 都拒绝安装，即使 `C'_ell` 和 VSS proof 完全有效。
3. **旧状态不可跨 commit：** 已确认擦除节点的未完成 repair 状态必须标记为 pending capability 并一并清除，不能只删除已经安装的 direct share；未确认节点的 pending state 保留在 `X_current(U_ell)` 中并受 closure 条件约束。

### 24.4 为什么它具备状态完备性

`z'_ell,j` 与正常 direct share 具有完全相同的格式。下一次 repair 只需令节点把 `z'_ell,j` 作为新多项式的常数项：

```text
f'_j(0) = z'_ell,j.
```

因此没有 VSSR 的“恢复后只有 `u_i[0]`、无法继续生成 recovery contribution”问题。状态完备性来自接口递归，而不是额外保存恢复元数据。

## 25. 朴素 FGSR 的失败模式与最小修正

### Failure A: 只恢复 target

若其他节点继续持有旧 `F`，target 安装 `F'(target)`，系统同时存在两个 sharing polynomial。下一次 repair 的 helper 输入无法确定统一的 secret-sharing state。故一次 FGSR 必须让所有仍持有 live coordinate 的正确节点最终切换到同一个 `F'`，即使只有一个 target 发起请求。

### Failure B: helper set 按本地收到顺序选择

不同 receiver 选择不同 `H` 会得到不同 `lambda_h` 和不同 sharing。修正是使用 availability-certified ACS，而不是“前 `q` 条消息”。

### Failure C: 没有证明常数项绑定

一个恶意 helper 可以提交合法的 `f_h`，但令 `f_h(0)` 不等于其旧 share；普通 polynomial validity 不能保证 secret 不变。修正是加入 `f_h(0)=z_h` 的公开可验证一致性证明，并将 `z_h` 的当前 commitment 纳入验证。

### Failure D: 把 private channel 当作 transcript deletion

私密传输只阻止旁观者即时读取，不阻止 receiver、helper 或未来暴露的密钥状态重放旧 subshare。修正是 ephemeral receiver key、plaintext/系数擦除和 frontier 绑定三者同时存在。

### Failure E: 只在 repair 开始时检查 frontier

retirement 可以与 repair 并发发生；开始时 live 不代表安装时仍 live。修正是 authorize、每个 subshare generation 和 install 三处都重新检查 frontier，并把 instance order 纳入 validated agreement。

## 26. 初步安全命题

### Proposition 1: One-Shot Resharing Correctness

若共同集合 `H` 的每个 `z_h` 是 `F` 的有效 evaluation，且每个 `f_h(0)=z_h`，则所有正确节点计算出的 `z'_j` 是同一个 degree-`d` polynomial `F'` 的 evaluation，并且：

```text
F'(0)=F(0).
```

若至少一个 honest helper 的高阶系数对攻击者未知且 fresh，则 `F'` 对未在该实例中获得足够信息的 adversary 重新随机化。

### Proposition 2: Target-Excluded Liveness

在 `n=3f+2`、至多 `f` 个 Byzantine withholding、target 为正确但缺失旧 share 时，仍有 `n-f-1=2f+1` 个其他正确节点。若 ACS 能从它们形成 availability-certified `H`，则 target 和其他正确节点最终都能完成 Gate 2/3，不等待 Byzantine helper。

这里的“若”是协议证明的核心，而不是计数自动推出的结论。`H` 的可用性证书
至少需要满足：

```text
H is unique for all correct nodes;
H excludes target;
each h in H has a valid current-share commitment;
each h in H has an AVSS-complete input that every correct receiver can obtain.
```

最后一项排除了“helper 已广播 commitment、但随后只对部分 receiver 发送
subshare”的 Byzantine proposal。一个可行的证明路线是：helper 先完成带
availability certificate 的 AVSS instance，再由 ACS 对 `(rid,ell,H)` 的确定性
集合达成一致；receiver 只处理该 instance 的 authenticated point。若采用的
AVSS 只保证 dealer 被确认而不保证所有正确 receiver 的可恢复性，则它不能直接
作为 FGSR 的 `H` 证书，必须增加可恢复性证明或改变集合选择规则。

因此 Proposition 2 应拆成两个引理：

1. **Agreement:** 所有正确节点接受同一个 `H`，且不会接受含 target 的集合；
2. **Availability:** 在 target 正确但缺失旧 share、至多 `f` 个其他节点
   withholding 时，至少 `2f+1` 个正确 helper 的 AVSS instances 最终完成，
   从而 ACS 能输出满足上面四项条件的 `H`。

只有第二个引理使用 `n=3f+2` 的 target-exclusion 计数；第一个引理属于
validated agreement/AVSS 组合安全，不能用普通 quorum 交集一句话替代。

### 26.1 一个可实例化的 Common-H wrapper

令 `P^- = P \ {target}`，则 `|P^-|=3f+1`。只让 `P^-` 中的节点作为 ACS
提案者，但每个 helper 的 AVSS receiver 仍包括 target。流程为：

```text
1. h starts AVSS[rid,ell,h] for f_h with equality proof f_h(0)=z_h.
2. h proposes desc_h only after AVSS[rid,ell,h] is complete locally.
3. validated ACS over P^- outputs V with |V|>=2f+1; all nodes set
   H=Canonical_{2f+1}(V).
4. every receiver obtains the AVSS point for every h in H.
```

ACS 的外部有效性只接受带有效旧-share commitment、equality proof 和 AVSS
completion certificate 的 `desc_h`；`H` 是对 `V` 的确定性截取，并绑定
`(rid,ell,cfg,T_req)`。由 ACS agreement，所有正确节点使用同一个 `H`；由
`|H|=2f+1` 且至多 `f` 个 Byzantine，`H` 至少含 `f+1` 个 honest helper。

`desc_h` 不得公开旧 share `z_h`。首个证明友好实例可用 Pedersen 系数承诺：
helper 对当前承诺在 `h` 处的 opening 与新承诺在 `0` 处的 opening 做零知识
消息相等证明；receiver 只验证承诺和收到的点值。若使用 KZG，则必须另给
zero-knowledge opening-equality proof，不能把普通 KZG opening proof 当作该
关系证明。

`H` 可以含 Byzantine helper，但这不破坏活性：AVSS 的 completion 语义必须保证
一个已完成 dealer instance 对所有正确 receiver 最终可恢复。若 Byzantine
helper 只发送 commitment、没有完成 AVSS，它不能产生有效 `desc_h`，因而不能
进入 `H`。因此目标不是通过身份判断“谁诚实”，而是通过 AVSS certificate
判断“哪一个输入已经可用”。

该 wrapper 的活性证明只需：全部 `2f+1` 个正确的非 target 节点最终完成其
AVSS；于是 ACS 的 `n'-f=2f+1` 终止条件满足。target 不参与 ACS 提案，不会因
缺失旧 share 阻塞集合选择，但作为 AVSS receiver 接收最终的 `f_h(target)`。
这给出比“前 `q` 条消息”更精确的 liveness 条件，也明确了 FGSR 对底层 AVSS
接口的真实依赖。

### Proposition 3: Retired-Coordinate Closure (Target Form)

若 `ell` 的 retirement certificate 在 repair instance 的 install 前生效，且：

```text
all generation checks use T_req,
all pending plaintext/key state is erased,
all archived subshares require erased ephemeral receiver keys,
```

则该实例不会为 retired `ell` 生成新的可安装 direct capability。若退休前历史能力低于 `q_rec`，且旧 transcript 不可展开为额外 `F_ell(j)`，则 `Cl_rec` 在 `C_dec(ell)` 上不扩张。

Proposition 3 仍是条件命题；其正式证明需要把 VSS/AVSS transcript simulator、擦除假设和 `Composable Edge Realizability` 接入既有 Repair-Closure Theorem。

### Proposition 4: Cross-Coordinate Affine Coupling (Candidate)

设 BF-RPTA 的 coordinate 集合为 `I`。对每个 `ell in I`，第 `r` 代的 sharing
polynomial 为 `F^r_ell`，degree 为 `d_ell`，所有可见 positions 包含在
`E_ell` 中，且 `|E_ell|<=d_ell`。若每个 helper set `H_{r,ell}` 含
`d_ell+1` 个点，并满足：

```text
F^{r+1}_ell(X) = sum_{h in H_{r,ell}}
                    lambda_{r,ell,h} f^r_{ell,h}(X),
f^r_{ell,h}(0) = F^r_ell(h),
```

定义：

```text
L_ell(X) = product_{j in E_ell}(X-j) / product_{j in E_ell}(-j),
F^r_{ell,Delta}(X) = F^r_ell(X) + Delta*L_ell(X),
f^r_{ell,h,Delta}(X) = f^r_{ell,h}(X)
                         + Delta*L_ell(h)*L_ell(X).
```

则对任意同一个 `Delta`：

1. 所有 `E_ell` 上的 direct share 与 subshare point 不变；
2. 每个 helper 的 equality relation 保持；
3. 因 `L_ell(0)=1` 且 `degree(L_ell)<=d_ell`，每个 coordinate 的 resharing
   recursion 保持；
4. 若各 coordinate 编码同一个 mask key，所有 coordinate 的秘密同时平移
   `Delta`，所以该一致性关系保持。

该命题是 `Cross-Generation Affine Coupling` 的多坐标版本。它只证明线性
share-to-share transcript 存在同一个未知视图自由度，不证明 `Static-AO` 的
aggregate-opening 游戏安全。后者还要求跨坐标 consistency proof 是 zero
knowledge 且不产生 share opening，并单独证明：

```text
partial shares across coordinates + public relation proof
    -/-> new aggregate-opening capability.
```

共享高阶系数、公开跨坐标 opening 或 packed coordinates 暂不属于该命题的接口；
任何一种都必须重新计算 residual exposure set 与 `Gamma_dec^cap`。

## 27. 成本与主创新边界

朴素 FGSR 对一个 coordinate 需要每个 helper 向每个 receiver 分发一次 VSS subshare，通信通常为 `O(n^2)`，并且 repair 会刷新该 coordinate 的所有 current shares。这是有意识的安全基线，不是最终性能宣称。

可后续优化但不提前混入主定理的方向只有：

1. 用 packed AVSS 同时处理多个 live coordinates；
2. 批量证明多个 `f_h(0)=z_h` 一致性；
3. 让 ACS 复用多个 repair instance 的可用性证书。

这些优化不能改变三条安全不变量：共同 `H`、state-complete `F'`、frontier-gated extraction/install。论文第一版应先证明安全闭环，再比较 packed/batched 实现的通信。
