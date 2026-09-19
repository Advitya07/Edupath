from app.config.settings import get_settings

TRACKS = {
    "Full Stack Engineer": ["JavaScript", "React", "APIs", "SQL", "Docker", "System Design"],
    "ML Engineer": ["Python", "SQL", "Machine Learning", "PyTorch", "MLOps", "System Design"],
    "DevOps": ["Linux", "Git", "Docker", "CI/CD", "Kubernetes", "AWS"],
    "Data Scientist": ["Python", "SQL", "Pandas", "Statistics", "Machine Learning", "Storytelling"],
    "Cloud Architect": ["Linux", "Networking", "AWS", "Security", "Terraform", "System Design"],
}


def make_roadmap(career: str, scores: dict[str, float], skills: list[str]) -> dict:
    topics = TRACKS.get(career, TRACKS["Full Stack Engineer"])
    nodes = []
    for index, topic in enumerate(topics):
        score = round(scores.get(topic, 72 if topic in skills else 42), 1)
        status = "completed" if score >= 80 else "in_progress" if score >= 55 else "weak_gap"
        nodes.append({"id": topic.lower().replace(" ", "-"), "topic": topic, "mastery": score, "status": status,
                      "position": {"x": 70 + (index % 3) * 280, "y": 80 + (index // 3) * 230}})
    edges = [{"id": f"e-{nodes[i]['id']}-{nodes[i+1]['id']}", "source": nodes[i]["id"], "target": nodes[i + 1]["id"], "animated": nodes[i]["status"] == "in_progress"} for i in range(len(nodes) - 1)]
    return {"career_target": career, "nodes": nodes, "edges": edges, "completion": round(sum(n["mastery"] for n in nodes) / len(nodes), 1)}
