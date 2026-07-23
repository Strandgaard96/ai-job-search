---
name: arbeidsplassen-search
version: 1.0.0
description: >
  Search live job listings on arbeidsplassen.nav.no, NAV's official Norwegian public
  job bank, for any role or Norwegian location (Oslo, Bergen, Trondheim, Stavanger,
  remote, etc.). No authentication, zero runtime dependencies. Trigger phrases:
  Norwegian jobs, jobs in Norway, jobs in Oslo, arbeidsplassen, NAV jobs, ledige
  stillinger, jobbsøk, søk jobb, finn jobb, stillingsannonse, norske jobber.
context: fork
allowed-tools: Bash(bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts *)
---

# Arbeidsplassen (NAV) Search Skill

Search live job listings from **arbeidsplassen.nav.no**, NAV's official Norwegian public job
bank, covering the whole Norwegian market. No authentication, no API key, and **zero runtime
dependencies** — it runs with just `bun`.

`robots.txt` (`Disallow:` empty, all paths allowed) permits crawling this site; no personal-use
warning is required here (contrast with `linkedin-search`, which does carry one).

## When to use this skill

- Search for job openings anywhere in Norway (city, county, or remote)
- Filter by recency (posted within the last N days) or by county
- Get the full description, employer, deadline, and apply link for a specific listing

## Commands

### Search job listings

```bash
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keyword search (title, skill, role). Recommended.
- `--county <code>` — NAV county code. **Verified working:** `OSLO`, `VESTLAND`. If a code
  doesn't filter as expected, fold the city into `--query` instead (e.g. `-q "utvikler bergen"`)
  — the same fallback `jobindex-search` uses for its Danish equivalent.
- `--jobage <days>` — posted within N days. No server-side date param exists for this portal;
  filtered client-side against each result's parsed published date. Omit for all postings.
- `--page <n>` — page number (1-indexed, 25 results per page, fixed).
- `--limit <n>` / `-n <n>` — cap total results emitted (client-side).
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts detail <uuid|url> [--format json|plain]
```

`uuid` is the job ID from `search` results, or pass a full `/stillinger/stilling/<uuid>` URL.
Returns the full description, employer, sector, employment type, position count, deadline
(exact date, not the search card's year-less text), work languages, and apply link.

## Usage examples

```bash
# Software engineer roles in Oslo
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts search -q "software engineer" --county OSLO --format table

# ML/data roles, last 14 days, any location
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts search -q "maskinlæring" --jobage 14 --format table

# City folded into the query (reliable fallback when a county code is unverified)
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts search -q "data engineer bergen" --format table

# Cloud/DevOps roles in Trondheim
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts search -q "cloud engineer trondheim" --format table

# Full detail for a specific job
bun run .agents/skills/arbeidsplassen-search/cli/src/cli.ts detail 825d5dc5-c362-4d3c-8155-b36c6d6e016a --format plain
```

## Output formats

| Format | Best for |
|--------|----------|
| `json` | Default — programmatic use, passing ids to `detail` |
| `table` | Quick human-readable scanning |
| `plain` | Reading a single job's full detail (`detail` command) |

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- Data source: arbeidsplassen.nav.no's public, server-rendered search and detail pages. No
  credentials required; `robots.txt` permits automated access.
- Search results are parsed from HTML (`<article aria-label="Title, Employer, Location">` cards)
  — no public JSON search API is exposed. NAV's official structured feed API exists but requires
  a bearer token requested by email, so it isn't a zero-setup option; see `url-reference.md`.
- `detail` decodes the job's data from the page's embedded Next.js RSC streaming payload rather
  than scraping rendered markup — see `url-reference.md` for exactly how that's structured.
- Page size is fixed at 25 results per page; pagination uses an offset (`from`), not a page number.
- The `--county` filter has only been spot-verified for two codes; treat others as unconfirmed
  until tested, and prefer folding the city into `--query` when in doubt.
