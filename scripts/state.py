"""
state.py
--------
Tracks which (problem, language) pairs have already been synced, so the
workflow is idempotent no matter how often it runs.

The state file is small, human-readable JSON, and is committed to the
repo alongside the solutions themselves — that way the "source of truth"
for what's already synced travels with the repo, and a fresh clone /
fresh runner has everything it needs without any external database.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("leetcode_sync.state")


class SyncState:
    def __init__(self, path: str):
        self.path = path
        self._data: dict[str, Any] = {"synced": {}, "version": 1}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            logger.info("No existing state file at %s, starting fresh.", self.path)
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            self._data.setdefault("synced", {})
        except (json.JSONDecodeError, OSError) as exc:
            # Never let a corrupt state file crash the whole sync — treat
            # it as empty and let re-sync naturally re-derive everything.
            # Duplicate files are still prevented downstream because
            # repo_writer checks for existing solution folders on disk too.
            logger.warning("State file unreadable (%s), starting fresh: %s", self.path, exc)
            self._data = {"synced": {}, "version": 1}

    @staticmethod
    def _key(slug: str, lang: str) -> str:
        return f"{slug}::{lang}"

    def is_synced(self, slug: str, lang: str) -> bool:
        return self._key(slug, lang) in self._data["synced"]

    def mark_synced(self, slug: str, lang: str, submission_id: str, timestamp: int) -> None:
        self._data["synced"][self._key(slug, lang)] = {
            "submission_id": submission_id,
            "timestamp": timestamp,
        }

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
            f.write("\n")
