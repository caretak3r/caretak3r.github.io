#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""backfill-toc.py — Inject section IDs + right-rail TOC into existing SEF reports.

Old SEF reports (pre-2026-05-07 emitter) shipped without `id="sec-…"` on
section headings and without a `<aside class="report-toc">` block. The
Hugo site previously re-built those structures client-side via
`static/js/report-nav.js`. Now that the upstream emitter generates them
server-side, the existing on-disk corpus needs a one-shot upgrade so it
matches the new shape.

Idempotent: any report that already contains `<aside class="report-toc">`
is skipped. Safe to run repeatedly.

Targets (default both):
  ~/.tradingagents/reports/SEF_*.html   (raw /analyze output)
  ./sef-input/SEF_*.html                (committed mirror in this repo)

The slug algorithm matches static/js/report-nav.js:14-26 byte-for-byte
so any external `#sec-…` deep-links keep resolving.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS = (
    Path("~/.tradingagents/reports").expanduser(),
    REPO_ROOT / "sef-input",
)

_SECTION_HEADING_RE = re.compile(
    r'<h2(?P<attrs>[^>]*)>(?P<text>.*?)</h2>',
    re.DOTALL,
)
_SLUG_NORMALIZE_RE = re.compile(r'[^a-z0-9]+')
_TOC_PRESENT_RE = re.compile(r'<aside\s+class="report-toc"', re.IGNORECASE)
_HTML_TAG_RE = re.compile(r'<[^>]+>')


def slugify(text: str, taken: dict[str, int]) -> str:
    base = 'sec-' + _SLUG_NORMALIZE_RE.sub('-', (text or '').lower()).strip('-')
    if base not in taken:
        taken[base] = 1
        return base
    taken[base] += 1
    return f"{base}-{taken[base]}"


def _is_section_h2(attrs: str, text: str) -> bool:
    if 'id=' in attrs:
        return False
    if 'class="section"' in attrs or "class='section'" in attrs:
        return True
    return text.strip() == 'Portfolio Decision'


def _escape_html(text: str) -> str:
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def inject(html: str) -> tuple[str, list[tuple[str, str]], bool]:
    """Returns (patched_html, headings, was_modified).

    was_modified=False when the file already has a TOC aside.
    """
    if _TOC_PRESENT_RE.search(html):
        return html, [], False

    taken: dict[str, int] = {}
    headings: list[tuple[str, str]] = []

    def repl(m: re.Match) -> str:
        attrs = m.group('attrs')
        inner = m.group('text')
        if not _is_section_h2(attrs, inner):
            return m.group(0)
        label = _HTML_TAG_RE.sub('', inner).strip()
        slug = slugify(label, taken)
        headings.append((slug, label))
        return f'<h2{attrs} id="{slug}">{inner}</h2>'

    patched = _SECTION_HEADING_RE.sub(repl, html)

    if not headings:
        return html, [], False

    items = '\n    '.join(
        f'<li><a class="report-toc-link" data-section="{slug}" '
        f'href="#{slug}">{_escape_html(label)}</a></li>'
        for slug, label in headings
    )
    aside = (
        '<aside class="report-toc" aria-label="Sections">\n'
        '  <div class="report-toc-label">Sections</div>\n'
        '  <ol class="report-toc-list">\n'
        f'    {items}\n'
        '  </ol>\n'
        '</aside>\n\n'
    )

    # Insert immediately after the closing </div> of the .header block
    # (the one that contains the rating-badge). This places the TOC at
    # the top of the body content, before the lede.
    rb_pos = patched.find('rating-badge')
    if rb_pos == -1:
        return html, [], False
    head_close = patched.find('</div>\n\n', rb_pos)
    if head_close == -1:
        # Loose match — different whitespace
        head_close = patched.find('</div>', rb_pos)
        if head_close == -1:
            return html, [], False
        insert_at = head_close + len('</div>')
        patched = patched[:insert_at] + '\n\n' + aside + patched[insert_at:]
    else:
        insert_at = head_close + len('</div>\n\n')
        patched = patched[:insert_at] + aside + patched[insert_at:]

    return patched, headings, True


# ---------------------------------------------------------------------------
# Self-test fixtures (the deep-link contract)
# ---------------------------------------------------------------------------

PINNED_SLUGS = [
    ("Research Manager", "sec-research-manager"),
    ("Trader", "sec-trader"),
    ("Investment Debate", "sec-investment-debate"),
    ("Risk Assessment", "sec-risk-assessment"),
    ("Technical Read", "sec-technical-read"),
    ("Risk Factors (Item 1A)", "sec-risk-factors-item-1a"),
    ("Portfolio Decision", "sec-portfolio-decision"),
    ("Analyst Reports", "sec-analyst-reports"),
]


def selftest() -> int:
    failures = 0
    for label, expected in PINNED_SLUGS:
        got = slugify(label, {})
        if got != expected:
            print(f"FAIL slug {label!r}: got {got!r}, want {expected!r}", file=sys.stderr)
            failures += 1
    if failures:
        print(f"selftest: {failures} failure(s)", file=sys.stderr)
        return 1
    print(f"selftest: {len(PINNED_SLUGS)} fixtures OK")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def process_dir(directory: Path, dry_run: bool) -> tuple[int, int]:
    """(modified, skipped)"""
    if not directory.exists():
        print(f"warning: {directory} does not exist; skipping", file=sys.stderr)
        return 0, 0
    files = sorted(directory.glob("SEF_*.html"))
    modified = 0
    skipped = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        new_text, headings, changed = inject(text)
        if not changed:
            skipped += 1
            continue
        if dry_run:
            print(f"WOULD WRITE  {f.relative_to(directory.parent)}  ({len(headings)} sections)")
        else:
            f.write_text(new_text, encoding="utf-8")
            print(f"WROTE        {f.relative_to(directory.parent)}  ({len(headings)} sections)")
        modified += 1
    return modified, skipped


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("paths", nargs="*", type=Path,
                   help=f"Directories to scan (default: {[str(d) for d in DEFAULTS]})")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would change without writing")
    p.add_argument("--selftest", action="store_true",
                   help="Run slug fixtures and exit")
    args = p.parse_args()

    if args.selftest:
        return selftest()

    targets = args.paths if args.paths else list(DEFAULTS)
    rc = selftest()
    if rc != 0:
        return rc

    total_mod = 0
    total_skip = 0
    for d in targets:
        mod, skip = process_dir(d, args.dry_run)
        total_mod += mod
        total_skip += skip
    print(f"\nsummary: {total_mod} modified, {total_skip} already had TOC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
