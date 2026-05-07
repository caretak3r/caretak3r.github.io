#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4>=4.12", "lxml>=5.0"]
# ///
"""
sync-research.py — Ingest SEF research HTML reports into Hugo content.

Reads:   ~/.tradingagents/reports/SEF_<TICKER>_<YYYY-MM-DD>.html (local default)
         sef-input/SEF_<TICKER>_<YYYY-MM-DD>.html (CI fallback / committed source)
Writes:  content/research/<ticker-lower>-<YYYY-MM-DD>/index.html

Each output file gets Hugo front-matter (ticker, date, rating, company, sector,
thesis_oneliner, source_file, source_hash) followed by the raw HTML body of
the source report. The site's research single.html layout wraps the inlined
HTML in the topbar shell.

Idempotent: if source_hash in existing front-matter matches the current source
file, we skip rewriting. CI-safe: any extraction failure exits nonzero with the
specific filename + selector that failed.

Decisions baked in:
- Confidentiality footer stays (per project decision).
- No AI-augmented disclaimer banner injected.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, Comment, Tag

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_INPUT = Path("~/.tradingagents/reports").expanduser()
REPO_INPUT = REPO_ROOT / "sef-input"
DEFAULT_INPUT = LOCAL_INPUT if LOCAL_INPUT.exists() else REPO_INPUT
DEFAULT_OUTPUT = REPO_ROOT / "content" / "research"

VALID_RATINGS = {"BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL"}
SLUG_RE = re.compile(r"^SEF_([A-Z0-9.]+)_(\d{4}-\d{2}-\d{2})\.html$")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Report:
    source_path: Path
    source_hash: str
    ticker: str
    date: str  # ISO YYYY-MM-DD
    rating: str  # lowercase: overweight | hold | underweight
    company: str
    sector: str
    thesis_oneliner: str
    body_html: str

    @property
    def slug(self) -> str:
        return f"{self.ticker.lower()}-{self.date}"

    @property
    def title(self) -> str:
        return f"{self.ticker} — {self.rating.upper()}"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


class ExtractError(RuntimeError):
    """Raised when a required selector is missing or malformed."""


def require_text(soup: BeautifulSoup, selector: str, source: Path) -> str:
    el = soup.select_one(selector)
    if el is None:
        raise ExtractError(f"{source.name}: selector not found: {selector!r}")
    text = el.get_text(strip=True)
    if not text:
        raise ExtractError(f"{source.name}: selector empty: {selector!r}")
    return text


def find_text(soup: BeautifulSoup, selector: str) -> str | None:
    el = soup.select_one(selector)
    if el is None:
        return None
    text = el.get_text(strip=True)
    return text or None


def parse_date(text: str, source: Path) -> str:
    """Accept either 'May 03, 2026' (header) or '2026-05-03' (filename)."""
    text = text.strip()
    for fmt in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ExtractError(f"{source.name}: unparseable date {text!r}")


def parse_rating(text: str, source: Path) -> str:
    text = text.strip().upper()
    if text not in VALID_RATINGS:
        raise ExtractError(
            f"{source.name}: bad rating {text!r}; expected one of {sorted(VALID_RATINGS)}"
        )
    return text.lower()


def extract_sector(soup: BeautifulSoup) -> str:
    """Find the meta-row span containing 'Sector:'."""
    meta = soup.select_one("div.meta-row")
    if meta is None:
        return ""
    for span in meta.find_all("span"):
        text = span.get_text(strip=True)
        if text.lower().startswith("sector:"):
            return text.split(":", 1)[1].strip()
    return ""


def extract_thesis_oneliner(soup: BeautifulSoup) -> str:
    """Pull the first <p> from div.lede; fall back to the decision-box summary."""
    lede = soup.select_one("div.lede p")
    if lede is None:
        lede = soup.select_one("div.decision-box .summary p")
    if lede is None:
        return ""
    text = lede.get_text(strip=True)
    if len(text) > 300:
        text = text[:297].rstrip() + "…"
    return text


def extract_body_html(soup: BeautifulSoup, source: Path) -> str:
    """Serialize the inner contents of <body>, stripped of source styles.

    The site owns the visual treatment via assets/css/research-report.css,
    which targets the SEF semantic classes (.ticker, .lede, .decision-box,
    etc.) against site design tokens. So we drop the source <style> blocks
    and Google Fonts <link> tags — they would fight the site stylesheet.

    Also strip any <style>/<link> tags that appear inside <body> for the same
    reason. The report's structural HTML (classes, semantics) is preserved.
    """
    body = soup.body
    if body is None:
        raise ExtractError(f"{source.name}: no <body> found")

    for tag in body.find_all(["style", "link"]):
        tag.decompose()

    # HTML comments (`<!-- /.col-prose -->` etc.) are decorative annotations
    # in the SEF source; lxml's serializer drops the comment wrappers and
    # leaks the inner text as visible page content. Strip them outright —
    # they have no semantic value once the report is on the site.
    for node in body.find_all(string=lambda t: isinstance(t, Comment)):
        node.extract()

    return "".join(str(c) for c in body.children)


def parse_filename(path: Path) -> tuple[str, str]:
    m = SLUG_RE.match(path.name)
    if not m:
        raise ExtractError(
            f"{path.name}: filename does not match SEF_<TICKER>_<YYYY-MM-DD>.html"
        )
    return m.group(1), m.group(2)


# ---------------------------------------------------------------------------
# Front-matter (de)serialization
# ---------------------------------------------------------------------------


def render_front_matter(report: Report) -> str:
    fm_lines = [
        "---",
        f'title: "{escape_yaml(report.title)}"',
        f"date: {report.date}",
        "draft: false",
        f'slug: "{report.slug}"',
        f'ticker: "{report.ticker}"',
        f'company: "{escape_yaml(report.company)}"',
        f'rating: "{report.rating}"',
        f'sector: "{escape_yaml(report.sector)}"',
        f'thesis_oneliner: "{escape_yaml(report.thesis_oneliner)}"',
        'layout: "report-html"',
        f'source_file: "{report.source_path.name}"',
        # Hash key generations:
        #   source_hash    — original
        #   source_hash_v2 — comment-stripping landed
        #   source_hash_v3 — server-side TOC + section IDs landed; bumping
        #                    forces every report to re-ingest with the new
        #                    `<aside class="report-toc">` and `id="sec-…"`
        #                    attributes that backfill-toc.py just injected
        #                    into sef-input/.
        f'source_hash_v3: "{report.source_hash}"',
        "---",
    ]
    return "\n".join(fm_lines) + "\n\n"


def escape_yaml(value: str) -> str:
    """Minimal YAML string escaping for our double-quoted style."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def existing_hash(target: Path) -> str | None:
    if not target.exists():
        return None
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    front_matter = text[3:end]
    for line in front_matter.splitlines():
        line = line.strip()
        if line.startswith("source_hash_v3:"):
            value = line.split(":", 1)[1].strip()
            return value.strip('"').strip("'")
    return None


