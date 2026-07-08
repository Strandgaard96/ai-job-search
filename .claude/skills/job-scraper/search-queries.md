# Search Queries for Job Scraper

<!-- SETUP: Customize these queries based on your skills, target roles, and location -->

## Search Sites

Primary (Danish job market):
- **jobindex.dk** - largest Danish job board
- **linkedin.com/jobs** - LinkedIn job listings (filter: Denmark / your city)
- **karriere.dk** - IDA's job board (engineering/science roles)
- **jobfinder.dk** - another major Danish job board
- **akademikernes.dk** - academic union job board

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for known target companies

## Query Categories

Queries are grouped by priority. Each query should be combined with your location terms (e.g. "Copenhagen", "Sjælland", "Hovedstaden") where the site supports it.

### Priority 1: Software / ML Engineering

These match your strongest and most desired career direction.

```
site:jobindex.dk "Software Engineer" OR "ML Engineer" OR "Data Scientist" Copenhagen
site:jobindex.dk "Python" "Terraform" OR "AWS" Copenhagen
site:linkedin.com/jobs "Software Engineer" OR "Machine Learning Engineer" Denmark
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

### Priority 4: Broader Technical / Consulting

Wider net for general technical roles.

```
site:jobindex.dk Python developer Copenhagen
site:linkedin.com/jobs "Python developer" OR "cloud engineer" Copenhagen
site:jobindex.dk "technical consultant" Python OR cloud Copenhagen
```

## Location Filter

When evaluating results, verify the job location is within reasonable commute distance from home, or in the accepted secondary city. Define acceptable areas:
- Copenhagen and surrounding areas (ideal)
- Oslo, Norway (acceptable - candidate is open to this location)
- Rest of Sjælland / Hovedstaden region (acceptable, longer commute)
- Rest of Denmark or Norway outside these areas (borderline - discuss remote/relocation feasibility with candidate)
- Outside Denmark/Norway, or roles requiring frequent international travel (too far / deal-breaker)

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
