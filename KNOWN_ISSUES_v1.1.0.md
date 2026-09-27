# MD Converter v1.1.0 Known Issues / Accepted Limitations

本文件只列出 **用户可见、且已被接受** 的限制，供 RC 分发与 P12-11 Human
Acceptance 使用。内部工程债不在本文件（见 `Doc/V2/Implementation/P12-09/`
与 `Doc/V2/Implementation/P12-10/` 的 closure evidence）。

`v1.0.0` 已记录的通用限制继续有效，见 `KNOWN_LIMITATIONS_v1.0.0.md`。

---

## 1. 简单表格识别刻意保守（已批准行为，不是缺陷）

空白对齐（ruler 型）简单表格只在以下条件全部满足时才转为 Word 表格：

```text
2 列；>= 3 行；第 2 行是 ruler（>= 2 段、每段 >= 3 个连字符）；
列间隔存在公共锚点；单元格为非空纯文本；无管道符/制表符；位于顶层段落
```

不满足条件的块保持原样段落，且**默认不产生任何诊断**（这是已批准的
CLAR-01 行为）。3 列以上、富文本单元格、列表/引用块内的块均不识别。

开关：`simple_tables.enabled`（默认 `true`）。

## 2. 最终物理分页由 Word 决定

转换器保证图形几何与 keep-together 语义，**不承诺**精确页码或分页确定性；
最终分页版面由 Microsoft Word 渲染时确定。

## 3. 图形最小宽度与极宽图形

按已批准策略，图形收缩后若低于主题下限（`figure.min_width`），仍交付适配
后的尺寸并给出 `RENDER005` WARNING。渲染高度极小的“极宽图形”不属于该策略
范围。

## 4. Mermaid 图需要可选依赖与网络

文档中的 Mermaid 图渲染需要 `[mermaid]` extra（Playwright + Chromium），且
运行时会从 `https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`
加载脚本。离线或无 Chromium 环境下该图无法渲染（非正常转换路径的缺陷）。

## 5. Word COM 功能仅 Windows + Word

TOC 页码自动刷新依赖 Windows + Microsoft Word + pywin32（`[windows]`）。缺少
COM 时仍生成含原生 TOC 域的文档，页码由用户在 Word 中按 F9 刷新。

## 6. 安装包未做代码签名（已知发布条件）

`MD_Converter_v1.1.0_Setup.exe` 与打包可执行文件**均未代码签名**。首次运行时
Windows SmartScreen 可能提示“Windows 已保护你的电脑”，需要 “更多信息 →
仍要运行”。这不是缺陷，也不阻止正常安装；本阶段未采购证书、未搭建签名
基础设施（见 `WP-P12-10-04_EVIDENCE.md`）。

## 7. 使用默认图标

当前没有权威的自定义产品图标，可执行文件与安装程序使用默认图标；未自造
品牌资源。

## 8. 明确的 Non-Goals（未实现功能）

```text
Footnotes / Cross References / PDF Backend / HTML Backend
Incremental Compilation / Multi-threaded Compilation
```

这些不属于 v1.1.0 capability，不视为缺陷。

## 9. Python 版本范围（仅源码/wheel 分发路径）

`requires-python >=3.8` 为元数据兼容性声明；canonical 验证环境为 Python 3.12
/ Windows。**Windows 安装包用户不需要 Python**——安装包已自带运行时。

## 10. 非 UTF-8 控制台重定向（仅 CLI）

在强制 cp1252 的重定向/管道环境中，CLI 输出（含 emoji/CJK）可能触发
`UnicodeEncodeError`。缓解方式：

```powershell
$env:PYTHONUTF8 = "1"
```

打包 GUI（windowed）不写重定向控制台输出，P12-09 已复验 CASE A：不重现。
