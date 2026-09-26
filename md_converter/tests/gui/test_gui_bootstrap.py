"""Focused verification for the GUI bootstrap (WP-P12-04-01 §9).

PySide6 is a development dependency; when it is unavailable these focused
tests skip rather than failing collection (project convention for optional
capabilities).

Covered:

* GUI modules import;
* ``QApplication`` can be constructed (once per process);
* ``MainWindow`` can be instantiated, shows, and closes without exception;
* window title and stable initial size;
* GUI entry point launches the event loop and exits normally;
* CLI entry point still imports and runs;
* application layer and conversion core stay free of Qt.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  The
#: offscreen platform keeps the focused GUI tests headless-safe; an interactive
#: session can override it by exporting ``QT_QPA_PLATFORM``.
#:
#: This is set here rather than in a directory ``conftest.py`` on purpose: the
#: test tree is not a package, so a second ``conftest`` module would shadow the
#: shared ``md_converter/tests/conftest.py`` for ``from conftest import ...``
#: users (``test_golden.py``).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APPLICATION_DIR = PROJECT_ROOT / "md_converter" / "application"

#: Modules that must never depend on the GUI framework (WP-P12-04-01 §6/§7).
GUI_FREE_MODULES = (
    "md_converter/cli.py",
    "md_converter/compiler.py",
    "md_converter/config.py",
    "md_converter/quality_gate.py",
)

_GUI_MODULE_SENTINEL = "GUI_MODULES="


@pytest.fixture(scope="session")
def qapp():
    """Return the process-wide ``QApplication`` used by GUI tests."""
    from md_converter.gui.app import create_application

    return create_application([])


@pytest.fixture(scope="session")
def main_window_class():
    """Return ``MainWindow`` (imported lazily so Qt stays optional)."""
    from md_converter.gui.main_window import MainWindow

    return MainWindow


def _run_python(code: str) -> subprocess.CompletedProcess:
    """Run ``code`` in a fresh interpreter of the active virtual environment."""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        timeout=180,
    )


# ============================================================
# Import / construction
# ============================================================


def test_gui_modules_import_successfully() -> None:
    """The GUI package and its modules import."""
    import md_converter.gui
    import md_converter.gui.app
    import md_converter.gui.main_window

    assert md_converter.gui.MainWindow is md_converter.gui.main_window.MainWindow


def test_qapplication_is_constructed_once(qapp) -> None:
    """``create_application`` returns the single process QApplication."""
    from PySide6.QtWidgets import QApplication

    from md_converter.gui.app import APPLICATION_NAME, create_application

    assert isinstance(qapp, QApplication)
    assert QApplication.instance() is qapp
    assert create_application([]) is qapp
    assert qapp.applicationName() == APPLICATION_NAME


def test_main_window_can_be_instantiated(qapp, main_window_class) -> None:
    """MainWindow has a central widget, a layout and placeholder content."""
    from PySide6.QtWidgets import QLabel, QMainWindow

    window = main_window_class()
    try:
        assert isinstance(window, QMainWindow)
        central = window.centralWidget()
        assert central is not None
        assert central.layout() is not None

        placeholder = window.findChild(QLabel, "placeholderLabel")
        assert placeholder is not None
        assert placeholder.text().strip()
    finally:
        window.close()


def test_window_title_is_correct(qapp, main_window_class) -> None:
    """The window carries the product title."""
    from md_converter.gui.main_window import WINDOW_TITLE

    window = main_window_class()
    try:
        assert WINDOW_TITLE == "MD Converter"
        assert window.windowTitle() == WINDOW_TITLE
    finally:
        window.close()


def test_window_has_stable_initial_size(qapp, main_window_class) -> None:
    """The initial size is stable and above the configured minimum."""
    from PySide6.QtCore import QSize

    from md_converter.gui.main_window import WINDOW_HEIGHT, WINDOW_WIDTH

    first = main_window_class()
    second = main_window_class()
    try:
        assert first.size() == QSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        assert second.size() == first.size()
        assert first.minimumWidth() <= first.width()
        assert first.minimumHeight() <= first.height()
        assert first.minimumWidth() > 0 and first.minimumHeight() > 0
    finally:
        first.close()
        second.close()


def test_window_shows_and_closes_without_exception(qapp, main_window_class) -> None:
    """Show, process events, close, and stay closed - without raising."""
    window = main_window_class()
    window.show()
    qapp.processEvents()
    assert window.isVisible()

    window.close()
    qapp.processEvents()
    assert not window.isVisible()


# ============================================================
# Entry points
# ============================================================


def test_gui_entry_point_launches_event_loop_and_exits() -> None:
    """The bootstrap entry point runs QApplication -> MainWindow -> exec -> exit."""
    code = "\n".join(
        [
            "import os",
            "os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')",
            "from PySide6.QtCore import QTimer",
            "from md_converter.gui.app import create_application, main",
            "app = create_application([])",
            "QTimer.singleShot(0, app.quit)",
            "exit_code = main([])",
            "print('EXIT_CODE=%d' % exit_code)",
        ]
    )

    proc = _run_python(code)

    assert proc.returncode == 0, proc.stderr
    assert "EXIT_CODE=0" in proc.stdout


def test_gui_package_is_runnable_as_module() -> None:
    """``python -m md_converter.gui`` resolves and starts without error."""
    code = "\n".join(
        [
            "import runpy, os",
            "os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')",
            "from PySide6.QtCore import QTimer",
            "from md_converter.gui.app import create_application",
            "app = create_application([])",
            "QTimer.singleShot(0, app.quit)",
            "try:",
            "    runpy.run_module('md_converter.gui', run_name='__main__')",
            "except SystemExit as exc:",
            "    print('EXIT_CODE=%s' % exc.code)",
        ]
    )

    proc = _run_python(code)

    assert proc.returncode == 0, proc.stderr
    assert "EXIT_CODE=0" in proc.stdout


def test_cli_entry_point_still_imports_and_runs() -> None:
    """The CLI front end is untouched and still works (WP-P12-04-01 §7)."""
    from click.testing import CliRunner

    from md_converter.cli import main as cli_main

    result = CliRunner().invoke(cli_main, ["--help"])

    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output


# ============================================================
# Dependency boundary
# ============================================================


def test_application_layer_source_has_no_qt_dependency() -> None:
    """``md_converter/application`` must not reference a GUI framework."""
    modules = sorted(APPLICATION_DIR.glob("*.py"))

    assert modules
    for module in modules:
        text = module.read_text(encoding="utf-8")
        assert "PySide6" not in text, module.name
        assert "PyQt" not in text, module.name


def test_application_layer_import_loads_no_qt_module() -> None:
    """Importing the application layer must not pull Qt into the process."""
    code = "\n".join(
        [
            "import sys",
            "import md_converter.application",
            "names = {'PySide6', 'PyQt5', 'PyQt6'}",
            "loaded = sorted(n for n in sys.modules if n.split('.')[0] in names)",
            "print('" + _GUI_MODULE_SENTINEL + "' + ','.join(loaded))",
        ]
    )

    proc = _run_python(code)

    assert proc.returncode == 0, proc.stderr
    sentinel_lines = [
        line for line in proc.stdout.splitlines() if line.startswith(_GUI_MODULE_SENTINEL)
    ]
    assert sentinel_lines == [_GUI_MODULE_SENTINEL]


def test_core_and_cli_modules_stay_gui_free() -> None:
    """The GUI layer boundary does not leak into CLI or conversion core."""
    for relative in GUI_FREE_MODULES:
        text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        assert "PySide6" not in text, relative
        assert "PyQt" not in text, relative
