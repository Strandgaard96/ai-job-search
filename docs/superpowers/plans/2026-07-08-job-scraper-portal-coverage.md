# job-scraper Portal Discovery + Coverage Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/scrape` (the `job-scraper` skill) discover and call the installed portal CLIs directly instead of generic WebSearch, and report exactly which portals/locations were searched vs skipped on every run.

**Architecture:** `job-scraper` is a single markdown skill file (`.claude/skills/job-scraper/SKILL.md`) that an LLM reads and follows step-by-step — there is no application code to compile. "Implementation" here means precisely rewriting three sections of that file (Step 0, Step 1, Step 5) plus its frontmatter, so that a future run of the skill discovers portals via `Glob`, derives per-portal queries from the existing `search-queries.md` categories, calls each portal's CLI via `Bash`, and prints a coverage table before the results table. "Tests" are manual verification passes (Bash smoke commands + one live `/scrape` run), since the deliverable is agent instructions, not executable code.

**Tech Stack:** Markdown skill file, Bash (to invoke `bun run .agents/skills/<name>/cli/src/cli.ts ...`), Glob.

## Global Constraints

- No WebSearch fallback for portals without a dedicated CLI (karriere.dk, jobfinder.dk, akademikernes.dk) — they are reported as uncovered, never scraped via WebSearch.
- Portal roster must be discovered dynamically via `Glob(".agents/skills/*/SKILL.md")` at run time — never hardcoded in `job-scraper`'s own `SKILL.md`.
- `search-queries.md` is read-only in this change — no reformatting, no new Oslo category, no content edits.
- "Locations queried" in the coverage report must reflect what was actually passed that run, not a fixed/aspirational list.
- A portal call that errors (rate limit, timeout, non-zero exit) must show as `Error` with a short reason in the coverage report — never silently dropped or conflated with `Searched`.

---

### Task 1: Frontmatter tool access + Step 0 portal discovery

**Files:**
- Modify: `.claude/skills/job-scraper/SKILL.md:1-7` (frontmatter), `:33-37` (Step 0)

**Interfaces:**
- Produces: a documented "portal discovery" procedure (Glob-based) that Task 2 and Task 3 refer to as "the roster from Step 0".

- [ ] **Step 1: Edit the frontmatter to add `Bash` and drop `WebSearch`**

Old:
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Agent, AskUserQuestion
```

New:
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Agent, AskUserQuestion
```

Use the Edit tool on `.claude/skills/job-scraper/SKILL.md` with `old_string` set to the line above (as it appears in the file, including the `allowed-tools:` prefix) and `new_string` set to the replacement line.

- [ ] **Step 2: Rewrite Step 0 to add portal discovery**

Old:
```markdown
### Step 0: Load State

1. Read `job_scraper/seen_jobs.json` (create if missing - start with `{"seen": {}}`)
2. Read `job_search_tracker.csv` to extract already-applied companies+roles
3. Read `search-queries.md` (this directory) for the search strategy
```

New:
```markdown
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
```

Use the Edit tool with the full old block as `old_string` and the full new block as `new_string`.

- [ ] **Step 3: Verify the discovery mechanism structurally**

Run:
```bash
find .agents/skills -maxdepth 1 -type d -name "*-search"
```
Expected output (order may vary):
```
.agents/skills/jobbank-search
.agents/skills/jobdanmark-search
.agents/skills/jobindex-search
.agents/skills/jobnet-search
.agents/skills/linkedin-search
```

Then confirm each has a CLI entrypoint:
```bash
for d in .agents/skills/*-search; do test -f "$d/cli/src/cli.ts" && echo "OK: $d" || echo "MISSING cli.ts: $d"; done
```
Expected: `OK: <path>` for all 5 directories, no `MISSING` lines.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/job-scraper/SKILL.md
git commit -m "$(cat <<'EOF'
feat(job-scraper): discover portal CLIs dynamically in Step 0

