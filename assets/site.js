/* TRC Tracker — header behaviour, scroll reveal and Calls directory filters */
window.addEventListener('load', function () {
  if (!window.AOS) {
    Array.prototype.forEach.call(document.querySelectorAll('[data-aos]'), function (el) { el.classList.add('aos-animate'); });
    return;
  }
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  AOS.init({ once: true, duration: 500, offset: 40, disable: reduce });
});
(function () {
  'use strict';
  var root = document.documentElement;
  var header = document.querySelector('.site-header');
  var sticky = document.querySelector('[data-sticky]') || header;

  function setHeaderHeight() {
    if (sticky) root.style.setProperty('--hdr-h', sticky.offsetHeight + 'px');
  }
  var isD = header && header.classList.contains('hdr-d');
  function onScroll() {
    var y = window.scrollY, on = root.classList.contains('scrolled');
    var limit = isD ? header.offsetHeight - 4 : 40;
    var next = on ? y > limit - 30 : y > limit;
    if (next !== on) { root.classList.toggle('scrolled', next); setTimeout(setHeaderHeight, 300); }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', setHeaderHeight);
  onScroll();
  setHeaderHeight();
  if (header) header.addEventListener('transitionend', setHeaderHeight);

  // Phone menu (header style A)
  var toggle = document.querySelector('.hdr-toggle');
  if (toggle && header) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      header.classList.toggle('open', open);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && header.classList.contains('open')) {
        toggle.setAttribute('aria-expanded', 'false');
        header.classList.remove('open');
        toggle.focus();
      }
    });
  }

  // Calls directory
  var list = document.getElementById('calls');
  if (!list) return;
  var cards = Array.prototype.slice.call(list.querySelectorAll('.call'));
  var search = document.getElementById('search');
  var topic = document.getElementById('topic');
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var status = '';
  var groups = Array.prototype.slice.call(list.querySelectorAll('.group'));
  var parts = Array.prototype.slice.call(list.querySelectorAll('.part'));
  var saved = null;

  function render() {
    var q = (search.value || '').toLowerCase().trim();
    var num = /^#?\d{1,2}$/.test(q) ? q.replace('#', '') : null;
    var shown = 0;
    cards.forEach(function (c) {
      var ok = (!topic.value || c.dataset.topic === topic.value) &&
        (!status || c.dataset.status === status) &&
        (!q || (num ? c.id === 'call-' + num : c.dataset.search.indexOf(q) !== -1));
      c.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = shown + ' of 94 Calls to Action';
    empty.hidden = shown !== 0;
    var filtering = !!(q || topic.value || status);
    if (filtering && !saved) saved = groups.map(function (g) { return g.open; });
    groups.forEach(function (g, i) {
      var n = g.querySelectorAll('.call:not([hidden])').length;
      g.hidden = n === 0;
      if (filtering) { g.open = n > 0; g.classList.add('aos-animate'); }
      else if (saved) g.open = saved[i];
    });
    if (!filtering) saved = null;
    parts.forEach(function (p) {
      var next = p.nextElementSibling, any = false;
      while (next && next.classList.contains('group')) { if (!next.hidden) any = true; next = next.nextElementSibling; }
      p.hidden = !any;
    });
  }
  search.addEventListener('input', render);
  topic.addEventListener('change', render);
  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      status = status === b.dataset.status ? '' : b.dataset.status;
      chips.forEach(function (o) { o.setAttribute('aria-pressed', String(o.dataset.status === status)); });
      render();
    });
  });
  document.getElementById('reset').addEventListener('click', function () {
    search.value = ''; topic.value = ''; status = '';
    chips.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
    render(); search.focus();
  });

  // Open a Call from the address (#call-12) and focus search from #search
  function fromHash() {
    var h = location.hash;
    if (h === '#search') { search.focus(); return; }
    var m = /^#call-(\d{1,2})$/.exec(h);
    if (m) {
      var el = document.getElementById('call-' + m[1]);
      if (el) {
        if (el.hidden) { search.value = ''; topic.value = ''; status = ''; render(); }
        var g = el.closest('.group');
        if (g) { g.open = true; g.classList.add('aos-animate'); }
        el.querySelector('details').open = true;
        el.scrollIntoView();
      }
    }
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();

  list.addEventListener('click', function (e) {
    var a = e.target.closest('.copy-link');
    if (!a || !navigator.clipboard) return;
    e.preventDefault();
    var url = location.origin + '/#call-' + a.dataset.call;
    navigator.clipboard.writeText(url).then(function () {
      var t = a.textContent; a.textContent = 'Link copied'; setTimeout(function () { a.textContent = t; }, 1600);
      history.replaceState(null, '', '#call-' + a.dataset.call);
    });
  });
})();
