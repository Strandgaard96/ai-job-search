# CV Protected Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `build.py validate` subcommand that fails when a per-company CV override cuts or rewords content locked in `cv/protected.yaml` (starting with `publications` and `projects`), and wire it into `/apply` and the docs so it's a hard gate instead of a thing a drafter can forget.

**Architecture:** A new `cv/protected.yaml` declares which `cv.yaml` sections are `no_cut` / `no_reword`. `build.py` gains pure comparison functions (`_entry_key`, `find_violations`) plus a `validate` CLI subcommand that loads master + override + protected config and reports mismatches. `.claude/commands/apply.md`, `05-cv-templates.md`, and `CLAUDE.md` are updated to call this gate and document it.

**Tech Stack:** Python 3.12, PyYAML, pytest (existing `cv/` project, `uv run` for execution).

## Global Constraints

- `cv/protected.yaml` is never merged into the RenderCV input — `build_pdf()` must not read it. RenderCV's schema only tolerates the `cv:`/`design:` top-level keys already present in `cv.yaml`.
- Only whole-section locking is in scope. No per-item (bullet-level) locking.
- Default `cv/protected.yaml` locks only `publications` (no_cut) and `projects` (no_cut, no_reword). `experience` and `skills` are never locked by default — tailoring those is the point of `/apply`.
- All new tests follow the existing plain-pytest style in `cv/tests/test_build.py` (no fixtures/mocks framework).
- Exit code contract: `build.py validate` exits `0` and prints `OK` when clean, exits `1` and prints violations to stderr when not.

---

### Task 1: `protected.yaml` + match-key and violation-finding logic

**Files:**
- Create: `cv/protected.yaml`
- Modify: `cv/build.py` (insert after `build_profile()`, i.e. after line 177, before the `if __name__ == "__main__":` block at line 180)
- Test: `cv/tests/test_build.py` (append)

**Interfaces:**
- Consumes: nothing new (plain dicts loaded from YAML by the caller).
- Produces:
  - `SECTION_MATCH_FIELDS: dict[str, tuple[str, ...]]` — module-level constant in `build.py`.
  - `_entry_key(section: str, entry) -> tuple` — function in `build.py`. Returns a hashable identity for one entry within a section.
  - `find_violations(master: dict, override: dict, protected: dict) -> list[str]` — function in `build.py`. Returns a list of human-readable violation strings (empty list = compliant).

- [ ] **Step 1: Write the failing tests**

Append to `cv/tests/test_build.py`:

