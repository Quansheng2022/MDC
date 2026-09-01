# QCFP-MTF 2.1.1 开发计划（基于 TA_Workflow 现有数据底座）

> 版本：v0.1（评审稿）
> 日期：2026-08-19
> 依据：《QCFP-MTF 2.1.1 架构设计.md》（已冻结）
> 目标：在 TA_Workflow 现有 SQLite 原始数据之上，落地「季度筹码-资金-价格 三维多时间周期框架」分析系统

---

## 一、结论速览

### 1.1 新系统目录位置

**建议：放在 `PROJECT ROOT\Core\QCFP_MTF`（下划线），完全合适。**

理由：

1. 该框架是跨周期系统（季度结构 + 月线阶段 + 周线触发），不属于现有 `Core/Daily`、`Core/Weekly`、`Core/Monthly`、`Core/Quarterly` 中任何单一周期，独立成目录符合"单步单职责 + 周期×步骤"的项目结构；
2. 沿用项目四层组织：入口脚本放根目录（`run_QCFP_MTF_workflow.py`），业务脚本放 `Core/QCFP_MTF`，共享工具继续收口在 `Core/utl`，配置放 `Config`，产物写 `Report/Prompt/Log/Temp`；
3. 目录名建议用下划线 `QCFP_MTF` 而非连字符 `QCFP-MTF`：Windows 文件夹两者皆可，但 Python 包导入（`from QCFP_MTF.structural import ...`）不支持连字符；对外文档、入口脚本名、`model_version`（`QCFP-MTF-2.1.1`）仍保留连字符标识。

### 1.2 数据底座审计结论（2026-08-19 实测）

| 数据表 | 行数 | 股票数 | 时间范围 | 结论 |
| :--- | :--- | :--- | :--- | :--- |
| `hk_hist_daily_kline` | 46,312 | 15 | 2010-01-04 ~ 2026-08-19 | 完整，turnover/amount/volume 无缺失 |
| `hk_hist_daily_moneyflow` | 19,876 | 15 | 2021-02-03 ~ 2026-08-19 | 仅 2021 起 |
| `hk_idx_hist` | 2,860 | — | 2015-01-02 ~ 2026-08-19 | 大盘环境/回测分层可用 |
| `hk_hist_institutional_holdings` | 944 | 14 | 2004/Q1 ~ 2026/Q2 | A 级筹码唯一来源，14 只 |
| `hk_hist_weekly_kline` | 9,827 | 15 | 2010-01-08 ~ 2026-08-14 | 完整 |
| `hk_hist_weekly_moneyflow` | 4,229 | 15 | 2021-02-05 ~ 2026-08-14 | 仅 2021 起 |
| `hk_hist_monthly_kline` | 2,267 | 15 | 2010-01-31 ~ 2026-07-31 | 完整（close 有 7 条缺失） |
| `hk_hist_monthly_moneyflow` | 1,000 | 15 | 2021-02-01 ~ 2026-07-31 | 仅 2021 起 |
| `hk_hist_quarterly_kline` | 752 | 15 | 2010-03-31 ~ 2026-06-30 | 完整 |
| `hk_hist_quarterly_moneyflow` | 324 | 15 | 2021-03-31 ~ 2026-06-30 | 仅 2021 起 |

**关键发现**：

1. `stock_list.json` 含 17 只，但日/周/月/季 K 线仅 15 只（缺 `00579`、`02602`）；机构持股仅 14 只（`03033` ETF 无机构数据）。计划中按"缺失即降级"处理；
2. 已有季度分析表 `hk_quarterly_institutional_holdings_analysis`、`hk_quarterly_chip_analysis`（由 `Core/Quarterly` TA4C/TA4D 产出）已实现 QCFP 1.x 的 C/F/P 方向、背离与 Regime，**新系统应作为 L2 事实层直接复用，不重复造轮子**；
3. 规格书要求的 `available_date`（机构持股真实披露日）目前表内没有，只有 `period_text`（`2026/Q2`）与 `update_time`——这是必须解决的数据缺口，见 §8；
4. 资金流表只有大/中/小单与资金趋势，机构/散户净流入需沿用现有 IDR/FBI 派生逻辑（`hk_quarterly_chip_analysis` 已有 `institutional_flow`/`individual_flow`/`idr`/`fbi`）。

