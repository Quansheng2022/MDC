"""R2-V01 WP-04 application / CLI / GUI / serial-batch integration verification.

Drives the *real* entry points and measures the accepted invariants:

  G  GUI single-file and multi-file Serial Batch through ``GuiWorker`` ->
     ``ConversionService`` -> Canonical Core: strict serial
     (``active_conversion_count <= 1``), list order, failure isolation,
     per-file state, derived summary, profile capture, no state leakage,
     worker cleanup.
  H  CLI entry point (installed ``md-converter`` console script): stable output
     naming, single-file and directory modes.
  I  Cross-entry consistency: identical source + config through the service and
     through the CLI produce the same canonical document.

Exit code 0 == every check passed.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence, Tuple

REPO_ROOT = None
for _candidate in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
    if (_candidate / "md_converter" / "__init__.py").is_file():
        REPO_ROOT = _candidate
        break
if REPO_ROOT is None:  # pragma: no cover - defensive
    raise RuntimeError("repository root not found")

PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
CLI = REPO_ROOT / ".venv" / "Scripts" / "md-converter.exe"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONUTF8", "1")

SUCCESS_BODY = "# Notes\n\nStable body text.\n"
WARNING_BODY = "#\n\nSome body text.\n"
FAILURE_BODY = ""


class Report:
    """Collect and print PASS/FAIL checks."""

    def __init__(self) -> None:
        self.rows: List[Tuple[str, bool, str]] = []

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        """Record one check."""
        self.rows.append((label, bool(ok), detail))

    def print(self) -> int:
        """Print the report and return the number of failures."""
        print("R2-V01 WP-04 APPLICATION / CLI / GUI / SERIAL BATCH")
        print("=" * 72)
        failures = 0
        for label, ok, detail in self.rows:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
            if detail:
                print(f"       {detail}")
            failures += 0 if ok else 1
        print("=" * 72)
        print(f"checks={len(self.rows)} failed={failures}")
        return failures


# --------------------------------------------------------------------------
# GUI helpers
# --------------------------------------------------------------------------
def pump() -> None:
    """Deliver pending Qt events."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


def wait_until(predicate: Callable[[], bool], timeout_ms: int = 60000) -> bool:
    """Process GUI events until ``predicate`` holds, or the timeout expires."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        pump()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def write_markdown(path: Path, body: str) -> Path:
    """Write ``body`` as UTF-8 Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def spy_on_service(window: Any) -> Dict[str, Any]:
    """Record real service calls: order, thread identity and peak concurrency."""
    original = window.service.convert
    state: Dict[str, Any] = {
        "calls": [],
        "threads": [],
        "requests": [],
        "active": 0,
        "concurrency": 0,
    }

    def recording(request: Any) -> Any:
        state["calls"].append(Path(str(request.source_path)).name)
        state["threads"].append(threading.get_ident())
        state["requests"].append(request)
        state["active"] += 1
        state["concurrency"] = max(state["concurrency"], state["active"])
        try:
            return original(request)
        finally:
            state["active"] -= 1

    window.service.convert = recording
    return state


def run_batch(window: Any) -> None:
    """Start the batch and wait for the run and the worker to finish."""
    from md_converter.gui.state import GuiState

    window.start_conversion()
    wait_until(lambda: not window.worker.is_running and window.state is not GuiState.CONVERTING)


def prepare_batch(
    window: Any, workspace: Path, names: List[str], bodies: Dict[str, str]
) -> List[Path]:
    """Select ``names`` as a batch and point the output folder into ``workspace``."""
    sources = [write_markdown(workspace / name, bodies.get(name, SUCCESS_BODY)) for name in names]
    output_dir = workspace / "out"
    output_dir.mkdir(exist_ok=True)
    window.set_output_directory(output_dir)
    window.set_source_file(str(sources[0]))
    if len(sources) > 1:
        window.add_source_files([str(source) for source in sources[1:]])
    return sources