Replaces the implicit assumption that job-scraper only knows about
WebSearch with an explicit Glob-based discovery of installed
*-search portal CLIs, so newly added portals (e.g. via /add-portal)
are picked up automatically without editing this file again.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Step 1 rewrite — per-portal query derivation and CLI calls

**Files:**
- Modify: `.claude/skills/job-scraper/SKILL.md:39-48` (Step 1, post-Task-1 line numbers will have shifted — locate by the `### Step 1: Search` heading)

**Interfaces:**
- Consumes: the portal roster and per-portal flag notes produced by Task 1's Step 0 rewrite.
- Produces: a per-run "coverage record" (which categories ran, which locations were passed per
  portal, raw result counts, error status) that Task 3's Step 5 rewrite reads to fill the Portal
  Coverage table. This record is described in prose (it's an LLM's working notes for the run, not
  a file), so Task 3 refers to it by the same name used here: "the record from Step 1".

- [ ] **Step 1: Rewrite the Step 1 section**

Old:
```markdown
### Step 1: Search

Run **WebSearch** queries from `search-queries.md`. By default, run the top 3 priority categories. If the user said "broad", run all categories.

If the user specified a focus area (e.g. "data science"), prioritize queries from that category.

For each search:
- Use `WebSearch` with site-specific queries (jobindex.dk, linkedin.com/jobs, karriere.dk, etc.)
- Target your configured geographic area
- Look for postings from the last 14 days
```

New:
```markdown
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
```

Use the Edit tool with the full old block as `old_string` and the full new block as `new_string`.

- [ ] **Step 2: Verify one derived query actually runs against a real portal**

Run a manual smoke test reproducing what Step 1 now describes, using the "Priority 1" category
from `search-queries.md` (`site:jobindex.dk "Software Engineer" OR "ML Engineer" OR "Data
Scientist" Copenhagen`) against `jobindex-search`:

```bash
bun run .agents/skills/jobindex-search/cli/src/cli.ts search --query "software engineer" --jobage 14 --sort date --format table
```
Expected: exit code 0, a table with an `id`/`title`/`company`/`location` header row (result
content will vary run to run — this only confirms the derived call is well-formed and the CLI
responds).

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/job-scraper/SKILL.md
git commit -m "$(cat <<'EOF'
feat(job-scraper): derive per-portal queries from search-queries.md categories

Step 1 now strips the site:/location boilerplate from each priority
category's query strings and calls the discovered portal CLIs
directly (jobindex-search, jobbank-search, jobdanmark-search,
jobnet-search, linkedin-search) instead of generic WebSearch, which
was returning stale/archived results. Sites with no CLI are no
longer WebSearched as a fallback.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Step 5 Portal Coverage table + Important Rules update

**Files:**
- Modify: `.claude/skills/job-scraper/SKILL.md` — the `### Step 5: Present Results` section
  (originally lines 85-103) and the `## Important Rules` section (originally lines 118-125);
  locate both by heading since line numbers shifted after Tasks 1-2.

**Interfaces:**
- Consumes: "the record from Step 1" (per-portal categories/locations/result-counts/errors) and
  the list of no-CLI sites recorded in Step 1.

- [ ] **Step 1: Insert the Portal Coverage table at the start of Step 5**

Old:
```markdown
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
```

New:
```markdown
### Step 5: Present Results

First, print the Portal Coverage table from the record kept in Step 1:

```
### Portal Coverage
| Portal | Status | Locations queried |
|--------|--------|--------------------|
| jobindex-search | Searched | Denmark-wide (city in query) |
| jobbank-search | Searched | Storkøbenhavn |
| jobdanmark-search | Searched | København |
| jobnet-search | Searched | Hovedstaden og Bornholm |
| linkedin-search | Searched | Copenhagen |
| karriere.dk | Not searched | no CLI installed - /add-portal or paste posting into /apply |
| jobfinder.dk | Not searched | no CLI installed |
| akademikernes.dk | Not searched | no CLI installed |
```

Fill this table from what actually happened this run - a portal with an error shows `Error` with
a short reason (e.g. "rate limited, backed off") instead of `Searched`, and is never silently
dropped from the table. A portal skipped because the user picked a narrow focus area still gets a
row, showing which categories were and weren't run. "Locations queried" always reflects what was
actually passed this run, not every location the portal could support.

Then present new jobs in a table sorted by fit (high first):

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
```

