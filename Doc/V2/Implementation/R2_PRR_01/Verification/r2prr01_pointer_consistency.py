"""R2-PRR-01 release-evidence pointer consistency check (verification-only).

Read-only.  It verifies that:

1. the Markdown pointer and the JSON pointer carry identical facts
   (version, commit anchors, artifact identities, canonical mapping, status);
2. every referenced current-authority evidence path exists;
3. the frozen artifact identities still match the pointer
   (packaged EXE, installer, THIRD_PARTY_NOTICES.txt);
4. the historical generated release evidence and the frozen R2-RC-02 evidence
   are byte-unchanged against the pre-task baseline recorded by this gate.

Usage:
    python r2prr01_pointer_consistency.py [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
POINTER_MD = REPO_ROOT / "RC_EVIDENCE" / "CURRENT_RELEASE_EVIDENCE_POINTER.md"
POINTER_JSON = REPO_ROOT / "RC_EVIDENCE" / "current_release_evidence_pointer.json"
#: Frozen R2-RC-02 manifest that the pointer must match exactly.
FROZEN_MANIFEST = REPO_ROOT / "Doc" / "V2" / "Implementation" / "R2_RC_02" / "R2_RC_02_MANIFEST.md"

#: Pre-task baseline recorded by R2-PRR-01 (must remain byte-identical).
PROTECTED_BASELINE = {
    "RC_EVIDENCE/RELEASE_EVIDENCE.md": (
        "6D0108A9B9E7CF2752F90BDBBA8638B56B2DCFFA703011328B330B4CDF063DC1"
    ),
    "RC_EVIDENCE/release_evidence.json": (
        "EB5716543BC33283C48D185BF3C993665491C3D3B9504E00932DE21C59882512"
    ),
    "RC_EVIDENCE/P12_v1.1.0/RELEASE_CANDIDATE_EVIDENCE.md": (
        "B9861045DBA69A52409665AB5DC9BD1DC718048A330245E55E97D9A6FB17964F"
    ),
    "Doc/V2/Implementation/R2_RC_02/R2_RC_02_MANIFEST.md": (
        "2C646B673C2DC4265880AEFA50F746D2B24493DE06695FB401BC72695AAF0687"
    ),
    "Doc/V2/Implementation/R2_RC_02/R2_RC_02_CLOSURE_EVIDENCE.md": (
        "8C66BB2EEEAE37430DAA15F8BD4939AA674F33F4A71A9FA31467482EAA41F672"
    ),
    "Doc/V2/Implementation/R2_RC_02/Evidence/R2RC02-01_IDENTITY_RECHECK.json": (
        "C915EE7D9A81DE309D8AD858FC714327F1D2A91F4253C98A639F448538442704"
    ),
}

FACT_LINE = re.compile(r"^- (?P<key>[a-z0-9_]+): (?P<value>.+?)\s*$")


def sha256(path: Path) -> str:
    """Return the uppercase SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def json_facts(document: dict) -> dict[str, str]:
    """Flatten the JSON pointer into the Markdown fact key space."""
    artifacts = document["artifacts"]
    chain = document["release_chain"]
    return {
        "pointer_schema": document["pointer_schema"],
        "pointer_version": document["pointer_version"],
        "status": document["status"],
        "spec_mapping": " / ".join(document["canonical_spec_mapping"]),
        "product_version": document["product"]["version"],
        "r2_rc_02_freeze_commit": chain["r2_rc_02_freeze_commit"],
        "human_acceptance_commit": chain["targeted_human_acceptance_commit"],
        "ha02_closure_commit": chain["ha02_closure_commit"],
        "r2_prerc02_closure_commit": chain["r2_prerc02_closure_commit"],
        "packaged_exe_path": artifacts["packaged_exe"]["repo_relative_path"],
        "packaged_exe_absolute_path": artifacts["packaged_exe"]["absolute_path"],
        "packaged_exe_bytes": str(artifacts["packaged_exe"]["bytes"]),
        "packaged_exe_sha256": artifacts["packaged_exe"]["sha256"],
        "payload_path": artifacts["payload"]["repo_relative_path"],
        "payload_absolute_path": artifacts["payload"]["absolute_path"],
        "payload_file_count": str(artifacts["payload"]["file_count"]),
        "payload_total_bytes": str(artifacts["payload"]["total_bytes"]),
        "payload_tree_digest_sha256": artifacts["payload"]["tree_digest_sha256"],
        "installer_path": artifacts["installer"]["repo_relative_path"],
        "installer_absolute_path": artifacts["installer"]["absolute_path"],
        "installer_bytes": str(artifacts["installer"]["bytes"]),
        "installer_sha256": artifacts["installer"]["sha256"],
        "third_party_notices_path": artifacts["third_party_notices"]["repo_relative_path"],
        "third_party_notices_absolute_path": artifacts["third_party_notices"]["absolute_path"],
        "third_party_notices_bytes": str(artifacts["third_party_notices"]["bytes"]),
        "third_party_notices_sha256": artifacts["third_party_notices"]["sha256"],
    }


