# P11 Git Closure — P11-MNT-001

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `P11_GIT_CLOSURE_GATE.md` / `Doc/Phase_11_Maintenance_Specification.md` v1.0（§16） |
| Date | 2026-09-04 |

---

# 1. Git Closure Sequence

```text
git status --short
git diff -- P11/P11_MAINTENANCE_REGISTRY.md
git diff -- P11/maintenance/P11-MNT-001/
git diff -- tools/review/merge_project_for_phase11_review.py

git add P11/P11_MAINTENANCE_REGISTRY.md
git add P11/maintenance/P11-MNT-001/ISSUE_INTAKE.md
git add P11/maintenance/P11-MNT-001/REPRODUCTION.md
git add P11/maintenance/P11-MNT-001/ROOT_CAUSE_ANALYSIS.md
git add P11/maintenance/P11-MNT-001/CHANGE_PACKAGE.md
git add P11/maintenance/P11-MNT-001/TARGET_VERIFICATION.md
git add P11/maintenance/P11-MNT-001/REGRESSION_EVIDENCE.md
git add P11/maintenance/P11-MNT-001/SCOPE_AUDIT.md
git add P11/maintenance/P11-MNT-001/GIT_CLOSURE.md
git add P11/maintenance/P11-MNT-001/CLOSURE.md
git add tools/review/merge_project_for_phase11_review.py

git diff --cached --name-status
git diff --cached --check
git diff --cached
git commit -m "governance(p11): close P11-MNT-001 test defect"
git rev-parse HEAD
git status --short
```

禁止 `git add .`；使用显式文件清单。

---

# 2. Pre-Commit Verification

```text
Unauthorized File:
0

Whitespace Error（git diff --cached --check）:
0 / PASS

Staged Files:
exactly authorized（Registry + P11/maintenance/P11-MNT-001/* +
tools/review/merge_project_for_phase11_review.py；测试补丁已于 42394ad）
```

---

# 3. Closure Commit SHA（自引用规则）

本文件在 closure commit 中提交时不得填写该 commit 自身尚不存在的 SHA
（P11_AGENT_PLAN_B §22）。正确顺序：

```text
Closure Commit
    ↓
obtain SHA
    ↓
Registry / ratification record 引用 SHA
```

```text
Closure Commit SHA:
ebcd4f948a3eee16476eb7b15c45b2b81ea67ac8
```

---

# 4. Post-Commit Verification

```text
git rev-parse HEAD:
ebcd4f948a3eee16476eb7b15c45b2b81ea67ac8

git status --short:
（closure commit 后：CLEAN）

Working Tree:
CLEAN
```

---

# 5. B-12 Maintenance Merger（在 clean closed state 上执行）

```text
Command:
python .\tools\review\merge_project_for_phase11_review.py
    --mode maintenance
    --run-pytest
    --strict

Result:
RESULT: PASS
（277 passed in 542.35s；merged files 163；manifest 含测试文件、
P11/maintenance/P11-MNT-001/*、Registry；详见 REGRESSION_EVIDENCE.md）
```
