#!/usr/bin/env python3
"""
Cleanup Script: Remove migrated expert_sheet rows from practice_problems table.

Usage:
    # 1. Preview (Dry Run):
    python3 backend/scripts/cleanup_expert_sheet_problems.py

    # 2. Execute Deletion:
    python3 backend/scripts/cleanup_expert_sheet_problems.py --execute

    # 3. Optional: Also delete the newbie-to-expert-cp sheet from dsa_sheets:
    python3 backend/scripts/cleanup_expert_sheet_problems.py --execute --delete-sheet
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load backend/.env
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

from app.database import get_supabase_client


def main():
    parser = argparse.ArgumentParser(
        description="Clean up expert_sheet problems from practice_problems."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the deletion. Without this flag, script runs in dry-run mode.",
    )
    parser.add_argument(
        "--delete-sheet",
        action="store_true",
        help="Also delete 'newbie-to-expert-cp' entry from dsa_sheets table.",
    )
    args = parser.parse_args()

    client = get_supabase_client()

    print("==================================================")
    print("   PRACTICE_PROBLEMS CLEANUP SCRIPT")
    print("==================================================")
    print(f"Mode: {'EXECUTE (Permanent Deletion)' if args.execute else 'DRY RUN (Preview Only)'}\n")

    # 1. Verify current total count in practice_problems
    res_total = client.table("practice_problems").select("id", count="exact").execute()
    total_before = res_total.count
    print(f"[*] Total practice_problems currently in DB: {total_before}")

    # 2. Find problems with sheet_source = 'expert_sheet'
    res_expert_attrib = (
        client.table("practice_problems")
        .select("id, slug, title")
        .contains("attributes", {"sheet_source": "expert_sheet"})
        .execute()
    )
    attrib_ids = {r["id"] for r in (res_expert_attrib.data or [])}

    # 3. Find problems matching IDs in public.expert_sheet table
    res_es = client.table("expert_sheet").select("id").execute()
    es_table_ids = {r["id"] for r in (res_es.data or [])}

    # Combined candidate IDs to remove
    target_ids = list(attrib_ids.union(es_table_ids))
    print(f"[*] Target problems identified for removal: {len(target_ids)}")

    if not target_ids:
        print("[+] No migrated expert_sheet problems found in practice_problems. Nothing to delete!")
        return

    # Print sample
    print(f"\nSample problems targeted for deletion (showing up to 5 of {len(target_ids)}):")
    for r in (res_expert_attrib.data or [])[:5]:
        print(f"  - [{r['id']}] {r['slug']} -> {r['title']}")

    if not args.execute:
        print("\n" + "=" * 50)
        print("[!] DRY RUN COMPLETED: No rows were deleted.")
        print("To execute deletion, re-run with:")
        print("    python3 backend/scripts/cleanup_expert_sheet_problems.py --execute")
        if not args.delete_sheet:
            print("To also delete the sheet in dsa_sheets, add:")
            print("    --delete-sheet")
        print("=" * 50)
        return

    # 4. Perform deletion in batches of 50
    print("\n[*] Deleting rows from practice_problems in batches...")
    batch_size = 50
    deleted_count = 0

    for i in range(0, len(target_ids), batch_size):
        batch = target_ids[i : i + batch_size]
        res_del = client.table("practice_problems").delete().in_("id", batch).execute()
        deleted_count += len(batch)
        print(f"  -> Deleted batch {i // batch_size + 1} ({len(batch)} rows)")

    # 5. Verify remaining count
    res_after = client.table("practice_problems").select("id", count="exact").execute()
    total_after = res_after.count
    print(f"\n[+] Successfully removed {len(target_ids)} rows.")
    print(f"[+] Total practice_problems now remaining in DB: {total_after} (Expected: {total_before - len(target_ids)})")

    # 6. Optional: Delete sheet entry
    if args.delete_sheet:
        print("\n[*] Removing 'newbie-to-expert-cp' from dsa_sheets...")
        res_sheet_del = client.table("dsa_sheets").delete().eq("id", "newbie-to-expert-cp").execute()
        print("[+] 'newbie-to-expert-cp' removed from dsa_sheets.")

    print("\n" + "=" * 50)
    print("   CLEANUP FINISHED SUCCESSFULLY")
    print("   The 'expert_sheet' table remains 100% intact.")
    print("=" * 50)


if __name__ == "__main__":
    main()
