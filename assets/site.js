/* TRC Tracker — header behaviour and Calls directory filters */
(function () {
  'use strict';
  var root = document.documentElement;
  var header = document.querySelector('.site-header');
  var sticky = document.querySelector('[data-sticky]') || header;

  function setHeaderHeight() {
    if (sticky) root.style.setProperty('--hdr-h', sticky.offsetHeight + 'px');
  }
  function onScroll() {
    root.classList.toggle('scrolled', header && header.classList.contains('hdr-d') ? window.scrollY > header.offsetHeight - 4 : window.scrollY > 40);
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
