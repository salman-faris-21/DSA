# Setup Guide

## 1. Get your LeetCode session credentials

There is no LeetCode OAuth app for this, so authentication uses your own
browser session cookies (the same way the LeetCode website itself stays
logged in). This only ever accesses **your own account**.

1. Log in to [leetcode.com](https://leetcode.com) in your browser.
2. Open DevTools → Application (Chrome) or Storage (Firefox) → Cookies →
   `https://leetcode.com`.
3. Copy the values of:
   - `LEETCODE_SESSION`
   - `csrftoken`

These act like a password — treat them the same way. They will expire
periodically (LeetCode session cookies typically last a few weeks to
months), at which point the workflow's auth step will fail with a clear
"credentials expired" error in the logs, and you'll repeat this step.

## 2. Configure the repository

Edit `config.yml` at the repo root:

```yaml
leetcode:
  username: "your-leetcode-username"
github:
  repository: "your-username/your-repo"
  branch: "main"
```

Adjust `preferred_languages`, `solution_dir`, etc. as you like.

## 3. Add GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name             | Value                              |
|--------------------------|-------------------------------------|
| `LEETCODE_SESSION`       | value of the `LEETCODE_SESSION` cookie |
| `LEETCODE_CSRF_TOKEN`    | value of the `csrftoken` cookie     |

No GitHub token needs to be added manually — the workflow uses the
built-in `GITHUB_TOKEN` (already granted `contents: write` in the
workflow file) to commit and push.

> If your default branch is protected in a way that blocks the built-in
> `GITHUB_TOKEN` from pushing directly (e.g. required PR reviews), you'll
> need to either allow GitHub Actions to bypass that rule for this bot,
> or switch to a personal access token stored as an additional secret
> (e.g. `GH_PAT`) and reference it in the checkout/push steps instead.

## 4. Enable GitHub Actions

Actions are usually enabled by default for a repo once you push the
`.github/workflows/leetcode-sync.yml` file. If not: **Settings → Actions
→ General → Allow all actions**.

## 5. Run the first sync manually

1. Go to the **Actions** tab → **LeetCode Sync** workflow.
2. Click **Run workflow** (this uses the `workflow_dispatch` trigger).
3. Watch the run logs. On success, check the repo for a new commit like:

   ```
   leetcode: sync new solutions
   ```

## 6. Verify ongoing sync

- Solve a new problem on LeetCode.
- Wait for the next scheduled run (every 6 hours by default — see
  `sync.schedule_cron` in `config.yml` and the `cron:` line in the
  workflow file, which must be kept in sync manually since GitHub Actions
  doesn't read `config.yml` for scheduling), or trigger it manually via
  **Run workflow**.
- Confirm the new problem appears under `leetcode/<difficulty>/` and the
  README's `LeetCode Progress` section reflects the updated count.

## Troubleshooting

| Symptom in logs | Cause | Fix |
|---|---|---|
| `Missing LeetCode credentials` | Secrets not set | Re-check step 3 |
| `LeetCode rejected credentials (HTTP 401/403)` | Session expired | Repeat step 1, update secrets |
| `No such LeetCode user` | Wrong username or private profile | Fix `config.yml`, make profile public |
| Workflow runs but no commit appears | Nothing new to sync | Expected — it's idempotent |
| `Rate limited by LeetCode` warnings | Too frequent polling | Increase `schedule_cron` interval |