---

## 二、与现有系统的关系（复用清单）

| 能力 | 现有资产 | 新系统用法 |
| :--- | :--- | :--- |
| 配置/路径 | `Core/utl/stock_analysis_utl.py`、`GlobalConfig` | 直接复用 |
| 股票列表 | `Core/utl/stock_list_loader.py` + `Config/stock_list.json` | 直接复用 |
| 季度筹码事实 | `hk_quarterly_institutional_holdings_analysis`（qoq/yoy/4q 变化、迁移、集中度） | L2 Fact 输入 |
| 季度 C/F/P 联合 | `hk_quarterly_chip_analysis`（chip_direction/flow_direction/price_direction、Regime、integrated_score） | 校验基准 + 部分因子来源 |
| 资金流派生 | `hk_*_moneyflow_analysis`（institutional_flow/individual_flow/idr/fbi） | F 因子输入 |
| 数据字典 | `Config/*_dictionary.*` 全套生成脚本 `Code_utl/Generate_*_Dictionary.py` | 新表沿用同规范 |
| 报告/日志 | `Report/`、`Log/`、reportlab + Windows 中文字体 | 沿用 |

**边界约定**：

- 新系统只读现有 hist/analysis 表，不改写；写 `qcfp_*` 新表；
- 入口 `run_QCFP_MTF_workflow.py` 启动时校验前置表是否有数据，缺失则提示先运行 `run_Quarterly_TA_workflow.py` 与 `run_Daily_TA_workflow.py`；
- 新系统与 `Core/Quarterly` 的关系：Quarterly 是"季度单周期分析"，QCFP_MTF 是"季度定结构 + 月线定阶段 + 周线定时机的跨周期决策系统"，两者并存、互不覆盖。

---

## 三、目录结构（落地版）

```text
TA_Workflow/
├── run_QCFP_MTF_workflow.py            # 入口编排（仿 run_Quarterly_TA_workflow.py）
├── Core/
│   └── QCFP_MTF/                       # 新系统（下划线目录名）
│       ├── common/                     # 共享：logger、sqlite 读写、日期、标准化工具
│       ├── config/                     # qcfp_settings.yaml（权重/阈值/开关，可回测校准）
│       ├── data/                       # 数据加载与质量
│       │   ├── loader.py               # 从现有表加载并标准化
│       │   ├── quality.py              # data_quality A/B/C/D
│       │   └── evidence.py             # 证据等级 A/A-/B/C/D 静态映射 + 动态判定
│       ├── structural/                 # P1 季度结构引擎（Layer 1）
│       │   ├── chip_factors.py         # C 因子（复用机构持股分析表）
│       │   ├── flow_factors.py         # F 因子（复用资金流分析 + IFA Z-Score）
│       │   ├── price_factors.py        # P 因子（季度收益/Trend Score/52W 位置）
│       │   ├── structural_regime.py    # FSM-1（6 状态 + Core Score）
│       │   └── divergence.py           # CPD/FPD/CFD 背离
│       ├── behavioral/                 # P2 月线行为引擎（Layer 2）
│       │   ├── turnover_factors.py     # 换手 Z-Score/百分位/T1~T5
│       │   ├── volume_factors.py       # 量加速度/量比
│       │   ├── vp_matrix.py            # 9 种 VP_Regime
│       │   ├── cbi.py                  # CBI（Winsorize→Z→0~100→加权）
│       │   ├── cost_position.py        # 周/月/季 VWAP 成本位置
│       │   └── monthly_stage.py        # Improving/Stable/Deteriorating
│       ├── tactical/                   # P3 周线战术引擎（Layer 3）
│       │   ├── weekly_volume.py        # 放量/缩量检测
│       │   ├── weekly_turnover.py      # 换手偏离/极端换手
│       │   ├── weekly_vwap.py          # 周 VWAP 偏离
│       │   └── weekly_signal.py        # Breakout/Pullback/Consolidation/Breakdown
│       ├── fusion/                     # P4 多周期融合层（Layer 4）
│       │   ├── chip_confidence.py      # Chip Stability Confidence（60/40 可配置）
│       │   ├── mtf_alignment.py        # 硬编码对齐矩阵（12 条映射）
│       │   ├── mtf_fsm.py              # FSM-2（5 状态转换）
│       │   └── anti_inference.py       # 禁止推断过滤器
│       ├── decision/                   # P5 DSS 决策层（Layer 5）
│       │   ├── score_calculator.py     # State-First 评分
│       │   ├── action_generator.py     # 单向门控 Action
│       │   ├── risk_evaluator.py       # 风险等级
│       │   ├── dss_output.py           # JSON 协议
│       │   └── report_generator.py     # 个股 PDF/Markdown 报告
│       ├── backtest/                   # P6 回测与校准
│       │   ├── lookahead_filter.py     # available_date 防偏
│       │   ├── engine.py               # 回测引擎（pandas 向量化先行）
│       │   ├── cost_model.py           # 港股费用模型
│       │   ├── performance.py          # 绩效评估
│       │   ├── calibration.py          # 参数寻优
│       │   └── robustness.py           # 牛熊/震荡分层验证
│       └── tests/                      # 单元/集成测试（与模块一一对应）
└── Config/
    ├── qcfp_settings.yaml              # 新系统配置（权重、阈值、开关）
    └── qcfp_*_dictionary.json/md/xlsx  # 新表数据字典（沿用生成脚本）
```

