#!/usr/bin/env python3
"""
sync.py
-------
Orchestrator for the LeetCode -> GitHub sync. This is the only script the
GitHub Actions workflow calls directly.

Flow:
  1. Load config.yml.
  2. Fetch recent accepted submissions + progress stats from LeetCode
     (leetcode_client.py).
  3. Filter out anything already synced (state.py) to stay idempotent.
  4. Write new/updated solution files into the repo (repo_writer.py).
  5. Update the README dashboard block (readme_updater.py).
  6. Persist updated state.
  7. Exit 0 with a machine-readable "changed: true/false" line on stdout
     so the workflow's shell step can decide whether to commit.

Exit codes:
  0 - ran successfully (regardless of whether anything changed)
  1 - configuration error (fix config.yml / secrets, don't retry blindly)
  2 - transient failure (network, LeetCode rate limit, etc.) - safe to retry
"""

from __future__ import annotations

import logging
import os
import sys

import yaml

from leetcode_client import LeetCodeClient, LeetCodeAuthError, LeetCodeAPIError
from repo_writer import write_solution
from readme_updater import update_readme
from state import SyncState

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("leetcode_sync.sync")


def load_config(path: str = "config.yml") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config.yml not found at %s", path)
        sys.exit(1)
    except yaml.YAMLError as exc:
        logger.error("config.yml is not valid YAML: %s", exc)
        sys.exit(1)


def pick_submissions_to_sync(submissions, cfg: dict, state: SyncState):
    """Apply preferred-language filtering + dedup against state."""
    store_all = cfg["leetcode"].get("store_all_languages", False)
    preferred = cfg["leetcode"].get("preferred_languages", [])

    # Group by slug so we can apply "one language per problem" if configured.
    by_slug: dict[str, list] = {}
    for s in submissions:
        by_slug.setdefault(s.slug, []).append(s)

    to_sync = []
    for slug, subs in by_slug.items():
        if store_all:
            candidates = subs
        else:
            # Prefer the configured language order; fall back to most recent.
            ordered = sorted(
                subs,
                key=lambda s: (
                    preferred.index(s.lang) if s.lang in preferred else len(preferred),
                    -s.timestamp,
                ),
            )
            candidates = ordered[:1]

        for sub in candidates:
            if state.is_synced(sub.slug, sub.lang):
                continue
            to_sync.append(sub)

    return to_sync


def main() -> int:
    cfg = load_config()

    username = cfg["leetcode"]["username"]
    solution_root = cfg["github"]["solution_dir"]
    readme_path = cfg["github"]["readme_path"]
    state_path = cfg["state"]["file"]
    fetch_limit = cfg["leetcode"].get("submission_fetch_limit", 20)

    try:
        client = LeetCodeClient(username=username)
    except LeetCodeAuthError as exc:
        logger.error(str(exc))
        return 1

    state = SyncState(state_path)

    try:
        submissions = client.get_recent_accepted_submissions(limit=fetch_limit)
        stats = client.get_progress_stats()
    except LeetCodeAuthError as exc:
        logger.error(str(exc))
        return 1
    except LeetCodeAPIError as exc:
        logger.error("Transient LeetCode API failure: %s", exc)
        return 2

    to_sync = pick_submissions_to_sync(submissions, cfg, state)
    logger.info("%d new submission(s) to sync (of %d fetched).", len(to_sync), len(submissions))

    any_files_changed = False
    for submission in to_sync:
        try:
            changed = write_solution(solution_root, submission)
            any_files_changed |= changed
            state.mark_synced(submission.slug, submission.lang,
                               submission.submission_id, submission.timestamp)
            logger.info("Synced %s (%s) [%s]", submission.slug, submission.lang,
                        "updated" if changed else "unchanged")
        except OSError as exc:
            # A single bad filesystem write shouldn't abort the whole run.
            logger.warning("Failed to write solution for %s: %s", submission.slug, exc)
            continue

    # README dashboard: always recompute from current stats + most recent
    # synced-or-existing submissions, but only touch the file if the
    # rendered block actually differs.
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()
    except FileNotFoundError:
        logger.warning("%s not found, creating a new one.", readme_path)
        readme_text = f"# {cfg['github']['repository']}\n"

    recent_for_table = sorted(submissions, key=lambda s: -s.timestamp)
    new_readme, readme_changed = update_readme(readme_text, stats, recent_for_table)
    if readme_changed:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        logger.info("README dashboard updated.")

    state.save()

    changed = any_files_changed or readme_changed
    print(f"changed={'true' if changed else 'false'}")
    logger.info("Sync complete. changed=%s", changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
