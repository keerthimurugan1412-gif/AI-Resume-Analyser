"""
Skill-Gap Analysis:

Turns a list of missing skills for a target role into a simple,
week-by-week rule-based learning roadmap, plus a short suggested
resource/topic for each skill. This is the "beginner approach"
(rule-based roadmap) from the project brief; an LLM-generated version
could later replace `SKILL_LEARNING_NOTES` as an advanced improvement.
"""

from __future__ import annotations

from dataclasses import dataclass

# A small, hand-curated knowledge base mapping each skill to a short,
# actionable learning note. Falls back to a generic note if a skill
# isn't listed here.
SKILL_LEARNING_NOTES: dict[str, str] = {
    "Python": "Practice core Python syntax, data structures, and functions.",
    "SQL": "Learn SELECT, JOIN, GROUP BY queries using a free dataset.",
    "Excel": "Practice pivot tables, formulas, and basic dashboards.",
    "Power BI": "Build a small dashboard connecting to a sample dataset.",
    "Tableau": "Recreate a public dashboard to learn charts and filters.",
    "Pandas": "Practice loading, filtering, and grouping data with DataFrames.",
    "NumPy": "Learn array operations, broadcasting, and basic linear algebra.",
    "Machine Learning": "Complete a supervised-learning course and build one model end-to-end.",
    "Deep Learning": "Learn neural network basics: layers, activations, backpropagation.",
    "scikit-learn": "Train and evaluate a classifier/regressor on a public dataset.",
    "TensorFlow": "Build and train a simple neural network with tf.keras.",
    "PyTorch": "Build a small neural network and training loop from scratch.",
    "NLP": "Learn tokenization, embeddings, and a basic text-classification pipeline.",
    "spaCy": "Practice named-entity recognition and POS tagging on sample text.",
    "Transformers": "Fine-tune a small pretrained model on a text-classification task.",
    "Sentence Transformers": "Use sentence embeddings to build a simple semantic search demo.",
    "LLM": "Learn prompt design and how to call an LLM API for a small task.",
    "RAG": "Build a minimal retrieval-augmented-generation pipeline over a few documents.",
    "Prompt Engineering": "Practice writing structured prompts with clear instructions and examples.",
    "OpenCV": "Practice image loading, filtering, and basic object detection with OpenCV.",
    "CNN": "Train a small convolutional network on an image-classification dataset.",
    "YOLO": "Run a pretrained YOLO model and fine-tune it on a custom small dataset.",
    "Computer Vision": "Complete an introductory computer-vision project end-to-end.",
    "FastAPI": "Build and deploy a simple REST API with two or three endpoints.",
    "Flask": "Build a small web app with routes, templates, and a form.",
    "Django": "Build a small CRUD app using Django's models and admin panel.",
    "REST API": "Learn HTTP methods, status codes, and how to design clean endpoints.",
    "Docker": "Containerize a small Python app and run it with docker run.",
    "Kubernetes": "Learn pods, deployments, and services using a local cluster (minikube).",
    "AWS": "Deploy a small app using EC2 or a managed service like Elastic Beanstalk.",
    "Azure": "Deploy a small app using Azure App Service.",
    "GCP": "Deploy a small app using Google Cloud Run.",
    "MLflow": "Track experiments, parameters, and metrics for a sample ML model.",
    "Git": "Practice commits, branches, and pull requests on a personal repo.",
    "GitHub": "Publish a project with a clear README and commit history.",
    "Streamlit": "Build and deploy a small interactive dashboard.",
    "Matplotlib": "Practice line, bar, and scatter plots on sample data.",
    "Seaborn": "Practice statistical plots such as heatmaps and pairplots.",
    "Plotly": "Build one interactive chart and embed it in a small app.",
}

GENERIC_NOTE = "Study the fundamentals and build one small hands-on project using this skill."

WEEKS_PER_BATCH = 1
SKILLS_PER_WEEK = 2


@dataclass
class RoadmapWeek:
    week_number: int
    skills: list[str]
    notes: list[str]


def generate_roadmap(missing_skills: list[str], skills_per_week: int = SKILLS_PER_WEEK) -> list[RoadmapWeek]:
    """
    Group missing skills into a simple week-by-week roadmap.

    Skills are kept in their given order (typically the order required
    by the job role) so foundational skills can be listed first by the
    caller if desired.
    """
    if not missing_skills:
        return []

    weeks: list[RoadmapWeek] = []
    for i in range(0, len(missing_skills), skills_per_week):
        batch = missing_skills[i : i + skills_per_week]
        notes = [SKILL_LEARNING_NOTES.get(skill, GENERIC_NOTE) for skill in batch]
        weeks.append(RoadmapWeek(week_number=len(weeks) + 1, skills=batch, notes=notes))

    return weeks


def roadmap_to_text(weeks: list[RoadmapWeek]) -> str:
    """Render the roadmap as plain text, e.g. for reports or the CLI."""
    if not weeks:
        return "No missing skills detected for this role - great work!"

    lines = []
    for week in weeks:
        skill_text = " & ".join(week.skills)
        lines.append(f"Week {week.week_number}: {skill_text}")
        for skill, note in zip(week.skills, week.notes):
            lines.append(f"   - {skill}: {note}")
    return "\n".join(lines)
