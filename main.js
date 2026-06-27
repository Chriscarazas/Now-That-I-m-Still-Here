/* ============================================================
   main.js — chriscarazas.com
   Nav scroll, mobile toggle, slideshows, scroll reveal,
   podcast feed toggle. Written from scratch to replace
   inline scripts.
   ============================================================ */

'use strict';

/* NAV SCROLL */
(function () {
  var nav = document.querySelector('nav');
  if (!nav) return;
  function tick() { nav.classList.toggle('scrolled', window.scrollY > 1); }
  window.addEventListener('scroll', tick, { passive: true });
  tick();
}());

/* MOBILE NAV TOGGLE */
(function () {
  var nav   = document.querySelector('nav');
  var btn   = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (!btn || !links) return;

  function closeNav() {
    links.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
    btn.textContent = 'Menu';
  }

  btn.addEventListener('click', function (e) {
    e.stopPropagation(); /* prevent the document listener from immediately closing it */
    var open = links.classList.toggle('open');
    btn.setAttribute('aria-expanded', String(open));
    btn.textContent = open ? 'Close' : 'Menu';
  });

  /* Close when a nav link is clicked */
  links.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', closeNav);
  });

  /* Close when clicking anywhere outside the nav */
  document.addEventListener('click', function (e) {
    if (links.classList.contains('open') && nav && !nav.contains(e.target)) {
      closeNav();
    }
  });

  /* Close on Escape key */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && links.classList.contains('open')) {
      closeNav();
      btn.focus();
    }
  });
}());

/* SLIDESHOW FACTORY */
function makeSlideshow(slides, dots, prev, next, activeSlide, activeDot, interval) {
  if (!slides.length) return;
  var cur = 0;
  var timer;

  function show(n) {
    slides[cur].classList.remove(activeSlide);
    if (dots[cur]) { dots[cur].classList.remove(activeDot); dots[cur].setAttribute('aria-selected', 'false'); }
    cur = (n + slides.length) % slides.length;
    slides[cur].classList.add(activeSlide);
    if (dots[cur]) { dots[cur].classList.add(activeDot); dots[cur].setAttribute('aria-selected', 'true'); }
  }

  function restart() {
    if (!interval) return;
    clearInterval(timer);
    timer = setInterval(function () { show(cur + 1); }, interval);
  }

  if (prev) prev.addEventListener('click', function () { show(cur - 1); restart(); });
  if (next) next.addEventListener('click', function () { show(cur + 1); restart(); });
  dots.forEach(function (d, i) {
    d.addEventListener('click', function () { show(i); restart(); });
  });

  show(0);
  restart();
}

/* QUOTE SLIDESHOW */
(function () {
  var slides = Array.from(document.querySelectorAll('.qs-slide'));
  var dots   = Array.from(document.querySelectorAll('.qs-dot'));
  var arrows = document.querySelectorAll('.qs-arrow');
  makeSlideshow(slides, dots, arrows[0], arrows[1], 'active', 'active', 6000);
}());

/* REVIEW SLIDESHOW */
(function () {
  var slides = Array.from(document.querySelectorAll('.rslide'));
  var dots   = Array.from(document.querySelectorAll('.rslide-dot'));
  var arrows = document.querySelectorAll('.rslide-arrow');
  makeSlideshow(slides, dots, arrows[0], arrows[1], 'rslide-active', 'rslide-dot-active', 7000);
}());

/* SCROLL REVEAL */
(function () {
  var els = document.querySelectorAll('.fade-up');
  if (!els.length) return;
  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('visible'); });
    return;
  }
  var obs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  els.forEach(function (el) { obs.observe(el); });
}());

/* PODCAST FEED TOGGLE */
(function () {
  var btn  = document.querySelector('.pod-feed-toggle');
  var list = document.querySelector('.pod-feed-list');
  if (!btn || !list) return;
  btn.addEventListener('click', function () {
    var expanded = list.classList.toggle('expanded');
    btn.textContent = expanded ? 'Show fewer conversations' : 'Show all 17 conversations';
  });
}());
