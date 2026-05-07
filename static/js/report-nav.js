/* report-nav.js — research report reading aids
 * - Assigns IDs to h2.section and h2[Portfolio Decision] so anchors work
 * - Builds a right-rail TOC that highlights the section in view
 * - Tracks scroll progress as --scroll-progress on <html>
 * No deps. Safe to no-op if .report-shell isn't on the page. */
(function () {
  'use strict';

  var shell = document.querySelector('.report-shell');
  if (!shell) return;

  // ---------- 1. Slug + assign IDs ----------
  var slugTaken = Object.create(null);
  function slugify(text) {
    var base = 'sec-' + (text || '')
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    if (!slugTaken[base]) {
      slugTaken[base] = 1;
      return base;
    }
    slugTaken[base] += 1;
    return base + '-' + slugTaken[base];
  }

  var headings = Array.prototype.slice.call(
    shell.querySelectorAll('h2.section, .decision-box > h2')
  );
  headings.forEach(function (h) {
    if (!h.id) h.id = slugify(h.textContent);
  });

  // ---------- 2. Build TOC ----------
  var toc = document.querySelector('.report-toc');
  if (toc && headings.length > 0) {
    var list = document.createElement('ol');
    list.className = 'report-toc-list';
    headings.forEach(function (h) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.className = 'report-toc-link';
      a.setAttribute('data-section', h.id);
      a.textContent = (h.textContent || '').trim();
      li.appendChild(a);
      list.appendChild(li);
    });
    toc.appendChild(list);
    toc.hidden = false;
  }

  // ---------- 3. Active-section observer ----------
  var links = Array.prototype.slice.call(
    document.querySelectorAll('.report-toc-link')
  );
  if (links.length > 0 && 'IntersectionObserver' in window) {
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

  // ---------- 4. Scroll progress ----------
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
