# 实验目录

当前实现以本文协议内核为入口，真实组件核验作为接入依据：

| 路径 | 用途 |
|---|---|
| `reconfigurable_async_fl.py` | 本文协议内核：加权聚合、按实例延续、开启与提交分离、模型应用及累计暴露观察 |
| `check_our_protocol.py` | 双实例与新训练并行轨迹、乱序和故障检查、数值对照及事件重放 |
| `OUR_PROTOCOL_IMPLEMENTATION.md` | 本文方案实现计划、进展、验证依据与真实组件接入边界 |
| `upstream/dycaps` | DyCAPS 原始仓库，只读参考与交接基准 |
| `upstream/optimistic-dpss` | Optimistic DPSS 原始仓库，只读参考与恢复基准 |
| `upstream/buffalo` | Buffalo 原始仓库，含 RLWE、Olympia 及 FLSim 代码 |
| `run_dycaps_handoff.py`、`dycaps_handoff_test.go` | 原组退出后，后继执行真实交接并延续系数聚合 |
| `check_departure_recovery.py` | 发送进程结束后的交接载荷和聚合恢复检查 |
| `check_abstract_protocol.py` | 实例状态、交接顺序和结果封存检查 |
| `REAL_COMPONENT_BRINGUP.md` | 当前真实组件接入记录 |
| `verification/` | 上游原生运行核验脚本与逐项目报告 |
| `results/upstream-verification/` | 原生运行日志、环境记录和检查结果 |
| `archive/legacy-design` | 旧实验构建稿和旧基线计划 |

上游仓库保持原样。适配器、轨迹和测量脚本放在本目录，不直接修改上游代码。

运行 `python3 experiments/check_our_protocol.py` 检验本文协议规则。数值结果与轨迹写入 `experiments/results/our-protocol/`。首版使用理想认证事件和抽象阈值后端，提供精确数值的聚合与模型轨迹对照。

从项目根目录执行 `python3 experiments/run_dycaps_handoff.py`。原始日志和公开检查结果写入 `experiments/results/dycaps-handoff/`；私密交接输入存放在临时目录并在运行后移除。
