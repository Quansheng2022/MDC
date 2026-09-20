"""P11-MNT-006 / ISSUE-008: optional Word COM must degrade, never abort the build.

Scope: only the optional COM capability boundary
(``md_converter/renderer/post_processor.py``) and its CLI diagnostic surface.
The real Word-COM refresh path is covered by ``test_word_com_final_artifact.py``
(that test skips when no interactive Word COM session is available).
"""

from __future__ import annotations

import builtins
import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

from md_converter.compiler import CompilerContext, compile_markdown
from md_converter.renderer import post_processor
from md_converter.renderer.post_processor import DocxPostProcessor

REPO_ROOT = Path(__file__).resolve().parents[2]

MARKDOWN = """# 标题

正文内容。
"""

#: Cycle 01 的 bounded reproduction envelope（Doc/production_soak/cycle_01）：
#: 只保留 PATH 与 UTF-8 控制变量，不提供 APPDATA / USERPROFILE / TEMP，
#: 使 pywin32 gencache 生成目录解析到不可写的 C:\WINDOWS\gen_py。
MINIMAL_ENV_KEYS = ("PATH", "PYTHONPATH")

#: 复现 ISSUE-008 时 pywin32 抛出的错误文本（Cycle 01 实测值）
SHIM_PERMISSION_ERROR = "[WinError 5] Access is denied: 'C:\\\\WINDOWS\\\\gen_py'"


def _reload_with_failing_win32com(monkeypatch: pytest.MonkeyPatch, exc: BaseException) -> None:
    """Reload post_processor while ``win32com`` raises ``exc`` on import."""
    real_import: Callable[..., Any] = builtins.__import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "win32com" or name.startswith("win32com."):
            raise exc
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    importlib.reload(post_processor)


def _restore_post_processor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Undo the injected import failure and re-execute the real module."""
    monkeypatch.undo()
    importlib.reload(post_processor)


def _minimal_env() -> dict[str, str]:
    """Service-like environment: PATH + UTF-8 only (P11-MNT-006 intake)."""
    env = {key: os.environ[key] for key in MINIMAL_ENV_KEYS if key in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _run_cli(md_path: Path, out_path: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Run the public CLI in a bounded environment."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "md_converter.cli",
            str(md_path),
            "--no-open",
            "-o",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
        timeout=300,
    )


def test_ut_com_001_permission_error_import_degrades_gracefully(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """UT-COM-001: PermissionError on optional import must not abort the compiler."""
    try:
        _reload_with_failing_win32com(
            monkeypatch,
            PermissionError("[WinError 5] Access is denied: 'C:\\\\WINDOWS\\\\gen_py'"),
        )

        assert post_processor.WIN32_AVAILABLE is False
        reason = DocxPostProcessor.com_unavailable_reason()
        assert reason is not None and "PermissionError" in reason

        # 包/编译器初始化与文档生成必须继续（COM 可选，文档生成不可选）
        out = tmp_path / "ut_com_001.docx"
        ctx = CompilerContext.create({"word_com": True})
        ctx.compile(MARKDOWN, {"title": "ut-com-001"}, out)
        assert out.exists() and out.stat().st_size > 0

        captured = capsys.readouterr()
        assert "[POST002]" in captured.out
    finally:
        _restore_post_processor(monkeypatch)

    assert post_processor.WIN32_AVAILABLE is True
    assert DocxPostProcessor.com_unavailable_reason() is None


def test_it_env_001_cli_survives_service_like_environment(tmp_path: Path) -> None:
    """IT-ENV-001: the bounded minimal environment must still produce a DOCX."""
    md_path = tmp_path / "in.md"
    md_path.write_text(MARKDOWN, encoding="utf-8")
    out = tmp_path / "it_env_001.docx"

    proc = _run_cli(md_path, out, _minimal_env())
    combined = (proc.stdout or "") + (proc.stderr or "")

    assert "Traceback" not in combined
    assert proc.returncode == 0, combined[-800:]
    assert out.exists() and out.stat().st_size > 0
    # 该环境在已认证宿主上使可选 COM 能力不可用，此时降级必须可见且结构化
    # （POST002）。若宿主环境使 COM 可用（例如 C:\WINDOWS\gen_py 可写或存在
    # 可写回退目录），则无需降级诊断；机制级覆盖由 IT-ENV-002 保证。
    if "[POST002]" in combined:
        assert "📋 Diagnostics" in combined


def test_it_env_002_cli_reports_post002_when_optional_com_import_fails(
    tmp_path: Path,
) -> None:
    """IT-ENV-002: deterministic injection of a failing optional COM import."""
    shim = tmp_path / "shim"
    (shim / "win32com").mkdir(parents=True)
    (shim / "win32com" / "__init__.py").write_text(
        f"raise PermissionError({SHIM_PERMISSION_ERROR!r})\n",
        encoding="utf-8",
    )
    md_path = tmp_path / "in.md"
    md_path.write_text(MARKDOWN, encoding="utf-8")
    out = tmp_path / "it_env_002.docx"

    env = _minimal_env()
    env["PYTHONPATH"] = str(shim)
    proc = _run_cli(md_path, out, env)
    combined = (proc.stdout or "") + (proc.stderr or "")

    assert "Traceback" not in combined
    assert proc.returncode == 0, combined[-800:]
    assert out.exists() and out.stat().st_size > 0
    assert "[POST002]" in combined
    assert "📋 Diagnostics" in combined


def test_normal_com_smoke_com_available_path_unchanged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """NORMAL-COM-SMOKE: with COM available the Word refresh path is still used."""
    if platform.system() != "Windows":
        pytest.skip("Word COM path is Windows-only (KNOWN_LIMITATIONS §3)")

    out = tmp_path / "com_smoke.docx"
    compile_markdown(MARKDOWN, config={"toc": True, "word_com": False}, output_path=out)

    calls: list[Path] = []
    monkeypatch.setattr(post_processor, "WIN32_AVAILABLE", True)
    monkeypatch.setattr(post_processor, "WIN32_UNAVAILABLE_REASON", None)
    monkeypatch.setattr(
        DocxPostProcessor,
        "_update_toc_with_word",
        classmethod(lambda cls, path: calls.append(path)),
    )
    capsys.readouterr()

    DocxPostProcessor.process(out, {"title": "com-smoke"}, {"toc": True, "word_com": True})

    assert calls == [out]
    captured = capsys.readouterr()
    assert "[POST002]" not in captured.out