Use the Edit tool with the full old block as `old_string` and the full new block as `new_string`.

- [ ] **Step 2: Update Important Rules 1 and 6**

Old:
```markdown
1. **Never fabricate job postings.** Only present jobs found via actual WebSearch/WebFetch results.
```

New:
```markdown
1. **Never fabricate job postings.** Only present jobs found via actual portal-CLI or WebFetch results.
```

Use the Edit tool with the old line as `old_string` and the new line as `new_string`.

Old:
```markdown
6. **Parallel searches.** Use the Agent tool or parallel WebSearch calls to speed up the search phase.
```

New:
```markdown
6. **Parallel searches.** Run multiple portal CLI calls in parallel (several Bash calls in one turn) to speed up the search phase.
```

Use the Edit tool with the old line as `old_string` and the new line as `new_string`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/job-scraper/SKILL.md
git commit -m "$(cat <<'EOF'
feat(job-scraper): add Portal Coverage table to Step 5, update rules

Every /scrape run now prints which portals were searched (with
locations) and which had no CLI installed, before the job-matches
table. Important Rules 1 and 6 updated to reflect CLI-based search
instead of WebSearch.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: End-to-end verification

**Files:**
- None (verification only — no file changes).

- [ ] **Step 1: Confirm the fully-edited file reads correctly end to end**

Run:
```bash
cat -n .claude/skills/job-scraper/SKILL.md
```
Expected: a single coherent document — frontmatter with `Bash` present and `WebSearch` absent;
Step 0 ending with the portal-discovery sub-steps; Step 1 describing per-portal CLI calls with no
mention of WebSearch; Step 5 starting with the Portal Coverage table before the job-matches
table; Important Rules 1 and 6 matching the text from Task 3.

- [ ] **Step 2: Confirm no stale WebSearch references remain**

Run:
```bash
grep -n "WebSearch" .claude/skills/job-scraper/SKILL.md
```
Expected: no output (exit code 1 / no matches).

- [ ] **Step 3: Simulate a portal going missing**

```bash
mv .agents/skills/jobnet-search .agents/skills/jobnet-search.bak
find .agents/skills -maxdepth 1 -type d -name "*-search"
```
Expected: only 4 directories listed (`jobbank-search`, `jobdanmark-search`, `jobindex-search`,
`linkedin-search`) — confirms the discovery mechanism (Task 1, Step 3's `find` command) naturally
drops a portal that's been removed, without needing any change to `job-scraper`'s own file.

Restore it:
```bash
mv .agents/skills/jobnet-search.bak .agents/skills/jobnet-search
find .agents/skills -maxdepth 1 -type d -name "*-search"
```
Expected: all 5 directories listed again.

- [ ] **Step 4: Live dry run**

Invoke `/scrape data science` in a Claude Code session against this repo and confirm:
- The response opens with (or includes early) a `### Portal Coverage` table listing all 5
  installed CLIs as `Searched` with a real location value each, and `karriere.dk`, `jobfinder.dk`,
  `akademikernes.dk` as `Not searched — no CLI installed`.
- No WebSearch tool calls appear in the transcript for this run.
- The job-matches table (if any new postings found) appears after the coverage table, unchanged
  in format from before this change.

This step has no shell command — it's a manual read of the actual skill invocation's output
against the criteria above.

- [ ] **Step 5: Commit (if Step 4 required any fixes)**

If Step 4 surfaced any wording or logic issue, fix it with the Edit tool and commit:
```bash
git add .claude/skills/job-scraper/SKILL.md
git commit -m "$(cat <<'EOF'
fix(job-scraper): correct portal-coverage wording found in dry run

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```
If Step 4 required no fixes, skip this commit — there is nothing to commit.
