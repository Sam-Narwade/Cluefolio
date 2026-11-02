# Resource Register

What we actually checked, what we adopted, and what we rejected. Short and actionable.

Legend:
- **Available** — already in the environment, reusable now.
- **Adopted** — verified and integrated into this workflow.
- **Inaccessible** — useful, but blocked by cost, auth, hardware, or terms.
- **Rejected** — investigated and not worth it, with a reason.

Last updated: 2026-10-19

---

## 1. Already available and reusable

| Resource | What it does | Why it matters | License / terms | Requirements | Status |
|---|---|---|---|---|---|
| OpenCode v2.0.26 | Agent runtime, subagents, skills, permissions | Runs the whole studio | Proprietary client | Installed | **Available** — verified |
| `websearch` tool | Web search | Story discovery, source finding | Provider terms | Built in | **Available** — used |
| `webfetch` tool | Fetch pages as markdown/text/html | Reading archives, docs, catalogs | Target site terms | Built in | **Available** — used |
| Wikimedia Commons API | Search and metadata for 100M+ media files | Primary archival image source with machine-readable licenses | CC/PD per file; API terms | HTTP | **Adopted** — verified, used |
| Library of Congress (loc.gov) | US national archive, photo collections | Authoritative US imagery, "no known restrictions" records | Per item; many PD | HTTP | **Adopted** — verified, used |
| National Archives (archives.gov / catalog) | Federal records and photographs | Primary-source documents and images | Mostly PD (US Gov) | HTTP | **Adopted** — verified, used |
| Newberry Library IIIF | Chicago history collections, Eastland records | Deep local archives with open-access policy | "No Copyright – United States" per item | IIIF | **Available** — manifest verified |
| Pillow 12.3 | Image processing | Crop, grade, composite, export | HPND | Python | **Adopted** — used |
| numpy 2.5 | Array math | Grain, tone curves, fast compositing | BSD | Python | **Adopted** — used |
| ffmpeg 9.0 | Video/audio encode | Future Reels adaptation | LGPL/GPL build | Installed | **Available** — verified |
| Playwright 1.64 + Chromium | Headless browser | Rendering HTML-based layouts, screenshotting | Apache-2.0 | Installed | **Available** — verified |
| Georgia / Segoe UI | System fonts | Brand typography | Microsoft system fonts | Windows | **Adopted** — used |
| `agent-reach` CLI | Multi-platform fetch (YouTube, RSS, Jina reader) | Supplemental research | MIT-ish; per-backend terms | Installed | **Available** — doctor run |

## 2. Verified and adopted

| Resource | Role in workflow | Verification performed | Limitation |
|---|---|---|---|
| Wikimedia Commons API (`action=query&prop=imageinfo`) | Image search + license extraction | Live queries returned files with `LicenseShortName`, `Artist`, `Credit`, dimensions | Rate limits (HTTP 429) under rapid automated requests; requires UA and backoff |
| NARA direct image files | High-resolution archival photos | Downloaded and inspected `eastlandcapsized-281841.jpg` (1200×956) | Some catalog endpoints are JS-rendered; direct file URLs work |
| LOC direct image CDN (`cdn.loc.gov`) | Photo downloads | Downloaded `3a30783r.jpg` (640×465, grayscale) | Small derivatives; TIFF masters exist but are large |
| Newberry IIIF Presentation API | Record metadata and rights | Manifest returned HTTP 200 | Image endpoint returned 500 on one asset; use manifest metadata, not image proxy |
| `tesseract` (optional) | OCR of newspaper scans | Not installed | Would help verify 1915 headlines; not required for this post |

## 3. Useful but not currently accessible

| Resource | What it would add | Blocker | Workaround used |
|---|---|---|---|
| Pollinations.ai image API | Free text-to-image | Now returns **HTTP 402 Payment Required** | Not needed — authentic archival imagery is stronger |
| Hugging Face Inference API | Hosted open-weight image models | No token configured; free tier gated | Not needed for this story |
| Replicate / fal.ai / Stability | High-quality generation and upscaling | Paid; no authorization | Rejected on cost grounds |
| Local Stable Diffusion / ComfyUI | Local generation | No discrete GPU; Intel Iris Xe only, 32 GB RAM | Not practical; would take hours per usable image |
| GitHub API / `gh` | Repo search, issue research | `gh` not authenticated | Used public web search and raw URLs instead |
| Reddit API | Audience research | Anonymous JSON blocked; OAuth requires approval | Used public web search only; no scraping |
| Instagram / Facebook public data | Audience and format research | Login-walled; scraping violates terms | Relied on official platform specs and public documentation |
| Google Trends | Keyword demand | No accessible API without auth | Used qualitative search-term reasoning |
| Exa semantic search | Broad research | Configured in `mcporter` but not connectivity-verified | Not claimed as working; used `websearch` instead |

## 4. Investigated and rejected

| Resource | Reason for rejection |
|---|---|
| Pollinations.ai | Paywalled as of this run (HTTP 402). No free tier available. |
| AI-generated "historical" imagery for this story | Authentic public-domain photographs exist and are better. Generating would be both unnecessary and an authenticity risk. |
| Upscaling archival scans with AI | Would invent texture and detail not present in the record. Violates editorial standards. |
| ComfyUI / AUTOMATIC1111 local install | No suitable GPU; install size and runtime cost are disproportionate for one post. |
| Scraping Instagram/Facebook | Violates platform terms and requires bypassing access controls. |
| Paid stock libraries | Unnecessary; public-domain archives cover the story. |
| Building a database or orchestration service | Overkill for a file-based pipeline. Flat files and three scripts are sufficient. |
| `gh` CLI repo search | Not authenticated; public search was sufficient for discovery. |

## 5. Cost record

| Item | Cost |
|---|---|
| OpenCode models used | $0 (free-tier models) |
| Image generation | $0 (not used) |
| Archives and APIs | $0 |
| Fonts | $0 (system fonts) |
| **Total** | **$0** |

No subscriptions, credits, or paid API calls were activated.

## 6. Reuse guidance

Reuse for future posts:
- Wikimedia Commons + LOC + NARA as the default archival triad.
- The `fetch_assets.py` → `render_post.py` → `validate_post.py` chain.
- The claim-ID ledger and G2 factual lock.
- The 1080×1350 archival-first visual system.

Re-evaluate per post:
- Image count and sequence.
- Whether an AI reconstruction is genuinely needed (and if so, disclose it).
- Hashtag and timing choices.