> 注：规格书建议 PostgreSQL + YAML + Loguru + VectorBT；本项目落地时**保持 SQLite + INI/YAML + 项目自有日志/报告体系**，回测先用 pandas 向量化实现，性能不足再引入 VectorBT。此差异属于"工程实现适配"，不改变架构。

---

## 四、数据库新增表设计（`SQLiteDB/HK_Stock.db`）

按规格书建 5 张表，均加 `model_version`、`data_quality`、`update_time`，索引 `(stock_code, 周期末日期)` 唯一：

| 表 | 关键字段 | 数据来源映射 |
| :--- | :--- | :--- |
| `qcfp_quarterly_structural` | period_end、available_date、inst_ownership_pct_chg、holder_quantity_chg_pct、inst_participation_chg、q_inst_flow_raw、q_inst_flow_z、q_ifa_zscore、q_return、q_trend_score、q_position_52w、c_state/f_state/p_state、structural_regime、core_score | holder_pct_qoq_pp、holder_quantity_qoq_pct、institution_quantity_qoq_pct（来自 `hk_quarterly_institutional_holdings_analysis`）；institutional_flow/idr/fbi（来自 `hk_quarterly_chip_analysis`）；close/change_percent（来自 `hk_hist_quarterly_kline`） |
| `qcfp_monthly_behavior` | month_end、m_turnover_zscore、m_turnover_pctl、m_turnover_ma_ratio、m_volume_ma_ratio、m_volume_accel、m_vwap_deviation、m_vp_regime、turnover_liquidity_regime、monthly_behavior_state | `hk_hist_monthly_kline`（turnover_rate/volume/amount/amplitude/close） |
| `qcfp_weekly_tactical` | week_end、w_turnover_deviation、w_turnover_spike、w_volume_breakout、w_vwap_deviation、w_ma_slope、w_breakout、w_breakdown、tactical_signal | `hk_hist_weekly_kline` |
| `qcfp_mtf_decision` | decision_date、structural_regime、monthly_behavior_state、tactical_signal、cbi_score、cost_position、chip_stability_confidence、mtf_regime、qcfp_score、action_signal、risk_level、market_context | 三层引擎输出 + `hk_idx_hist`（HSI/HSTECH/VHSI/SouthboundFlow 派生大盘环境） |
| `qcfp_backtest_results` | stock_code、signal_date、action、position、pnl、market_regime 等 | 回测引擎输出 |

**实现约定**：

- 新增表必须同步生成数据字典（`Code_utl/Generate_*_Dictionary.py` 模板）；
- `period_end`/`month_end`/`week_end` 采用 `YYYY-MM-DD`；
- 机构持股无真实披露日时，`available_date` 先采用「季度末 + 固定披露滞后天数」配置化推算（默认 45 天），并在 `data_quality` 中降级为 B/C，同时在字典与报告中明确标注"推算值"。

