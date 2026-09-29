# silent.engineer: Agent Instructions

`CLAUDE.md` is a symlink to this file. Edit `AGENTS.md` only.

This repository is the source for https://silent.engineer, the personal site of Rohit Gudi. It holds engineering notes, equity research reports, financial notes, and a projects index. It is a Hugo site with no theme: every template is in `layouts/`. GitHub Pages serves it from the `main` branch.

## Setup

| Tool | Version | Used for |
|---|---|---|
| Hugo extended | CI pins 0.161.1; 0.165 works locally | Build and dev server |
| uv (Python 3.11+) | any recent | Research ingestion scripts and their tests |
| Node.js | 20 (CI) | `tests/` purity and smoke checks (Playwright) |
| bd (beads) | see `.beads/` | Task tracking |

```bash
make dev          # hugo server -D --bind 127.0.0.1 --port 1313
make build        # hugo --minify --gc  (writes public/, which is git-ignored)
make test         # ingestion script tests
cd tests && npm install && npx playwright install chromium   # once, for smoke tests
```

## Repository Map

| Path | What it holds |
|---|---|
| `hugo.toml` | Site config: `baseURL`, author/social `[params]`, permalinks, markup settings, `security.allowContent` (lets raw-HTML research pages build). |
| `content/posts/` | Engineering notes in Markdown. Served at `/posts/<slug>/` and listed on `/engineering/`. |
| `content/engineering/_index.md` | Intro text for the `/engineering/` ledger. The page lists `posts` plus any `projects` pages. |
| `content/research/<ticker>-<date>/index.html` | Generated equity research reports (raw HTML with front matter). Do not edit by hand; see "Research pipeline". |
| `content/financials/` | Longer financial notes in Markdown. Styled by `body[data-section="financials"]` rules in `style.css`. |
| `content/projects/_index.md` | Section stub for `/projects/`. Project cards come from `data/projects.yaml`, not from pages. |
| `content/about.md`, `privacy.md`, `terms.md` | Top-level pages rendered by `layouts/_default/single.html`. |
| `data/projects.yaml` | The projects index. One entry per card. |
| `layouts/_default/baseof.html` | Page shell: font preloads, stylesheets, theme bootstrap, topbar, footer, Mermaid loader. |
| `layouts/index.html` | Home: intro, engineering and research split grid, first four project cards. |
| `layouts/{engineering,posts,projects,research}/` | Section list and single templates. `research/single.html` wraps generated report HTML. |
| `layouts/partials/proj-stamp.html` | Wax-seal SVG stamp per project, plus the stamp specification. |
| `layouts/partials/topbar.html` | Top navigation. Hard-coded; see "Gotchas". |
| `layouts/partials/mermaid-loader.html` | Loads Mermaid only on pages with diagrams and applies the brand theme. |
| `layouts/_default/_markup/` | Render hooks: Mermaid code fences and wide tables. |
| `assets/css/style.css` | Site stylesheet: tokens, `@font-face`, layout, components. Minified and fingerprinted by Hugo. |
| `assets/css/research-report.css` | Styles for generated research reports. Loaded only in the `research` section. |
| `assets/js/listing.js` | Filter and sort for ledger tables. |
| `static/fonts/` | Self-hosted woff2 fonts and their OFL license files. |
| `static/js/report-nav.js` | Research report progress bar and table of contents. |
| `static/Rohit Gudi.pdf` | Resume linked from the home page. |
| `sef-input/` | Committed copies of the source research reports (`SEF_<TICKER>_<DATE>.html`). CI regenerates `content/research/` from these. |
| `scripts/` | Research pipeline scripts (see below) and their tests. |
| `tests/` | `purity.mjs` (banned phrases) and `smoke.mjs` (behavior, overflow, console errors). See `tests/README.md`. |
| `archetypes/` | Front-matter templates for `hugo new`. |
| `.github/workflows/` | `hugo.yml` builds and deploys; `pr-checks.yml` runs purity and smoke on pull requests. |
| `changes.md` | Rohit's punch list of requested site changes. |
| `.beads/`, `.claude/`, `.codex/`, `.agents/` | Task tracker and agent tool configuration. Do not edit `.beads/` internals. |

## Where Things Go

