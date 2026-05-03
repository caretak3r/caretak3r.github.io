#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4>=4.12", "lxml>=5.0", "pytest>=8.0"]
# ///
"""
Tests for sync-research.py.

Run via:
    uv run scripts/test_sync_research.py

The tests exercise pure helpers with synthetic HTML, and run an end-to-end
ingest against a real SEF fixture from data/reports/ if one is present.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "sync-research.py"
FIXTURES = REPO_ROOT / "data" / "reports"


def _load_module():
    spec = importlib.util.spec_from_file_location("sync_research", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_research"] = module
    spec.loader.exec_module(module)
    return module


sr = _load_module()


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestParseFilename:
    def test_happy_path(self):
        ticker, date = sr.parse_filename(Path("SEF_ASML_2026-05-03.html"))
        assert ticker == "ASML"
        assert date == "2026-05-03"

    def test_dotted_ticker(self):
        # Some filenames may contain dotted tickers (e.g., RGAKF). Regex allows it.
        ticker, date = sr.parse_filename(Path("SEF_BRK.B_2026-05-03.html"))
        assert ticker == "BRK.B"
        assert date == "2026-05-03"

    def test_rejects_bad_format(self):
        with pytest.raises(sr.ExtractError):
            sr.parse_filename(Path("not-a-sef-report.html"))

    def test_rejects_lowercase_ticker(self):
        # Tickers must be uppercase per convention.
        with pytest.raises(sr.ExtractError):
            sr.parse_filename(Path("SEF_asml_2026-05-03.html"))


class TestParseDate:
    def test_long_form(self):
        assert sr.parse_date("May 03, 2026", Path("x.html")) == "2026-05-03"

    def test_iso_form(self):
        assert sr.parse_date("2026-05-03", Path("x.html")) == "2026-05-03"

    def test_rejects_garbage(self):
        with pytest.raises(sr.ExtractError):
            sr.parse_date("Funday the umpteenth", Path("x.html"))


class TestParseRating:
    @pytest.mark.parametrize("text,expected", [
        ("OVERWEIGHT", "overweight"),
        ("Hold", "hold"),
        ("  underweight  ", "underweight"),
    ])
    def test_valid(self, text, expected):
        assert sr.parse_rating(text, Path("x.html")) == expected

    def test_rejects_invalid(self):
        with pytest.raises(sr.ExtractError):
            sr.parse_rating("BUY", Path("x.html"))


class TestEscapeYaml:
    def test_quotes(self):
        assert sr.escape_yaml('he said "hi"') == 'he said \\"hi\\"'

    def test_backslash(self):
        assert sr.escape_yaml(r"path\to\file") == r"path\\to\\file"


# ---------------------------------------------------------------------------
# DOM helpers (synthetic fixtures)
# ---------------------------------------------------------------------------


SYNTHETIC = """
<html>
<head><style>.x{color:red}</style>
<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet">
</head>
<body>
<div class="header">
  <div class="header-top">
    <div class="fund-name">Silent Engineering Fund</div>
    <div class="date">May 03, 2026</div>
  </div>
  <div class="ticker">XXXX</div>
  <div class="company-full">Example Corp</div>
  <div class="meta-row">
    <span>Analysis Date: 2026-05-03</span>
    <span>Sector: Technology &amp; Things</span>
  </div>
  <div class="rating-badge">HOLD</div>
