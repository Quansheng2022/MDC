# Phase 11 Maintenance Specification

## MD_Converter v1.x Maintenance Program

| é¡¹ç›® | å€¼ |
| --- | --- |
| Project | MD_Converterï¼ˆMarkdown â†’ DOCX Compilerï¼‰ |
| Phase | **P11 â€” Maintenance** |
| Spec ç‰ˆæœ¬ | **1.0** |
| åˆ›å»ºæ—¥æœŸ | **2026-09-04** |
| å½“å‰çŠ¶æ€ | **DRAFT â€” READY FOR HUMAN REVIEW / FREEZE** |
| Authority Role | **P11 Maintenance Authorityï¼ˆç» Human Freeze åŽç”Ÿæ•ˆï¼‰** |
| Product Canonical Authority | `CANONICAL_SPEC.md` 1.0 FROZEN |
| P10 Release Baseline | annotated tag `v1.0.0` â†’ `5d2c92a6af662ec8ee392f5a1a4d66f1f022229e` |
| P10 Final Governance Closure | `dab9142f1ece898f7dcd66c2fe53d6106f59230c` |
| Maintenance Version Line | `v1.0.x` patch releases by default |
| Evolution Boundary | Feature / semantic / architecture evolution â†’ **P12 Evolution** |

---

# 1. Authority and Governance Model

## 1.1 Authority Hierarchy

P11 é‡‡ç”¨ä»¥ä¸‹æƒå¨é¡ºåºï¼š

```text
CANONICAL_SPEC.md
    â†“
ADR / Frozen Architecture Decisions
    â†“
Phase_11_Maintenance_Specification.md
    â†“
IMPLEMENTATION_PLAN.md
    â†“
Approved P11 Maintenance Change Package
    â†“
Implementation
    â†“
Test / Evidence
```

è§£é‡Šï¼š

1. `CANONICAL_SPEC.md` ç»§ç»­å®šä¹‰ **äº§å“è¯­ä¹‰ä¸Žä¸å¯è¿åçš„ä¸å˜é‡**ã€‚
2. ADR / Frozen Architecture Decisions ç»§ç»­å®šä¹‰ **æž¶æž„è¾¹ç•Œä¸Žå·²å†»ç»“è®¾è®¡å†³ç­–**ã€‚
3. æœ¬æ–‡æ¡£å®šä¹‰ **P11 Maintenance çš„æµç¨‹ã€æƒé™ã€åˆ†ç±»ã€æµ‹è¯•ã€Release Gate ä¸Ž Closure è§„åˆ™**ã€‚
4. `IMPLEMENTATION_PLAN.md` ç”¨äºŽç™»è®°å·²æ‰¹å‡†çš„å®žé™…å®žæ–½æ¡ç›®ï¼Œä¸å¾—åå‘ä¿®æ”¹æœ¬ Authorityã€‚
5. å•ä¸ª Maintenance Change Package åªèƒ½åœ¨æœ¬æ–‡æ¡£å…è®¸çš„è¾¹ç•Œå†…æ‰§è¡Œã€‚
6. Test / Evidence ç”¨äºŽéªŒè¯å®žçŽ°ï¼Œä¸å¾—æ›¿ä»£ Canonical Authority æˆ–äººä¸ºæ”¹å†™äº§å“è¯­ä¹‰ã€‚

è‹¥å‘ç”Ÿå†²çªï¼š

```text
Canonical > ADR > P11 Maintenance Authority > Implementation Plan
> Change Package > Implementation > Test Convenience
```

## 1.2 Human Gate

ä»¥ä¸‹äº‹é¡¹å¿…é¡»ç”± Human æ˜Žç¡®æ‰¹å‡†ï¼Œä¸å¾—ç”± AI Agent è‡ªåŠ¨å®Œæˆï¼š

- P11 Maintenance Authority Freeze
- SPEC_GAP çš„ Canonical clarification
- ARCH_CHANGE çš„ ADR / Architecture approval
- Patch Release Approval
- Release Tag Approval / Ratification
- P11 Final Closure

---

# 2. Purpose

P11 çš„ç›®æ ‡æ˜¯ï¼š

> **åœ¨ä¸ç ´å MD_Converter v1.0.0 Canonical è¡Œä¸ºå’Œ Frozen Core çš„å‰æä¸‹ï¼Œå¯¹ç”Ÿäº§ä½¿ç”¨è¿‡ç¨‹ä¸­å‘çŽ°çš„çœŸå®žç¼ºé™·ã€ç¨³å®šæ€§ã€å…¼å®¹æ€§ã€å®‰å…¨æ€§ã€ä¾èµ–å’Œæ–‡æ¡£ä¸€è‡´æ€§é—®é¢˜å®žæ–½å¯å®¡è®¡ã€å¯éªŒè¯ã€æœ€å°åŒ–çš„ç»´æŠ¤ã€‚**

P11 ä¸æ˜¯ç»§ç»­å¼€å‘æ–°åŠŸèƒ½çš„é˜¶æ®µã€‚

æ ¸å¿ƒç›®æ ‡ï¼š

