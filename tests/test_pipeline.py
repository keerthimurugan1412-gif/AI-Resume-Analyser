import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from text_cleaner import clean_text
from skill_extractor import extract_skills, load_skill_dictionary
from job_matcher import load_job_roles, rank_roles, get_role_match

PROTECTED_TERMS = ["gender", "age", "religion", "nationality", "photo", "marital", "disability", "race", "caste"]


def run_case(label: str, resume_text: str, expected_top_role: str, skill_df, job_roles_df):
    cleaned = clean_text(resume_text)
    skills = extract_skills(cleaned, skill_df)
    ranked = rank_roles(cleaned, skills.found_skills, job_roles_df)
    actual_top_role = ranked[0].job_role if ranked else None

    status = "PASS" if actual_top_role == expected_top_role else "CHECK"
    print(f"[{status}] {label}")
    print(f"      expected top role: {expected_top_role}")
    print(f"      actual top role:   {actual_top_role} ({ranked[0].match_score if ranked else 0}%)")
    print(f"      skills found:      {skills.found_skills}")
    print()
    return actual_top_role == expected_top_role


def test_fairness_no_protected_attributes(skill_df):
    skill_names = " ".join(skill_df["skill"].astype(str)).lower()
    for term in PROTECTED_TERMS:
        assert term not in skill_names, f"Protected term '{term}' found in skill dictionary!"
    print("[PASS] Fairness check: no protected attributes in the skill dictionary.\n")


def test_score_consistency(skill_df, job_roles_df):
    base_text = clean_text("python sql pandas")
    plus_text = clean_text("python sql pandas fastapi docker")

    base_skills = extract_skills(base_text, skill_df).found_skills
    plus_skills = extract_skills(plus_text, skill_df).found_skills

    base_match = get_role_match(rank_roles(base_text, base_skills, job_roles_df), "Machine Learning Engineer")
    plus_match = get_role_match(rank_roles(plus_text, plus_skills, job_roles_df), "Machine Learning Engineer")

    assert plus_match.match_score >= base_match.match_score, "Adding relevant skills should not lower the match score."
    print(f"[PASS] Score consistency: {base_match.match_score}% -> {plus_match.match_score}% after adding FastAPI & Docker.\n")


def test_extraction_edge_cases(skill_df, job_roles_df):
    empty_result = extract_skills(clean_text(""), skill_df)
    assert empty_result.found_skills == [], "Empty text should yield no detected skills."
    print("[PASS] Edge case: empty resume text yields zero skills, no crash.\n")


def main():
    skill_df = load_skill_dictionary()
    job_roles_df = load_job_roles()

    resumes_dir = Path(__file__).resolve().parent.parent / "sample_resumes"
    cases = [
        ("resume_A_data_analyst.txt", "Data Analyst"),
        ("resume_B_ml_engineer.txt", "Machine Learning Engineer"),
        ("resume_C_nlp_engineer.txt", "NLP Engineer"),
    ]

    results = []
    for filename, expected_role in cases:
        text = (resumes_dir / filename).read_text(encoding="utf-8")
        results.append(run_case(filename, text, expected_role, skill_df, job_roles_df))

    test_fairness_no_protected_attributes(skill_df)
    test_score_consistency(skill_df, job_roles_df)
    test_extraction_edge_cases(skill_df, job_roles_df)

    passed = sum(results)
    print(f"Summary: {passed}/{len(results)} role-ranking cases matched the expected top role.")


if __name__ == "__main__":
    main()