```python
# ── protected content ──────────────────────────────────────────────────────

def _sample_master():
    return {
        "cv": {
            "sections": {
                "publications": [
                    {"title": "Paper A", "doi": "10.1/a", "journal": "J1", "date": "2024"},
                    {"title": "Paper B", "doi": "10.1/b", "journal": "J2", "date": "2023"},
                ],
                "projects": [
                    {"name": "Homelab", "highlights": ["Runs Proxmox."]},
                ],
                "experience": [
                    {"company": "Acme", "position": "Engineer", "start_date": "2025",
                     "end_date": "present", "highlights": ["Did a thing."]},
                ],
            }
        }
    }


def test_find_violations_no_cut_detects_missing_entry():
    from build import find_violations
    master = _sample_master()
    override = {
        "cv": {
            "sections": {
                "publications": [
                    {"title": "Paper A", "doi": "10.1/a", "journal": "J1", "date": "2024"},
                ]
            }
        }
    }
    protected = {"no_cut": ["publications"]}
    violations = find_violations(master, override, protected)
    assert len(violations) == 1
    assert "no_cut" in violations[0]
    assert "publications" in violations[0]


def test_find_violations_no_reword_detects_changed_entry():
    from build import find_violations
    master = _sample_master()
    override = {
        "cv": {
            "sections": {
                "projects": [
                    {"name": "Homelab", "highlights": ["Runs Proxmox and more."]},
                ]
            }
        }
    }
    protected = {"no_reword": ["projects"]}
    violations = find_violations(master, override, protected)
    assert len(violations) == 1
    assert "no_reword" in violations[0]
    assert "projects" in violations[0]


def test_find_violations_section_untouched_by_override_passes():
    from build import find_violations
    master = _sample_master()
    override = {"cv": {"sections": {"experience": master["cv"]["sections"]["experience"]}}}
    protected = {"no_cut": ["publications"], "no_reword": ["projects"]}
    assert find_violations(master, override, protected) == []


def test_find_violations_section_present_and_compliant_passes():
    from build import find_violations
    master = _sample_master()
    override = {
        "cv": {
            "sections": {
                "publications": list(master["cv"]["sections"]["publications"]),
                "projects": list(master["cv"]["sections"]["projects"]),
            }
        }
    }
    protected = {"no_cut": ["publications"], "no_reword": ["projects"]}
    assert find_violations(master, override, protected) == []


def test_find_violations_new_entry_not_in_master_is_not_reword_violation():
    from build import find_violations
    master = _sample_master()
    override = {
        "cv": {
            "sections": {
                "projects": [
                    {"name": "Homelab", "highlights": ["Runs Proxmox."]},
                    {"name": "New Side Project", "highlights": ["Brand new."]},
                ]
            }
        }
    }
    protected = {"no_reword": ["projects"]}
    assert find_violations(master, override, protected) == []


def test_entry_key_publications_falls_back_to_title_without_doi():
    from build import _entry_key
    assert _entry_key("publications", {"title": "No DOI Paper"}) == ("No DOI Paper",)


def test_entry_key_string_entry_used_as_its_own_key():
    from build import _entry_key
    assert _entry_key("summary", "Some summary text.") == ("Some summary text.",)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd cv && uv run pytest tests/test_build.py -k "find_violations or entry_key" -v
```

Expected: all new tests FAIL with `ImportError: cannot import name 'find_violations'` (or `_entry_key`) — neither function exists in `build.py` yet.

- [ ] **Step 3: Implement `SECTION_MATCH_FIELDS`, `_entry_key`, `find_violations`**

Insert into `cv/build.py` after `build_profile()` (after line 177), before `if __name__ == "__main__":`:

```python
SECTION_MATCH_FIELDS = {
    "publications": ("doi", "title"),
    "experience": ("company", "position", "start_date"),
    "projects": ("name",),
    "skills": ("label",),
    "education": ("institution", "degree", "start_date"),
}


def _entry_key(section: str, entry) -> tuple:
    """Stable identity for one section entry, for matching across master/override."""
    if isinstance(entry, str):
        return (entry,)
    if section == "publications":
        return (entry.get("doi") or entry.get("title"),)
    fields = SECTION_MATCH_FIELDS.get(section)
    if fields is None:
        raise ValueError(f"no match key defined for section '{section}'")
    return tuple(entry.get(f) for f in fields)


def find_violations(master: dict, override: dict, protected: dict) -> list[str]:
    """Check an override against protected.yaml's no_cut/no_reword locks. Returns violation strings."""
    violations = []
    master_sections = master.get("cv", {}).get("sections", {})
    override_sections = override.get("cv", {}).get("sections", {})

    for section in protected.get("no_cut", []):
        if section not in override_sections:
            continue
        master_entries = master_sections.get(section, [])
        override_entries = override_sections.get(section, [])
        master_keys = {_entry_key(section, e) for e in master_entries}
        override_keys = {_entry_key(section, e) for e in override_entries}
        missing = master_keys - override_keys
        if missing:
            violations.append(f"no_cut: {section} missing entries: {sorted(missing)}")

    for section in protected.get("no_reword", []):
        if section not in override_sections:
            continue
        master_entries = master_sections.get(section, [])
        override_entries = override_sections.get(section, [])
        master_by_key = {_entry_key(section, e): e for e in master_entries}
        for entry in override_entries:
            key = _entry_key(section, entry)
            master_entry = master_by_key.get(key)
            if master_entry is not None and master_entry != entry:
                violations.append(f"no_reword: {section} entry {key} differs from master")

    return violations
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd cv && uv run pytest tests/test_build.py -k "find_violations or entry_key" -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Create `cv/protected.yaml`**

```yaml
no_cut:
  - publications
  - projects