1. ä¿æŒ v1.x æ­£ç¡®æ€§å’Œç¨³å®šæ€§ã€‚
2. å¯¹çœŸå®žé—®é¢˜å®žæ–½æœ€å°èŒƒå›´ä¿®å¤ã€‚
3. é˜²æ­¢ Maintenance æ¼”å˜ä¸ºæ— è¾¹ç•Œé‡æž„ã€‚
4. é˜²æ­¢ Optional Improvement è¢«åŒ…è£…æˆ Defectã€‚
5. é˜²æ­¢ Golden / Acceptance baseline ä¸ºè¿å°±å®žçŽ°è€Œæ¼‚ç§»ã€‚
6. ä¿æŒæ¯ä¸ªå˜æ›´å¯è¿½æº¯ã€å¯æµ‹è¯•ã€å¯å›žæ»šã€å¯ Git æ”¶å£ã€‚
7. éœ€è¦æ—¶äº§ç”Ÿå—æŽ§çš„ `v1.0.x` Patch Releaseã€‚
8. å°† Feature / Semantic / Architecture Evolution æ˜Žç¡®éš”ç¦»åˆ° P12ã€‚

---

# 3. P11 Baseline

## 3.1 Release Baseline

```text
Release:
v1.0.0

Annotated Tag:
v1.0.0

Tag Target:
5d2c92a6af662ec8ee392f5a1a4d66f1f022229e
```

è¯¥ tag æ˜¯æ­£å¼ production release baselineï¼ŒP11 ä¸å¾—ç§»åŠ¨ã€åˆ é™¤ã€é‡å»ºæˆ–å¼ºåˆ¶è¦†ç›–è¯¥ tagã€‚

## 3.2 Governance Baseline

```text
P10 Final Governance Closure Commit:
dab9142f1ece898f7dcd66c2fe53d6106f59230c
```

P11 ä»Ž P10 å®Œæ•´æ²»ç†æ”¶å£åŽçš„ repository çŠ¶æ€å¼€å§‹ã€‚

## 3.3 Baseline Protection

é™¤éžæœ‰ç»è¿‡æ‰¹å‡†çš„ Maintenance Change Packageï¼Œå¦åˆ™ç¦æ­¢ä¿®æ”¹ï¼š

- `CANONICAL_SPEC.md`
- Frozen Core
- Golden expected structure / semantic meaning
- Acceptance Corpus meaning
- Release tag `v1.0.0`
- å·²å…³é—­çš„ P10 evidence
- å·²å†»ç»“çš„ P10 release artifacts / hashes / manifest

---

# 4. Scope

## 4.1 Allowed Maintenance Scope

P11 å…è®¸ï¼š

| ç±»åž‹ | æ˜¯å¦å…è®¸ | å…¸åž‹ç¤ºä¾‹ |
| --- | --- | --- |
| Product Defect Fix | âœ… | é”™è¯¯ DOCXã€é”™è¯¯å†³ç­–ã€å¼‚å¸¸ crash |
| Stability Fix | âœ… | èµ„æºæ³„æ¼ã€COM cleanupã€retry defect |
| Security Fix | âœ… | path traversalã€symlinkã€å¤–éƒ¨å†…å®¹æ³„æ¼ã€fail-open |
| Compatibility Fix | âœ… | Windows / Word / Python patch compatibility |
| Dependency Maintenance | âœ… | Playwright / pywin32 / setuptools / build tooling |
| Test Defect Fix | âœ… | é”™è¯¯ assertionã€fixtureã€mockã€æµ‹è¯•è¾¹ç•Œç¼ºå¤± |
| Documentation Correction | âœ… | å®‰è£…è¯´æ˜Žã€é™åˆ¶ã€CLI æ–‡æ¡£ä¸Žå®žé™…è¡Œä¸ºä¸ä¸€è‡´ |
| Performance Regression Fix | âœ… | å·²è¯æ˜Ž regression ä¸”ä¸æ”¹å˜ Canonical è¯­ä¹‰ |
| Operational / Diagnostic Fix | âœ… | æ˜Žç¡®é”™è¯¯ä¿¡æ¯ã€æ—¥å¿—ã€è¯Šæ–­èƒ½åŠ› |
| Minimal Refactor Required by Fix | âš ï¸ | ä»…é™ç¼ºé™·ä¿®å¤ä¸å¯é¿å…çš„æœ€å°ç»“æž„è°ƒæ•´ |

## 4.2 Forbidden Maintenance Scope

P11 é»˜è®¤ç¦æ­¢ï¼š

- æ–° Markdown feature
- æ–° CLI product feature
- æ–° renderer
- æ–° output format
- AST schema evolution
- DecisionEngine semantic change
- LayoutPlan schema evolution
- Theme V2 / Canonical theme semantic change
- Acceptance Corpus semantic redefinition
- Golden baseline ä»…ä¸ºè¿å°±æ–°å®žçŽ°è€Œä¿®æ”¹
- å¤§èŒƒå›´â€œä»£ç æ¸…ç†â€
- æ— ç¼ºé™·ä¾æ®çš„ architecture refactor
- Optional Improvement è‡ªåŠ¨è¿›å…¥ implementation
- é€šè¿‡ä¿®æ”¹æµ‹è¯•æŽ©ç›–äº§å“ç¼ºé™·

