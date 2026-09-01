"""
Helpers - 通用工具函数

提供文件操作、Frontmatter 解析、路径处理等通用工具函数。
"""

import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import yaml

# ============================================================
# Frontmatter 解析
# ============================================================

def parse_frontmatter(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    解析 YAML Frontmatter。

    支持两种格式:
        1. 标准 YAML: --- ... ---
        2. JSON: { ... }

    参数:
        content: Markdown 文本内容

    返回:
        Tuple[str, Dict[str, Any]]: (正文内容, Frontmatter 元数据)

    示例:
        >>> content = '''---
        ... title: My Document
        ... date: 2024-01-01
        ... tags: [python, markdown]
        ... ---
        ... # Hello World
        ... '''
        >>> body, meta = parse_frontmatter(content)
        >>> meta['title']
        'My Document'
    """
    lines = content.split('\n')

    # 检查是否以 --- 或 { 开头
    if not lines:
        return content, {}

    first_line = lines[0].strip()

    # YAML Frontmatter
    if first_line == '---':
        return _parse_yaml_frontmatter(lines)

    # JSON Frontmatter
    if first_line.startswith('{'):
        return _parse_json_frontmatter(content)

    return content, {}

def _parse_yaml_frontmatter(lines: List[str]) -> Tuple[str, Dict[str, Any]]:
    """
    解析 YAML Frontmatter。

    参数:
        lines: 文本行列表

    返回:
        Tuple[str, Dict[str, Any]]: (正文内容, 元数据)
    """
    # 查找结束标记
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        # 没有结束标记，返回全文
        return '\n'.join(lines), {}

    # 提取 Frontmatter 和正文
    frontmatter_lines = lines[1:end_idx]
    body_lines = lines[end_idx + 1:]

    # 解析 YAML
    try:
        frontmatter_text = '\n'.join(frontmatter_lines)
        metadata = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        metadata = {}

    # 规范化元数据
    metadata = _normalize_metadata(metadata)

    # 移除正文开头的空行
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    return '\n'.join(body_lines), metadata

def _parse_json_frontmatter(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    解析 JSON Frontmatter。

    参数:
        content: 文本内容

    返回:
        Tuple[str, Dict[str, Any]]: (正文内容, 元数据)
    """
    import json

    # 查找第一个 } 的位置
    lines = content.split('\n')
    brace_count = 0
    end_idx = None

    for i, line in enumerate(lines):
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and i > 0:
            end_idx = i
            break

    if end_idx is None:
        return content, {}

    # 提取 JSON 和正文
    json_lines = lines[:end_idx + 1]
    body_lines = lines[end_idx + 1:]

    try:
        json_text = '\n'.join(json_lines)
        metadata = json.loads(json_text)
    except json.JSONDecodeError:
        metadata = {}

    metadata = _normalize_metadata(metadata)

    # 移除正文开头的空行
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    return '\n'.join(body_lines), metadata

def _normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    规范化元数据。

    确保元数据字段类型一致。

    参数:
        metadata: 原始元数据

    返回:
        Dict[str, Any]: 规范化后的元数据
    """
    normalized = {}

    for key, value in metadata.items():
        # 处理日期类型
        if key == 'date' and hasattr(value, 'isoformat'):
            normalized[key] = value.isoformat()
        elif key == 'date':
            normalized[key] = str(value)

        # 处理标签
        elif key == 'tags':
            if isinstance(value, list):
                normalized[key] = [str(t) for t in value if t]
            elif isinstance(value, str):
                if value.startswith('[') and value.endswith(']'):
                    # 字符串列表格式: [tag1, tag2]
                    tags = [t.strip().strip('"\'') for t in value[1:-1].split(',') if t.strip()]
                    normalized[key] = tags
                else:
                    normalized[key] = [value] if value else []
            else:
                normalized[key] = [str(value)] if value else []

        # 标题
        elif key == 'title':
            normalized[key] = str(value)

        # 作者
        elif key in ('author', 'authors'):
            if isinstance(value, list):
                normalized[key] = [str(a) for a in value]
            else:
                normalized[key] = [str(value)] if value else []

        # 其他字段
        else:
            normalized[key] = value

    return normalized

def get_frontmatter_value(
    metadata: Dict[str, Any],
    key: str,
    default: Any = None
) -> Any:
    """
    安全获取 Frontmatter 值。

    参数:
        metadata: Frontmatter 元数据
        key: 键名
        default: 默认值

    返回:
        Any: 值
    """
    return metadata.get(key, default)

def has_frontmatter(content: str) -> bool:
    """
    检查文本是否包含 Frontmatter。

    参数:
        content: 文本内容

    返回:
        bool: 是否包含 Frontmatter
    """
    lines = content.split('\n')
    if not lines:
        return False

    first_line = lines[0].strip()
    return first_line == '---' or first_line.startswith('{')

# ============================================================
# 文件操作
# ============================================================

def ensure_directory(path: Path) -> Path:
    """
    确保目录存在。

    参数:
        path: 目录路径

    返回:
        Path: 目录路径
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def ensure_parent(file_path: Path) -> Path:
    """
    确保文件的父目录存在。

    参数:
        file_path: 文件路径

    返回:
        Path: 文件路径
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path

def read_file(path: Path, encoding: str = 'utf-8') -> str:
    """
    读取文件内容。

    参数:
        path: 文件路径
        encoding: 字符编码

    返回:
        str: 文件内容

    异常:
        FileNotFoundError: 文件不存在
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding=encoding) as f:
        return f.read()

def write_file(path: Path, content: str, encoding: str = 'utf-8') -> None:
    """
    写入文件内容。

    参数:
        path: 文件路径
        content: 文件内容
        encoding: 字符编码
    """
    path = Path(path)
    ensure_parent(path)
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)

