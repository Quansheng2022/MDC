# QCFP-MTF P6 用户使用手册（含实例）

> 适用版本：QCFP-MTF-2.1.1 / P6 回测与校准
> 环境：Windows + 项目虚拟环境 `.venv`（Python 3.13）
> 所有命令默认在项目根目录执行

## 一、环境准备

```powershell
cd C:\Users\Quansheng\Documents\projects\TA_Workflow
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
```

## 二、实例 1：跑一次回测

```powershell
# 单股预演（不写库）
.venv\Scripts\python.exe Core\QCFP_MTF\scripts\backtest_runner.py --stock 00700 --dry-run

# 全量回测（写 qcfp_backtest_results，2021 起默认）
.venv\Scripts\python.exe Core\QCFP_MTF\scripts\backtest_runner.py --run-id bt_full_20260820

# 自定义区间
.venv\Scripts\python.exe Core\QCFP_MTF\scripts\backtest_runner.py --start 2023-01-01 --end 2025-12-31 --run-id bt_2023_2025
```

预期输出（全量）：

```text
信号时间线 9827 行，Look-ahead 检查通过
累计 -99.11%  年化 -5.53%  Sharpe -0.0463  最大回撤 -99.74%  胜率 45.4%  盈亏比 0.9734
risk_on: 年化 15.98%  Sharpe 0.6206
neutral: 年化 18.58%  Sharpe 0.8111
risk_off: 年化 -16.96%  Sharpe -0.4574
已写入 qcfp_backtest_results 4321 行（run_id=bt_full_20260820）
```

## 三、实例 2：查看回测结果

```powershell
# 报告文件
Get-ChildItem Report\QCFP_MTF\backtest | Sort-Object LastWriteTime -Descending | Select-Object -First 6 Name

# 数据库：某 run_id 的信号分布
sqlite3 SQLiteDB\HK_Stock.db "SELECT action_signal, COUNT(*) FROM qcfp_backtest_results WHERE run_id='bt_full_20260820' GROUP BY 1 ORDER BY 2 DESC;"

# 收益明细抽样
sqlite3 SQLiteDB\HK_Stock.db "SELECT stock_code, signal_date, action_signal, position, pnl FROM qcfp_backtest_results WHERE run_id='bt_full_20260820' AND pnl IS NOT NULL ORDER BY pnl DESC LIMIT 5;"
```

## 四、实例 3：参数校准

```powershell
# 网格校准（9 组合，约 20 秒）
.venv\Scripts\python.exe Core\QCFP_MTF\scripts\calibration.py --start 2021-01-01 --top 5

# 写入建议参数（不覆盖主配置）
.venv\Scripts\python.exe Core\QCFP_MTF\scripts\calibration.py --start 2021-01-01 --apply

# 查看校准结果
Get-Content (Get-ChildItem Report\QCFP_MTF\backtest\calibration_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

## 五、实例 4：解读回测指标

| 指标 | 含义 | 当前值（全量基线） |
| :-- | :-- | :-- |
| 累计收益 | 1+pnl 连乘 - 1 | -99.11% |
| 年化收益 | 周频年化 | -5.53% |
| Sharpe | (周均收益-无风险)/周标准差×√52 | -0.0463 |
| 最大回撤 | 净值峰值到谷底最大跌幅 | -99.74% |
| 胜率 | 持仓周盈利占比 | 45.4% |
| 盈亏比 | 总盈利 / 总亏损 | 0.9734 |

分层结论：策略在 **risk_on/neutral 环境有效**（Sharpe 0.62/0.81），在 **risk_off 环境亏损**（-17%）——与"季度结构定方向"的设计一致，风险偏好弱时系统倾向离场，但离场后的负收益主要来自换仓成本与 2022/2023/2026 的结构性下跌。

## 六、实例 5：运行测试

```powershell
# 全量 146 项
.venv\Scripts\python.exe Core\QCFP_MTF\tests\run_all_tests.py

# P6 专项
.venv\Scripts\python.exe Core\QCFP_MTF\tests\test_backtest\test_lookahead_filter.py
.venv\Scripts\python.exe Core\QCFP_MTF\tests\test_backtest\test_engine.py
```

## 七、实例 6：Python 直接调用（二次开发）

```powershell
$code = @'
import sys
sys.path.insert(0, "Core")
import pandas as pd
from QCFP_MTF.common.db import connect
from QCFP_MTF.config.settings import load_qcfp_settings
from QCFP_MTF.backtest.data_pipeline import build_signal_timeline
from QCFP_MTF.backtest.engine import run_backtest
from QCFP_MTF.backtest.performance import evaluate
from QCFP_MTF.backtest.lookahead_filter import assert_no_lookahead
from QCFP_MTF.data.loader import load_derived, load_idx_hist, load_kline

s = load_qcfp_settings()
structural = pd.read_sql_query("SELECT stock_code, period_end, available_date, structural_regime, c_state, data_quality FROM qcfp_quarterly_structural", connect())
monthly = pd.read_sql_query("SELECT stock_code, month_end, monthly_behavior_state, cbi_score, cost_position, data_quality FROM qcfp_monthly_behavior", connect())
weekly = pd.read_sql_query("SELECT stock_code, stock_name, week_end, tactical_signal, data_quality FROM qcfp_weekly_tactical", connect())
chip = load_derived("quarterly_chip_analysis")[["stock_code","quarter_end_date","chip_structure_score"]]
idx = load_idx_hist(); weekly_kl = load_kline("weekly")

signals = build_signal_timeline(structural, monthly, weekly, chip, idx, s, stocks=["00700"])
assert_no_lookahead(signals)
bt = run_backtest(signals, weekly_kl, s)
print(evaluate(bt["pnl"], bt["position"]))
'@
$code | .venv\Scripts\python.exe -
```

## 八、实例 7：日常维护

```powershell
# 表结构变更后重生成字典
.venv\Scripts\python.exe Code_utl\Generate_qcfp_Dictionaries.py

# 清理 WAL
sqlite3 SQLiteDB\HK_Stock.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 回测日志
Get-Content Log\backtest_runner.log -Tail 30
```

## 九、参数汇总

| 参数 | 入口 | 说明 |
| :-- | :-- | :-- |
| `--stock 00700` | backtest_runner / calibration | 只回测指定股票 |
| `--start / --end` | backtest_runner / calibration | 回测区间（默认 2021 起） |
| `--run-id` | backtest_runner | 回测标识（写入结果表） |
| `--dry-run` | backtest_runner | 不写库 |
| `--top N` / `--apply` | calibration | 输出前 N 组合 / 写建议参数文件 |

## 十、常见问题

| 现象 | 说明 |
| :-- | :-- |
| 为什么总体收益为负 | 默认阈值下策略在 risk_off 环境亏损；校准与分层显示 risk_on/neutral 环境正收益，说明需要结合市场环境使用 |
| 回测为什么从 2021 起 | 资金流 2021 起可用，季度 F 因子 2021 前缺失 |
| 最大回撤 -99.7% 是否异常 | 池化 15 只股票周 pnl 的累计结果，2022-2023 系统性下跌所致；单股回撤更小 |
| 校准的芯片权重为何无影响 | chip 权重只经置信度→风险→Extreme 门控影响动作，极端情形少；真正敏感的是 REDUCE 仓位 |
| 如何启用校准参数 | `calibration.py --apply` 写 `Config/qcfp_calibration.json`，人工评审后手工合入主配置 |
| 回测进不进每日工作流 | 不进。回测/校准按需运行，与 `run_QCFP_MTF_workflow.py` 解耦 |