ä»¥ä¸Šäº‹é¡¹åŽŸåˆ™ä¸Šè½¬å…¥ï¼š

```text
P12 â€” Evolution
```

---

# 5. Issue Classification

æ‰€æœ‰ P11 Issue å¿…é¡»é¦–å…ˆåˆ†ç±»ã€‚

| Classification | å®šä¹‰ | P11 å¤„ç† |
| --- | --- | --- |
| **DEFECT** | å®žçŽ°è¿å Canonical / Approved Behavior | Change Plan â†’ Patch â†’ Evidence |
| **TEST_DEFECT** | æµ‹è¯•é”™è¯¯ï¼Œäº§å“è¡Œä¸ºæœ¬èº«æ— ç¼ºé™· | Test Change Review â†’ Test Patch |
| **SPEC_GAP** | Canonical å¯¹çœŸå®žåœºæ™¯å®šä¹‰ä¸è¶³æˆ–çŸ›ç›¾ | åœæ­¢äº§å“ä¿®æ”¹ï¼›Human clarification / P12 |
| **ARCH_CHANGE** | ä¿®å¤éœ€è¦æ”¹å˜å·²å†»ç»“æž¶æž„è¾¹ç•Œ | ADR â†’ Human Approval â†’ é€šå¸¸è¿›å…¥ P12 |
| **OPTIONAL_IMPROVEMENT** | éžå¿…è¦æ”¹è¿›ã€å¯è¯»æ€§ã€ä¾¿åˆ©æ€§ã€æœªæ¥ä¼˜åŒ– | Backlogï¼›é»˜è®¤ä¸å®žæ–½ |

## 5.1 Classification Guard

ç¦æ­¢ï¼š

```text
OPTIONAL_IMPROVEMENT
    â†“
é‡æ–°å‘½åä¸º DEFECT
    â†“
ç»•è¿‡ P12 / Human Gate
```

Reviewer å¿…é¡»è¦æ±‚ï¼š

- å¯å¤çŽ°é—®é¢˜ï¼›
- Expected Behavior æƒå¨æ¥æºï¼›
- Actual Behaviorï¼›
- æ˜Žç¡® deviationï¼›
- å¯éªŒè¯ acceptance criteriaã€‚

æ²¡æœ‰è¿™äº›è¯æ®ï¼Œä¸å¾—æŒ‰ DEFECT æ‰§è¡Œã€‚

---

# 6. Severity and Priority

| Severity | å®šä¹‰ | å¤„ç†è¦æ±‚ |
| --- | --- | --- |
| **P1 â€” Critical / Release Blocker** | æ•°æ®æŸåã€ä¸¥é‡é”™è¯¯è¾“å‡ºã€å®‰å…¨é—®é¢˜ã€æ ¸å¿ƒæµç¨‹ä¸å¯ç”¨ | ç«‹å³å»ºç«‹ Change Packageï¼›ä¸å¾—å‘å¸ƒå­˜åœ¨è¯¥ blocker çš„ patch |
| **P2 â€” Major** | ä¸»è¦åŠŸèƒ½é”™è¯¯ã€æ˜Žæ˜¾ç¨³å®šæ€§é—®é¢˜ã€å¸¸è§çŽ¯å¢ƒå¤±è´¥ | é«˜ä¼˜å…ˆçº§å¤„ç† |
| **P3 â€” Normal** | è¾¹ç¼˜ç¼ºé™·ã€ä½Žé¢‘å…¼å®¹é—®é¢˜ã€éžæ ¸å¿ƒé”™è¯¯ | æ­£å¸¸ Maintenance backlog |
| **P4 â€” Minor** | cosmeticã€è½»å¾®æ–‡æ¡£ã€ä½Žå½±å“è¯Šæ–­é—®é¢˜ | å¯å»¶åŽ |
| **Enhancement** | éžç¼ºé™·æ–°èƒ½åŠ›æˆ–æ”¹è¿› | è½¬ P12 / Evolution backlog |

Severity ä¸å¾—ç”±å®žçŽ°éš¾åº¦å†³å®šï¼Œè€Œåº”ç”±ç”¨æˆ·å½±å“ã€é”™è¯¯ä¸¥é‡æ€§ã€æ•°æ®é£Žé™©ã€å®‰å…¨é£Žé™©å’Œå‘ç”Ÿæ¦‚çŽ‡å†³å®šã€‚

---

# 7. Maintenance Workflow

æ ‡å‡†æµç¨‹ï¼š

```text
Issue Intake
    â†“
Classification
    â†“
Severity
    â†“
Reproduction Evidence
    â†“
Expected vs Actual
    â†“
Root Cause Analysis
    â†“
Change Package
    â†“
Reviewer Approval
    â†“
Bounded Patch
    â†“
Targeted Test
    â†“
Regression Gate
    â†“
Conditional Golden / DOCX / COM / Packaging Gate
    â†“
Git Closure
    â†“
CLOSED / ACCEPTED
```