# ---------------------------------------------------------------------------
# Per-report pipeline
# ---------------------------------------------------------------------------


def ingest_one(source: Path, output_root: Path, dry_run: bool) -> tuple[str, bool]:
    """Process one report. Returns (slug, was_written)."""
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()

    soup = BeautifulSoup(raw, "lxml")

    ticker_fname, date_fname = parse_filename(source)

    ticker_html = require_text(soup, "div.ticker", source)
    if ticker_html != ticker_fname:
        raise ExtractError(
            f"{source.name}: ticker mismatch — filename={ticker_fname} html={ticker_html}"
        )

    # Header div.date is the publish date; filename encodes the *analysis* date.
    # They legitimately differ (e.g., report analyzes through 2026-04-30 but is
    # written/published on 2026-05-01). The filename is authoritative for slug
    # ordering and Hugo .Date. We just sanity-parse the header date and log a
    # mismatch as informational, not fatal.
    date_iso = date_fname  # authoritative
    header_date_text = find_text(soup, "div.header div.date")
    if header_date_text:
        try:
            header_iso = parse_date(header_date_text, source)
            if header_iso != date_fname:
                # Quietly tolerated: headers reflect publish date, not analysis date.
                pass
        except ExtractError:
            pass  # malformed header date; filename still wins

    rating_raw = require_text(soup, "div.rating-badge", source)
    rating = parse_rating(rating_raw, source)

    company = find_text(soup, "div.company-full") or ""
    sector = extract_sector(soup)
    thesis = extract_thesis_oneliner(soup)
    body_html = extract_body_html(soup, source)

    report = Report(
        source_path=source,
        source_hash=digest,
        ticker=ticker_fname,
        date=date_iso,
        rating=rating,
        company=company,
        sector=sector,
        thesis_oneliner=thesis,
        body_html=body_html,
    )

    target_dir = output_root / report.slug
    target = target_dir / "index.html"

    prior = existing_hash(target)
    if prior == digest:
        return report.slug, False

    if dry_run:
        return report.slug, True

    target_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(
        render_front_matter(report) + report.body_html + "\n",
        encoding="utf-8",
    )
    return report.slug, True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input directory of SEF *.html reports (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output Hugo content/research/ root (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report but don't write anything",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: input dir does not exist: {args.input}", file=sys.stderr)
        return 2

    sources = sorted(args.input.glob("SEF_*.html"))
    if not sources:
        print(f"warning: no SEF_*.html files in {args.input}", file=sys.stderr)
        return 0

    failures: list[tuple[Path, Exception]] = []
    written = 0
    skipped = 0

    for source in sources:
        try:
            slug, was_written = ingest_one(source, args.output, args.dry_run)
        except ExtractError as exc:
            failures.append((source, exc))
            print(f"FAIL {source.name}: {exc}", file=sys.stderr)
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append((source, exc))
            print(f"FAIL {source.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue

        if was_written:
            verb = "WOULD WRITE" if args.dry_run else "WROTE"
            print(f"{verb}  {slug}  ← {source.name}")
            written += 1
        else:
            print(f"SKIP   {slug}  (unchanged)")
            skipped += 1

    print(
        f"\nsummary: {written} written, {skipped} skipped, {len(failures)} failed "
        f"out of {len(sources)} reports."
    )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
