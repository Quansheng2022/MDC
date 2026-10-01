"""HA-02 Mermaid rendering probe (verification-only).

Reproduces the product's Mermaid rendering path in isolation so the first
causal failure can be observed without running a full conversion.

It extracts the ```mermaid blocks from a fixture and renders them through the
same HTML + Playwright mechanism used by
``md_converter/pipeline/passes/diagram_pass.py``, reporting whether the Mermaid
runtime loaded and whether the diagram actually became an ``<svg>``.

Usage:
    python ha02_mermaid_probe.py --fixture <file.md> [--outdir <dir>]
                                 [--runtime <mermaid.min.js>] [--timeout 3000]

This script never imports or modifies product source; it only measures.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CDN_URL = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; padding: 20px; background: white; }}
        .mermaid {{ text-align: center; }}
    </style>
</head>
<body>
    <pre class="mermaid">{content}</pre>
</body>
</html>
"""

INIT_SCRIPT = """async () => {
    window.__mermaidLoaded = (typeof mermaid !== 'undefined');
    if (!window.__mermaidLoaded) { return; }
    mermaid.initialize({startOnLoad: false, theme: 'default'});
    await mermaid.run({querySelector: '.mermaid'});
}"""


def extract_mermaid_blocks(text: str) -> list[str]:
    """Return the content of every ```mermaid fenced block, in document order."""
    pattern = re.compile(
        r"^[ \t]*`{3,}[ \t]*mermaid[^\n]*\n(.*?)^[ \t]*`{3,}[ \t]*$",
        re.M | re.S,
    )
    return [m.group(1).rstrip("\n") for m in pattern.finditer(text)]


def probe(
    blocks: list[str],
    outdir: Path,
    runtime: Path | None,
    timeout_ms: int,
    offline: bool = False,
) -> dict:
    """Render each block and report the observed rendering facts."""
    from playwright.sync_api import sync_playwright

    outdir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        if offline:
            page.route(
                "**/*",
                lambda route: (
                    route.abort() if route.request.url.startswith("http") else route.continue_()
                ),
            )
        for index, block in enumerate(blocks, start=1):
            page.set_content(PAGE_TEMPLATE.format(content=block))
            if runtime is not None:
                page.add_script_tag(content=runtime.read_text(encoding="utf-8"))
            else:
                page.add_script_tag(url=CDN_URL)
            try:
                page.evaluate(INIT_SCRIPT)
            except Exception as exc:  # rendering error is reported, not raised
                page.evaluate(
                    "(message) => { window.__mermaidRunError = String(message); }",
                    str(exc),
                )
            try:
                page.wait_for_selector(".mermaid svg", timeout=timeout_ms)
            except Exception:
                page.wait_for_timeout(200)
            observed = page.evaluate("""() => {
                    const el = document.querySelector('.mermaid');
                    return {
                        mermaidLoaded: !!window.__mermaidLoaded,
                        runError: window.__mermaidRunError || null,
                        elementFound: !!el,
                        svgCount: el ? el.querySelectorAll('svg').length : 0,
                        svgGlobalCount: document.querySelectorAll('svg').length,
                        textLength: el ? el.innerText.length : 0,
                        textHead: el ? el.innerText.slice(0, 80) : null,
                    };
                }""")
            element = page.query_selector(".mermaid")
            shot = element.screenshot(type="png") if element else b""
            png = outdir / f"case_{index:02d}.png"
            png.write_bytes(shot)
            observed["block_lines"] = len(block.splitlines())
            observed["screenshot_bytes"] = len(shot)
            observed["screenshot"] = str(png)
            observed["rendered"] = bool(observed["svgCount"])
            results.append(observed)
        browser.close()
    return {
        "blocks": len(blocks),
        "runtime": str(runtime) if runtime else CDN_URL,
        "results": results,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--outdir", default="build/ha02_probe")
    parser.add_argument(
        "--runtime",
        default=None,
        help="local mermaid.min.js to inject instead of the CDN",
    )
    parser.add_argument("--timeout", type=int, default=3000)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="abort every http(s) request so only the local runtime can render",
    )
    args = parser.parse_args(argv)

    fixture = Path(args.fixture)
    blocks = extract_mermaid_blocks(fixture.read_text(encoding="utf-8"))
    if not blocks:
        print(json.dumps({"error": "no mermaid blocks found", "fixture": str(fixture)}, indent=2))
        return 2

    runtime = Path(args.runtime) if args.runtime else None
    report = probe(blocks, Path(args.outdir), runtime, args.timeout, args.offline)
    report["fixture"] = str(fixture)
    report["offline"] = bool(args.offline)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
