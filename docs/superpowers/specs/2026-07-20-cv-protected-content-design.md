# CV Protected Content: Lock Sections Against Cutting/Rewording

Status: Approved (sub-project 1 of 2; see "Related work" below)
Date: 2026-07-20

## Problem

`/apply`'s drafter and reviewer freely cut and reword `cv.yaml` content when tailoring a
per-company override, following `05-cv-templates.md`'s relevance-weighted cutting guidance. This
guidance has no concept of content that must never be touched regardless of relevance score.

Consequence observed in practice: during a live `/apply` run for DNV, the reviewer's Part A edits
and the drafter's own tailoring trimmed the publications list from 4 entries to 2 (mirroring the
pattern already used in `overrides/orsted.yaml`), without flagging the cut or asking first. The
user only caught it because they were watching the diff mid-turn and said "Don't remove any of my
publications. Keep all of them." Nothing before that point would have caught a silent drop if the
user hadn't been watching closely.

## Goal

Let the candidate mark specific `cv.yaml` sections as protected, at two independent levels:
- **no_cut**: every entry present in the master must survive into any override that touches that
  section.
- **no_reword**: entries that do appear in an override must match the master's text exactly.

Turn this into an automated gate (a script check), not a documentation reminder the drafter can
forget under token pressure — the same category of problem `05-cv-templates.md`'s page-budget
rules already solve for page count, just for content integrity instead of layout.

## Non-goals

- Per-item (bullet-level) locking. Only whole-section locking is in scope (e.g. "all of
  Publications," not "just this one publication"). If a future need arises for finer granularity,
  that's a separate follow-up — YAGNI for now.
- Enforcing protection inside `cv.yaml` itself (the master file is always the source of truth and
  is never "wrong" relative to itself). Protection only constrains override files.
- Any change to `build.py`'s `pdf` or `profile` subcommands' existing behavior. This adds a new
  `validate` subcommand alongside them.
- Locking `experience` or `skills` sections by default. Tailoring those per-role is the explicit
  purpose of `/apply` — only `publications` and `projects` are protected out of the box.

## Design

### 1. `cv/protected.yaml` — new file, sits beside `cv.yaml`

```yaml
no_cut:
  - publications
  - projects
no_reword:
  - projects
```

Kept **out of `cv.yaml`** and never merged into the RenderCV input in `build_pdf()`. `cv.yaml`
must stay exactly what RenderCV's schema expects; this file is tooling-only metadata read solely
by the new `validate` subcommand.

Section names are keys under `cv.sections` in `cv.yaml` (`summary`, `experience`, `skills`,
`publications`, `projects`, `education`). Any subset may appear under either list; a section may
appear in both.

### 2. Per-section match keys

To compare "the same entry" between master and override without relying on list position (an
override may reorder), each section type has a defined identity key:

| Section | Match key | Fallback |
|---|---|---|
| `publications` | `doi` | `title` if `doi` absent |
| `experience` | `company` + `position` + `start_date` | — |
| `projects` | `name` | — |
| `skills` | `label` | — |
| `summary` | whole list as one unit | — |
| `education` | `institution` + `degree` + `start_date` | — |

These keys live as a small constant dict in `build.py` (not in `protected.yaml` — they're
structural facts about the schema, not per-candidate configuration).

### 3. `build.py validate` — new subcommand

```bash
cd cv && uv run python build.py validate --override overrides/dnv.yaml
```

Algorithm:
1. Load `cv.yaml` (master) and `protected.yaml`. Load the override file.
2. For each section name in `protected.yaml`'s `no_cut` list:
   - If the override's `cv.sections` does not contain this key at all, skip (nothing to check —
     the section is inherited unchanged from master).
   - Otherwise, compute the match-key set from master's version of the section and from the
     override's version. Any master key missing from the override's set is a violation:
     `no_cut: <section> missing entries: [<match keys>]`.
3. For each section name in `protected.yaml`'s `no_reword` list:
   - If the override doesn't contain the section, skip.
   - For each override entry, find the master entry with the same match key (skip entries that are
     genuinely new — not in master at all — those are additions, not rewords, and are out of
     scope for this check).
   - Compare all fields of the matched pair as normalized dicts (order-independent keys, exact
     string equality on values). Mismatch is a violation:
     `no_reword: <section> entry '<match key>' differs from master`.
4. Print all violations found (if any) and exit 1. If none, print `OK` and exit 0.

### 4. Wiring into `/apply`

- **`.claude/commands/apply.md` Step 4** (after edits are applied, before Step 5's compile) gains a
  sub-step: run `build.py validate --override overrides/<company>.yaml`. On failure, the drafter
  must either restore the flagged content or explicitly ask the user to confirm the cut/reword
  before proceeding — never silently pass through a violation.
- **`05-cv-templates.md`**, under "Relevance-weighted cutting," gains a note: sections listed in
  `cv/protected.yaml`'s `no_cut` are excluded from the cutting algorithm entirely — never a
  candidate for the lowest-score cut, regardless of how low a publication or project scores on
  relevance to the current posting.
- **`CLAUDE.md`** Verification Checklist, Quality subsection, gains one line: "Protected-content
  validation passes (`build.py validate`)."

## Files touched

- `cv/protected.yaml` — new file (initial content: `publications`, `projects` under `no_cut`;
  `projects` under `no_reword`).
- `cv/build.py` — new `validate` subcommand, match-key constant, comparison logic.
- `cv/tests/test_build.py` — new tests for the validation function.
- `.claude/commands/apply.md` — Step 4 gains the validation sub-step.
- `.claude/skills/job-application-assistant/05-cv-templates.md` — cutting-algorithm note.
- `CLAUDE.md` — one checklist line.

## Testing / verification

- Unit tests in `cv/tests/test_build.py`, following the existing plain-pytest style (no
  fixtures/mocks framework currently in use):
  - `no_cut` violation detected when an override drops a protected entry.
  - `no_reword` violation detected when an override changes a protected entry's text.
  - Section untouched by the override (key absent) passes trivially.
  - Section present and fully compliant passes.
  - New entry in the override not present in master (an addition, not a removal) does not trigger
    a `no_reword` false positive.
- One smoke test running `validate` against the real `overrides/dnv.yaml` and `protected.yaml` as
  a positive control — should pass now that all 4 publications were restored during this session.

## Related work (not in this spec)

Requested together with a second, independent fix: making job-scraper result-table URLs
selectable as plain text in tmux copy-mode. See
`2026-07-20-job-scraper-clickable-url-design.md`.
