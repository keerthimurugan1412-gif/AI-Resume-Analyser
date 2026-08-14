"""
Text Extraction and Cleaning:

Cleans and normalizes raw resume text while preserving technical
tokens such as "C++", "C#", ".NET", "Node.js" that would otherwise be
mangled by naive symbol stripping.
"""

from __future__ import annotations

import re

# Technical tokens that must survive cleaning untouched.
# Longer tokens are listed first so they are protected before shorter
# substrings of themselves.
PROTECTED_TOKENS = [
    "C++",
    "C#",
    ".NET",
    "Node.js",
    "Vue.js",
    "React.js",
    "ASP.NET",
    "Scikit-learn",
    "scikit-learn",
]

_WHITESPACE_RE = re.compile(r"\s+")
_BULLET_RE = re.compile(r"[•▪●■♦◦‣·]+")
# Keep letters, numbers, spaces, and a safe set of technical punctuation.
_UNSAFE_SYMBOLS_RE = re.compile(r"[^a-z0-9\s\.\+\#\-\_/@]")


def _protect_tokens(text: str) -> tuple[str, dict[str, str]]:
    """Temporarily swap protected tokens for unique placeholders."""
    mapping: dict[str, str] = {}
    for i, token in enumerate(PROTECTED_TOKENS):
        placeholder = f"__PROTECTED_{i}__"
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        if pattern.search(text):
            text = pattern.sub(placeholder, text)
            mapping[placeholder] = token
    return text, mapping


def _restore_tokens(text: str, mapping: dict[str, str]) -> str:
    for placeholder, token in mapping.items():
        text = text.replace(placeholder.lower(), token)
    return text


def clean_text(raw_text: str) -> str:
    """
    Clean and normalize resume text for downstream NLP processing.

    Steps:
    1. Protect important technical symbols (C++, C#, .NET, ...).
    2. Convert to lowercase for consistent comparison.
    3. Remove bullet characters and stray symbols.
    4. Collapse repeated whitespace / blank lines.
    5. Restore protected technical tokens.
    """
    if not raw_text:
        return ""

    text = raw_text
    text = _BULLET_RE.sub(" ", text)

    # Protect technical tokens before lowercasing / stripping symbols.
    text, mapping = _protect_tokens(text)

    text = text.lower()
    text = _UNSAFE_SYMBOLS_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()

    text = _restore_tokens(text, mapping)
    return text


def split_into_lines(raw_text: str) -> list[str]:
    """Split raw (uncleaned) text into non-empty, stripped lines - useful for section detection."""
    return [line.strip() for line in raw_text.splitlines() if line.strip()]
