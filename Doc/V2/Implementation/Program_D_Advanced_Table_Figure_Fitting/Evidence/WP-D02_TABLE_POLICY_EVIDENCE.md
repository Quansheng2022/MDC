# WP-D02 — Table Fitting Policy

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-02 (one deterministic table fitting authority, no integration yet)
**Status:** PASS
**Baseline for this WP:** `05b05c7` (`D-01 freeze table and figure fitting architecture`)
**Specification references:** `SPEC-FUNC-004`, `SPEC-ARCH-009`, `SPEC-INV-002`, `SPEC-INV-003`,
`SPEC-INV-006`, `Program_D_Product_Specification.md` §3.1, §6.1–§6.3, §8, §9, §11.1.

---

## 1. Deliverable

| Artifact | Path | Nature |
| --- | --- | --- |
| Table fitting authority | `md_converter/renderer/layout/table_fitting.py` (new) | pure / no I/O / no Qt / no profile-ID branch |
| Focused policy tests | `md_converter/tests/test_table_fitting.py` (new) | 25 tests |

Public API:

```python
@dataclass(frozen=True)
class TableFitPlan:
    column_widths_cm: Tuple[float, ...]
    total_width_cm: float
    font_size_pt: float
    fixed_layout: bool
    filled_content_width: bool
    squeezed: bool
    min_column_width_cm: float
    def to_dict(self) -> Dict[str, Any]: ...

def column_signal_lengths(rows: Sequence[Sequence[str]]) -> Tuple[int, ...]: ...

def plan_table_fit(
    rows: Sequence[Sequence[str]],
    *,
    content_width_cm: float,
    base_font_size_pt: float,
    min_column_width_cm: float = 1.2,          # theme table.constraints.min_width
    char_width_cm: float = 0.19,               # same estimate as estimate_table_width_cm
    readability_floor_pt: float = 8.5,         # theme readability.minimum.table_font
    narrow_fill_ratio: float = 0.6,
    signal_char_cap: int = 48,
    font_step_pt: float = 0.5,
) -> TableFitPlan: ...
```

## 2. Decision algorithm (deterministic, documented)

```text
signal_i  = max visible cell character count of column i      (cheap, language-agnostic)
natural_i = clamp(signal_i, 1, signal_char_cap) x char_width, raised to min_column_width
required  = sum(natural_i)
min_total = column_count x min_column_width

1) required <= content_width
   required >= content_width x narrow_fill_ratio -> fill content width, allocate proportionally
   otherwise                                      -> keep natural width (narrow tables not stretched)
2) required >  content_width and min_total <= content_width
   -> fill content width; shrink only the part above min_column_width, proportionally
3) min_total >  content_width
   -> keep min_column_width for every column, total = min_total, squeezed = True

font = base; if squeezed: font = base - font_step_pt; font = clamp(font, readability_floor, base)
```

Property check of the algorithm against the Product Specification §6.1 preference order:

1. *Use available content width efficiently* — cases 1 (fill branch) and 2 fill the effective
   content width exactly (`Σ widths == content_width`).
2. *Proportional, not equal, allocation* — widths are always derived from `natural_i`; equal
   allocation never occurs.
3. *Allow normal Word wrapping* — no text is shortened; the renderer keeps writing complete cell
   text and Word wraps.
4. *Bounded compactness* — case 2 shrinks only the excess above the minimum column width.
5. *Bounded font reduction* — at most one `font_step_pt` (0.5pt) and never below 8.5pt.
6. *Preserve content when perfect fitting is impossible* — case 3 keeps full content, keeps the
   readability floor, and flags `squeezed` so the caller can record the limitation. No unbounded
   shrinking loop exists.

## 3. Requirement mapping

| Requirement | Status | Evidence |
| --- | --- | --- |
| deterministic | PASS | pure arithmetic; `test_repeated_planning_is_deterministic` |
| no IO / no network / no GUI | PASS | module imports only `dataclasses`/`typing` |
| no profile-ID branching | PASS | module never sees a profile; `test_profile_geometry_variation_through_resolved_width_only` |
| no content mutation | PASS | inputs are read-only `Sequence[str]`; nothing is written |
| table font floor >= 8.5pt | PASS | `test_readability_floor_is_never_violated_when_squeezed` (parametrised 9.5/9.0/8.6 base) |
| no margin weakening | PASS | margins never touched; `content_width_cm` is an input |
| no unbounded shrinking | PASS | 3 cases terminate; `min_column_width_cm` is a hard floor |
| content-aware weighting | PASS | `column_signal_lengths` + proportional allocation |
| narrow table not degraded | PASS | `test_narrow_table_is_not_expanded_to_full_width` |
| wide 8+ column table | PASS | `test_wide_table_shrinks_to_content_width_keeping_floor` |
| numeric-heavy / empty cells | PASS | `test_numeric_heavy_columns_keep_minimum_floor`, `test_empty_and_ragged_cells_never_produce_zero_width_columns` |
| fail loudly on invalid input | PASS | `test_invalid_inputs_fail_loudly` (9 parametrised cases), `test_empty_table_fails_loudly` |

`squeezed=True` is the documented "irreducible wide table" channel required by Product
Specification §6.3: the WP-D03 integration turns it into a structured diagnostic and keeps every
cell value, rather than adding landscape sections or transforming content.

## 4. Verification run (real output)

```text
$ .venv\Scripts\python.exe -m pytest md_converter/tests/test_table_fitting.py -p no:cacheprovider -q
.........................                                                [100%]
25 passed

$ .venv\Scripts\python.exe -m ruff check md_converter/renderer/layout/table_fitting.py \
      md_converter/tests/test_table_fitting.py
All checks passed!

$ .venv\Scripts\python.exe -m black --check --no-cache md_converter/renderer/layout/table_fitting.py \
      md_converter/tests/test_table_fitting.py
All done! 2 files would be left unchanged.

$ .venv\Scripts\python.exe -m isort --check-only --settings-path pyproject.toml \
      md_converter/renderer/layout/table_fitting.py md_converter/tests/test_table_fitting.py
(no output -> clean)
```

Environment note: `black` without `--no-cache` does not terminate in this sandbox because its
global cache directory is outside the writable roots. `--no-cache` is used for every Program D
lint/format check; this is an environment observation, not a code finding.

## 5. Scope discipline

Only the two files listed in §1 were created. No renderer, writer, post-processor, theme, config or
existing test was modified in this WP — integration is deferred to WP-D03 so that the policy can be
verified independently of Word objects.

## 6. WP-D02 conclusion

One deterministic, pure, profile-independent table fitting authority now exists with a documented
decision algorithm and 25 focused tests, including readability-floor protection and deterministic
repeat behaviour. No existing behaviour changed yet.

**Decision: PASS — next WP is D-03 (table renderer integration).**
