"""
Configuration Module - 配置加载和管理
"""

import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# ============================================================
# 默认配置
# ============================================================

DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": "output",
    "verbose": False,
    "normalize": True,
    "diagram": True,
    "ascii_to_mermaid": {
        "enabled": True,
        "mode": "auto",  # auto | interactive | preview
        "confidence_threshold": 0.30,
        "preview_dir": "output/ascii_preview",
    },
    "theme": "default",
    "toc": True,
    "toc_depth": 3,
    "enable_cover": True,
    "style_tables": True,
    "frontmatter": True,
    "smart_quotes": True,
    "footnotes": True,
    "table_style": "Table Grid",
    "code_highlight": True,
    "image_width": 5,  # inches
    "quality_gate": {
        "fail_on_error": True,
        "fail_on_warning": False,
        "max_repair_iterations": 2,
    },
    "page_width": "A4",
    "page_margins": {
        "top": 2.5,
        "bottom": 2.5,
        "left": 2.5,
        "right": 2.5,
    },
}


def resolve_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return validated compiler configuration with defaults applied."""
    config = deepcopy(DEFAULT_CONFIG)
    if overrides:
        _merge_config(config, overrides)
        _apply_governance_aliases(config, overrides)

    errors = validate_config(config)
    if errors:
        raise ValueError("Invalid compiler configuration: " + "; ".join(errors))
    return config


# ============================================================
# 配置数据结构
# ============================================================


@dataclass
class PageMargins:
    """页面边距配置"""

    top: float = 2.5
    bottom: float = 2.5
    left: float = 2.5
    right: float = 2.5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageMargins":
        return cls(
            top=data.get("top", 2.5),
            bottom=data.get("bottom", 2.5),
            left=data.get("left", 2.5),
            right=data.get("right", 2.5),
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "top": self.top,
            "bottom": self.bottom,
            "left": self.left,
            "right": self.right,
        }


@dataclass
class CompilerConfig:
    """编译器完整配置"""

    output_dir: str = "output"
    verbose: bool = False
    normalize: bool = True
    diagram: bool = True
    theme: str = "default"
    toc: bool = DEFAULT_CONFIG["toc"]
    toc_depth: int = 3
    enable_cover: bool = DEFAULT_CONFIG["enable_cover"]
    style_tables: bool = DEFAULT_CONFIG["style_tables"]
    frontmatter: bool = True
    smart_quotes: bool = True
    footnotes: bool = True
    table_style: str = "Table Grid"
    code_highlight: bool = True
    image_width: int = 5
    page_width: str = "A4"
    page_margins: PageMargins = field(default_factory=PageMargins)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompilerConfig":
        """从字典创建配置对象"""
        margins_data = data.get("page_margins", {})
        margins = (
            PageMargins.from_dict(margins_data) if isinstance(margins_data, dict) else PageMargins()
        )

        # 提取已知字段
        known_fields = {
            "output_dir",
            "verbose",
            "normalize",
            "diagram",
            "theme",
            "toc",
            "toc_depth",
            "enable_cover",
            "style_tables",
            "frontmatter",
            "smart_quotes",
            "footnotes",
            "table_style",
            "code_highlight",
            "image_width",
            "page_width",
            "page_margins",
        }

        # 分离额外字段
        extra = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            output_dir=data.get("output_dir", "output"),
            verbose=data.get("verbose", False),
            normalize=data.get("normalize", True),
            diagram=data.get("diagram", True),
            theme=data.get("theme", "default"),
            toc=data.get("toc", DEFAULT_CONFIG["toc"]),
            toc_depth=data.get("toc_depth", 3),
            enable_cover=data.get("enable_cover", DEFAULT_CONFIG["enable_cover"]),
            style_tables=data.get("style_tables", DEFAULT_CONFIG["style_tables"]),
            frontmatter=data.get("frontmatter", True),
            smart_quotes=data.get("smart_quotes", True),
            footnotes=data.get("footnotes", True),
            table_style=data.get("table_style", "Table Grid"),
            code_highlight=data.get("code_highlight", True),
            image_width=data.get("image_width", 5),
            page_width=data.get("page_width", "A4"),
            page_margins=margins,
            extra=extra,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "output_dir": self.output_dir,
            "verbose": self.verbose,
            "normalize": self.normalize,
            "diagram": self.diagram,
            "theme": self.theme,
            "toc": self.toc,
            "toc_depth": self.toc_depth,
            "enable_cover": self.enable_cover,
            "style_tables": self.style_tables,
            "frontmatter": self.frontmatter,
            "smart_quotes": self.smart_quotes,
            "footnotes": self.footnotes,
            "table_style": self.table_style,
            "code_highlight": self.code_highlight,
            "image_width": self.image_width,
            "page_width": self.page_width,
            "page_margins": self.page_margins.to_dict(),
        }
        result.update(self.extra)
        return result


# ============================================================
# 配置加载函数
# ============================================================


def load_config(
    path: Optional[Union[str, Path]] = None, defaults: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    加载 YAML 配置文件，与默认配置合并。

    参数:
        path: 配置文件路径（可选）
        defaults: 默认配置字典（可选）

    返回:
        Dict[str, Any]: 合并后的配置字典

    示例:
        >>> config = load_config("config.yaml")
        >>> output_dir = config.get("output_dir", "output")
    """
    if defaults is None:
        defaults = deepcopy(DEFAULT_CONFIG)

    config = deepcopy(defaults)

    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
            if user_config and isinstance(user_config, dict):
                # 递归合并（覆盖默认值）
                _merge_config(config, user_config)
                _apply_governance_aliases(config, user_config)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {path}: {e}")

    errors = validate_config(config)
    if errors:
        raise ValueError("Invalid compiler configuration: " + "; ".join(errors))
    return config