ä»»ä½•æ­¥éª¤å¤±è´¥ï¼Œä¸å¾—è·³è¿‡åŽç»­ Gate ç›´æŽ¥ CLOSEDã€‚

---

# 8. Maintenance Change Package

æ¯ä¸ªå®žé™…ä¿®æ”¹å¿…é¡»æ‹¥æœ‰ç‹¬ç«‹ Change Packageã€‚

æŽ¨è IDï¼š

```text
P11-MNT-001
P11-MNT-002
P11-MNT-003
...
```

## 8.1 Mandatory Schema

```text
Change Package:
P11-MNT-XXX

Title:
<short descriptive title>

Source:
<Canonical / ADR / defect evidence / compatibility requirement>

Classification:
DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT

Severity:
P1 / P2 / P3 / P4 / Enhancement

Affected Version:
v1.0.0 / v1.0.x

Affected Component:
<component>

Problem:
<verified problem>

Reproduction:
<minimal deterministic reproduction>

Expected:
<expected behavior>

Actual:
<actual behavior>

Evidence:
<logs / output / DOCX / stack trace / failing test>

Root Cause:
<verified root cause; UNKNOWN until verified>

Allowed Scope:
<exact files/modules allowed to change>

Forbidden Scope:
<files/modules explicitly prohibited>

Required Tests:
<targeted tests>

Conditional Gates:
Golden / Acceptance / Real DOCX / COM / Packaging / Fresh Install

Acceptance Criteria:
<measurable pass criteria>

Rollback:
<how to revert if needed>

Git Closure:
exact diff
authorized files only
git diff --check PASS
working tree CLEAN
closure commit SHA

Status:
OPEN / APPROVED / IMPLEMENTED / VERIFIED / CLOSED / REJECTED
```

## 8.2 Scope Rule

Allowed Scope å¿…é¡»å°½é‡å°ã€‚

AI Agent ä¸å¾—å› ä¸ºï¼š

- â€œé¡ºä¾¿é‡æž„â€
- â€œä»£ç æ›´ä¼˜é›…â€
- â€œç»Ÿä¸€é£Žæ ¼â€
- â€œæ¶ˆé™¤æŠ€æœ¯å€ºâ€
- â€œæœªæ¥æ›´æ˜“æ‰©å±•â€

è€Œæ‰©å¤§èŒƒå›´ã€‚

---

# 9. Root Cause Gate

Patch å‰å¿…é¡»åŒºåˆ†ï¼š

```text
Symptom
â‰ 
Root Cause
```

å¦‚æžœ Root Cause æœªéªŒè¯ï¼š

```text
Status:
ROOT CAUSE UNVERIFIED
```

æ­¤æ—¶å…è®¸ï¼š

- å¢žåŠ è¯Šæ–­ï¼›
- å¢žåŠ  reproduction testï¼›
- å¢žåŠ  evidenceï¼›

ä½†ä¸å¾—å®žæ–½æœªç»è¯æ®æ”¯æŒçš„å¤§èŒƒå›´ä¿®å¤ã€‚

---

# 10. Test Matrix

æµ‹è¯•æŒ‰é£Žé™©è§¦å‘ï¼Œä¸è¦æ±‚æ¯æ¬¡ Maintenance éƒ½æœºæ¢°è¿è¡Œå…¨éƒ¨ release testsã€‚

| Change Type | Unit | Targeted | Full Pytest | Golden | Acceptance | Real DOCX | COM | Fresh Install |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Docs only | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” |
| TEST_DEFECT | âœ… | âœ… | âœ… | æ¡ä»¶ | æ¡ä»¶ | æ¡ä»¶ | æ¡ä»¶ | â€” |
| Parser / Normalize | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | â€” | â€” |
| Diagram | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | â€” | æ¡ä»¶ |
| Decision / Layout | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | æ¡ä»¶ | â€” |
| Renderer / Writer | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… æ¡ä»¶ | â€” |
| PostProcessor / Final QA | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… æ¡ä»¶ | â€” |
| COM lifecycle | âœ… | âœ… | âœ… | æ¡ä»¶ | æ¡ä»¶ | âœ… | âœ… | â€” |
| CLI | âœ… | âœ… | âœ… | â€” | æ¡ä»¶ | æ¡ä»¶ | â€” | âœ… æ¡ä»¶ |
| Packaging metadata | âœ… | âœ… | âœ… | â€” | â€” | â€” | â€” | âœ… |
| Dependency update | âœ… | âœ… | âœ… | âœ… æ¡ä»¶ | âœ… æ¡ä»¶ | âœ… | âœ… æ¡ä»¶ | âœ… |
| Security boundary | âœ… | âœ… | âœ… | æŒ‰å½±å“ | æŒ‰å½±å“ | æŒ‰å½±å“ | æŒ‰å½±å“ | æ¡ä»¶ |
| Performance regression | âœ… | âœ… | âœ… | æ¡ä»¶ | æ¡ä»¶ | âœ… æ¡ä»¶ | æ¡ä»¶ | â€” |

