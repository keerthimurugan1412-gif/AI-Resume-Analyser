# 📊 AI Resume Analyzer and Job Recommendation System

An NLP-based Streamlit application that scores how well a resume matches
selected job roles, lists missing skills, and generates a simple
week-by-week learning roadmap — built as a guided student project.

> Match scores are automated **estimates for self-guided learning**, not
> hiring or rejection decisions. See [Responsible AI](#-responsible-ai-rules) below.

---

## ✨ Features

- Upload a **PDF or DOCX** resume (validated for type & size, processed in memory only).
- Extracts and cleans resume text while preserving technical tokens like `C++`, `C#`, `.NET`.
- Detects **50+ job-related skills** across 10 categories using a controlled skill dictionary.
- Compares the resume against **7 predefined job roles** using a blended score:
  - 65% skill-overlap score (explainable: "you have 6 of 8 required skills")
  - 35% TF-IDF cosine-similarity score (captures overall wording/context)
- Ranks and recommends the **top N** most suitable roles.
- Shows **matched vs. missing skills** for any selected target role.
- Generates a **rule-based, week-by-week learning roadmap** for missing skills.
- **Downloadable PDF analysis report** for offline sharing.
- Built-in **Responsible AI** guardrails (see below).

---

---

## ⚙️ Setup

**Requirements:** Python 3.10+

```
# 1. Clone / unzip the project, then move into it
cd ai_resume_analyzer

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Create a .env file if you plan to add an
#    "AI feedback" provider later. Not required to run the core app.
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## ▶️ Run the app

```
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## 🧪 Run the automated tests

```
python tests/test_pipeline.py
```

This checks extraction/skill detection on the three sample resumes, verifies
role ranking, checks score consistency (adding a relevant skill should never
lower the score), and confirms no protected attributes exist in the skill
dictionary.

---

## 🖥️ Using the app

1. **Upload** a PDF or DOCX resume.
2. Choose a **target job role** from the dropdown.
3. Check the **processing consent** box (resumes are never written to disk).
4. Click **Analyze Resume**.
5. Review:
   - Extracted skills, grouped by category
   - A match-score bar chart across all job roles
   - Top recommended roles
   - Matched vs. missing skills for your chosen target role
   - A week-by-week learning roadmap
   - A downloadable PDF report

> To try it without a real resume, open any file in `sample_resumes/`, paste
> its content into Word or Google Docs, and save/export as `.docx` or `.pdf`.

---

## 🧠 How matching works 

1. **Skill overlap score** — `matched_required_skills / total_required_skills × 100`.
2. **TF-IDF + cosine similarity** — the resume text and each role's
   description/skill text are vectorized with `TfidfVectorizer`
   (scikit-learn) and compared with cosine similarity.
3. **Final match score** = `0.65 × overlap_score + 0.35 × tfidf_score`.

This keeps scores easy to explain to a student ("you're missing Docker and
FastAPI") while still rewarding resumes whose overall language matches the
role.

### Advanced approach (optional upgrade path)

- Replace keyword matching with **spaCy** phrase/entity extraction.
- Replace/augment TF-IDF with **Sentence Transformers** embeddings for
  semantic similarity.
- Train a **supervised classifier** once labelled resume->role data exists.
- Add **LLM-generated resume feedback** via a controlled prompt (Groq /
  Gemini / OpenAI / local model) — see `.env`.
- Serve the pipeline behind a **FastAPI** backend with Docker deployment.

---

## 🔒 Responsible AI Rules

This project follows the guidance in the original project brief:

- The tool is for **guidance only** — never automatic hiring or rejection.
- The skill dictionary **never scores** gender, age, religion, nationality,
  photographs, marital status, or disability.
- Only **job-related skills, education, projects, and experience** are evaluated.
- Match scores are clearly labelled as **estimates**, not recruiter decisions.
- Uploaded resumes are **processed in memory only** and are not written to
  disk by default.
- The app **does not claim** that a missing keyword always means missing
  ability — this is stated directly in the sidebar and PDF report.

---

## 📊 Example Output

```
Target Role: Machine Learning Engineer
Match Score: 76%

Skills Found: Python, Machine Learning, scikit-learn, Pandas, NumPy, SQL, Git, FastAPI, Docker
Missing Skills: (none - all required skills found)

Recommended Roles:
 1. Machine Learning Engineer - 76%
 2. Data Scientist - 63%
 3. AI Engineer - 41%
```

---

## 🚀 Deployment

- **Streamlit Community Cloud**: push this repo to GitHub, connect it at
  share.streamlit.io, and set `app.py` as the entry point.
- **Docker**: wrap `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`
  in a `Dockerfile` based on `python:3.11-slim`, `COPY` the project, `pip
  install -r requirements.txt`, and `EXPOSE 8501`.
- **Render**: deploy as a Web Service with the same start command.

---


