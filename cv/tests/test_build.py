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