## 10.1 Regression Rule

å¯¹ product code çš„ P11 ä¿®å¤ï¼Œé»˜è®¤è¦æ±‚ï¼š

```text
Targeted Test:
PASS

Full Regression:
PASS

New Failure:
0

Required Skip:
0
```

å¦‚æžœ full regression ä¸é€‚ç”¨ï¼ŒChange Package å¿…é¡»æ˜Žç¡®è¯´æ˜ŽåŽŸå› å¹¶ç”± Reviewer æ‰¹å‡†ã€‚

## 10.2 Golden / Acceptance Protection

ç¦æ­¢ï¼š

```text
Implementation fails Golden
    â†“
Modify Golden expected output
    â†“
Test becomes green
```

Golden / Acceptance baseline åªæœ‰åœ¨ï¼š

1. Canonical Authority æ˜Žç¡®å…è®¸è¡Œä¸ºå˜åŒ–ï¼›
2. å¯¹åº” Spec / ADR å·²æ‰¹å‡†ï¼›
3. ä¸å±žäºŽç®€å• P11 defect patchï¼›

æ—¶æ‰å…è®¸ä¿®æ”¹ã€‚

é€šå¸¸åº”è¿›å…¥ P12ã€‚

---

# 11. Runtime / Word COM Gate

å¦‚æžœå˜æ›´æ¶‰åŠï¼š

- `WordRenderer`
- `WordWriter`
- PostProcessor
- COM lifecycle
- TOC / Paragraph / Style proxy
- retry / Word process cleanup

åˆ™è‡³å°‘è¦æ±‚ï¼š

```text
Dedicated COM Tests:
PASS

Representative DOCX:
PASS

FinalArtifactQA:
PASS

Fatal COM Error:
0
```

ä¸å¾—å›  COM çŽ¯å¢ƒå¶å‘æ€§è€ŒæŠŠ required test æ”¹ä¸º silent skipã€‚

---

# 12. Security Maintenance

P11 Security Review è‡³å°‘è¦†ç›–ï¼š

- path traversal
- symlink / reparse boundary
- å¤–éƒ¨æ–‡ä»¶è¯»å–
- ä¸´æ—¶ç›®å½•
- shell / subprocess boundary
- Mermaid / external renderer
- untrusted Markdown input
- fail-open quality path
- dependency vulnerability
- package integrity
- unsafe cleanup / delete behavior

Security DEFECT é»˜è®¤è‡³å°‘ P2ï¼›å­˜åœ¨æ•°æ®æ³„æ¼ã€ä»»æ„æ–‡ä»¶è®¿é—®ã€ä»£ç æ‰§è¡Œæˆ–ä¸¥é‡ integrity é£Žé™©æ—¶æŒ‰ P1 å¤„ç†ã€‚

---

# 13. Dependency and Compatibility Maintenance

## 13.1 Permitted

å¯ç»´æŠ¤ï¼š

- Python patch-level compatibility
- Playwright / Chromium compatibility
- pywin32 / Word compatibility
- setuptools / build compatibility
- packaging metadata correctness
- dependency security patches

## 13.2 Upgrade Rule

Dependency upgrade å¿…é¡»è¯´æ˜Žï¼š

```text
Why Upgrade
Affected Behavior
Compatibility Risk
Rollback Version
Required Tests
```

ä¸å¾—ä¸ºäº†â€œè¿½æœ€æ–°ç‰ˆæœ¬â€è‡ªåŠ¨å‡çº§ã€‚

å¦‚æžœå‡çº§å¯¼è‡´ï¼š

- Canonical output change
- Architecture change
- Acceptance drift
- major renderer behavior change

åˆ™åœæ­¢ P11 patchï¼Œè½¬ P12 evaluationã€‚

---

# 14. Documentation Maintenance

å…è®¸ä¿®æ­£æ–‡æ¡£ä¸Žå®žé™…è¡Œä¸ºçš„ä¸ä¸€è‡´ã€‚

æ–‡æ¡£ä¿®å¤å¿…é¡»åˆ¤æ–­ï¼š

```text
Documentation is wrong
or
Implementation is wrong
```

ä¸å¾—é»˜è®¤ä»¥ä¿®æ”¹æ–‡æ¡£æ¥æŽ©ç›–å®žçŽ°ç¼ºé™·ã€‚

æ–‡æ¡£-only Change Package å¯ä¸è¿è¡Œ full regressionï¼Œä½†ä»è¦æ±‚ï¼š

- exact diff
- factual consistency review
- authorized scope
- `git diff --check`
- clean Git closure

---

# 15. AI Agent Governance

P11 ç»§ç»­é‡‡ç”¨ï¼š

```text
              Specification
                   â–²
                   â”‚
            ChatGPT Reviewer
              â–²          â–²
              â”‚          â”‚
         AI Agent â”€â”€â”€ Test System
```

## 15.1 Reviewer

Reviewer å¯ï¼š

