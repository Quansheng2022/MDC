# MD Converter v1.0.1 Release Notes

| 项目 | 值 |
| --- | --- |
| Release | **v1.0.1**（patch） |
| Date | 2026-09-20 |
| Previous Release | `v1.0.0` |
| Artifact Authority | `RELEASE_MANIFEST_v1.0.1.json` |
| Canonical Spec | 1.0（FROZEN，未修改） |
| Architecture | 2.0（未修改） |
| Theme | QS-Word-Default-V1.5（frozen，未修改） |

---

## v1.0.1 Scope

v1.0.1 是 **patch release candidate**：只包含 Production Usage Validation Cycle 01
中经 Human 接受、已关闭的 P11 maintenance 修复。不新增能力，不改变 Canonical
语义与架构。

```text
new features:                NONE
breaking changes:            NONE
Canonical semantic changes:  NONE
architecture changes:        NONE
P12 work:                    NONE
```

---

## Fixed defects

| Package | Issue(s) | Fix |
| --- | --- | --- |
| P11-MNT-006 | ISSUE-008 | 可选 Word COM 依赖的导入/能力初始化失败（如 pywin32 gencache 目录不可写的 `PermissionError`）不再终止 package/CLI 初始化；能力标记为不可用、原因保留，并以 `POST002` 结构化诊断上报，DOCX 照常生成（native TOC 域保留）。 |
| P11-MNT-007 | ISSUE-001 / ISSUE-002 | Markdown 链接现在写入真实 `w:hyperlink` 与外链关系，`http/https`、`mailto`、相对路径与 `#anchor` 目标均可从最终 DOCX 恢复；可见文本与既有蓝色下划线样式不变。AC010 现在同时断言链接文本与目标（含负向证明）。 |
| P11-MNT-008 | ISSUE-007 | 冻结主题/配置的 `page.size = A4` 现在应用于 portrait 文档（`11906 × 16838` twips）；页边距不变，landscape 宽表仍使用同一 A4 权威。此前 52/52 产物沿用模板 US Letter。 |
| P11-MNT-009 | ISSUE-004 | Markdown 中由空行分隔的两个独立表格不再以直接相邻的 `w:tbl` 输出，Word COM 打开/保存不再合并它们（表格数量、表头重复、列结构保持）；FinalArtifactQA 新增 `adjacent_tables` 结构信号，回归时不会静默通过。 |

---

## Verification basis

```text
Canonical environment:   PASS（Chromium launchable, backend=playwright, Word COM live）
Acceptance:              PASS 35/35
Golden:                  PASS（baseline 未修改）
Full regression:         PASS 308/308 — failed 0, errors 0, required skip 0
Representative repair:   MNT-006 / MNT-007 / MNT-008 / MNT-009 各自代表性文档 PASS
```

---

## Known Limitations

`KNOWN_LIMITATIONS_v1.0.0.md` 仍然有效，未因本次修复产生事实性过时内容
（未发现需要修改的陈述）：

```text
Known Limitations Update: NOT REQUIRED / unchanged
```

---

## Explicitly not included

```text
ISSUE-003（figure 过大 / page-fit 策略；Human classification / SPEC_GAP 待裁）
ISSUE-005（随机临时图片名与 ZIP 时间戳确定性；backlog）
ISSUE-006（字节级 determinism 粒度；SPEC_GAP / backlog）
ISSUE-009（空标题占位文本；behaviour-policy clarification）
ISSUE-010（库内 debug print 输出；P4 / OPTIONAL_IMPROVEMENT）
P12-CAND-001（whitespace-aligned 表格识别；DISCOVERY ONLY）
```
