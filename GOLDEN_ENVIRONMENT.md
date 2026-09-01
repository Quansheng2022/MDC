# Golden Environment Contract（F5）

Golden Test 的 baseline 与运行环境强绑定：**不允许在缺 Mermaid renderer 的
环境里拿同一条 baseline 假装通过**。`test_golden.py` 会在每次运行时记录
`renderer_backend`，与 baseline 不一致时直接失败并提示本文件。

# Golden Test Environment（C3）

Canonical Mermaid backend:

```text
Playwright + Chromium
```

Required:

```text
- Python 3.12+（项目 .venv）
- playwright ==1.62.0（pyproject.toml [mermaid] extra，精确 pin）
- Chromium installed by Playwright
- md_converter dependencies installed（pip install -e .[mermaid]）
```

Setup:

```bash
pip install -e ".[mermaid]"
python -m playwright install chromium
```

Linux CI 如需系统依赖：

```bash
python -m playwright install --with-deps chromium
```

Verification（Golden preflight）：

```bash
pytest md_converter/tests/test_golden_environment.py -q
pytest md_converter/tests/test_golden.py -q
```

Expected:

```text
all passed
renderer_backend = playwright
```

不满足时 Golden 必须 FAIL（不得 skip、不得 fallback PASS）。

Golden command:

```bash
python -m pytest md_converter/tests/test_golden.py -q
```

Full regression:

```bash
python -m pytest md_converter/tests -q -rs
```

Expected:

```text
renderer_backend = playwright
Golden = PASS
Required skip = 0
```

> **外部依赖声明（2.9/2.10）**：当前 Playwright Mermaid renderer 使用
> `https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`，
> 因此 Golden 执行要求网络可达该 pinned CDN endpoint。长期稳定性建议
> 后续将 Mermaid JS 本地化 pin（本轮不动 DiagramPass，属 Forbidden Scope）。

## Canonical Golden Renderer

二选一，作为正式 Release 环境的 Canonical Golden renderer：

```text
playwright（Chromium）   <- 本项目当前 Canonical
或
mmdc（Mermaid CLI）
```

不要随机“有 Chromium 用 Chromium、没有就 fallback”，然后仍拿同一 baseline
比较。`renderer_backend` 取值：

```text
playwright
mmdc
fallback（渲染失败，DIAG002）
```

`fallback` 只允许用于开发调试；**Golden baseline 不得在 fallback 环境下
生成或验收**。

## 当前固定环境（2026-08-31 验证）

| 组件 | 版本 |
| --- | --- |
| Python | 3.12.13（项目 `.venv`） |
| playwright | 1.62.0 |
| Chromium | chromium_headless_shell-1234（playwright 管理） |
| Mermaid renderer 实现 | DiagramPass（playwright 截图，CDN mermaid@10） |
| Mermaid 版本 | mermaid@10（jsdelivr CDN） |
| OS | Windows |
| baseline renderer_backend | `playwright` |

> 注：本环境存在 `mmdc.CMD` shim，但 `mmdc --version` 无法执行
> （Windows CreateProcess 无法直接运行 .CMD），因此 Canonical renderer
> 为 playwright。探测逻辑与 `DiagramPass._check_mmdc` 一致，
> 以实际执行成功为准，而不是 `shutil.which`。

> 该表为基线记录；升级任一组件后必须重新生成 Golden baseline，
> 并走 investigate → ADR/Spec approval → approve baseline 流程。

## 标准 Release CI 顺序

```text
1. Static / lint（black / isort / ruff）
2. Unit
3. Integration
4. Golden（必须为 Canonical renderer 环境）
5. Acceptance（AC001–AC015）
6. Governance tests（quality gate / release evidence / config consistency）
7. Full regression
8. Release Evidence（md-converter-release-evidence）
```

Golden 在缺 Mermaid renderer 的沙箱环境会因 `renderer_backend=fallback`
显式失败（环境契约失败，而非神秘快照 diff）。
