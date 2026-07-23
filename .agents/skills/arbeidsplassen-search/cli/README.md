# arbeidsplassen-cli

CLI for searching jobs on **arbeidsplassen.nav.no**, NAV's official Norwegian public job bank.

**Data source**: arbeidsplassen.nav.no server-rendered search results + embedded job-detail data.
**Authentication**: None required. `robots.txt` permits crawling (no Disallow rules).
**Dependencies**: None (plain `bun` + `fetch`). `bun install` is optional and only pulls dev type defs.

## Installation

```bash
cd .agents/skills/arbeidsplassen-search/cli
bun install   # optional — only installs TypeScript dev types
```

The CLI runs without any install because it has zero runtime dependencies.

## Commands

| Command | Description |
|---------|-------------|
| `search` | Search for job listings |
| `detail` | Fetch full detail for a single job listing |

`search` accepts `--format json|table|plain` (default `json`); `detail` accepts `--format json|plain`.
All errors are written to **stderr** as `{ "error": "...", "code": "..." }` with exit code `1`.

## Quick examples

```bash
# Software engineer roles in Oslo
bun run src/cli.ts search -q "software engineer" --county OSLO --format table

# ML roles, last 14 days
bun run src/cli.ts search -q "maskinlæring" --jobage 14 --format table

# City folded into the query (reliable fallback — see Notes)
bun run src/cli.ts search -q "data engineer bergen" --format table

# Full detail for one job
bun run src/cli.ts detail 825d5dc5-c362-4d3c-8155-b36c6d6e016a --format plain
```

See `../SKILL.md` for the full flag reference and portal notes.

## Search flags

| Flag | Alias | Description |
|------|-------|-------------|
| `--query` | `-q` | Keywords (title / skill / role). Recommended. |
| `--county` | | NAV county code, e.g. `OSLO`, `VESTLAND` (verified). Others may need testing — fold the city into `--query` instead if a code doesn't filter. |
| `--jobage` | | Posted within N days. Filtered client-side against each card's published date (no server-side date param exists). |
| `--page` | | 1-indexed page (25 results/page). |
| `--limit` | `-n` | Cap results emitted. |
| `--format` | | `json` \| `table` \| `plain`. |

## Notes

- `search` parses server-rendered HTML result cards (`<article aria-label="Title, Employer, Location">`).
- `detail` decodes the Next.js RSC streaming payload embedded in the detail page to get
  structured fields (employer, location, deadline, description) rather than scraping rendered markup.
- The `--county` filter is confirmed working for `OSLO` and `VESTLAND`; NAV's other county-code
  spellings (post-2024 county reorganization) haven't all been verified live.
