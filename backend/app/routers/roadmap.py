from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.schemas.roadmap import RoadmapRequest, ResourceRequest
from app.ai.chains.roadmap_chain import apply_recommendations, make_roadmap
from app.database.mongodb import db
from app.ai.vector.pinecone_client import find_resources
from app.services.roadmap_ingestion import get_roles, load_roadmap, ROADMAPS_DIR
import json
import re

router = APIRouter(tags=["roadmap"])


def find_topic_score(label: str, normalized_scores: dict[str, float]) -> float | None:
    """Accurately matches a node label against normalized scores without short substring collisions."""
    if not label or not normalized_scores:
        return None
    lbl = label.strip().lower()
    # 1. Exact match
    if lbl in normalized_scores:
        return normalized_scores[lbl]

    lbl_clean = re.sub(r"[^\w\s]", " ", lbl)
    lbl_words = set(lbl_clean.split())

    best_match = None
    best_len = 0
    for k, v in normalized_scores.items():
        k_clean = re.sub(r"[^\w\s]", " ", k)
        k_words = set(k_clean.split())

        # Exact clean match
        if lbl_clean.strip() == k_clean.strip():
            return v

        # Word-boundary match for multi-word or words >= 3 chars (prevents 'go' matching 'algorithms')
        if len(k.strip()) >= 3 and re.search(r"\b" + re.escape(k.strip()) + r"\b", lbl):
            if len(k.strip()) > best_len:
                best_len = len(k.strip())
                best_match = v
        elif len(lbl) >= 4 and re.search(r"\b" + re.escape(lbl) + r"\b", k):
            if len(lbl) > best_len:
                best_len = len(lbl)
                best_match = v
        elif len(k_words) >= 2 and k_words.issubset(lbl_words):
            if len(k.strip()) > best_len:
                best_len = len(k.strip())
                best_match = v

    return best_match


def _apply_scores_to_roadmap(roadmap_data: dict, scores: dict[str, float], skills: list[str]) -> dict:
    """Updates status and mastery of topic/subtopic/checkpoint nodes based on scores and skills."""
    next_roadmap = json.loads(json.dumps(roadmap_data))
    normalized_scores = {k.strip().lower(): v for k, v in (scores or {}).items()}
    normalized_skills = {s.strip().lower() for s in (skills or [])}

    topic_nodes = []
    for node in next_roadmap.get("nodes", []):
        ndata = node.get("data", {})
        ntype = node.get("type")
        if ntype in ("topic", "subtopic", "checkpoint", "skill", "todo"):
            topic_nodes.append(node)
            label = (ndata.get("label") or ndata.get("topic") or node.get("label") or node.get("topic") or "").strip()

            matched_score = find_topic_score(label, normalized_scores)

            if matched_score is None:
                lbl_low = label.lower()
                if lbl_low in normalized_skills or any(len(s) >= 3 and (s in lbl_low or lbl_low in s) for s in normalized_skills):
                    matched_score = 75.0
                    status = "in_progress"
                else:
                    matched_score = float(ndata.get("mastery") or node.get("mastery") or 0.0)
                    status = ndata.get("status") or node.get("status") or ("not_started" if matched_score == 0 else "weak_gap")
            else:
                score_val = round(float(matched_score), 1)
                status = "completed" if score_val >= 80 else "in_progress" if score_val >= 55 else "weak_gap" if score_val > 0 else "not_started"

            score = round(float(matched_score), 1)

            ndata["mastery"] = score
            ndata["status"] = status
            node["data"] = ndata
            # Top-level fields for backwards compatibility
            node["mastery"] = score
            node["status"] = status
            node["topic"] = ndata.get("label") or ndata.get("topic") or label

    if topic_nodes:
        next_roadmap["completion"] = round(sum(n["data"]["mastery"] for n in topic_nodes) / len(topic_nodes), 1)
    else:
        next_roadmap["completion"] = 0.0

    return next_roadmap