def read_binary_file(path: Path) -> bytes:
    """
    读取二进制文件。

    参数:
        path: 文件路径

    返回:
        bytes: 文件内容
    """
    path = Path(path)
    with open(path, 'rb') as f:
        return f.read()

def write_binary_file(path: Path, data: bytes) -> None:
    """
    写入二进制文件。

    参数:
        path: 文件路径
        data: 二进制数据
    """
    path = Path(path)
    ensure_parent(path)
    with open(path, 'wb') as f:
        f.write(data)

def copy_file(src: Path, dst: Path) -> None:
    """
    复制文件。

    参数:
        src: 源文件路径
        dst: 目标文件路径
    """
    import shutil
    src = Path(src)
    dst = Path(dst)
    ensure_parent(dst)
    shutil.copy2(src, dst)

def find_files(
    directory: Path,
    pattern: str = '*',
    recursive: bool = True
) -> List[Path]:
    """
    查找文件。

    参数:
        directory: 目录路径
        pattern: 文件匹配模式
        recursive: 是否递归查找

    返回:
        List[Path]: 文件路径列表
    """
    directory = Path(directory)
    if recursive:
        return list(directory.rglob(pattern))
    return list(directory.glob(pattern))

def get_file_extension(path: Path) -> str:
    """
    获取文件扩展名（不含点）。

    参数:
        path: 文件路径

    返回:
        str: 文件扩展名
    """
    return path.suffix[1:]

def change_extension(path: Path, new_extension: str) -> Path:
    """
    修改文件扩展名。

    参数:
        path: 文件路径
        new_extension: 新扩展名（不含点）

    返回:
        Path: 修改后的路径
    """
    return path.with_suffix(f'.{new_extension}')

# ============================================================
# 系统工具
# ============================================================

def open_docx(filepath: Path) -> bool:
    """
    打开 DOCX 文件。

    参数:
        filepath: 文件路径

    返回:
        bool: 是否成功打开
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return False

    try:
        system = platform.system()
        if system == 'Windows':
            os.startfile(str(filepath))
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', str(filepath)])
        else:  # Linux
            subprocess.run(['xdg-open', str(filepath)])
        return True
    except Exception:
        return False

def get_temp_dir() -> Path:
    """
    获取临时目录。

    返回:
        Path: 临时目录路径
    """
    import tempfile
    return Path(tempfile.gettempdir())

def create_temp_file(suffix: str = '', prefix: str = '') -> Path:
    """
    创建临时文件。

    参数:
        suffix: 文件后缀
        prefix: 文件前缀

    返回:
        Path: 临时文件路径
    """
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return Path(path)

def create_temp_dir(prefix: str = '') -> Path:
    """
    创建临时目录。

    参数:
        prefix: 目录前缀

    返回:
        Path: 临时目录路径
    """
    import tempfile
    return Path(tempfile.mkdtemp(prefix=prefix))

# ============================================================
# 路径工具
# ============================================================

def is_absolute_path(path: Union[str, Path]) -> bool:
    """
    检查是否为绝对路径。

    参数:
        path: 路径

    返回:
        bool: 是否为绝对路径
    """
    return Path(path).is_absolute()

def normalize_path(path: Union[str, Path]) -> Path:
    """
    规范化路径。

    参数:
        path: 路径

    返回:
        Path: 规范化后的路径
    """
    return Path(path).resolve()

def get_relative_path(
    path: Union[str, Path],
    base: Union[str, Path]
) -> Path:
    """
    获取相对路径。

    参数:
        path: 路径
        base: 基础路径

    返回:
        Path: 相对路径
    """
    return Path(path).relative_to(Path(base))

def join_path(base: Union[str, Path], *parts: str) -> Path:
    """
    拼接路径。

    参数:
        base: 基础路径
        *parts: 路径部分

    返回:
        Path: 拼接后的路径
    """
    return Path(base).joinpath(*parts)

# ============================================================
# 字符串工具
# ============================================================

def slugify(text: str, separator: str = '-') -> str:
    """
    生成 URL 友好的 Slug。

    参数:
        text: 文本
        separator: 分隔符

    返回:
        str: Slug
    """
    # 转为小写
    text = text.lower()
    # 替换空格为分隔符
    text = text.replace(' ', separator)
    # 移除特殊字符
    text = re.sub(r'[^a-z0-9' + re.escape(separator) + ']', '', text)
    # 移除连续分隔符
    text = re.sub(r'[' + re.escape(separator) + ']+', separator, text)
    # 移除首尾分隔符
    text = text.strip(separator)
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断文本。

    参数:
        text: 文本
        max_length: 最大长度
        suffix: 后缀

    返回:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def escape_html(text: str) -> str:
    """
    转义 HTML 特殊字符。

    参数:
        text: 文本

    返回:
        str: 转义后的文本
    """
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;',
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text

def unescape_html(text: str) -> str:
    """
    反转义 HTML 特殊字符。

    参数:
        text: 文本

    返回:
        str: 反转义后的文本
    """
    replacements = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
    }
    for escaped, char in replacements.items():
        text = text.replace(escaped, char)
    return text

def normalize_whitespace(text: str) -> str:
    """
    规范化空白字符。

    将多个空白字符（空格、换行、制表符）替换为单个空格。

    参数:
        text: 文本

    返回:
        str: 规范化后的文本
    """
    return ' '.join(text.split())

def remove_markdown(text: str) -> str:
    """
    移除 Markdown 标记。

    参数:
        text: 文本

    返回:
        str: 移除标记后的文本
    """
    # 移除链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 移除图片 ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # 移除粗体/斜体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # 移除行内代码
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # 移除标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 移除列表标记
    text = re.sub(r'^[\*\-+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    return text