def _merge_config(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    递归合并配置字典（原地修改 target）。

    参数:
        target: 目标字典（将被修改）
        source: 源字典（覆盖 target 中相同的键）
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            _merge_config(target[key], value)
        else:
            # 直接覆盖
            target[key] = value


def _apply_governance_aliases(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    将顶层兼容键（fail_on_error / fail_on_warning / max_repair_iterations）
    归一化到 quality_gate 配置节。

    仅当用户在 source 中未显式提供 quality_gate 节时生效，
    避免默认 quality_gate 节遮蔽用户顶层配置。
    """
    if "quality_gate" in source:
        return
    section = target.setdefault("quality_gate", {})
    for key in ("fail_on_error", "fail_on_warning", "max_repair_iterations"):
        if key in source:
            section[key] = source[key]


def load_config_object(path: Optional[Union[str, Path]] = None) -> CompilerConfig:
    """
    加载配置文件并返回 CompilerConfig 对象。

    参数:
        path: 配置文件路径（可选）

    返回:
        CompilerConfig: 类型安全的配置对象
    """
    config_dict = load_config(path)
    return CompilerConfig.from_dict(config_dict)


def save_config(path: Union[str, Path], config: Union[Dict[str, Any], CompilerConfig]) -> None:
    """
    保存配置到 YAML 文件。

    参数:
        path: 输出文件路径
        config: 配置字典或 CompilerConfig 对象
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(config, CompilerConfig):
        config_dict = config.to_dict()
    else:
        config_dict = deepcopy(config)

    with open(path_obj, "w", encoding="utf-8") as f:
        yaml.dump(
            config_dict,
            f,
            default_flow_style=False,
            allow_unicode=True,
            indent=2,
        )


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取配置值，支持点号分隔的嵌套键。

    参数:
        config: 配置字典
        key: 键名，支持点号分隔，如 "page_margins.top"
        default: 默认值

    返回:
        Any: 配置值

    示例:
        >>> config = {"page_margins": {"top": 2.5}}
        >>> top = get_config_value(config, "page_margins.top", 1.0)
        >>> print(top)  # 2.5
    """
    keys = key.split(".")
    current = config
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    return current


def set_config_value(config: Dict[str, Any], key: str, value: Any) -> None:
    """
    设置配置值，支持点号分隔的嵌套键。

    参数:
        config: 配置字典（将被修改）
        key: 键名，支持点号分隔，如 "page_margins.top"
        value: 要设置的值

    示例:
        >>> config = {}
        >>> set_config_value(config, "page_margins.top", 3.0)
        >>> print(config)  # {"page_margins": {"top": 3.0}}
    """
    keys = key.split(".")
    current = config
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value


# ============================================================
# 环境变量支持
# ============================================================


def load_config_from_env(prefix: str = "MD_") -> Dict[str, Any]:
    """
    从环境变量加载配置。

    环境变量格式: MD_OUTPUT_DIR, MD_VERBOSE, MD_THEME 等。
    支持嵌套键，用双下划线表示点号: MD_PAGE_MARGINS__TOP

    参数:
        prefix: 环境变量前缀

    返回:
        Dict[str, Any]: 从环境变量提取的配置
    """
    config = {}
    env_vars = {k: v for k, v in os.environ.items() if k.startswith(prefix)}

    for key, value in env_vars.items():
        # 移除前缀
        config_key = key[len(prefix) :]
        # 转换双下划线为点号（嵌套键）
        config_key = config_key.replace("__", ".")
        # 解析值类型
        parsed_value = _parse_env_value(value)
        set_config_value(config, config_key, parsed_value)

    return config


def _parse_env_value(value: str) -> Any:
    """
    解析环境变量的值，自动转换为合适的类型。

    支持的类型:
        - "true"/"false" → bool
        - 数字 → int/float
        - JSON 数组 → list
        - 其他 → str
    """
    # 布尔值
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    # 数字
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # JSON 数组（简单格式）
    if value.startswith("[") and value.endswith("]"):
        try:
            import json

            return json.loads(value)
        except json.JSONDecodeError:
            pass

    return value


# ============================================================
# 配置验证
# ============================================================


def validate_config(config: Dict[str, Any]) -> list:
    """
    验证配置的有效性。

    参数:
        config: 配置字典

    返回:
        list: 错误信息列表，空列表表示配置有效
    """
    errors = []

    # 验证 output_dir
    output_dir = config.get("output_dir", "output")
    if not isinstance(output_dir, str):
        errors.append("output_dir must be a string")

    # 验证 toc_depth
    toc_depth = config.get("toc_depth", 3)
    if not isinstance(toc_depth, int) or toc_depth < 1 or toc_depth > 6:
        errors.append("toc_depth must be an integer between 1 and 6")

    # 验证 image_width
    image_width = config.get("image_width", 5)
    if not isinstance(image_width, (int, float)) or image_width <= 0:
        errors.append("image_width must be a positive number")

    # 验证 page_margins
    margins = config.get("page_margins", {})
    if isinstance(margins, dict):
        for key in ["top", "bottom", "left", "right"]:
            val = margins.get(key, 2.5)
            if not isinstance(val, (int, float)) or val < 0:
                errors.append(f"page_margins.{key} must be a non-negative number")

    # 验证 table_style
    valid_styles = ["Table Grid", "Light Shading", "Light List", "Light Grid", "Medium Shading 1"]
    table_style = config.get("table_style", "Table Grid")
    if table_style and table_style not in valid_styles:
        errors.append(f"table_style must be one of: {', '.join(valid_styles)}")

    # 验证 quality_gate
    quality_gate = config.get("quality_gate", {})
    if not isinstance(quality_gate, dict):
        errors.append("quality_gate must be a mapping")
    else:
        max_repair_iterations = quality_gate.get("max_repair_iterations", 2)
        if (
            not isinstance(max_repair_iterations, int)
            or isinstance(max_repair_iterations, bool)
            or max_repair_iterations < 0
        ):
            errors.append("quality_gate.max_repair_iterations must be a non-negative integer")
        for key in ("fail_on_error", "fail_on_warning"):
            if key in quality_gate and not isinstance(quality_gate[key], bool):
                errors.append(f"quality_gate.{key} must be a boolean")

    return errors
