import os
import json
import random
from pathlib import Path
from dotenv import load_dotenv
import datetime
import re
from memory import update_memory, get_all_previous_memory, normalize
from sentence_transformers import SentenceTransformer, util
import torch
from question_duplication import is_semantic_duplicate

from langchain_community.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

#Load API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#Load Sentence Transformer
embedder = SentenceTransformer('all-MiniLM-L6-v2')

#Global Memory
covered_topics = set()
mentioned_projects = set()
used_projects = set()
used_metrics = set()

#Job Description
job_description = """
Job Title: Data Analyst  
Company: Novalytix Insights

Company Overview:
Novalytix Insights is a fast-growing analytics and intelligence firm specializing in delivering data-driven solutions to mid-size and enterprise clients across healthcare, fintech, and retail sectors. Our mission is to empower organizations to unlock value from their data and make smarter decisions with confidence.

Role Summary:
We are seeking a highly analytical and detail-oriented Data Analyst to join our Insights & Strategy team. In this role, you will transform raw data into actionable insights that drive business performance, operational efficiency, and customer satisfaction. You will work cross-functionally with business stakeholders, data engineers, and product teams to deliver high-impact analytics solutions.

Key Responsibilities:
- Collect, clean, and validate data from multiple sources to ensure data quality and integrity.
- Design and build dashboards and reports that communicate trends, forecasts, and performance metrics.
- Conduct exploratory data analysis (EDA) and use statistical techniques to identify patterns and business opportunities.
- Collaborate with stakeholders to define key performance indicators (KPIs) and support data-driven decision-making.
- Present insights and findings to both technical and non-technical audiences through visual storytelling.
- Partner with data engineers to improve data pipelines and automate data collection processes.

Required Qualifications:
- Bachelor’s degree in Statistics, Mathematics, Computer Science, Economics, or a related field.
- 2–4 years of experience in a data analyst or similar analytical role.
- Proficiency in SQL and one or more of the following: Python, R, or Excel.
- Experience with BI tools such as Tableau, Power BI, or Looker.
- Strong communication skills with the ability to translate complex data into clear insights.

Preferred Skills:
- Experience in the healthcare, fintech, or retail industries.
- Knowledge of data warehousing and cloud platforms like Snowflake, BigQuery, or AWS.
- Familiarity with A/B testing and statistical inference methods.
- Exposure to predictive analytics or machine learning workflows.

Benefits:
- Competitive salary with annual performance bonuses.
- Flexible working hours and remote work options.
- Health, dental, and vision insurance.
- 401(k) with company matching.
- Generous PTO and paid holidays.
- Learning and development stipend.

Novalytix Insights is an equal opportunity employer. We celebrate diversity and are committed to creating an inclusive environment for all employees.
"""



def extract_topic_from_question(q):
    topic_map = {
    "technical_sql": ["sql", "joins", "group by", "cte", "subquery"],
    "technical_r": ["r", "ggplot", "dplyr", "shiny", "tidyverse"],
    "technical_python": ["python", "pandas", "sklearn", "matplotlib", "seaborn"],
    "technical_modeling": ["regression", "classifier", "predictive model", "machine learning"],
    "eda": ["eda", "exploratory", "exploration", "distribution", "outliers"],
    "soft_collaboration": ["stakeholder", "collaboration", "cross-functional", "teamwork"],
    "soft_communication": ["presentation", "storytelling", "communication", "explained"],
    "soft_conflict": ["conflict", "disagreement", "pushback", "resolve"],
    "soft_initiative": ["initiative", "proactive", "ownership", "independent"],
    "soft_failure": ["failure", "mistake", "learned", "overcame"],
    "soft_time_management": ["deadline", "time", "prioritize", "multi-task"],
    "business_strategy": ["trade-off", "strategy", "decision-making", "impact"],
    "data_quality": ["missing data", "validation", "cleaning", "inconsistency"],
    "visualization": ["tableau", "dashboard", "charts", "storytelling"],
    }
    for canonical_topic, keywords in topic_map.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", q, re.IGNORECASE):
                return canonical_topic
    return "general"

