"""
Language Detection - 中英混排语言检测与 Run 分割（第十章 10.3 / 第十一章 11.2）

实现:
    - CJK / Latin 占比检测（权重: cjk 1.0, latin_word 1.0, number 0.25）
    - 语言自适应段落对齐（中文两端对齐、西文左对齐）
    - 原子序列保持（URL、邮箱、小数、百分比、货币、单位、标识符）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# ============================================================
# 字符分类
# ============================================================


class TextScript(str, Enum):
    """文本脚本分类。"""

    CJK = "cjk"
    LATIN = "latin"
    DIGIT = "digit"
    OTHER = "other"


_CJK_RE = re.compile(
    "[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u30ff\uac00-\ud7af"
    "\u3000-\u303f\uff00-\uffef\u2014\u2018\u2019\u201c\u201d\u2026]"
)
_LATIN_RE = re.compile("[A-Za-z]")
_DIGIT_RE = re.compile("[0-9]")
_WHITESPACE_RE = re.compile(r"\s")


def classify_char(ch: str) -> TextScript:
    """分类单个字符的脚本。"""
    if _CJK_RE.match(ch):
        return TextScript.CJK
    if _LATIN_RE.match(ch):
        return TextScript.LATIN
    if _DIGIT_RE.match(ch):
        return TextScript.DIGIT
    return TextScript.OTHER


#: 汉字（Han ideograph）单独识别：CJK 统一表意文字基本区 + 扩展 A 区。
#: 刻意比 :data:`_CJK_RE` 更窄——后者还包含假名、谚文与 CJK 标点，
#: 因此不能直接用于“正向检测到中文内容”的判断（例如全角标点不应算中文）。
_HAN_RE = re.compile("[\u4e00-\u9fff\u3400-\u4dbf]")


def contains_han_ideograph(text: str) -> bool:
    """判断文本是否包含至少一个汉字。

    参数:
        text: 待检测文本（``None`` 或空文本返回 ``False``）

    返回:
        bool: 是否包含汉字（CJK 统一表意文字基本区或扩展 A 区）。
            纯数字、纯标点（含全角标点）、纯拉丁文本均返回 ``False``。
    """
    if not text:
        return False
    return _HAN_RE.search(text) is not None


# ============================================================
# 原子序列（10.3 run_segmentation.atomic_sequences）
# ============================================================

_ATOMIC_PATTERNS: List[re.Pattern] = [
    # URL
    re.compile(r"(?:https?://|ftp://|www\.)[^\s\u4e00-\u9fff]+"),
    # Email
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    # 货币（$12.8B / 35.6% 等）
    re.compile(
        r"[$€£¥]\s*\d[\d,.]*(?:[A-Za-z]*|%|亿元|万)?|\d[\d,.]*(?:\.\d+)?\s*(?:USD|EUR|CNY|RMB|元|美元|人民币)"
    ),
    # 百分比
    re.compile(r"\d[\d,]*(?:\.\d+)?%"),
    # 小数 / 千分位数字
    re.compile(r"\d[\d,]*(?:\.\d+)+"),
    # 数字
    re.compile(r"\d+"),
    # 标识符 / 版本号
    re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]*"),
    # 单词（含连字符）
    re.compile(r"[A-Za-z]+(?:['\-][A-Za-z]+)*"),
]

_MASTER_TOKEN_RE = re.compile("|".join(f"({p.pattern})" for p in _ATOMIC_PATTERNS))


@dataclass(frozen=True)
class TextSegment:
    """Run 分割段。"""

    text: str
    script: TextScript
    atomic: bool = False


@dataclass(frozen=True)
class LanguageProfile:
    """语言检测结果。"""

    text: str
    cjk_ratio: float
    latin_ratio: float
    digit_ratio: float
    dominant: str  # cjk | latin | mixed
    code_heavy: bool = False
    url_heavy: bool = False

    def alignment(
        self,
        cjk_threshold: float = 0.55,
        latin_threshold: float = 0.60,
        code_heavy: Optional[bool] = None,
        url_heavy: Optional[bool] = None,
        table_cell: bool = False,
    ) -> str:
        """
        按第十一章 11.2 规则决定对齐方式。

        返回:
            str: 'justified' 或 'left'
        """
        if table_cell:
            return "left"
        if code_heavy if code_heavy is not None else self.code_heavy:
            return "left"
        if url_heavy if url_heavy is not None else self.url_heavy:
            return "left"
        if self.cjk_ratio > cjk_threshold:
            return "justified"
        if self.latin_ratio > latin_threshold:
            return "left"
        return "justified"  # mixed


def detect_language(
    text: str,
    cjk_weight: float = 1.0,
    latin_weight: float = 1.0,
    digit_weight: float = 0.25,
    long_word_threshold: int = 20,
    url_break_prefixes: Optional[List[str]] = None,
) -> LanguageProfile:
    """
    检测文本语言占比。

    参数:
        text: 待检测文本
        cjk_weight: CJK 字符权重
        latin_weight: Latin 单词权重
        digit_weight: 数字权重
        long_word_threshold: 长单词阈值（用于 url_heavy 判断）
        url_break_prefixes: URL 前缀列表

    返回:
        LanguageProfile: 语言画像
    """
    cjk = sum(1 for ch in text if classify_char(ch) == TextScript.CJK)
    latin_words = len(re.findall(r"[A-Za-z]+", text))
    digits = sum(1 for ch in text if classify_char(ch) == TextScript.DIGIT)

    cjk_score = cjk * cjk_weight
    latin_score = latin_words * latin_weight
    digit_score = digits * digit_weight
    total = cjk_score + latin_score + digit_score
    if total <= 0:
        return LanguageProfile(
            text=text, cjk_ratio=0.0, latin_ratio=0.0, digit_ratio=0.0, dominant="mixed"
        )

    cjk_ratio = cjk_score / total
    latin_ratio = latin_score / total
    digit_ratio = digit_score / total

    if cjk_ratio >= latin_ratio and cjk_ratio > 0:
        dominant = "cjk"
    elif latin_ratio > cjk_ratio:
        dominant = "latin"
    else:
        dominant = "mixed"

    prefixes = url_break_prefixes or ["http://", "https://", "www.", "ftp://"]
    url_heavy = any(p in text for p in prefixes)
    long_words = re.findall(r"[A-Za-z0-9_\-./]{20,}", text)
    if long_words:
        url_heavy = True
    code_heavy = bool(re.search(r"`[^`]+`", text)) or bool(
        re.search(r"\b(?:def|class|import|return|if|else|for|while|function)\b", text)
    )

    return LanguageProfile(
        text=text,
        cjk_ratio=cjk_ratio,
        latin_ratio=latin_ratio,
        digit_ratio=digit_ratio,
        dominant=dominant,
        code_heavy=code_heavy,
        url_heavy=url_heavy,
    )


# ============================================================
# Run 分割（10.3）
# ============================================================


def segment_text(text: str, preserve_spaces: bool = True) -> List[TextSegment]:
    """
    将文本按脚本分割为 Run 段，保持原子序列完整。

    分割规则:
        - CJK 与 Latin 分属不同段（分别使用 eastAsia / ascii 字体）
        - URL、邮箱、小数、百分比、货币、单位、标识符保持为单个段
        - 保留 Markdown 空格

    参数:
        text: 待分割文本
        preserve_spaces: 是否保留空格（默认 True）

    返回:
        List[TextSegment]: 分割段列表
    """
    if not text:
        return []

    segments: List[TextSegment] = []
    pos = 0
    for match in _MASTER_TOKEN_RE.finditer(text):
        start, end = match.start(), match.end()
        # 匹配之间的普通文本
        if start > pos:
            _append_classified(text[pos:start], segments, preserve_spaces)
        token = match.group(0)
        script = _classify_token(token)
        segments.append(TextSegment(text=token, script=script, atomic=True))
        pos = end
    if pos < len(text):
        _append_classified(text[pos:], segments, preserve_spaces)

    return _merge_adjacent(segments)


def _classify_token(token: str) -> TextScript:
    """分类原子 token 的脚本。"""
    if any(classify_char(ch) == TextScript.CJK for ch in token):
        return TextScript.CJK
    if any(classify_char(ch) in (TextScript.LATIN, TextScript.DIGIT) for ch in token):
        return TextScript.LATIN
    return TextScript.OTHER


def _append_classified(chunk: str, segments: List[TextSegment], preserve_spaces: bool) -> None:
    """将普通文本按脚本拆分为连续段。"""
    if not chunk:
        return
    current: List[str] = []
    current_script: Optional[TextScript] = None

    def flush() -> None:
        nonlocal current, current_script
        if current:
            segments.append(
                TextSegment(text="".join(current), script=current_script or TextScript.OTHER)
            )
        current = []
        current_script = None

    for ch in chunk:
        if ch.isspace() and not preserve_spaces:
            flush()
            continue
        script = classify_char(ch)
        # 空格归属前一段（保持连读），ASCII 标点跟随相邻段
        if ch.isspace():
            if current:
                current.append(ch)
                continue
            segments.append(TextSegment(text=ch, script=TextScript.OTHER))
            continue
        if script == TextScript.OTHER:
            if current:
                current.append(ch)
                continue
            segments.append(TextSegment(text=ch, script=TextScript.OTHER))
            continue
        if current_script is not None and script != current_script:
            flush()
        current.append(ch)
        current_script = script
    flush()


def _merge_adjacent(segments: List[TextSegment]) -> List[TextSegment]:
    """合并脚本相同的相邻段。"""
    if not segments:
        return segments
    merged: List[TextSegment] = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        if last.script == seg.script and not last.atomic and not seg.atomic:
            merged[-1] = TextSegment(
                text=last.text + seg.text,
                script=last.script,
                atomic=False,
            )
        else:
            merged.append(seg)
    return merged
