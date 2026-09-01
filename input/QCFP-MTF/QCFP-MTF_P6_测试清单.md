# QCFP-MTF P6 测试清单

> 适用范围：回测与校准系统（Look-ahead / 时间线 / 引擎 / 绩效 / 分层 / 校准）
> 验收口径：A~G 全部勾选 = P6 完成
> 记录：2026-08-20 实测基线（当前全部通过）

## 运行环境

- 项目根目录 `C:\Users\Quansheng\Documents\projects\TA_Workflow`；
- 使用 `.venv\Scripts\python.exe`；中文乱码先执行 `$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"`；
- 数据库：`SQLiteDB/HK_Stock.db`。

---

## A. 单元测试（自动化）

- [ ] A1 全量回归：`.venv\Scripts\python.exe Core\QCFP_MTF\tests\run_all_tests.py`
  → 共 146 项全部 PASS（P0~P5 133 + P6 13），退出码 0
- [ ] A2 pytest：`.venv\Scripts\python.exe -m pytest Core\QCFP_MTF\tests -v`
  → 146 passed
- [ ] A3 P6 专项：`... python Core\QCFP_MTF\tests\test_backtest\test_lookahead_filter.py`（其余 5 个 P6 模块同理）
  → 每模块"全部通过 ✅"

## B. 回测模块单测（合成数据）

- [ ] B1 Look-ahead：available_date > 决策日剔除、空值不算违规、断言抛错
- [ ] B2 信号时间线：结构按 available_date 对齐（5/29 用 5/15 披露的季度、8/14 用 8/14 披露的季度）
- [ ] B3 引擎：仓位次周生效、建仓/清仓换手成本 0.45%、pnl 手算一致
- [ ] B4 绩效：年化/夏普/最大回撤/胜率/盈亏比/分年度
- [ ] B5 校准：小网格可运行、输出按 Sharpe 排序

## C. 数据表验证（qcfp_backtest_results）

- [ ] C1 行数与 run_id：`SELECT COUNT(*), COUNT(DISTINCT run_id) FROM qcfp_backtest_results`
  → 4321 行 / 1 个 run_id（bt_full_20260820）
- [ ] C2 股票与区间：15 只 / 2021-01-01 ~ 2026-08-14
- [ ] C3 信号分布：`SELECT action_signal, COUNT(*) ... GROUP BY 1`
  → EXIT 1962 / HOLD 1319 / REDUCE 678 / WAIT 359 / BUY 3
- [ ] C4 仓位与收益合理：`SELECT AVG(position), AVG(pnl) FROM ...`
  → 0.384 / -0.000267
- [ ] C5 唯一性：`(run_id, stock_code, signal_date)` 不重复（重复运行追加新 run_id）

## D. 回测运行

- [ ] D1 单股：`... backtest_runner.py --stock 00700 --dry-run` → Look-ahead 检查通过、退出码 0
- [ ] D2 全量：`... backtest_runner.py --run-id bt_full_20260820` → 写 4321 行
- [ ] D3 报告产物：`Report/QCFP_MTF/backtest/{equity_*.csv, summary_*.json}`
  → summary 含 overall / by_year / by_market_regime / expanding_windows
- [ ] D4 Look-ahead 断言：全量 9827 行信号时间线 0 违规

## E. 校准运行

- [ ] E1 `calibration.py --start 2021-01-01 --top 5` → 9 组合约 20 秒完成
- [ ] E2 输出 `Report/QCFP_MTF/backtest/calibration_*.json`，按 Sharpe 降序
- [ ] E3 `--apply` 写入 `Config/qcfp_calibration.json`（不覆盖主配置）

## F. 结果合理性

- [ ] F1 分层符合直觉：risk_on/neutral 正收益（年化 +16%/+19%）、risk_off 负收益（-17%）
- [ ] F2 总体绩效为负（年化 -5.53%）属客观事实，说明默认参数待校准——这正是 P6 的价值
- [ ] F3 校准发现 reduce=0.7 优于 0.5（Sharpe -0.032 vs -0.046）
- [ ] F4 2024/2025 年正收益（+8.4%/+5.4%）、2022/2023/2026 负收益，与市场环境一致

## G. 工程约定

- [ ] G1 字典同步：`Code_utl\Generate_qcfp_Dictionaries.py` 重跑后 qcfp_backtest_results 字段数 = PRAGMA 列数
- [ ] G2 源表只读：`hk_*` 表结构未被 P6 改动
- [ ] G3 回测不进入每日工作流（`SCRIPT_LIST` 未包含），按需运行

---

## 验收标准

- 必备：A1、B1~B5、C1~C5、D1~D4、E1~E2、F1~F4、G1~G3；
- 可选：A2~A3、E3；
- 说明：F2/F3 属结果性发现（默认参数下策略为负收益），验收的是系统正确性而非策略盈利性；校准参数仅作建议，是否启用由人工决定。
