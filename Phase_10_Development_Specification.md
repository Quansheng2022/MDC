# Phase 10 Development Specification

## MD_Converter v1.0.0 Production Release Program

| 项目 | 值 |
| --- | --- |
| Project | MD_Converter（Markdown → DOCX Compiler） |
| Phase | **P10 — v1.0.0 Production Release** |
| Spec 版本 | 1.0（本文档为 P10 开发规格，随 P10 进度维护） |
| 创建日期 | 2026-09-02 |
| 当前状态 | **IN PROGRESS** |
| Canonical Authority | `CANONICAL_SPEC.md`（1.0 FROZEN，本阶段不修改） |
| 架构依据 | `Doc/ARCHITECTURE.md`、ADR-001..009 |
| 实施追踪 | `IMPLEMENTATION_PLAN.md`（本阶段条目：IMP-021） |
| 基线 | Git HEAD `e5c4ccb0c9c8dc436ab603d45cf5608bce488264`（Clean） |

---

## 1. 目的与范围（Purpose & Scope）

P10 的目标是把已经通过 P8 验收、P9 RC 关闭（`RC-20260901-05`）以及
P10-COM-01 缺陷关闭的代码，正式发布为 **v1.0.0 Production Release**：

```text
Source Freeze（已完成）
    ↓
P10-PKG-01  Packaging Single Authority（当前 P1 Release Blocker）
    ↓
P10-09..10  Build wheel + sdist / Artifact Integrity（SHA256）
    ↓
P10-11..13  Clean Install / CLI Smoke / Representative DOCX
    ↓
P10-14..17  Release Notes / Install Guide / Limitations / Manifest
    ↓
P10-18..24  Final Regression → Tag v1.0.0 → Archive → Post-release Verify → P10 CLOSED
```

### 1.1 范围冻结（Scope Freeze）

- v1.0.0 功能范围固定，**不新增 feature**。
- `CANONICAL_SPEC.md` 1.0 FROZEN，**不修改**。
- 已 CLOSED 的 P7 / P9 / P10-COM-01 / P10-GIT-CLOSE-01 **保持冻结，
  不得重新打开或反复优化**。
- 发现的新问题：按 `REVIEW_TEMPLATE.md` 分类（DEFECT / TEST_DEFECT /
  SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT），**只报告、不修改**
  （除非另行登记 IMP 并列入 Allowed Scope）。

### 1.2 约束（Governance Constraints）

1. 任何 P10 代码变更必须登记 IMP-ID，声明 SPEC-ID/ADR-ID、Allowed Scope 与
   Forbidden Scope。
2. StaticQA / RenderedQA / FinalArtifactQA 为强制质量门；FAIL 不得静默通过。
3. Release Evidence 单一权威目录为 `RC_EVIDENCE/`；Release Decision 由规则
   生成（`md-converter-release-evidence`），不由人工口头判定。
4. 没有 `RELEASE_EVIDENCE.md` / `release_evidence.json` 的 build 不得标记为
   Release Candidate。
5. P10 Git 收口要求：exact diff、authorized scope、working tree clean、
   记录 closure commit SHA。

---

## 2. P10 总体状态快照（截至 2026-09-02）

| Phase | 状态 |
| --- | --- |
| P0..P3 Definition / Spec / Architecture / Implementation Spec | ✅ CLOSED |
| P4..P6 Foundation / Rendering / Quality Engineering | ✅ 100% |
| P7 Governance Engineering | ✅ CLOSED / ACCEPTED |
| P8 Verification & Acceptance | ✅ PASS |
| P9 RC Closure（RC-20260901-05） | ✅ CLOSED / ACCEPTED |
| **P10 Production Release** | 🟡 **IN PROGRESS** |
| P11 Maintenance / P12 Evolution | ⏳ PLANNED |

### 2.1 P10 已关闭工作包（不得重开）

