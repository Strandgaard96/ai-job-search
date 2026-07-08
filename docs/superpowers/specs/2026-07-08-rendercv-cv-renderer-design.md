# RenderCV CV Renderer (replacing LaTeX as the default)

Status: Approved (sub-project 3 of 3; sub-project 1 — job-scraper portal coverage — already
shipped; sub-project 2 — Norwegian job portals — skipped, already covered by the existing
`/add-portal` generator, no dedicated spec needed)

Date: 2026-07-08

## Problem

CV generation in this repo (`/apply`'s CV step, `05-cv-templates.md`, `CLAUDE.md`'s verification
checklist) is built entirely around LaTeX (`moderncv` banking style, compiled with `lualatex`).
The user maintains a separate personal-site repo (`../CV/`) that already solved CV rendering
without LaTeX at all: a single `cv.yaml` data file, a `build.py` script that drives `rendercv`
(Typst-based) to produce a PDF, and a lightweight `overrides/<name>.yaml` deep-merge mechanism for
tailored variants. The user wants that renderer adopted here as the new default, with the LaTeX
path kept working but never used unless explicitly requested.

## Goal

1. Add a RenderCV-based build system to this repo (`cv/cv.yaml`, `cv/build.py`,
   `cv/overrides/<company>.yaml`), modeled on `../CV/`'s pattern but adapted for this repo's
   need to keep multiple tailored CVs coexisting (one per application) rather than a single
   deployed PDF.
2. Make RenderCV the default renderer `/apply` and related skills instruct the agent to use.
3. Keep the existing LaTeX/`moderncv` system fully intact and working, used only when the user
   explicitly asks for it (e.g. "use the LaTeX template").
4. Make `cv.yaml` the source of truth for the CV-shaped fields it covers; regenerate the matching
   sections of `01-candidate-profile.md` from it rather than hand-maintaining both.
5. Update every doc/skill file that currently assumes LaTeX-by-default so a future session (or a
   fresh Claude instance reading `CLAUDE.md`/`README.md`) picks RenderCV correctly without
   rediscovering this decision.

## Non-goals

- Cover letters. `cover_letters/` (`cover.cls`, XeLaTeX, Lato/Raleway fonts) is entirely untouched
  by this change — this spec is CV-only.
- `add-template.md` (the custom-template registration command). It remains LaTeX-oriented;
  RenderCV is a new *built-in* default, not a slot `/add-template` manages. Not touched.
- An HTML/web output target. `../CV/build.py` also builds `public/index.html` for a deployed
  personal site; this repo has no such site, so `cv/build.py` here is PDF-only — no `web:` block,
  no Jinja2/HTML template, no `templates/` directory.
- Changing the per-company override *mechanism* itself. It is carried over unchanged from
  `../CV/`: `deep_merge(base, override)` where dicts merge recursively and lists/arrays are
  replaced wholesale, never appended. This is explicitly preserved, not redesigned.

## Design

### 1. File layout (new, under `cv/`, alongside the existing LaTeX files)

```
cv/
├── cv.yaml                  # NEW — master profile, CV-shaped fields only. Tracked in git.
├── build.py                 # NEW — PDF-only build script (see below). Tracked in git.
├── pyproject.toml           # NEW — uv project scoped to cv/. Tracked in git.
├── uv.lock                  # NEW — tracked in git (reproducible builds).
├── cv_image.jpeg            # NEW — copied from ../CV/. Gitignored (repo's existing blanket
│                             #   *.jpeg rule — personal photos are never committed here).
├── overrides/
│   ├── example.yaml         # NEW — tracked template override, mirrors ../CV/'s example.yaml.
│   └── <company>.yaml       # NEW per application — gitignored, personal.
├── rendercv_output/          # NEW — RenderCV's intermediate .typ working dir. Gitignored.
├── main_example.tex         # EXISTING — untouched, stays the LaTeX master template.
└── main_<company>.tex       # EXISTING — untouched, created only when LaTeX explicitly requested.
```

