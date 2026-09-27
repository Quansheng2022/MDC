# WP-P12-10-05 — RC Smoke & Integrity

**Product Baseline:** `4c02734`

## Objective
Perform only the minimum post-freeze smoke needed to prove the frozen RC is unchanged and operational.

## Before Smoke
Recompute installer size/hash/version and compare with WP-01. Any binary hash drift = STOP.

## Minimal Smoke
1. install frozen installer
2. launch app
3. verify About/version
4. convert one representative Markdown to DOCX
5. verify output exists
6. Open Document and confirm Word actually opens/reads it
7. quick Settings persistence check
8. clean close
9. uninstall
10. confirm user document preserved

Do not repeat P12-09 full matrices.

## cp1252
If binary identity is unchanged, one normal conversion on the accepted Windows environment is sufficient; do not repeat elaborate encoding investigation.

## Acceptance
Binary identity unchanged and minimal install/launch/convert/open/uninstall smoke PASS.
