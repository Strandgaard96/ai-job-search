import { DETAIL_BASE_URL, htmlFetch, parseJobDetail, writeError } from "../helpers.js"

export interface DetailOpts {
  id: string
  format: "json" | "plain"
}

/** Accept a raw job UUID or a full /stillinger/stilling/<uuid> URL. */
function normalizeId(input: string): string | null {
  const url = input.match(/\/stillinger\/stilling\/([a-f0-9-]{36})/i)
  if (url) return url[1]
  const bare = input.match(/^[a-f0-9-]{36}$/i)
  if (bare) return input
  return null
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = normalizeId(opts.id)
  if (!id) {
    writeError(`Could not parse a job UUID from "${opts.id}"`, "BAD_ID")
    return 1
  }
  try {
    const html = await htmlFetch(`${DETAIL_BASE_URL}/${id}`)
    if (!html) {
      writeError("Job not found", "NOT_FOUND")
      return 1
    }
    const job = parseJobDetail(html, id)
    if (!job) {
      writeError("Could not parse job detail from the response", "PARSE_FAILED")
      return 1
    }

    if (opts.format === "plain") {
      const lines = [
        job.title,
        `${job.company || "—"} · ${job.location || "—"}`,
        "",
        job.employmentType ? `Employment: ${job.employmentType}` : "",
        job.positionCount ? `Positions: ${job.positionCount}` : "",
        job.deadline ? `Deadline: ${job.deadline}` : "Deadline: rolling / not specified",
        job.sector ? `Sector: ${job.sector}` : "",
        job.workLanguages ? `Languages: ${job.workLanguages}` : "",
        "",
        job.description || "(no description)",
        "",
        `URL: ${job.url}`,
        job.applyUrl ? `Apply: ${job.applyUrl}` : "",
      ].filter((l) => l !== "")
      process.stdout.write(lines.join("\n") + "\n")
    } else {
      process.stdout.write(JSON.stringify(job, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "DETAIL_FAILED")
    return 1
  }
}
