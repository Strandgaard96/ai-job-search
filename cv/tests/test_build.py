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
