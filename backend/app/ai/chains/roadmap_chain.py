TRACKS = {
    "Full Stack Engineer": ["JavaScript", "React", "APIs", "SQL", "Docker", "System Design"],
    "ML Engineer": ["Python", "SQL", "Machine Learning", "PyTorch", "MLOps", "System Design"],
    "DevOps": ["Linux", "Git", "Docker", "CI/CD", "Kubernetes", "AWS"],
    "Data Scientist": ["Python", "SQL", "Pandas", "Statistics", "Machine Learning", "Storytelling"],
    "Cloud Architect": ["Linux", "Networking", "AWS", "Security", "Terraform", "System Design"],
}


def _node_id(topic: str) -> str:
    return topic.lower().replace(" ", "-").replace("/", "-")


def _status(score: float) -> str:
    return "completed" if score >= 80 else "in_progress" if score >= 55 else "weak_gap"


def _priority(score: float) -> str:
    return "high" if score < 55 else "medium" if score < 80 else "low"


def make_roadmap(career: str, scores: dict[str, float], skills: list[str]) -> dict:
    topics = TRACKS.get(career, TRACKS["Full Stack Engineer"])
    nodes = []
    for index, topic in enumerate(topics):
        score = round(scores.get(topic, 72 if topic in skills else 42), 1)
        nodes.append({"id": _node_id(topic), "topic": topic, "mastery": score, "status": _status(score),
                      "priority": _priority(score), "position": {"x": 70 + (index % 3) * 280, "y": 80 + (index // 3) * 230}})
    edges = [{"id": f"e-{nodes[i]['id']}-{nodes[i+1]['id']}", "source": nodes[i]["id"], "target": nodes[i + 1]["id"], "animated": nodes[i]["status"] == "in_progress"} for i in range(len(nodes) - 1)]
    return {"career_target": career, "nodes": nodes, "edges": edges, "completion": round(sum(n["mastery"] for n in nodes) / len(nodes), 1)}


def apply_recommendations(roadmap: dict, scores: dict[str, float], recommendations: dict | None) -> dict:
    """Update state only; node IDs, positions and prerequisite edges remain stable."""
    recommendation_map = {
        item["skill"].strip().lower(): item
        for item in (recommendations or {}).get("priority_skills", [])
        if item.get("skill")
    }
    score_map = {topic.strip().lower(): score for topic, score in scores.items()}
    nodes = []
    for node in roadmap.get("nodes", []):
        next_node = node.copy()
        key = node.get("topic", "").strip().lower()
        score = score_map.get(key, float(node.get("mastery", 0)))
        item = recommendation_map.get(key)
        next_node["mastery"] = round(float(score), 1)
        next_node["status"] = _status(next_node["mastery"])
        next_node["priority"] = item.get("priority") if item else _priority(next_node["mastery"])
        if item:
            next_node["recommended_concepts"] = item.get("next_topics", [])
            next_node["practice"] = item.get("practice", "")
            next_node["needs_reassessment"] = item.get("needs_reassessment", False)
        nodes.append(next_node)
    node_status_map = {n["id"]: n["status"] for n in nodes}
    edges = []
    for edge in roadmap.get("edges", []):
        next_edge = edge.copy()
        src_status = node_status_map.get(edge.get("source"))
        next_edge["animated"] = (src_status == "in_progress")
        edges.append(next_edge)
    return {
        **roadmap,
        "nodes": nodes,
        "edges": edges if edges else roadmap.get("edges", []),
        "completion": round(sum(node["mastery"] for node in nodes) / max(1, len(nodes)), 1),
    }