---

## 五、开发阶段计划（P0 ~ P6）

### P0：基础设施与数据层（约 4~5 天）

| # | 任务 | 子模块 | 输入/产出 | 验收 |
| :--- | :--- | :--- | :--- | :--- |
| 0.1 | 建目录与入口脚本 | `Core/QCFP_MTF/` + `run_QCFP_MTF_workflow.py` | 目录结构 + 编排脚本 | 可顺序执行空流程 |
| 0.2 | 建 5 张 `qcfp_*` 表 + 索引 | SQL 脚本（沿用 `create_hk_stock_info.sql` 风格） | `HK_Stock.db` 新增表 | `SELECT` 正常 |
| 0.3 | 配置管理 | `Config/qcfp_settings.yaml` + 写入 `stock_data_analysis.par` 的 `[QCFP_MTF]` 节 | 权重/阈值/开关可读 | 配置热更新 |
| 0.4 | 数据加载器 | `data/loader.py` | 现有 10 张 hist/analysis 表 → 标准化 DataFrame | 单股全周期数据可加载 |
| 0.5 | 数据质量检测 | `data/quality.py` | A/B/C/D 标签 | 全部股票可出标签 |
| 0.6 | 证据等级标注 | `data/evidence.py` | 因子 → A/A-/B/C/D | 静态表 + 动态判定 |
| 0.7 | 港股日历与周期对齐 | `common/calendar.py` | 日→周→月→季切分对齐 | 周期边界正确 |
| 0.8 | 覆盖度审计脚本 | `scripts/audit_coverage.py` | 每股票×每表覆盖报告 | 输出缺口清单 |

**里程碑 M0**：任意股票可输出 `data_quality` 标签 + 覆盖度报告。

### P1：季度结构引擎（约 5~6 天）

> P1 详细计划见 [QCFP-MTF_P1_开发计划.md](QCFP-MTF_P1_开发计划.md)。

| # | 任务 | 子模块 | 说明 |
| :--- | :--- | :--- | :--- |
| 1.1 | C 因子 | `structural/chip_factors.py` | `inst_ownership_pct_chg`、`holder_quantity_chg_pct`、`inst_participation_chg` → `c_state`（阈值可配置） |
| 1.2 | F 因子 | `structural/flow_factors.py` | 季度资金流聚合 + IFA Z-Score → `f_state` |
| 1.3 | P 因子 | `structural/price_factors.py` | 季度收益、Trend Score（季末快照窗口）、52W 位置 → `p_state` |
| 1.4 | FSM-1 | `structural/structural_regime.py` | C/F/P → 6 状态 + Core Score（State-First） |
| 1.5 | 背离检测 | `structural/divergence.py` | CPD/FPD/CFD Z-Score 偏离 |
| 1.6 | 单元测试 | `tests/test_structural/` | 状态转换全覆盖，含 8 条规格书转换规则 |

**里程碑 M1**：输入任意股票，输出 `structural_regime` + `core_score` + 背离信号，并与 `hk_quarterly_chip_analysis.chip_flow_price_regime` 交叉验证一致性。

### P2：月线行为引擎（约 5~6 天）

| # | 任务 | 子模块 | 说明 |
| :--- | :--- | :--- | :--- |
| 2.1 | 换手因子 | `behavioral/turnover_factors.py` | 月换手 Z-Score/52W 百分位/MA6 比值 → T1~T5 |
| 2.2 | 量因子 | `behavioral/volume_factors.py` | 量加速度、量比 |
| 2.3 | 量价矩阵 | `behavioral/vp_matrix.py` | 9 种 VP_Regime（含 `VP_STABLE_ASCENT`） |
| 2.4 | CBI | `behavioral/cbi.py` | **严格** Winsorize(1%~99%)→Z-Score→0~100→加权（30/30/25/15，权重可配置） |
| 2.5 | Cost Position | `behavioral/cost_position.py` | 周/月/季 VWAP（amount/volume）偏离 + 三周期综合 |
| 2.6 | 月线阶段 | `behavioral/monthly_stage.py` | Improving/Stable/Deteriorating |
| 2.7 | 单元测试 | `tests/test_behavioral/` | CBI 标准化、VWAP 剥离、Stage 判定 |