def markdown_facts(path: Path) -> dict[str, str]:
    """Extract the 'Canonical facts' block from the Markdown pointer."""
    facts: dict[str, str] = {}
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Canonical facts":
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            match = FACT_LINE.match(line)
            if match:
                facts[match.group("key")] = match.group("value")
    return facts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    document = json.loads(POINTER_JSON.read_text(encoding="utf-8"))
    expected = json_facts(document)
    actual = markdown_facts(POINTER_MD)

    pointer_mismatches = [
        f"{key}: md={actual.get(key)!r} json={expected[key]!r}"
        for key in sorted(set(expected) | set(actual))
        if actual.get(key) != expected.get(key)
    ]

    missing_references = [
        entry["path"]
        for entry in document["current_authority_evidence"]
        if not (REPO_ROOT / entry["path"]).exists()
    ]

    artifacts = document["artifacts"]
    artifact_mismatches = []
    for label, entry in artifacts.items():
        target = REPO_ROOT / entry["repo_relative_path"]
        if label == "payload":
            continue
        if not target.exists():
            artifact_mismatches.append(f"{label}: missing {target}")
            continue
        if sha256(target) != entry["sha256"]:
            artifact_mismatches.append(f"{label}: sha256 mismatch")
        if target.stat().st_size != entry["bytes"]:
            artifact_mismatches.append(f"{label}: size mismatch")

    changed_protected = []
    for relative, baseline in PROTECTED_BASELINE.items():
        target = REPO_ROOT / relative
        if not target.exists():
            changed_protected.append(f"{relative}: missing")
        elif sha256(target) != baseline:
            changed_protected.append(f"{relative}: modified")

    manifest_text = FROZEN_MANIFEST.read_text(encoding="utf-8")
    frozen_manifest_mismatches = [
        f"{label}: not found in frozen R2-RC-02 manifest"
        for label, value in (
            ("packaged_exe_sha256", expected["packaged_exe_sha256"]),
            ("payload_tree_digest_sha256", expected["payload_tree_digest_sha256"]),
            ("installer_sha256", expected["installer_sha256"]),
            ("third_party_notices_sha256", expected["third_party_notices_sha256"]),
        )
        if value not in manifest_text
    ]

    legacy_generated = [item for item in changed_protected if item.startswith("RC_EVIDENCE/")]
    frozen_rc = [
        item for item in changed_protected if item.startswith("Doc/V2/Implementation/R2_RC_02/")
    ]

    report = {
        "pointer_md": str(POINTER_MD),
        "pointer_json": str(POINTER_JSON),
        "fact_keys": len(expected),
        "pointer_md_json_mismatch": len(pointer_mismatches),
        "pointer_mismatch_details": pointer_mismatches,
        "missing_referenced_evidence": len(missing_references),
        "missing_reference_details": missing_references,
        "artifact_identity_mismatch": len(artifact_mismatches),
        "artifact_mismatch_details": artifact_mismatches,
        "frozen_manifest_mismatch": len(frozen_manifest_mismatches),
        "frozen_manifest_mismatch_details": frozen_manifest_mismatches,
        "legacy_generated_evidence_modifications": len(legacy_generated),
        "frozen_rc_modifications": len(frozen_rc),
        "protected_file_changes": changed_protected,
        "release_evidence_authority_ambiguity": (
            0
            if document["status"] == ("CURRENT_CANONICAL_RELEASE_EVIDENCE")
            and not pointer_mismatches
            else 1
        ),
    }
    report["result"] = (
        "PASS"
        if not any(
            report[key]
            for key in (
                "pointer_md_json_mismatch",
                "missing_referenced_evidence",
                "artifact_identity_mismatch",
                "frozen_manifest_mismatch",
                "legacy_generated_evidence_modifications",
                "frozen_rc_modifications",
                "release_evidence_authority_ambiguity",
            )
        )
        else "FAIL"
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for key, value in report.items():
            if key.endswith("_details"):
                continue
            print(f"{key}: {value}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
