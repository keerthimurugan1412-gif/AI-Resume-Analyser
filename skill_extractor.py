"""
Skill Extraction:

Loads a controlled skill dictionary (data/skill_dictionary.csv) and
searches cleaned resume text for those skills using whole-word /
whole-phrase keyword matching, then groups the results by category.

This is the "beginner approach" described in the project brief
(keyword matching). spaCy or an LLM can be swapped in later as an
"advanced improvement" without changing the public API of
`extract_skills`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DEFAULT_SKILL_DICT_PATH = Path(__file__).parent / "data" / "skill_dictionary.csv"


@dataclass
class SkillExtractionResult:
    found_skills: list[str] = field(default_factory=list)
    skills_by_category: dict[str, list[str]] = field(default_factory=dict)


def _build_pattern_map(skill_df: pd.DataFrame) -> dict[str, re.Pattern]:
    """
    Build a regex pattern for every skill (and its aliases) with word
    boundaries so 'r' doesn't match inside 'server', etc.
    """
    patterns: dict[str, re.Pattern] = {}
    for _, row in skill_df.iterrows():
        skill = str(row["skill"]).strip()
        alias_field = str(row.get("aliases", "") or "")
        variants = [skill] + [a.strip() for a in alias_field.split("|") if a.strip()]

        escaped = [re.escape(v.lower()) for v in variants]
        # Use non-word boundaries that tolerate symbols like '++', '#', '.'
        pattern_str = r"(?<![a-z0-9])(" + "|".join(escaped) + r")(?![a-z0-9])"
        patterns[skill] = re.compile(pattern_str, re.IGNORECASE)
    return patterns


def load_skill_dictionary(path: Path = DEFAULT_SKILL_DICT_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def extract_skills(cleaned_text: str, skill_df: pd.DataFrame | None = None) -> SkillExtractionResult:
    """
    Search cleaned resume text for known skills.

    Parameters
    ----------
    cleaned_text: output of text_cleaner.clean_text()
    skill_df: optional pre-loaded skill dictionary (avoids re-reading
              the CSV on every call, e.g. inside a Streamlit app).
    """
    if skill_df is None:
        skill_df = load_skill_dictionary()

    patterns = _build_pattern_map(skill_df)

    found: list[str] = []
    for skill, pattern in patterns.items():
        if pattern.search(cleaned_text):
            found.append(skill)

    category_map = dict(zip(skill_df["skill"], skill_df["category"]))
    by_category: dict[str, list[str]] = {}
    for skill in found:
        category = category_map.get(skill, "Other")
        by_category.setdefault(category, []).append(skill)

    for category in by_category:
        by_category[category].sort()

    return SkillExtractionResult(found_skills=sorted(found), skills_by_category=by_category)