`.gitignore` additions:
```
cv/overrides/*.yaml
!cv/overrides/example.yaml
cv/rendercv_output/
cv/rendercv_input_tmp.yaml
```

(`cv/cv.yaml` needs no new ignore rule — it isn't matched by any existing pattern, so it's
tracked by default, same as `main_example.tex` today via its explicit `!cv/main_example.tex`
carve-out.)

### 2. `cv/build.py` behavior

Adapted from `../CV/build.py`'s `build_pdf()` — same RenderCV-render → Typst-compile pipeline,
same circular-photo-crop regex patch on the generated `.typ` file, same education-entry-spacing
patch. Two differences from `../CV/`:

- **No `build_html()`, no `web:` block in `cv.yaml`, no `templates/` dir.** PDF-only.
- **Output path is derived from the override, not fixed.** `../CV/build.py` always writes
  `public/cv.pdf`, overwriting on every build — fine for a personal site with one canonical CV.
  This repo needs many tailored CVs to coexist. So:
  ```bash
  cd cv && uv run python build.py pdf                                   # -> cv/main_example.pdf
  cd cv && uv run python build.py pdf --override overrides/netcompany.yaml  # -> cv/main_netcompany.pdf
  ```
  The output filename's company segment is the override file's stem (`netcompany.yaml` →
  `main_netcompany.pdf`), matching the existing `main_<company>.tex` naming convention exactly so
  `/apply`'s file-naming logic barely changes.

`cv/pyproject.toml` dependencies: `rendercv[full]` (includes the Typst compiler + fonts),
`pyyaml`; dev: `pytest`. No `jinja2`/`click` (no HTML build, argparse is enough, matching
`../CV/build.py`'s own CLI style).

### 3. `cv.yaml` ↔ `01-candidate-profile.md`

`cv.yaml` becomes canonical for the fields it covers: Identity, Education, Professional
Experience, Technical Skills, Publications, Independent Projects/Projects, photo. A new
`build.py profile` command (or equivalent step folded into `/setup --section profile`)
regenerates the matching sections of `01-candidate-profile.md` from `cv.yaml` — a one-way
generation. Those generated sections are never hand-edited directly; edit `cv.yaml`, regenerate.

`01-candidate-profile.md`'s other sections — Behavioral Profile, Awards, References, career
goals/deal-breakers material that has no CV equivalent — have no representation in `cv.yaml` and
stay hand-maintained prose, untouched by generation.

The per-company override mechanism (Non-goals, and `cv/build.py`'s `deep_merge`) is preserved
exactly: an override file only needs to contain the fields that differ for that application
(profile statement, reordered/reworded highlights), same as today's `cv/overrides/*.yaml` pattern
in `../CV/`.

### 4. Fallback trigger: RenderCV is default, LaTeX only on explicit request

`/apply` (and every skill doc below) defaults to RenderCV unconditionally. The LaTeX/`moderncv`
path is used only when the user's request explicitly says so (e.g. "use the LaTeX template",
"use moderncv") — there is no "ask every time" prompt. This trigger phrase is documented in both
`05-cv-templates.md` and `apply.md` so the agent recognizes it consistently.

### 5. Files updated to reflect the new default

- **`.claude/skills/job-application-assistant/05-cv-templates.md`** — restructured. New
  "Template: RenderCV (default)" section at the top: compile command, the existing
  page-budget/relevance-weighted-cutting guidance (kept — it's renderer-agnostic content
  strategy), the existing ATS-parseability check (kept — output is still a PDF, `pdftotext`
  still applies), a note on the photo/circular-crop behavior. All current moderncv/LaTeX content
  (document structure, `\cventry` orphan-title pitfalls, `\needspace`/`\enlargethispage` rescue
  patterns, itemize-spacing bug) moves under a new heading: "## Legacy: LaTeX/moderncv (opt-in
  only — use when the user explicitly asks for it)", preserved verbatim.
