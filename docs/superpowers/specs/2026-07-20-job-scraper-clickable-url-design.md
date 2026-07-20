# job-scraper: URL Text That Survives tmux Copy-Mode

Status: Approved (sub-project 2 of 2; see "Related work" below)
Date: 2026-07-20

## Problem

`job-scraper`'s Step 5 results table renders each job's URL as a markdown hyperlink with generic
anchor text: `[Link](https://...)`. In a normal terminal this is clickable. In tmux, once the user
enters mouse/copy mode to scroll back up through terminal history to reach the table (scrollback
and live-click handling are mutually exclusive in tmux's mouse mode), the hyperlink is no longer
clickable — and the only text available to select and copy is the word "Link," which is useless.

## Goal

Make the URL itself recoverable by copy-paste from terminal scrollback, without giving up
clickability in the normal case.

## Non-goals

- Changing `/rank`'s shortlist table format. The user confirmed this fix is scoped to
  `job-scraper`'s own Step 5 table only; `/rank` presents a different table and is out of scope
  for this round.
- Any change to how URLs are fetched, stored in `seen_jobs.json`, or deduplicated. This is a
  presentation-only fix in the Step 5 template.
- Building a copy-to-clipboard mechanism or terminal-integration feature. The fix is purely about
  what text is visible/selectable in the rendered table.

## Design

Change the Step 5 table template in `.claude/skills/job-scraper/SKILL.md` so the link's anchor
text is the URL itself, not a generic label:

Before:
```
| 1 | High | ... | [Link](https://www.jobindex.dk/jobannonce/h1679626/...) |
```

After:
```
| 1 | High | ... | [https://www.jobindex.dk/jobannonce/h1679626/...](https://www.jobindex.dk/jobannonce/h1679626/...) |
```

This is still a clickable markdown link in any renderer that supports them (unchanged behavior in
the normal case), but the visible text is now the real URL. In tmux copy-mode, where the click
handler is unavailable, the user can select and copy the visible text directly and get a working
URL — no click required.

Same treatment applies to the "High-Match Highlights" section's per-job link if one is present
there (currently the highlights are bullet points without an explicit URL repeat, so no change
needed there unless a future edit adds one).

## Files touched

- `.claude/skills/job-scraper/SKILL.md` — Step 5's example table template updated to show the URL
  as its own anchor text instead of "Link".

## Testing / verification

- Run `/scrape` and confirm the presented table's link column shows the full URL as visible text,
  and that clicking it still navigates correctly in a standard terminal.
- No automated test — this is a formatting change to a skill's markdown instructions, not
  executable code.

## Related work (not in this spec)

Requested together with a second, independent fix: locking specific `cv.yaml` sections
(publications, projects) against being cut or reworded during `/apply` tailoring. See
`2026-07-20-cv-protected-content-design.md`.
