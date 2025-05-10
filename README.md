# AI Interview Simulation System

## Dashboard Preview
![](https://github.com/DSM2499/AI_Interview_Simulator/blob/main/screenshots/AI%20Interview%20Review.jpeg)

## How to run
Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
Install dependencies
```bash
pip install -r requirements.txt
```
Create a `.env` file in the rool directory:
```bash
OPEN_AI_KEY = Your_Key_Here
```
To run a full simulation
- With a PDF Resume
```bash
python run_simulation.py path/to/resume.pdf
```
- With Pre-built JSON Resume
```bash
python run_simulation.py path/to/profile.json --json
```

To run the dashboard manually
```bash
stremlit run app.py
```

## 1. Project Overview

The AI Interview Simulation Platform is an intelligent end-to-end system designed to simulate multi-round job interviews for data analyst roles. This system evaluates candidates based on custom-generated resumes (or uploaded ones), conducts interview rounds using LLM agents, provides detailed evaluations, and outputs comprehensive reports and dashboards. It automates candidate screening and helps recruiters visualize performance across various evaluation criteria.

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

## 4. Project Workflow & Implementation
The project evolved in well-structured phases, each delivering core functionality and integrations. Below is a breakdown of how the work progressed.

### 🔹 Phase 1: Resume Processing and Profile Generation
- **Input Options**: Users can submit:
  - PDF Resumes (parsed using LLMs)
  - Structured JSON profiles
- **Profile Generator (Rudimentory ATS)**:
  - Extracts educational background, tools, skills, projects, and experiences
  - Converts inputs into a lean profile schema for downstream tasks

### 🔹 Phase 2: Interview Simulation Engine
- Dynamically generate personalized questions
- Answers are evaluated by a 3rd agent with feedback, scoring and justification
Key Strategies:
- Round-specific interviewer personas
- Embedding-based topic memory to reduce redundancy
- Penalization for repetitive answers/projects
- Multi-turn agent interaction using `ConversationBufferMemory`

### 🔹 Phase 3: Scoring Framework
- Each answer is evaluated on four dimensions:
  - Analytical thinking
  - Technical Depth
  - Business Insight
  - Communication
- Each criterion is scored [1–10] and averaged per response
- Round-level and overall scores are derived
- Final hiring recommendations:
  - `Strong Hire` (≥ 8.5)
  - `Lean Hire` (7.0–8.4)
  - `No Hire` (< 7.0)

### 🔹 Phase 4: Report Generation
- For each candidate, the system:
  - Aggregates scores
  - Embeds performance charts
  - Attaches round-wise feedback
  - Creates an HTML summary report

### 🔹 Phase 5: Real-Time Dashboard (Streamlit)
- A user-friendly dashboard built with Streamlit:
  - Candidate Selector
  - Score + recommendation display
  - Embedded performance chart
  - Interactive Q&A per round with evaluator feedback
- Supports dropdowns, custom styling, and expandable components
**Backend Features**
  - Automatic discovery of reports/transcripts
  - Complied transcript dictionaries
  - Profile + transcript syncing

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

## 7. Evaluation & Scoring Framework

### 7.1 Overview

Each candidate answer is evaluated using a second LLM with a strict JSON schema.

### 7.2 Scoring Schema

{
  "score": 8.2,
  "feedback": "Clear, technically sound, business-aligned.",
  "dimensions": {
    "communication": 8,
    "technical_accuracy": 7.5,
    "relevance": 9
  }
}

### 7.3 Aggregation Logic

Per round:  
`mean(score_i)`  
Overall:  
`mean(score_r)`

### 7.4 Recommendation Logic

| Score Range | Verdict       |
|-------------|---------------|
| ≥ 8.5       | Strong Hire   |
| 7.0–8.49    | Lean Hire     |
| < 7.0       | No Hire       |

## 8. Impact and Use Cases
- Internal candidate simulation & benchmarking tools
- AI-based resume review assistants
- Technical hiring augmentation for startups
- Talent development platforms with LLMs