**里程碑 M2**：输出 `CBI_Score`、`Cost_Position`、`Monthly_Stage`。

### P3：周线战术引擎（约 3 天）

| # | 任务 | 子模块 | 说明 |
| :--- | :--- | :--- | :--- |
| 3.1 | 周量检测 | `tactical/weekly_volume.py` | 放量突破（>MA20×1.8）/ 极度缩量（<MA20×0.5） |
| 3.2 | 周换手检测 | `tactical/weekly_turnover.py` | 偏离度 vs 季度周均、极端换手（>MA8×2.0） |
| 3.3 | 周 VWAP | `tactical/weekly_vwap.py` | close/VWAP_W−1 |
| 3.4 | 均线结构 | `tactical/weekly_signal.py` | 5/10/20 周 MA 斜率（二阶差分） |
| 3.5 | 信号合成 | `tactical/weekly_signal.py` | Breakout/Pullback/Consolidation/Breakdown |
| 3.6 | 单元测试 | `tests/test_tactical/` | 阈值与信号合成，防误触发 |

**里程碑 M3**：输出 `tactical_signal` + `w_breakout`/`w_breakdown` 布尔标记。

### P4：多周期融合层（约 4~5 天）

| # | 任务 | 子模块 | 说明 |
| :--- | :--- | :--- | :--- |
| 4.1 | 筹码稳定置信度 | `fusion/chip_confidence.py` | 60%×Quarterly_Chip_Score + 40%×CBI_Normalized（权重可配置）→ High/Medium/Low |
| 4.2 | 多周期对齐 | `fusion/mtf_alignment.py` | 规格书 12 条映射矩阵硬编码实现（含"禁止越权"两铁律） |
| 4.3 | FSM-2 | `fusion/mtf_fsm.py` | State(t)+Event(t)→State(t+1) |
| 4.4 | 禁止推断过滤 | `fusion/anti_inference.py` | 规则表驱动：扫描结论文本，触发即降级为允许表述（先用"警告+降级"模式） |
| 4.5 | 结构-行为背离 | `fusion/mtf_alignment.py` | 季度强势+月线恶化 / 季度弱势+月线改善 → 背离标记 |
| 4.6 | 集成测试 | `tests/test_fusion/` | 三层输入 → MTF Regime → 置信度 → 防推断全链路 |

**里程碑 M4**：输出 `mtf_regime` + `chip_stability_confidence`，两铁律用例（STRUCTURAL_BULLISH+Breakdown→BULLISH_WARNING 等）全部通过。

### P5：DSS 决策层（约 3~4 天）

| # | 任务 | 子模块 | 说明 |
| :--- | :--- | :--- | :--- |
| 5.1 | 评分 | `decision/score_calculator.py` | State-First：由 MTF Regime 映射 0~100 分 |
| 5.2 | Action | `decision/action_generator.py` | BUY/ADD/HOLD/REDUCE/EXIT/WAIT，单向门控（DECLINE/DISTRIBUTION 禁止 BUY/ADD；BULLISH 下 Breakdown 只给 REDUCE/HOLD） |
| 5.3 | 风险 | `decision/risk_evaluator.py` | Low/Medium/High/Extreme（背离 + 状态位置 + 数据质量） |
| 5.4 | DSS 输出 | `decision/dss_output.py` | 与规格书第七章 JSON 协议一致（含 evidence_summary、anti_inference_check、stop_loss_trigger） |
| 5.5 | 报告 | `decision/report_generator.py` | JSON → 个股 Markdown/PDF（沿用 reportlab + 中文字体方案） |
| 5.6 | 端到端测试 | `tests/test_e2e.py` | 单股全流程 |

**里程碑 M5**：输入股票代码+日期 → 完整 DSS JSON + 可读报告。

### P6：回测与校准（约 5~6 天）

