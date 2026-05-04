// Filter + sort behavior for engineering / research ledger tables.
// Wired from layouts/partials/listing-script.html. Defer-loaded.
(function () {
  'use strict';

  var ledger = document.querySelector('.ledger');
  if (!ledger) return;
  var tbody = ledger.querySelector('tbody');
  if (!tbody) return;
  var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));

  function parseFilterToken(text) {
    // "OVERWEIGHT (5)" → "OVERWEIGHT"; "ALL" → "ALL"
    return text.replace(/\s*\(.*\)\s*$/, '').trim().toUpperCase();
  }

  // ---- FILTER ----
  var filterBtns = document.querySelectorAll('.filter-row button');
  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      filterBtns.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var want = parseFilterToken(btn.textContent);
      rows.forEach(function (r) {
        var t = (r.getAttribute('data-type') || '').toUpperCase();
        r.hidden = !(want === 'ALL' || t === want);
      });
    });
  });

  // ---- SORT (date asc / desc toggle) ----
  var sort = document.querySelector('.filter-row .sort-label');
  if (!sort) return;
  sort.style.cursor = 'pointer';
  sort.style.userSelect = 'none';
  sort.setAttribute('role', 'button');
  sort.setAttribute('tabindex', '0');
  sort.setAttribute('aria-label', 'Toggle sort by date');

  var asc = false;
  function applySort() {
    var sorted = rows.slice().sort(function (a, b) {
      var da = a.getAttribute('data-date') || '';
      var db = b.getAttribute('data-date') || '';
      return asc ? da.localeCompare(db) : db.localeCompare(da);
    });
    sorted.forEach(function (r) { tbody.appendChild(r); });
    sort.textContent = asc ? 'SORT: DATE ▲' : 'SORT: DATE ▼';
  }
  function toggleSort() { asc = !asc; applySort(); }

  sort.addEventListener('click', toggleSort);
  sort.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleSort();
    }
  });
})();
