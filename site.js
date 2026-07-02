(() => {
  // Let page-specific title-sequence motion begin only after the document is ready.
  requestAnimationFrame(() => document.body.classList.add('is-loaded'));

  const menuButton = document.querySelector('.nav-toggle');
  const nav = document.getElementById('primary-nav');
  if (menuButton && nav) {
    nav.addEventListener('click', (event) => { if (event.target.closest('a')) { nav.classList.remove('open'); menuButton.setAttribute('aria-expanded','false'); } });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape') { nav.classList.remove('open'); menuButton.setAttribute('aria-expanded','false'); } });
    menuButton.addEventListener('click', () => {
      const open = menuButton.getAttribute('aria-expanded') === 'true';
      menuButton.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('open', !open);
    });
    document.addEventListener('click', (event) => {
      if (!nav.classList.contains('open') || nav.contains(event.target) || menuButton.contains(event.target)) return;
      nav.classList.remove('open');
      menuButton.setAttribute('aria-expanded', 'false');
    });
  }

  // Announce new-window behavior without burdening the visible Victorian labels.
  document.querySelectorAll('a[target="_blank"]').forEach((link) => {
    if (link.querySelector('.new-window-note')) return;
    const note = document.createElement('span');
    note.className = 'sr-only new-window-note';
    note.textContent = ' (opens in a new tab)';
    link.append(note);
  });

  const dropdowns = [...document.querySelectorAll('[data-getbook]')];
  const closeDropdowns = (except = null) => {
    dropdowns.forEach((wrap) => {
      if (wrap === except) return;
      const button = wrap.querySelector('button');
      const panel = wrap.querySelector('.getbook-panel');
      button?.setAttribute('aria-expanded', 'false');
      if (panel) panel.hidden = true;
    });
  };
  dropdowns.forEach((wrap) => {
    const button = wrap.querySelector('button');
    const panel = wrap.querySelector('.getbook-panel');
    if (!button || !panel) return;
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      const open = button.getAttribute('aria-expanded') === 'true';
      closeDropdowns(wrap);
      button.setAttribute('aria-expanded', String(!open));
      panel.hidden = open;
      if (!open) panel.querySelector('a')?.focus();
    });
    wrap.addEventListener('keydown', (event) => {
      const items = [...panel.querySelectorAll('a')];
      const index = items.indexOf(document.activeElement);
      if (event.key === 'Escape') {
        panel.hidden = true;
        button.setAttribute('aria-expanded', 'false');
        button.focus();
      } else if (event.key === 'ArrowDown' && !panel.hidden) {
        event.preventDefault();
        items[(index + 1 + items.length) % items.length]?.focus();
      } else if (event.key === 'ArrowUp' && !panel.hidden) {
        event.preventDefault();
        items[(index - 1 + items.length) % items.length]?.focus();
      }
    });
  });
  document.addEventListener('click', () => closeDropdowns());

  document.querySelectorAll('[data-year]').forEach((el) => el.textContent = new Date().getFullYear());

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const revealNodes = [...document.querySelectorAll('[data-reveal]')];
  if (reduced || !('IntersectionObserver' in window)) {
    revealNodes.forEach((node) => node.classList.add('is-visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    revealNodes.forEach((node) => observer.observe(node));
  }

  const progressBar = document.querySelector('.nav-progress span');
  const updateProgress = () => {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
    if (progressBar) progressBar.style.width = `${pct}%`;
  };
  let progressQueued = false;
  const queueProgress = () => {
    if (progressQueued) return;
    progressQueued = true;
    requestAnimationFrame(() => { updateProgress(); progressQueued = false; });
  };
  window.addEventListener('scroll', queueProgress, { passive: true });
  updateProgress();


  // Page-view signals for the core conversion funnel.
  const path = location.pathname;
  const funnelEvent = path === '/sample/' ? 'sample_view' : path === '/buy/' ? 'buy_page_view' : path === '/book/' ? 'book_page_view' : '';
  if (funnelEvent) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: funnelEvent, page: path });
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest('[data-event]');
    if (!link) return;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: link.dataset.event, page: location.pathname, destination: link.href || '' });
  });
})();


// Archive publication details
(() => {
  document.querySelectorAll('.katie-card-interlude h2, .archive-hero h1').forEach((el) => el.classList.add('red-proof'));
  document.querySelectorAll('.artifact-entry').forEach((entry, index) => entry.style.setProperty('--archive-order', index + 1));
})();


// Same-origin, last-known-good Substack cache.
(async () => {
  const target = document.getElementById('substack-posts');
  if (!target) return;
  const status = document.getElementById('feed-status');
  try {
    const response = await fetch('/data/substack-posts.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Feed cache unavailable');
    const payload = await response.json();
    const posts = Array.isArray(payload.posts) ? payload.posts.filter((post) => post?.title && post?.url) : [];
    if (!posts.length) throw new Error('Feed cache empty');
    const fragment = document.createDocumentFragment();
    posts.slice(0, 3).forEach((post) => {
      const article = document.createElement('article');
      article.className = 'rss-card';
      const label = document.createElement('span'); label.textContent = post.date || 'Latest essay';
      const heading = document.createElement('h3'); heading.textContent = post.title;
      const excerpt = document.createElement('p'); excerpt.textContent = post.excerpt || 'Read the latest essay on Substack.';
      const link = document.createElement('a');
      if (post.internalPath) {
        link.href = post.internalPath;
        link.textContent = 'Read the preview →';
        link.dataset.event = 'owned_essay_preview_click';
      } else {
        link.href = post.url;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = 'Read on Substack →';
        link.dataset.event = 'substack_read_click';
      }
      article.append(label, heading, excerpt, link); fragment.append(article);
    });
    target.replaceChildren(fragment);
    if (status && payload.generatedAt) {
      const refreshed = new Date(payload.generatedAt);
      const ageDays = (Date.now() - refreshed.getTime()) / 86400000;
      status.textContent = ageDays > 7
        ? `Showing the latest verified archive cached ${refreshed.toLocaleDateString()}.`
        : `Feed refreshed ${refreshed.toLocaleDateString()}.`;
    }
  } catch (error) {
    if (status) status.textContent = 'Showing the editorial selection while the live archive catches its breath.';
  }
})();
