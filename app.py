from __future__ import annotations

"""
📊 AI Resume Analyzer & Job Recommendation System
"""


import matplotlib.pyplot as plt
import streamlit as st

from resume_parser import extract_resume_text
from text_cleaner import clean_text
from skill_extractor import extract_skills, load_skill_dictionary
from job_matcher import load_job_roles, rank_roles, top_recommendations, get_role_match
from roadmap_generator import generate_roadmap, roadmap_to_text
from report_generator import build_pdf_report

st.set_page_config(page_title="AI Resume Analyzer", page_icon="🚀", layout="wide")


# --------------------------------------------------------------------------- #
# Cached resource loaders (avoid re-reading CSVs on every interaction)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def get_skill_dictionary():
    return load_skill_dictionary()


@st.cache_data(show_spinner=False)
def get_job_roles():
    return load_job_roles()


# --------------------------------------------------------------------------- #
# Sidebar - Responsible AI notice + settings
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.title("🚀 AI Resume Analyzer")
    st.caption("NLP-based resume-to-job matching & learning roadmap generator")

    st.markdown("### ⚙️ Settings")
    top_n = st.slider("Number of role recommendations", min_value=1, max_value=5, value=3)
    skills_per_week = st.slider("Skills to learn per roadmap week", min_value=1, max_value=3, value=2)

    st.markdown("---")
    st.markdown("### 🔒 Responsible AI")
    st.info(
        "- Match scores are **estimates for self-guided learning**, not hiring decisions.\n"
        "- No gender, age, religion, nationality, photo, marital status, or disability data is used.\n"
        "- Only job-related skills, education, projects, and experience are evaluated.\n"
        "- Your resume is processed **in memory only** and is not stored on a server.\n"
        "- A missing keyword does not always mean a missing ability."
    )


# --------------------------------------------------------------------------- #
#  Resume Upload
# --------------------------------------------------------------------------- #
st.header("1. Upload Your Resume")

