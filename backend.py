import json
from pathlib import Path
from collections import defaultdict

# ----------- Constants -----------
TRANSCRIPT_DIR = Path("transcripts")
PROFILE_DIR = Path("data/profiles")
REPORT_DIR = Path("reports")
SCORES_PATH = Path("results/aggregated_scores.json")
COMPILED_TRANSCRIPT_DIR = Path("compiled_transcripts")
COMPILED_TRANSCRIPT_DIR.mkdir(exist_ok=True)

def load_profiles(path="results/aggregated_scores.json"):
    with open(path) as f:
        data = json.load(f)
    
    # Convert list of profiles into dict keyed by candidate_name
    profiles = {entry["candidate_name"]: entry for entry in data}
    return profiles

def load_transcripts(candidate_name):
    all_files = list(Path("transcripts").glob(f"{candidate_name.replace(' ', '_')}_*.jsonl"))
    transcript_by_round = {}

    for file in all_files:
        try:
            qna = []
            with open(file) as f:
                for line in f:
                    obj = json.loads(line)
                    if "question" in obj and "answer" in obj and "evaluation" in obj:
                        qna.append({
                            "question": obj["question"],
                            "answer": obj["answer"],
                            "feedback": obj["evaluation"].get("feedback", "No feedback")
                        })
            round_name_parts = file.stem.split("_")
            round_name = round_name_parts[-2] if "Round" in round_name_parts[-3] else round_name_parts[-3]
            transcript_by_round[round_name] = {"qna": qna}

            # Save compiled version for that round
            compiled_path = COMPILED_TRANSCRIPT_DIR / f"{candidate_name.replace(' ', '_')}_{round_name}_compiled.json"
            with open(compiled_path, "w") as out_file:
                json.dump(qna, out_file, indent = 2)

        except Exception as e:
            print(f"❌ Failed to parse {file.name}: {e}")
    return transcript_by_round

def load_scores():
    with open(SCORES_PATH, "r") as f:
        return json.load(f)

def load_reports():
    reports = {}
    for file in REPORT_DIR.glob("*.html"):
        name = file.stem.replace("_report", "").replace("_", " ")
        reports[name] = str(file)
    return reports

# Generate compiled transcripts for all profiles
def compile_all_transcripts():
    profiles = load_profiles()
    for candidate_name in profiles:
        load_transcripts(candidate_name)
    return f"✅ Compiled transcripts saved in {COMPILED_TRANSCRIPT_DIR}"