import os
import json
from pathlib import Path
import matplotlib.pyplot as plt
from io import BytesIO
import base64

TRANSCRIPTS_DIR = Path("transcripts")
AGGREGATED_PATH = Path("results/aggregated_scores.json")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# ----------- Plot Round-wise Score Chart -----------
def plot_scores(round_scores, candidate_name):
    fig, ax = plt.subplots()
    rounds = list(round_scores.keys())
    scores = list(round_scores.values())
    ax.bar(rounds, scores)
    ax.set_ylim(0, 10)
    ax.set_title(f"Round-wise Performance for {candidate_name}")
    ax.set_ylabel("Score (out of 10)")
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    img_data = base64.b64encode(buffer.read()).decode("utf-8")
    return f'<img src="data:image/png;base64,{img_data}" />'

# ----------- Extract Feedback by Scanning all Matching Files -----------
def extract_feedback(candidate_name):
    feedback_by_round = {}
    all_files = list(TRANSCRIPTS_DIR.glob(f"{candidate_name.replace(' ', '_')}_*.jsonl"))

    for file in all_files:
        parts = file.stem.split("_")
        # Find round name based on the last word(s)
        if "Technical" in parts:
            round_key = "Technical"
        elif "Behavioral" in parts:
            round_key = "Behavioral"
        elif "Manager" in parts:
            round_key = "Manager"
        else:
            continue

        feedback_list = []
        with open(file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ev = entry.get("evaluation", {})
                    if ev.get("feedback"):
                        feedback_list.append(ev["feedback"])
                except json.JSONDecodeError:
                    continue

        feedback_by_round[round_key] = "<br>".join(feedback_list) if feedback_list else "No feedback recorded."
    return feedback_by_round

# ----------- Build a Single Candidate's HTML Report -----------
def build_html_report(candidate):
    name = candidate["candidate_name"]
    round_scores = candidate["round_scores"]
    overall = candidate["overall_score"]
    reco = candidate["recommendation"]

    chart = plot_scores(round_scores, name)
    feedback_by_round = extract_feedback(name)

    feedback_blocks = ""
    for round_name in round_scores:
        fb = feedback_by_round.get(round_name, "No feedback found.")
        feedback_blocks += f"<h4>{round_name}</h4><p>{fb}</p>"

    html = f"""
    <html>
    <head>
        <title>Interview Summary - {name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            .summary {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
            h4 {{ color: #2c3e50; margin-top: 20px; }}
            p {{ line-height: 1.6; }}
        </style>
    </head>
    <body>
        <h1>Interview Summary: {name}</h1>
        <div class="summary">
            <p><strong>Final Score:</strong> {overall}/10</p>
            <p><strong>Recommendation:</strong> <b>{reco}</b></p>
        </div>
        <hr>
        <h2>Round-wise Scores</h2>
        {chart}
        <hr>
        <h2>Evaluator Feedback</h2>
        {feedback_blocks}
    </body>
    </html>
    """
    return html

# ----------- Generate Reports for All Candidates -----------
def generate_all_reports():
    with open(AGGREGATED_PATH, 'r') as f:
        data = json.load(f)

    for candidate in data:
        html = build_html_report(candidate)
        filename = REPORTS_DIR / f"{candidate['candidate_name'].replace(' ', '_')}_report.html"
        with open(filename, 'w') as f:
            f.write(html)
        print(f"✅ Report saved: {filename}")

if __name__ == "__main__":
    generate_all_reports()