| # | 任务 | 子模块 | 说明 |
| :--- | :--- | :--- | :--- |
| 6.1 | 防 Look-ahead | `backtest/lookahead_filter.py` | 强制按 `available_date` 切片，`period_end` 仅作展示 |
| 6.2 | 回测引擎 | `backtest/engine.py` | pandas 向量化回测（先实现），港股成本模型（佣金+滑点+印花税） |
| 6.3 | 绩效评估 | `backtest/performance.py` | 年化、夏普、最大回撤、胜率、盈亏比、分年度 |
| 6.4 | 扩展窗口交叉验证 | `backtest/calibration.py` | Expanding Window，避免全历史单次优化过拟合 |
| 6.5 | 参数校准 | `backtest/calibration.py` | CBI 权重、Chip Confidence 权重、Z-Score/百分位阈值网格搜索，回写 `qcfp_settings.yaml` |
| 6.6 | 稳健性 | `backtest/robustness.py` | 用 `hk_idx_hist`（HSI 趋势/波动）划分牛/熊/震荡环境分别回测 |
| 6.7 | 回测报告 | `Report/QCFP_MTF/backtest/` | 收益曲线、状态分布、参数敏感性 |

**里程碑 M6**：任意历史区间无偏回测 + 校准参数回写。

---

## 六、关键实现决策

1. **层级不可越权（最高宪法）**：在 `fusion/mtf_alignment.py` 用规格书 12 条映射矩阵 + 显式"禁止输出"断言实现，不允许用加权打分替代状态映射；
2. **State-First, Score-Second**：`score_calculator` 只做"状态→分数"查表，任何地方不得"先算分再推状态"；
3. **证据等级与数据质量双门禁**：任一关键因子为 D 级时该周期不产生决策信号，仅输出 `DATA_INSUFFICIENT`；
4. **Anti-Inference 先"警告+降级"后"阻断"**：初期不直接阻断输出，记录违规案例，积累后再收紧；
5. **权重与阈值全部配置化**：进 `qcfp_settings.yaml`，默认用规格书值，P6 回测校准后回写；
6. **复用优先**：能读现有分析表就不重算，重算时必须与现有表交叉验证（如季度 Regime 与 `hk_quarterly_chip_analysis` 对比）；
7. **版本可复现**：每张结果表带 `model_version`，运行日志记录 `qcfp_settings.yaml` 内容快照。

---

## 七、数据缺口与风险清单

| # | 缺口/风险 | 影响 | 应对 |
| :--- | :--- | :--- | :--- |
| 1 | 机构持股无真实披露日（`available_date` 缺失） | 回测存在 Look-ahead 风险 | 配置化披露滞后天数推算 + `data_quality` 降级标注；后续补充披露日历 |
| 2 | 资金流数据仅 2021 年起 | 季度 F 因子历史长度不足 | 回测区间以 2021 起为准；更早区间仅用 C/P 并标注数据质量 |
| 3 | `03033`（ETF）无机构持股；`00579`、`02602` 无行情 | 覆盖不全 | 覆盖度审计自动降级，ETF 可配置排除出结构引擎 |
| 4 | 月线 close 有 7 条缺失 | CBI/成本位置轻微失真 | 缺失月份剔除/前值填充，标注 B 级 |
| 5 | 机构/散户资金流为派生值（IDR/FBI），非原始拆分 | F 因子属 A-/B 级证据 | 证据等级按派生来源标注，报告中注明 |
| 6 | 换手率口径（自由流通股本变化） | 长期 T 状态可比性 | 使用分位数与 Z-Score 缓释，不做绝对阈值 |
| 7 | Anti-Inference 规则文本匹配 | 报告生成质量 | 规则表 JSON 化，先警告后阻断，迭代案例库 |
| 8 | 回测参数过拟合 | 校准失真 | 扩展窗口交叉验证 + 牛熊/震荡分层稳健性测试 |

---

## 八、里程碑与工时汇总

| 阶段 | 内容 | 预计工时（人天） |
| :--- | :--- | :--- |
| P0 | 基础设施与数据层 | 4~5 |
| P1 | 季度结构引擎 | 5~6 |
| P2 | 月线行为引擎 | 5~6 |
| P3 | 周线战术引擎 | 3 |
| P4 | 多周期融合层 | 4~5 |
| P5 | DSS 决策层 | 3~4 |
| P6 | 回测与校准 | 5~6 |
| **合计** | | **约 29~35 人天（约 6~7 周，1 人全职）** |

