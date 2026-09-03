#!/usr/bin/env python3
"""
MD Converter CLI - 命令行入口
"""

import builtins
import json
import re
import sys
from pathlib import Path

import click

from .compiler import CompilerContext
from .config import load_config
from .diagnostics.diagnostic import Severity
from .release_evidence import (
    build_release_evidence,
    validate_governance_evidence,
    validate_test_evidence,
    write_release_evidence,
)
from .utils.helpers import open_docx, parse_frontmatter


def _make_interactive_selector():
    """
    创建交互式方案选择回调（用于 --ascii-mode interactive）。

    返回:
        Callable[[ConversionPlan], ConversionScheme]
    """

    def select(plan):
        click.echo("\n📊 ASCII 图转换方案：")
        for i, scheme in enumerate(plan.schemes, start=1):
            summary = ", ".join(f"{k}={v}" for k, v in scheme.summary.items())
            detail = f" [{summary}]" if summary else ""
            click.echo(f"  {i}. {scheme.diagram_type} " f"(置信度 {scheme.confidence:.2f}){detail}")
        if len(plan.schemes) == 1:
            click.echo("  按回车接受推荐方案")
        choice = click.prompt(
            "选择方案（回车=推荐）",
            type=int,
            default=1,
            show_default=False,
        )
        return plan.schemes[choice - 1]

    return select