- Classification
- Severity Review
- Root Cause Review
- Change Plan
- Allowed / Forbidden Scope
- Test Matrix Selection
- Evidence Review
- Closure Review

Reviewer ä¸å¾—æ›¿ä»£ Human Gateã€‚

## 15.2 AI Agent

AI Agent åªèƒ½ï¼š

- æ‰§è¡Œå·²æ‰¹å‡† Change Packageï¼›
- ä¿®æ”¹ Allowed Scope å†…æ–‡ä»¶ï¼›
- è¿è¡Œæ‰¹å‡†çš„æµ‹è¯•ï¼›
- è¾“å‡º evidenceã€‚

AI Agent ç¦æ­¢ï¼š

- ä¿®æ”¹ Canonical Authorityï¼›
- æ‰©å¤§ Allowed Scopeï¼›
- è‡ªåŠ¨æ”¹å˜ Goldenï¼›
- è‡ªåŠ¨æ”¹å˜ Acceptance Criteriaï¼›
- æŠŠ Optional Improvement æ”¹æˆ DEFECTï¼›
- è‡ªåŠ¨æ‰¹å‡† Patch Releaseï¼›
- è‡ªåŠ¨å®Œæˆ Human Closureã€‚

---

# 16. Git Closure Gate

æ¯ä¸ªå·²å®žæ–½çš„ Maintenance Change Package å¿…é¡» Git æ”¶å£ã€‚

æœ€ä½Žè¦æ±‚ï¼š

```powershell
git status --short
git diff -- <allowed-files>
git add <allowed-files>
git diff --cached --name-status
git diff --cached --check
git diff --cached
git commit -m "<bounded maintenance commit>"
git rev-parse HEAD
git status --short
```

éªŒæ”¶ï¼š

```text
Changed Files:
exactly authorized

Forbidden Files:
0

git diff --cached --check:
PASS

Working Tree:
CLEAN

Closure SHA:
RECORDED
```

ç¦æ­¢ï¼š

- unrelated files æ··å…¥ï¼›
- `git add .` åœ¨ scope æœªå®¡æŸ¥æ—¶ç›´æŽ¥ä½¿ç”¨ï¼›
- amend å·²å†»ç»“ release commitsï¼›
- é‡å†™ `v1.0.0` tagï¼›
- ä¸ºç»´æŠ¤æäº¤æ‰§è¡Œæ— å¿…è¦çš„ rebase / history rewriteã€‚

---

# 17. Patch Release Policy

## 17.1 Version Policy

é»˜è®¤ï¼š

| Change | Version Policy |
| --- | --- |
| Bug / Security / Compatibility fix | `1.0.1`, `1.0.2`, ... |
| Backward-compatible feature | P12 â†’ candidate `1.1.0` |
| Canonical semantic change | P12 |
| Breaking change | P12 â†’ candidate `2.0.0` |

P11 é»˜è®¤åªç”Ÿäº§ **Patch Release**ã€‚

## 17.2 Patch Release Trigger

ä»¥ä¸‹ä»»ä¸€æƒ…å†µå¯è€ƒè™‘ patch releaseï¼š

- å·²å…³é—­ P1 / P2 production defectï¼›
- security fixï¼›
- major compatibility fixï¼›
- å¤šä¸ªå·²éªŒè¯ P3 ä¿®å¤ç´¯ç§¯åˆ°å‘å¸ƒé˜ˆå€¼ï¼›
- Human æ˜Žç¡®è¦æ±‚ patch releaseã€‚

ä¸æ˜¯æ¯ä¸ª Maintenance Commit éƒ½å¿…é¡»å‘å¸ƒã€‚

---

# 18. Patch Release Gate

Patch Release å¿…é¡»é€šè¿‡ï¼š

| Gate | Acceptance |
| --- | --- |
| Maintenance Packages | Release èŒƒå›´å†…å…¨éƒ¨ CLOSED / ACCEPTED |
| Open P1 Blockers | **0** |
| Release-Critical P2 | **0** |
| Targeted Tests | PASS |
| Full Regression | PASS |
| Required Skip | 0 |
| Golden | PASS if affected |
| Acceptance | PASS if affected |
| Representative DOCX | PASS if affected |
| FinalArtifactQA | PASS |
| COM Gate | PASS if affected |
| Packaging | PASS |
| wheel + sdist | Build PASS |
| Artifact Integrity | SHA256 recorded |
| Fresh Install | PASS |
| CLI Smoke | PASS |
| Version Consistency | PASS |
| Release Notes | COMPLETE |
| Patch Manifest | COMPLETE |
| Known Limitations | UPDATED if needed |
| Git Tree | CLEAN |
| Human Production Approval | REQUIRED |

Default decision:

```text
Any Required Gate FAIL
    â†“
PATCH RELEASE DENIED
```

ç¦æ­¢ fail-openã€‚

---

# 19. Patch Release Evidence

Patch release å»ºè®®äº§ç”Ÿç‹¬ç«‹è¯æ®ï¼Œä¾‹å¦‚ï¼š

