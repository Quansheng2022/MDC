"""IMG-CFG-01 contract & regression guards for ``image_width`` propagation.

These guards lock the WP-IC03 repair: the resolved ``image_width`` now reaches the
frozen figure-sizing authority (``plan_figure_fit``) through the existing
``RenderContext.config`` slot, so ``SPEC-FUNC-023`` holds end to end:

* the default behaviour is unchanged (``5 in`` -> ``12.70 cm``);
* a smaller configured width is honoured (including the small-raster case);
* a larger configured width is honoured up to the effective page cap;
* aspect ratio is preserved and the delivered geometry equals the single
  ``plan_figure_fit`` authority;
* no profile-ID branching is introduced on the image path;
* the batch (service) path and the single-file path agree;
* only ``image_width`` is propagated - the other latent ``RenderContext.config``
  keys stay dormant (zero drift).

The PNG fixtures are produced by a tiny pure-Python PNG writer, so no third-party
dependency is introduced.
"""

from __future__ import annotations

import base64
import contextlib
import io
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest
from docx import Document

from md_converter.application import (
    ConversionRequest,
    ConversionService,
    ConversionStatus,
)
from md_converter.compiler import CompilerContext
from md_converter.renderer.layout import figure_sizing
from md_converter.renderer.layout.figure_sizing import CM_PER_INCH, plan_figure_fit

#: Frozen reference geometry (A4 + 1in, SPEC-FUNC-023 CLAR-02).
CONTENT_WIDTH_CM = 21.0 - 2.54 - 2.54
CONTENT_HEIGHT_CM = 29.7 - 2.54 - 2.54

BASE_CONFIG: Dict[str, Any] = {
    "word_com": False,
    "enable_cover": False,
    "toc": False,
    "verbose": False,
}

WORLD_FIGURE = (400, 100)  # 4:1 wide raster
SMALL_FIGURE = (82, 41)  # frozen baseline fixture (2:1)


