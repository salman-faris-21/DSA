# Architecture

## Layers

```
scripts/
├── leetcode_client.py   # LeetCode data-fetching layer (only layer that talks to LeetCode)
├── state.py              # idempotency: tracks what's already been synced
├── repo_writer.py        # writes solution files + per-problem README into leetcode/
├── readme_updater.py     # updates only the marked dashboard section of the root README
└── sync.py               # orchestrator glueing the above together; called by CI
```

The LeetCode layer (`leetcode_client.py`) returns plain `Submission` /
`ProgressStats` objects and never touches the filesystem or git. The repo
layer (`repo_writer.py`, `readme_updater.py`) never talks to LeetCode. This
means either side can be replaced independently — e.g. if LeetCode's
GraphQL schema changes, or you want to point this at a different judge
entirely, only `leetcode_client.py` needs to change.

## LeetCode integration approach

LeetCode has no official, documented public API for retrieving your own
submission source code. The approach used here — calling the same
GraphQL endpoint (`https://leetcode.com/graphql`) that the LeetCode
website itself calls, authenticated with your own session cookie — is the
standard approach used by the broader ecosystem of LeetCode-sync tools,
and is considerably more stable than scraping rendered HTML pages, since
it's a single structured JSON endpoint.

Because it's still unofficial:

- All calls go through one retry/backoff wrapper (`LeetCodeClient._post`).
- Auth failures (expired session) are surfaced clearly rather than
  retried blindly, since retrying won't fix an expired cookie.
- If LeetCode ever stops returning submission code from this endpoint,
  `repo_writer.write_solution` degrades gracefully: it still writes the
  per-problem README with metadata and skips only the source file,
  logging a warning instead of failing the whole run.
- The fetch/GitHub layers are separated (see above) specifically so this
  endpoint can be swapped for an official API in the future with minimal
  blast radius.

## Idempotency

Two independent safety nets prevent duplicate work:

1. `leetcode/.sync_state.json` records every `(problem slug, language)`
   pair that has already been synced, keyed off LeetCode's own problem
   slug/number — the natural unique identifier.
2. `repo_writer._write_if_changed` compares new content against what's
   already on disk and only writes (and thus only stages for commit)
   when something actually differs.

The workflow itself also checks `git status --porcelain` before
committing, so a run with no new submissions and no stat changes produces
zero commits.

## Copyright handling

Per-problem READMEs store only metadata (title, number, difficulty, URL,
language) plus a short, user-authored description/approach — never the
full LeetCode problem statement, which is copyrighted content owned by
LeetCode.
