/* report-nav.js — viewport-bound reading aids
 * - Active-section highlight in the right-rail TOC
 * - Scroll-progress CSS variable on <html>
 *
 * Heading IDs and the TOC markup itself are emitted server-side now —
 * see scripts/backfill-toc.py and the upstream sef-research-report
 * generator (build_report → _inject_section_ids_and_toc). This file is
 * intentionally only the bits that need a viewport to mean anything. */
(function () {
  'use strict';

  var shell = document.querySelector('.report-shell');
  if (!shell) return;

  // ---------- Active-section observer ----------
  var headings = Array.prototype.slice.call(
    shell.querySelectorAll('h2[id]')
  );
  var links = Array.prototype.slice.call(
    document.querySelectorAll('.report-toc-link')
  );
  if (links.length > 0 && headings.length > 0 && 'IntersectionObserver' in window) {
    var byId = Object.create(null);
    links.forEach(function (l) { byId[l.getAttribute('data-section')] = l; });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          links.forEach(function (l) { l.classList.remove('is-active'); });
          var link = byId[e.target.id];
          if (link) link.classList.add('is-active');
        }
      });
    }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });
    headings.forEach(function (h) { io.observe(h); });
  }

  // ---------- Scroll progress ----------
  var raf = null;
  function update() {
    raf = null;
    var doc = document.documentElement;
    var max = doc.scrollHeight - window.innerHeight;
    var pct = max > 0 ? (window.scrollY / max) * 100 : 0;
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    doc.style.setProperty('--scroll-progress', pct.toFixed(2) + '%');
  }
  function schedule() {
    if (raf == null) raf = window.requestAnimationFrame(update);
  }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  update();
})();