def _png_data_uri(width: int, height: int) -> str:
    """Return a deterministic solid-colour PNG data URI (no dependencies)."""
    scanline = b"\x00" + bytes((0x2F, 0x54, 0x96)) * width
    raw = scanline * height

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return (
            struct.pack(">I", len(payload))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def _body(px_width: int, px_height: int, alt: str = "figure") -> str:
    """Markdown body containing exactly one generated PNG figure."""
    return f"# Figure\n\n![{alt}]({_png_data_uri(px_width, px_height)})\n"


def _compile(
    tmp_path: Path,
    name: str,
    *,
    body: str,
    **overrides: Any,
) -> Tuple[CompilerContext, Path]:
    """Compile ``body`` through the public compiler context."""
    config = dict(BASE_CONFIG)
    config.update(overrides)
    context = CompilerContext.create(config)
    output = tmp_path / f"{name}.docx"
    with contextlib.redirect_stdout(io.StringIO()):
        context.compile(body, {"title": name}, output)
    return context, output


def _shape(path: Path):
    """Return the single inline shape of a one-figure artifact."""
    shapes = list(Document(str(path)).inline_shapes)
    assert len(shapes) == 1, f"expected exactly one figure, got {len(shapes)}"
    return shapes[0]


def _authority(px_width: int, px_height: int, configured_in: float) -> float:
    """The frozen SPEC-FUNC-023 width, resolved by the single authority."""
    target = min(configured_in * CM_PER_INCH, CONTENT_WIDTH_CM)
    return plan_figure_fit(
        intrinsic_width_px=px_width,
        intrinsic_height_px=px_height,
        target_width_cm=target,
        content_width_cm=CONTENT_WIDTH_CM,
        content_height_cm=CONTENT_HEIGHT_CM,
    ).width_cm


# ============================================================
# Wiring
# ============================================================


def test_render_context_receives_exactly_the_resolved_image_width() -> None:
    """The IC-03 repair propagates ``image_width`` and nothing else."""
    context = CompilerContext.create({**BASE_CONFIG, "image_width": 3})

    assert context.config["image_width"] == 3
    assert context.render_ctx.config == {"image_width": 3}


def test_other_latent_render_context_keys_stay_dormant() -> None:
    """``page_margins`` / ``page_width`` / ``toc_depth`` are not activated (zero drift)."""
    context = CompilerContext.create(BASE_CONFIG)

    assert context.render_ctx.config.get("page_margins") is None
    assert context.render_ctx.config.get("page_width") is None
    assert context.render_ctx.config.get("toc_depth") is None
    # toc include-depth keeps the historical fallback.
    assert context.render_ctx.toc.include_depth == 3


# ============================================================
# Contract behaviour
# ============================================================


def test_default_width_behaviour_is_unchanged(tmp_path: Path) -> None:
    """No explicit ``image_width`` keeps the accepted 12.70 cm baseline."""
    _, output = _compile(tmp_path, "default", body=_body(*SMALL_FIGURE))
    shape = _shape(output)

    assert shape.width.cm == pytest.approx(12.7, abs=0.01)
    assert shape.height.cm == pytest.approx(6.35, abs=0.01)


def test_smaller_configured_width_is_honoured(tmp_path: Path) -> None:
    """A smaller configured width must shrink the delivered figure."""
    _, output = _compile(tmp_path, "smaller", body=_body(*WORLD_FIGURE), image_width=2)
    shape = _shape(output)

    assert shape.width.cm == pytest.approx(5.08, abs=0.02)
    assert shape.width.cm == pytest.approx(_authority(*WORLD_FIGURE, 2), abs=0.02)


def test_smaller_configured_width_shrinks_a_small_raster(tmp_path: Path) -> None:
    """A small raster is delivered at the configured target (never beyond it)."""
    _, output = _compile(tmp_path, "smaller_small", body=_body(*SMALL_FIGURE), image_width=2)
    shape = _shape(output)

    assert shape.width.cm == pytest.approx(5.08, abs=0.02)
    assert shape.width.cm <= 2 * CM_PER_INCH + 0.02


def test_larger_configured_width_within_bounds_is_honoured(tmp_path: Path) -> None:
    """A larger configured width grows the figure while it fits the page."""
    _, output = _compile(tmp_path, "larger", body=_body(*WORLD_FIGURE), image_width=6)
    shape = _shape(output)

    assert shape.width.cm == pytest.approx(15.24, abs=0.02)
    assert shape.width.cm <= CONTENT_WIDTH_CM


@pytest.mark.parametrize("configured_in", [8, 20])
def test_configured_width_is_capped_by_the_effective_page_width(
    tmp_path: Path, configured_in: int
) -> None:
    """The effective content width still caps an over-wide target."""
    _, output = _compile(
        tmp_path, f"capped_{configured_in}", body=_body(*WORLD_FIGURE), image_width=configured_in
    )
    shape = _shape(output)

    assert shape.width.cm == pytest.approx(CONTENT_WIDTH_CM, abs=0.05)
    assert shape.width.cm <= CONTENT_WIDTH_CM + 0.05


@pytest.mark.parametrize("configured_in", [2, 5, 6, 8])
def test_aspect_ratio_is_preserved_for_any_configured_width(
    tmp_path: Path, configured_in: float
) -> None:
    """Widening/narrowing the target never crops or stretches the figure."""
    px_w, px_h = WORLD_FIGURE
    _, output = _compile(
        tmp_path, f"aspect_{configured_in}", body=_body(px_w, px_h), image_width=configured_in
    )
    shape = _shape(output)

    assert shape.width.cm / shape.height.cm == pytest.approx(px_w / px_h, rel=0.01)


@pytest.mark.parametrize("configured_in", [2, 5, 6, 8, 20])
def test_delivered_geometry_equals_the_single_sizing_authority(
    tmp_path: Path, configured_in: float
) -> None:
    """The artifact matches ``plan_figure_fit`` exactly -> sole authority holds."""
    px_w, px_h = WORLD_FIGURE
    _, output = _compile(
        tmp_path,
        f"authority_{configured_in}",
        body=_body(px_w, px_h),
        image_width=configured_in,
    )
    shape = _shape(output)

    assert shape.width.cm == pytest.approx(_authority(px_w, px_h, configured_in), abs=0.02)


# ============================================================
# Layer / branching guards
# ============================================================


def _source(relative: str) -> str:
    """Read a module source file relative to the ``md_converter`` package root."""
    package_root = Path(figure_sizing.__file__).resolve().parents[2]
    return (package_root / relative).read_text(encoding="utf-8")


def test_figure_sizing_module_exposes_one_plan_entry_point() -> None:
    """There is a single sizing authority; the legacy wrapper delegates to it."""
    source = Path(figure_sizing.__file__).read_text(encoding="utf-8")

    assert source.count("def plan_figure_fit(") == 1
    assert "plan_figure_fit(" in source.split("def fit_figure_size(")[1]


def test_no_profile_id_branching_on_the_image_path() -> None:
    """Neither the renderer nor the sizing authority branches on a profile id."""
    for relative in ("renderer/word_renderer.py", "renderer/layout/figure_sizing.py"):
        text = _source(relative)
        assert "output_profile" not in text, relative
        for profile_id in ("professional_report", "business_report", "academic", "clean_minimal"):
            assert profile_id not in text, (relative, profile_id)


@pytest.mark.parametrize("profile_id", ["professional_report", "clean_minimal"])
def test_profiles_with_equal_geometry_deliver_equal_widths(tmp_path: Path, profile_id: str) -> None:
    """Profile identity does not change the figure: only resolved geometry can."""
    _, baseline_output = _compile(
        tmp_path, "geometry_default", body=_body(*WORLD_FIGURE), image_width=6
    )
    _, output = _compile(
        tmp_path,
        f"geometry_{profile_id}",
        body=_body(*WORLD_FIGURE),
        image_width=6,
        output_profile=profile_id,
    )

    assert _shape(output).width.cm == pytest.approx(_shape(baseline_output).width.cm, abs=0.02)


# ============================================================
# Batch / single-file parity
# ============================================================


def test_batch_path_and_single_file_path_agree(tmp_path: Path, monkeypatch) -> None:
    """The service (batch worker) path honours ``image_width`` identically."""
    monkeypatch.chdir(tmp_path)

    source = tmp_path / "batch_source.md"
    source.write_text(_body(*WORLD_FIGURE), encoding="utf-8")

    service = ConversionService(
        {"word_com": False, "enable_cover": False, "toc": False, "image_width": 6}
    )
    result = service.convert(ConversionRequest(source))

    assert result.status is ConversionStatus.SUCCESS
    assert result.output_path is not None and result.output_path.exists()
    batch_width = _shape(result.output_path).width.cm

    _, single_output = _compile(tmp_path, "single_parity", body=_body(*WORLD_FIGURE), image_width=6)

    assert batch_width == pytest.approx(15.24, abs=0.02)
    assert batch_width == pytest.approx(_shape(single_output).width.cm, abs=0.02)
