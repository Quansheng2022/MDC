#!/usr/bin/env python3
"""
RC Evidence Package 一致性检查（RC-EVID-01）

RC_EVIDENCE/ 是唯一正式 RC Evidence Package。本工具校验 governance 与
release 两个证据文件的关键字段是否来自同一次 RC（单 RC ID、单证据包）。

最少检查字段：
    spec_version / spec_status / regression.current /
    regression.new_failures / unauthorized_spec_changes / spec_deviations
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_MATCH_FIELDS = (
    "spec_version",
    "spec_status",
    "unauthorized_spec_changes",
    "spec_deviations",
)


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def validate_rc_package(rc_dir: Path) -> List[str]:
    """
    校验 RC Evidence Package 内部一致性。

    返回:
        List[str]: 错误列表；空列表表示一致
    """
    rc_dir = Path(rc_dir)
    governance_path = rc_dir / "governance_evidence.json"
    release_path = rc_dir / "release_evidence.json"

    errors: List[str] = []
    if not governance_path.exists():
        errors.append(f"missing {governance_path.name}")
        return errors
    if not release_path.exists():
        errors.append(f"missing {release_path.name}")
        return errors

    governance = _load_json(governance_path)
    release = _load_json(release_path)

    for field in REQUIRED_MATCH_FIELDS:
        gov_value = governance.get(field)
        rel_value = release.get(field)
        if gov_value != rel_value:
            errors.append(
                f"RC mismatch: governance.{field}={gov_value!r} != "
                f"release.{field}={rel_value!r}"
            )

    gov_current = governance.get("regression", {}).get("current")
    rel_current = release.get("regression", {}).get("current")
    if gov_current != rel_current:
        errors.append(
            f"RC mismatch: governance.regression.current={gov_current!r} != "
            f"release.regression.current={rel_current!r}"
        )

    gov_new_failures = governance.get("regression", {}).get("new_failures")
    rel_new_failures = release.get("regression", {}).get("new_failures")
    if gov_new_failures != rel_new_failures:
        errors.append(
            f"RC mismatch: governance.regression.new_failures={gov_new_failures!r} != "
            f"release.regression.new_failures={rel_new_failures!r}"
        )

    if release.get("result") != "RELEASE_ELIGIBLE":
        errors.append(f"release.result={release.get('result')!r} != RELEASE_ELIGIBLE")
    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RC Evidence Package consistency check")
    parser.add_argument(
        "--rc-dir",
        default="RC_EVIDENCE",
        help="Path to the RC Evidence package directory",
    )
    args = parser.parse_args(argv)

    errors = validate_rc_package(Path(args.rc_dir))
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        print(f"RC package internal mismatches: {len(errors)}")
        return 1
    print("RC package internal mismatches: 0")
    print("STATUS: CONSISTENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
