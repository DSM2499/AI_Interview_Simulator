import sys
import json
import shutil
import argparse
from pathlib import Path
from uuid import uuid4
import subprocess

# Import necessary functions (assuming these modules exist and are in the same directory)
from interview_engine import run_multi_rounds, run_interview
from score_aggregator import aggregate_scores
from generate_reports import generate_all_reports
from generate_profile import generate_profile_from_resume

PROFILE_DIR = Path("data/profiles")

def load_profile_from_json(json_path):
    with open(json_path, 'r') as f:
        profile = json.load(f)
    candidate_id = profile["name"].replace(" ", "_") + f"_{uuid4().hex[:6]}"
    output_path = PROFILE_DIR / f"{candidate_id}.json"
    with open(output_path, 'w') as out:
        json.dump(profile, out, indent=2)
    print(f"✅ Loaded profile JSON and saved to {output_path}")
    return output_path

def run_full_simulation(input_path, is_resume = True):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    if is_resume:
        profile_path = generate_profile_from_resume(input_path)
    else:
        profile_path = load_profile_from_json(input_path)
    
    print(f"🚀 Running interview simulation for: {Path(profile_path).name}")
    rounds = [
        ("Round_1_Technical", 5),
        ("Round_2_Behavioral", 4),
        ("Round_3_Hiring_Manager", 3)
    ]
    run_multi_rounds(profile_path, rounds)

    print("📊 Aggregating scores...")
    aggregate_scores()

    print("📝 Generating final reports...")
    generate_all_reports()

    print("✅ Full simulation completed. Dashboard and reports updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Run full AI Interview simulation pipeline.")
    parser.add_argument("input", help = "Path to resume (PDF) or profile (JSON)")
    parser.add_argument("--json", action = "store_true", help="Flag if input is already a JSON profile")

    args = parser.parse_args()
    input_path = Path(args.input)
    is_resume = not args.json

    if not input_path.exists():
        print("❌ Error: Input file does not exist.")
        sys.exit(1)

    run_full_simulation(input_path, is_resume)
    print("🚀 Launching the dashboard...")
    subprocess.run(["streamlit", "run", "app.py"])