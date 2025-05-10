# AI Interview Simulation System

## Dashboard Preview
!

## 1. Project Overview

This project is a comprehensive AI-powered interview simulation framework built to evaluate candidates based on structured resumes or directly ingested JSON profiles. It automates the end-to-end simulation of multi-round interviews, evaluates responses using LLM-based scoring, generates performance reports, and displays real-time dashboards for review.

## 2. Key Components

- **Resume/Profile Ingestion:** Accepts PDF resumes or pre-formatted JSON profiles.
- **Multi-Round Interviews:** Simulates rounds like Technical, Behavioral, and Hiring Manager using GPT-4-based question generation.
- **Answer Evaluation:** Each candidate answer is scored on a 0–10 scale with qualitative feedback.
- **Score Aggregation:** Final score and round-wise breakdowns are computed for ranking.
- **Report Generation:** A professional HTML report is generated per candidate.
- **Dashboard Interface:** A Streamlit dashboard displays performance, Q&A, and evaluator comments.

## 3. Pipeline Flow

1. **Input:** Resume (PDF) or JSON profile
2. **Profile Creation:** Resume is converted into structured candidate profile JSON (rudimentary ATS)
3. **Interview Simulation:** Questions are generated and answers are simulated
4. **Evaluation:** Each answer is scored by a separate evaluation agent
5. **Transcript Generation:** Full JSONL transcript per round is stored
6. **Score Aggregation:** All scores are compiled per candidate
7. **Report Generation:** Graphs, summary, and evaluator feedback rendered to HTML
8. **Dashboard:** Streamlit frontend visualizes all data

## 4. Technologies Used

- **OpenAI API (GPT-3.5-turbo)**
- **Python** (LLM orchestration, backend logic)
- **Streamlit** (real-time dashboard)
- **Matplotlib** (performance visualizations)
- **FPDF** (report export)
- **HTML/CSS** (report styling)

## 5. Candidate Simulation Modes

- `--pdf`: Accepts a resume and converts to profile
- `--json`: Accepts an existing profile and runs simulation
- End-to-end flow is triggered via `run_simulation.py`

## 6. Backend Structure

- `interview_engine.py`: Handles simulation, evaluation, transcript storage
- `generate_reports.py`: Aggregates scores and builds reports
- `score_aggregate.py`: Compiles round and overall scores
- `backend.py`: Loads data for frontend
- `app.py`: Streamlit UI

## 7. Report Features

- Final score and recommendation
- Round-wise bar chart
- Evaluator feedback per question
- Clean layout, exportable as PDF or HTML

## 8. Dashboard Features

- Candidate selector
- Summary of scores and recommendation
- Per-round Q&A with feedback in collapsible sections
- Embedded report visualizations

## 9. Evaluation & Scoring Framework

### 9.1 Overview

Each candidate answer is evaluated using a second LLM with a strict JSON schema.

### 9.2 Scoring Schema

{
  "score": 8.2,
  "feedback": "Clear, technically sound, business-aligned.",
  "dimensions": {
    "communication": 8,
    "technical_accuracy": 7.5,
    "relevance": 9
  }
}

### 9.3 Aggregation Logic

Per round:  
`mean(score_i)`  
Overall:  
`mean(score_r)`

### 9.4 Recommendation Logic

| Score Range | Verdict       |
|-------------|---------------|
| ≥ 8.5       | Strong Hire   |
| 7.0–8.49    | Lean Hire     |
| < 7.0       | No Hire       |

### 9.5 Benefits

- Multi-dimensional scoring
- Objective and explainable
- All transcripts and scores are saved