no_reword:
  - projects
```

- [ ] **Step 6: Commit**

```bash
git add cv/build.py cv/tests/test_build.py cv/protected.yaml
git commit -m "feat(cv): add protected-content violation detection"
```

---

### Task 2: `validate` CLI subcommand

**Files:**
- Modify: `cv/build.py:180-196` (the `if __name__ == "__main__":` block, plus a new `validate()` function placed just above it)
- Test: `cv/tests/test_build.py` (append)

**Interfaces:**
- Consumes: `find_violations(master, override, protected)` from Task 1.
- Produces: `validate(override_path: pathlib.Path) -> int` — loads `cv.yaml`, `protected.yaml` (if present), and the given override, prints `OK` or the violations, returns an exit code (`0` or `1`). Also produces the `validate` argparse subcommand, invoked as `uv run python build.py validate --override overrides/<company>.yaml`.

- [ ] **Step 1: Write the failing test**

Append to `cv/tests/test_build.py`:

```python
def test_validate_returns_zero_and_prints_ok_when_compliant(capsys):
    import build
    import pathlib as _pathlib

    override_path = _pathlib.Path("overrides/_test_validate_ok.yaml")
    override_path.write_text('cv:\n  sections:\n    experience: []\n')
    try:
        code = build.validate(override_path)
        assert code == 0
        assert "OK" in capsys.readouterr().out
    finally:
        override_path.unlink(missing_ok=True)


def test_validate_returns_one_and_prints_violation_when_publication_dropped(capsys):
    import build
    import pathlib as _pathlib

    override_path = _pathlib.Path("overrides/_test_validate_bad.yaml")
    override_path.write_text(
        'cv:\n  sections:\n    publications:\n      - title: "Only One Kept"\n        doi: "10.0/x"\n'
    )
    try:
        code = build.validate(override_path)
        assert code == 1
        assert "no_cut" in capsys.readouterr().err
    finally:
        override_path.unlink(missing_ok=True)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd cv && uv run pytest tests/test_build.py -k "test_validate_returns" -v
```

Expected: FAIL with `AttributeError: module 'build' has no attribute 'validate'`.

- [ ] **Step 3: Implement `validate()` and wire the subcommand**

Insert into `cv/build.py` directly above `if __name__ == "__main__":` (i.e. right after the `find_violations` function from Task 1):

```python
def validate(override_path: pathlib.Path) -> int:
    """Check an override against cv/protected.yaml. Returns 0 if clean, 1 if violations found."""
    master = yaml.safe_load(pathlib.Path("cv.yaml").read_text())
    protected_path = pathlib.Path("protected.yaml")
    protected = yaml.safe_load(protected_path.read_text()) if protected_path.exists() else {}
    override = yaml.safe_load(override_path.read_text())

    violations = find_violations(master, override, protected)
    if violations:
        for v in violations:
            print(v, file=sys.stderr)
        return 1
    print("OK")
    return 0
