---
name: job-scraper
description: >
  Scrapes Danish job sites for new positions matching your profile. Deduplicates across runs.
  Triggers on: job scrape, find jobs, search jobs, new jobs, job search, scrape jobs, /scrape
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Agent, AskUserQuestion
---

# Job Scraper

---

## How It Works

This skill searches multiple Danish job sites using targeted queries based on your profile, deduplicates against previously seen jobs and the application tracker, and presents new matches with a quick fit assessment.

## Invocation

The user triggers this skill by saying things like:
- "Find new jobs"
- "Scrape for jobs"
- "Any new positions?"
- "/scrape"

Optional arguments:
- A focus area, e.g. "/scrape data science" or "/scrape geophysics"
- "broad" to run all search categories, e.g. "/scrape broad"

---

## Execution Steps

### Step 0: Load State

1. Read `job_scraper/seen_jobs.json` (create if missing - start with `{"seen": {}}`)
2. Read `job_search_tracker.csv` to extract already-applied companies+roles
3. Read `search-queries.md` (this directory) for the search strategy
4. Discover installed portal CLIs: run `Glob(".agents/skills/*/SKILL.md")`, keep only paths whose
   parent directory name ends in `-search` and that also has a `cli/src/cli.ts` file (confirm
   with `Glob(".agents/skills/<name>/cli/src/cli.ts")` per candidate). This is the live roster of
   portals for this run - never hardcode portal names here. When a new portal skill is added
   later (e.g. via `/add-portal`), it is picked up automatically on the next run with no edit to
   this file.
5. For each discovered portal, read its `SKILL.md` "Key flags" section once to note: the keyword
   flag it uses (`--query`, `--key`, `--text`, `--search-string`), and how it takes location
   (`--location`/`-l` as free text, a region/municipality flag, or folded into the keyword query -
   documented in that portal's own `SKILL.md`).

### Step 1: Search

For each portal discovered in Step 0, call its CLI directly via Bash - never use WebSearch for
portal scraping.

1. Pick the priority categories to run: by default the top 3 from `search-queries.md`; all
   categories if the user said "broad"; the matching category (plus 2-3 custom queries) if the
   user gave a focus area.
2. For each selected category, take its query strings and strip the `site:<domain>` prefix and
   any bare location tokens (e.g. `Copenhagen`, `OR [YOUR_REGION]`) to recover the core
   keyword/title phrase. Example: `site:jobindex.dk "Software Engineer" OR "ML Engineer"
   Copenhagen` becomes the keyword phrase `software engineer OR ML engineer`.
3. For each discovered portal, run its `search` command with that keyword phrase via the flag
   noted in Step 0, plus the portal's own location mechanism, sourced from the candidate's
   location filter in `search-queries.md`. Examples: `--location 2` for Storkøbenhavn on
   `jobbank-search`; `--region HovedstadenOgBornholm` on `jobnet-search`; `--municipality
   "København"` on `jobdanmark-search`; `-l "Copenhagen, Capital Region, Denmark"` on
   `linkedin-search`; city folded directly into `--query` on `jobindex-search` (its API has no
   location parameter). Use `--jobage 14` (or the portal's closest equivalent) to bias toward
   recent postings.
4. Record, per portal: which categories were run, which location(s) were passed, how many raw
   results came back, and whether the call errored (non-zero exit, rate limit, timeout). This
   record feeds the Portal Coverage table in Step 5.
5. Sites listed in `search-queries.md` with no discovered CLI match are not queried at all - no
   WebSearch fallback. Record them as uncovered for the Step 5 report.

### Step 2: Fetch & Parse

For each promising result from Step 1:
- Use `WebFetch` to retrieve the job posting page
- Extract: **job title**, **company**, **location**, **posting date** (or "recent"), **URL**, **key requirements** (brief), **application deadline** (if listed)
- Skip if the URL or company+title combo already exists in `seen_jobs.json`
- Skip if the company+role already appears in `job_search_tracker.csv`

### Step 3: Quick Fit Assessment

For each new job, do a rapid fit check (NOT the full evaluation from `04-job-evaluation.md` - just a quick signal):

- **High match**: Role directly involves your core skills
- **Medium match**: Role is adjacent to your experience
- **Low match**: Role requires significant skills you lack

### Step 4: Deduplicate & Store

1. Add ALL fetched jobs (new and skipped) to `seen_jobs.json` with structure:
```json
{
  "seen": {
    "<url_or_company_title_key>": {
      "title": "...",
      "company": "...",
      "url": "...",
      "first_seen": "YYYY-MM-DD",
      "fit": "high/medium/low",
      "status": "new/skipped/evaluated/ranked/expired"
    }
  }
}
```
2. Only present jobs NOT already in the seen list or tracker.

### Step 5: Present Results

Present new jobs in a table sorted by fit (high first):

```
## New Job Matches - YYYY-MM-DD

Found X new positions (Y high, Z medium, W low match).

| # | Fit | Title | Company | Location | Deadline | URL |
|---|-----|-------|---------|----------|----------|-----|
| 1 | High | ... | ... | ... | ... | [Link](...) |

### High-Match Highlights
For each high-match job, add 2-3 bullet points:
- Why it matches your profile
- Key requirements to check
- Any red flags
```

After presenting, ask:
> "Want me to evaluate any of these in detail? Just give me the number(s)."

If the user picks a number, invoke the **job-application-assistant** skill workflow (fit evaluation first, then CV + cover letter if approved).

If the run found many new jobs (roughly 8+), also suggest `/rank` - it batch-scores all new postings against the full fit framework and returns a ranked shortlist, which beats eyeballing a long table. (`/rank` sets the `ranked` and `expired` status values in `seen_jobs.json`; treat both as already-seen for dedup purposes.)

### Step 6: Update Tracker (Optional)

If the user decides to apply to any job, add a row to `job_search_tracker.csv`.

---

## Important Rules

1. **Never fabricate job postings.** Only present jobs found via actual WebSearch/WebFetch results.
2. **Respect deduplication.** Always check seen_jobs.json AND job_search_tracker.csv before presenting.
3. **Focus on configured geographic area.** Skip jobs that require relocation or are clearly outside commute range.
4. **Only open positions.** Skip postings with expired deadlines or those marked as closed.
5. **Be efficient with WebFetch.** Don't fetch every search result - use titles and snippets to pre-filter before fetching.
6. **Parallel searches.** Use the Agent tool or parallel WebSearch calls to speed up the search phase.
