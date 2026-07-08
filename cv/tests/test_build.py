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