col_upload, col_role = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader("Upload a PDF or DOCX resume", type=["pdf", "docx"])
    if uploaded_file is not None:
        st.success(f"Uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

job_roles_df = get_job_roles()
skill_dict_df = get_skill_dictionary()

with col_role:
    target_role = st.selectbox("Target job role", options=job_roles_df["job_role"].tolist())

consent = st.checkbox(
    "I give permission to temporarily process my resume text for this analysis "
    "(it is not saved permanently).",
    value=True,
)

analyze_clicked = st.button("🔍 Analyze Resume", type="primary", disabled=uploaded_file is None or not consent)


# --------------------------------------------------------------------------- #
# Run the pipeline once the user clicks "Analyze"
# --------------------------------------------------------------------------- #
if analyze_clicked and uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()  # kept in memory only, never written to disk

    with st.spinner("Extracting and cleaning resume text..."):
        extraction = extract_resume_text(uploaded_file.name, file_bytes)

    if not extraction.success:
        st.error(extraction.error)
        st.stop()

    cleaned_text = clean_text(extraction.text)

    with st.spinner("Identifying skills..."):
        skill_result = extract_skills(cleaned_text, skill_dict_df)

    with st.spinner("Comparing resume with job roles..."):
        ranked_roles = rank_roles(cleaned_text, skill_result.found_skills, job_roles_df)
        recommendations = top_recommendations(ranked_roles, top_n=top_n)
        selected_match = get_role_match(ranked_roles, target_role)

    roadmap_weeks = generate_roadmap(selected_match.missing_skills, skills_per_week=skills_per_week)

    st.session_state["last_run"] = {
        "file_name": uploaded_file.name,
        "target_role": target_role,
        "skill_result": skill_result,
        "ranked_roles": ranked_roles,
        "recommendations": recommendations,
        "selected_match": selected_match,
        "roadmap_weeks": roadmap_weeks,
    }

# --------------------------------------------------------------------------- #
# Results (persisted in session_state so widget interactions don't reset it)
# --------------------------------------------------------------------------- #
if "last_run" in st.session_state:
    run = st.session_state["last_run"]
    skill_result = run["skill_result"]
    ranked_roles = run["ranked_roles"]
    recommendations = run["recommendations"]
    selected_match = run["selected_match"]
    roadmap_weeks = run["roadmap_weeks"]

    st.divider()

    # ----------------------------------------------------------------- #
    # Extracted Skills Display
    # ----------------------------------------------------------------- #
    st.header("2. Extracted Skills")
    if not skill_result.found_skills:
        st.warning("No known skills were detected. Try a resume with a clearer 'Skills' section.")
    else:
        st.write(f"**{len(skill_result.found_skills)} skills detected**, grouped by category:")
        cat_cols = st.columns(min(4, max(1, len(skill_result.skills_by_category))))
        for i, (category, skills) in enumerate(sorted(skill_result.skills_by_category.items())):
            with cat_cols[i % len(cat_cols)]:
                st.markdown(f"**{category}**")
                for s in skills:
                    st.markdown(f"- {s}")

    # ----------------------------------------------------------------- #
    # Match-Score Chart + Recommended Roles
    # ----------------------------------------------------------------- #
    st.header("3. Match Score & Recommended Roles")

    left, right = st.columns([2, 1])

    with left:
        fig, ax = plt.subplots(figsize=(6, 3.2))
        roles_sorted = sorted(ranked_roles, key=lambda r: r.match_score)
        labels = [r.job_role for r in roles_sorted]
        scores = [r.match_score for r in roles_sorted]
        colors_ = ["#1F77B4" if r.job_role != run["target_role"] else "#FF7F0E" for r in roles_sorted]
        ax.barh(labels, scores, color=colors_)
        ax.set_xlabel("Match Score (%)")
        ax.set_xlim(0, 100)
        for i, v in enumerate(scores):
            ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9)
        fig.tight_layout()
        st.pyplot(fig)
        st.markdown(
    """
    <div style="display:flex; align-items:center; gap:6px; font-size:0.85rem; color:gray;">
        <div style="width:14px; height:14px; background-color:#FF7F0E; border-radius:3px;"></div>
        <span>= your selected target role</span>
    </div>
    """,
    unsafe_allow_html=True,
)

    with right:
        st.subheader(f"Top {len(recommendations)} Recommended Roles")
        for i, role in enumerate(recommendations, start=1):
            st.metric(label=f"{i}. {role.job_role}", value=f"{role.match_score}%")

    # ----------------------------------------------------------------- #
    # Skill-Gap Analysis + Roadmap for the SELECTED target role
    # ----------------------------------------------------------------- #
    st.header(f"4. Skill Gap Analysis for '{run['target_role']}'")

    gap_col1, gap_col2 = st.columns(2)
    with gap_col1:
        st.markdown("✅ **Skills already in your resume**")
        if selected_match.matched_skills:
            st.write(", ".join(selected_match.matched_skills))
        else:
            st.write("None of the required skills were detected yet.")

    with gap_col2:
        st.markdown("❌ **Missing / weak skills**")
        if selected_match.missing_skills:
            st.write(", ".join(selected_match.missing_skills))
        else:
            st.success("None - you already cover every required skill for this role!")

    st.header("5. Suggested Learning Roadmap")
    if not roadmap_weeks:
        st.success("No roadmap needed - you already meet the required skills for this role. 🎉")
    else:
        for week in roadmap_weeks:
            with st.expander(f"Week {week.week_number}: {' & '.join(week.skills)}", expanded=(week.week_number == 1)):
                for skill, note in zip(week.skills, week.notes):
                    st.markdown(f"- **{skill}** — {note}")

    # ----------------------------------------------------------------- #
    # Downloadable analysis report
    # ----------------------------------------------------------------- #
    st.header("6. Download Report")
    pdf_bytes = build_pdf_report(
        candidate_label=run["file_name"],
        target_role=run["target_role"],
        role_match=selected_match,
        top_roles=recommendations,
        roadmap_weeks=roadmap_weeks,
    )
    st.download_button(
        label="📄 Download PDF Analysis Report",
        data=pdf_bytes,
        file_name="resume_analysis_report.pdf",
        mime="application/pdf",
    )

    with st.expander("Plain-text summary (for copy/paste)"):
        st.text(roadmap_to_text(roadmap_weeks))

else:
    st.info("Upload a resume, choose a target role, give processing consent, then click **Analyze Resume**.")