> 相比规格书 54 人天，因直接复用现有季度分析表、utl 与字典体系，预计节省约 1/3 工时。

---

## 九、测试策略

- 单元测试：每个模块 1 个测试文件，`tests/` 与模块目录一一对应；
- 关键断言用例（必须覆盖）：
  - `STRUCTURAL_BULLISH + Breakdown → BULLISH_WARNING`（严禁 BEARISH_CONFIRMED）；
  - `STRUCTURAL_DECLINE + Breakout → BEARISH_RECOVERY_CANDIDATE`（严禁 BULLISH_CONFIRMED）；
  - `data_quality = D → 无决策信号`；
  - CBI 标准化流程（Winsorize 边界、0~100 域）；
  - Anti-Inference 表全规则回归；
  - 回测 look-ahead 检测（人为注入未来数据应被拦截）。
- 集成测试：P4 与 P5 各一次端到端；P6 结束后全量回归。

---

## 十、下一步行动（建议顺序）

1. 确认目录方案（`Core/QCFP_MTF`）与本计划；
2. 启动 P0：建目录、建表、写数据加载器与覆盖度审计脚本（产出 M0）；
3. 并行调研：确认机构持股披露日历 / 补 `available_date` 的数据源（Longbridge/CCASS 备选）；
4. P1~P3 按依赖顺序推进，每阶段完成即跑测试与里程碑验证；
5. 全部阶段完成后，输出首份个股 QCFP-MTF 报告并进入回测校准。

---

## 附：P0 交付记录（2026-08-19）

| 计划任务 | 状态 | 交付物 |
| :--- | :--- | :--- |
| 0.1 建目录与入口脚本 | ✅ | `Core/QCFP_MTF/`（common/config/data/structural/behavioral/tactical/fusion/decision/backtest/scripts/tests/sql）+ `run_QCFP_MTF_workflow.py` |
| 0.2 建 5 张表 + 索引 | ✅ | `sql/create_qcfp_tables.sql`，6 张 `qcfp_*` 表已建入 `SQLiteDB/HK_Stock.db`（含审计快照表） |
| 0.3 配置管理 | ✅ | `Config/qcfp_settings.yaml` + `stock_data_analysis.par [QCFP_MTF]` 节 + `config/settings.py`（含无 PyYAML 兜底解析） |
| 0.4 数据加载器 | ✅ | `data/loader.py`（10 张源表 + 2 张季度派生表，统一 5 位代码/日期标准化） |
| 0.5 数据质量检测 | ✅ | `data/quality.py` + `scripts/check_data_quality.py`，写 `qcfp_data_quality_audit` 快照 |
| 0.6 证据等级标注 | ✅ | `data/evidence.py`（A/A-/B/C/D 静态表 + 派生降级规则） |
| 0.7 港股日历与周期对齐 | ✅ | `common/calendar.py`（交易日序列 + 周/月/季切分） |
| 0.8 覆盖度审计 | ✅ | `scripts/audit_coverage.py`，输出 `Report/QCFP_MTF/audit/coverage_report_*.{csv,json}` |
| 数据字典同步 | ✅ | `Code_utl/Generate_qcfp_Dictionaries.py`，6 表 × {json,md,xlsx} 已生成至 `Config/` |
| 测试 | ✅ | `tests/` 36 项全部通过（含无 pytest 的运行器 `run_all_tests.py`） |

> P0 验收细则见 [QCFP-MTF_P0_测试清单.md](QCFP-MTF_P0_测试清单.md)（A~G 逐项打勾）。

**P1（季度结构引擎）已交付（2026-08-19）**：C/F/P 因子 + FSM-1 + Core Score + 三维背离，`qcfp_quarterly_structural` 944 行；交叉验证 direct 一致率 90%；60 项测试全过。详见 [QCFP-MTF_P1_开发计划.md](QCFP-MTF_P1_开发计划.md) 交付记录。

> P1 验收细则见 [QCFP-MTF_P1_测试清单.md](QCFP-MTF_P1_测试清单.md)；使用实例见 [QCFP-MTF_P1_使用手册.md](QCFP-MTF_P1_使用手册.md)。

