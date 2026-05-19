// TOC active-link highlighter + collapsible subsections.
//
// Active-link highlight: "last heading whose top has crossed the trigger
// line" (same algorithm as the page-sidebar scrollspy below).
//
// Collapse: each top-level #TableOfContents > ul > li (level-agnostic) with
// a child <ul> gets a .toc-toggle button; its child <ul> is wrapped in an
// animatable .toc-disclosure. Scrollspy keeps exactly the active section
// expanded (instant, no animation, clears manual "peek"). A manual chevron
// click is an additive animated peek the next scroll re-asserts away.
// No JS -> Hugo's full tree stays visible (true progressive enhancement).
window.addEventListener('DOMContentLoaded', () => {
  const tocRoot = document.getElementById('TableOfContents');
  if (!tocRoot) return;
  const tocLinks = tocRoot.querySelectorAll('a[href^="#"]');
  if (tocLinks.length === 0) return;

  const sections = Array.from(tocLinks)
    .map((link) => ({ link, target: document.querySelector(link.getAttribute('href')) }))
    .filter((s) => s.target);
  if (sections.length === 0) return;

  // --- Collapse: one-time DOM transform ---------------------------------
  let uid = 0;
  const metas = []; // { li, btn, disclosure }

  function setExpanded(meta, open, instant) {
    if (instant) meta.disclosure.classList.add('is-instant');
    meta.btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    meta.li.classList.toggle('is-expanded', open);
    meta.disclosure.inert = !open;
    if (instant) {
      // Force layout so the no-transition state is committed, then drop
      // .is-instant so a later manual toggle on this section animates.
      void meta.disclosure.offsetHeight;
      meta.disclosure.classList.remove('is-instant');
    }
  }

  Array.from(tocRoot.querySelectorAll(':scope > ul > li')).forEach((li) => {
    const subList = li.querySelector(':scope > ul');
    if (!subList) return;
    uid += 1;
    const id = `toc-sub-${uid}`;
    const disclosure = document.createElement('div');
    disclosure.className = 'toc-disclosure';
    disclosure.id = id;
    li.insertBefore(disclosure, subList);
    disclosure.appendChild(subList);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'toc-toggle';
    btn.setAttribute('aria-controls', id);
    const label = (li.querySelector(':scope > a')?.textContent || 'section').trim();
    btn.setAttribute('aria-label', `Toggle ${label} subsections`);
    li.insertBefore(btn, li.firstChild);
    li.classList.add('toc-section');

    const meta = { li, btn, disclosure };
    metas.push(meta);
    setExpanded(meta, false, true); // start collapsed, no flash/animation

    btn.addEventListener('click', () => {
      const willOpen = btn.getAttribute('aria-expanded') !== 'true';
      // Spec decision 3: a manual click is an additive peek — it must not
      // collapse the section scrollspy considers active (it would only
      // snap back open on the next scroll). Closing any OTHER section, or
      // opening any section, is allowed.
      const activeLink = tocRoot.querySelector('.is-active');
      const activeMeta = activeLink
        ? metas.find((m) => m.li.contains(activeLink))
        : null;
      if (!willOpen && meta === activeMeta) return;
      setExpanded(meta, willOpen, false); // manual => animated peek
    });
  });

  function applyActive(activeLink) {
    if (metas.length === 0) return;
    const activeMeta = activeLink
      ? metas.find((m) => m.li.contains(activeLink))
      : null;
    metas.forEach((m) => {
      const shouldOpen = m === activeMeta;
      const isOpen = m.btn.getAttribute('aria-expanded') === 'true';
      // Scrollspy wins: re-assert exactly the active section (instant),
      // collapsing any manually-peeked inactive section on this scroll.
      if (shouldOpen !== isOpen) setExpanded(m, shouldOpen, true);
    });
  }

  // --- Scrollspy (drives both highlight and collapse) -------------------
  function updateActive() {
    const scrollY = window.scrollY;
    const viewHeight = window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;
    const triggerY = scrollY + viewHeight * 0.1;
    const atBottom = scrollY + viewHeight >= docHeight - 2;

    let activeHref = sections[0].link.getAttribute('href');
    if (atBottom) {
      activeHref = sections[sections.length - 1].link.getAttribute('href');
    } else {
      for (const s of sections) {
        if (s.target.getBoundingClientRect().top + scrollY <= triggerY) {
          activeHref = s.link.getAttribute('href');
        }
      }
    }

    let activeLink = null;
    tocLinks.forEach((a) => {
      const on = a.getAttribute('href') === activeHref;
      a.classList.toggle('is-active', on);
      if (on) activeLink = a;
    });
    applyActive(activeLink);
  }

  window.addEventListener('scroll', updateActive, { passive: true });
  window.addEventListener('resize', updateActive, { passive: true });
  updateActive();
});

// Page sidebar — scrollspy + click handler.
// Activates on any page that calls partials/page-sidebar.html.
//
// The active section is the LAST one whose top has crossed the trigger
// line (10% from the top of the viewport). At the document bottom we
// force the last sidebar link active — otherwise a short final section
// (whose top can't reach the trigger before the document bottoms out)
// would never get highlighted while a longer earlier section still spans
// the trigger line.
window.addEventListener('DOMContentLoaded', () => {
  const sidebarLinks = document.querySelectorAll('.page-sidebar a[href^="#"]');
  if (sidebarLinks.length === 0) return;

  const sections = Array.from(sidebarLinks)
    .map((link) => ({ link, target: document.querySelector(link.getAttribute('href')) }))
    .filter((s) => s.target);
  if (sections.length === 0) return;

  function updateActive() {
    const scrollY = window.scrollY;
    const viewHeight = window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;
    const triggerY = scrollY + viewHeight * 0.1;
    const atBottom = scrollY + viewHeight >= docHeight - 2;

    let activeHref = sections[0].link.getAttribute('href');
    if (atBottom) {
      activeHref = sections[sections.length - 1].link.getAttribute('href');
    } else {
      for (const s of sections) {
        if (s.target.getBoundingClientRect().top + scrollY <= triggerY) {
          activeHref = s.link.getAttribute('href');
        }
      }
    }

    // Toggle by href so BOTH the rail label and the strip dot for the
    // active section flip together — sidebarLinks holds both DOMs.
    sidebarLinks.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === activeHref));
  }

  window.addEventListener('scroll', updateActive, { passive: true });
  window.addEventListener('resize', updateActive, { passive: true });
  updateActive();

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  sidebarLinks.forEach((a) => {
    a.addEventListener('click', (e) => {
      const href = a.getAttribute('href');
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
      history.pushState(null, '', href);
    });
  });
});