- **Engineering note:** `hugo new posts/<slug>.md`. Set `title`, `date`, `description`, `categories`, `tags`, and `draft: false`. Diagrams go in ```mermaid``` fences.
- **Financial note:** add Markdown to `content/financials/` with the same front matter.
- **Research report:** do not write it by hand. Put the `SEF_*.html` file in `sef-input/` and run the pipeline.
- **Project:** add an entry to `data/projects.yaml` and a stamp to `layouts/partials/proj-stamp.html`. Follow "Projects" in the design system below.
- **Top-level page:** add `content/<name>.md`. It renders with `layouts/_default/single.html` at `/<name>/`. Link it from `layouts/partials/footer.html` if it belongs in the footer.
- **New nav tab:** edit `layouts/partials/topbar.html` and the `.topbar` `grid-template-columns` rule in `style.css`, and update the anchor count check in `tests/smoke.mjs`.
- **Styles:** extend `assets/css/style.css` with the existing tokens. Research-only rules go in `research-report.css`. Do not add inline `style=` attributes in new templates.
- **Fonts:** `static/fonts/` plus `@font-face` at the top of `style.css`.
- **Images:** prefer `static/` or page bundles. A new external image host must be listed in `content/privacy.md`.

## Research Pipeline

```
~/.tradingagents/reports/SEF_*.html  --rsync-->  sef-input/  --sync-research.py-->  content/research/<ticker>-<date>/index.html
```

- `scripts/publish.sh` runs the whole path locally and builds the site. `--commit` and `--push` are opt-in flags; do not use them without authority.
- `scripts/sync-research.py` writes Hugo front matter (ticker, rating, sector, thesis, `source_hash_v3`) and the report body. It skips a report when the hash is unchanged. It also replaces status glyphs with Met, Partial, and Unmet. With no `--input`, it reads `~/.tradingagents/reports` when that directory exists.
- `scripts/verify-class-taxonomy.py` fails if a report uses a CSS class that `research-report.css` does not style. Add styles, or add an explained entry to `ALLOWED_UNSTYLED`.
- `scripts/backfill-toc.py` is a one-time upgrade that adds section IDs and the table of contents to older reports. It is idempotent.
- CI runs the taxonomy check, regenerates from `sef-input/`, and warns on any diff. After you edit a file in `sef-input/`, run `uv run scripts/sync-research.py --input sef-input` and commit the regenerated `content/research/` files so the hashes match.

## Deployment and CI

- A push to `main` runs `.github/workflows/hugo.yml`: install Hugo, run the research checks, build with `--minify`, and deploy to GitHub Pages. The custom domain comes from `static/CNAME`.
- Pull requests against `main` run `pr-checks.yml` (purity and smoke) and the `hugo.yml` build without deploying.
- Nothing is live until it merges to `main`.

## Gotchas

- `[menu.main]` in `hugo.toml` renders nothing. The navigation is hard-coded in `layouts/partials/topbar.html`.
- CI checks out a shallow clone, so `.GitInfo` is nil there. Features that need Git history also need `fetch-depth: 0`.
- About 18 CSS rules key off `body[data-section="financials"]` (drop caps, ticker chips, disclaimer). Moving financial content to another section drops those styles.
- The theme toggle stores `theme` in `localStorage`. `baseof.html` applies it before first paint.
- The smoke test launches Playwright's bundled Chromium. If the download stalls, run the same checks with `chromium.launch({ channel: 'chrome' })` in a throwaway copy of the script. Do not change the committed test for this.

## Contributing

- Work on a feature branch, not directly on `main`. Open a pull request against `main`.
- Commit messages use Conventional Commits: `feat`, `fix`, `docs`, `style`, `refactor`, `build`, `ci`, `chore`, `perf`, `test`. Keep each commit to one concern. Do not add AI or agent attribution trailers or session links.
- Do not commit or push unless Rohit asks for it in the current session.
- Track work in `bd` (see "Task Tracking").
- Before you report work as done, run the checks in "Verification before you report done" and list the commands you ran.
- Show file paths to Rohit as full absolute paths.

## Site Design System (silent.engineer)

