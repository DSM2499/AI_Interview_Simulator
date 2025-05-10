import streamlit as st
from backend import load_profiles, load_transcripts, load_scores, load_reports, compile_all_transcripts
from pathlib import Path
# Load all data
profiles = load_profiles()
scores = load_scores()
reports = load_reports()

round_mapping = {
    '1': 'Technical',
    '2': 'Behavioral',
    '3': 'Managerial'
}

# Title
st.set_page_config(page_title="AI Interview Review", layout="wide")
st.title("📊 AI Interview Evaluation Dashboard")

# Sidebar: Candidate Selector
candidate_names = sorted(profiles.keys())
selected_name = st.sidebar.selectbox("Select Candidate", candidate_names)
transcripts = load_transcripts(selected_name)

# Show Resume Summary
st.header(f"🧑‍💼 Resume Overview: {selected_name}")
profile = profiles[selected_name]

# Safely extract fields with fallback
summary = profile.get("summary") or "N/A"
skills = profile.get("skills") or []
tools = profile.get("tools") or []

if isinstance(skills, str):
    skills = [s.strip() for s in skills.split(",") if s.strip()]
if isinstance(tools, str):
    tools = [t.strip() for t in tools.split(",") if t.strip()]

st.markdown(f"**Summary**: {summary}")
st.markdown(f"**Skills**: {', '.join(skills) if skills else 'N/A'}")
st.markdown(f"**Tools**: {', '.join(tools) if tools else 'N/A'}")

with st.expander("📘 View Full Resume"):
    st.markdown("### Education")
    for edu in profile.get("education", []):
        st.markdown(f"- {edu['degree']} at {edu['institution']} ({edu['year']})")

    st.markdown("### Experience")
    for exp in profile.get("experience", []):
        st.markdown(f"- **{exp['title']}** at *{exp['company']}* ({exp['years']}): {exp['description']}")

    st.markdown("### Projects")
    for proj in profile.get("projects", []):
        st.markdown(f"- **{proj['name']}**: {proj['description']}")

# Show Scores
st.header("📈 Round-wise Performance")

candidate_score = next((item for item in scores if item["candidate_name"] == selected_name), None)
if candidate_score:
    st.metric("Final Score", candidate_score["overall_score"])
    st.metric("Recommendation", candidate_score["recommendation"])
    st.bar_chart(candidate_score["round_scores"])
else:
    st.warning("No score data available.")

# Show Interview Transcripts
transcripts = load_transcripts(selected_name)
st.subheader("🧾 Interview Q&A")

with st.expander("🧾 Interview Q&A"):
    for round_name, round_data in transcripts.items():
        st.markdown(f"<div class='round-header'> 📋 Round {round_name} ({round_mapping[round_name]})</div>", unsafe_allow_html=True)
        for i, qa in enumerate(round_data["qna"]):
            st.markdown(f"<div class='question'>Q{i+1}: {qa['question']}\n</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='answer'>A{i+1}: {qa['answer']}\n</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='feedback-box'>🔍 <strong>Evaluator Feedback:</strong> {qa['feedback']}\n</div>", unsafe_allow_html=True)
            st.markdown("---")
        st.markdown("---")

# Show Report
st.header("📄 Full Interview Report")
if selected_name in reports:
    report_path = reports[selected_name]
    with open(report_path, "r") as f:
        html = f.read()
        st.components.v1.html(html, height=800, scrolling=True)
    st.download_button("📥 Download Report", html, file_name=Path(report_path).name, mime="text/html")
else:
    st.info("No report available for this candidate.")