#Load a random profile
def load_random_profile():
    profile_dir = Path("data/profiles")
    profiles = list(profile_dir.glob("*.json"))
    selected_path = random.choice(profiles)
    with open(selected_path, "r") as f:
        data = json.load(f)
        print(f"🧑 Interviewing: {data['name']} ({selected_path.name})")
    return data

#Format profile into string

def format_resume_text(profile):
    if isinstance(profile, Path):
        with open(profile, "r") as f:
            profile = json.load(f)
    
    summary = profile.get("summary", "")
    education = "\n".join([f"{e['degree']} from {e['institution']} ({e['year']})" for e in profile.get("education", [])])
    experience = "\n".join([f"{e['title']} at {e['company']} ({e['years']}): {e['description']}" for e in profile.get("experience", [])])
    skills = ", ".join(profile.get("skills", []))
    projects = "\n".join([f"{p['name']}: {p['description']}" for p in profile.get("projects", [])])
    tools = ", ".join(profile.get("tools", []))

    return f"""
Summary:
{summary}

Education:
{education}

Experience:
{experience}

Skills:
{skills}

Projects:
{projects}

Tools:
{tools}
""".strip()

def resolve_profile(profile):
    if isinstance(profile, Path):
        with open(profile, "r") as f:
            return json.load(f)
    elif isinstance(profile, str):
        with open(profile, "r") as f:
            return json.load(f)
    return profile