```text
RC_EVIDENCE/P11_v1.0.1/
```

æˆ–é¡¹ç›®æ—¢æœ‰ Release Evidence Authority è§„å®šçš„ç­‰æ•ˆç»“æž„ã€‚

è‡³å°‘è®°å½•ï¼š

- source commit SHA
- maintenance package IDs
- Python / dependency environment
- regression result
- Golden / Acceptance resultï¼ˆå¦‚é€‚ç”¨ï¼‰
- representative DOCX evidenceï¼ˆå¦‚é€‚ç”¨ï¼‰
- package filenames
- SHA256
- fresh install result
- CLI smoke result
- release decision
- Human approval

---

# 20. P11 Work Packages

| S/N | Phase# | Task | Work Package | Deliverable / Acceptance | Status |
| ---: | --- | --- | --- | --- | --- |
| 1 | P11-01 | Maintenance Scope Freeze | WP-MNT-01 Scope | Allowed / Forbidden Scopeï¼›NO FEATURE DEVELOPMENTï¼›P12 boundary | â³ PLANNED |
| 2 | P11-02 | Maintenance Baseline | WP-MNT-02 Baseline | `v1.0.0` tag targetï¼›P10 closure SHAï¼›test/environment baseline | â³ PLANNED |
| 3 | P11-03 | Issue Classification | WP-MNT-03 Triage | 5-class classification frozen | â³ PLANNED |
| 4 | P11-04 | Severity Gate | WP-MNT-04 Priority | P1/P2/P3/P4/Enhancement rules | â³ PLANNED |
| 5 | P11-05 | Reproduction Evidence | WP-MNT-05 Repro | deterministic reproductionï¼›Expected vs Actual | â³ PLANNED |
| 6 | P11-06 | Change Package Authority | WP-MNT-06 Change Control | Mandatory Change Package schema | â³ PLANNED |
| 7 | P11-07 | Bounded Patch | WP-MNT-07 Patch | minimal authorized modification | â³ CONTINUOUS |
| 8 | P11-08 | Target Verification | WP-MNT-08 Target Test | failing reproduction â†’ PASS | â³ CONTINUOUS |
| 9 | P11-09 | Regression Gate | WP-MNT-09 Regression | full regression PASSï¼›new failure=0 | â³ CONTINUOUS |
| 10 | P11-10 | Golden / Acceptance Gate | WP-MNT-10 Golden | affected behavior remains canonical | â³ CONDITIONAL |
| 11 | P11-11 | Runtime / COM Gate | WP-MNT-11 Runtime | COM / DOCX / FinalArtifactQA | â³ CONDITIONAL |
| 12 | P11-12 | Dependency Maintenance | WP-MNT-12 Dependency | compatibility + rollback + test evidence | â³ CONTINUOUS |
| 13 | P11-13 | Security Maintenance | WP-MNT-13 Security | boundary / dependency / fail-open review | â³ CONTINUOUS |
| 14 | P11-14 | Documentation Maintenance | WP-MNT-14 Docs | docs == actual approved behavior | â³ CONTINUOUS |
| 15 | P11-15 | Git Closure | WP-MNT-15 Git Gate | exact diffï¼›forbidden=0ï¼›clean treeï¼›SHA | â³ CONTINUOUS |
| 16 | P11-16 | Patch Release Decision | WP-MNT-16 Release Gate | release threshold + blockers + Human decision | â³ CONDITIONAL |
| 17 | P11-17 | Patch Build / Verify | WP-MNT-17 Patch Release | wheel/sdist/hash/install/smoke/evidence | â³ CONDITIONAL |
| 18 | P11-18 | Governance Review | WP-MNT-18 Governance | no unauthorized driftï¼›all packages classified | â³ PLANNED |
| 19 | P11-19 | Final Human Closure | WP-MNT-19 Closure | Human approvalï¼›P11 CLOSED / transition decision | â³ PLANNED |

---

# 21. Continuous Maintenance Model

P11 ä¸Ž Development Phase ä¸åŒã€‚

P11-07..15 ä¸ºé•¿æœŸå¾ªçŽ¯ï¼š

```text
P11 Foundation
    â†“
P11-MNT-001
    â†“
Closure
    â†“
P11-MNT-002
    â†“
Closure
    â†“
...
    â†“
Patch Release when justified
```

å› æ­¤ï¼š

- å•ä¸ª Maintenance Package å¯ä»¥ CLOSEDï¼›
- P11 Program å¯ä»¥ä¿æŒ ACTIVEï¼›
- ä¸è¦æ±‚æ¯ä¸ª defect åŽç«‹å³å…³é—­æ•´ä¸ª P11ï¼›
- P11 Final Closure ä»…åœ¨ Human å†³å®šç»“æŸè¯¥ maintenance line æˆ–è¿›å…¥ä¸‹ä¸€æ²»ç†é˜¶æ®µæ—¶æ‰§è¡Œã€‚

---

# 22. P11 Definition of Done

P11 Foundation DoDï¼š

