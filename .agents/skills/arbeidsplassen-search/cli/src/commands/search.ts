import { SEARCH_URL, htmlFetch, parseJobCards, writeError, type JobCard } from "../helpers.js"

export interface SearchOpts {
  query?: string
  county?: string
  jobage: number
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

const PAGE_SIZE = 25

function buildUrl(opts: SearchOpts): string {
  const params = new URLSearchParams()
  if (opts.query) params.set("q", opts.query)
  if (opts.county) params.set("county", opts.county)
  const from = (opts.page - 1) * PAGE_SIZE
  if (from > 0) params.set("from", String(from))
  return `${SEARCH_URL}?${params.toString()}`
}

/** Client-side posting-age filter: the portal has no server-side date-range param. */
function filterByAge(cards: JobCard[], days: number): JobCard[] {
  if (!days || days <= 0 || days >= 9999) return cards
  const cutoff = Date.now() - days * 86400 * 1000
  return cards.filter((c) => {
    if (!c.date) return true // keep undated cards rather than silently dropping them
    return new Date(c.date).getTime() >= cutoff
  })
}

function renderTable(cards: JobCard[]): string {
  if (cards.length === 0) return "No results."
  const rows = cards.map((c) => {
    const title = (c.title || "").slice(0, 42).padEnd(42)
    const company = (c.company || "—").slice(0, 26).padEnd(26)
    const loc = (c.location || "—").slice(0, 20).padEnd(20)
    const date = c.date || "—"
    return `${c.id.slice(0, 8).padEnd(9)} ${title} ${company} ${loc} ${date}`
  })
  const header =
    "ID".padEnd(9) + " " + "TITLE".padEnd(42) + " " + "COMPANY".padEnd(26) + " " + "LOCATION".padEnd(20) + " DATE"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const html = await htmlFetch(buildUrl(opts))
    let cards = parseJobCards(html)
    cards = filterByAge(cards, opts.jobage)
    if (opts.limit && opts.limit > 0) cards = cards.slice(0, opts.limit)

    if (opts.format === "table") {
      process.stdout.write(renderTable(cards) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        cards
          .map((c) => `${c.title}\n  ${c.company || "—"} · ${c.location || "—"} · ${c.date || "—"}\n  id: ${c.id}\n  ${c.url}`)
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(JSON.stringify({ meta: { count: cards.length, page: opts.page }, results: cards }, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
