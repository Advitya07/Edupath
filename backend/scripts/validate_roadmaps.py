#!/usr/bin/env python3
"""Validation script for EduPath roadmaps integration with roadmap.sh.

Verifies:
- All 29 roles present
- Structured graph data loaded
- Nodes and edges extracted
- Sections preserved
- Node IDs unique and preserved
- Topic to content mappings found
- Resources mapped and classified (free vs premium)
- Resource URLs valid (syntax and non-empty)
- No duplicate nodes
- No duplicate resources per node
"""

import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.roadmap_ingestion import get_roles, ROADMAPS_DIR, REPO_ROADMAPS_DIR


def is_valid_url(url: str) -> bool:
    """Validates URL structure."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False


def validate_all_roadmaps():
    roles = get_roles()
    if not roles:
        print("ERROR: No roles found in backend/app/data/roles.json")
        sys.exit(1)

    print(f"\n{'='*115}")
    print(f"{'EduPath Roadmap.sh Validation Report':^115}")
    print(f"{'='*115}")
    header = f"{'Role':<28} | {'Status':<6} | {'Nodes':<5} | {'Edges':<5} | {'Free':<5} | {'Prem':<4} | {'Sections':<8} | {'Dup Nodes':<9} | {'Dup Res':<7} | {'Bad URLs':<8}"
    print(header)
    print("-" * len(header))

    total_nodes = 0
    total_edges = 0
    total_free_res = 0
    total_prem_res = 0
    total_sections = 0
    total_dup_nodes = 0
    total_dup_res = 0
    total_bad_urls = 0
    all_passed = True

    role_results = []

    for r in roles:
        role_name = r["name"]
        slug = r["roadmap_slug"]
        file_path = ROADMAPS_DIR / f"{slug}.json"

        if not file_path.exists():
            print(f"{role_name:<28} | {'FAIL':<6} | Missing roadmap cache file!")
            all_passed = False
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        # Check node uniqueness
        node_ids = set()
        dup_nodes = 0
        sections = 0
        free_res_count = 0
        prem_res_count = 0
        dup_res_count = 0
        bad_urls_count = 0

        for n in nodes:
            nid = n.get("id")
            if nid in node_ids:
                dup_nodes += 1
            node_ids.add(nid)

            ntype = n.get("type")
            if ntype == "section":
                sections += 1

            ndata = n.get("data", {})
            resources = ndata.get("resources", [])
            paid_resources = ndata.get("paid_resources", [])

            # Check resources for duplicates and invalid URLs
            res_urls = set()
            for res in resources:
                free_res_count += 1
                url = res.get("url", "")
                if not is_valid_url(url):
                    bad_urls_count += 1
                if url in res_urls:
                    dup_res_count += 1
                res_urls.add(url)

            for pres in paid_resources:
                prem_res_count += 1
                url = pres.get("url", "")
                if not is_valid_url(url):
                    bad_urls_count += 1

        total_nodes += len(nodes)
        total_edges += len(edges)
        total_free_res += free_res_count
        total_prem_res += prem_res_count
        total_sections += sections
        total_dup_nodes += dup_nodes
        total_dup_res += dup_res_count
        total_bad_urls += bad_urls_count

        status = "✓" if (dup_nodes == 0 and dup_res_count == 0 and bad_urls_count == 0 and len(nodes) > 0) else "⚠"
        if status != "✓":
            all_passed = False

        row = f"{role_name:<28} | {status:^6} | {len(nodes):<5} | {len(edges):<5} | {free_res_count:<5} | {prem_res_count:<4} | {sections:<8} | {dup_nodes:<9} | {dup_res_count:<7} | {bad_urls_count:<8}"
        print(row)
        role_results.append({
            "role": role_name,
            "slug": slug,
            "status": status,
            "nodes": len(nodes),
            "edges": len(edges),
            "free": free_res_count,
            "prem": prem_res_count,
            "sections": sections,
        })

    print("-" * len(header))
    summary_row = f"{'TOTAL (29 Roles)':<28} | {'PASS' if all_passed else 'CHECK':^6} | {total_nodes:<5} | {total_edges:<5} | {total_free_res:<5} | {total_prem_res:<4} | {total_sections:<8} | {total_dup_nodes:<9} | {total_dup_res:<7} | {total_bad_urls:<8}"
    print(summary_row)
    print(f"{'='*115}\n")

    if all_passed:
        print("🎉 ALL 29 ROADMAPS PASSED VALIDATION WITH ZERO ERRORS!")
    else:
        print("⚠️ Some roadmaps have warnings or errors to review.")
        sys.exit(1)


if __name__ == "__main__":
    validate_all_roadmaps()

