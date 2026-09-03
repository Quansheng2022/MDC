# MD Converter v1.0.0 Release Notes

| 项目 | 值 |
| --- | --- |
| Release | **v1.0.0** |
| Date | 2026-09-03 |
| RC Baseline | `RC-20260901-05` |
| P10-PKG-01 Closure | `cae92ff99accac94ce7dd2356cc470072efecdba` |
| Canonical Spec | 1.0（FROZEN） |
| Theme | QS-Word-Default-V1.5（frozen） |
| Artifact Authority | `RELEASE_MANIFEST_v1.0.0.json`（P10-17 定稿） |

---

## v1.0.0 Scope

MD Converter v1.0.0 是把 Markdown 编译为生产级 Word（.docx）文档的正式版本，
覆盖 P0–P9 全部 MVP 验收范围，并完成 P10 release engineering 收口。

本版本：

- 不新增 feature（Scope Freeze）。
- 不修改 `CANONICAL_SPEC.md` 1.0（FROZEN）。
- 修复 P10-COM-01（Word COM lifecycle）与 P10-PKG-01（Packaging Single
  Authority）两类 release blocker。

## Major Capabilities

- 完整 Markdown 语法：标题 / 段落 / 列表 / 表格 / 代码块 / 引用块 /
  水平分割线 / 行内样式 / 链接 / 图片。
- Diagram：Mermaid（Playwright + Chromium）与 ASCII → Mermaid 自动转换。
- 文档自动化：Frontmatter 封面页、TOC（Word COM 页码刷新）、自动分页。
- 编译器架构：Parser → Immutable AST → Pipeline（Normalize/Diagram/
  插件）→ DecisionEngine/LayoutPlan → Renderer → PostProcessor → QA。
- 主题系统：QS-Word-Default-V1.5（frozen），中英混排字体（东亚字体，
  避免 MS Mincho fallback）。
- 质量门：StaticQA / RenderedQA / Repair / FinalArtifactQA；
  FAIL 不得静默通过。
- 诊断系统、Golden Test、Canonical Acceptance Corpus（AC001–AC015）、
  Release Evidence（Default Deny）。

## Architecture Summary

```text
Markdown
  ↓
Parser（markdown-it-py + BuilderRegistry）
  ↓
Immutable AST
  ↓
Pipeline Passes（NormalizePass / AsciiToMermaidPass / DiagramPass / plugins）
  ↓
DecisionEngine → LayoutPlan
  ↓
WordRenderer / WordWriter
  ↓
PostProcessor（Cover / TOC / Table styling / Word COM）
  ↓
FinalArtifactQA
  ↓
DOCX
```

## Release Fixes

### P10-COM-01 — Word COM Lifecycle Cleanup（IMP-020）

- retry proxy reset；TOC / Paragraph / Style proxy release；
  child → document → Word cleanup 顺序。
- 结果：`0x800706BE = 0`、`0x800706BA = 0`、fatal diagnostic = 0；
  dedicated COM verification 3/3 PASS。

### P10-PKG-01 — Packaging Single Authority（IMP-021）

- `pyproject.toml` 为唯一 packaging authority；删除 legacy `setup.py`
  （消除 dependency/extras/scripts/entry-points/package-data 双重权威）。
- 修复 `md-converter-check` 无效 CLI target：新增 `cli.check_dependencies`。
- 补建 `md_converter/py.typed`（PEP 561 marker）；修正 `MANIFEST.in`
  与实际资源一致；生成物 `build/ dist/ *.egg-info/` 不再入库。
- Extras 收口：`windows` / `mermaid` / `dev`；license 改 SPDX `MIT`
  （PEP 639，构建零 deprecation warning）；classifier 改为
  `5 - Production/Stable`。
- README/AGENTS 文档与 metadata 对齐。

## Validation Summary

| Gate | Result |
| --- | --- |
| Packaging metadata tests（PKG-META-01..14） | PASS |
| Wheel + sdist build（PEP 517） | PASS |
| twine check | PASS |
| Clean install（fresh venv, wheel only, repo 外） | PASS |
| CLI smoke（help / check / basic conversion / evidence help） | PASS |
| Representative production DOCX（TOC/table/image/Mermaid/ASCII/COM） | PASS |
| Development full regression（pre-release HEAD） | 277/277 PASS |
| P10-18 final release regression | 在 tag 前执行，结果记入 P10 evidence |

## Breaking Changes

None。

- 安装方式改为 wheel / pyproject 声明；旧 `setup.py` 不再存在（内部
  metadata 一致性修复，不影响 CLI 与 API 契约）。
- Extras 名称统一为 `windows` / `mermaid` / `dev`（legacy
  `win32` / `svg` / `image` 等不再提供）。

## Known Limitations

详见 [KNOWN_LIMITATIONS_v1.0.0.md](KNOWN_LIMITATIONS_v1.0.0.md)。

## Validated Environment

Canonical v1.0.0 validation：

```text
OS:        Windows
Python:    3.12.13（项目 .venv / release venv）
Playwright: 1.62.0
Chromium:  playwright-managed headless shell
Word:      Windows Word（COM）
```

`requires-python >=3.8` 是 metadata compatibility declaration，
不等于完整 release certification matrix。
