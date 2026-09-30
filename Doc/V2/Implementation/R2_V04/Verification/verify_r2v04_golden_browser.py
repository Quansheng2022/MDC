"""R2-V04 targeted Golden/browser verification.

Verification-only script for R2-V04 (WP-R2V04-02). It does not modify product
source, Golden baselines, comparison semantics, or test behavior.

It produces machine-readable evidence for:
    - canonical Golden/browser environment status;
    - frozen Golden baseline identity (sha256 of the reference artifact);
    - the exact previously blocked Golden check, evaluated with the existing
      frozen comparison method (``GoldenTest.compare``);
    - Golden drift count and backend attribution.

Usage:
    python Doc/V2/Implementation/R2_V04/Verification/verify_r2v04_golden_browser.py \
        --out <path.json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[5]
TESTS_DIR = PROJECT_ROOT / "md_converter" / "tests"
GOLDEN_DIR = TESTS_DIR / "golden"
REFERENCE_ARTIFACT = GOLDEN_DIR / "sample.expected.json"


def _sha256(path: Path) -> str:
    """Return the sha256 hex digest of ``path``."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    """Run a read-only git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def main() -> int:
    """Run the R2-V04 targeted verification and emit JSON evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if str(TESTS_DIR) not in sys.path:
        sys.path.insert(0, str(TESTS_DIR))

    from test_golden import GoldenTest

    from md_converter.tests.golden_environment import inspect_golden_environment

    baseline_sha_before = _sha256(REFERENCE_ARTIFACT)

    status = inspect_golden_environment()
    env = status.to_dict()

    golden = GoldenTest.from_golden_dir("sample", GOLDEN_DIR)
    expected = golden.load_expected() or {}
    differences = golden.compare()
    actual = golden._actual or {}

    baseline_sha_after = _sha256(REFERENCE_ARTIFACT)

    payload: Dict[str, Any] = {
        "task": "R2-V04",
        "wp": "WP-R2V04-02",
        "git": {
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "head": _git("rev-parse", "HEAD"),
        },
        "baseline_identity": {
            "reference_artifact": str(REFERENCE_ARTIFACT.relative_to(PROJECT_ROOT)),
            "sha256_before": baseline_sha_before,
            "sha256_after": baseline_sha_after,
            "unchanged": baseline_sha_before == baseline_sha_after,
            "expected_renderer_backend": expected.get("renderer_backend"),
        },
        "environment": env,
        "golden_check": {
            "test_id": "md_converter/tests/test_golden.py::test_golden[sample]",
            "actual_renderer_backend": actual.get("renderer_backend"),
            "backend_matches_baseline": (
                actual.get("renderer_backend") == expected.get("renderer_backend")
            ),
            "drift_count": len(differences),
            "differences": differences[:20],
            "result": "PASS" if not differences else "FAIL",
        },
    }
    payload["summary"] = {
        "browser_launch": "PASS" if env.get("chromium_launchable") else "FAIL",
        "unexpected_golden_drift": len(differences),
        "golden_baseline_changed": not payload["baseline_identity"]["unchanged"],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(json.dumps(payload["summary"], indent=2))
    return 0 if payload["golden_check"]["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
