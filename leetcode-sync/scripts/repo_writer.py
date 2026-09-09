"""
repo_writer.py
--------------
GitHub-repo-side layer: takes normalized submission data and lays it out
on disk in the target repository's folder structure. Knows nothing about
LeetCode's API — it only deals with Submission objects (see
leetcode_client.Submission) and plain filesystem operations. This
separation means the LeetCode source could be swapped out entirely
without touching this file.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from leetcode_client import Submission

logger = logging.getLogger("leetcode_sync.repo_writer")

LANG_EXTENSIONS = {
    "cpp": "cpp",
    "c": "c",
    "java": "java",
    "python": "py",
    "python3": "py",
    "csharp": "cs",
    "javascript": "js",
    "typescript": "ts",
    "php": "php",
    "swift": "swift",
    "kotlin": "kt",
    "dart": "dart",
    "golang": "go",
    "ruby": "rb",
    "scala": "scala",
    "rust": "rs",
    "racket": "rkt",
    "erlang": "erl",
    "elixir": "ex",
}

DIFFICULTY_DIR = {
    "Easy": "easy",
    "Medium": "medium",
    "Hard": "hard",
}


def _slugify_dirname(number: str, slug: str) -> str:
    clean_slug = re.sub(r"[^a-z0-9\-]", "", slug.lower())
    return f"{number}-{clean_slug}"


def _extension_for(lang: str) -> str:
    return LANG_EXTENSIONS.get(lang.lower(), "txt")


def problem_dir(solution_root: str, submission: Submission) -> str:
    difficulty_dir = DIFFICULTY_DIR.get(submission.difficulty, "misc")
    dirname = _slugify_dirname(submission.number, submission.slug)
    return os.path.join(solution_root, difficulty_dir, dirname)


def _problem_readme(submission: Submission, short_description: Optional[str],
                     time_complexity: str, space_complexity: str, approach: str) -> str:
    # Deliberately does NOT reproduce the LeetCode problem statement.
    # Only metadata plus a short, original-language description/approach
    # is stored, to stay clear of copying copyrighted problem text.
    lines = [
        f"# {submission.number}. {submission.title}",
        "",
        f"- **Difficulty:** {submission.difficulty}",
        f"- **LeetCode Problem:** [{submission.url}]({submission.url})",
        f"- **Language:** {submission.lang}",
        "",
        "## Description",
        short_description or (
            "See the problem statement on LeetCode (link above) — "
            "not reproduced here for copyright reasons."
        ),
        "",
        "## Approach",
        approach or "_TODO: describe your approach here._",
        "",
        "## Complexity",
        f"- **Time complexity:** {time_complexity or '_TODO_'}",
        f"- **Space complexity:** {space_complexity or '_TODO_'}",
        "",
    ]
    return "\n".join(lines)


def write_solution(solution_root: str, submission: Submission,
                    short_description: Optional[str] = None,
                    time_complexity: str = "",
                    space_complexity: str = "",
                    approach: str = "") -> bool:
    """
    Write (or update) the solution + README for a single submission.
    Returns True if anything on disk actually changed (new file or
    different content) so the caller can decide whether a commit is
    needed — this is what keeps re-runs idempotent instead of creating
    empty/no-op commits.
    """
    target_dir = problem_dir(solution_root, submission)
    os.makedirs(target_dir, exist_ok=True)

    changed = False

    if submission.code:
        ext = _extension_for(submission.lang)
        code_path = os.path.join(target_dir, f"solution.{ext}")
        changed |= _write_if_changed(code_path, submission.code)
    else:
        logger.warning(
            "No source code available for %s (%s) — writing README only.",
            submission.slug, submission.lang,
        )

    readme_path = os.path.join(target_dir, "README.md")
    readme_content = _problem_readme(
        submission, short_description, time_complexity, space_complexity, approach
    )
    changed |= _write_if_changed(readme_path, readme_content)

    return changed


def _write_if_changed(path: str, content: str) -> bool:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing == content:
            return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True