| WP | 任务 | 验收证据 | 状态 |
| --- | --- | --- | --- |
| P10-01 | Release Scope Freeze | 功能范围固定、无新 feature、Canonical 1.0 不修改 | ✅ PASS |
| P10-02 | Source Freeze | frozen core 不再修改；release defect 走独立 Change Package | ✅ PASS |
| P10-03 | Version Gate（FINAL VERIFY） | `pyproject.toml=1.0.0`；`__version__=1.0.0`；Canonical software version=1.0.0；manifest=1.0.0 | ✅ PASS（2026-09-02 复核：PKG-META-03 + CANONICAL_SPEC 一致） |
| P10-04 | Git Baseline | root Git repository；baseline `e5c4ccb…` | ✅ PASS |
| P10-05 | Environment Gate | `.venv` Python 3.12.13；playwright 1.62.0；Chromium launchable | ✅ PASS |
| P10-06 | Golden Gate | Golden PASS；renderer_backend=playwright | ✅ PASS |
| P10-07 | Regression Gate | 263 collected；263/263 PASS；failed=0；required skip=0 | ✅ PASS |
| P10-08 | RC Evidence Recheck（RC05） | new failures=0；QA all PASS；`RELEASE_ELIGIBLE` | ✅ PASS |
| P10-COM-01 | Word COM Lifecycle Cleanup（IMP-020） | retry proxy reset；TOC/Paragraph/Style proxy release；cleanup 顺序；0x800706BE=0；0x800706BA=0；3/3 PASS | ✅ **CLOSED / ACCEPTED**（`3852574c`） |
| P10-GIT-CLOSE-01 | COM 精确 Git 收口 | exact diff；unauthorized files=0；clean tree；closure SHA | ✅ **CLOSED / ACCEPTED** |

---

## 3. P10-PKG-01 — Packaging Single Authority（当前 P1 Release Blocker）

### 3.1 目标

消除 `pyproject.toml` 与 `setup.py` 的**双重 packaging 权威漂移**，
明确 `pyproject.toml` 为唯一 production packaging metadata，保证
wheel / sdist 内容与声明一致。

### 3.2 工作包与验收清单

| S/N | WP | 交付 / 验收清单 | 状态 |
| --: | --- | --- | --- |
| 33 | WP-PKG-01 Authority Audit | 比较 `pyproject.toml` 与 `setup.py`；识别 dependency/extras/scripts/package-data 重复权威；审计结论落档 | ✅ PASS（§3.3 共 13 项） |
| 34 | WP-PKG-02 Single Authority | `pyproject.toml` 为唯一 production packaging metadata；禁止双重配置漂移 | ✅ IMPLEMENTED（wheel metadata == pyproject，零漂移） |
| 35 | WP-PKG-03 Legacy Cleanup | 删除 / 最小化 legacy `setup.py`；不得继续维护独立 dependencies/extras | ✅ IMPLEMENTED（`setup.py` 已删除） |
| 36 | WP-PKG-04 Extras Alignment | `windows` / `mermaid` / `dev` 与文档一致；不存在“文档声称但 metadata 不存在”的 extras | ✅ IMPLEMENTED（PKG-META-07/08/09） |
| 37 | WP-PKG-05 Script Validation | `md-converter` / `md-converter-check` / `md-converter-release-evidence` metadata 正确 | ✅ IMPLEMENTED（含新增 `cli.check_dependencies`；PKG-META-04/14） |
| 38 | WP-PKG-06 Package Data | `py.typed`；theme YAML；必要资源进入 wheel/sdist | ✅ VERIFIED（wheel/sdist 均含 `py.typed` + `default_v1_5.yaml`） |
| 39 | WP-PKG-07 Metadata Tests | Build metadata 可解析；wheel metadata 与 pyproject 一致；无 duplicate authority | ✅ PASS（PKG-META-01..14；wheel METADATA 比对一致） |
| 40 | WP-PKG-08 Git Gate | exact diff；authorized scope；clean tree；commit SHA | ⏳ |
| 41 | P10-PKG-01 DoD | Packaging authorities=1；metadata mismatch=0；README mismatch=0 | ⏳ |

> **注意：P10-PKG-01 不得重新打开 P10-COM-01。**

### 3.3 Authority Audit 结论（2026-09-02 实审）

