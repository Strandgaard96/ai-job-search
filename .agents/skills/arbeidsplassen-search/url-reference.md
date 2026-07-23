# arbeidsplassen.nav.no — URL & Parsing Reference

## Access

- `robots.txt` (https://arbeidsplassen.nav.no/robots.txt): `User-agent: * / Disallow:` — no
  restrictions on any path. Crawling is explicitly permitted.
- No authentication required for the public search/detail pages used here.
- NAV also publishes an official structured feed API (`pam-stilling-feed`, successor to the
  deprecated `pam-public-feed`), but it requires a bearer token obtained by emailing
  `plattform.for.arbeidsmarkedet@nav.no` — not a zero-setup public API, so this skill scrapes
  the public frontend instead, which needs no credentials at all.

## Search

```
GET https://arbeidsplassen.nav.no/stillinger?q=<query>&county=<code>&from=<offset>
```

- `q` — free-text keyword query. Matches title/description loosely (not strict boolean).
- `county` — confirmed working as a real server-side filter (verified: `q=software engineer` is
  119 hits with no county param, 42 with `county=OSLO`, 16 with `county=VESTLAND`). Tried
  `location=<city>` and `municipal=<city>` params — both silently ignored (no effect on hit
  count), so `location`/`municipal` are **not** real filter params despite intuitive naming.
  Other county codes (post-2024 Norwegian county reorganization) were not exhaustively verified
  — `TRONDELAG` returned 0 hits, so the correct spelling for that county is unconfirmed.
- `from` — pagination offset. Page size is a **fixed 25 results**; `size`/`page` params tested
  and had no effect. `from=25` returns a genuinely different result set from `from=0`.
- No server-side posting-age/date-range param was found in the UI; `--jobage` in this skill is
  a client-side post-filter using each card's parsed published date.

### Result parsing

Results are plain server-rendered HTML (no JSON search API is exposed publicly). Each real job
card renders as:

```html
<article aria-label="Senior Software Engineer (Rust), Six Robotics, Oslo" ...>
  ...
  <p>19. februar 2026</p>            <!-- published date, "D. month YYYY" (Norwegian) -->
  <a href="/stillinger/stilling/{uuid}">Senior Software Engineer (Rust)</a>
  ...
  <p>Søk senest torsdag 30. juli</p>  <!-- deadline text, no year — often absent (rolling) -->
</article>
```

- `aria-label` on the `<article>` is `"{Title}, {Employer}, {Location}"` — split from the right
  (`.pop()` location, then employer, remainder joined back is the title) so a comma inside a
  title doesn't break the split.
- **Facet/category chips** (e.g. `aria-label="Museum, bibliotek, arkiv (Kategori)"`) also render
  as `<article>` and can superficially match the same comma-count, but never contain the
  `/stillinger/stilling/{uuid}` href — require that href as the real discriminator when chunking.
- Split the whole page on the literal string `<article` and treat each chunk independently, so
  one unexpected/malformed card can't break parsing of the rest.
- The uuid from the `href` is both the job's `id` and the path segment for the detail URL.

## Detail

```
GET https://arbeidsplassen.nav.no/stillinger/stilling/<uuid>
```

The rendered HTML body does **not** contain the full description as plain markup — it's a
Next.js App Router page streamed via React Server Components. The actual structured job object
and full description HTML are embedded in `<script>self.__next_f.push([1, "..."])</script>` tags
scattered through the page.

### Decoding the RSC stream

Each `push([1, "..."])` argument is a **JSON-escaped JS string literal** (produced by
`JSON.stringify` on the server), not raw HTML/JSON. To recover chunk N's real text:

1. Scan from `self.__next_f.push([1,"` to the next **unescaped** `"` (tracking `\` escapes so an
   escaped quote `\"` doesn't end the scan early).
2. `JSON.parse('"' + rawSlice + '"')` — this alone decodes all `\uXXXX`, `\"`, `\\`, `\n` etc.
   into the real characters, giving the chunk's actual content in document order.

### The `adData` object

One decoded chunk contains a call like `7:["$","$L1d",null,{"adData":{...}, ...}]`. Extract the
JSON object following the literal `"adData":` with a balanced-brace scan (respecting quoted
strings, since brace characters can appear inside string values) and `JSON.parse` just that
substring — it's clean, self-contained JSON. Fields used by this skill:

| Field | Notes |
|-------|-------|
| `id`, `title` | |
| `employer.name`, `employer.sector` | |
| `locationList[0].city` / `.municipal` / `.county` | Array — normally one entry |
| `published`, `expires` | ISO 8601 timestamps |
| `application.applicationDueDate` | ISO date, or absent for rolling/no-deadline postings |
| `application.applicationUrl` | External apply link (often a different ATS, e.g. jobbnorge.no) |
| `engagementType`, `extent[]` | e.g. `"Åremål"` + `["Heltid"]` → "fixed-term, full-time" |
| `positionCount` | |
| `workLanguages[]` | e.g. `["Norsk","Engelsk"]` |
| `adTextHtml` | **Not inline** — a reference like `"$2c"` pointing at another RSC chunk (see below) |

### Resolving `adTextHtml`

`adData.adTextHtml` holds a placeholder like `"$2c"` rather than the description itself. The
marker for the real HTML is a **trailing line inside an unrelated earlier chunk** (a JS-module
manifest chunk, in practice), not a standalone chunk of its own:

```
...2e:I[31967,[],"IconMark"]\n2c:T2bcf,     <!-- marker "{id}:T{hexLength}," ends some other chunk -->
```
```
<h2>Om stilllingen</h2><p>...</p>...        <!-- the very next chunk: the actual description HTML -->
```

Find the chunk whose *decoded* text **contains** `{id}:T[0-9a-f]+,` anywhere in it (where `{id}`
is the digits after `$` in `adTextHtml` — don't anchor the match to the whole chunk, it's
usually a suffix), then take the **next** decoded chunk in array order — that is the full
description HTML (already unescaped by the earlier `JSON.parse('"'+raw+'"')` step, e.g. `<`
→ `<`). Strip tags and decode remaining HTML entities as usual to get plain text.

## Quirks

- Norwegian long-date format (`"29. juni 2026"`) needs a small month-name lookup table; no
  built-in JS date parser handles Norwegian month names.
- The deadline text ("Søk senest ...") on search cards omits the year, so it can't be reliably
  parsed to an absolute date from the card alone — use `detail`'s `application.applicationDueDate`
  for an exact deadline.
- `adData.application` may be entirely absent for postings with no formal deadline (rolling
  applications) — treat as "rolling", not an error.
