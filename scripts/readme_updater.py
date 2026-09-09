"""
readme_updater.py
------------------
Maintains the `<!-- LEETCODE_STATS_START -->` ... `<!-- LEETCODE_STATS_END -->`
block inside the repo's README.md, without touching anything outside it.

If the markers don't exist yet, they're appended to the end of the file
once (so the very first run "installs" the dashboard); after that, only
the content between the markers is ever replaced.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from leetcode_client import ProgressStats, Submission

logger = logging.getLogger("leetcode_sync.readme_updater")

START_MARKER = "<!-- LEETCODE_STATS_START -->"
END_MARKER = "<!-- LEETCODE_STATS_END -->"

_BLOCK_RE = re.compile(
    re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
    re.DOTALL,
)


def _render_block(stats: ProgressStats, recent: Iterable[Submission], max_recent: int = 10) -> str:
    recent_list = list(recent)[:max_recent]

    table_rows = "\n".join(
        f"| {s.number} | [{s.title}]({s.url}) | {s.difficulty} | {s.lang} |"
        for s in recent_list
    ) or "| - | _no recent solutions yet_ | - | - |"

    body = f"""{START_MARKER}
## LeetCode Progress

**Solved:** {stats.total_solved}

| Easy | Medium | Hard |
|------|--------|------|
| {stats.easy_solved} | {stats.medium_solved} | {stats.hard_solved} |

**Acceptance Rate:** {stats.acceptance_rate}%

### Recent Solutions

| # | Problem | Difficulty | Language |
|---|---------|------------|----------|
{table_rows}

_Last updated automatically by [leetcode-sync](.github/workflows/leetcode-sync.yml)._
{END_MARKER}"""
    return body


def update_readme(readme_text: str, stats: ProgressStats,
                   recent: Iterable[Submission]) -> tuple[str, bool]:
    """
    Returns (new_readme_text, changed).
    """
    new_block = _render_block(stats, recent)

    if _BLOCK_RE.search(readme_text):
        updated = _BLOCK_RE.sub(lambda _: new_block, readme_text, count=1)
    else:
        logger.info("No LEETCODE_STATS markers found — appending dashboard section.")
        separator = "\n\n" if readme_text and not readme_text.endswith("\n\n") else ""
        updated = f"{readme_text}{separator}{new_block}\n"

    return updated, updated != readme_text
