# P11 Baseline Evidence

## Evidence Header

| Field | Value |
| --- | --- |
| Work Package | P11-MNT-GOV-01 — Maintenance Governance Foundation |
| Plan | P11_AGENT_PLAN_A |
| Step | A-03 — Maintenance Baseline |
| Date | 2026-09-04 |
| Result | **BASELINE RECORDED** |

---

# 1. Source Baseline

```text
Canonical Specification:  CANONICAL_SPEC.md
Spec Version:             1.0
Spec Status:              FROZEN
Freeze Date:              2026-08-30
Architecture Version:     2.0
Theme Version:            QS-Word-Default-V1.5 (1.5, frozen)
Software Version:         1.0.0 (pyproject.toml / md_converter.__version__)
Applicable ADRs:          ADR-001 .. ADR-009 (Doc/ARCHITECTURE.md)
Acceptance Baseline:      AC001-AC015 (md_converter/tests/acceptance/)
```

---

# 2. Release Baseline

```text
Release:
v1.0.0

Release Tag:
v1.0.0（annotated）

Release Tag Target:
5d2c92a6af662ec8ee392f5a1a4d66f1f022229e

Verified:
git show v1.0.0 --no-patch -> commit 5d2c92a6af662ec8ee392f5a1a4d66f1f022229e
```

---

# 3. Governance Baseline

```text
P10 Final Governance Closure Commit:
dab9142f1ece898f7dcd66c2fe53d6106f59230c

Current HEAD:
dab9142f1ece898f7dcd66c2fe53d6106f59230c

Baseline Protection:
tag v1.0.0 不移动；P10 evidence / Golden / Acceptance / Frozen Core READ ONLY。
```

---

# 4. Environment Baseline

```text
OS:                     Windows NT 10.0.26200.0
Python:                 3.12.14（项目 .venv）
pip:                    26.2.1
pytest:                 9.1.1
Playwright:             1.62.0
Chromium:               playwright-managed chromium_headless_shell-1234
pywin32:                312
Microsoft Word:         Office16 (C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE)
build:                  1.6.0
setuptools:             84.0.0
wheel:                  0.47.0
python-docx:            1.2.0
markdown-it-py:         4.2.0
lxml:                   6.1.1
```

> 注：P10 Release Evidence 记录 Python 3.12.13；本次基线为 3.12.14（patch-level
> 差异），全量回归 PASS，见 §6。

---

# 5. Dependency Baseline

执行 `python -m pip freeze` 输出：

```text
ast_serialize==0.8.0
black==26.5.1
build==1.6.0
cairocffi==1.7.1
CairoSVG==2.9.0
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.5.1
click==8.4.2
colorama==0.4.6
coverage==7.15.4
cssselect2==0.9.0
defusedxml==0.7.1
docutils==0.23
greenlet==3.5.4
id==1.6.1
idna==3.19
iniconfig==2.3.0
isort==8.0.1
jaraco.classes==3.4.0
jaraco.context==6.1.2
jaraco.functools==4.6.0
keyring==25.7.0
librt==0.15.0
lxml==6.1.1
markdown-it-py==4.2.0
-e c:\users\quansheng\documents\projects\md_converter
mdurl==0.1.2
more-itertools==11.1.0
mypy==2.3.0
mypy_extensions==1.1.0
nh3==0.3.7
packaging==26.3
pathspec==1.1.1
pillow==12.3.0
platformdirs==4.11.0
playwright==1.62.0
pluggy==1.6.0
pycparser==3.0
pyee==13.0.1
Pygments==2.20.0
pypandoc_binary==1.17
pyproject_hooks==1.2.0
pytest==9.1.1
pytest-cov==7.1.0
python-docx==1.2.0
pytokens==0.4.1
pywin32==312
pywin32-ctypes==0.2.3
PyYAML==6.0.3
readme_renderer==46.0
requests==2.34.2
requests-toolbelt==1.0.0
rfc3986==2.0.0
rich==15.0.0
ruff==0.16.1
setuptools==84.0.0
tinycss2==1.5.1
twine==7.0.0
typing_extensions==4.16.0
urllib3==2.7.0
webencodings==0.5.1
wheel==0.47.0
```

> pip freeze 元数据警告：沙箱内无法读取 git remote 配置（WinError 5），editable
> source 版本解析失败；不影响依赖版本记录。

---

# 6. Test Baseline

## 6.1 Canonical 环境运行（正式基线）

```text
Command:    python -m pytest md_converter/tests -rs
Collected:  277
Passed:     277
Failed:     0
Skipped:    0
Duration:   596.83s
Environment: Windows + Word COM 可启动 + Playwright Chromium 可启动（canonical golden env）
```

结果与 P10-18 Final Release Regression（277/277 PASS）一致。

## 6.2 沙箱限制运行记录（证据，非正式基线）

```text
Collected:  277
Passed:     274
Failed:     2（test_golden[sample]、test_canonical_golden_environment）
Skipped:    1（test_word_com_final_artifact）

原因：
- Chromium launch: spawn EPERM（沙箱禁止启动子进程）
- Word COM DispatchEx 失败（沙箱禁止 COM / 进程启动）
- 均为环境限制，非产品代码缺陷；产品代码在两次运行中完全相同。
```

## 6.3 测试运行副作用

运行全量测试会重写被跟踪的 `output/document.docx`（测试产物）。基线记录后已将其
还原为 HEAD 状态，工作树恢复。

---

# 7. Known Environment Limitations

```text
1. 默认沙箱禁止 Chromium / Word COM 子进程启动；
   Golden / COM / FinalArtifactQA required gates 必须在非沙箱环境执行。
2. Python 3.12.14 vs P10 evidence 3.12.13（patch-level）；回归 PASS。
3. 沙箱内 pip freeze 无法解析 editable 包 git remote 版本（metadata-only）。
4. 全量回归运行会改写 output/document.docx 测试产物；运行后需还原或忽略。
```

---

# 8. Baseline 结论

```text
Source Baseline:      RECORDED（CANONICAL_SPEC.md 1.0 FROZEN）
Release Baseline:     RECORDED（v1.0.0 -> 5d2c92a6af662ec8ee392f5a1a4d66f1f022229e）
Governance Baseline:  RECORDED（dab9142f1ece898f7dcd66c2fe53d6106f59230c）
Environment Baseline: RECORDED
Dependency Baseline:  RECORDED
Test Baseline:        RECORDED（277/277 PASS，596.83s）
Known Limitations:    RECORDED

Result:
BASELINE RECORDED
```