- **`.claude/skills/job-application-assistant/SKILL.md:30`** — "Create `cv/main_<company>.tex`
  with tailored content" → generate via `cv/overrides/<company>.yaml` + `cv/build.py`, producing
  `cv/main_<company>.pdf`, unless the user asked for LaTeX.
- **`.claude/commands/apply.md`** — CV section (~line 66), compile command (line 185), ATS-check
  command (line 230), file list (line 279): all switch to the RenderCV command by default. One
  line documents the LaTeX trigger phrase as the escape hatch.
- **`CLAUDE.md`** Verification Checklist, "Compiled PDF verification" section — the "CV compiled
  with lualatex" bullet is replaced with "CV built via RenderCV by default
  (`uv run python cv/build.py pdf --override cv/overrides/<company>.yaml`); LaTeX/lualatex only
  if explicitly requested." The 2-page hard-limit bullet and the ATS-check bullet are unchanged
  (both renderer-agnostic). The cover-letter/xelatex bullet is untouched (cover letters are out of
  scope).
- **`.claude/commands/setup.md`** — Step 3 item 7 targets `cv/cv.yaml` as the primary file to
  populate, instead of `cv/main_example.tex` (which remains supported, populated only when the
  user is using the LaTeX path).
- **`.claude/commands/outcome.md:61`** — the archival fallback lookup (used when a tracker row's
  `cv_file` column is empty) also checks for `cv/overrides/<company>.yaml` — the RenderCV "draft
  source" — alongside the existing `cv/main_<company>.tex` fallback.
- **`README.md`** — Prerequisites section notes RenderCV/`uv` as the CV requirement by default,
  with the LaTeX distribution requirement reframed as "only needed if you use the legacy LaTeX CV
  template." File-structure tree gains `cv/cv.yaml`, `cv/build.py`, `cv/overrides/` entries
  alongside the existing (now-labeled-legacy) `main_example.tex` line. The "Compile and inspect"
  step in "How `/apply` works" describes the RenderCV build-and-inspect loop as the default, with
  a note that LaTeX compilation happens only on explicit request. The "LaTeX templates" section
  under Customization gains a short RenderCV-default note pointing at `cv/cv.yaml`.

## Testing / verification

- `cd cv && uv sync` installs cleanly with the new `pyproject.toml`.
- `cd cv && uv run python build.py pdf` produces `cv/main_example.pdf`, exactly 2 pages, with the
  candidate's photo rendered as a circular crop.
- `cd cv && uv run python build.py pdf --override overrides/example.yaml` produces a
  differently-named PDF (`cv/main_example.pdf` still, since the shipped example's stem is
  `example` — a real per-company override like `overrides/netcompany.yaml` must be used to
  confirm distinct output naming, e.g. `cv/main_netcompany.pdf`).
- `pdftotext -layout` on the output extracts cleanly (no `(cid:*)` markers), matching the existing
  ATS-parseability bar.
- Asking `/apply` to generate a CV with no renderer specified produces a RenderCV PDF. Asking it
  with "use the LaTeX template" produces the existing `lualatex`-compiled PDF, unchanged from
  today's behavior.
- `01-candidate-profile.md`'s CV-derived sections match `cv.yaml` after regeneration; its
  Behavioral Profile/Awards/References sections are untouched by the regeneration step.

## Open items for the implementation plan

- Exact content of `cv/cv.yaml`, ported from the candidate's existing `cv/main_example.tex` +
  `01-candidate-profile.md` data (already gathered during this repo's `/setup` run earlier in
  this project).
- Exact wording/command for the `01-candidate-profile.md` regeneration step (new `build.py`
  subcommand vs. folding into `/setup --section profile`) — a plan-level implementation detail,
  not a design-level fork, since either way the behavior described in Design §3 is the same.