def check_gui(report: Report, workspace: Path) -> None:
    """GUI single-file + serial batch invariants."""
    from md_converter.application.conversion_service import ConversionService
    from md_converter.gui.app import create_application
    from md_converter.gui.batch import BatchItemStatus
    from md_converter.gui.main_window import MainWindow
    from md_converter.gui.state import GuiState

    create_application([])
    window = MainWindow()
    window.service = ConversionService({"word_com": False})
    main_thread = threading.get_ident()
    try:
        # --- serial batch: success, failure, warning, success ----------------
        prepare_batch(
            window,
            workspace / "batch",
            ["a.md", "b.md", "c.md", "d.md"],
            {
                "a.md": SUCCESS_BODY,
                "b.md": FAILURE_BODY,
                "c.md": WARNING_BODY,
                "d.md": SUCCESS_BODY,
            },
        )
        state = spy_on_service(window)
        run_batch(window)

        report.check(
            "G1 strict list order is the execution order",
            state["calls"] == ["a.md", "b.md", "c.md", "d.md"],
            f"calls={state['calls']}",
        )
        report.check(
            "G2 active_conversion_count <= 1 (strict serial)",
            state["concurrency"] == 1,
            f"peak_concurrency={state['concurrency']}",
        )
        report.check(
            "G3 every conversion runs off the GUI thread",
            all(thread_id != main_thread for thread_id in state["threads"]),
            f"threads={state['threads']}",
        )
        run = window.batch_run
        report.check(
            "G4 per-file state: 2 succeeded, 1 warning, 1 failed",
            run is not None and (run.succeeded, run.warnings, run.failed) == (2, 1, 1),
            f"summary={(run.succeeded, run.warnings, run.failed) if run else None}",
        )
        g5_detail = (
            f"item1={run.items[1].status if run else None} "
            f"item3={run.items[3].status if run else None}"
        )
        report.check(
            "G5 failure isolation: the source after the failure still converts",
            run is not None
            and run.items[1].status is BatchItemStatus.FAILED
            and run.items[3].status is BatchItemStatus.SUCCESS
            and run.items[3].output_path is not None
            and run.items[3].output_path.exists(),
            g5_detail,
        )
        g6_outputs = [item.output_path.name if item.output_path else None for item in run.items]
        report.check(
            "G6 one document per successful source, named after the source stem",
            run is not None
            and all(
                item.output_path is not None
                and item.output_path.name.startswith(item.source_path.stem)
                for item in run.items
                if item.status.produced_output
            )
            and run.items[1].output_path is None,
            f"outputs={g6_outputs}",
        )
        report.check(
            "G7 batch returns the window to READY",
            window.state is GuiState.READY,
            f"state={window.state}",
        )
        report.check(
            "G8 worker / thread cleanup leaves no reference",
            window.worker.is_running is False
            and window.worker.thread is None
            and window.is_conversion_active is False,
            f"running={window.worker.is_running} "
            f"thread={window.worker.thread} active={window.is_conversion_active}",
        )

        # --- no state leakage: a fresh single-file batch still works ----------
        prepare_batch(window, workspace / "second", ["solo.md"], {"solo.md": SUCCESS_BODY})
        state2 = spy_on_service(window)
        run_batch(window)
        second_run = window.batch_run
        report.check(
            "G9 no state leakage: a later single-file conversion still succeeds cleanly",
            state2["calls"] == ["solo.md"]
            and state2["concurrency"] == 1
            and second_run is not None
            and (second_run.succeeded, second_run.warnings, second_run.failed) == (1, 0, 0)
            and window.state is GuiState.SUCCESS,
            f"calls={state2['calls']} concurrency={state2['concurrency']} state={window.state}",
        )
        solo_output = second_run.items[0].output_path if second_run else None
        report.check(
            "G10 single-file surface produces exactly one document",
            solo_output is not None and solo_output.exists() and solo_output.parent.name == "out",
            f"output={solo_output}",
        )

        # --- profile captured for the batch -----------------------------------
        profile_workspace = workspace / "profile"
        prepare_batch(window, profile_workspace, ["p1.md", "p2.md"], {})
        window.set_output_profile("academic")
        state3 = spy_on_service(window)
        run_batch(window)
        captured = [
            (request.config_overrides or {}).get("output_profile") for request in state3["requests"]
        ]
        report.check(
            "G11 selected profile is captured on every batch request",
            captured == ["academic", "academic"] and window.output_profile == "academic",
            f"captured={captured} window_profile={window.output_profile}",
        )
        from docx import Document

        academic_doc = Document(str(window.batch_run.items[0].output_path))
        report.check(
            "G12 captured profile reaches the rendered geometry",
            abs(academic_doc.sections[-1].left_margin.cm - 3.0) < 0.02,
            f"left_margin={round(academic_doc.sections[-1].left_margin.cm,3)}",
        )
        window.set_output_profile("professional_report")
    finally:
        wait_until(lambda: not window.worker.is_running, timeout_ms=15000)
        window.close()
        pump()


