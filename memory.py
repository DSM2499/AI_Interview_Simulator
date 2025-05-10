import json
from pathlib import Path

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)

def normalize(text):
    import re
    return re.sub(r"[^a-z0-9 ]", "", text.lower())

def memory_path(candidate_name):
    return MEMORY_DIR / f"memory_{candidate_name.replace(' ', '_')}.json"

def load_memory(candidate_name):
    path = memory_path(candidate_name)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    else:
        return {}

def save_memory(candidate_name, memory_dict):
    path = memory_path(candidate_name)
    with open(path, "w") as f:
        json.dump(memory_dict, f, indent=2)

def update_memory(candidate_name, round_name, topic=None, project=None):
    memory = load_memory(candidate_name)
    round_mem = memory.get(round_name, {"topics": [], "projects": []})

    if topic and topic not in round_mem["topics"]:
        round_mem["topics"].append(topic)
    if project and project not in round_mem["projects"]:
        round_mem["projects"].append(project)

    memory[round_name] = round_mem
    save_memory(candidate_name, memory)

def get_all_previous_memory(candidate_name, current_round):
    memory = load_memory(candidate_name)
    all_topics = set()
    all_projects = set()
    for rnd, data in memory.items():
        if rnd != current_round:
            all_topics.update(data.get("topics", []))
            all_projects.update(data.get("projects", []))
    return sorted(all_topics), sorted(all_projects)
