"""Tests for compiler configuration resolution."""

import pytest

from md_converter.config import DEFAULT_CONFIG, CompilerConfig, resolve_config
from md_converter.renderer.layout.artifact_contract import ArtifactContract


def test_resolve_config_applies_defaults_without_mutating_input() -> None:
    """Configuration overrides retain defaults and input remains unchanged."""
    overrides = {"page_margins": {"top": 1.5}, "toc": True}

    config = resolve_config(overrides)

    assert config["toc"] is True
    assert config["enable_cover"] is True
    assert config["page_margins"] == {
        "top": 1.5,
        "bottom": 2.5,
        "left": 2.5,
        "right": 2.5,
    }
    assert overrides == {"page_margins": {"top": 1.5}, "toc": True}
    assert config is not DEFAULT_CONFIG


def test_resolve_config_rejects_invalid_values() -> None:
    """Invalid overrides fail before compilation starts."""
    with pytest.raises(ValueError, match="toc_depth"):
        resolve_config({"toc_depth": 0})


def test_canonical_configuration_defaults_are_consistent() -> None:
    """
    F4.5：配置默认值唯一权威一致性测试。

    resolve_config / CompilerConfig / ArtifactContract 必须全部引用
    同一组默认值；任何一处被单独改动都会导致本测试失败。
    """
    resolved = resolve_config({})
    compiler_config = CompilerConfig.from_dict({})

    assert compiler_config.toc == resolved["toc"]
    assert compiler_config.enable_cover == resolved["enable_cover"]
    assert compiler_config.style_tables == resolved["style_tables"]

    contract = ArtifactContract.from_config(resolved)
    assert contract.toc_required == resolved["toc"]
    assert contract.cover_required == resolved["enable_cover"]
    assert contract.table_styling_required == resolved["style_tables"]

    # 默认值必须落在 DEFAULT_CONFIG 唯一来源上
    assert resolved["toc"] == DEFAULT_CONFIG["toc"]
    assert resolved["enable_cover"] == DEFAULT_CONFIG["enable_cover"]
    assert resolved["style_tables"] == DEFAULT_CONFIG["style_tables"]


def test_artifact_contract_has_no_implicit_defaults() -> None:
    """
    C2.6：ArtifactContract 不携带隐式默认值。

    直接 ``ArtifactContract()`` 必须 TypeError；
    默认值唯一来源只能是 DEFAULT_CONFIG（经 resolve_config 注入）。
    """
    with pytest.raises(TypeError):
        ArtifactContract()  # type: ignore[call-arg]


def test_artifact_contract_matches_resolved_config() -> None:
    """C2.6：ArtifactContract 与 resolved config 完全一致。"""
    cfg = resolve_config({})
    contract = ArtifactContract.from_config(cfg)

    assert contract.cover_required == cfg["enable_cover"]
    assert contract.toc_required == cfg["toc"]
    assert contract.table_styling_required == cfg["style_tables"]


def test_artifact_contract_respects_explicit_overrides() -> None:
    """C2.7：显式 override 必须传导到 ArtifactContract。"""
    cfg = resolve_config(
        {
            "enable_cover": False,
            "toc": False,
            "style_tables": False,
        }
    )
    contract = ArtifactContract.from_config(cfg)

    assert contract.cover_required is False
    assert contract.toc_required is False
    assert contract.table_styling_required is False
