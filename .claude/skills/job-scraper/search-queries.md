# Search Queries for Job Scraper

<!-- SETUP: Customize these queries based on your skills, target roles, and location -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Shipped country-agnostic CLIs include `linkedin-search` and `freehire-search`; Danish demos and any skill you add with `/add-portal` are included the same way. You do **not** need a matching `site:` line below for those CLIs to run.

The `site:` query templates in this file are the **WebSearch fallback** — for portals without a CLI, company career pages, or when a CLI fails.

## Search Sites

Primary (your market's job boards - scaffold one with `/add-portal`):
- **[YOUR_JOB_BOARD]** - your market's largest general job board
- **linkedin.com/jobs** - LinkedIn job listings (filter: [YOUR_COUNTRY] / [YOUR_CITY]); also covered by `linkedin-search` CLI
- **[YOUR_INDUSTRY_JOB_BOARD]** - a niche/industry board for your field (optional)
- **[YOUR_ADDITIONAL_JOB_BOARD]** - another major board for your market (optional)

Primary (Norwegian job market - Oslo is an equal-tier location, see Location Filter):
- **arbeidsplassen.nav.no** - NAV's official Norwegian public job bank (`arbeidsplassen-search` CLI)

Primary (Swiss job market - Basel and Zurich are in-scope relocation targets, see Location Filter):
- No dedicated CLI; covered by `linkedin-search` (`-l "Basel, Switzerland"` / `-l "Zurich, Switzerland"`) and
  `freehire-search` (`--country CH`). Basel is the pharma / drug-discovery hub, so Priority 2 queries
  (computational chemistry, cheminformatics, CADD) hit hardest there.

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for known target companies

## Query Categories

Queries are grouped by priority. Each query should be combined with your location terms (e.g. your city, region, or metro area) where the site supports it.

**Sector gate (applies to every category below):** a software/ML/data-engineering role only
counts as a match if the employer's core business is green energy, healthcare, or computational
chemistry / scientific ML. Generic tech/IT companies, IT consultancies/staffing/outsourcing,
financial-IT, and insurance are excluded regardless of how well the tech stack matches - see
Sector Filter below. Don't run bare "Software Engineer Copenhagen"-style queries with no sector
qualifier; they mostly surface exactly these excluded employers.

### Priority 1: Software / ML Engineering in Green Energy or Healthcare

Tech-stack match paired with a mission sector - your strongest and most desired direction.

```
site:jobindex.dk "Software Engineer" OR "ML Engineer" OR "Data Engineer" energy OR renewable OR wind OR solar Copenhagen
site:jobindex.dk "Software Engineer" OR "ML Engineer" OR "Data Scientist" healthcare OR hospital OR pharma OR biotech Copenhagen
site:linkedin.com/jobs "Software Engineer" OR "Machine Learning Engineer" energy OR healthcare Denmark
```

### Priority 2: Computational Chemistry / Scientific ML

These match your PhD domain expertise.

```
site:jobindex.dk "Computational Chemist" OR "Cheminformatics" Copenhagen OR Sjælland
site:jobindex.dk "Research Scientist" cheminformatics OR "molecular design" Denmark
site:linkedin.com/jobs cheminformatics OR "computational chemistry" Copenhagen Denmark
```

### Priority 3: Applied / Research Scientist (Adjacent)

Adjacent roles bridging the two directions above.

```
site:jobindex.dk "Applied Scientist" OR "Research Scientist" Python OR PyTorch Copenhagen
site:jobindex.dk "Machine Learning" chemistry OR materials OR "drug discovery" Copenhagen
```

### Priority 4: Broader Technical Roles in Mission Sectors

Wider net, but still gated to green energy, healthcare, or scientific ML employers - not a
general-IT catch-all.

```
site:jobindex.dk Python developer energy OR renewable OR healthcare OR pharma Copenhagen
site:linkedin.com/jobs "Python developer" OR "cloud engineer" energy OR healthcare Denmark
site:jobindex.dk "cloud engineer" OR "DevOps" wind OR "energy transition" Copenhagen
```

### Norway (arbeidsplassen.nav.no)

Since Oslo is an equal-tier location, run the same sector-gated categories against
`arbeidsplassen-search` with Norwegian-language keyword variants (its `--query` matches loosely,
so English titles often work too):

```
arbeidsplassen-search: "software engineer" OR "data engineer" OR "maskinlæring" --county OSLO
arbeidsplassen-search: "cheminformatics" OR "computational chemist" OR "molekylær" --county OSLO
```

Use `--county OSLO` (verified filter). If a role's location doesn't show as expected, fold the
city into `--query` instead (e.g. `-q "utvikler bergen"`) per that skill's own notes.

## Location Filter

When evaluating results, verify the job location is within reasonable commute distance from home, or in the accepted secondary city. Define acceptable areas:
- Copenhagen and surrounding areas (ideal)
- Oslo, Norway (ideal - candidate treats this as equal to Copenhagen)
- Rest of Sjælland / Hovedstaden region (acceptable, longer commute)
- Basel and Zurich, Switzerland (in scope as relocation targets - score fit normally, flag the relocation)
- Rest of Denmark or Norway outside these areas (borderline - discuss remote/relocation feasibility with candidate)
- Elsewhere outside Denmark/Norway/Switzerland, or roles requiring frequent international travel (too far / deal-breaker)

## Sector Filter

A software/ML/data-engineering role is only a match if the employer's core business is:
- Green energy transition
- Healthcare
- Computational chemistry / scientific ML (cheminformatics, drug discovery, materials science, energy storage)

Exclude regardless of tech-stack match:
- Insurance sector
- Pure IT sector: generic enterprise software, IT consulting/staffing/outsourcing, financial-IT,
  or any software/ML role at a company with no tie to a sector above

Computational chemistry / scientific ML roles (Priority 2 and 3) are always in scope - the sector
gate above applies to general software/ML/data-engineering roles (Priority 1 and 4), not to
domain-expertise roles.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
