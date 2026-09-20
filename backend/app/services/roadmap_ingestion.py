"""Roadmap ingestion and sync service.
Uses roadmap.sh as the single source of truth for:
- 29 Role-based roadmaps
- Graph nodes and edges
- Sections, subtopics, and ordering
- Node descriptions and free/paid resources
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any
import urllib.request

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROADMAPS_DIR = DATA_DIR / "roadmaps"
ROLES_FILE = DATA_DIR / "roles.json"
REPO_ROADMAPS_DIR = Path("/tmp/dev-roadmap/roadmaps")

TYPE_MAP = {
    "book": "Book",
    "article": "Article",
    "video": "Video",
    "course": "Course",
    "official": "Documentation",
    "opensource": "Open Source",
    "roadmap": "Roadmap Guide",
    "podcast": "Podcast",
    "feed": "Feed",
}


def get_roles() -> list[dict[str, Any]]:
    if not ROLES_FILE.exists():
        return []
    with open(ROLES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; EduPath-Sync/1.0)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_markdown_content(md_content: str) -> dict[str, Any]:
    """Extracts title, description, and resources from roadmap.sh markdown content."""
    lines = md_content.strip().split("\n")
    title = ""
    description_lines = []
    resources = []
    
    in_resources = False
    type_pattern = re.compile(r"-\s*\[@([a-zA-Z0-9_.-]+)@([^\]]+)\]\(([^)]+)\)")

    seen_urls = set()
    for line in lines:
        stripped = line.strip()
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue

        if "Visit the following resources to learn more:" in stripped:
            in_resources = True
            continue

        if in_resources:
            match = type_pattern.match(stripped)
            if match:
                raw_type, r_title, raw_url = match.groups()
                clean_url = raw_url.strip().lstrip("] [()")
                if clean_url.startswith("ttps://"):
                    clean_url = "https://" + clean_url[7:]
                elif clean_url.startswith("ttp://"):
                    clean_url = "http://" + clean_url[6:]
                
                if clean_url in seen_urls:
                    continue
                seen_urls.add(clean_url)

                res_type = TYPE_MAP.get(raw_type.lower(), raw_type.capitalize())
                resources.append({
                    "title": r_title.strip(),
                    "type": res_type,
                    "url": clean_url,
                    "access_type": "free",
                    "source": "roadmap.sh",
                })
        else:
            description_lines.append(line)

    description = "\n".join(description_lines).strip()
    return {
        "title": title,
        "description": description,
        "resources": resources,
    }


def ingest_roadmap(role_info: dict[str, Any], use_remote_node_json: bool = False) -> dict[str, Any]:
    """Ingests a single role roadmap from roadmap.sh structured data."""
    slug = role_info["roadmap_slug"]
    role_name = role_info["name"]
    source_url = role_info.get("source_url", f"https://roadmap.sh/{slug}")

    # 1. Fetch main graph JSON
    graph_url = f"https://roadmap.sh/{slug}.json"
    try:
        raw_graph = _fetch_json(graph_url)
    except Exception as e:
        print(f"Warning: Failed to fetch {graph_url}: {e}. Checking local cache.")
        cached_file = ROADMAPS_DIR / f"{slug}.json"
        if cached_file.exists():
            with open(cached_file, "r", encoding="utf-8") as f:
                return json.load(f)
        raise RuntimeError(f"Could not load roadmap data for {slug}: {e}")

    # 2. Index local content files from cloned repo if available
    content_map: dict[str, dict[str, Any]] = {}
    content_dir = REPO_ROADMAPS_DIR / slug / "content"
    if content_dir.exists():
        for fname in os.listdir(content_dir):
            if fname.endswith(".md") and "@" in fname:
                node_id = fname.split("@")[1].replace(".md", "")
                fpath = content_dir / fname
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content_map[node_id] = parse_markdown_content(f.read())
                except Exception as ex:
                    print(f"Error reading {fpath}: {ex}")

    # 3. Process nodes
    nodes = []
    seen_node_ids = set()
    raw_nodes = raw_graph.get("nodes", [])

    for raw_node in raw_nodes:
        nid = raw_node.get("id")
        if not nid or nid in seen_node_ids:
            continue
        seen_node_ids.add(nid)

        ntype = raw_node.get("type", "topic")
        ndata = raw_node.get("data", {})
        old_id = ndata.get("oldId")
        label = ndata.get("label", "")

        # Match content
        content = content_map.get(nid) or (content_map.get(old_id) if old_id else None)
        
        description = content.get("description", "") if content else ""
        free_resources = content.get("resources", []) if content else []
        paid_resources = []

        # Optionally query remote node json if resources missing or to fetch paid resources
        if use_remote_node_json and ntype in ("topic", "subtopic") and not free_resources:
            try:
                node_json_url = f"https://roadmap.sh/{slug}/{nid}.json"
                node_data = _fetch_json(node_json_url)
                if not description and node_data.get("description"):
                    description = node_data["description"]
                if not free_resources and node_data.get("resources"):
                    for r in node_data["resources"]:
                        raw_t = r.get("type", "article")
                        free_resources.append({
                            "title": r.get("title", ""),
                            "type": TYPE_MAP.get(raw_t.lower(), raw_t.capitalize()),
                            "url": r.get("url", ""),
                            "access_type": "free",
                            "source": "roadmap.sh",
                        })
                if node_data.get("paidResources"):
                    for pr in node_data["paidResources"]:
                        raw_t = pr.get("type", "course")
                        paid_resources.append({
                            "title": pr.get("title", ""),
                            "type": TYPE_MAP.get(raw_t.lower(), raw_t.capitalize()),
                            "url": pr.get("url", ""),
                            "access_type": "premium",
                            "partner": pr.get("partner", ""),
                            "source": "roadmap.sh",
                        })
            except Exception:
                pass

        # Build normalized node
        normalized_node = {
            "id": nid,
            "type": ntype,
            "position": raw_node.get("position", {"x": 0, "y": 0}),
            "data": {
                "id": nid,
                "label": label,
                "topic": label,
                "oldId": old_id,
                "style": ndata.get("style", {}),
                "description": description,
                "resources": free_resources,
                "paid_resources": paid_resources,
                "status": "weak_gap",
                "mastery": 0,
                "source": "roadmap.sh",
                "source_node_id": nid,
            },
            "width": raw_node.get("width") or raw_node.get("measured", {}).get("width"),
            "height": raw_node.get("height") or raw_node.get("measured", {}).get("height"),
            "style": raw_node.get("style", {}),
            "zIndex": raw_node.get("zIndex", 1),
        }
        nodes.append(normalized_node)

    # 4. Process edges
    edges = []
    seen_edge_ids = set()
    raw_edges = raw_graph.get("edges", [])

    for raw_edge in raw_edges:
        eid = raw_edge.get("id")
        if not eid or eid in seen_edge_ids:
            continue
        seen_edge_ids.add(eid)

        edges.append({
            "id": eid,
            "source": raw_edge.get("source"),
            "target": raw_edge.get("target"),
            "sourceHandle": raw_edge.get("sourceHandle"),
            "targetHandle": raw_edge.get("targetHandle"),
            "style": raw_edge.get("style", {}),
            "data": raw_edge.get("data", {}),
            "animated": False,
        })

    # 5. Build roadmap document
    now_iso = datetime.now(timezone.utc).isoformat()
    roadmap_doc = {
        "id": slug,
        "slug": slug,
        "role_id": role_info["id"],
        "role_name": role_name,
        "career_target": role_name,
        "title": role_name,
        "description": raw_graph.get("description", f"Interactive {role_name} roadmap from roadmap.sh"),
        "source": "roadmap.sh",
        "source_url": source_url,
        "roadmap_slug": slug,
        "last_synced_at": now_iso,
        "dimensions": raw_graph.get("dimensions", {"width": 1200, "height": 2000}),
        "nodes": nodes,
        "edges": edges,
        "completion": 0,
    }

    # 6. Save to disk cache
    ROADMAPS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = ROADMAPS_DIR / f"{slug}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(roadmap_doc, f, indent=2)

    print(f"✓ Ingested {role_name} ({slug}): {len(nodes)} nodes, {len(edges)} edges -> {out_file}")
    return roadmap_doc


def load_roadmap(slug: str) -> dict[str, Any] | None:
    """Loads roadmap from cached JSON or ingests it if missing."""
    target_file = ROADMAPS_DIR / f"{slug}.json"
    if target_file.exists():
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Check if role exists in roles.json
    roles = get_roles()
    role_info = next((r for r in roles if r["roadmap_slug"] == slug or r["slug"] == slug or r["name"].lower() == slug.lower()), None)
    if role_info:
        return ingest_roadmap(role_info)
    return None
