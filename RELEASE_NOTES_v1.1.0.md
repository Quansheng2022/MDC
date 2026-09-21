# MD Converter v1.1.0 Release Notes

| 项目 | 值 |
| --- | --- |
| Release | **v1.1.0**（minor / feature） |
| Date | 2026-09-21 |
| Previous Release | `v1.0.1` |
| Artifact Authority | `RELEASE_MANIFEST_v1.1.0.json` |
| Version Policy Basis | `P11/P11_PATCH_RELEASE_GATE.md` §2（backward-compatible feature → P12 → candidate `1.1.0`） |
| Canonical Spec | **1.1（FROZEN，2026-09-21 re-freeze；supersedes 1.0）** |
| Architecture | 2.0（未修改） |
| Theme | QS-Word-Default-V1.5（frozen，未修改） |
| Implementation Status | IMPLEMENTED / VERIFIED / HUMAN ACCEPTED（2026-09-21） |

---

## Scope

v1.1.0 是 P12 Product Evolution 的第一个 **feature release candidate**：只包含
Human 已接受的三个 P12 候选、其必需测试与验收夹具、已批准的 P12 文档，以及释放版本
元数据。没有其他功能进入本 RC。

```text
new features:                Figure page-fit policy；conservative simple-table recognition
behaviour correction:        Empty heading（WARN + DROP）
breaking changes:            NONE
architecture changes:        NONE
Canonical 1.0 document:      UNCHANGED（P12 提案已批准，等待并入/re-freeze）
```

---

## P12-CAND-002 — Figure Page-Fit / Figure Size Policy

图形尺寸现在由**有效 section 内容区**决定（页宽/页高减去页边距；A4/1in ≈ 15.92 × 24.62 cm
只是当前参考几何，不是硬编码常数）：

```text
目标宽度 = min(配置 image_width, 有效内容区宽度)
保持宽高比；永不放大；永不超出内容区宽/高
超出内容区高度 -> 按高度收缩到恰好适配
收缩后低于主题 figure.min_width（8cm）-> 仍交付适配尺寸，并给出 RENDER005 WARNING
RenderedQA 现在真实测量 figure_overflow（ERROR，沿用 fail_on_error）与 figure_below_min_width（WARNING）
物理分页仍由 Word 决定（converter 只保证几何与 keep-together 语义）
```

## P12-CAND-001 — Whitespace-aligned / Simple-Table Recognition

保守识别"带横线分隔行（ruler）的两列空白对齐块"，转换为真实 Word 表格：

```text
必需：>= 3 行；第 2 行是 ruler（>= 2 段 >= 3 个连字符）；其余每行恰好 1 段 >= 2 空格的列间隔；
      两列单元格非空；列间隔存在公共锚点；无管道符/制表符；仅纯文本行内内容
输出：首行为表头行（Word 重复表头），ruler 行不产生行；恰好 2 列
不满足：保留原段落，且默认不产生任何诊断（CLAR-01）
开关：simple_tables.enabled（默认 true）
```

## P12-CAND-003 — Empty Heading Behaviour Policy

```text
空标题（含仅空白/仅制表符变体）不再渲染：不产生段落、不产生占位文本 "Heading"、不递增标题计数
AST 保留该 Heading 节点（source truth）；既有 StaticQA semantic_empty_heading WARNING 保持不变
目录与标题编号不再出现合成条目
```

---

## Compatibility

```text
不含 ruler 型空白对齐块的文档：输出不变
不含空标题的文档：输出不变
已在内容区内的图形：尺寸不变（仍使用 min(image_width, 内容区宽度)）
既有 Markdown 管道表格 / HTML 表格、围栏代码块：行为不变
紧急回滚开关：simple_tables.enabled=false（图形/标题策略无配置开关，如需回滚则回退提交）
```

## Known Limitations

```text
Simple Table recognition 刻意保守：3+ 列、富文本单元格、列表/引用块内、无 ruler 的块均不识别，
    且拒绝时不产生诊断（这是已批准行为，不是缺陷）
最终物理分页仍归 Word；不承诺页码或分页确定性
图形最小宽度处理受已批准策略约束：适配后低于主题下限时仍交付适配尺寸并给 WARNING
极宽图形（渲染高度极小）不属于本策略范围
```

## Environment Requirements

```text
Python >= 3.8（包元数据）；canonical 验证环境 Python 3.12（.venv）
可选：pywin32（Word COM TOC 页码刷新）、Playwright + Chromium + CDN（Mermaid canonical 渲染）
无上述可选依赖时按既有 KNOWN_LIMITATIONS_v1.0.0.md 降级（native TOC 域 / 文本回退图），不视为缺陷
```

## Breaking Changes

```text
NONE
```

## Canonical Specification Identity

```text
CANONICAL_SPEC.md  spec_version 1.1 / spec_status FROZEN / freeze_date 2026-09-21
Supersedes         spec 1.0（FROZEN 2026-08-30；记录保留于 SPEC_CHANGELOG.md）
Incorporated       SPEC-FUNC-022 / SPEC-FUNC-023 / SPEC-FUNC-024
                   SPEC-INV-013 / SPEC-INV-014 / SPEC-QA-005
Clarifications     CLAR-01（识别失败不产生诊断）/ CLAR-02（有效 section 内容区）
Acceptance corpus  AC001–AC018
ADR                none required for the P12 delta
```

## Verification Basis（release readiness）

```text
HUMAN CANONICAL ENVIRONMENT（authoritative release-gate evidence; executed by the Human）:
    Canonical Golden   PASS（-k "canonical_golden_environment or golden" → "....."）
    Word COM           PASS（-k "wordcom or word_com" → ".." + [100%]）
    Full regression    PASS / exit 0（[100%]；PowerShell $LASTEXITCODE = 0）
AGENT RESTRICTED SANDBOX（non-authoritative environment limitation, not a product defect）:
    Chromium           cannot launch（BrowserType.launch: spawn EPERM）
    Word COM           COM dispatch unavailable（logon session）
Evidence set: RC_EVIDENCE/P12_v1.1.0/（含 human_canonical_verification.json）
Final wheel        fresh non-editable install PASS + CLI PASS + representative P12 smoke PASS
```

## Publication Status

```text
TAG:           NOT CREATED
REMOTE PUSH:   NOT PERFORMED
PUBLICATION:   NOT PERFORMED — 等待 Human Production Release Approval
```
