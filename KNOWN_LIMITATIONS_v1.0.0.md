# MD Converter v1.0.0 Known Limitations

以下限制均为 v1.0.0 实测或契约内已知项，不构成缺陷承诺遗漏。

## 1. Non-UTF-8 redirected console

在强制 cp1252 / 非 UTF-8 的管道或重定向环境中，CLI 输出（含 emoji/CJK）
可能触发 `UnicodeEncodeError`（P10-12 targeted diagnostic 确认，
exit=1）。

缓解：

```powershell
$env:PYTHONUTF8 = "1"
```

正常 Windows Terminal / UTF-8 环境无此问题（P10-12：UTF-8 PASS）。

## 2. Mermaid rendering requires Playwright + Chromium + CDN

- 需要 `[mermaid]` extra 并执行 `python -m playwright install chromium`。
- 运行时从 `https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`
  加载（外部网络依赖）。
- 离线 / 无 Chromium 环境下 Golden test 必须显式 FAIL（不得 skip、
  不得 fallback PASS）；文档中的 Mermaid 图可能无法渲染。

## 3. Word COM final processing is Windows + Word only

- TOC 页码自动刷新依赖 Windows + Word + pywin32（`[windows]`）。
- 无 COM 时仍生成含原生 TOC 域的文档，页码由 Word 打开后 F9 刷新。

## 4. 未实现功能（v1.0 明确 Non-Goals）

- Footnotes
- Cross References
- PDF / HTML Backend
- Incremental Compilation
- Multi-threaded Compilation

这些不属于 v1.0 capability，不视为缺陷。

## 5. SVG image 支持依赖可选转换器

嵌入 SVG 需要 cairosvg（Cairo）或 wand（ImageMagick）等可选转换器；
未安装时文档内以错误占位文本提示。

## 6. Python 版本范围

`requires-python >=3.8` 为 metadata 兼容性声明；canonical v1.0.0 验证矩阵为
Python 3.12.13 / Windows。其他版本组合未做完整 release certification。