```text
[ ] P11 Maintenance Authority Human-Frozen
[ ] Maintenance Scope frozen
[ ] v1.0.0 release baseline recorded
[ ] P10 governance baseline recorded
[ ] Classification rules frozen
[ ] Severity rules frozen
[ ] Change Package template frozen
[ ] Test Matrix frozen
[ ] Git Closure Gate frozen
[ ] Patch Release Gate frozen
[ ] P12 Evolution boundary frozen
```

P11 Program Final Closure DoDï¼š

```text
[ ] All accepted P11 P1 issues CLOSED
[ ] Release-critical P2 issues = 0
[ ] All implemented Maintenance Packages individually Git-closed
[ ] Unauthorized files = 0
[ ] Unauthorized Frozen Core drift = 0
[ ] Canonical semantic drift = 0
[ ] Silent Golden drift = 0
[ ] Silent Acceptance drift = 0
[ ] Patch releases, if any, fully verified
[ ] Patch release tags, if any, Human-approved
[ ] Open backlog fully classified
[ ] P12 candidates separated from P11
[ ] Governance-only Closure Review PASS
[ ] Final Human Closure APPROVED
```

---

# 23. Initial P11 State

åœ¨æœ¬æ–‡æ¡£ Freeze ä¹‹å‰ï¼š

```text
P11 Status:
DRAFT / NOT YET FROZEN

Product Code Change:
NONE AUTHORIZED

Canonical Change:
NONE AUTHORIZED

Frozen Core Change:
NONE AUTHORIZED

Patch Release:
NONE AUTHORIZED
```

æœ¬æ–‡æ¡£ Human Freeze åŽï¼š

```text
P11 Status:
ACTIVE

Initial Work Package:
P11-MNT-GOV-01
Maintenance Governance Foundation

Immediate Scope:
Governance / Baseline / Triage only

Product Code Change:
NONE until an approved Change Package exists
```

---

# 24. Maintenance Governance Principles

P11 æœ€ç»ˆå›ºå®šä»¥ä¸‹åŽŸåˆ™ï¼š

1. **Canonical Authority**
   Maintenance ä¸å¾—è¶Šè¿‡ Canonicalã€‚

2. **Minimal Change**
   åªä¿®å¤å·²éªŒè¯é—®é¢˜ï¼Œä¸è¿›è¡Œé¡ºå¸¦é‡æž„ã€‚

3. **Evidence Before Patch**
   æ²¡æœ‰ reproduction / deviation evidenceï¼Œä¸å®žæ–½äº§å“ä¿®å¤ã€‚

4. **Classification Before Implementation**
   å…ˆåˆ¤æ–­ DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENTã€‚

5. **Default Deny Scope**
   æœªåˆ—å…¥ Allowed Scope çš„æ–‡ä»¶é»˜è®¤ç¦æ­¢ä¿®æ”¹ã€‚

6. **No Silent Baseline Drift**
   Goldenã€Acceptanceã€Canonicalã€Release Evidence ä¸å¾—ä¸ºè¿å°±å®žçŽ°è€Œé™é»˜å˜åŒ–ã€‚

7. **Risk-Based Testing**
   æµ‹è¯• Gate ç”±å—å½±å“è¾¹ç•Œå†³å®šï¼Œä½† required gate ä¸å¾—é™é»˜ skipã€‚

8. **Git Closure Is Mandatory**
   æ¯ä¸ªå·²å®žæ–½ Maintenance Package å¿…é¡»å½¢æˆ exactã€cleanã€å¯è¿½æº¯ closureã€‚

9. **Patch Release Is Conditional**
   Maintenance commit ä¸ç­‰äºŽå¿…é¡» releaseã€‚

10. **Human Release Authority**
    Patch Production Approvalã€Tagã€P11 Final Closure ä¿ç•™ Human Gateã€‚

11. **Evolution Separation**
    Feature / Semantic / Architecture evolution å±žäºŽ P12ï¼Œä¸å¾—å€Ÿ P11 è¶Šæƒå®žçŽ°ã€‚

---

# 25. Freeze Gate

æœ¬æ–‡æ¡£æˆä¸ºæ­£å¼ **P11 Maintenance Authority** å‰ï¼Œåº”ç”± Human æ˜Žç¡®æ‰¹å‡†ï¼š

```text
APPROVE AND FREEZE
Phase_11_Maintenance_Specification.md
VERSION: 1.0
AS P11 MAINTENANCE AUTHORITY
```

æ‰¹å‡†åŽè®°å½•ï¼š

```text
Spec Version:
1.0

Status:
FROZEN / ACTIVE

Authority:
P11 Maintenance Authority

Human Freeze:
APPROVED

Freeze Date:
<date>

Freeze Commit:
<git SHA>
```

ä¹‹åŽå¯¹æœ¬æ–‡æ¡£æœ¬èº«çš„å®žè´¨æ€§è§„åˆ™ä¿®æ”¹å¿…é¡»èµ°ï¼š

```text
SPEC_GAP / GOVERNANCE CHANGE
    â†“
Review
    â†“
Human Approval
    â†“
Version Update
    â†“
Re-Freeze
```
