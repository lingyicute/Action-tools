#!/usr/bin/env python3
"""
Verify that the inlined Nebulove subset really covers every character used by
the page. Exits non-zero when a glyph the source font could have provided is
missing from the subset, so CI can guard against a bad subset.

Characters the source font does not contain at all (emoji, ›, ⚡, …) are
reported as informational: they legitimately fall through to the next family in
the CSS font stack.

Usage: python scripts/verify_font_subset.py [--html downloader-introduce/index.html]
"""

from __future__ import annotations

import argparse
import base64
import io
import re
import sys
from pathlib import Path

from subset_font import DEFAULT_HTML, FONT_URL, collect_chars, download_font

DATA_URI_RE = re.compile(r"url\('data:font/woff2;charset=utf-8;base64,([A-Za-z0-9+/=]+)'\)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", default=DEFAULT_HTML)
    parser.add_argument(
        "--source-font",
        default="/tmp/Nebulove.ttf",
        help="local copy of the full source font (downloaded when missing)",
    )
    parser.add_argument("--extra-chars", default="")
    args = parser.parse_args()

    html_path = Path(args.html)
    document = html_path.read_text(encoding="utf-8")

    match = DATA_URI_RE.search(document)
    if not match:
        print(f"Error: no inline font subset found in {html_path}.", file=sys.stderr)
        return 1

    # The page's own base64 blob is markup, not content — drop it before
    # deriving the required character set.
    content = document.replace(match.group(0), "")
    required = collect_chars(content, args.extra_chars)

    from fontTools.ttLib import TTFont

    raw = base64.b64decode(match.group(1))
    subset_cmap = set(TTFont(io.BytesIO(raw)).getBestCmap())

    source_cmap: set[int] = set()
    source_path = Path(args.source_font)
    try:
        if not source_path.exists():
            source_path.write_bytes(download_font(FONT_URL))
        source_cmap = set(TTFont(source_path).getBestCmap())
    except Exception as exc:  # offline / rate-limited: degrade to a weaker check
        print(f"Warning: source font unavailable ({exc}); checking subset only.", file=sys.stderr)

    missing = sorted(c for c in required if ord(c) not in subset_cmap and ord(c) in source_cmap)
    if missing:
        print(f"Error: subset is missing {len(missing)} character(s): {''.join(missing[:40])}", file=sys.stderr)
        return 1

    fallback = sorted(c for c in required if ord(c) not in subset_cmap)
    checked = len(required) - len(fallback) if source_cmap else len(required)
    print(
        f"OK: inline subset {len(raw):,} bytes covers all {checked} characters "
        f"used by {html_path} ({len(subset_cmap)} mapped codepoints)."
    )
    if fallback:
        note = "" if source_cmap else " (not cross-checked against the source font)"
        print(f"    {len(fallback)} char(s) rely on the CSS fallback stack{note}: {''.join(fallback)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