def find_previous_topics(roadmap: dict, topic: str, node_id: str | None = None) -> list[str]:
    """Discovers predecessor and prerequisite topics for a given topic in the roadmap graph."""
    if not roadmap:
        return []
    nodes = roadmap.get("nodes", [])
    edges = roadmap.get("edges", [])
    nodes_by_id = {n["id"]: n for n in nodes}

    target = None
    if node_id and node_id in nodes_by_id:
        target = nodes_by_id[node_id]
    if not target and topic:
        t_low = topic.strip().lower()
        for n in nodes:
            ndata = n.get("data", {})
            lbl = (ndata.get("label") or ndata.get("topic") or n.get("topic") or n.get("label") or "").strip().lower()
            if lbl == t_low or (lbl and (lbl in t_low or t_low in lbl)):
                target = n
                break

    if not target:
        return []

    target_id = target["id"]
    prev_topics = []
    seen = {target_id}

    # 1. Incoming graph edges (direct and ancestor predecessors)
    queue = [target_id]
    while queue and len(prev_topics) < 4:
        curr = queue.pop(0)
        for e in edges:
            if e.get("target") == curr:
                s_id = e.get("source")
                if s_id and s_id not in seen:
                    seen.add(s_id)
                    queue.append(s_id)
                    s_node = nodes_by_id.get(s_id)
                    if s_node:
                        s_data = s_node.get("data", {})
                        lbl = (s_data.get("label") or s_data.get("topic") or s_node.get("label") or s_node.get("topic") or "").strip()
                        t = s_node.get("type")
                        if t in ("topic", "subtopic", "checkpoint", "skill", "todo") and lbl and lbl not in prev_topics and lbl.lower() != topic.lower():
                            prev_topics.append(lbl)

    # 2. Sequential earlier topics in layout flow
    topic_nodes = [
        n for n in nodes
        if n.get("type") in ("topic", "subtopic", "checkpoint", "skill", "todo")
        and (n.get("data", {}).get("label") or n.get("data", {}).get("topic") or n.get("label") or "").strip()
    ]
    topic_nodes_sorted = sorted(
        topic_nodes,
        key=lambda n: (n.get("position", {}).get("y", 0), n.get("position", {}).get("x", 0))
    )
    target_idx = next((i for i, n in enumerate(topic_nodes_sorted) if n["id"] == target_id), -1)
    if target_idx > 0:
        for n in reversed(topic_nodes_sorted[:target_idx]):
            s_data = n.get("data", {})
            lbl = (s_data.get("label") or s_data.get("topic") or n.get("label") or "").strip()
            if lbl and lbl not in prev_topics and lbl.lower() != topic.lower():
                prev_topics.append(lbl)
            if len(prev_topics) >= 5:
                break

    return prev_topics[:4]