#Interview Loop
def run_interview(profile, num_questions = 6, round_name = 'Round_1_Technical'):
    profile = resolve_profile(profile)
    resume_text = format_resume_text(profile)
    project_titles = [p["name"].lower() for p in profile.get("projects", [])]
    candidate_name = profile.get('name') or "Candidate"
    forbidden_topics, forbidden_projects = get_all_previous_memory(candidate_name, round_name)
    previous_answers = []
    previous_embeddings = []
    semantic_reused = False

    print(f"📄 Running interview for: {candidate_name}")

    #Interviewing agent
    base_interviewer_prompt = f"""
You are acting as a senior data science interviewer conducting the **{round_name}** of a real-time interview for a Data Analyst position.
Understand the nuances of the job description and round name to tailor the questions and ensure the candidate is not repeating themselves and the right questions are being asked.

Here is the Job Description, Tailor the questions to the job description.

Job Description:
---------------------
{job_description}
---------------------

Follow these instructions carefully:

1. Ask **only one** question at a time.
2. Your questions must evaluate the candidate’s **technical expertise**, **analytical thinking**, and **behavioral fit**, with a focus appropriate to the **{round_name}**.
3. Base your questions specifically on the candidate's resume provided below.
4. Do **not** answer or simulate responses for the candidate.
5. Keep your tone **professional**, **concise**, and **neutral**—just like in a real interview.
6. After each candidate response, determine whether to:
    - Ask a follow-up to probe deeper,
    - Ask for clarification, or
    - Transition to a new topic relevant to the round.
7. Your goal is to cover **new** topics in each round. DO NOT ask questions about previously discussed topics or reworded project examples

Candidate Resume:
---------------------
{resume_text}
---------------------

Begin the interview by asking your first question. You are human, avoid robotic responses and patterns.
"""
    candidate_prompt = f"""
You are a data analyst participating in a job interview. This is the **{round_name}** of the interview process.
You are given a job description and a candidate resume.

Answer each interview question truthfully and confidently **as yourself**, based **only** on the information in the resume below.

Instructions:
1. Do **not** invent or exaggerate any skills, experiences, or qualifications that are not explicitly mentioned in your resume.
2. Stay fully in character as a professional data analyst whose background matches the resume provided.
3. Tailor your answers to reflect the focus of this round (**{round_name}**) while using clear, relevant, and technically accurate language.
4. If a question refers to something outside the scope of your resume, acknowledge it politely and honestly.
5. Maintain a tone that is **confident**, **authentic**, and **professionally concise**.
6. Do NOT reuse the same project (e.g., Patient Flow Optimization) or metric (e.g., 15% improvement) across multiple answers unless explicitly asked. Use different examples to showcase range.

Your Resume:
---------------------
{resume_text}
---------------------

Job Description:
---------------------
{job_description}
---------------------

You are human, avoid robotic responses and patterns.
"""
    evaluation_prompt_template = """
You are a senior evaluator on a data science hiring panel.

Your task is to critically evaluate the candidate’s response based on the interview question and the scoring criteria provided below.

Question:
{question}

Answer:
{answer}

Scoring Criteria (Rate each from 1 = Poor to 4 = Excellent):
1. Analytical Problem-Solving – Does the candidate demonstrate structured thinking and critical reasoning?
2. Technical Proficiency – Are appropriate tools, methods, or techniques applied or explained clearly?
3. Business Insight – Does the candidate connect their work to business goals, user needs, or impact?
4. Communication & Explanation – Is the response clear, direct, and professionally articulated?

Also include:
- Overall Score (1–10): A holistic judgment of the candidate’s performance for this answer.
- Feedback Summary: A concise comment (1–2 sentences) highlighting strengths or weaknesses.

Guidelines:
- Be brutally honest. This evaluation may influence hiring decisions.
- Do not sugarcoat. If the answer lacks depth, say so.
- Do not be robotic or generic. Provide human, thoughtful feedback.
- If the candidate reuses ANY project or claim (even paraphrased), set "reused_project" = true.
- Penalize repetition explicitly. Drop overall_score by 1–2 points unless reused by instruction.
- Provide clear reasons in "penalty_reason".

Respond strictly in this raw JSON format (no markdown, no extra text):

{{
  "analytical_score": 1-4,
  "technical_score": 1-4,
  "business_score": 1-4,
  "communication_score": 1-4,
  "overall_score": 1-10,
  "reused_project": true/false,
  "penalty_reason": "If repetition is found, explain clearly. Otherwise, leave blank."
  "feedback": "Your concise evaluation here (2-3 sentences)."
}}
Consider all the following information when scoring:
Previously Mentioned Projects:
{used_projects}

Previously Used Metrics or Claims:
{used_metrics}

Forbidden Topics for this Round:
{forbidden_topics}

Forbidden Projects for this Round:
{forbidden_projects}

Semantic Reuse:
{semantic_reused}

Be Brutally Honest. You are a senior data science interview evaluator. Do not be afraid to be harsh. Do not be robotic.
Strictly follow these instructions. DO NOT overlook repetition. Penalize it even if the response is well-structured.
Do not be afraid to be harsh or reject candidates outright.
"""
    round_type_context = {
   "Round_1_Technical": """
This round evaluates the candidate’s technical expertise, hands-on execution ability, and problem-solving skills.
Ask questions that assess tools, modeling techniques, code workflows, data pipelines, or quantitative methods. Avoid strategic or behavioral scenarios.

Focus Areas:
- Proficiency with tools: SQL, Python, R
- Techniques: Exploratory Data Analysis (EDA), statistical modeling, data visualization
- Use cases: forecasting, segmentation, pipeline development, healthcare analytics

Strict Exclusions:
- Do NOT ask about stakeholder collaboration, business strategy, or leadership scenarios.
- Stay focused on technical execution and analytical depth only.
""",

    "Round_2_Behavioral": """
This round assesses the candidate’s interpersonal effectiveness, adaptability, and communication skills in real-world scenarios.
Ask situational or STAR-based behavioral questions. Focus on teamwork, failure, communication, and ambiguity. Avoid technical project walk-throughs.

Focus Areas:
- Teamwork, cross-functional collaboration, and conflict resolution
- Handling ambiguity, showing initiative, and owning outcomes
- Examples of impact, failure recovery, and professional growth

- Topics to cover (pick varied ones across questions):
    - Cross-functional collaboration
    - Communication breakdowns
    - Handling difficult stakeholders
    - Learning from failure
    - Dealing with ambiguity
    - Showing initiative or ownership
    - Managing tight deadlines or conflicting priorities
    - Giving or receiving feedback
    - Conflict resolution within teams

Strict Exclusions:
- Do NOT ask technical or tool-specific questions.
- Prioritize situational and behavioral storytelling, not technical detail.
- Technical implementations
- Tool-specific discussions
- Project metric repetition
""",

    "Round_3_Hiring_Manager": """
This round evaluates the candidate’s strategic thinking, leadership potential, and alignment with business goals.
Focus on strategy, business impact, tradeoffs, and decision-making. Avoid tool-specific or tactical execution details unless framed as strategic decisions.

Focus Areas:
- Business acumen, stakeholder management, and decision-making
- Trade-off analysis, long-term planning, and initiative ownership
- Communicating effectively with executives and aligning with company strategy

Strict Exclusions:
- Avoid deep dives into technical implementation or tool usage.
- Focus on big-picture thinking and leadership readiness.
"""
}
    

    #Setup agents
    interviewer = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = 0.7)
    candidate = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = 0.8)
    evaluator = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = 0.3)
    
    memory = ConversationBufferMemory()

    #Log Transcript
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path('transcripts')
    log_dir.mkdir(exist_ok = True)
    jsonl_path = log_dir / f"{candidate_name.replace(' ', '_')}_{round_name}.jsonl"
    txt_path = log_dir / f"{candidate_name.replace(' ', '_')}_{round_name}.txt"

    print(f"\n🧪 Starting Interview: {round_name}\n" + "-" * 60)

    with open(jsonl_path, 'w') as jf, open(txt_path, 'w') as tf:
        for i in range(num_questions):
            #Get round type context
            round_context = round_type_context.get(round_name, "")
            round_context_prompt = f"""
You are acting as a senior interviewer for the **{round_name}** of a Data Analyst interview.

Context:
- You are evaluating a candidate for the following role:
{job_description}

Round Focus:
{round_context}

Guidelines:
1. Ask only **one** question at a time.
2. Tailor your questions to the goals of the **{round_name}** round.
3. Do **not** repeat topics or reword project examples already discussed in earlier rounds.
4. Base your questions on the candidate's resume, role requirements, and round-specific priorities.
5. Keep the tone professional, neutral, and concise.
6. After each response, decide whether to:
   - Probe deeper,
   - Ask for clarification, or
   - Move to another relevant topic.

You must vary the theme of each behavioral question. Rotate across these categories without repeating within the same round:
- Working with a difficult person
- Handling ambiguity or vague expectations
- Receiving/giving feedback
- Failing and recovering
- Taking initiative or ownership without instruction
- Managing deadlines and time pressure

Candidate Resume:
---------------------
{resume_text}
---------------------

Begin the interview by asking your first question.
STRICT INSTRUCTION: You must NOT ask about these topics or projects again:
Topics: {', '.join(forbidden_topics) or 'None'}
Projects: {', '.join(forbidden_projects) or 'None'}
"""
            
            dynamic_interviewer_prompt = base_interviewer_prompt + round_context_prompt
            
            #Interviewer asks
            question_prompt = [
                SystemMessage(content = dynamic_interviewer_prompt),
                HumanMessage(content = "Ask the next question.")
            ]
            max_attempts = 6
            for attempt in range(max_attempts):
                question = interviewer.invoke(question_prompt).content.strip()
                if not is_semantic_duplicate(question):
                    break
                #else:
                    #print(f"⚠️ Skipped semantically similar question (attempt {attempt + 1})")
            #else:
                #print(f"❌ Failed to generate a non-duplicate question after {max_attempts} attempts")
                
            topic = extract_topic_from_question(question)
            covered_topics.add(topic)

            print(f"\n👩‍💼 Interviewer: {question}")
            tf.write(f"\n👩‍💼 Interviewer: {question}\n")

            #Candidate answers
            answer_prompt = [
                SystemMessage(content = candidate_prompt),
                HumanMessage(content = question)
            ]
            answer = candidate.invoke(answer_prompt).content.strip()

            print(f"\n👨‍💼 Candidate: {answer}")
            tf.write(f"\n👨‍💼 Candidate: {answer}\n")

            update_memory(candidate_name, round_name, topic)

            for proj in project_titles:
                if normalize(proj) in normalize(answer):
                    mentioned_projects.add(proj)
                    used_projects.add(proj)
            
            for phrase in ["15% reduction", "20% efficiency", "readmission", "forecasting accuracy"]:
                if phrase in answer.lower():
                    used_metrics.add(phrase)

            current_embedding = embedder.encode(answer, convert_to_tensor = True)
            semantic_reused = False
            if previous_embeddings:
                cosine_scores = util.cos_sim(current_embedding, torch.stack(previous_embeddings))
                if cosine_scores.max().item() > 0.80:
                    semantic_reused = True
            previous_answers.append(answer)
            previous_embeddings.append(current_embedding)
                
            #Evaluate answer
            eval_prompt = evaluation_prompt_template.format(
                question = question,
                answer = answer,
                used_projects = ", ".join(sorted(used_projects)) or 'None',
                used_metrics = ", ".join(sorted(used_metrics)) or 'None',
                forbidden_projects = ", ".join(sorted(forbidden_projects)) or 'None',
                forbidden_topics = ", ".join(sorted(forbidden_topics)) or 'None',
                semantic_reused = semantic_reused
            )

            eval_response = evaluator.invoke([
                SystemMessage(content = eval_prompt)]).content
            try:
                evaluation = json.loads(eval_response)
            except json.JSONDecodeError:
                print("\n⚠️ Evaluation JSON Parse Failed:\n", eval_response)
                evaluation = {
                    "analytical_score": None,
                    "technical_score": None,
                    "business_score": None,
                    "communication_score": None,
                    "overall_score": None,
                    "reused_project": None,
                    "penalty_reason": "JSON parse failed",
                    "feedback": eval_response[:100]
            }

            if semantic_reused:
                evaluation['reused_project'] = True
                evaluation['penalty_reason'] = "Answer is semantically similar to a previous one"
                if evaluation.get('overall_score') and isinstance(evaluation['overall_score'], int):
                    evaluation['overall_score'] = max(1, evaluation['overall_score'] - 2)
            
            #Log all
            log_entry = {
                'turn': i + 1,
                'candidate_name': candidate_name,
                'round_name': round_name,
                'timestamp': timestamp,
                'question': question,
                'answer': answer,
                'evaluation': evaluation,
            }
            jf.write(json.dumps(log_entry) + "\n")
            tf.write(f"📝 Evaluation: {json.dumps(evaluation, indent=2)}\n")

            #Memory
            memory.chat_memory.add_user_message(question)
            memory.chat_memory.add_ai_message(answer)

        #Final evaluator Summary
        qa_summary_text = "\n".join(
            [f"Q: {q}\nA: {a}" for q, a in zip(memory.chat_memory.messages[::2], memory.chat_memory.messages[1::2])]
        )

        final_summary_prompt = f"""
You are a senior evaluator on the data science hiring team.

Below is a transcript of the candidate's interview in Q&A format. Carefully review the entire exchange and assess the candidate’s performance holistically.

Transcript:
---------------------
{qa_summary_text}
---------------------

Instructions:
Write a **concise, professional summary** (1–2 paragraphs) that covers:
- Key **strengths** demonstrated by the candidate.
- Notable **weaknesses**, gaps, or areas for improvement.
- A clear **hiring recommendation**, choosing one of the following:
  - **Strong Hire**
  - **Lean Hire**
  - **No Hire**

Make sure your summary is based entirely on the candidate’s answers and reflects performance relevant to a Data Analyst role.
"""

        final_summary = evaluator.invoke([
            SystemMessage(content = final_summary_prompt)
        ]).content.strip()

        tf.write("\n🧾 Final Interview Summary:\n")
        tf.write(final_summary + "\n")
        #print("\n🧾 Final Interview Summary:\n", final_summary)

    print(f"\n✅ Interview Complete. Transcript saved: {jsonl_path}")

def run_multi_rounds(profile, rounds):
    for round_name, num_questions in rounds:
        run_interview(profile, num_questions, round_name)

if __name__ == "__main__":
    profile = load_random_profile()
    rounds = [
        ("Round_1_Technical", 5),
        ("Round_2_Behavioral", 4),
        ("Round_3_Hiring_Manager", 3)
    ]
    run_multi_rounds(profile, rounds)