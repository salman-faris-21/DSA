"""
leetcode_client.py
------------------
LeetCode data-fetching layer.

Responsibility: talk to LeetCode and return plain Python data (dicts).
This module knows NOTHING about git, GitHub, or the filesystem layout of
the target repo — that separation is what lets the GitHub sync layer be
swapped out or reused independently (e.g. if you later point it at a
different judge/site, or LeetCode changes its API).

LeetCode does not publish a stable, documented public API. The de-facto
standard approach used by the wider LeetCode-automation community (e.g.
"leetcode-sync", "lc-sync" style tools) is to call the same GraphQL
endpoint the LeetCode website itself uses (https://leetcode.com/graphql),
authenticated with the cookies of your own logged-in browser session.
There is no scraping of HTML pages here — it's a single JSON API endpoint,
which is far more stable than parsing rendered HTML, but it is still an
unofficial/undocumented endpoint, so:

  * All access is treated as best-effort and wrapped in retries/backoff.
  * Every network call is isolated so it can be swapped for an official
    API in the future with no changes needed outside this file.
  * Only YOUR OWN session (via secrets you control) is used — this fetches
    your own submissions, not anyone else's.

Required credentials (read from environment variables, never hardcoded):
  LEETCODE_SESSION     - value of the `LEETCODE_SESSION` cookie
  LEETCODE_CSRF_TOKEN  - value of the `csrftoken` cookie

How to obtain them: see docs/SETUP.md.
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger("leetcode_sync.leetcode_client")

GRAPHQL_URL = "https://leetcode.com/graphql"
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 2


class LeetCodeAuthError(RuntimeError):
    """Raised when credentials are missing or LeetCode rejects them."""


class LeetCodeAPIError(RuntimeError):
    """Raised for non-auth API failures (network, rate limit, bad response)."""


@dataclass
class Submission:
    submission_id: str
    slug: str
    title: str
    number: str
    difficulty: str
    lang: str
    code: Optional[str]
    timestamp: int
    status: str
    url: str = field(default="")

    def __post_init__(self):
        if not self.url:
            self.url = f"https://leetcode.com/problems/{self.slug}/"


@dataclass
class ProgressStats:
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    total_submissions: int
    accepted_submissions: int

    @property
    def acceptance_rate(self) -> float:
        if self.total_submissions == 0:
            return 0.0
        return round(100.0 * self.accepted_submissions / self.total_submissions, 1)


class LeetCodeClient:
    """Thin client around LeetCode's GraphQL endpoint using session auth."""

    def __init__(self, username: str, session: Optional[str] = None,
                 csrf_token: Optional[str] = None):
        self.username = username
        self.session_cookie = session or os.environ.get("LEETCODE_SESSION")
        self.csrf_token = csrf_token or os.environ.get("LEETCODE_CSRF_TOKEN")

        if not self.session_cookie or not self.csrf_token:
            raise LeetCodeAuthError(
                "Missing LeetCode credentials. Set LEETCODE_SESSION and "
                "LEETCODE_CSRF_TOKEN as environment variables / GitHub Secrets. "
                "See docs/SETUP.md for how to obtain them."
            )

        self._http = requests.Session()
        self._http.cookies.set("LEETCODE_SESSION", self.session_cookie, domain="leetcode.com")
        self._http.cookies.set("csrftoken", self.csrf_token, domain="leetcode.com")
        self._http.headers.update({
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "x-csrftoken": self.csrf_token,
            "User-Agent": "leetcode-sync-bot/1.0 (+personal automation)",
        })

    # ---------- low-level request helper with retry/backoff ----------

    def _post(self, payload: dict) -> dict:
        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._http.post(GRAPHQL_URL, json=payload, timeout=DEFAULT_TIMEOUT)
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("Network error (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
                time.sleep(BACKOFF_BASE_SECONDS ** attempt)
                continue

            if resp.status_code == 401 or resp.status_code == 403:
                raise LeetCodeAuthError(
                    f"LeetCode rejected credentials (HTTP {resp.status_code}). "
                    "Your session cookie has likely expired — refresh it and "
                    "update the GitHub Secrets."
                )

            if resp.status_code == 429:
                wait = BACKOFF_BASE_SECONDS ** attempt
                logger.warning("Rate limited by LeetCode, backing off %ss", wait)
                time.sleep(wait)
                continue

            if resp.status_code >= 500:
                last_error = LeetCodeAPIError(f"LeetCode server error {resp.status_code}")
                time.sleep(BACKOFF_BASE_SECONDS ** attempt)
                continue

            if resp.status_code != 200:
                raise LeetCodeAPIError(
                    f"Unexpected HTTP {resp.status_code} from LeetCode: {resp.text[:300]}"
                )

            try:
                data = resp.json()
            except ValueError as exc:
                raise LeetCodeAPIError(f"Invalid JSON from LeetCode: {exc}") from exc

            if "errors" in data:
                raise LeetCodeAPIError(f"GraphQL errors: {data['errors']}")

            return data.get("data", {})

        raise LeetCodeAPIError(f"Exhausted retries contacting LeetCode: {last_error}")

    # ---------- public API ----------

    def get_recent_accepted_submissions(self, limit: int = 20) -> list[Submission]:
        """Return the most recent *accepted* submissions for the user."""
        query = """
        query recentAcSubmissions($username: String!, $limit: Int!) {
          recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
            statusDisplay
            lang
          }
        }
        """
        data = self._post({
            "query": query,
            "variables": {"username": self.username, "limit": limit},
        })
        raw = data.get("recentAcSubmissionList") or []

        submissions = []
        for item in raw:
            try:
                meta = self.get_problem_metadata(item["titleSlug"])
                code = self.get_submission_code(item["id"])
                submissions.append(Submission(
                    submission_id=str(item["id"]),
                    slug=item["titleSlug"],
                    title=item["title"],
                    number=meta.get("questionFrontendId", "0"),
                    difficulty=meta.get("difficulty", "Unknown"),
                    lang=item.get("lang", "unknown"),
                    code=code,
                    timestamp=int(item.get("timestamp", 0)),
                    status=item.get("statusDisplay", "Accepted"),
                ))
            except (LeetCodeAPIError, KeyError) as exc:
                # Don't let one bad/missing submission break the whole run.
                logger.warning("Skipping submission %s (%s): %s",
                                item.get("id"), item.get("titleSlug"), exc)
                continue

        return submissions

    def get_problem_metadata(self, slug: str) -> dict:
        query = """
        query questionMeta($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionFrontendId
            title
            difficulty
          }
        }
        """
        data = self._post({"query": query, "variables": {"titleSlug": slug}})
        question = data.get("question")
        if not question:
            raise LeetCodeAPIError(f"No metadata returned for problem '{slug}'")
        return question

    def get_submission_code(self, submission_id: str) -> Optional[str]:
        """
        Fetch the source code for a specific accepted submission.

        This is only possible for YOUR OWN submissions while authenticated
        as you — LeetCode does not expose other users' solution code, and
        this client never attempts to retrieve it. If this endpoint ever
        stops returning code (LeetCode has changed undocumented behavior
        before), the sync should degrade gracefully rather than fail hard:
        the caller stores the problem metadata/README without a code file
        and logs a warning.
        """
        query = """
        query submissionDetails($submissionId: Int!) {
          submissionDetails(submissionId: $submissionId) {
            code
          }
        }
        """
        try:
            data = self._post({
                "query": query,
                "variables": {"submissionId": int(submission_id)},
            })
        except LeetCodeAPIError as exc:
            logger.warning("Could not fetch code for submission %s: %s", submission_id, exc)
            return None

        details = data.get("submissionDetails")
        if not details:
            return None
        return details.get("code")

    def get_progress_stats(self) -> ProgressStats:
        query = """
        query userProgress($username: String!) {
          matchedUser(username: $username) {
            submitStats {
              acSubmissionNum { difficulty count }
              totalSubmissionNum { difficulty count }
            }
          }
        }
        """
        data = self._post({"query": query, "variables": {"username": self.username}})
        matched = data.get("matchedUser")
        if not matched:
            raise LeetCodeAPIError(
                f"No such LeetCode user '{self.username}', or profile is private."
            )

        ac = {row["difficulty"]: row["count"] for row in matched["submitStats"]["acSubmissionNum"]}
        total = {row["difficulty"]: row["count"] for row in matched["submitStats"]["totalSubmissionNum"]}

        return ProgressStats(
            total_solved=ac.get("All", 0),
            easy_solved=ac.get("Easy", 0),
            medium_solved=ac.get("Medium", 0),
            hard_solved=ac.get("Hard", 0),
            total_submissions=total.get("All", 0),
            accepted_submissions=ac.get("All", 0),
        )
