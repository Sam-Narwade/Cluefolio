# Cluefolio automation

Free, end-to-end publishing for an approved Cluefolio package.

```
GitHub Actions (Wed 17:00 UTC)
        │
        ├── reads content/dashboard.json
        ├── validates images, captions, and public URLs
        ├── Instagram Graph API  → carousel or single image
        ├── Facebook Graph API   → multi-photo post
        ├── pins the source-ledger first comment
        ├── records IDs in automation/state/published.json
        └── commits the ledger back to the repo
```

Content creation and fact-checking stay in the editorial pipeline. This layer
automates packaging, scheduling, publishing, first comments, and the audit trail.

## What it costs

| Piece | Free tier |
|---|---|
| Scheduler + compute | GitHub Actions |
| Public image host | GitHub Pages |
| Instagram + Facebook posting | Meta Graph API |
| Ledger | JSON in the repo |
| Notifications | Discord webhook (optional) |

A **public** GitHub repository is the simplest free setup because GitHub Pages
for private repositories requires a paid plan. The repository contains no
credentials; secrets live in GitHub Settings.

## One-time Meta setup

1. Convert the Instagram account to **Business** or **Creator**.
2. Create a Facebook **Page** and link the Instagram account to it.
3. Create a Meta app at <https://developers.facebook.com/apps>.
4. Add the **Facebook Login for Business** and **Instagram Graph API** products.
5. Request these permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
6. Complete App Review for the publish permissions.
7. Generate a **long-lived Page access token** and note the Page ID and
   Instagram Business Account ID.

The account must be a Business/Creator account. The API cannot post to a
personal Instagram account.

## One-time GitHub setup

1. Push this repository to GitHub.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. **Settings → Secrets and variables → Actions → Secrets**:

   | Secret | Value |
   |---|---|
   | `META_PAGE_ID` | Facebook Page ID |
   | `META_IG_USER_ID` | Instagram Business Account ID |
   | `META_PAGE_ACCESS_TOKEN` | Long-lived Page token |
   | `PUBLIC_BASE_URL` | `https://USERNAME.github.io/REPO` |
   | `DISCORD_WEBHOOK_URL` | Optional |

4. **Settings → Environments → New environment → `production`** and add
   yourself as a **required reviewer**. This is the human approval gate.
   Remove the required reviewers only if you want fully unattended runs.
5. Run **Actions → Deploy public site → Run workflow**.
6. Open `PUBLIC_BASE_URL/content/first-post/images/01-cover.jpg` and confirm it
   returns a JPEG. Meta must be able to fetch this URL.

`PUBLIC_BASE_URL` has no trailing slash. For a custom domain, use that domain.

## Local setup

```powershell
copy .env.example .env
# fill in the values, then:
python -m automation.doctor
python -m automation.publish --post 001 --dry-run
```

`doctor` checks the Page token, the Page-to-Instagram link, and a public image
URL. Dry-run validates file sizes, aspect ratios, caption limits, hashtag
counts, and the exact API plan without calling Meta.

Publish a specific post for real:

```powershell
python -m automation.publish --post 002
```

Publish whatever is scheduled for today in `America/New_York`:

```powershell
python -m automation.publish --due
```

## Schedule

`.github/workflows/publish.yml` runs every **Wednesday at 17:00 UTC**:

- 12:00 EST (November–March)
- 13:00 EDT (March–November)

That keeps the run inside the brand's 12:00–13:00 ET window. Manual runs are
available from the Actions tab. `dry_run` defaults to **true** for manual runs.
GitHub may delay scheduled jobs by a few minutes; that is normal.

The job targets the `production` environment, so a required reviewer must
approve before any token is used.

## Idempotency and partial failures

`automation/state/published.json` records the Instagram media ID and Facebook
post ID for every post. The workflow commits it back to the repository.

- A rerun skips a post already marked `published`.
- If Instagram succeeds and Facebook fails, the ledger keeps the Instagram ID
  and the next run resumes at Facebook.
- `--force` republishes both platforms. This creates duplicates; use it only
  when you intend to.

`automation/state/last-run.json` is uploaded as a workflow artifact and ignored
by git.

## Token refresh

Long-lived Page tokens can expire. Refresh locally:

```powershell
python -m automation.refresh_token --write .env.tokens
```

Then update the `META_PAGE_ACCESS_TOKEN` secret with the new Page token and
delete `.env.tokens`. The script never writes to GitHub.

## Files

| File | Purpose |
|---|---|
| `automation/publish.py` | CLI, selection, validation, ledger, notifications |
| `automation/content.py` | Due-post selection, plan building, pre-flight |
| `automation/publisher.py` | Instagram and Facebook API operations |
| `automation/graph.py` | Graph client with retries and error mapping |
| `automation/ledger.py` | Atomic JSON ledger |
| `automation/doctor.py` | Credential and public-URL checks |
| `automation/refresh_token.py` | Long-lived Page token exchange |
| `scripts/build_public.py` | Pages artifact with all post images |
| `.github/workflows/publish.yml` | Wednesday schedule + approval gate |
| `.github/workflows/deploy-pages.yml` | Public site and image deployment |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Access token is invalid or expired` | Refresh the token, update the secret |
| `Permission denied` | Complete App Review; confirm the Page role |
| `Media URL is not accessible` | Deploy Pages; check `PUBLIC_BASE_URL` |
| `Unsupported aspect ratio` | Export at 1080×1350, 4:5 |
| No post due | The schedule is Wednesday; use `--post` for a manual run |
| Ledger push rejected | Re-run the workflow; it will fetch and commit again |

## Safety

- Never commit `.env` or `.env.tokens`.
- Never paste a token into a caption, issue, or chat.
- Required reviewers on `production` are the last line of defense.
- The publisher refuses placeholder hosts, local URLs, oversized files, and
  captions over the platform limits.
- AI-reconstructed covers remain labeled on the image and in the caption.

## Tests

```powershell
python -m unittest discover -s automation/tests -v
```
