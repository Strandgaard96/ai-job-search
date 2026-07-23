# job-scraper Clickable URL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change `job-scraper`'s Step 5 results-table template so a job's URL is shown as its own link text, staying clickable in a normal terminal while also being copy-able as plain text when tmux copy-mode blocks clicking.

**Architecture:** One-line template edit in `.claude/skills/job-scraper/SKILL.md`. No code, no tests beyond a manual `/scrape` run.

**Tech Stack:** Markdown (skill instruction file only).

## Global Constraints

- Scope is `job-scraper`'s Step 5 table only. `/rank`'s shortlist table is explicitly out of scope for this change.
- No change to how URLs are fetched, stored in `seen_jobs.json`, or deduplicated — presentation-only.

---

### Task 1: Update the Step 5 table template

**Files:**
- Modify: `.claude/skills/job-scraper/SKILL.md:141-143`

**Interfaces:**
- Consumes: nothing (standalone doc edit).
- Produces: nothing consumed by other tasks — this plan has only one task.

- [ ] **Step 1: Make the edit**

Current text at `.claude/skills/job-scraper/SKILL.md:141-143`:

```
| # | Fit | Title | Company | Location | Deadline | URL |
|---|-----|-------|---------|----------|----------|-----|
| 1 | High | ... | ... | ... | ... | [Link](...) |
```

Replace the third line with:

```
| 1 | High | ... | ... | ... | ... | [https://example.com/job/...](https://example.com/job/...) |
```

So the full block reads:

```
| # | Fit | Title | Company | Location | Deadline | URL |
|---|-----|-------|---------|----------|----------|-----|
| 1 | High | ... | ... | ... | ... | [https://example.com/job/...](https://example.com/job/...) |
```

- [ ] **Step 2: Verify the edit landed correctly**

```bash
grep -n "example.com/job" .claude/skills/job-scraper/SKILL.md
```

Expected: one match, showing the new template line.

```bash
grep -n "\[Link\](" .claude/skills/job-scraper/SKILL.md
```

Expected: no matches (the old generic-anchor-text template is gone).

- [ ] **Step 3: Manual verification**

Run `/scrape` (or `/scrape <focus area>`) and confirm the presented results table shows each job's full URL as the visible link text — e.g. `[https://www.jobindex.dk/jobannonce/h1679626/...](https://www.jobindex.dk/jobannonce/h1679626/...)` rather than `[Link](...)`. Confirm clicking it still navigates correctly in a standard (non-tmux-copy-mode) terminal.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/job-scraper/SKILL.md
git commit -m "docs(job-scraper): show full URL as link text for tmux copy-mode"
```
