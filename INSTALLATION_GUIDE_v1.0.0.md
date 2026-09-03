# MD Converter v1.0.0 Installation Guide

| 项目 | 值 |
| --- | --- |
| Release | v1.0.0 |
| Canonical validation | Python 3.12.13 / Windows |
| Artifacts | `md_converter-1.0.0-py3-none-any.whl` + `md_converter-1.0.0.tar.gz`（hash 见 `RELEASE_MANIFEST_v1.0.0.json`） |

---

## 1. 前置条件

- Windows（推荐；Word COM 功能仅 Windows + Word 可用）。
- Python 3.12（canonical release validation 环境）；metadata 声明
  `requires-python >=3.8` 为兼容性声明，不等于完整认证矩阵。

## 2. Base Install（wheel）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install md_converter-1.0.0-py3-none-any.whl
```

不要使用 editable install（`pip install -e .`）验证正式发布。

## 3. Windows / Word COM（`[windows]`）

```powershell
pip install "md_converter-1.0.0-py3-none-any.whl[windows]"
```

安装后 Word COM 用于 TOC 页码自动刷新。未安装 pywin32 时仍可生成文档，
TOC 以原生 Word 域插入，页码由用户按 F9 刷新。

## 4. Mermaid（`[mermaid]`）

```powershell
pip install "md_converter-1.0.0-py3-none-any.whl[mermaid]"
python -m playwright install chromium
```

Mermaid 运行时从 pinned CDN（jsdelivr，mermaid@10）加载脚本，
渲染需要网络可达该 CDN。

## 5. Full Windows Production（`[windows,mermaid]`）

```powershell
pip install "md_converter-1.0.0-py3-none-any.whl[windows,mermaid]"
python -m playwright install chromium
```

## 6. Dependency Verification

```powershell
md-converter-check
```

Required 依赖（click / markdown-it-py / python-docx / PyYAML）齐备时退出码 0；
可选依赖（pywin32 / playwright）以警告列出，不阻断。

## 7. Basic Usage

```powershell
md-converter input.md
md-converter input.md --output result.docx --no-open
md-converter --help
```

Release Evidence CLI：

```powershell
md-converter-release-evidence input.md --test-report tests_report.json `
  --governance-report governance_evidence.json
```

证据规则判定 `RELEASE_BLOCKED` 时退出码为 1。

## 8. Canonical Validated Environment

```text
Canonical v1.0.0 validation:
Python 3.12.13 / Windows
Playwright 1.62.0
Chromium: playwright-managed headless shell
Word: Windows Word（COM）
```
