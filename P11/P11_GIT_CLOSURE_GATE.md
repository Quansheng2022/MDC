# P11 Git Closure Gate

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§16 Git Closure Gate） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN |
| Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |

---

# 1. Purpose

每个已实施 / 已关闭的 Maintenance Change Package 必须 Git 收口。本文件固定收口
流程与验收标准。

---

# 2. 标准命令序列

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

---

# 3. 验收标准

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

---

# 4. Scope Audit Before Commit

```text
Product Code Files Changed:
0

Frozen Core Files Changed:
0

Golden Files Changed:
0

Acceptance Files Changed:
0

Release Tag Changed:
0

P10 Evidence Changed:
0
```

只允许已授权的 governance artifacts / Change Package Allowed Scope 文件。

---

# 5. 禁止事项

```text
unrelated files 混入 commit
未审查的 git add .
amend 已冻结 release commits
重写 v1.0.0 tag
为维护提交执行无必要的 rebase / history rewrite
```

禁止无审查使用：

```powershell
git add .
```

---

# 6. Closure 记录

Change Package 收口后在 `P11_MAINTENANCE_REGISTRY.md` 与 Closure Template 中记录：

```text
Closure Commit SHA:
<actual SHA>

Working Tree:
CLEAN
```
