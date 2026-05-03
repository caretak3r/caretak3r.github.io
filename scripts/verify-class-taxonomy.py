#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""verify-class-taxonomy.py — Guard against SEF↔Hugo CSS class drift.

Reads:
  data/reports/SEF_*.html   — extract every CSS class actually used
  assets/css/research-report.css — extract every class targeted by a rule

Reports any class used in a report that the site CSS does not target. Optionally
reports the inverse (CSS rules with no callers, i.e. dead CSS). Exits nonzero if
any unstyled classes are found, so this is CI-safe.

Stdlib-only: zero deps. Runs in <1s on the full report corpus.

Tolerated unstyled classes
--------------------------
A small allowlist of classes is treated as ``intentionally unstyled``:
  * ``rating-modifier`` modifiers like ``rating-badge.overweight`` are matched
    via attribute selectors, so the modifier alone is allowed.
  * Utility wrappers the renderer emits but doesn't visually distinguish.

To add a class to the allowlist, edit ``ALLOWED_UNSTYLED`` below with a comment
explaining why. The point is to make every exception explicit and reviewed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORTS = REPO_ROOT / "data" / "reports"
DEFAULT_CSS = REPO_ROOT / "assets" / "css" / "research-report.css"

# Classes the renderer emits structurally but the site doesn't visually
# distinguish. Each entry needs a one-line justification.
ALLOWED_UNSTYLED: dict[str, str] = {
    # Modifier classes targeted via .rating-badge.overweight selectors.
    "overweight": "rating modifier on .rating-badge",
    "hold": "rating modifier on .rating-badge",
    "underweight": "rating modifier on .rating-badge",
    # Layout helpers — flat block-level wrappers with default spacing.
    "header-top": "internal flex row inside .header",
    "summary": "first paragraph of .decision-box (inherits .decision-box typography)",
    "content": "inner block of .interim-box (already styled via .interim-box .content)",
    "report-content": "analyst report body wrapper (styled via .report-content)",
    # Section semantic markers
    "section": "h2.section selector targets these",
    # Renderer occasionally emits a bare ".high" alongside ".cat-very" on
    # catalyst rows; the visual treatment comes from .cat-very, so the
    # bare modifier is decorative and intentionally unstyled.
    "high": "redundant modifier on .cat-very catalyst rows",
}

# HTML class extraction — `class="a b c"` and `class='a b c'`
CLASS_ATTR_RE = re.compile(r'class\s*=\s*["\']([^"\']+)["\']')

# CSS class extraction — `.foo`, `.foo.bar`, `.foo:hover` etc. We strip leading
# scope selectors like ``.report-shell`` since they're a wrapper, not a class
# the renderer emits inside the report body.
CSS_CLASS_RE = re.compile(r"\.([a-zA-Z_][\w-]*)")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def classes_used_in_html(html_path: Path) -> set[str]:
    """All CSS classes referenced in `class="..."` attributes."""
    text = html_path.read_text(encoding="utf-8", errors="replace")
    used: set[str] = set()
    for match in CLASS_ATTR_RE.finditer(text):
        for token in match.group(1).split():
            if token:
                used.add(token)
    return used


def classes_targeted_in_css(css_path: Path) -> set[str]:
    """All CSS classes appearing in any selector. Stripped of comments."""
    text = css_path.read_text(encoding="utf-8")
    text = CSS_COMMENT_RE.sub(" ", text)
    targeted: set[str] = set()
    for match in CSS_CLASS_RE.finditer(text):
        targeted.add(match.group(1))
    return targeted


def collect_used(reports_dir: Path) -> dict[str, set[str]]:
    """Map of report filename → set of classes used."""
    out: dict[str, set[str]] = {}
    for path in sorted(reports_dir.glob("SEF_*.html")):
        out[path.name] = classes_used_in_html(path)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reports", type=Path, default=DEFAULT_REPORTS,
                        help=f"Directory of SEF_*.html reports (default: {DEFAULT_REPORTS})")
    parser.add_argument("--css", type=Path, default=DEFAULT_CSS,
                        help=f"Site stylesheet to verify against (default: {DEFAULT_CSS})")
    parser.add_argument("--show-dead", action="store_true",
                        help="Also report site CSS classes that no SEF report uses")
    args = parser.parse_args(argv)

    if not args.reports.exists():
        print(f"error: reports dir missing: {args.reports}", file=sys.stderr)
        return 2
    if not args.css.exists():
        print(f"error: css file missing: {args.css}", file=sys.stderr)
        return 2

    used_by_report = collect_used(args.reports)
    if not used_by_report:
        print(f"warning: no SEF_*.html in {args.reports}", file=sys.stderr)
        return 0

    targeted = classes_targeted_in_css(args.css)
    all_used: set[str] = set()
    for s in used_by_report.values():
        all_used.update(s)

    unstyled = sorted(c for c in all_used
                      if c not in targeted and c not in ALLOWED_UNSTYLED)

    print(f"reports scanned: {len(used_by_report)}")
    print(f"classes used:    {len(all_used)}")
    print(f"classes targeted in CSS: {len(targeted)}")
    print(f"allowlisted:     {len(ALLOWED_UNSTYLED)}")
    print()

    if unstyled:
        print(f"FAIL: {len(unstyled)} class(es) used in reports but not styled by site CSS:")
        for cls in unstyled:
            # Show which reports use it
            using = [name for name, classes in used_by_report.items() if cls in classes]
            example = using[0] if using else "?"
            extra = f" (+ {len(using) - 1} more)" if len(using) > 1 else ""
            print(f"  - .{cls}   first seen in {example}{extra}")
        print()
        print("Action: either add a CSS rule in assets/css/research-report.css,")
        print("        or add the class to ALLOWED_UNSTYLED here with a justification.")
        return 1

    print("OK: every class used in reports is styled by the site CSS.")

    if args.show_dead:
        # Site classes (lowercased to scope) the reports never reference.
        # We exclude .report-shell itself since it's the layout wrapper,
        # plus any pseudo-class fragments that slipped through.
        scoped = {"report-shell"}
        site_emitted = set(ALLOWED_UNSTYLED.keys())
        dead = sorted(c for c in targeted
                      if c not in all_used
                      and c not in scoped
                      and c not in site_emitted)
        if dead:
            print()
            print(f"INFO: {len(dead)} CSS class(es) targeted but unused in current reports:")
            for cls in dead:
                print(f"  - .{cls}")
            print("(may be intentional — kept for future SEF features or content types)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
