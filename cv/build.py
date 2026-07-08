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
