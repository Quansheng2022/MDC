"""
Windows Word COM round-trip regression（P0-TBL-04）。

真实生产路径:
    Renderer -> PostProcessor -> python-docx save -> Word COM Open
    -> TOC update -> Word Save -> FinalArtifactQA

仅在 Windows + Word 已安装 + win32com 可真实启动 Word 时运行；
否则 skip（Windows Release Gate，不是日常跨平台强制测试）。
"""

import platform
from pathlib import Path

import pytest

from md_converter.compiler import CompilerContext
from md_converter.renderer.layout.final_artifact_qa import FinalArtifactQA


def _word_com_reachable() -> bool:
    """探测 Word COM 是否真实可用（Windows + pywin32 + Word 实例可启动）。"""
    if platform.system() != "Windows":
        return False
    try:
        import win32com.client
    except Exception:
        return False
    word = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
    except Exception:
        return False
    try:
        # 与生产路径 _update_toc_with_word 相同的初始化，
        # 避免 Word 尚未完成启动时立即 Quit 造成 RPC 竞态
        word.Visible = False
        word.DisplayAlerts = 0
        word.Quit()
    except Exception:
        pass
    finally:
        # 与 P10-COM-01 相同：proxy 显式释放，避免残留 COM proxy
        word = None
    return True


pytestmark = pytest.mark.skipif(
    not _word_com_reachable(),
    reason="Requires Windows + installed Word + pywin32 (Windows Release Gate)",
)


@pytest.mark.integration
def test_word_com_roundtrip_final_artifact_qa_pass(tmp_path: Path) -> None:
    """Word 保存后，Table Grid style-only 边框仍通过 FinalArtifactQA。"""
    markdown = "# Roadmap\n\n" "| A | B |\n" "| --- | --- |\n" "| 1 | 2 |\n"
    out_path = tmp_path / "word_com_roundtrip.docx"
    ctx = CompilerContext.create({"word_com": True})
    ctx.compile(markdown, None, out_path)

    assert ctx.final_artifact_qa_result is not None
    assert ctx.final_artifact_qa_result.status == "PASS"
    assert ctx.final_artifact_sha256

    from docx import Document

    doc = Document(str(out_path))
    assert doc.tables
    for table in doc.tables:
        assert FinalArtifactQA._has_effective_table_borders(table)