@click.command()
@click.argument(
    "input",
    type=click.Path(exists=True, dir_okay=True, readable=True),
    required=False,
    default="input",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to YAML configuration file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=True, writable=True),
    help="Output file path (default: ./output/<title>.docx).",
)
@click.option(
    "--open/--no-open",
    default=True,
    help="Open the generated DOCX file after conversion.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed diagnostic messages.",
)
@click.option(
    "--ascii-mode",
    type=click.Choice(["auto", "interactive", "preview"]),
    default=None,
    help="ASCII diagram → Mermaid conversion mode (default: auto).",
)
@click.option(
    "--ascii-preview-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Directory for multi-scheme ASCII → Mermaid preview files.",
)
def main(
    input: str,
    config: str,
    output: str,
    open: bool,
    verbose: bool,
    ascii_mode: str,
    ascii_preview_dir: str,
) -> None:
    """
    Convert a Markdown file to a DOCX document.

    \b
    Examples:
        md-converter README.md
        md-converter doc.md --config config.yaml --output ./build/result.docx --open
        md-converter                # 默认编译 PROJECT_ROOT/input/ 下所有 .md
        md-converter input/         # 批量编译 input 目录
    """
    # 保存 open 参数值，避免与内置 open() 冲突
    open_after = open

    # 加载配置
    cfg = load_config(config)
    if verbose:
        cfg["verbose"] = True
    cfg.setdefault("output_dir", "output")
    ascii_cfg = cfg.setdefault("ascii_to_mermaid", {})
    if ascii_mode:
        ascii_cfg["mode"] = ascii_mode
    if ascii_preview_dir:
        ascii_cfg["preview_dir"] = ascii_preview_dir
    if ascii_cfg.get("mode") == "interactive":
        ascii_cfg["selector"] = _make_interactive_selector()

    # 解析输入：单文件或目录（默认 PROJECT_ROOT/input）
    input_path = Path(input)
    if input_path.is_dir():
        md_files = sorted(input_path.glob("*.md"))
        if not md_files:
            click.echo(f"❌ No Markdown files found in {input_path}", err=True)
            sys.exit(1)
    else:
        md_files = [input_path]
    single = len(md_files) == 1

    # 创建编译器上下文
    try:
        ctx = CompilerContext.create(cfg)
    except Exception as e:
        click.echo(f"❌ Failed to initialize compiler: {e}", err=True)
        sys.exit(1)

    # 逐个编译
    generated: list = []
    errors = 0
    for md_path in md_files:
        try:
            with builtins.open(md_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            click.echo(f"❌ Failed to read {md_path}: {e}", err=True)
            errors += 1
            continue

        # 解析 Frontmatter
        body, meta = parse_frontmatter(raw)
        title = meta.get("title", md_path.stem)

        # 确定输出路径
        if single and output:
            out_path = Path(output)
        else:
            safe_title = re.sub(r'[<>:"/\\|?* ]', "_", title)
            out_dir = Path(output) if (output and not single) else Path(cfg["output_dir"])
            out_path = out_dir / f"{safe_title}.docx"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            ctx.compile(body, meta, out_path)
            generated.append(out_path)
            click.echo(f"✅ Generated: {out_path}")
        except Exception as e:
            click.echo(f"❌ Compilation error ({md_path}): {e}", err=True)
            if verbose:
                import traceback

                traceback.print_exc()
            errors += 1
            continue

    # 报告诊断信息
    if ctx.diag.diagnostics:
        click.echo("\n📋 Diagnostics:")
        for d in ctx.diag.diagnostics:
            loc = f"{d.location.start_line}:{d.location.start_col}" if d.location else "unknown"
            symbol = (
                "⚠️"
                if d.severity == Severity.WARNING
                else "❌" if d.severity == Severity.ERROR else "ℹ️"
            )
            click.echo(f"  {symbol} [{d.code}] {d.message} (at {loc})")
        if any(d.severity == Severity.ERROR for d in ctx.diag.diagnostics):
            click.echo("⚠️  Conversion completed with errors.", err=True)

    if not single and generated:
        click.echo(f"✅ Generated {len(generated)} document(s) from {input_path}")

    if errors:
        click.echo(f"⚠️ {errors} file(s) failed.", err=True)
        sys.exit(1)

    # 单文件模式：按 --open 打开文档
    if single and open_after and generated and generated[0].exists():
        open_docx(generated[0])


if __name__ == "__main__":
    main()


@click.command()
@click.argument(
    "input",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to YAML configuration file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Output DOCX path (default: <output_dir>/<input stem>.docx).",
)
@click.option(
    "--test-report",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help='JSON file with test summary, e.g. {"unit": "PASS", "golden": "PASS"}.',
)
@click.option(
    "--governance-report",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="JSON file with governance evidence (governance_evidence.json).",
)
@click.option(
    "--evidence-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Directory for RELEASE_EVIDENCE.md / release_evidence.json.",
)
def release_evidence(
    input: str,
    config: str,
    output: str,
    test_report: str,
    governance_report: str,
    evidence_dir: str,
) -> None:
    """
    Compile a Markdown file and generate Release Evidence (P1-10).

    Generates RELEASE_EVIDENCE.md + release_evidence.json next to the DOCX.
    Exits with code 1 when the release decision is RELEASE_BLOCKED.

    \b
    Examples:
        md-converter-release-evidence README.md
        md-converter-release-evidence doc.md --test-report tests.json \
            --governance-report governance_evidence.json
    """
    cfg = load_config(config)
    try:
        ctx = CompilerContext.create(cfg)
    except Exception as e:
        click.echo(f"❌ Failed to initialize compiler: {e}", err=True)
        sys.exit(1)

    input_path = Path(input)
    try:
        with builtins.open(input_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        click.echo(f"❌ Failed to read {input_path}: {e}", err=True)
        sys.exit(1)

    body, meta = parse_frontmatter(raw)
    if output:
        out_path = Path(output)
    else:
        out_dir = Path(cfg.get("output_dir", "output"))
        out_path = out_dir / f"{input_path.stem}.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 证据输入先加载并校验（fail fast：报告非法则不再编译）
    tests = {}
    if test_report:
        try:
            with builtins.open(test_report, "r", encoding="utf-8") as f:
                tests = json.load(f)
        except Exception as e:
            click.echo(f"❌ Failed to read test report: {e}", err=True)
            sys.exit(1)
        test_errors = validate_test_evidence(tests)
        if test_errors:
            click.echo("❌ Invalid test report: " + "; ".join(test_errors), err=True)
            sys.exit(1)

    governance = None
    if governance_report:
        try:
            with builtins.open(governance_report, "r", encoding="utf-8") as f:
                governance = json.load(f)
        except Exception as e:
            click.echo(f"❌ Failed to read governance report: {e}", err=True)
            sys.exit(1)
        governance_errors = validate_governance_evidence(governance)
        if governance_errors:
            click.echo(
                "❌ Invalid governance report: " + "; ".join(governance_errors),
                err=True,
            )
            sys.exit(1)

    try:
        ctx.compile(body, meta, out_path)
    except Exception as e:
        click.echo(f"❌ Compilation failed: {e}", err=True)
        sys.exit(1)

    evidence = build_release_evidence(ctx, out_path, tests=tests, governance=governance)
    directory = Path(evidence_dir) if evidence_dir else out_path.parent
    md_path, json_path = write_release_evidence(evidence, directory)

    click.echo(f"✅ Release Evidence: {md_path}")
    click.echo(f"✅ {json_path}")
    click.echo(f"Result: {evidence.result}")
    if evidence.result != "RELEASE_ELIGIBLE":
        click.echo("❌ Release BLOCKED by evidence rules.", err=True)
        sys.exit(1)


@click.command()
@click.option(
    "--json-output",
    is_flag=True,
    help="Print the dependency report as JSON.",
)
def check_dependencies(json_output: bool) -> None:
    """
    Check that MD Converter runtime dependencies are installed.

    Required: click / markdown-it-py / python-docx / PyYAML.
    Optional: pywin32（Windows Word COM）/ playwright（Mermaid renderer）。

    Exit code is 0 when all required dependencies are available, 1 otherwise.

    \b
    Examples:
        md-converter-check
        md-converter-check --json-output
    """
    from importlib import metadata

    def _status(dist_name: str) -> dict:
        """Return installed/version status for one distribution."""
        try:
            version = metadata.version(dist_name)
            return {"distribution": dist_name, "installed": True, "version": version}
        except metadata.PackageNotFoundError:
            return {"distribution": dist_name, "installed": False, "version": None}

    required_names = ("click", "markdown-it-py", "python-docx", "pyyaml")
    optional_names = ("playwright", "pywin32")

    required = [_status(name) for name in required_names]
    optional = [_status(name) for name in optional_names]
    all_required_ok = all(item["installed"] for item in required)
    report = {"required": required, "optional": optional, "ok": all_required_ok}

    if json_output:
        click.echo(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for item in required:
            mark = "✅" if item["installed"] else "❌"
            version = item["version"] or "missing"
            click.echo(f"  {mark} {item['distribution']} {version}")
        for item in optional:
            mark = "✅" if item["installed"] else "⚠️"
            version = item["version"] or "not installed (optional)"
            click.echo(f"  {mark} {item['distribution']} {version}")
        if all_required_ok:
            click.echo("✅ All required dependencies are available.")
        else:
            click.echo("❌ Missing required dependencies.", err=True)

    if not all_required_ok:
        sys.exit(1)