**P2（月线行为引擎）已交付（2026-08-19）**：T1~T5 + 9 种 VP_Regime + CBI + Cost Position + Stage，`qcfp_monthly_behavior` 2267 行；81 项测试全过；工作流 6 步端到端 ✅。详见 [QCFP-MTF_P2_开发计划.md](QCFP-MTF_P2_开发计划.md) 交付记录；验收细则见 [QCFP-MTF_P2_测试清单.md](QCFP-MTF_P2_测试清单.md)；使用实例见 [QCFP-MTF_P2_使用手册.md](QCFP-MTF_P2_使用手册.md)。

**P3（周线战术引擎）已交付（2026-08-19）**：放量/缩量 + 换手偏离/极端 + VWAP 偏离 + 均线斜率 + 4 种信号，`qcfp_weekly_tactical` 9827 行；97 项测试全过；工作流 7 步端到端 ✅。详见 [QCFP-MTF_P3_开发计划.md](QCFP-MTF_P3_开发计划.md) 交付记录；验收细则见 [QCFP-MTF_P3_测试清单.md](QCFP-MTF_P3_测试清单.md)；使用实例见 [QCFP-MTF_P3_使用手册.md](QCFP-MTF_P3_使用手册.md)。

**P4（多周期融合层）已交付（2026-08-19）**：Chip Confidence + MTF 对齐（12 矩阵+兜底）+ FSM-2 + Anti-Inference + 结构-行为背离，`qcfp_mtf_decision` 9827 行；全量不越权验证 0 违规；118 项测试全过；工作流 8 步端到端 ✅。详见 [QCFP-MTF_P4_开发计划.md](QCFP-MTF_P4_开发计划.md) 交付记录；验收细则见 [QCFP-MTF_P4_测试清单.md](QCFP-MTF_P4_测试清单.md)；使用实例见 [QCFP-MTF_P4_使用手册.md](QCFP-MTF_P4_使用手册.md)。

**P5（DSS 决策层）已交付（2026-08-20）**：Score + Action（单向门控）+ Risk + 标准 JSON/MD 报告，`qcfp_mtf_decision` 9827 行全部回写 action/risk；全量门控验证 0 违规；133 项测试全过；工作流 9 步端到端 ✅。详见 [QCFP-MTF_P5_开发计划.md](QCFP-MTF_P5_开发计划.md) 交付记录；验收细则见 [QCFP-MTF_P5_测试清单.md](QCFP-MTF_P5_测试清单.md)；使用实例见 [QCFP-MTF_P5_使用手册.md](QCFP-MTF_P5_使用手册.md)。

**P6（回测与校准）已交付（2026-08-20）**：防 Look-ahead 时间线 + 向量化回测 + 绩效/分层/扩展窗口 + 网格校准，`qcfp_backtest_results` 4321 行；146 项测试全过；P0~P6 全链路闭环 ✅。详见 [QCFP-MTF_P6_开发计划.md](QCFP-MTF_P6_开发计划.md) 交付记录；验收细则见 [QCFP-MTF_P6_测试清单.md](QCFP-MTF_P6_测试清单.md)；使用实例见 [QCFP-MTF_P6_使用手册.md](QCFP-MTF_P6_使用手册.md)。

**M0 验证结果（实测）**：

- 全量工作流 `run_QCFP_MTF_workflow.py` 三步全部通过；
- 覆盖度：10 张源表、15 只有行情股票；发现 `00579`/`02602` 完全无数据、`03033`（ETF）缺机构持股；
- 质量：全量 135 项快照，A:76 / B:24 / C:35 / D:0；主要降级原因是早期历史负价格占位数据（如 01093 有 442 条）与资金流辅助列缺失；
- 单股票验证：`--stock 00700` 输出 10 类数据质量标签（daily_kline C 级：负价格 4 条）。

**下一步（P1 前置说明）**：季度结构引擎可直接读取 `qcfp_data_quality_audit` 与 `hk_quarterly_institutional_holdings_analysis`/`hk_quarterly_chip_analysis`；`available_date` 仍为推算模式（披露滞后 45 天），P6 回测前建议补充真实披露日历。
