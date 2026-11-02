# QA Report — {{TITLE}}

**Slug:** {{SLUG}}
**QA Lead:** qa-lead
**Date:** {{DATE}}
**Gate:** G6 — Sign-off

---

## 1. Automated validation

Command run:

```
python scripts/validate_post.py --slug {{SLUG}}
```

Output:

```
{{VALIDATOR_OUTPUT}}
```

## 2. File inventory

| Expected | Exists | Size | Note |
|---|---|---|---|
| | | | |

## 3. Image inspection

Every image opened at full size.

| Image | Dimensions | Mode | Size | Crop | Type legible at 200px | Credit strip | Verdict |
|---|---|---|---|---|---|---|---|
| 01-cover.jpg | | | | | | | |

## 4. Carousel order

Filenames sort correctly and match `08-visual-plan.md`:

{{ORDER_CHECK}}

## 5. Caption checks

| Check | Instagram | Facebook |
|---|---|---|
| Within character limit | | |
| Hook in first 125 chars | | |
| Hashtags present and specific | | |
| Alt text present | | |
| Credits present | | |
| AI disclosure (if required) | | |

## 6. Claim traceability

Every factual statement in the captions maps to a claim ID.

| Caption statement | Claim ID | Present in ledger |
|---|---|---|
| | | |

## 7. Path verification

| Path named in deliverables | Exists |
|---|---|
| | |

## 8. Defects found

| Defect | Severity | Owner | Fix required |
|---|---|---|---|
| | | | |

## 9. Decision

**Status:** SIGNED OFF | BLOCKED

{{DECISION_NOTES}}
