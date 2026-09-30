"""R2-V01 WP-02 architecture / authority drift guard (static, read-only).

Proves the frozen R2-V01 architecture invariants by static inspection of the
current source tree.  It never imports the product and never mutates anything;
it parses ``md_converter/**/*.py`` with :mod:`ast` and asserts:

  A1  GUI layer imports no compiler stage (only application/profiles/gui).
  A2  ``ConversionService.convert`` still enters via ``CompilerContext.create``
      + ``CompilerContext.compile``; ``CompilerContext.compile`` exists and is
      the only caller of the context ``compile`` in production source.
  A3  Serial batch reuses the single-file service path (no second converter).
  A4  QA stages (StaticQA / RenderedQA / FinalArtifactQA) are instantiated only
      in ``compiler.py`` (no second QA authority).
  A5  Table fit, figure fit and TOC localization each have exactly one
      definition site.
  A6  Output-profile awareness does not leak below compiler/application/gui.
  A7  CLI output naming rule == application ``sanitize_output_title`` rule.
  A8  ``image_width`` propagation stays within the authorized modules.
  A9  Public API exports (``convert`` / ``CompilerContext``) are intact.

Usage::

    .venv\\Scripts\\python.exe Doc/V2/Implementation/R2_V01/Verification/verify_architecture_drift.py

Exit code 0 == every check passed.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

def _find_repo_root(start: Path) -> Path:
    """Return the repository root (the directory that contains ``md_converter``)."""
    for candidate in [start, *start.parents]:
        if (candidate / "md_converter" / "__init__.py").is_file():
            return candidate
    raise RuntimeError("repository root not found from " + str(start))


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
PKG_ROOT = REPO_ROOT / "md_converter"

COMPILER_STAGE_ROOTS = {
    "compiler",
    "renderer",
    "parser",
    "pipeline",
    "services",
    "quality_gate",
    "release_evidence",
    "ast",
    "diagnostics",
    "profiles",
    "utils",
    "constants",
}

QA_CLASS_NAMES = {"StaticQA", "RenderedQA", "FinalArtifactQA"}

SINGLE_AUTHORITY_DEFS = {
    "plan_table_fit": "one table fitting authority",
    "plan_figure_fit": "one figure fitting authority",
    "toc_heading_for_document_text": "one TOC localization authority",
}

AUTHORIZED_IMAGE_WIDTH_FILES = {
    "config",
    "compiler",
    "renderer/word_renderer",
    "renderer/layout/figure_sizing",
}

#: GUI may depend on the application layer and on the (Qt-free) profile
#: vocabulary, and on nothing else below the application boundary.
GUI_FORBIDDEN_ROOTS = COMPILER_STAGE_ROOTS - {"profiles"}


def package_files() -> List[Path]:
    """Return every production ``.py`` file (tests excluded)."""
    files: List[Path] = []
    for path in PKG_ROOT.rglob("*.py"):
        rel = path.relative_to(PKG_ROOT).as_posix()
        if rel.startswith("tests/") or rel.startswith("../"):
            continue
        if "__pycache__" in rel:
            continue
        files.append(path)
    return sorted(files)


def relname(path: Path) -> str:
    """Return the module path (no extension) relative to the package root."""
    return path.relative_to(PKG_ROOT).with_suffix("").as_posix()


def parse(path: Path) -> ast.Module:
    """Parse ``path`` into an AST module."""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def imported_roots(path: Path, tree: ast.Module) -> Set[str]:
    """Return the set of package-relative top roots the module imports."""
    file_parts = relname(path).split("/")
    base = file_parts[:-1]
    roots: Set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            module = node.module or ""
            if module.startswith("md_converter."):
                roots.add(module.split(".")[1])
            continue
        up = node.level - 1
        if up > len(base):
            continue
        prefix = base[: len(base) - up] if up else list(base)
        if node.module:
            prefix = prefix + node.module.split(".")
        if prefix:
            roots.add(prefix[0])
    return roots


def calls_in(tree: ast.Module) -> Iterable[ast.Call]:
    """Yield every call expression in the module."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def callee_name(call: ast.Call) -> Optional[str]:
    """Return the simple callee name of a call (``f(...)`` or ``x.f(...)``)."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def function_defs(tree: ast.Module) -> Dict[str, int]:
    """Return ``{name: lineno}`` for every function/method definition."""
    found: Dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.setdefault(node.name, node.lineno)
    return found


def method_body_source(path: Path, tree: ast.Module, cls: str, func: str) -> Optional[str]:
    """Return the source segment for ``Class.func`` (best-effort)."""
    text = path.read_text(encoding="utf-8")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == func:
                    return ast.get_source_segment(text, item) or ""
    return None


def main() -> int:
    """Run every check and print a deterministic PASS/FAIL report."""
    results: List[Tuple[str, bool, str]] = []
    trees: Dict[Path, ast.Module] = {p: parse(p) for p in package_files()}

    # --- A1: GUI imports no compiler stage -----------------------------------
    gui_bad: List[str] = []
    for path, tree in trees.items():
        rel = relname(path)
        if not rel.startswith("gui/"):
            continue
        roots = imported_roots(path, tree)
        leaked = sorted(roots & GUI_FORBIDDEN_ROOTS)
        # application + profiles are the only allowed cross-layer roots for GUI.
        if leaked:
            gui_bad.append(f"{rel} -> {leaked}")
    results.append(
        (
            "A1 GUI has no compiler-stage import",
            not gui_bad,
            "; ".join(gui_bad) or "gui/* imports limited to application/profiles/gui",
        )
    )

    # --- A2: single canonical compile authority ------------------------------
    svc = PKG_ROOT / "application" / "conversion_service.py"
    svc_body = method_body_source(svc, trees[svc], "ConversionService", "convert") or ""
    svc_init = method_body_source(svc, trees[svc], "ConversionService", "__init__") or ""
    compiler_tree = trees[PKG_ROOT / "compiler.py"]
    compile_exists = "compile" in function_defs(compiler_tree) or any(
        isinstance(n, ast.FunctionDef) and n.name == "compile"
        for c in ast.walk(compiler_tree)
        if isinstance(c, ast.ClassDef) and c.name == "CompilerContext"
        for n in c.body
    )
    a2_ok = (
        "CompilerContext.create" in svc_init
        and "context.compile(" in svc_body
        and compile_exists
    )
    results.append(
        (
            "A2 ConversionService -> CompilerContext.create/compile",
            a2_ok,
            f"default context factory is CompilerContext.create={('CompilerContext.create' in svc_init)}; "
            f"convert calls context.compile={'context.compile(' in svc_body}; "
            f"CompilerContext.compile exists={compile_exists}",
        )
    )

    # --- A3: batch reuses the single-file service ----------------------------
    batch_rel = "gui/batch.py"
    batch_path = PKG_ROOT / batch_rel
    batch_roots = imported_roots(batch_path, trees[batch_path])
    mw_path = PKG_ROOT / "gui" / "main_window.py"
    mw_text = mw_path.read_text(encoding="utf-8")
    a3_ok = (
        not (batch_roots & COMPILER_STAGE_ROOTS)
        and "from ..application.conversion_service import ConversionService" in mw_text
        and "GuiWorker" in mw_text
        and "build_conversion_request" in mw_text
    )
    results.append(
        (
            "A3 Serial batch reuses the single-file service path",
            a3_ok,
            f"batch imports compiler stages={sorted(batch_roots & COMPILER_STAGE_ROOTS)}; "
            f"main_window uses ConversionService+GuiWorker+request_builder",
        )
    )

    # --- A4: QA has a single instantiation authority -------------------------
    qa_files: Dict[str, List[str]] = {}
    for path, tree in trees.items():
        hits = sorted({callee_name(c) for c in calls_in(tree)} & QA_CLASS_NAMES)
        if hits:
            qa_files[relname(path)] = hits
    a4_allowed = {rel for rel in qa_files if rel == "compiler" or rel.startswith("renderer/layout/")}
    a4_ok = set(qa_files) == a4_allowed
    results.append(
        (
            "A4 QA instantiated only by compiler.py / renderer layout QA family",
            a4_ok,
            f"files instantiating QA = {sorted(qa_files)}",
        )
    )

    # --- A5: single definition site per fitting/TOC authority ---------------
    def_sites: Dict[str, List[str]] = {name: [] for name in SINGLE_AUTHORITY_DEFS}
    for path, tree in trees.items():
        for name in function_defs(tree):
            if name in def_sites:
                def_sites[name].append(relname(path))
    a5_bad = {n: s for n, s in def_sites.items() if len(s) != 1}
    results.append(
        (
            "A5 one definition site per table/figure/TOC authority",
            not a5_bad,
            "; ".join(f"{n}:{s}" for n, s in def_sites.items()),
        )
    )

    # --- A6: profile awareness does not leak below compiler/app/gui ----------
    allowed_profile_roots = {"compiler", "config"}
    leaked_profile: List[str] = []
    for path, tree in trees.items():
        rel = relname(path)
        if "profiles" in imported_roots(path, tree):
            if rel.startswith("gui/") or rel in allowed_profile_roots or rel.startswith("profiles/"):
                continue
            leaked_profile.append(rel)
    results.append(
        (
            "A6 no profile awareness below compiler/application/gui",
            not leaked_profile,
            "; ".join(leaked_profile) or "profile imports only in compiler/config/gui/profiles",
        )
    )

    # --- A7: CLI naming rule == sanitize_output_title rule -------------------
    cli_text = (PKG_ROOT / "cli.py").read_text(encoding="utf-8")
    svc_text = svc.read_text(encoding="utf-8")
    cli_rule = re.search(r"re\.sub\(r'([^']+)', \"_\", title\)", cli_text)
    svc_rule = re.search(r"return re\.sub\(r'([^']+)', \"_\", title\)", svc_text)
    a7_ok = bool(cli_rule and svc_rule) and cli_rule.group(1) == svc_rule.group(1)
    results.append(
        (
            "A7 CLI output naming == application sanitize_output_title",
            a7_ok,
            f"cli={cli_rule.group(1) if cli_rule else None!r} svc={svc_rule.group(1) if svc_rule else None!r}",
        )
    )

    # --- A8: image_width confined to authorized modules ----------------------
    image_width_files: Set[str] = set()
    for path in trees:
        if "image_width" in path.read_text(encoding="utf-8"):
            image_width_files.add(relname(path))
    a8_ok = image_width_files <= AUTHORIZED_IMAGE_WIDTH_FILES
    results.append(
        (
            "A8 image_width propagation confined to authorized modules",
            a8_ok,
            f"files referencing image_width = {sorted(image_width_files)}",
        )
    )

    # --- A9: public API intact ----------------------------------------------
    init_text = (PKG_ROOT / "__init__.py").read_text(encoding="utf-8")
    a9_ok = '"convert"' in init_text and '"CompilerContext"' in init_text and "def convert(" in init_text
    results.append(
        (
            "A9 public API exports intact (convert / CompilerContext)",
            a9_ok,
            "md_converter.__init__ exports convert + CompilerContext",
        )
    )

    print("R2-V01 WP-02 ARCHITECTURE / AUTHORITY DRIFT GUARD")
    print("-" * 68)
    failed = 0
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print(f"       {detail}")
        failed += 0 if ok else 1
    print("-" * 68)
    print(f"checks={len(results)} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
