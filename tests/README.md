# tests/

PR-time smoke tests for silent.engineer. Two layers:

| Test | What it catches | Runtime |
|------|-----------------|---------|
| `purity.mjs` | Re-introduction of banned phrases (AI-augmented / TradingAgents) anywhere in `content/`, `layouts/`, `assets/`, `hugo.toml`. | <1s |
| `smoke.mjs` | Behavior + visual regressions: filter buttons, sort toggle, mermaid lightbox, table header contrast, mobile horizontal-overflow on six key URLs. Also fails on any console error or HTTP 4xx/5xx. | ~25s |

## Run locally

```sh
# Terminal 1
hugo server -D --port 1313 --bind 127.0.0.1 --disableFastRender

# Terminal 2
cd tests
npm install
npx playwright install --with-deps chromium
npm run purity
npm run smoke
# Override base URL if you serve elsewhere:
BASE_URL=http://localhost:1313 npm run smoke
```

## What the smoke test asserts

- Home: lede copy, resume link, banned phrases scrubbed, topbar has 5 tabs, projects strip ≤3.
- `/engineering/`: clicking a filter button hides rows; SORT label flips arrow.
- `/research/`: OVERWEIGHT filter narrows the row set.
- `/projects/`, `/financials/`: 2xx responses (catches the broken redirect bug we just fixed).
- Mermaid post: `.mermaid-zoomable` exists, click opens the `<dialog>` lightbox.
- Wide-table post: tables fit viewport, headers have non-transparent background in light AND dark mode.
- Mobile (393×852): no horizontal page scroll on six key URLs.
- Zero console errors. Zero non-livereload 4xx/5xx.

## Adding a check

Edit `smoke.mjs`, add another `await check('label', async () => {...})`. Throw to fail.