</div>
<div class="lede"><p>The actual story sits one segment deeper.</p></div>
<div class="footer">CONFIDENTIAL — DO NOT DISTRIBUTE</div>
</body>
</html>
"""


@pytest.fixture
def soup():
    return BeautifulSoup(SYNTHETIC, "lxml")


class TestExtractSector:
    def test_finds_sector(self, soup):
        assert sr.extract_sector(soup) == "Technology & Things"


class TestExtractThesisOneliner:
    def test_finds_lede(self, soup):
        text = sr.extract_thesis_oneliner(soup)
        assert text == "The actual story sits one segment deeper."

    def test_truncates_long(self):
        long_p = "<div class='lede'><p>" + ("x" * 400) + "</p></div>"
        s = BeautifulSoup(f"<html><body>{long_p}</body></html>", "lxml")
        text = sr.extract_thesis_oneliner(s)
        assert text.endswith("…")
        assert len(text) <= 300


class TestExtractBodyHtml:
    def test_strips_styles_keeps_body(self, soup):
        body = sr.extract_body_html(soup, Path("x.html"))
        # Source <style> from <head> must NOT be carried over — site owns theming
        assert ".x{color:red}" not in body
        # Google Fonts <link> must NOT be carried over
        assert "fonts.googleapis.com" not in body
        # Body classes survive (semantic structure preserved for site CSS to target)
        assert 'class="ticker"' in body
        # Confidentiality footer survives (per project decision)
        assert "CONFIDENTIAL" in body
        # Outer <html>/<head>/<body> wrappers stripped
        assert "<html" not in body.lower()
        assert "<body" not in body.lower()

    def test_strips_inline_style_tags_in_body(self):
        html = """
        <html><head></head><body>
        <style>.inline-style { color: red; }</style>
        <link rel="stylesheet" href="https://fonts.googleapis.com/foo">
        <div class="ticker">XXXX</div>
        </body></html>
        """
        s = BeautifulSoup(html, "lxml")
        body = sr.extract_body_html(s, Path("x.html"))
        assert ".inline-style" not in body
        assert "fonts.googleapis.com" not in body
        assert 'class="ticker"' in body


# ---------------------------------------------------------------------------
# End-to-end against a real fixture
# ---------------------------------------------------------------------------


REAL_FIXTURE = FIXTURES / "SEF_ASML_2026-05-03.html"


@pytest.mark.skipif(not REAL_FIXTURE.exists(), reason="real fixture not staged")
class TestEndToEnd:
    def test_ingest_writes_expected_file(self, tmp_path):
        slug, written = sr.ingest_one(REAL_FIXTURE, tmp_path, dry_run=False)
        assert slug == "asml-2026-05-03"
        assert written is True
        target = tmp_path / "asml-2026-05-03" / "index.html"
        assert target.exists()
        content = target.read_text()
        assert content.startswith("---")
        assert 'ticker: "ASML"' in content
        assert 'rating: "overweight"' in content
        assert 'date: 2026-05-03' in content
        assert 'layout: "report-html"' in content
        # slug must match the directory name so Hugo permalinks resolve to /research/<slug>/
        assert 'slug: "asml-2026-05-03"' in content
        # Source body content present
        assert 'class="ticker"' in content
        # Confidentiality footer kept (per project decision)
        assert "confidential" in content.lower() or "Silent Engineering Fund" in content

    def test_ingest_is_idempotent(self, tmp_path):
        # First run writes
        _, w1 = sr.ingest_one(REAL_FIXTURE, tmp_path, dry_run=False)
        assert w1 is True
        # Second run skips (source_hash matches)
        _, w2 = sr.ingest_one(REAL_FIXTURE, tmp_path, dry_run=False)
        assert w2 is False

    def test_dry_run_does_not_write(self, tmp_path):
        _, w = sr.ingest_one(REAL_FIXTURE, tmp_path, dry_run=True)
        assert w is True
        assert not (tmp_path / "asml-2026-05-03").exists()


# ---------------------------------------------------------------------------
# Integration: filename mismatch must fail loud
# ---------------------------------------------------------------------------


class TestMismatch:
    def test_filename_ticker_mismatch_raises(self, tmp_path):
        bad = tmp_path / "SEF_ZZZZ_2026-05-03.html"
        bad.write_text(SYNTHETIC.replace("XXXX", "XXXX"), encoding="utf-8")  # html says XXXX, filename says ZZZZ
        with pytest.raises(sr.ExtractError, match="ticker mismatch"):
            sr.ingest_one(bad, tmp_path / "out", dry_run=True)

    def test_invalid_rating_raises(self, tmp_path):
        bad_html = SYNTHETIC.replace(">HOLD<", ">SUPERWEIGHT<")
        bad = tmp_path / "SEF_XXXX_2026-05-03.html"
        bad.write_text(bad_html, encoding="utf-8")
        with pytest.raises(sr.ExtractError, match="bad rating"):
            sr.ingest_one(bad, tmp_path / "out", dry_run=True)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
