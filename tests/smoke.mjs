// Headless behavioral + visual smoke test for silent.engineer.
// Assumes a Hugo dev server is running at $BASE_URL (default http://127.0.0.1:1313).
// Exits 1 if any check fails or any console / network error is observed.

import { chromium } from 'playwright';

const BASE = process.env.BASE_URL || 'http://127.0.0.1:1313';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();

const errs = [];
page.on('pageerror', e => errs.push(`pageerror: ${e.message}`));
page.on('console', m => {
  if (m.type() === 'error') errs.push(`console.error: ${m.text()}`);
});
page.on('response', r => {
  // Allow live-reload (dev server) probes; flag everything else.
  if (r.status() >= 400 && !r.url().includes('livereload')) {
    errs.push(`HTTP ${r.status()} ${r.url()}`);
  }
});

let failed = 0;
async function check(label, fn) {
  try {
    await fn();
    console.log(`  PASS ${label}`);
  } catch (e) {
    failed += 1;
    console.log(`  FAIL ${label}`);
    console.log(`        ${e.message}`);
  }
}

// ---- HOME ----
console.log('--- HOME ---');
await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
await check('lede mentions "10-year platform / infrastructure"', async () => {
  const txt = await page.locator('.lede').textContent();
  if (!/10-year platform \/ infrastructure/.test(txt)) throw new Error(`got: ${txt}`);
});
await check('resume link present (a.resume-link → /Rohit%20Gudi.pdf)', async () => {
  const href = await page.locator('a.resume-link').getAttribute('href');
  if (href !== '/Rohit%20Gudi.pdf') throw new Error(`href: ${href}`);
});
await check('no AI-augmented or TradingAgents text on rendered page', async () => {
  const body = await page.locator('body').innerText();
  if (/AI[- ]augmented|TradingAgents/i.test(body)) throw new Error('found banned text');
});
await check('topbar exposes 5 nav anchors + brand', async () => {
  const links = await page.locator('.topbar a').count();
  if (links !== 6) throw new Error(`expected 6 anchors (brand + 5 tabs), got ${links}`);
});
await check('home projects strip caps to 3', async () => {
  const n = await page.locator('.projects-grid .proj').count();
  if (n > 3) throw new Error(`projects=${n} (expected ≤3)`);
});

// ---- ENGINEERING ----
console.log('--- ENGINEERING ---');
await page.goto(`${BASE}/engineering/`, { waitUntil: 'networkidle' });
await check('filter buttons hide rows when clicked', async () => {
  await page.waitForSelector('.filter-row button');
  const total = await page.locator('.ledger tbody tr').count();
  await page.locator('.filter-row button:has-text("PROJECT")').click();
  await page.waitForTimeout(150);
  const visible = await page.locator('.ledger tbody tr:not([hidden])').count();
  if (visible === 0) throw new Error('filter hid every row');
  if (visible === total) throw new Error('filter changed nothing');
});
await check('SORT: DATE label flips arrow on click', async () => {
  const before = await page.locator('.sort-label').textContent();
  await page.locator('.sort-label').click();
  await page.waitForTimeout(150);
  const after = await page.locator('.sort-label').textContent();
  if (before === after) throw new Error(`label unchanged: ${before}`);
  if (!/▲|▼/.test(after)) throw new Error(`no arrow in: ${after}`);
});

// ---- RESEARCH ----
console.log('--- RESEARCH ---');
await page.goto(`${BASE}/research/`, { waitUntil: 'networkidle' });
await check('OVERWEIGHT filter narrows the row set', async () => {
  await page.waitForSelector('.filter-row button');
  const total = await page.locator('.ledger tbody tr').count();
  await page.locator('.filter-row button:has-text("OVERWEIGHT")').click();
  await page.waitForTimeout(150);
  const visible = await page.locator('.ledger tbody tr:not([hidden])').count();
  if (visible === 0 || visible === total) {
    throw new Error(`visible=${visible} total=${total} — filter ineffective`);
  }
});

