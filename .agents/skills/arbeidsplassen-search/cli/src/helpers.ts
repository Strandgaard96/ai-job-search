// Data source: arbeidsplassen.nav.no (NAV's official Norwegian public job bank).
// robots.txt allows all crawling (no Disallow rules). No authentication required
// for the public search/detail pages we use here.
//
// Search results are server-rendered HTML: each result is an <article aria-label
// ="Title, Employer, Location"> card linking to /stillinger/stilling/<uuid>. We
// parse that directly — no JSON search API is exposed publicly (NAV's structured
// feed API requires a bearer token; see url-reference.md).
//
// Detail pages embed a full structured job object (id, employer, location list,
// application deadline, description HTML, ...) inside a Next.js RSC streaming
// payload (`self.__next_f.push([1, "..."])` script tags). We decode those pushes
// and extract the `adData` JSON object plus its out-of-line description-HTML
// chunk — far more reliable than scraping the rendered detail-page markup.

export const SEARCH_URL = "https://arbeidsplassen.nav.no/stillinger"
export const DETAIL_BASE_URL = "https://arbeidsplassen.nav.no/stillinger/stilling"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

/** Fetch HTML with exponential backoff on 429/5xx. Returns "" on a 404. */
export async function htmlFetch(url: string): Promise<string> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "nb-NO,nb;q=0.9,en;q=0.8",
      },
      redirect: "follow",
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`)
      }
      const jitter = Math.floor(Math.random() * 500)
      await new Promise((r) => setTimeout(r, delay + jitter))
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (response.status === 404) return ""
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.text()
  }
  throw new Error("Request failed after max retries")
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
}

export interface JobDetail extends JobCard {
  description: string | null
  employmentType: string | null
  positionCount: number | null
  deadline: string | null
  workLanguages: string | null
  sector: string | null
  applyUrl: string | null
}

function numericEntity(cp: number): string {
  return cp >= 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : ""
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, dec) => numericEntity(parseInt(dec, 10)))
    .replace(/&#[xX]([0-9a-fA-F]+);/g, (_, hex) => numericEntity(parseInt(hex, 16)))
    .replace(/&nbsp;/g, " ")
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
}

const NB_MONTHS: Record<string, number> = {
  januar: 0, februar: 1, mars: 2, april: 3, mai: 4, juni: 5,
  juli: 6, august: 7, september: 8, oktober: 9, november: 10, desember: 11,
}

/** Parse a Norwegian long date like "29. juni 2026" into an ISO date string. */
export function parseNorwegianDate(text: string | null): string | null {
  if (!text) return null
  const m = text.match(/(\d{1,2})\.\s*([a-zæøå]+)\s*(\d{4})/i)
  if (!m) return null
  const month = NB_MONTHS[m[2].toLowerCase()]
  if (month === undefined) return null
  const d = new Date(Date.UTC(parseInt(m[3], 10), month, parseInt(m[1], 10)))
  return d.toISOString().slice(0, 10)
}

/**
 * Parse the search-results page: each real job card is an <article aria-label=
 * "Title, Employer, Location"> that links to /stillinger/stilling/<uuid>. Facet
 * chips ("X (Kategori)") also render as <article> but never contain that link,
 * so we split on "<article" and skip any chunk without the job-detail href —
 * one malformed/unexpected chunk cannot break the rest.
 */
export function parseJobCards(html: string): JobCard[] {
  const results: JobCard[] = []
  const chunks = html.split("<article").slice(1)

  for (const chunk of chunks) {
    const hrefMatch = chunk.match(/href="\/stillinger\/stilling\/([a-f0-9-]+)"/i)
    if (!hrefMatch) continue
    const id = hrefMatch[1]

    const ariaMatch = chunk.match(/^\s*aria-label="([^"]+)"/i)
    if (!ariaMatch) continue
    const parts = decodeHtmlEntities(ariaMatch[1]).split(", ")
    if (parts.length < 2) continue
    const location = parts.pop() || null
    const company = parts.length > 0 ? parts.pop() || null : null
    const title = parts.join(", ") || null
    if (!title) continue

    const dateMatch = chunk.match(/(\d{1,2}\.\s*[a-zæøå]+\s*\d{4})/i)
    const date = dateMatch ? parseNorwegianDate(dateMatch[1]) : null

    results.push({
      id,
      title,
      company,
      location: location === "" ? null : location,
      date,
      url: `${DETAIL_BASE_URL}/${id}`,
    })
  }

  return results
}

/**
 * Decode every `self.__next_f.push([1, "..."])` RSC chunk in a Next.js-rendered
 * page into its real string content, in document order. Each push argument is
 * a JSON-escaped JS string literal (not raw HTML), so we scan for the matching
 * unescaped closing quote and let JSON.parse do entity/escape decoding.
 */
function extractRscChunks(html: string): string[] {
  const chunks: string[] = []
  const marker = 'self.__next_f.push([1,"'
  let pos = 0
  while (true) {
    const start = html.indexOf(marker, pos)
    if (start === -1) break
    let i = start + marker.length
    let escaped = false
    while (i < html.length) {
      const ch = html[i]
      if (escaped) {
        escaped = false
      } else if (ch === "\\") {
        escaped = true
      } else if (ch === '"') {
        break
      }
      i++
    }
    const raw = html.slice(start + marker.length, i)
    try {
      chunks.push(JSON.parse(`"${raw}"`))
    } catch {
      // Skip a chunk we can't decode rather than aborting the whole parse.
    }
    pos = i + 1
  }
  return chunks
}

/** Extract the balanced-brace JSON object following `"key":` in `text`. */
function extractBalancedObject(text: string, key: string): string | null {
  const needle = `"${key}":`
  const at = text.indexOf(needle)
  if (at === -1) return null
  const start = text.indexOf("{", at)
  if (start === -1) return null
  let depth = 0
  let inString = false
  let escaped = false
  for (let i = start; i < text.length; i++) {
    const ch = text[i]
    if (inString) {
      if (escaped) escaped = false
      else if (ch === "\\") escaped = true
      else if (ch === '"') inString = false
      continue
    }
    if (ch === '"') inString = true
    else if (ch === "{") depth++
    else if (ch === "}") {
      depth--
      if (depth === 0) return text.slice(start, i + 1)
    }
  }
  return null
}

interface AdData {
  id: string
  title: string
  engagementType: string | null
  positionCount: number | null
  extent: string[] | null
  workLanguages: string[] | null
  published: string | null
  expires: string | null
  adTextHtml: string | null
  application?: { applicationDueDate: string | null; applicationUrl: string | null }
  employer?: { name: string | null; sector: string | null }
  locationList?: Array<{ city: string | null; municipal: string | null; county: string | null }>
}

/** Parse a job detail page by decoding its embedded Next.js RSC `adData` payload. */
export function parseJobDetail(html: string, id: string): JobDetail | null {
  const chunks = extractRscChunks(html)
  const adDataChunk = chunks.find((c) => c.includes('"adData":{'))
  if (!adDataChunk) return null

  const adDataJson = extractBalancedObject(adDataChunk, "adData")
  if (!adDataJson) return null

  let adData: AdData
  try {
    adData = JSON.parse(adDataJson)
  } catch {
    return null
  }

  let description: string | null = null
  const ref = adData.adTextHtml
  if (ref && ref.startsWith("$")) {
    const chunkId = ref.slice(1)
    // The marker "{chunkId}:T{hexLength}," is typically a trailing line inside a
    // larger chunk (not a standalone one) — search as a substring, not a full match.
    const markerIdx = chunks.findIndex((c) => new RegExp(`${chunkId}:T[0-9a-f]+,`).test(c))
    const html2 = markerIdx !== -1 ? chunks[markerIdx + 1] : undefined
    if (html2) {
      const withBreaks = html2
        .replace(/<\s*br\s*\/?>/gi, "\n")
        .replace(/<\/(p|li|ul|ol|div|h\d)>/gi, "\n")
      description = decodeHtmlEntities(stripTags(withBreaks)).replace(/\n{3,}/g, "\n\n").trim() || null
    }
  } else if (ref) {
    description = decodeHtmlEntities(stripTags(ref)).trim() || null
  }

  const loc = adData.locationList?.[0]
  const location = loc ? [loc.city, loc.municipal].filter((v, i, a) => v && a.indexOf(v) === i).join(", ") || null : null

  const employmentType = [adData.engagementType, ...(adData.extent || [])].filter(Boolean).join(", ") || null

  return {
    id,
    title: adData.title || "(untitled)",
    company: adData.employer?.name ?? null,
    location,
    date: adData.published ? adData.published.slice(0, 10) : null,
    url: `${DETAIL_BASE_URL}/${id}`,
    description,
    employmentType,
    positionCount: adData.positionCount ?? null,
    deadline: adData.application?.applicationDueDate?.slice(0, 10) ?? null,
    workLanguages: adData.workLanguages?.join(", ") ?? null,
    sector: adData.employer?.sector ?? null,
    applyUrl: adData.application?.applicationUrl ?? null,
  }
}
