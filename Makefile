# caretak3r.github.io — local dev + ingestion targets
# All targets run in the repo root.

.PHONY: dev build sync-research test clean help

help:
	@echo "Targets:"
	@echo "  dev             — hugo server -D --bind 127.0.0.1 --port 1313"
	@echo "  build           — hugo --minify --gc"
	@echo "  sync-research   — ingest data/reports/SEF_*.html into content/research/"
	@echo "  test            — run python tests for ingestion script"
	@echo "  clean           — remove public/ and resources/_gen/"

dev:
	hugo server -D --bind 127.0.0.1 --port 1313

build:
	hugo --minify --gc

sync-research:
	uv run scripts/sync-research.py

sync-research-dry:
	uv run scripts/sync-research.py --dry-run

test:
	uv run scripts/test_sync_research.py

clean:
	rm -rf public/ resources/_gen/