// ---- FINANCIALS / PROJECTS landing ----
for (const slug of ['/financials/', '/projects/']) {
  console.log(`--- ${slug} ---`);
  const r = await page.goto(`${BASE}${slug}`, { waitUntil: 'networkidle' });
  await check(`${slug} returns 2xx`, async () => {
    if (!r.ok()) throw new Error(`status ${r.status()}`);
  });
}

// ---- MERMAID DIAGRAM POST ----
console.log('--- MERMAID POST ---');
await page.goto(`${BASE}/posts/how-does-helm-work-diagram/`, { waitUntil: 'networkidle' });
await page.waitForTimeout(800); // mermaid renders async via ESM
await check('clickable .mermaid-zoomable + caption present', async () => {
  await page.waitForSelector('.mermaid-zoomable', { timeout: 5000 });
  const cap = await page.locator('.mermaid-caption').first().textContent();
  if (!/CLICK TO ENLARGE/.test(cap)) throw new Error(`caption: ${cap}`);
});
await check('clicking diagram opens lightbox dialog (open=true)', async () => {
  await page.locator('.mermaid-zoomable').first().click();
  await page.waitForTimeout(200);
  const open = await page.locator('#mermaid-lightbox').evaluate(d => d.open);
  if (!open) throw new Error('dialog did not open');
  await page.keyboard.press('Escape');
});

// ---- WIDE TABLE POST ----
console.log('--- WIDE TABLE POST ---');
const tablePost = '/posts/a-comparative-analysis-of-allegations-and-subsequent-verifications-pertaining-to-quantumscape-corporations-technological-viability/';
await page.goto(`${BASE}${tablePost}`, { waitUntil: 'networkidle' });
await check('article tables fit viewport (no horizontal page scroll)', async () => {
  const m = await page.evaluate(() => ({
    docW: document.documentElement.scrollWidth,
    vw: window.innerWidth,
  }));
  if (m.docW > m.vw + 2) throw new Error(`docW=${m.docW} vw=${m.vw}`);
});
await check('article table headers have a non-transparent background', async () => {
  const bg = await page.locator('.article-content table th').first()
    .evaluate(el => getComputedStyle(el).backgroundColor);
  if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') {
    throw new Error(`th background: ${bg}`);
  }
});
await check('dark mode keeps article table headers legible', async () => {
  await page.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await page.waitForTimeout(150);
  const bg = await page.locator('.article-content table th').first()
    .evaluate(el => getComputedStyle(el).backgroundColor);
  if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') {
    throw new Error(`dark th background: ${bg}`);
  }
});

// ---- MOBILE VIEWPORT (393x852, iPhone-class) ----
console.log('--- MOBILE OVERFLOW ---');
const mobile = await browser.newPage({ viewport: { width: 393, height: 852 } });
const mobileChecks = [
  ['/', 'home'],
  ['/engineering/', 'engineering'],
  ['/research/', 'research'],
  ['/projects/', 'projects'],
  ['/financials/', 'financials'],
  [tablePost, 'wide-table-post'],
];
for (const [url, label] of mobileChecks) {
  await mobile.goto(`${BASE}${url}`, { waitUntil: 'networkidle' });
  await check(`mobile ${label} no horizontal page scroll`, async () => {
    const m = await mobile.evaluate(() => ({
      docW: document.documentElement.scrollWidth,
      vw: window.innerWidth,
    }));
    if (m.docW > m.vw + 2) throw new Error(`docW=${m.docW} vw=${m.vw}`);
  });
}

// ---- DONE ----
await browser.close();

if (errs.length) {
  console.log('\n--- console / network errors observed:');
  errs.slice(0, 20).forEach(e => console.log(`  ${e}`));
  if (errs.length > 20) console.log(`  …and ${errs.length - 20} more`);
  failed += errs.length;
}

if (failed) {
  console.log(`\nFAIL: ${failed} issue(s)`);
  process.exit(1);
}
console.log('\nOK: all smoke checks passed');