```

Replace the existing `if __name__ == "__main__":` block (currently lines 180-196) with:

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a CV PDF from cv.yaml via RenderCV.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pdf_p = sub.add_parser("pdf", help="Generate main_<company>.pdf via RenderCV")
    pdf_p.add_argument("--override", type=pathlib.Path, default=None,
                        help="Override YAML (e.g. overrides/netcompany.yaml)")

    profile_p = sub.add_parser("profile", help="Regenerate 01-candidate-profile.md from cv.yaml")

    validate_p = sub.add_parser("validate", help="Check an override against cv/protected.yaml locks")
    validate_p.add_argument("--override", type=pathlib.Path, required=True,
                             help="Override YAML to validate (e.g. overrides/dnv.yaml)")

    args = parser.parse_args()

    if args.cmd == "pdf":
        build_pdf(args.override)
    elif args.cmd == "profile":
        build_profile()
    elif args.cmd == "validate":
        sys.exit(validate(args.override))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd cv && uv run pytest tests/test_build.py -k "test_validate_returns" -v
```

Expected: both tests PASS.

- [ ] **Step 5: Run the full test suite**

```bash
cd cv && uv run pytest tests/test_build.py -v
```

Expected: all tests (existing + new) PASS.

- [ ] **Step 6: Smoke-test against the real `dnv.yaml` override**

```bash
cd cv && uv run python build.py validate --override overrides/dnv.yaml
```

Expected: `OK` printed, exit code 0 (the DNV override was already fixed to keep all 4 publications and its project entries untouched earlier in this project's history — this is a positive-control check, not new work).

- [ ] **Step 7: Commit**

```bash
git add cv/build.py cv/tests/test_build.py
git commit -m "feat(cv): add 'build.py validate' subcommand"
```

---

### Task 3: Wire the gate into `/apply`, `05-cv-templates.md`, `CLAUDE.md`

**Files:**
- Modify: `.claude/commands/apply.md` (Step 4 section)
- Modify: `.claude/skills/job-application-assistant/05-cv-templates.md` ("Relevance-weighted cutting" section)
- Modify: `CLAUDE.md` (Verification Checklist, Quality subsection)

**Interfaces:**
- Consumes: `uv run python build.py validate --override overrides/<company>.yaml` (Task 2's CLI, exit code `0`/`1`).
- Produces: nothing new for later tasks — this is the last task in this plan.

- [ ] **Step 1: Update `.claude/commands/apply.md` Step 4**

Find the "Step 4: DRAFTER - Revise Based on Feedback" section. After its numbered list (which ends with `3. Do NOT incorporate any suggestion that would fabricate...`), add:

```markdown
4. **Run the protected-content gate:**
   ```bash
   cd cv && uv run python build.py validate --override overrides/<company>.yaml
   ```
   If it exits non-zero, the override has cut or reworded content locked in `cv/protected.yaml`
   (by default: publications, projects). Either restore the flagged content, or — if the cut is
   genuinely intentional for this posting — ask the user to confirm before proceeding. Never pass
   a violation through silently. Re-run until it prints `OK`.
```

- [ ] **Step 2: Update `05-cv-templates.md`**

Find the "Relevance-weighted cutting" section, immediately after its introductory paragraph (the one starting "**Cut by signal, not by section.**"). Add:

```markdown
**Protected sections are exempt.** Sections listed in `cv/protected.yaml`'s `no_cut` list
(publications and projects, by default) are never candidates for the lowest-score cut, no matter
how low they score on relevance to the current posting. `build.py validate --override
overrides/<company>.yaml` enforces this — run it after any cut and fix any violation before
compiling.
```

- [ ] **Step 3: Update `CLAUDE.md`**

Find the Verification Checklist's "### Quality" subsection. After the line `- [ ] No syntax errors in the CV source...`, add:

```markdown
- [ ] Protected-content validation passes (`cd cv && uv run python build.py validate --override overrides/<company>.yaml` prints `OK`)
```

- [ ] **Step 4: Verify the docs changes render sensibly**

```bash
grep -n "build.py validate" .claude/commands/apply.md .claude/skills/job-application-assistant/05-cv-templates.md CLAUDE.md
```

Expected: one match in each of the three files.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/apply.md .claude/skills/job-application-assistant/05-cv-templates.md CLAUDE.md
git commit -m "docs: wire protected-content validation into /apply and verification checklist"
```