# --------------------------------------------------------------------------
# CLI helpers
# --------------------------------------------------------------------------
def run_cli(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run the installed CLI console script and capture its output."""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [str(CLI), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
    )


def check_cli(report: Report, workspace: Path) -> None:
    """CLI entry point: naming contract, single-file and directory modes."""
    cli_workspace = workspace / "cli"
    (cli_workspace / "input").mkdir(parents=True)
    write_markdown(cli_workspace / "input" / "alpha.md", SUCCESS_BODY)
    write_markdown(
        cli_workspace / "input" / "beta.md",
        "---\ntitle: A/B Report\n---\n\n# Section\n\nBody.\n",
    )
    config_path = cli_workspace / "config.yaml"
    config_path.write_text("word_com: false\n", encoding="utf-8")

    directory_out = cli_workspace / "dir_out"
    completed = run_cli(
        ["input", "--no-open", "--output", str(directory_out), "--config", str(config_path)],
        cwd=cli_workspace,
    )
    produced = (
        sorted(p.name for p in directory_out.glob("*.docx")) if directory_out.exists() else []
    )
    report.check(
        "H1 CLI directory mode exits 0",
        completed.returncode == 0,
        f"rc={completed.returncode} stderr_tail={completed.stderr.strip()[-160:]!r}",
    )
    report.check(
        "H2 CLI names outputs from the sanitized frontmatter title / stem",
        produced == ["A_B_Report.docx", "alpha.docx"],
        f"produced={produced}",
    )

    single_out = cli_workspace / "single" / "explicit.docx"
    single_out.parent.mkdir(parents=True, exist_ok=True)
    completed_single = run_cli(
        ["input/alpha.md", "--no-open", "--output", str(single_out), "--config", str(config_path)],
        cwd=cli_workspace,
    )
    report.check(
        "H3 CLI single-file mode honours an explicit output path",
        completed_single.returncode == 0 and single_out.exists(),
        f"rc={completed_single.returncode} exists={single_out.exists()}",
    )


def normalized_document_xml(path: Path) -> str:
    """Return ``word/document.xml`` with the data-URI picture name masked."""
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    return re.sub(r'(<pic:cNvPr id="\d+" name=")[^"]*(")', r"\1<image>\2", xml)


def check_cross_entry(report: Report, workspace: Path) -> None:
    """Equivalent source + config through the service and the CLI agree."""
    from md_converter.application.conversion_request import ConversionRequest
    from md_converter.application.conversion_service import ConversionService

    cross = workspace / "cross"
    cross.mkdir(parents=True, exist_ok=True)
    body = (
        "---\ntitle: Cross Entry\n---\n\n# Cross Entry\n\nIntro.\n\n"
        "## Data\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n"
    )
    source = write_markdown(cross / "cross.md", body)

    service_out = cross / "service.docx"
    with open(os.devnull, "w", encoding="utf-8") as sink:
        import contextlib

        with contextlib.redirect_stdout(sink):
            ConversionService({"word_com": False}).convert(
                ConversionRequest(source_path=source, output_path=service_out)
            )

    config_path = cross / "config.yaml"
    config_path.write_text("word_com: false\n", encoding="utf-8")
    cli_out = cross / "cli.docx"
    completed = run_cli(
        [str(source), "--no-open", "--output", str(cli_out), "--config", str(config_path)],
        cwd=cross,
    )

    service_xml = normalized_document_xml(service_out) if service_out.exists() else ""
    cli_xml = normalized_document_xml(cli_out) if cli_out.exists() else ""
    i1_detail = (
        f"rc={completed.returncode} "
        f"service_sha={hashlib.sha256(service_xml.encode()).hexdigest()[:16]} "
        f"cli_sha={hashlib.sha256(cli_xml.encode()).hexdigest()[:16]}"
    )
    report.check(
        "I1 CLI and service produce the same canonical document for the same input",
        completed.returncode == 0 and bool(service_xml) and service_xml == cli_xml,
        i1_detail,
    )


def main() -> int:
    """Run every WP-04 check."""
    report = Report()
    workspace = Path(tempfile.mkdtemp(prefix="r2v01_wp04_"))
    check_gui(report, workspace)
    check_cli(report, workspace)
    check_cross_entry(report, workspace)
    print(f"workspace={workspace}")
    failures = report.print()
    print_entry_path_observation()
    return 1 if failures else 0


def print_entry_path_observation() -> None:
    """Print the factual entry-point path of each surface (no PASS/FAIL)."""
    cli_text = (REPO_ROOT / "md_converter" / "cli.py").read_text(encoding="utf-8")
    uses_service = "ConversionService" in cli_text
    uses_core = "from .compiler import CompilerContext" in cli_text
    print("ENTRY-POINT PATH OBSERVATION (informational, no PASS/FAIL)")
    print("  GUI single-file / serial batch -> ConversionService: YES")
    print(
        f"  CLI -> ConversionService: {'YES' if uses_service else 'NO'}; "
        f"CLI -> CompilerContext (canonical core): {'YES' if uses_core else 'NO'}"
    )
    print(
        "  Note: CLI convergence onto ConversionService is the documented deferred "
        "'Step C' (P12-02 ARCHITECTURE_INSPECTION section 11); the CLI still enters "
        "the canonical core, so no compiler stage is bypassed. Not a R2-V01 drift."
    )


if __name__ == "__main__":
    sys.exit(main())
