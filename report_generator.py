"""
Builds a downloadable PDF analysis report
summarizing the resume-to-role match, skills found, missing skills,
and the suggested learning roadmap.
"""

from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from job_matcher import RoleMatch
from roadmap_generator import RoadmapWeek


def build_pdf_report(
    candidate_label: str,
    target_role: str,
    role_match: RoleMatch,
    top_roles: list[RoleMatch],
    roadmap_weeks: list[RoadmapWeek],
) -> bytes:
    """Return the PDF report as raw bytes, ready for a Streamlit download button."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1F3864"))
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], textColor=colors.HexColor("#1F3864"))
    body_style = styles["BodyText"]

    story = []
    story.append(Paragraph("AI Resume Analyzer - Analysis Report", title_style))
    story.append(Paragraph(datetime.now().strftime("Generated on %B %d, %Y at %H:%M"), body_style))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(f"Target Role: {target_role}", heading_style))
    story.append(Paragraph(f"Match Score: <b>{role_match.match_score}%</b>", body_style))
    story.append(Paragraph(
        f"(Skill overlap: {role_match.skill_overlap_score}% &nbsp;|&nbsp; Text similarity: {role_match.tfidf_score}%)",
        body_style,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Skills Found", heading_style))
    found_text = ", ".join(role_match.matched_skills) if role_match.matched_skills else "None detected for this role."
    story.append(Paragraph(found_text, body_style))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Missing Skills", heading_style))
    missing_text = ", ".join(role_match.missing_skills) if role_match.missing_skills else "None - all required skills found!"
    story.append(Paragraph(missing_text, body_style))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Recommended Roles", heading_style))
    table_data = [["Rank", "Job Role", "Match Score"]]
    for i, role in enumerate(top_roles, start=1):
        table_data.append([str(i), role.job_role, f"{role.match_score}%"])
    table = Table(table_data, colWidths=[2 * cm, 8 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Suggested Learning Roadmap", heading_style))
    if not roadmap_weeks:
        story.append(Paragraph("No missing skills detected for this role - great work!", body_style))
    else:
        for week in roadmap_weeks:
            story.append(Paragraph(f"<b>Week {week.week_number}:</b> {' & '.join(week.skills)}", body_style))
            for skill, note in zip(week.skills, week.notes):
                story.append(Paragraph(f"&nbsp;&nbsp;&bull; {skill}: {note}", body_style))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 0.5 * cm))
    disclaimer = (
        "Disclaimer: This match score is an automated estimate for self-guided learning purposes "
        "only. It is not a hiring decision and does not evaluate protected personal attributes."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle("Disclaimer", parent=body_style, textColor=colors.grey, fontSize=8)))

    doc.build(story)
    return buffer.getvalue()
