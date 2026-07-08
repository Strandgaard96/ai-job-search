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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a CV PDF from cv.yaml via RenderCV.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pdf_p = sub.add_parser("pdf", help="Generate main_<company>.pdf via RenderCV")
    pdf_p.add_argument("--override", type=pathlib.Path, default=None,
                        help="Override YAML (e.g. overrides/netcompany.yaml)")

    profile_p = sub.add_parser("profile", help="Regenerate 01-candidate-profile.md from cv.yaml")

    args = parser.parse_args()

    if args.cmd == "pdf":
        build_pdf(args.override)
    elif args.cmd == "profile":
        build_profile()
