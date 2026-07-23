# RenderCV CV Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a RenderCV/Typst-based CV build system (`cv/cv.yaml` + `cv/build.py`) as the default CV renderer for this repo, replacing LaTeX/moderncv as the instructed default everywhere while keeping the LaTeX path fully intact for explicit opt-in use, and make `cv.yaml` the source of truth for the CV-shaped fields it covers (regenerating the matching sections of `01-candidate-profile.md`).

**Architecture:** A new self-contained `cv/` Python subsystem (own `pyproject.toml`/`uv.lock`, own `cv.yaml` data file, own `build.py` driving `rendercv` → Typst → PDF, with a per-company `overrides/<company>.yaml` deep-merge mechanism identical to the pattern in the user's separate `../CV/` project) sits alongside the existing LaTeX files untouched. Seven markdown skill/doc files (`05-cv-templates.md`, `job-application-assistant/SKILL.md`, `apply.md`, `CLAUDE.md`, `outcome.md`, `setup.md`, `README.md`) are updated so every instruction defaults to the RenderCV command and only falls back to LaTeX on an explicit user request.

**Tech Stack:** Python 3.12+, `uv`, `rendercv[full]` (bundles the Typst compiler + fonts), `pyyaml`, `pytest`.

## Global Constraints

- RenderCV is the default renderer everywhere; LaTeX/`moderncv` is used **only** when the user's request explicitly says so (e.g. "use the LaTeX template", "use moderncv") — never an "ask every time" prompt.
- The per-company override mechanism is carried over unchanged from `../CV/`: `deep_merge(base, override)` merges dicts recursively; lists/arrays are **replaced wholesale, never appended**.
- Output naming: no override → `cv/main_example.pdf`; `--override overrides/<company>.yaml` → `cv/main_<company>.pdf` (the company segment is the override file's stem) — matches the existing `main_<company>.tex` convention exactly.
- `cv/build.py` is **PDF-only** — no `build_html()`, no `web:` block in `cv.yaml`, no `templates/` directory, no Jinja2/Click dependency. This repo has no website to deploy.
- `cv.yaml` is canonical for: Identity's CV fields (name/email/phone/LinkedIn/GitHub/website), Education, Professional Experience, Independent Projects, Technical Skills, Publications, photo. `01-candidate-profile.md`'s Behavioral Profile / Awards / References / Languages / Status / Constraints / career-goal material has no `cv.yaml` equivalent and is never touched by generation.
- Cover letters (`cover_letters/`, `cover.cls`, XeLaTeX) are completely out of scope — not touched anywhere in this plan.
- `.claude/commands/add-template.md` is completely out of scope — not touched anywhere in this plan.
- Photo is included (unlike the current LaTeX `main_example.tex`, which has no `\photo`): `cv_image.jpeg` copied from `../CV/`, circular-cropped via the same Typst post-processing regex `../CV/build.py` already uses.

---

### Task 1: Scaffold the `cv/` RenderCV subsystem — data and config

**Files:**
- Create: `cv/pyproject.toml`
- Create: `cv/cv.yaml`
- Create: `cv/cv_image.jpeg` (binary copy, not a text edit — see Step 1)
- Modify: `.gitignore` (append new rules)

**Interfaces:**
- Produces: `cv/cv.yaml` — a YAML file with top-level key `cv:` containing `name`, `email`, `phone`, `website`, `photo`, `social_networks` (list of `{network, username}`), `location`, and `sections:` (`summary` list-of-1-string, `experience` list of `{company, position, location, start_date, end_date, highlights}`, `education` list of `{institution, area, degree, start_date, end_date}`, `skills` list of `{label, details}`, `publications` list of `{title, authors, journal, date, doi}`, `projects` list of `{name, url?, highlights}`), plus a `design:` block. Task 2's `build.py` reads this file's `cv:` key directly.

- [ ] **Step 1: Copy the photo asset**

```bash
cp /home/magst/git/CV/cv_image.jpeg /home/magst/git/ai-job-search/cv/cv_image.jpeg
```

- [ ] **Step 2: Create `cv/pyproject.toml`**

```toml
[project]
name = "job-search-cv-builder"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pyyaml>=6.0",
    "rendercv[full]>=2.8",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
]
```

- [ ] **Step 3: Create `cv/cv.yaml`**

```yaml
cv:
  name: Magnus Strandgaard
  location: Copenhagen, Denmark
  email: magnus@strandgaard.dev
  phone: "+4593993124"
  website: https://cv.strandgaard.dev
  photo: cv_image.jpeg
  social_networks:
    - network: LinkedIn
      username: magnusstrandgaard
    - network: GitHub
      username: Strandgaard96
  sections:
    summary:
      - "Computational chemist with extensive experience with data science and cloud engineering — from multi-cluster HPC and ML pipelines to production AWS cloud environments. PhD in computational chemistry with a track record of end-to-end Python/ML systems for generative molecular design and property prediction, paired with enterprise cloud experience (AWS, Terraform, CI/CD) supporting a 1M+ user application. Driven by a strong passion to build computational systems that accelerate the green energy transition and healthcare."

    experience:
      - company: Netcompany
        position: Linux Operations Engineer
        location: Copenhagen, DK
        start_date: "2025"
        end_date: present
        highlights:
          - "Maintained and extended the AWS infrastructure for a **1M+ user application across 11 environments** (10 dev replicas + production), defining compute, networking, and data resources as code in Terraform with per-environment workspaces and AWS SSO access."
          - "Became the team's **lead Terraform developer within 3 months** of joining. Led the zero-downtime migration of an enterprise solution (1,000+ live resources) to a managed Terraform state, establishing rigorous code review practices and mitigating edge cases for seamless production deployment."
          - "Developed and maintained automated **CI/CD** pipelines in Azure DevOps and Jenkins, integrating strict policy checks and testing to ensure high-quality, production-ready code delivery."
          - "Python development for automation of internal processes. Including ingestion and processing of critical data. Engineered a robust **Python data-processing pipeline** that replaced a legacy service, resolving performance bottlenecks and **reducing cloud spend by ~$3,500/month** while ensuring secure data handling."

      - company: "Dept. of Chemistry, University of Copenhagen"
        position: Postdoctoral Researcher
        location: Copenhagen, DK
        start_date: "2024"
        end_date: "2025"
        highlights:
          - "Designed and operated **data pipelines across 4 HPC clusters** to ingest, curate, and validate **100K+ molecular records** from the Cambridge Structural Database, enabling **structure–property analysis** of transition-metal complexes."
          - "Built **predictive ML workflows** combining molecular fingerprints and **graph neural networks** to predict chemical properties of 3D structures, with accuracy gains over baseline models. Orchestrated distributed GPU training via **SLURM** and the WandB **MLOps** tool."
          - "Developed a novel **synthetic accessibility scoring tool** in **Python with C++ bindings** for generative molecular design pipelines."

      - company: "Dept. of Chemistry, University of Copenhagen"
        position: PhD Researcher
        location: Copenhagen, DK
        start_date: "2021"
        end_date: "2024"
        highlights:
          - "Developed end-to-end **in silico molecular discovery pipelines** coupling quantum chemistry with **generative ML models** (genetic algorithms, variational autoencoders) for **catalyst design and compound optimization**, screening thousands of candidates with **RDKit, Pandas, and SQLite**."
          - "Collaborated with the **University of Oslo** theoretical chemistry group to implement a **variational autoencoder (VAE)** for molecular inverse design, training PyTorch models on HPC GPUs to generate novel transition-metal complexes."
          - "Served as **HPC cluster administrator** for the physical chemistry department (**50+ active users**), managing Linux environments, SLURM job scheduling, and **reproducible computational workflows**."
          - "Created and maintained **4 open-source research repositories** on GitHub as lead developer."
          - "Mentored **60+ undergraduate students** as teaching assistant for physical chemistry and mathematics courses."

      - company: "Dept. of Energy, Technical University of Denmark"
        position: Research Assistant
        location: "Kongens Lyngby, DK"
        start_date: "2021"
        end_date: "2021"
        highlights:
          - "Implemented a **Message Passing Neural Network (MPNN)** in **PyTorch** to predict forces and energies of magnesium battery cathode candidates, enabling **molecular dynamics simulations** of next-generation energy-storage materials."

    education:
      - institution: University of Copenhagen
        area: Computational Chemistry
        degree: PhD
        start_date: "2021"
        end_date: "2024"
      - institution: Technical University of Denmark
        area: Physics and Nanotechnology
        degree: MSc
        start_date: "2018"
        end_date: "2021"
      - institution: Technical University of Denmark
        area: Physics and Nanotechnology
        degree: BSc
        start_date: "2015"
        end_date: "2018"

    skills:
      - label: Languages & Engineering
        details: "Python (Expert) · FastAPI · REST APIs · Unit Testing (Pytest) · SQL & NoSQL (RDS/DynamoDB) · Git · Docker · CI/CD · Familiar with: TypeScript, React, Tailwind, C++, Golang"
      - label: Data Science & ML
        details: "PyTorch · Scikit-learn · SciPy · NumPy · Pandas · MLOps (WandB, MLflow) · Familiar with: LangChain, dbt"
      - label: Scientific Visualization
        details: "Streamlit · Plotly · Matplotlib"
      - label: Cloud & Platform
        details: "AWS (Full Stack) · Terraform · SLURM (HPC admin) · Proxmox · Ansible · Jenkins · Azure DevOps · Linux · Familiar with: Nextflow, Apache Airflow, Azure"
      - label: Cheminformatics
        details: "RDKit · Molecular Embeddings · QSPR/QSAR · ORCA · xTB · VASP · ADF"
      - label: AI-Assisted Development
        details: "Claude Code · Gemini CLI · GitHub Copilot · building and shipping production software with AI coding agents"
      - label: Spoken
        details: "Danish & Norwegian (native) · English (fluent) · Spanish (basic)"

    publications:
      - title: "A Deep Generative Model for the Inverse Design of Transition Metal Ligands and Complexes"
        authors:
          - "**Magnus Strandgaard**"
          - Linjordet T
          - Kneiding H
          - Burnage AL
          - Nova A
          - Jensen JH
          - Balcells D
        journal: JACS Au
        date: "2025"
        doi: "10.1021/jacsau.5c00242"
      - title: "Discovery of molybdenum-based nitrogen fixation catalysts with genetic algorithms"
        authors:
          - "**Magnus Strandgaard**"
          - Seumer J
          - Jensen JH
        journal: Chemical Science
        date: "2024"
        doi: "10.1039/D4SC02227K"
      - title: "Genetic algorithm-based re-optimization of the Schrock catalyst for dinitrogen fixation"
        authors:
          - "**Magnus Strandgaard**"
          - Seumer J
          - Benediktsson B
          - Bhowmik A
          - Vegge T
          - Jensen JH
        journal: PeerJ Physical Chemistry
        date: "2023"
        doi: "10.7717/peerj-pchem.30"
      - title: "SMILES All Around: Structure to SMILES conversion for Transition Metal Complexes"
        authors:
          - Rasmussen MH
          - "**Magnus Strandgaard**"
          - Seumer J
          - Hemmingsen LK
          - Frei A
          - Balcells D
          - Jensen JH
        journal: Journal of Cheminformatics
        date: "2025"
        doi: "10.1186/s13321-025-01008-1"

    projects:
      - name: "Self-hosted Proxmox Homelab"
        highlights:
          - "Deploy and maintain a self-hosted **Proxmox** server orchestrating multiple VMs and LXC containers for web and IT services on Linux, with provisioning and configuration **automated via Ansible and Terraform**."
      - name: "Full-stack AWS-hosted Web Application"
        url: "https://games.drmaggi.com"
        highlights:
          - "Engineered a **full-stack web application** — **React/TypeScript/Tailwind** frontend, **Python/FastAPI** backend — using AWS and Terraform knowledge to architect a near-zero-cost serverless AWS environment with Terraform and directing the implementation with Claude Code. Live at [games.drmaggi.com](https://games.drmaggi.com)."

design:
  theme: classic
  page:
    show_footer: false
    show_top_note: false
  colors:
    body: rgb(27, 28, 30)
    name: rgb(27, 28, 30)
    headline: rgb(21, 94, 82)
    connections: rgb(108, 111, 116)
    section_titles: rgb(21, 94, 82)
    links: rgb(21, 94, 82)
  typography:
    date_and_location_column_alignment: right
    alignment: justified
    line_spacing: 0.55em
  header:
    alignment: left
    photo_width: 3.5cm
    photo_position: right
    connections:
      phone_number_format: international
  links:
    underline: false
    show_external_link_icon: false
  entries:
    allow_page_break: true
  sections:
    show_time_spans_in: []
    space_between_regular_entries: 0.6em
  templates:
    single_date: YEAR
    experience_entry:
      main_column: "COMPANY, **POSITION**\nSUMMARY\nHIGHLIGHTS"
```

- [ ] **Step 4: Append `.gitignore` rules**

Old (end of file, after the existing `.agents/usage/` line):
```
.agents/**/node_modules/
.agents/**/*.log
.agents/usage/
```

New:
```
.agents/**/node_modules/
.agents/**/*.log
.agents/usage/

# RenderCV build system (cv/cv.yaml and cv/overrides/example.yaml are tracked templates;
# per-company overrides and build scratch are personal/regenerable)
cv/overrides/*.yaml
!cv/overrides/example.yaml
cv/rendercv_output/
cv/rendercv_input_tmp.yaml
```

Use the Edit tool with the old block (the last 3 lines of the current `.gitignore`) as `old_string`.

- [ ] **Step 5: Verify the environment installs cleanly**

```bash
cd cv && uv sync
```
Expected: exits 0, creates `cv/.venv/` and `cv/uv.lock` (already gitignored / to be tracked
respectively — `.venv/` is covered by the repo's existing blanket `.venv/` ignore rule, `uv.lock`
is a new file this step produces and Task 2 will commit alongside `build.py`).

- [ ] **Step 6: Commit**

```bash
git add cv/pyproject.toml cv/cv.yaml cv/cv_image.jpeg .gitignore
git commit -m "$(cat <<'EOF'
feat(cv): scaffold RenderCV data files and dependencies

Adds cv/cv.yaml (master profile, CV-shaped fields) and cv/pyproject.toml
(rendercv[full] + pyyaml) as the foundation for the new default CV
renderer, modeled on the ../CV/ personal-site project's pattern.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

Note: `cv/uv.lock` is created by Step 5 but committed in Task 2 (alongside `build.py`, once it's
actually exercised) rather than here, to keep this commit's diff focused on hand-authored files.

---

### Task 2: `cv/build.py` — PDF build command

**Files:**
- Create: `cv/build.py`
- Create: `cv/tests/test_build.py`
- Modify: nothing else

**Interfaces:**
- Consumes: `cv/cv.yaml` (Task 1).
- Produces: `deep_merge(base: dict, override: dict) -> dict` and `build_pdf(override_path: pathlib.Path | None = None) -> None`, both importable as `from build import deep_merge` / `from build import build_pdf` for tests and for Task 4's `build_profile()` (added to this same file in Task 4, which imports nothing new from this task but shares the file).
- Produces (CLI): `uv run python build.py pdf [--override PATH]` — writes `main_example.pdf` (no override) or `main_<override-stem>.pdf` (with override) into the `cv/` working directory.

- [ ] **Step 1: Write the failing test for `deep_merge`**

Create `cv/tests/test_build.py`:

```python
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


# ── deep_merge ────────────────────────────────────────────────────────────────

def test_deep_merge_scalar_override():
    from build import deep_merge
    base = {"cv": {"name": "Alice", "email": "a@a.com"}}
    override = {"cv": {"name": "Bob"}}
    result = deep_merge(base, override)
    assert result["cv"]["name"] == "Bob"
    assert result["cv"]["email"] == "a@a.com"


def test_deep_merge_list_replaced_not_appended():
    from build import deep_merge
    base = {"cv": {"sections": {"experience": ["job1", "job2"]}}}
    override = {"cv": {"sections": {"experience": ["job3"]}}}
    result = deep_merge(base, override)
    assert result["cv"]["sections"]["experience"] == ["job3"]


def test_deep_merge_partial_section_override():
    from build import deep_merge
    base = {"cv": {"sections": {"experience": ["job1"], "education": ["edu1"]}}}
    override = {"cv": {"sections": {"experience": ["job2"]}}}
    result = deep_merge(base, override)
    assert result["cv"]["sections"]["experience"] == ["job2"]
    assert result["cv"]["sections"]["education"] == ["edu1"]


def test_deep_merge_base_unchanged():
    from build import deep_merge
    base = {"cv": {"name": "Alice"}}
    override = {"cv": {"name": "Bob"}}
    deep_merge(base, override)
    assert base["cv"]["name"] == "Alice"


# ── output naming ─────────────────────────────────────────────────────────────

def test_output_stem_no_override():
    from build import _output_stem
    assert _output_stem(None) == "example"


def test_output_stem_with_override():
    from build import _output_stem
    assert _output_stem(pathlib.Path("overrides/netcompany.yaml")) == "netcompany"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd cv && uv run pytest tests/test_build.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'build'` (the file doesn't exist yet).

- [ ] **Step 3: Write `cv/build.py`**

```python
#!/usr/bin/env python3
"""Build a CV PDF from cv.yaml via RenderCV/Typst.

  uv run python build.py pdf
  uv run python build.py pdf --override overrides/netcompany.yaml
"""
import argparse
import copy
import pathlib
import re
import subprocess
import sys
import yaml


def deep_merge(base: dict, override: dict) -> dict:
    """Return new dict: override merged onto base. Lists replaced, not appended."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def _output_stem(override_path: pathlib.Path | None) -> str:
    """Derive the output PDF's company segment from the override filename."""
    if override_path is None:
        return "example"
    return override_path.stem


def build_pdf(override_path: pathlib.Path | None = None) -> None:
    import shutil as _shutil
    import typst as _typst
    import rendercv_fonts as _rendercv_fonts
    from rendercv.renderer.pdf_png import get_package_path

    base = yaml.safe_load(pathlib.Path("cv.yaml").read_text())
    merged = deep_merge(base, yaml.safe_load(override_path.read_text())) if override_path else base
    photo_name = merged.get("cv", {}).get("photo")

    out = pathlib.Path(f"main_{_output_stem(override_path)}.pdf")

    tmp_path = pathlib.Path("rendercv_input_tmp.yaml")
    tmp_path.write_text(yaml.dump(merged, allow_unicode=True, sort_keys=False))

    try:
        subprocess.run(
            [sys.executable, "-m", "rendercv", "render", str(tmp_path),
             "--dont-generate-pdf",
             "--dont-generate-markdown",
             "--dont-generate-html",
             "--dont-generate-png",
             "--quiet"],
            check=True,
            capture_output=True,
            text=True,
        )

        output_dir = pathlib.Path("rendercv_output")
        typ_files = list(output_dir.glob("*.typ"))
        if not typ_files:
            raise RuntimeError("No .typ file generated in rendercv_output/")
        typ_path = typ_files[0]

        if photo_name:
            photo_src = pathlib.Path(photo_name)
            if photo_src.exists():
                _shutil.copy(photo_src, output_dir / photo_src.name)

        content = typ_path.read_text()
        content = re.sub(
            r'(image\("[^"]+",\s*width:\s*[^)]+\))',
            r'box(clip: true, radius: 50%, \1)',
            content,
        )
        content = re.sub(
            r'(\))\n\n(#education-entry\()',
            r'\1\n#v(-0.6em)\n\2',
            content,
        )
        typ_path.write_text(content)

        compiler = _typst.Compiler(
            root=output_dir.resolve(),
            font_paths=_rendercv_fonts.paths_to_font_folders,
            package_path=get_package_path(),
        )
        compiler.compile(input=typ_path.resolve(), format="pdf", output=out.resolve())

    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        raise
    finally:
        tmp_path.unlink(missing_ok=True)

    print(f"Built {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a CV PDF from cv.yaml via RenderCV.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pdf_p = sub.add_parser("pdf", help="Generate main_<company>.pdf via RenderCV")
    pdf_p.add_argument("--override", type=pathlib.Path, default=None,
                        help="Override YAML (e.g. overrides/netcompany.yaml)")

    args = parser.parse_args()

    if args.cmd == "pdf":
        build_pdf(args.override)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd cv && uv run pytest tests/test_build.py -v
```
Expected: `6 passed` (the 4 `deep_merge` tests + 2 `_output_stem` tests), pristine output (no
warnings).

- [ ] **Step 5: Smoke-test an actual PDF build**

```bash
cd cv && uv run python build.py pdf
```
Expected: `Built main_example.pdf`, exit code 0, and `cv/main_example.pdf` exists.

```bash
cd cv && ls -la main_example.pdf && file main_example.pdf
```
Expected: file exists, `file` reports `PDF document`.

- [ ] **Step 6: Commit**

```bash
git add cv/build.py cv/tests/test_build.py cv/uv.lock
git commit -m "$(cat <<'EOF'
feat(cv): add build.py PDF build command

RenderCV -> Typst pipeline (ported from ../CV/build.py, PDF-only, no
HTML/web target). Output filename derives from the --override stem
(main_<company>.pdf) instead of a fixed path, so multiple tailored
CVs can coexist.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Per-company overrides + end-to-end tailored-PDF test

**Files:**
- Create: `cv/overrides/example.yaml`
- Modify: `cv/tests/test_build.py` (append tests)

**Interfaces:**
- Consumes: `build_pdf` and `_output_stem` from Task 2.
- Produces: nothing new consumed by later tasks — this task is a correctness/behavior gate on
  Task 2's output-naming and override behavior before docs start referencing it.

- [ ] **Step 1: Create `cv/overrides/example.yaml`**

```yaml
# Example override for a data engineering / ML role.
# Only fields listed here are changed; everything else comes from cv.yaml.
cv:
  sections:
    summary:
      - "Computational chemist turned data engineer with a track record of building
        end-to-end ML pipelines on HPC and cloud. PhD in computational chemistry.
        Deep experience with PyTorch, distributed training, and AWS data infrastructure."
    experience:
      - company: Netcompany
        position: Linux Operations Engineer
        location: Copenhagen, DK
        start_date: "2025"
        end_date: present
        highlights:
          - "**Cut AWS spend by ~$3,500/month** by building a Python data-processing and visualization pipeline that replaced a costly legacy service."
          - "Maintained AWS infrastructure (**S3, EC2, RDS, IAM, CloudWatch**) for a 1M+ user application, writing Terraform for all resource changes."
```

- [ ] **Step 2: Write the failing tests for override-driven output naming**

Append to `cv/tests/test_build.py`:

```python
# ── PDF build smoke tests ──────────────────────────────────────────────────────

def test_pdf_build_no_override_produces_main_example():
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "build.py", "pdf"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert pathlib.Path("main_example.pdf").exists()


def test_pdf_build_with_override_produces_distinct_filename():
    import subprocess
    import sys
    import shutil

    override_path = pathlib.Path("overrides/_test_company.yaml")
    override_path.write_text(
        'cv:\n  sections:\n    summary:\n      - "Test override summary."\n'
    )
    out_path = pathlib.Path("main__test_company.pdf")
    try:
        result = subprocess.run(
            [sys.executable, "build.py", "pdf", "--override", str(override_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert out_path.exists()
        assert out_path != pathlib.Path("main_example.pdf")
    finally:
        override_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
        shutil.rmtree("rendercv_output", ignore_errors=True)
```

- [ ] **Step 3: Run tests to verify they fail or pass for the right reason**

```bash
cd cv && uv run pytest tests/test_build.py -v -k "pdf_build"
```
Expected at this point: both tests should actually PASS already, since Task 2's `build_pdf` and
`_output_stem` already implement this behavior — this step is confirming that, not chasing a RED
state. If either fails, the failure means Task 2's implementation has a bug; fix `build.py`
before proceeding (do not weaken these tests).

- [ ] **Step 4: Run the full test suite**

```bash
cd cv && uv run pytest -v
```
Expected: all tests pass (the 6 from Task 2 plus the 2 new ones = 8), pristine output.

- [ ] **Step 5: Manually verify the tailored-CV workflow end to end**

```bash
cd cv && uv run python build.py pdf --override overrides/example.yaml
ls -la main_example.pdf
```
Expected: `Built main_example.pdf` (the shipped `example.yaml`'s stem is `example`, same as the
no-override case — this confirms the override content actually changed the PDF, not that the
filename differs; open/Read the PDF and confirm the summary paragraph matches
`overrides/example.yaml`'s text, not `cv.yaml`'s original summary).

- [ ] **Step 6: Verify ATS text-layer extraction still works on RenderCV output**

```bash
cd cv && pdftotext -layout main_example.pdf main_example.txt && cat main_example.txt | head -20
rm cv/main_example.txt
```
Expected: clean text extraction, no `(cid:*)` markers, email/phone appear as literal text. If
`pdftotext` is not installed, skip this step and note it in the report — same graceful-skip
convention as the rest of this repo's ATS check.

- [ ] **Step 7: Commit**

```bash
git add cv/overrides/example.yaml cv/tests/test_build.py
git commit -m "$(cat <<'EOF'
test(cv): verify per-company override and PDF output naming end to end

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `cv.yaml` → `01-candidate-profile.md` regeneration

**Files:**
- Modify: `.claude/skills/job-application-assistant/01-candidate-profile.md` (insert marker
  comments around 5 sections)
- Modify: `cv/build.py` (append `build_profile()` + CLI wiring)
- Modify: `cv/tests/test_build.py` (append tests)

**Interfaces:**
- Consumes: `cv/cv.yaml`'s `cv:` key structure (Task 1) and `deep_merge`-free direct YAML load
  (no override applies to profile regeneration — it always uses the un-overridden master
  `cv.yaml`).
- Produces: `build_profile() -> None` and `_replace_marked(text: str, name: str, replacement: str) -> str`, both in `cv/build.py`. CLI: `uv run python build.py profile`.

- [ ] **Step 1: Insert marker comments into `01-candidate-profile.md`**

Read the current file first (`.claude/skills/job-application-assistant/01-candidate-profile.md`)
to get its exact current text, then apply these 5 edits with the Edit tool. Each edit wraps an
existing block in a `<!-- CV-YAML:<NAME>:START -->` / `<!-- CV-YAML:<NAME>:END -->` pair without
changing the block's visible content.

**Edit 1 — Identity's CV-derived lines.** Old:
```markdown
- **Name:** Magnus Strandgaard
- **Location:** Copenhagen, Denmark
- **Phone:** +45 93 99 31 24
- **Email:** magnus@strandgaard.dev
- **LinkedIn:** linkedin.com/in/magnusstrandgaard
- **GitHub:** github.com/Strandgaard96
- **Website:** cv.strandgaard.dev
- **Languages:** Danish (native), Norwegian (native), English (fluent), Spanish (basic)
```
New:
```markdown
<!-- CV-YAML:IDENTITY:START -->
- **Name:** Magnus Strandgaard
- **Location:** Copenhagen, Denmark
- **Phone:** +45 93 99 31 24
- **Email:** magnus@strandgaard.dev
- **LinkedIn:** linkedin.com/in/magnusstrandgaard
- **GitHub:** github.com/Strandgaard96
- **Website:** cv.strandgaard.dev
<!-- CV-YAML:IDENTITY:END -->
- **Languages:** Danish (native), Norwegian (native), English (fluent), Spanish (basic)
```
(Languages/Status/Constraints lines stay outside the marker — `cv.yaml` has no equivalent field
for employment status or commute constraints, and its `Spoken` skill entry is a different
representation of languages than this line.)

**Edit 2 — Education table.** Old:
```markdown
## Education

| Degree | Period | Institution | Key Topics |
|--------|--------|-------------|------------|
| PhD, Computational Chemistry | 2021-2024 | University of Copenhagen | Generative ML (genetic algorithms, VAEs) for catalyst design and transition-metal complex inverse design; quantum chemistry |
| MSc, Physics and Nanotechnology | 2018-2021 | Technical University of Denmark | Physics, nanotechnology, materials |
| BSc, Physics and Nanotechnology | 2015-2018 | Technical University of Denmark | Physics, nanotechnology fundamentals |
```
New:
```markdown
## Education

<!-- CV-YAML:EDUCATION:START -->
| Degree | Period | Institution | Key Topics |
|--------|--------|-------------|------------|
| PhD, Computational Chemistry | 2021-2024 | University of Copenhagen | Generative ML (genetic algorithms, VAEs) for catalyst design and transition-metal complex inverse design; quantum chemistry |
| MSc, Physics and Nanotechnology | 2018-2021 | Technical University of Denmark | Physics, nanotechnology, materials |
| BSc, Physics and Nanotechnology | 2015-2018 | Technical University of Denmark | Physics, nanotechnology fundamentals |
<!-- CV-YAML:EDUCATION:END -->
```

**Edit 3 — Professional Experience (all 4 roles).** Old: the entire block starting at
`### Linux Operations Engineer - Netcompany (2025 - present)` through the end of the Research
Assistant role's single bullet (ending `...next-generation energy-storage materials`). New: same
block, wrapped:
```markdown
<!-- CV-YAML:EXPERIENCE:START -->
### Linux Operations Engineer - Netcompany (2025 - present)
Copenhagen, DK
- Maintained and extended AWS infrastructure for a 1M+ user application across 11 environments (10 dev replicas + production), defining compute, networking, and data resources as code in Terraform with per-environment workspaces and AWS SSO access
- Became the team's lead Terraform developer within 3 months of joining; led zero-downtime migration of an enterprise solution (1,000+ live resources) to managed Terraform state, establishing code review practices
- Developed and maintained automated CI/CD pipelines in Azure DevOps and Jenkins with strict policy checks and testing
- Engineered a Python data-processing pipeline replacing a legacy service, resolving performance bottlenecks and reducing cloud spend by ~$3,500/month while ensuring secure data handling

### Postdoctoral Researcher - Dept. of Chemistry, University of Copenhagen (2024 - 2025)
Copenhagen, DK
- Designed and operated data pipelines across 4 HPC clusters to ingest, curate, and validate 100K+ molecular records from the Cambridge Structural Database, enabling structure-property analysis of transition-metal complexes
- Built predictive ML workflows combining molecular fingerprints and graph neural networks to predict chemical properties of 3D structures, with accuracy gains over baseline models; orchestrated distributed GPU training via SLURM and WandB
- Developed a novel synthetic accessibility scoring tool in Python with C++ bindings for generative molecular design pipelines

### PhD Researcher - Dept. of Chemistry, University of Copenhagen (2021 - 2024)
Copenhagen, DK
- Developed end-to-end in silico molecular discovery pipelines coupling quantum chemistry with generative ML models (genetic algorithms, variational autoencoders) for catalyst design and compound optimization, screening thousands of candidates with RDKit, Pandas, and SQLite
- Collaborated with the University of Oslo theoretical chemistry group to implement a VAE for molecular inverse design, training PyTorch models on HPC GPUs to generate novel transition-metal complexes
- Served as HPC cluster administrator for the physical chemistry department (50+ active users), managing Linux environments, SLURM job scheduling, and reproducible computational workflows
- Created and maintained 4 open-source research repositories on GitHub as lead developer
- Mentored 60+ undergraduate students as teaching assistant for physical chemistry and mathematics courses

### Research Assistant - Dept. of Energy, Technical University of Denmark (2021 - 2021)
Kongens Lyngby, DK
- Implemented a Message Passing Neural Network (MPNN) in PyTorch to predict forces and energies of magnesium battery cathode candidates, enabling molecular dynamics simulations of next-generation energy-storage materials
<!-- CV-YAML:EXPERIENCE:END -->
```

**Edit 4 — Independent Projects.** Old:
```markdown
## Independent Projects
- **Self-hosted Proxmox Homelab**: Deploy and maintain a self-hosted Proxmox server orchestrating multiple VMs and LXC containers for web and IT services on Linux, with provisioning and configuration automated via Ansible and Terraform
- **Full-stack AWS-hosted Web Application**: Engineered a full-stack web application (React/TypeScript/Tailwind frontend, Python/FastAPI backend) using AWS and Terraform to architect a near-zero-cost serverless environment, directing implementation with Claude Code. Live at games.drmaggi.com
```
New:
```markdown
## Independent Projects
<!-- CV-YAML:PROJECTS:START -->
- **Self-hosted Proxmox Homelab**: Deploy and maintain a self-hosted Proxmox server orchestrating multiple VMs and LXC containers for web and IT services on Linux, with provisioning and configuration automated via Ansible and Terraform
- **Full-stack AWS-hosted Web Application**: Engineered a full-stack web application (React/TypeScript/Tailwind frontend, Python/FastAPI backend) using AWS and Terraform to architect a near-zero-cost serverless environment, directing implementation with Claude Code. Live at games.drmaggi.com
<!-- CV-YAML:PROJECTS:END -->
```

**Edit 5 — Technical Skills (reformatted to `cv.yaml`'s 7-category structure) and Publications.**
Old:
```markdown
## Technical Skills

### Programming & ML
- **Python** (Expert): FastAPI, REST APIs, Pytest, PyTorch, Scikit-learn, SciPy, NumPy, Pandas
- **Familiar:** TypeScript, React, Tailwind, C++, Golang
- **MLOps:** WandB, MLflow
- **Data:** SQL & NoSQL (RDS/DynamoDB), Git, Docker, CI/CD
- **Visualization:** Streamlit, Plotly, Matplotlib

### Domain Expertise
- Cheminformatics: RDKit, molecular embeddings, QSPR/QSAR, ORCA, xTB, VASP, ADF
- Computational chemistry / quantum chemistry
- Generative molecular design (genetic algorithms, VAEs, graph neural networks)
- AI-assisted software development: Claude Code, Gemini CLI, GitHub Copilot - building and shipping production software with AI coding agents

### Software & Tools
AWS (Full Stack), Terraform, SLURM (HPC admin), Proxmox, Ansible, Jenkins, Azure DevOps, Linux. Familiar: Nextflow, Apache Airflow, Azure

## Publications
1. Strandgaard M, Linjordet T, Kneiding H, Burnage AL, Nova A, Jensen JH, Balcells D (2025). A Deep Generative Model for the Inverse Design of Transition Metal Ligands and Complexes. JACS Au. 10.1021/jacsau.5c00242
2. Strandgaard M, Seumer J, Jensen JH (2024). Discovery of molybdenum-based nitrogen fixation catalysts with genetic algorithms. Chemical Science. 10.1039/D4SC02227K
3. Strandgaard M, Seumer J, Benediktsson B, Bhowmik A, Vegge T, Jensen JH (2023). Genetic algorithm-based re-optimization of the Schrock catalyst for dinitrogen fixation. PeerJ Physical Chemistry. 10.7717/peerj-pchem.30
4. Rasmussen MH, Strandgaard M, Seumer J, Hemmingsen LK, Frei A, Balcells D, Jensen JH (2025). SMILES All Around: Structure to SMILES conversion for Transition Metal Complexes. Journal of Cheminformatics. 10.1186/s13321-025-01008-1
```
New:
```markdown
## Technical Skills

<!-- CV-YAML:SKILLS:START -->
- **Languages & Engineering:** Python (Expert) · FastAPI · REST APIs · Unit Testing (Pytest) · SQL & NoSQL (RDS/DynamoDB) · Git · Docker · CI/CD · Familiar with: TypeScript, React, Tailwind, C++, Golang
- **Data Science & ML:** PyTorch · Scikit-learn · SciPy · NumPy · Pandas · MLOps (WandB, MLflow) · Familiar with: LangChain, dbt
- **Scientific Visualization:** Streamlit · Plotly · Matplotlib
- **Cloud & Platform:** AWS (Full Stack) · Terraform · SLURM (HPC admin) · Proxmox · Ansible · Jenkins · Azure DevOps · Linux · Familiar with: Nextflow, Apache Airflow, Azure
- **Cheminformatics:** RDKit · Molecular Embeddings · QSPR/QSAR · ORCA · xTB · VASP · ADF
- **AI-Assisted Development:** Claude Code · Gemini CLI · GitHub Copilot · building and shipping production software with AI coding agents
- **Spoken:** Danish & Norwegian (native) · English (fluent) · Spanish (basic)
<!-- CV-YAML:SKILLS:END -->

## Publications
<!-- CV-YAML:PUBLICATIONS:START -->
1. Strandgaard M, Linjordet T, Kneiding H, Burnage AL, Nova A, Jensen JH, Balcells D (2025). A Deep Generative Model for the Inverse Design of Transition Metal Ligands and Complexes. JACS Au. 10.1021/jacsau.5c00242
2. Strandgaard M, Seumer J, Jensen JH (2024). Discovery of molybdenum-based nitrogen fixation catalysts with genetic algorithms. Chemical Science. 10.1039/D4SC02227K
3. Strandgaard M, Seumer J, Benediktsson B, Bhowmik A, Vegge T, Jensen JH (2023). Genetic algorithm-based re-optimization of the Schrock catalyst for dinitrogen fixation. PeerJ Physical Chemistry. 10.7717/peerj-pchem.30
4. Rasmussen MH, Strandgaard M, Seumer J, Hemmingsen LK, Frei A, Balcells D, Jensen JH (2025). SMILES All Around: Structure to SMILES conversion for Transition Metal Complexes. Journal of Cheminformatics. 10.1186/s13321-025-01008-1
<!-- CV-YAML:PUBLICATIONS:END -->
```

Note: the "Spoken" skills line now duplicates the standalone Languages line in Identity (outside
the marker). This is expected and matches the spec — `cv.yaml`'s skill category and the
hand-maintained Languages line are two different fields that happen to overlap in content; do not
try to deduplicate them, that would require changing which fields `cv.yaml` covers.

- [ ] **Step 2: Write the failing test for `build_profile`**

Append to `cv/tests/test_build.py`:

```python
# ── profile regeneration ───────────────────────────────────────────────────────

def test_replace_marked_replaces_only_between_markers():
    from build import _replace_marked
    text = (
        "before\n"
        "<!-- CV-YAML:FOO:START -->\nold content\n<!-- CV-YAML:FOO:END -->\n"
        "after"
    )
    result = _replace_marked(text, "FOO", "new content")
    assert result == (
        "before\n"
        "<!-- CV-YAML:FOO:START -->\nnew content\n<!-- CV-YAML:FOO:END -->\n"
        "after"
    )


def test_replace_marked_raises_if_markers_missing():
    import pytest
    from build import _replace_marked
    with pytest.raises(RuntimeError, match="not found"):
        _replace_marked("no markers here", "MISSING", "x")


def test_build_profile_regenerates_only_marked_sections():
    from build import build_profile
    import pathlib

    profile_path = pathlib.Path(
        "../.claude/skills/job-application-assistant/01-candidate-profile.md"
    )
    original = profile_path.read_text()
    try:
        assert "<!-- CV-YAML:IDENTITY:START -->" in original, (
            "Task 4 Step 1 must insert markers before this test can pass"
        )
        build_profile()
        updated = profile_path.read_text()
        # Content outside any marker (Behavioral-adjacent Awards/References) is untouched
        assert "## Awards" in updated
        assert "## References" in updated
        assert "[none listed - add if applicable]" in updated
        # Marked content reflects cv.yaml, not stale hand-typed duplicates
        assert "**Name:** Magnus Strandgaard" in updated
        assert "JACS Au" in updated
    finally:
        profile_path.write_text(original)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd cv && uv run pytest tests/test_build.py -v -k "replace_marked or build_profile"
```
Expected: FAIL — `ImportError: cannot import name '_replace_marked'` /
`cannot import name 'build_profile'` (neither exists in `build.py` yet).

- [ ] **Step 4: Append `build_profile()` and `_replace_marked()` to `cv/build.py`**

Add after `build_pdf()` and before the `if __name__ == "__main__":` block:

```python
def _replace_marked(text: str, name: str, replacement: str) -> str:
    start = f"<!-- CV-YAML:{name}:START -->"
    end = f"<!-- CV-YAML:{name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError(f"Markers {start} / {end} not found in candidate profile")
    return pattern.sub(f"{start}\n{replacement}\n{end}", text)


def build_profile() -> None:
    """Regenerate the CV-derived sections of 01-candidate-profile.md from cv.yaml."""
    profile_path = pathlib.Path(
        "../.claude/skills/job-application-assistant/01-candidate-profile.md"
    )
    data = yaml.safe_load(pathlib.Path("cv.yaml").read_text())
    cv = data["cv"]
    s = cv["sections"]

    linkedin_user = next(
        n["username"] for n in cv["social_networks"] if n["network"] == "LinkedIn"
    )
    github_user = next(
        n["username"] for n in cv["social_networks"] if n["network"] == "GitHub"
    )
    identity_block = (
        f"- **Name:** {cv['name']}\n"
        f"- **Location:** {cv['location']}\n"
        f"- **Phone:** {cv['phone']}\n"
        f"- **Email:** {cv['email']}\n"
        f"- **LinkedIn:** linkedin.com/in/{linkedin_user}\n"
        f"- **GitHub:** github.com/{github_user}\n"
        f"- **Website:** {cv['website']}"
    )

    education_rows = "\n".join(
        f"| {e['degree']}, {e['area']} | {e['start_date']}-{e['end_date']} | {e['institution']} | |"
        for e in s["education"]
    )
    education_block = (
        "| Degree | Period | Institution | Key Topics |\n"
        "|--------|--------|-------------|------------|\n"
        f"{education_rows}"
    )

    experience_blocks = []
    for job in s["experience"]:
        highlights = "\n".join(f"- {h}" for h in job["highlights"])
        experience_blocks.append(
            f"### {job['position']} - {job['company']} ({job['start_date']} - {job['end_date']})\n"
            f"{job['location']}\n"
            f"{highlights}"
        )
    experience_block = "\n\n".join(experience_blocks)

    project_blocks = []
    for proj in s["projects"]:
        highlights = "\n".join(f"  {h}" for h in proj["highlights"])
        project_blocks.append(f"- **{proj['name']}**: {highlights.strip()}")
    projects_block = "\n".join(project_blocks)

    skills_block = "\n".join(
        f"- **{cat['label']}:** {cat['details']}" for cat in s["skills"]
    )

    pub_lines = []
    for i, pub in enumerate(s["publications"], start=1):
        authors = ", ".join(a.replace("**", "") for a in pub["authors"])
        pub_lines.append(
            f"{i}. {authors} ({pub['date']}). {pub['title']}. "
            f"{pub['journal']}. {pub['doi']}"
        )
    publications_block = "\n".join(pub_lines)

    text = profile_path.read_text()
    text = _replace_marked(text, "IDENTITY", identity_block)
    text = _replace_marked(text, "EDUCATION", education_block)
    text = _replace_marked(text, "EXPERIENCE", experience_block)
    text = _replace_marked(text, "PROJECTS", projects_block)
    text = _replace_marked(text, "SKILLS", skills_block)
    text = _replace_marked(text, "PUBLICATIONS", publications_block)
    profile_path.write_text(text)
    print(f"Regenerated CV-derived sections in {profile_path}")
```

Also add the `profile` subcommand to the argparse block, replacing:
```python
    args = parser.parse_args()

    if args.cmd == "pdf":
        build_pdf(args.override)
```
with:
```python
    profile_p = sub.add_parser("profile", help="Regenerate 01-candidate-profile.md from cv.yaml")

    args = parser.parse_args()

    if args.cmd == "pdf":
        build_pdf(args.override)
    elif args.cmd == "profile":
        build_profile()
```
(Insert the `profile_p = sub.add_parser(...)` line directly after the existing `pdf_p = ...`
block, before `args = parser.parse_args()`.)

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd cv && uv run pytest tests/test_build.py -v
```
Expected: all tests pass, including the 3 new ones from Step 2. Pristine output.

- [ ] **Step 6: Run the full suite**

```bash
cd cv && uv run pytest -v
```
Expected: all tests across the file pass (11 total: 6 from Task 2 + 2 from Task 3 + 3 from this
task).

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/job-application-assistant/01-candidate-profile.md cv/build.py cv/tests/test_build.py
git commit -m "$(cat <<'EOF'
feat(cv): regenerate 01-candidate-profile.md CV sections from cv.yaml

Adds marker-delimited sections (Identity's CV fields, Education,
Experience, Projects, Skills, Publications) and a `build.py profile`
command that regenerates exactly those sections from cv.yaml, leaving
Behavioral Profile/Awards/References/Languages/Status/Constraints
untouched since cv.yaml has no equivalent for them.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `05-cv-templates.md` — RenderCV default + LaTeX moved to Legacy

**Files:**
- Modify: `.claude/skills/job-application-assistant/05-cv-templates.md` (full restructure)

**Interfaces:**
- Consumes: `cv/build.py pdf --override` (Task 2/3), the page-budget and relevance-weighted
  cutting guidance already in this file (unchanged prose, just relocated/kept at top level since
  it's renderer-agnostic).
- Produces: the trigger phrase documented here ("use the LaTeX template" / "use moderncv") is
  read by Task 6's edits to `job-application-assistant/SKILL.md` and `apply.md`.

- [ ] **Step 1: Read the current file**

Read `.claude/skills/job-application-assistant/05-cv-templates.md` in full — it is long (~260
lines) and this task restructures nearly all of it. Do not skip this read; the exact current text
is needed to construct accurate Edit calls, and pasting the full current content here would
duplicate ~260 lines without adding information the file itself doesn't already have.

- [ ] **Step 2: Replace the file header and add the RenderCV-default section**

Replace the first two lines:
```markdown
# CV Templates and Tailoring Guide

<!-- SETUP: Profile statements and section ordering are personalized by running /setup -->
```
with:
```markdown
# CV Templates and Tailoring Guide

<!-- SETUP: Profile statements and section ordering are personalized by running /setup -->

## Default renderer: RenderCV

**RenderCV is the default CV renderer. Use it unless the user explicitly asks for the LaTeX
template** (trigger phrases: "use the LaTeX template", "use moderncv", or similar explicit
requests — never ask "which renderer?" by default).

**Master data file:** `cv/cv.yaml` (all CV content — identity, education, experience, skills,
publications, projects; comprehensive reference, use as source when building targeted CVs)
**Per-company tailoring:** `cv/overrides/<company>.yaml` — only the fields that differ from
`cv.yaml` (profile statement, reordered/reworded highlights). Arrays are replaced wholesale, not
merged — override only the entries you want to change.
**Output file:** `cv/main_<company>.pdf` (the company segment is the override file's stem)
**Compile command:**

```bash
cd cv && uv run python build.py pdf --override overrides/<company>.yaml
```

Expected output: `Built main_<company>.pdf`. `cv/main_<company>.pdf` must exist afterward.

### Compile-and-Inspect Loop (MANDATORY, RenderCV)

1. Run the compile command above.
2. Read the PDF via the Read tool and visually inspect it.
3. Confirm the page count is exactly 2 (see "Page Budget" below — unchanged from the LaTeX path).
4. If it isn't, cut or restore content per "Relevance-weighted cutting" below (this guidance is
   renderer-agnostic — it applies identically whether the underlying engine is Typst or LaTeX).

### ATS Parseability (RenderCV)

Identical check to the LaTeX path — the output is still a PDF, and an ATS still reads its
embedded text layer, not the rendered page:

```bash
cd cv && pdftotext -layout main_<company>.pdf main_<company>.txt
```

Same checks apply: no `(cid:*)` markers or `�` characters, email/phone present as literal text,
reading order matches visual order, keyword coverage against the posting. See "ATS Parseability"
under the Legacy section below for the full checklist — it is unchanged, just also applies here.

### Photo

`cv.yaml`'s `photo:` field points at `cv_image.jpeg`. `build.py` automatically applies a circular
crop via a Typst post-processing patch — no manual step needed.
```

- [ ] **Step 3: Move the "Page Budget" and "Relevance-weighted cutting" sections up, unchanged**

These two sections (currently mid-file, under the LaTeX-specific content) apply identically to
RenderCV output. Locate the exact current text of the `## Page Budget - Hard 2-Page Limit` and
`## Relevance-weighted cutting (the right way to shrink a CV)` sections (read in Step 1) and move
them, byte-for-byte unchanged, to immediately after the new "Photo" subsection added in Step 2 —
before the `## Legacy: LaTeX/moderncv` heading created in Step 4. Do not reword their content;
this is a relocation, not a rewrite.

- [ ] **Step 4: Wrap all remaining LaTeX-specific content under a Legacy heading**

Immediately before the first LaTeX-specific heading remaining in the file (`## Template: LaTeX
moderncv (Banking Style)`), insert:
```markdown
## Legacy: LaTeX/moderncv (opt-in only)

**Use this only when the user explicitly asks for the LaTeX template** (e.g. "use the LaTeX
template", "use moderncv"). Everything below this point describes the LaTeX/moderncv path;
RenderCV (above) is the default for all other requests.
```
Everything from the original `## Template: LaTeX moderncv (Banking Style)` heading through the
end of the file (Document Structure, spacing pitfalls, Compile-and-Inspect Loop for LaTeX, ATS
Parseability for LaTeX, Recommended Section Order, etc.) stays exactly as it was — only this one
new heading is inserted above it. The "Page Budget" and "Relevance-weighted cutting" sections
moved in Step 3 must be **removed** from their original location here (they now live above,
shared by both renderers) — do not leave a duplicate copy.

- [ ] **Step 5: Verify the restructured file**

```bash
grep -n "^## " /home/magst/git/ai-job-search/.claude/skills/job-application-assistant/05-cv-templates.md
```
Expected order: `Default renderer: RenderCV` (as an `##`-level heading — adjust Step 2's heading
level if it renders as `##` differently than intended), `Page Budget - Hard 2-Page Limit`,
`Relevance-weighted cutting (the right way to shrink a CV)`, `Legacy: LaTeX/moderncv (opt-in
only)`, `Template: LaTeX moderncv (Banking Style)`, then the rest of the original LaTeX headings
in their original order, with no heading appearing twice.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/job-application-assistant/05-cv-templates.md
git commit -m "$(cat <<'EOF'
docs(cv-templates): make RenderCV the default, move LaTeX to Legacy

Page-budget and relevance-weighted-cutting guidance is renderer-
agnostic and now lives at the top level, shared by both paths. LaTeX
content is preserved verbatim under a new opt-in-only Legacy heading.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Operational docs — `SKILL.md`, `apply.md`, `CLAUDE.md`, `outcome.md`

**Files:**
- Modify: `.claude/skills/job-application-assistant/SKILL.md:30`
- Modify: `.claude/commands/apply.md` (CV section, compile command, ATS-check command, file list)
- Modify: `CLAUDE.md` (Verification Checklist, "Compiled PDF verification" section)
- Modify: `.claude/commands/outcome.md:61`

**Interfaces:**
- Consumes: the RenderCV compile/ATS commands from Task 5, the LaTeX trigger phrase documented
  there.

- [ ] **Step 1: `job-application-assistant/SKILL.md`**

Old:
```markdown
### Step 2: Tailor CV
- Read the most relevant existing CV variant from `cv/` as a starting point
- Follow the guidelines in `05-cv-templates.md`
- Create `cv/main_<company>.tex` with tailored content
- Adjust: profile statement, skills section, experience bullet emphasis, section order
```
New:
```markdown
### Step 2: Tailor CV
- Read `cv/cv.yaml` as the master data source (unless the user asked for the LaTeX template, in
  which case read the most relevant existing `cv/main_*.tex` variant instead)
- Follow the guidelines in `05-cv-templates.md`
- By default: create `cv/overrides/<company>.yaml` with only the tailored fields, then build
  `cv/main_<company>.pdf` via `cd cv && uv run python build.py pdf --override overrides/<company>.yaml`
- If the user explicitly asked for LaTeX: create `cv/main_<company>.tex` with tailored content instead
- Adjust: profile statement, skills section, experience bullet emphasis, section order
```

Also update the reference table row:
Old:
```markdown
| `05-cv-templates.md` | LaTeX CV structure and tailoring rules |
```
New:
```markdown
| `05-cv-templates.md` | CV structure and tailoring rules (RenderCV default, LaTeX legacy) |
```

- [ ] **Step 2: `apply.md` — CV section (Step 2)**

Old:
```markdown
Also read the most recent existing CV and cover letter files for concrete structural reference (one of each is enough):
- Read any existing `cv/main_*.tex` file as a LaTeX template reference
- Read any existing `cover_letters/cover_*.tex` or `cover_letters/Cover_*.tex` file as a template reference

### CV (`cv/main_<company>.tex`)
- Always in **English**
- Follow the moderncv/banking format from `05-cv-templates.md`
- Tailor the profile statement and experience bullets to the specific role
- Reframe skills and achievements to match job requirements
- Keep to 2 pages
```
New:
```markdown
Also read reference material for concrete structural reference:
- Read `cv/cv.yaml` (the master CV data) — unless the user explicitly asked for the LaTeX
  template, in which case read an existing `cv/main_*.tex` file instead
- Read any existing `cover_letters/cover_*.tex` or `cover_letters/Cover_*.tex` file as a template reference

### CV (`cv/overrides/<company>.yaml`, default — or `cv/main_<company>.tex` if LaTeX was requested)
- Always in **English**
- Default: write `cv/overrides/<company>.yaml` following the RenderCV guidance in
  `05-cv-templates.md`. Only if the user explicitly asked for LaTeX: follow the moderncv/banking
  format instead
- Tailor the profile statement and experience bullets to the specific role
- Reframe skills and achievements to match job requirements
- Keep to 2 pages
```

- [ ] **Step 3: `apply.md` — Step 5 header, compile command, and CV verification bullets**

Old header and prose:
```markdown
## Step 5: DRAFTER - Compile & Inspect PDFs (MANDATORY)

**Never skip this step.** The `.tex` files looking fine is not sufficient — LaTeX page-break decisions are unpredictable and commonly produce broken layouts (orphaned job titles separated from their bullets, cover letters spilling to 2 pages, bullet fonts not matching body text). Compile both documents and visually verify the PDFs before presenting.

### 5a. Compile

```bash
cd cv && lualatex -interaction=nonstopmode main_<company>.tex
cd ../cover_letters && xelatex -interaction=nonstopmode cover_<company>_<role>.tex
```

- CV uses **lualatex** — pdflatex fails on modern MiKTeX with fontawesome5 font-expansion errors. lualatex handles the same sources cleanly.
- Cover letter uses **xelatex** — cover.cls requires fontspec.

If either compile fails, fix the error and re-compile until clean.
```
New:
```markdown
## Step 5: DRAFTER - Compile & Inspect PDFs (MANDATORY)

**Never skip this step.** A source file looking fine is not sufficient — page-break decisions are
unpredictable and commonly produce broken layouts (orphaned job titles separated from their
bullets, cover letters spilling to 2 pages, bullet fonts not matching body text). Compile both
documents and visually verify the PDFs before presenting.

### 5a. Compile

```bash
cd cv && uv run python build.py pdf --override overrides/<company>.yaml
cd ../cover_letters && xelatex -interaction=nonstopmode cover_<company>_<role>.tex
```

- CV uses **RenderCV/Typst by default** — only use `lualatex -interaction=nonstopmode main_<company>.tex` on `cv/main_<company>.tex` if the user explicitly requested the LaTeX template.
- Cover letter uses **xelatex** — cover.cls requires fontspec (cover letters are unaffected by the CV renderer choice).

If either compile fails, fix the error and re-compile until clean.
```

- [ ] **Step 4: `apply.md` — 5d ATS extraction command**

Old:
```markdown
```bash
cd cv && pdftotext -layout main_<company>.pdf main_<company>.txt
```
```
New:
```markdown
```bash
cd cv && pdftotext -layout main_<company>.pdf main_<company>.txt
```

(Same command regardless of renderer — both RenderCV and LaTeX produce `cv/main_<company>.pdf`.)
```

- [ ] **Step 5: `apply.md` — Step 6 file list**

Old:
```markdown
### Files Created
List the files written:
- `cv/main_<company>.tex`
- `cover_letters/cover_<company>_<role>.tex`
```
New:
```markdown
### Files Created
List the files written:
- `cv/overrides/<company>.yaml` and `cv/main_<company>.pdf` (default), or `cv/main_<company>.tex`
  and its compiled `.pdf` if the user requested the LaTeX template
- `cover_letters/cover_<company>_<role>.tex`
```

- [ ] **Step 6: `CLAUDE.md` — Verification Checklist, "Compiled PDF verification" section**

Old:
```markdown
- [ ] CV compiled with **lualatex** (pdflatex often fails on modern MiKTeX with fontawesome5 font-expansion errors). Cover letter compiled with **xelatex** (cover.cls requires fontspec).
```
New:
```markdown
- [ ] CV built via **RenderCV** by default (`cd cv && uv run python build.py pdf --override cv/overrides/<company>.yaml`); LaTeX/**lualatex** only if the user explicitly requested the LaTeX template (pdflatex often fails on modern MiKTeX with fontawesome5 font-expansion errors on that legacy path). Cover letter compiled with **xelatex** (cover.cls requires fontspec) — unaffected by the CV renderer choice.
```

- [ ] **Step 7: `outcome.md:61` — archival fallback lookup**

Old:
```markdown
1. **`cv_draft.tex` and `cover_letter.tex`** - copy (never move) the submitted files. Locate them via the tracker row's `cv_file`/`cover_letter_file` columns; if those are empty, look for `cv/main_<company>.tex` and `cover_letters/cover_<company>_*.tex`. If a file already exists in the archive, leave it - the archived version is what was actually submitted. If no draft files exist (application made outside `/apply`), skip with a note.
```
New:
```markdown
1. **`cv_draft` and `cover_letter.tex`** - copy (never move) the submitted files. Locate them via the tracker row's `cv_file`/`cover_letter_file` columns; if those are empty, look for `cv/overrides/<company>.yaml` (RenderCV, the default) or `cv/main_<company>.tex` (if LaTeX was used), plus `cover_letters/cover_<company>_*.tex`. If a file already exists in the archive, leave it - the archived version is what was actually submitted. If no draft files exist (application made outside `/apply`), skip with a note.
```

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/job-application-assistant/SKILL.md .claude/commands/apply.md CLAUDE.md .claude/commands/outcome.md
git commit -m "$(cat <<'EOF'
docs: point the /apply workflow at RenderCV by default

SKILL.md, apply.md, CLAUDE.md's verification checklist, and outcome.md's
archival fallback all now instruct/expect the RenderCV build by default,
with the LaTeX path preserved as an explicit-request fallback.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Onboarding docs — `setup.md` and `README.md`

**Files:**
- Modify: `.claude/commands/setup.md:225`, `:354-355`, `:377-384`
- Modify: `README.md` (Prerequisites, File structure, How `/apply` works, LaTeX templates section)

**Interfaces:**
- Consumes: `cv/cv.yaml` (Task 1), `build.py profile` (Task 4), the RenderCV compile command
  (Task 5).

- [ ] **Step 1: `setup.md` — Step 3 pointer and item 7**

Old:
```markdown
Then proceed to Step 3 to populate the non-skill files (`CLAUDE.md`, `cv/main_example.tex`, `.claude/skills/job-scraper/search-queries.md`). Step 3 will detect that the seven skill files are already populated and skip those substeps.
```
New:
```markdown
Then proceed to Step 3 to populate the non-skill files (`CLAUDE.md`, `cv/cv.yaml`,
`.claude/skills/job-scraper/search-queries.md`). Step 3 will detect that the seven skill files are
already populated and skip those substeps.
```

Old:
```markdown
### 7. Update `cv/main_example.tex`
Replace placeholder personal data with their actual name, contact info, and add their education and most recent experience entries.
```
New:
```markdown
### 7. Update `cv/cv.yaml`
Replace placeholder personal data with their actual name, contact info, education, and experience
entries (this is the RenderCV master data file — the default renderer). After populating it, run
`cd cv && uv run python build.py profile` to regenerate the matching sections of
`01-candidate-profile.md`. Only populate `cv/main_example.tex` (the legacy LaTeX template)
instead if the user has indicated they want to use the LaTeX path.
```

- [ ] **Step 2: `setup.md` — Step 4 confirmation summary**

Old:
```markdown
> - `cv/main_example.tex` - Your LaTeX CV template
```
New:
```markdown
> - `cv/cv.yaml` - Your RenderCV CV data (default renderer)
```

- [ ] **Step 3: `README.md` — Prerequisites**

Old:
```markdown
- LaTeX distribution with `lualatex` and `xelatex`: [TeX Live](https://tug.org/texlive/) or [MiKTeX](https://miktex.org/). The CV compiles with `lualatex` (pdflatex often fails on modern MiKTeX installs with `fontawesome5` font-expansion errors); the cover letter compiles with `xelatex` because `cover.cls` requires `fontspec`.
```
New:
```markdown
- [uv](https://docs.astral.sh/uv/) — runs the default CV renderer (`cd cv && uv sync` installs `rendercv[full]`, which bundles the Typst compiler).
- A LaTeX distribution with `xelatex` (needed for the cover letter, which always uses `cover.cls`/XeLaTeX regardless of CV renderer choice): [TeX Live](https://tug.org/texlive/) or [MiKTeX](https://miktex.org/). `lualatex` is only needed if you explicitly opt into the legacy LaTeX CV template (pdflatex often fails on modern MiKTeX installs with `fontawesome5` font-expansion errors on that path).
```

- [ ] **Step 4: `README.md` — File structure tree**

Old:
```markdown
├── cv/
│   └── main_example.tex               # moderncv LaTeX template
```
New:
```markdown
├── cv/
│   ├── cv.yaml                        # RenderCV master CV data (default renderer)
│   ├── build.py                       # RenderCV -> Typst PDF build script
│   ├── overrides/                     # Per-company tailored YAML overrides
│   └── main_example.tex               # moderncv LaTeX template (legacy, opt-in only)
```

- [ ] **Step 5: `README.md` — "How `/apply` works", step 6**

Old:
```markdown
6. **Compile and inspect** both PDFs: lualatex for the CV, xelatex for the cover letter. Claude reads the rendered pages and iterates on the LaTeX until the CV is exactly 2 pages with no orphaned entry titles, and the cover letter is exactly 1 page with the signature visible and fonts consistent.
```
New:
```markdown
6. **Compile and inspect** both PDFs: RenderCV/Typst for the CV by default (LaTeX only if
   explicitly requested), xelatex for the cover letter. Claude reads the rendered pages and
   iterates until the CV is exactly 2 pages with no orphaned entry titles, and the cover letter is
   exactly 1 page with the signature visible and fonts consistent.
```

- [ ] **Step 6: `README.md` — "LaTeX templates" section**

Old:
```markdown
### LaTeX templates

The CV uses [moderncv](https://ctan.org/pkg/moderncv) (banking style). The cover letter uses a custom `cover.cls` with Lato/Raleway fonts.
```
New:
```markdown
### CV renderer and templates

The CV is built by default via [RenderCV](https://rendercv.com)/Typst from `cv/cv.yaml` — see
`cv/build.py` and `.claude/skills/job-application-assistant/05-cv-templates.md`. A legacy
[moderncv](https://ctan.org/pkg/moderncv) (banking style) LaTeX template is still available;
ask for it explicitly (e.g. "use the LaTeX template") if you prefer it. The cover letter always
uses a custom `cover.cls` with Lato/Raleway fonts, regardless of which CV renderer is active.
```

- [ ] **Step 7: Commit**

```bash
git add .claude/commands/setup.md README.md
git commit -m "$(cat <<'EOF'
docs: update onboarding docs (setup.md, README.md) for RenderCV default

/setup now populates cv/cv.yaml instead of cv/main_example.tex by
default, and the README's prerequisites/file-structure/customization
sections describe RenderCV as the default CV renderer with LaTeX as
an explicit opt-in.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review Notes (for the plan author, not a task)

**Spec coverage:** File layout (Task 1) ✓, build script behavior incl. output naming (Task 2/3) ✓,
cv.yaml/01-candidate-profile.md data flow (Task 4) ✓, fallback trigger phrase documented (Task 5,
consumed by Task 6) ✓, all 7 files from the spec's integration list updated (05-cv-templates.md
Task 5; SKILL.md/apply.md/CLAUDE.md/outcome.md Task 6; setup.md/README.md Task 7) ✓. Non-goals
(cover letters, add-template.md) not touched by any task ✓.

**Placeholder scan:** no TBD/TODO; every step shows exact before/after text or complete code.

**Type/name consistency:** `deep_merge`, `_output_stem`, `build_pdf` (Task 2) → consumed as-named
by Task 3's tests and Task 4's shared file. `_replace_marked`, `build_profile` (Task 4) use the
same marker-name strings (`IDENTITY`, `EDUCATION`, `EXPERIENCE`, `PROJECTS`, `SKILLS`,
`PUBLICATIONS`) in both the inserted `01-candidate-profile.md` comments (Step 1) and the
`build_profile()` code (Step 4) — verified matching in both places above.