These rules apply to every new page, post, project, layout, and style change. Follow them without being asked. They override the `silent-engineer-design` skill where the two disagree: this site uses no Inter, no em dashes, no colored left stripes, and no hover transitions.

Do not change the project card layout, the fonts, or the palette without approval from Rohit.

### Palette

- Use the tokens in `assets/css/style.css` `:root` and `html[data-theme="dark"]`. Do not add a new color.
- Surfaces: `--bg` #E8DCC4 (sand), `--surface` #F2E8D0, `--surface-2` #DCD0B8. Ink: `--ink` #3D2E1B, `--muted`, `--dim`, `--line`.
- One accent: `--accent` #B85825 (burnt sienna). Use it for links, hover, focus, and small highlights.
- `--success`, `--warn`, and `--danger` are for research ratings only.
- Never use pure white (`#fff`), black backgrounds, gradients, neon, purple, pastel fills, or rainbow palettes.
- Every new component must work in light and dark themes. Dark mode is warm brown, not black.

### Type

- The site uses two families. Both are self-hosted in `static/fonts/` under the SIL OFL (license files sit beside the fonts). The `@font-face` rules are at the top of `assets/css/style.css`.
- Do not load fonts from Google Fonts or any other CDN. Do not use Inter, Geist, Space Grotesk, IBM Plex, or a system sans.
- `--font-display` (Departure Mono): headings, labels, nav, buttons, metadata, numbers, code, and diagram labels. Set labels in uppercase with 0.10em to 0.22em letter-spacing.
- `--font-body` ("EB Garamond Text", EB Garamond at `size-adjust: 112%`): running text.
- `--font-serif` (EB Garamond): italic descriptions, captions, and ledes.
- To add a weight or script, add the woff2 file to `static/fonts/` and an `@font-face` rule. Do not add a third family.

### Shape, depth, and motion

- `border-radius: 0` everywhere. The only exception is the 2px radius on rating chips.
- Draw structure with 1px `var(--ink)` borders and `var(--line)` hairlines.
- No `box-shadow`, `backdrop-filter`, glass effects, radial orbs, dot grids, or bento grids.
- No colored left stripe (a thick `border-left` in a color). To emphasize a block, use a full 1px border, a `--surface` fill, or top and bottom rules.
- No `transition`, `animation`, or `@keyframes`. Hover changes state instantly: text goes to `--accent`, or the row inverts to ink on sand.
- Keep the `:focus-visible` accent outline on every interactive element.

### Icons and glyphs

- Do not add icon libraries (Lucide, Heroicons, Font Awesome, or similar), emoji, sparkle icons, or checkmark bullets.
- Use static Unicode glyphs only: `→ ← ↗ ▶ ▼ ◐ ·`. Do not animate arrows.
- Every project has its own wax-seal stamp in `layouts/partials/proj-stamp.html`. The comment block at the top of that file is the stamp specification. Read it before you draw a stamp.

### Projects

- `data/projects.yaml` is the only source. It is a flat list. The file order is the page order.
- Fields: `slug`, `title`, `short` (mono sub-label), `url`, `repo` (optional), `description`, `status`.
- `url` is where the card goes when clicked. Use the live site if one exists. Otherwise use the GitHub repository. Set `repo` only when `url` is a live site; the card then shows a secondary `GITHUB ↗` link.
- Before you use a live site as `url`, confirm that it loads: `curl -s -o /dev/null -w '%{http_code}' <url>` must return 200.
- The description is one or two factual sentences taken from the repository README. Do not claim a feature that the repository does not show. Do not add stars, badges, language dots, or invented metrics.
- Each project renders as a `.proj-card`: a flat 1px rectangle with the stamp on the left and the name, `short`, description, and link on the right. The title link stretches over the whole card (`.proj-cover::after`), so a click anywhere opens the project in a new tab.
- `/projects/` shows every entry. The home page shows the first four. Keep `other-projects` as the last entry.
- To add a project:
  1. Add the entry to `data/projects.yaml`.
  2. Add a stamp branch to `layouts/partials/proj-stamp.html`, and add the motif to the reference list in its comment.
  3. Check the stamp at 88px and 64px in light and dark themes.
  4. Click the new card and confirm that it opens the correct destination.

### Pages and writing