| # | 审计项 | `pyproject.toml`（权威目标） | `setup.py`（legacy） | 漂移 |
| --: | --- | --- | --- | --- |
| 1 | dependencies | click / markdown-it-py / python-docx / pyyaml（代码实际 import 全部命中） | 额外声明 pypandoc、typing-extensions（代码未 import） | ✗ 重复权威 + 过期依赖 |
| 2 | extras | windows（pywin32>=306）、mermaid（playwright==1.62.0） | win32 / svg / image / mermaid / dev / docs / perf / all | ✗ 名称与集合不一致 |
| 3 | scripts | 3 个（含 `md-converter-release-evidence`）；但 `md-converter-check` 指向 `cli.check_dependencies`（源码缺失，WP-PKG-05 DEFECT） | 缺 `md-converter-release-evidence` | ✗（两处均需收口；缺陷已并入 IMP-021 修复） |
| 4 | passes entry-points | normalize / diagram | 同左 | ✓ 一致 |
| 5 | themes entry-points | default/v1_5 → V15Theme；github/academic/corporate → getter | default → DefaultTheme（v1_5 缺失） | ✗ default 指向漂移 |
| 6 | package-data | py.typed、themes/*.py、renderer/themes/*.yaml | 仅 py.typed | ✗ YAML 资源声明不一致 |
| 7 | py.typed 文件 | 声明存在 | 声明存在 | ✗ 实际文件缺失（两处都指向不存在文件） |
| 8 | MANIFEST.in | — | — | ✗ 引用不存在的 LICENSE/CHANGELOG/CONTRIBUTING/requirements.txt/examples 与错误 tests 路径 |
| 9 | README 文档 | `.[windows]` / `.[mermaid]` / `md-converter-release-evidence` | 插件注册仍写“在 setup.py 中添加 entry_points”；声称 Pandoc 可选依赖（代码未用） | ✗ README mismatch |
| 10 | AGENTS.md 开发流程 | 声明 `pip install -e .[dev]` | dev extra 仅在 setup.py | ✗ 删除 setup.py 后 `.[dev]` 将失效，须在 pyproject 补 dev extra |
| 11 | classifier | Development Status :: 4 - Beta | 同左 | ⚠ v1.0.0 Production Release 应为 5 - Production/Stable（列入本 WP 收口） |
| 12 | license | `license = {text = "MIT"}`（deprecated） | 同左 | ⚠ PEP 639：改 SPDX `license = "MIT"`，移除 License classifier，build-system setuptools>=77 |
| 13 | git 追踪 | 生成的 `md_converter.egg-info/` 7 文件被 git 追踪 | — | ✗ 生成 metadata 不入库；.gitignore 增加 build/ dist/ *.egg-info/ |

### 3.4 额外发现（只报告、不修改，v1.0.0 后另行评估）

| # | 发现 | 建议 |
| --: | --- | --- |
| A | `chk_dependency_packages.py` 维护独立包清单（pypandoc/svg/image），与 pyproject 不一致 | 单独工作包将其改为消费 pyproject metadata 或标注为 dev-only 工具 |
| B | wheel 目前会携带 `md_converter.tests`（packages.find include `md_converter*`） | v1.1 评估在 wheel 中排除测试子包 |
| C | `requires-python = ">=3.8"` 与 AGENTS.md（3.10+）及 Canonical 环境（3.12）不一致 | 统一支持范围需同步 README badge 与 classifiers，v1.1 变更 |
| D | 根目录无 LICENSE / CHANGELOG / CONTRIBUTING 实体文件，但旧 MANIFEST 引用 | 补文件或删除引用（本 WP 删除引用）；实体文件另立任务 |
| E | `md-converter --help` 在管道/非 UTF-8 控制台（cp1252）下抛 UnicodeEncodeError（emoji/CJK）；`PYTHONUTF8=1` 下正常（pre-existing，非本 WP 引入） | WP-REL-12 CLI Smoke 以 `PYTHONUTF8=1` 或 UTF-8 终端执行；如要求无环境依赖，另立小 IMP 在 cli.py 统一 reconfigure stdout |

---

## 4. P10 发布链（PKG-01 之后）

| S/N | Phase# | 任务 | WP | 验收清单 | 状态 |
| --: | --- | --- | --- | --- | --- |
| 42 | P10-09 | Build Clean Package | WP-REL-09 Build | `python -m build`；wheel + sdist；build exit=0；无 source-tree 污染 | ⏳ BLOCKED BY PKG-01 |
| 43 | P10-10 | Artifact Integrity | WP-REL-10 SHA256 | wheel/sdist SHA256；manifest 记录 filename/size/hash | ⏳ |
| 44 | P10-11 | Clean Install | WP-REL-11 Clean Venv | 全新 venv；从 wheel 安装；禁止 editable；依赖解析成功 | ⏳ |
| 45 | P10-12 | CLI Smoke Test | WP-REL-12 CLI Smoke | `md-converter --help`；`md-converter-check`；基本转换；退出码正确 | ⏳ |
| 46 | P10-13 | Representative Production Conversion | WP-REL-13 Real DOCX | 真实 Markdown → DOCX；TOC/表格/样式/图片/diagram 检查；FinalArtifactQA PASS | ⏳ |
| 47 | P10-14 | Release Notes | WP-DOC-14 | v1.0.0 scope；主要能力；release fixes；known limitations；breaking changes=None | ⏳ |
| 48 | P10-15 | Installation Guide | WP-DOC-15 | Python；base；`.[windows]`；`.[mermaid]`；Chromium；Word requirements | ⏳ |
| 49 | P10-16 | Known Limitations | WP-DOC-16 | Mermaid 外部依赖；Word COM Windows-only；未支持 footnotes/cross-ref/PDF/HTML | ⏳ |
| 50 | P10-17 | Release Manifest | WP-REL-17 | software/spec/arch/theme versions；RC05；code/closure SHA；package hashes；build env | 🟡 PARTIAL（`RELEASE_MANIFEST_v1.0.0.json` 待补全） |
| 51 | P10-18 | Final Release Regression | WP-REL-18 Final Gate | 从最终 source HEAD 全量回归；全部 PASS；required skip=0；fatal=0 | ⏳ |
| 52 | P10-19 | Git Tag | WP-REL-19 Tag | clean tree；annotated tag `v1.0.0` 指向 approved release commit | ⏳ **DO NOT TAG YET** |
| 53 | P10-20 | Final Distribution Package | WP-REL-20 | wheel + sdist + Release Notes + Install Guide + limitations + manifest + RC Evidence | ⏳ |
| 54 | P10-21 | Release Approval | WP-REL-21 | 所有 P10 required gates PASS；known blockers=0；spec deviations=0 | ⏳ |
| 55 | P10-22 | Publish / Archive | WP-REL-22 | Git tag；release bundle；RC Evidence immutable archive；SHA records | ⏳ |
| 56 | P10-23 | Post-Release Verification | WP-REL-23 | 从正式 package 再安装；CLI smoke；representative conversion；version/tag/hash match | ⏳ |
| 57 | P10-24 | P10 Closure | WP-REL-24 | Release package verified；tag verified；archive complete；open P1 blockers=0 | ⏳ |

---

## 5. 本阶段登记实施条目

### IMP-021：Packaging Single Authority（P10-PKG-01）

```text
Source:
  SPEC（Software Version authority：pyproject.toml / __version__）
  SPEC-QA-004 / SPEC-INV-010（Release Evidence / Release 质量门）
  ADR-007（Release Closure）

Classification:
  DEFECT

Category:
  RELEASE_PACKAGING

Severity:
  P1 Release Blocker

Modify:
  pyproject.toml（唯一 packaging 权威；extras/scripts/entry-points/
    package-data/classifiers 收口）
  MANIFEST.in（对齐实际 sdist 资源，清除不存在文件引用）
  setup.py（删除 legacy 权威）
  README.md（packaging/install/plugin 文档与 metadata 对齐）
  md_converter/cli.py（新增 check_dependencies，修复 md-converter-check
    缺失目标；纯依赖可用性报告，不改编译逻辑）
  .gitignore（build/ dist/ *.egg-info/ 忽略）
  md_converter.egg-info（git rm --cached：生成 metadata 不再入库）
  md_converter/py.typed（新建 PEP 561 marker）
  md_converter/tests/test_packaging_metadata.py（新建 metadata 契约测试）
  IMPLEMENTATION_PLAN.md（登记本条目）

Do not modify:
  CANONICAL_SPEC.md（FROZEN）
  Parser / AST / Pipeline / DiagramPass / DecisionEngine / LayoutPlan /
  WordRenderer / WordWriter / PostProcessor / Theme V1.5（default_v1_5.yaml）
  Golden baseline / Acceptance Corpus（AC001..AC015）
  release_evidence.py predicates / RC_EVIDENCE/ 既有证据
  chk_dependency_packages.py（额外发现 A，只报告）

Required Evidence:
  PKG-META-01..14（test_packaging_metadata.py）
  wheel / sdist 构建成功且包含 py.typed + default_v1_5.yaml
  Full pytest 回归（P10-18 最终门，本 WP 内至少 metadata 套件全绿）

Acceptance Criteria:
  packaging authorities = 1（仅 pyproject.toml）
  pyproject / wheel metadata / README 三方一致（metadata mismatch=0）
  `pip install -e ".[dev]"` 可解析（dev extra 存在）
  3 个 console scripts 与 entry-points 均可导入解析
  `md-converter-check` 可执行且 required 依赖全绿时 exit 0
  wheel 与 sdist 内含 md_converter/py.typed 与
    md_converter/renderer/themes/default_v1_5.yaml
  Development Status classifier = 5 - Production/Stable（v1.0.0）
  MANIFEST.in 不再引用不存在的文件/目录
```

---

## 6. P10 风险登记

| # | 风险 | 影响 | 缓解 |
| --: | --- | --- | --- |
| R1 | Clean Install / wheel 依赖解析需要 PyPI 网络 | P10-11 阻断 | Release 环境批准网络；本地 pip cache 兜底 |
| R2 | Golden / Mermaid 依赖 jsdelivr CDN | P10-06/18 | Canonical 环境已固定（playwright 1.62.0 + chromium）；离线环境 Golden 必须 FAIL 不 skip |
| R3 | Word COM 环境不稳定 | P10-13/23 | P10-COM-01 已收口；Windows 门内重跑 dedicated COM 测试 |
| R4 | 新 metadata 测试与既有 release_evidence 计数（263）漂移 | 回归计数变化 | 本 WP 属 Additive（263 → 277），最终门以新 baseline 计数为准 |
| R5 | 删除 setup.py 后旧命令/工具引用 | 构建/安装异常 | 全仓扫描（已执行）；README 同步；`pip install -e .` 由 pyproject PEP 517 承担 |

---

## 7. P10 完成定义（Definition of Done）

- [ ] P10-PKG-01 CLOSED：authorities=1；metadata mismatch=0；README mismatch=0；Git exact scope + closure SHA
- [ ] wheel + sdist 构建成功；SHA256 记录
- [ ] 全新 venv 从 wheel 安装成功（非 editable）
- [ ] CLI smoke（3 个命令）PASS；representative DOCX（TOC/表格/样式/图片/diagram）PASS
- [ ] Release Notes / Install Guide / Known Limitations / Release Manifest 完成
- [ ] 最终 source HEAD 全量回归 PASS；required skip=0；fatal=0
- [ ] annotated tag `v1.0.0` 指向 approved release commit
- [ ] Release bundle + RC Evidence 归档；post-release verification PASS
- [ ] P10 CLOSED（open P1 blockers=0）

---

## 8. Live Status（随 P10 进度更新）

| 时间 | 项目 | 结果 |
| --- | --- | --- |
| 2026-09-02 | 本文档创建（P10 开发启动） | ✅ 完成 |
| 2026-09-02 | P10-PKG-01 Authority Audit | ✅ 完成（§3.3） |
| 2026-09-02 | P10-PKG-01 实现（WP-PKG-02..07） | ✅ IMPLEMENTED / VERIFIED |
| 2026-09-02 | 构建验证（`python -m build --no-isolation`） | ✅ wheel + sdist 成功，零 deprecation warning |
| 2026-09-02 | Artifact SHA256 | wheel `7C0B4203…61EAE2`；sdist `D481B554…AADC4E` |
| 2026-09-02 | Full Regression | ✅ 277/277 PASS；required skip=0（exit 0） |
| 2026-09-02 | 版本一致性复核（P10-03） | ✅ 1.0.0 × 4 处一致 |
| — | WP-PKG-08 Git Gate / P10-PKG-01 DoD | ⏳ |
| — | P10-09..24 Release Chain | ⏳ |
