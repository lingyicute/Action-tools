#!/usr/bin/env python3
"""
Nebulove font subsetter & embedder.
"""

from __future__ import annotations

import argparse
import base64
import html as html_module
import io
import os
import re
import sys
import urllib.request
from pathlib import Path

FONT_URL = "https://raw.githubusercontent.com/lingyicute/Nebulove/main/Nebulove.ttf"
FALLBACK_URL = "https://cdn.jsdelivr.net/gh/lingyicute/Nebulove@main/Nebulove.ttf"
DEFAULT_HTML = "downloader-introduce/index.html"
FONT_FAMILY = "Nebulove"

# Same charset the 92li script guarantees, minus the redundant entries.
EXTRA_CHARS = "：，。！？；“”‘’（）【】—…·《》×＝÷＋－"

FONT_FACE_RE = re.compile(r"@font-face\s*\{[^}]*\}", re.IGNORECASE | re.DOTALL)
ENTITY_RE = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]{1,31}|#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6});")
CSS_ESCAPE_RE = re.compile(r"\\([0-9A-Fa-f]{2,6})\s?")
# lets a page pin characters that live outside its own markup, e.g. text typed
# by the user at runtime:  <!-- subset:extra 校验拆与 -->
EXTRA_DIRECTIVE_RE = re.compile(r"<!--\s*subset:extra\s+([^>]*?)\s*-->", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def collect_chars(document: str, extra: str = "") -> set[str]:
    """Every character the page may need a glyph for."""
    chars: set[str] = set(document)

    # full printable ASCII (32..126)
    chars.update(chr(c) for c in range(32, 127))

    # common CJK punctuation, kept from the 92li script
    chars.update(EXTRA_CHARS)
    chars.update(extra)

    # characters written as HTML entities: &amp; &mdash; &#8250; &#x2192; ...
    for entity in ENTITY_RE.findall(document):
        decoded = html_module.unescape(entity)
        if decoded != entity:
            chars.update(decoded)

    # characters written as CSS escapes: content:"\2713" / "\00d7"
    for hexdigits in CSS_ESCAPE_RE.findall(document):
        try:
            chars.add(chr(int(hexdigits, 16)))
        except ValueError:  # out of Unicode range
            pass

    # declarative extras: <!-- subset:extra ... -->
    for block in EXTRA_DIRECTIVE_RE.findall(document):
        chars.update(block.strip())

    chars.discard("\n")
    chars.discard("\r")
    return chars


def download_font(url: str) -> bytes:
    print(f"Downloading font from {url} ...")
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 (trusted, fixed URL)
        data = resp.read()
    if len(data) < 1024:
        raise RuntimeError(f"Downloaded font looks truncated ({len(data)} bytes)")
    return data


def subset_font(source: bytes, text: str) -> bytes:
    """Subset the font to `text` and return WOFF2 bytes."""
    from fontTools.ttLib import TTFont
    from fontTools.subset import Options, Subsetter

    options = Options()
    options.recalc_timestamp = False  # (CLI default too, kept explicit)
    if "FFTM" not in options.drop_tables:
        options.drop_tables.append("FFTM")  # FontForge timestamp table, noise only

    # TTFont defaults to recalcTimestamp=True, which stamps head.modified with
    # "now" on save: every run would emit different bytes even when nothing
    # changed, and CI would commit a new subset on every push. Keep the output
    # byte-for-byte reproducible instead — `--check` depends on it.
    font = TTFont(io.BytesIO(source), recalcTimestamp=False)
    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff2"

    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def build_font_face(b64: str, indent: str = "") -> str:
    """The inline `@font-face` rule (inline first, CDN fallback second)."""
    pad = indent
    return (
        f"{pad}@font-face {{\n"
        f"{pad}    font-family: '{FONT_FAMILY}';\n"
        f"{pad}    src: url('data:font/woff2;charset=utf-8;base64,{b64}') format('woff2'),\n"
        f"{pad}         url('{FALLBACK_URL}') format('truetype');\n"
        f"{pad}    font-weight: normal;\n"
        f"{pad}    font-style: normal;\n"
        f"{pad}    font-display: swap;\n"
        f"{pad}}}"
    )


def replace_font_face(document: str, font_face_css: str) -> tuple[str, str]:
    """
    Swap the page's Nebulove `@font-face` for the subset one.
    Returns (new_document, action) where action is one of
    'replaced' | 'inserted' | 'unchanged'.
    """
    for match in FONT_FACE_RE.finditer(document):
        block = match.group(0)
        if FONT_FAMILY.lower() in block.lower():
            indent = re.search(r"[ \t]*(?=@font-face)", document[: match.start()]) or re.match(r"", "")
            indent = (indent.group(0).splitlines() or [""])[-1]
            new_document = document[: match.start()] + font_face_css + document[match.end() :]
            return new_document, ("unchanged" if new_document == document else "replaced")

    # no Nebulove rule yet: inject one at the end of <head>
    if "</head>" not in document:
        raise RuntimeError("Could not find </head> to insert the @font-face rule into")
    rule = f"<style>\n{font_face_css}\n</style>\n"
    new_document = document.replace("</head>", rule + "</head>", 1)
    return new_document, "inserted"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Subset Nebulove and inline it into an HTML page.")
    parser.add_argument(
        "--html",
        default=os.environ.get("SUBSET_HTML", DEFAULT_HTML),
        help=f"target page (default: {DEFAULT_HTML}, or $SUBSET_HTML)",
    )
    parser.add_argument(
        "--font-url",
        default=os.environ.get("SUBSET_FONT_URL", FONT_URL),
        help="source TTF/WOFF2 to subset (default: Nebulove from GitHub)",
    )
    parser.add_argument(
        "--extra-chars",
        default=os.environ.get("SUBSET_EXTRA_CHARS", ""),
        help="additional characters to keep (e.g. text typed at runtime); "
        "the page can also declare them via <!-- subset:extra ... -->",
    )
    parser.add_argument("--check", action="store_true", help="exit 1 if the page is out of date; write nothing")
    parser.add_argument("--quiet", action="store_true", help="only report errors")
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log = (lambda *a: None) if args.quiet else print

    html_path = Path(args.html)
    if not html_path.exists():
        print(f"Error: {html_path} not found.", file=sys.stderr)
        return 1

    log(f"Reading {html_path} ...")
    document = html_path.read_text(encoding="utf-8")

    chars = collect_chars(document, args.extra_chars)
    log(f"Total unique characters needed: {len(chars)}")

    font_bytes = download_font(args.font_url)
    log(f"Source font: {len(font_bytes):,} bytes")

    try:
        woff2 = subset_font(font_bytes, "".join(sorted(chars)))
    except ImportError as exc:  # pragma: no cover
        print(f"Error: missing dependency ({exc}). Run: pip install fonttools brotli", file=sys.stderr)
        return 1

    ratio = len(woff2) / len(font_bytes) * 100
    log(f"Subsetted WOFF2: {len(woff2):,} bytes ({len(woff2) / 1024:.2f} KB, {ratio:.2f}% of source)")

    b64 = base64.b64encode(woff2).decode("ascii")
    new_document, action = replace_font_face(document, build_font_face(b64))

    if action == "unchanged":
        log(f"{html_path} is already up to date. No changes made.")
        return 0

    if args.check:
        print(f"Error: {html_path} is out of date (subset would be {action}).", file=sys.stderr)
        return 1

    html_path.write_text(new_document, encoding="utf-8")
    log(f"{html_path} updated successfully! (@font-face {action}, {len(new_document):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
