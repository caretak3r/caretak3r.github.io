#!/usr/bin/env bash
# publish.sh — Sync /analyze output into the site, regenerate, verify, build.
#
# Pipeline:
#   ~/.tradingagents/reports/SEF_*.html
#       → rsync → sef-input/                        (committed source for CI)
#       → sync-research.py → content/research/...   (Hugo content)
#       → hugo --gc --minify                         (production build gate)
#
# Idempotent: rsync --delete keeps sef-input/ in lockstep with the local
# /analyze output; sync-research.py skips files whose source_hash_v2 is
# unchanged. Safe to run repeatedly.
#
# Flags:
#   --commit   Stage sef-input/ + content/research/ and create a commit
#   --push     Implies --commit; pushes to origin after committing
#   --dry-run  Show what would happen without writing
#
# Exit codes:
#   0  success (or no changes to publish)
#   1  verification or build failure
#   2  source dir missing / preflight failure

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${HOME}/.tradingagents/reports"
INPUT_DIR="${REPO_ROOT}/sef-input"

cd "${REPO_ROOT}"

DO_COMMIT=0
DO_PUSH=0
DRY_RUN=0
RSYNC_FLAGS=(-a --delete --include='SEF_*.html' --include='*/' --exclude='*')

for arg in "$@"; do
  case "$arg" in
    --commit)  DO_COMMIT=1 ;;
    --push)    DO_COMMIT=1; DO_PUSH=1 ;;
    --dry-run) DRY_RUN=1; RSYNC_FLAGS+=(--dry-run) ;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "error: source dir missing: ${SOURCE_DIR}" >&2
  echo "       /analyze writes here. Run /analyze first or check the path." >&2
  exit 2
fi

# Hard guard: data/reports/ MUST NOT exist — Hugo's data loader walks /data/
# recursively, and these files aren't valid YAML/TOML/JSON, so the build
# explodes with "unmarshal of format ''". The path is gitignored, but if a
# stray rsync (or operator) recreates it we want a loud, immediate failure
# rather than a confusing CI error 30 seconds later.
if [[ -d "${REPO_ROOT}/data/reports" ]]; then
  echo "error: data/reports/ exists — this breaks Hugo's data loader." >&2
  echo "       SEF inputs must live under sef-input/, not data/." >&2
  echo "       Remove with:  rm -rf data/reports/" >&2
  exit 2
fi

echo "==> rsync ${SOURCE_DIR}/ → ${INPUT_DIR}/"
mkdir -p "${INPUT_DIR}"
rsync "${RSYNC_FLAGS[@]}" "${SOURCE_DIR}/" "${INPUT_DIR}/"

echo "==> verify class taxonomy"
uv run scripts/verify-class-taxonomy.py --reports sef-input

SYNC_ARGS=(--input sef-input)
if [[ "${DRY_RUN}" -eq 1 ]]; then
  SYNC_ARGS+=(--dry-run)
fi

echo "==> sync-research.py ${SYNC_ARGS[*]}"
uv run scripts/sync-research.py "${SYNC_ARGS[@]}"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "==> dry-run: skipping hugo build + commit"
  exit 0
fi

echo "==> hugo --gc --minify"
hugo --gc --minify

if [[ "${DO_COMMIT}" -eq 0 ]]; then
  echo
  echo "Done. Review changes with:  git status"
  echo "Commit + push with:         scripts/publish.sh --push"
  exit 0
fi

if git diff --quiet sef-input/ content/research/ \
   && [[ -z "$(git ls-files --others --exclude-standard sef-input/ content/research/)" ]]; then
  echo "==> no changes to commit"
  exit 0
fi

LATEST_DATE="$(ls sef-input/SEF_*.html 2>/dev/null \
  | sed -E 's/.*_([0-9]{4}-[0-9]{2}-[0-9]{2})\.html$/\1/' \
  | sort -u | tail -1)"
COMMIT_MSG="feat: refresh research reports through ${LATEST_DATE:-$(date +%Y-%m-%d)}"

echo "==> git commit -m \"${COMMIT_MSG}\""
git add sef-input/ content/research/
git commit -m "${COMMIT_MSG}"

if [[ "${DO_PUSH}" -eq 1 ]]; then
  echo "==> git push"
  git push
fi
