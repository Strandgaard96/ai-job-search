import { describe, test, expect } from "bun:test";
import { runCLI, parseJSON } from "./helpers";
import type { JobCard } from "../src/helpers";

const TEST_QUERY = "software engineer";

function parsedStderr(stderr: string): { error?: string; code?: string } {
  try {
    return JSON.parse(stderr);
  } catch {
    return {};
  }
}

describe("arbeidsplassen CLI flag validation", () => {
  test("non-numeric --jobage exits 1 with BAD_ARG", async () => {
    const result = await runCLI(["search", "-q", TEST_QUERY, "--jobage", "foo"]);
    expect(result.exitCode).not.toBe(0);
    const err = parsedStderr(result.stderr);
    expect(err.code).toBe("BAD_ARG");
    expect(err.error).toMatch(/jobage/);
  });

  test("non-numeric --page exits 1 with BAD_ARG", async () => {
    const result = await runCLI(["search", "-q", TEST_QUERY, "--page", "abc"]);
    expect(result.exitCode).not.toBe(0);
    const err = parsedStderr(result.stderr);
    expect(err.code).toBe("BAD_ARG");
  });

  test("detail with no id exits 1 with NO_ID", async () => {
    const result = await runCLI(["detail"]);
    expect(result.exitCode).not.toBe(0);
    const err = parsedStderr(result.stderr);
    expect(err.code).toBe("NO_ID");
  });

  test("detail with an unparseable id exits 1 with BAD_ID", async () => {
    const result = await runCLI(["detail", "not-a-uuid"]);
    expect(result.exitCode).not.toBe(0);
    const err = parsedStderr(result.stderr);
    expect(err.code).toBe("BAD_ID");
  });

  test("unknown command exits 1 with BAD_CMD", async () => {
    const result = await runCLI(["bogus"]);
    expect(result.exitCode).not.toBe(0);
    const err = parsedStderr(result.stderr);
    expect(err.code).toBe("BAD_CMD");
  });
});

describe("arbeidsplassen CLI live smoke test", () => {
  test("search returns real results with non-null id/title/url", async () => {
    const result = await runCLI(["search", "-q", TEST_QUERY, "--limit", "5"]);
    const body = parseJSON<{ meta: { count: number }; results: JobCard[] }>(result);
    expect(body.results.length).toBeGreaterThan(0);
    for (const card of body.results) {
      expect(card.id).toBeTruthy();
      expect(card.title).toBeTruthy();
      expect(card.url).toMatch(/^https:\/\/arbeidsplassen\.nav\.no\/stillinger\/stilling\//);
    }
  });

  test("detail returns a readable description for a live id", async () => {
    const search = await runCLI(["search", "-q", TEST_QUERY, "--limit", "1"]);
    const body = parseJSON<{ results: JobCard[] }>(search);
    expect(body.results.length).toBeGreaterThan(0);
    const id = body.results[0].id;

    const detail = await runCLI(["detail", id, "--format", "plain"]);
    expect(detail.exitCode).toBe(0);
    expect(detail.stdout.length).toBeGreaterThan(0);
    expect(detail.stdout).not.toMatch(/<[a-z]+>/i);
  });
});
