# Cluefolio Studio OS

Local command center for the season: all 11 posts, the rendered covers, full stories,
Instagram and Facebook captions, hashtags, keywords, SEO metadata, the content
calendar, and the production pipeline.

## Run it

Double-click `serve.bat`, or from the project root:

```powershell
python dashboard/serve.py
```

Then open <http://127.0.0.1:8080/dashboard/>.

The server binds to localhost only. Use `--port 8090` if 8080 is taken,
or `--no-browser` to skip opening a window.

## What it reads

- `content/dashboard.json` — compiled payload for every view
- `content/<slug>/images/*.jpg` — rendered covers and carousel frames
- `site/index.html` — the public static site, linked from the top bar

All data is authored in `scripts/dashboard_content.py` and compiled by
`scripts/build_dashboard_data.py`. To refresh after an edit:

```powershell
python scripts/build_dashboard_data.py
```

Then press the refresh button in the dashboard (or reload the page).
