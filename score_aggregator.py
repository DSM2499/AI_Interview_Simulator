import os
import json
from pathlib import Path
from collections import defaultdict

TRANSCRIPT_DIR = Path("transcripts")

ROUND_MAP = {
    "Round": {
        "1": "Technical",
        "2": "Behavioral",
        "3": "Manager"
    },
    "Hiring": "Manager"
}

def map_round_name(name_parts):
    if "Round" in name_parts:
        idx = name_parts.index("Round")
        round_number = name_parts[idx + 1] if idx + 1 < len(name_parts) else "Unknown"
        return ROUND_MAP.get("Round", {}).get(round_number, f"Round {round_number}")
    elif "Hiring" in name_parts:
        return ROUND_MAP["Hiring"]
    else:
        return "Unknown"

def normalize_candidate_name(name_parts):
    if "Round" in name_parts:
        idx = name_parts.index("Round")
        return " ".join(name_parts[:idx])
    elif "Hiring" in name_parts:
        idx = name_parts.index("Hiring")
        return " ".join(name_parts[:idx])
    else:
        return " ".join(name_parts)

def load_transcripts(transcript_dir):
    scores = defaultdict(lambda: defaultdict(list))
    for file in Path(transcript_dir).glob("*.jsonl"):
        name_parts = file.stem.split("_")
        candidate_name = normalize_candidate_name(name_parts)
        round_label = map_round_name(name_parts)
        with open(file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    eval_data = data.get("evaluation", {})
                    if eval_data.get("overall_score") is not None:
                        scores[candidate_name][round_label].append(eval_data["overall_score"])
                except json.JSONDecodeError:
                    continue
    return scores

def average(lst):
    return round(sum(lst) / len(lst), 2) if lst else 0.0

def recommend(overall):
    if overall >= 8.5:
        return "Strong Hire"
    elif overall >= 7.0:
        return "Lean Hire"
    else:
        return "No Hire"

def aggregate_scores():
    transcript_dir = Path("transcripts")
    output_file = Path("results/aggregated_scores.json")
    output_file.parent.mkdir(exist_ok=True)

    transcripts = load_transcripts(transcript_dir)
    final_scores = []

    for candidate, rounds in transcripts.items():
        round_scores = {}
        all_scores = []
        for round_name, values in rounds.items():
            avg_score = average(values)
            round_scores[round_name] = avg_score
            all_scores.extend(values)
        overall_score = average(all_scores)
        final_scores.append({
            "candidate_name": candidate,
            "round_scores": round_scores,
            "overall_score": overall_score,
            "recommendation": recommend(overall_score)
        })

    with open(output_file, "w") as f:
        json.dump(final_scores, f, indent=2)
    print(f"✅ Aggregated scores saved to {output_file}")

if __name__ == "__main__":
    aggregate_scores()