- Write new pages in Markdown under `content/` with `title`, `date`, `draft`, and `description` in the front matter. Use the existing layouts. Add a new layout only when no existing layout fits.
- Do not use em dashes. Rewrite the sentence with a period, comma, colon, or parentheses. Keep verbatim third-party quotations unchanged.
- Do not use the "It's not X, it's Y" formula. State the point directly.
- Do not use stock openers ("grab a coffee", "settle in") or marketing filler.
- Do not add fake testimonials, pricing tiers, invented demos, or placeholder content. A Demo or Docs link must point to a page that exists.
- Use words, not glyphs, for status: Met, Partial, Unmet. `normalize_status_glyphs()` in `scripts/sync-research.py` does this for ingested research reports.
- Known gap: the generated reports in `content/research/` still contain em dashes. Fix this in the report generator, not by hand.

### Diagrams

- `layouts/partials/mermaid-loader.html` sets the Mermaid theme for the whole site: base theme, sand plate, ink lines, and Departure Mono labels. Do not add `%%{init}%%` blocks or custom color `classDef`s to posts.

### Privacy and terms

- `content/privacy.md` lists every third party that the site loads. If you add an external script, font, image host, or embed, update `content/privacy.md` in the same change.
- `content/terms.md` holds the site-use terms and the investment disclaimer.

### Verification before you report done

```bash
hugo --gc --minify -d /tmp/site-check          # must exit 0 with no ERROR lines
(cd tests && npm run purity)
uv run --with beautifulsoup4 --with lxml --with pytest pytest scripts/test_sync_research.py -q

# Banned patterns: both commands must print nothing.
rg -n "transition:|animation:|@keyframes|gradient\(|box-shadow|backdrop-filter|fonts\.googleapis|'Inter'|#fff\b" assets/css layouts
rg -n '[✓✔✅❌⚠✨🚀🎉]' content layouts data

# Smoke test against a running server.
hugo server -D --port 1313 --bind 127.0.0.1 --disableFastRender
(cd tests && BASE_URL=http://127.0.0.1:1313 npm run smoke)
```

- Known smoke failures that also occur on `main` (tracked in bead `caretak3r_github_io-tvt`): the home lede text check, the engineering filter, and the mobile `/research/` overflow. A local run also reports the missing `/favicon.ico` (404). These are not regressions. Do not add new failures.
- Take screenshots at 1440px and 393px wide, in light and dark themes. Confirm that the page does not scroll horizontally.

## Task Tracking (beads)

This project uses **bd** (beads) for issue tracking. Run `bd prime` for full workflow context.

> **Architecture in one line:** Issues live in a local Dolt database
> (`.beads/dolt/`); cross-machine sync uses `bd dolt push/pull` (a
> git-compatible protocol), stored under `refs/dolt/data` on your git
> remote — separate from `refs/heads/*` where your code lives.
> `.beads/issues.jsonl` is a passive export, not the wire protocol.
>
> See [SYNC_CONCEPTS.md](https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md)
> for the one-screen overview and anti-patterns (don't treat JSONL as the
> source of truth; don't `bd import` during normal operation; don't
> reach for third-party Dolt hosting before trying the default).

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
bd close <id>         # Complete work
bd dolt push          # Push beads data to remote
```

### Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:970c3bf2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

<!-- BEGIN BEADS CODEX SETUP: generated by bd setup codex -->
## Beads Issue Tracker

Use Beads (`bd`) for durable task tracking in repositories that include it. Use the `beads` skill at `.agents/skills/beads/SKILL.md` (project install) or `~/.agents/skills/beads/SKILL.md` (global install) for Beads workflow guidance, then use the `bd` CLI for issue operations.

### Quick Reference

```bash
bd ready                # Find available work
bd show <id>            # View issue details
bd update <id> --claim  # Claim work
bd close <id>           # Complete work
bd prime                # Refresh Beads context
```

### Rules

- Use `bd` for all task tracking; do not create markdown TODO lists.
- Run `bd prime` when Beads context is missing or stale. Codex 0.129.0+ can load Beads context automatically through native hooks; use `/hooks` to inspect or toggle them.
- Keep persistent project memory in Beads via `bd remember`; do not create ad hoc memory files.

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.
<!-- END BEADS CODEX SETUP -->
