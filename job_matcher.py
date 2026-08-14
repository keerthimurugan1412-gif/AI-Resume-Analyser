"""
Job Role Dataset + Matching and Recommendation:

Combines two signals into a single, explainable match score:

1. Skill-overlap score: percentage of a role's REQUIRED skills that
   were actually found in the resume. Easy to explain to a student
   ("you have 6 of 8 required skills").
2. TF-IDF cosine-similarity score: treats the resume text and the job
   role's skill/description text as vectors and measures how similar
   their overall wording is. Captures context beyond a fixed skill
   list (the "beginner approach" from the project brief).

The final match score is a weighted blend of the two, which keeps
scores stable and intuitive while still rewarding resumes whose
overall language matches the role closely.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_JOB_ROLES_PATH = Path(__file__).parent / "data" / "job_roles.csv"

SKILL_OVERLAP_WEIGHT = 0.65
TFIDF_WEIGHT = 0.35


@dataclass
class RoleMatch:
    job_role: str
    match_score: float          # 0-100, blended score
    skill_overlap_score: float  # 0-100
    tfidf_score: float          # 0-100
    matched_skills: list[str]
    missing_skills: list[str]
    required_skills: list[str]


def load_job_roles(path: Path = DEFAULT_JOB_ROLES_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["required_skills_list"] = df["required_skills"].apply(
        lambda s: [skill.strip() for skill in str(s).split(",") if skill.strip()]
    )
    return df


def _skill_overlap_score(found_skills: set[str], required_skills: list[str]) -> tuple[float, list[str], list[str]]:
    found_lower = {s.lower() for s in found_skills}
    matched = [r for r in required_skills if r.lower() in found_lower]
    missing = [r for r in required_skills if r.lower() not in found_lower]
    if not required_skills:
        return 0.0, matched, missing
    score = (len(matched) / len(required_skills)) * 100
    return score, matched, missing


def _tfidf_scores(resume_text: str, role_texts: list[str]) -> list[float]:
    """Vectorize resume + all role descriptions together, then compare."""
    corpus = [resume_text] + role_texts
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Empty vocabulary edge case (e.g. resume text was too short).
        return [0.0 for _ in role_texts]

    resume_vector = tfidf_matrix[0:1]
    role_vectors = tfidf_matrix[1:]
    similarities = cosine_similarity(resume_vector, role_vectors)[0]
    return [max(0.0, min(1.0, s)) * 100 for s in similarities]


def rank_roles(
    resume_text_cleaned: str,
    found_skills: list[str],
    job_roles_df: pd.DataFrame | None = None,
) -> list[RoleMatch]:
    """
    Compare a resume against every job role in the dataset and return
    results ranked from the best match to the weakest.
    """
    if job_roles_df is None:
        job_roles_df = load_job_roles()

    role_texts = [
        f"{row['job_role']} {row['description']} " + " ".join(row["required_skills_list"])
        for _, row in job_roles_df.iterrows()
    ]
    tfidf_scores = _tfidf_scores(resume_text_cleaned, role_texts)

    found_skill_set = set(found_skills)
    results: list[RoleMatch] = []

    for (_, row), tfidf_score in zip(job_roles_df.iterrows(), tfidf_scores):
        overlap_score, matched, missing = _skill_overlap_score(found_skill_set, row["required_skills_list"])
        blended = (overlap_score * SKILL_OVERLAP_WEIGHT) + (tfidf_score * TFIDF_WEIGHT)

        results.append(
            RoleMatch(
                job_role=row["job_role"],
                match_score=round(blended, 1),
                skill_overlap_score=round(overlap_score, 1),
                tfidf_score=round(tfidf_score, 1),
                matched_skills=matched,
                missing_skills=missing,
                required_skills=row["required_skills_list"],
            )
        )

    results.sort(key=lambda r: r.match_score, reverse=True)
    return results


def top_recommendations(ranked_roles: list[RoleMatch], top_n: int = 3) -> list[RoleMatch]:
    return ranked_roles[:top_n]


def get_role_match(ranked_roles: list[RoleMatch], job_role: str) -> RoleMatch | None:
    for role in ranked_roles:
        if role.job_role == job_role:
            return role
    return None
