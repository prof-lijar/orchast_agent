#!/usr/bin/env python3
"""Render a Markdown paper into an IEEE-style two-column PDF via WeasyPrint.

Usage:
    book-writer/.venv/bin/python build_pdf.py paper.md -o outdir/ [--slug name]

Expects the Markdown file to start with YAML front matter:
    ---
    title: "..."
    authors: "A, B"
    affiliation: "..."   # optional
    date: "Month Year"   # optional
    keywords: "a, b, c"  # optional
    ---
followed by `## Abstract`, numbered body sections as `##`/`###`, and a final
`## References` section. Section numbering (I., II., ... / A., B., ...) is
applied by CSS counters; Abstract and References stay unnumbered.
"""

import argparse
import re
import sys
from pathlib import Path

import markdown
from weasyprint import HTML

try:
    import latex2mathml.converter as l2m
except ImportError:  # math becomes literal text
    l2m = None

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MD_EXTENSIONS = ["extra", "codehilite"]


def parse_front_matter(text):
    meta = {}
    m = FRONT_MATTER_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"')
        text = text[m.end():]
    return meta, text


def convert_math(text):
    """Replace $$...$$ and $...$ with MathML, mirroring book-writer's publisher."""
    if l2m is None:
        return text

    def repl(m, display):
        try:
            return l2m.convert(m.group(1), display="block" if display else "inline")
        except Exception:
            return m.group(0)

    text = re.sub(r"\$\$(.+?)\$\$", lambda m: repl(m, True), text, flags=re.DOTALL)
    text = re.sub(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", lambda m: repl(m, False), text)
    return text


def split_abstract(body_md):
    """Pull the '## Abstract' section out of the body Markdown."""
    m = re.search(r"^## Abstract\s*\n(.*?)(?=^## )", body_md, re.MULTILINE | re.DOTALL)
    if not m:
        return "", body_md
    return m.group(1).strip(), body_md[: m.start()] + body_md[m.end():]


def next_version_path(outdir, slug):
    versions = [
        int(m.group(1))
        for p in outdir.glob(f"{slug}-v*.pdf")
        if (m := re.fullmatch(rf"{re.escape(slug)}-v(\d+)", p.stem))
    ]
    return outdir / f"{slug}-v{max(versions, default=0) + 1}.pdf"


def build_html(meta, abstract_md, body_md):
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    abstract_html = md.convert(convert_math(abstract_md))
    md.reset()
    body_html = md.convert(convert_math(body_md))
    # Keep References out of the section-numbering counter.
    body_html = re.sub(
        r"<h2([^>]*)>(\s*References\s*)</h2>",
        r'<h2\1 class="unnumbered">\2</h2>',
        body_html,
        flags=re.IGNORECASE,
    )

    authors = " · ".join(a.strip() for a in meta.get("authors", "").split(","))
    affiliation = meta.get("affiliation", "")
    date = meta.get("date", "")
    keywords = meta.get("keywords", "")

    css_path = Path(__file__).resolve().parent.parent / "assets" / "ieee.css"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{meta.get("title", "Paper")}</title>
<style>{css_path.read_text(encoding="utf-8")}</style>
</head><body>
<header class="titleblock">
  <h1 class="paper-title">{meta.get("title", "")}</h1>
  <p class="paper-authors">{authors}</p>
  {f'<p class="paper-affiliation">{affiliation}</p>' if affiliation else ""}
  {f'<p class="paper-date">{date}</p>' if date else ""}
</header>
<div class="paper-body">
<section class="abstract">
  <p class="abstract-head">Abstract</p>
  {abstract_html}
  {f'<p class="keywords"><em>Index Terms</em>—{keywords}</p>' if keywords else ""}
</section>
{body_html}
</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="paper Markdown file")
    ap.add_argument("-o", "--outdir", type=Path, default=None,
                    help="output directory (default: input's directory)")
    ap.add_argument("--slug", default=None, help="output file slug")
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    if not meta.get("title"):
        sys.exit("error: front matter must define a title")
    abstract, body = split_abstract(body)

    slug = args.slug or re.sub(r"[^a-z0-9]+", "-", meta["title"].lower()).strip("-")[:60]
    outdir = args.outdir or args.input.parent
    outdir.mkdir(parents=True, exist_ok=True)
    out = next_version_path(outdir, slug)

    HTML(string=build_html(meta, abstract, body)).write_pdf(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
