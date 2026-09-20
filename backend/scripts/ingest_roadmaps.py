#!/usr/bin/env python3
"""CLI Script to ingest structured roadmap data from roadmap.sh for EduPath."""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.roadmap_ingestion import get_roles, ingest_roadmap, load_roadmap


def main():
    parser = argparse.ArgumentParser(description="Ingest roadmaps from roadmap.sh")
    parser.add_argument("--role", type=str, help="Specific role or roadmap slug to ingest (e.g. data-engineer)")
    parser.add_argument("--all", action="store_true", help="Ingest all 29 roles")
    parser.add_argument("--with-remote-json", action="store_true", help="Also query remote node endpoints for premium resources")
    args = parser.parse_args()

    roles = get_roles()
    if not roles:
        print("Error: No roles found in backend/app/data/roles.json")
        sys.exit(1)

    if args.role:
        role_target = args.role.lower().strip()
        matched = next((r for r in roles if r["roadmap_slug"] == role_target or r["slug"] == role_target or r["name"].lower() == role_target), None)
        if not matched:
            print(f"Error: Role '{args.role}' not found in canonical roles list.")
            sys.exit(1)
        print(f"Ingesting single role: {matched['name']} ({matched['roadmap_slug']})...")
        doc = ingest_roadmap(matched, use_remote_node_json=args.with_remote_json)
        print(f"Done! {matched['name']} has {len(doc['nodes'])} nodes and {len(doc['edges'])} edges.")
    elif args.all:
        print(f"Ingesting all {len(roles)} roles...")
        success = 0
        for r in roles:
            try:
                ingest_roadmap(r, use_remote_node_json=args.with_remote_json)
                success += 1
            except Exception as e:
                print(f"FAILED {r['name']}: {e}")
        print(f"\nCompleted: {success}/{len(roles)} roles successfully ingested.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