@router.get("/roadmaps")
async def list_roadmaps():
    """Returns all available career roadmaps and metadata."""
    roles = get_roles()
    roadmaps_list = []
    for r in roles:
        slug = r["roadmap_slug"]
        cached_file = ROADMAPS_DIR / f"{slug}.json"
        is_cached = cached_file.exists()
        node_count = 0
        edge_count = 0
        if is_cached:
            try:
                with open(cached_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    node_count = len(data.get("nodes", []))
                    edge_count = len(data.get("edges", []))
            except Exception:
                pass

        roadmaps_list.append({
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "roadmap_slug": slug,
            "source_url": r.get("source_url", f"https://roadmap.sh/{slug}"),
            "source": "roadmap.sh",
            "is_cached": is_cached,
            "node_count": node_count,
            "edge_count": edge_count,
        })
    return roadmaps_list


@router.get("/roadmaps/{slug}")
@router.get("/roadmap/{slug}")
async def get_roadmap(slug: str, user_id: str | None = None):
    """Returns the full interactive roadmap for a given role slug, overlaying learner scores if user_id is provided."""
    # Find matching role
    roles = get_roles()
    role_info = next((r for r in roles if r["roadmap_slug"] == slug or r["slug"] == slug or r["name"].lower() == slug.lower()), None)
    
    target_slug = role_info["roadmap_slug"] if role_info else slug
    roadmap = load_roadmap(target_slug)
    if not roadmap:
        raise HTTPException(status_code=404, detail=f"Roadmap not found for slug: {slug}")

    if user_id:
        state = await db.find_one("skill_states", {"user_id": user_id}) or {}
        scores = state.get("scores", {})
        user = await db.find_one("users", {"id": user_id}) or {}
        skills = user.get("skills", [])
        return _apply_scores_to_roadmap(roadmap, scores, skills)

    return roadmap


@router.post("/roadmap/generate")
async def generate(payload: RoadmapRequest):
    """Generates or updates a personalized roadmap overlaying learner scores."""
    roles = get_roles()
    role_info = next((r for r in roles if r["name"].lower() == payload.career_target.lower() or r["slug"] == payload.career_target.lower() or r["roadmap_slug"] == payload.career_target.lower()), None)
    
    if role_info:
        structured = load_roadmap(role_info["roadmap_slug"])
        if structured:
            scores = payload.scores
            if payload.user_id:
                state = await db.find_one("skill_states", {"user_id": payload.user_id}) or {}
                scores = state.get("scores") or scores
            next_roadmap = _apply_scores_to_roadmap(structured, scores, payload.skills)
            next_roadmap["user_id"] = payload.user_id
            next_roadmap["career_target"] = role_info["name"]
            next_roadmap["updated_at"] = datetime.now(timezone.utc).isoformat()
            if payload.user_id:
                await db.upsert("roadmaps", {"user_id": payload.user_id}, next_roadmap)
            return next_roadmap

    # Fallback to legacy generator if role is unknown
    if not payload.user_id:
        return make_roadmap(payload.career_target, payload.scores, payload.skills)
    state = await db.find_one("skill_states", {"user_id": payload.user_id}) or {}
    scores = state.get("scores") or payload.scores
    roadmap = await db.find_one("roadmaps", {"user_id": payload.user_id})
    recommendation_record = await db.find_one("recommendations", {"user_id": payload.user_id}) or {}
    recommendations = recommendation_record.get("recommendations")
    if roadmap and roadmap.get("career_target") == payload.career_target and roadmap.get("skill_state_version") == state.get("version", 0):
        return roadmap
    if roadmap and roadmap.get("career_target") == payload.career_target:
        next_roadmap = apply_recommendations(roadmap, scores, recommendations)
        roadmap_version = int(roadmap.get("roadmap_version", 0)) + 1
    else:
        next_roadmap = apply_recommendations(
            make_roadmap(payload.career_target, scores, payload.skills), scores, recommendations
        )
        roadmap_version = 1
    next_roadmap.update({
        "user_id": payload.user_id,
        "skill_state_version": state.get("version", 0),
        "roadmap_version": roadmap_version,
        "recommendations": recommendations or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.upsert("roadmaps", {"user_id": payload.user_id}, next_roadmap)
    return next_roadmap


@router.get("/roadmap/user/{user_id}")
async def get_user_roadmap(user_id: str):
    """Returns the current personalized roadmap for the user with latest scores applied."""
    user = await db.find_one("users", {"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    career = user.get("career_target") or "Data Engineer"
    roles = get_roles()
    role_info = next(
        (r for r in roles if r["name"].lower() == career.lower() or r["slug"] == career.lower() or r["roadmap_slug"] == career.lower()),
        None
    )
    target_slug = role_info["roadmap_slug"] if role_info else "data-engineer"

    state = await db.find_one("skill_states", {"user_id": user_id}) or {}
    scores = state.get("scores", {})
    skills = user.get("skills", [])

    roadmap = await db.find_one("roadmaps", {"user_id": user_id})
    if not roadmap or roadmap.get("career_target") != (role_info["name"] if role_info else career):
        raw = load_roadmap(target_slug) or make_roadmap(career, scores, skills)
        raw["user_id"] = user_id
        raw["career_target"] = role_info["name"] if role_info else career
        roadmap = raw

    next_roadmap = _apply_scores_to_roadmap(roadmap, scores, skills)
    next_roadmap["scores"] = scores
    next_roadmap["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.upsert("roadmaps", {"user_id": user_id}, next_roadmap)
    return next_roadmap


@router.post("/roadmap/resources")
async def resources(payload: ResourceRequest):
    """Returns official resources for a topic/node directly from roadmap.sh."""
    # Find matching role
    roles = get_roles()
    target_lower = payload.career_target.lower().strip()
    role_info = next(
        (r for r in roles if r["name"].lower() == target_lower or r["slug"] == target_lower or r["roadmap_slug"] == target_lower or target_lower.startswith(r["name"].lower()) or r["name"].lower() in target_lower),
        None
    )
    
    slug = role_info["roadmap_slug"] if role_info else "data-engineer"
    roadmap = load_roadmap(slug)
    
    node_match = None
    if roadmap:
        nodes = roadmap.get("nodes", [])
        if payload.node_id:
            node_match = next((n for n in nodes if n.get("id") == payload.node_id), None)
        if not node_match:
            topic_lower = payload.topic.strip().lower()
            node_match = next((n for n in nodes if (n.get("data", {}).get("label") or "").strip().lower() == topic_lower), None)

    if node_match:
        ndata = node_match.get("data", {})
        free_res = ndata.get("resources", [])
        if not free_res:
            free_res = await find_resources(payload.topic)
        return {
            "topic": ndata.get("label") or payload.topic,
            "node_id": node_match.get("id"),
            "description": ndata.get("description", ""),
            "resources": free_res,
            "paid_resources": ndata.get("paid_resources", []),
            "source": "roadmap.sh" if ndata.get("resources") else "curated",
            "source_url": f"https://roadmap.sh/{slug}",
            "practice_task": f"Build a practical exercise or project demonstrating {payload.topic} and document your decisions.",
        }

    # Fallback to curated resources
    return {
        "topic": payload.topic,
        "resources": await find_resources(payload.topic),
        "source": "curated",
        "practice_task": f"Build a small {payload.topic} feature and explain your design decisions."
    }
