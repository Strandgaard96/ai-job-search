# job-scraper: Portal Discovery + Coverage Reporting

Status: Approved (sub-project 1 of 3; see "Related work" below)
Date: 2026-07-08

## Problem

`job-scraper`'s `SKILL.md` (Step 1: Search) currently instructs Claude to run generic `WebSearch`
queries against `search-queries.md`'s site list. It never mentions the 5 dedicated portal CLIs
that actually exist in `.agents/skills/*-search/` (`jobindex-search`, `jobbank-search`,
`jobdanmark-search`, `jobnet-search`, `linkedin-search`).

Consequences observed in practice during a live `/scrape` run:
- Generic `WebSearch` against jobindex.dk returned stale/archived listings (301 redirects to
  `jobindexarkiv.dk`, expired postings from 2015) instead of live results.
- The dedicated CLIs were only discovered by accident, and only after the user asked "did you
  search X" three separate times (jobindex → linkedin → jobbank/jobdanmark/jobnet).
- Oslo (a location the candidate's own `search-queries.md` marks as acceptable) was silently
  skipped on the first LinkedIn pass and only queried after the user asked directly.
- The user had no way to tell, from the presented results, which sites had actually been
  searched versus silently skipped.

## Goal

1. Fix the root cause: `job-scraper` discovers and uses the installed portal CLIs automatically,
   instead of relying on a static/generic WebSearch instruction that can silently miss tools.
2. Make coverage visible: every `/scrape` run ends with a report of which portals were searched
   (and with which locations), which were skipped, and why — so the user never has to ask.

## Non-goals

- Reformatting `search-queries.md`'s query categories into a new portal-agnostic keyword format.
  Job-scraper will keep deriving keywords from the existing `site:`-prefixed strings (stripping
  the `site:`/location boilerplate at runtime) — no upfront rewrite of that file.
- Adding a default Oslo/Norway query category to `search-queries.md`. That's a content edit the
  user makes separately (e.g. via `/setup --section search`), not part of this fix.
- Building a WebSearch fallback for sites without a dedicated CLI (karriere.dk, jobfinder.dk,
  akademikernes.dk). These are reported as uncovered; the user's stated preference is to either
  run `/add-portal` for them later, or just paste a posting directly into `/apply` when they find
  one manually. No scraping fallback is built for the no-CLI case.

## Design

### 1. Portal discovery (replaces static WebSearch instruction)

`job-scraper`'s Step 0 (Load State) gains a discovery step:

- `Glob(".agents/skills/*/SKILL.md")`, keep only folders whose name matches `*-search` and that
  contain a `cli/src/cli.ts`. This is the live roster of queryable portals for this run — never
  a hardcoded list in `job-scraper`'s own `SKILL.md`. When a new portal skill is added later via
  `/add-portal` (e.g. a Norwegian site), it is automatically picked up on the next `/scrape` run
  with no edit to `job-scraper` required.
- For each discovered portal, read its `SKILL.md` "Key flags" section once to determine: does it
  accept `--location`/`-l` (like `linkedin-search`), or does it fold location into the keyword
  query / a region-code flag (like `jobbank-search --location 2`, `jobnet-search --region ...`,
  `jobdanmark-search --municipality ...`)? This determines how Step 1 calls it.

### 2. Query derivation (Step 1 rewrite)

For the default run (or the categories implied by a user-specified focus area, or all categories
for `/scrape broad`), Step 1 takes each priority category's query strings from `search-queries.md`
and, for each discovered portal:

- Strips the `site:<domain>` prefix and any bare location tokens already embedded in the string
  (e.g. `Copenhagen`, `OR [YOUR_REGION]`) to recover the core keyword/title phrase.
- Calls the portal's CLI `search` command with that keyword via whichever flag it uses
  (`--query`, `--key`, `--text`, `--search-string`), plus the portal's own location mechanism
  (region code, municipality name, or `--location` string) sourced from the candidate's location
  filter in `search-queries.md`.
- No new file format is introduced. `search-queries.md` is not edited by this change.

Sites listed in `search-queries.md` that have no matching discovered CLI (karriere.dk,
jobfinder.dk, akademikernes.dk as of this writing) are **not** queried via WebSearch. They are
carried through to the coverage report as uncovered.

### 3. Coverage report (Step 5 addition)

Before presenting the job-matches table, `/scrape` prints a "Portal Coverage" table:

```
### Portal Coverage
| Portal | Status | Locations queried |
|--------|--------|--------------------|
| jobindex-search | Searched | Denmark-wide (city in query) |
| jobbank-search | Searched | Storkøbenhavn |
| jobdanmark-search | Searched | København |
| jobnet-search | Searched | Hovedstaden og Bornholm |
| linkedin-search | Searched | Copenhagen |
| karriere.dk | Not searched | no CLI installed — /add-portal or paste posting into /apply |
| jobfinder.dk | Not searched | no CLI installed |
| akademikernes.dk | Not searched | no CLI installed |
```

Rules:
- "Locations queried" reflects what was **actually** passed this run — not a fixed list. If only
  Copenhagen was queried on `linkedin-search` (Oslo not included this run), the table says
  "Copenhagen", not "Copenhagen, Oslo", even though Oslo is a supported location for that portal.
- If a portal call errors (rate limit, timeout, non-zero exit), its row shows `Error` with a short
  reason (e.g. "rate limited, backed off") instead of being silently dropped from the table or
  conflated with "Searched".
- If the user ran a focus area or `/scrape broad`, the report reflects exactly which priority
  categories were used per portal (e.g. "Priority 1–3" vs "all categories").

## Files touched

- `.claude/skills/job-scraper/SKILL.md` — Step 0 gains portal discovery; Step 1 rewritten to
  derive per-portal queries from discovered CLIs instead of generic WebSearch; Step 5 gains the
  Portal Coverage table.

No other files change. `search-queries.md` is read but not modified by this change.

## Testing / verification

- Run `/scrape` and confirm the Portal Coverage table lists all 5 currently-installed CLIs as
  "Searched" and the 3 no-CLI sites as "Not searched".
- Run `/scrape` again after temporarily renaming one CLI folder (e.g. `jobnet-search` →
  `jobnet-search.bak`) and confirm it drops out of the discovered roster and shows as absent from
  the report rather than erroring the whole run.
- Confirm no WebSearch calls are made for karriere.dk/jobfinder.dk/akademikernes.dk during a run.

## Related work (not in this spec)

This is sub-project 1 of 3 requested together. The other two — adding Norwegian job-portal CLIs
via `/add-portal`, and a RenderCV-based CV renderer replacing LaTeX — are independent subsystems
and will each get their own spec after this one ships.
