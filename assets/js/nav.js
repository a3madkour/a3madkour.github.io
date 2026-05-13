// TOC active-link highlighter — observes headings with `id` and adds
// `is-active` to the corresponding anchor inside the TOC container.
// Used by per-essay layouts when a TOC is present (Phase 2 onward).

window.addEventListener('DOMContentLoaded', () => {
  const tocLinks = document.querySelectorAll('#TableOfContents a');
  if (tocLinks.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const id = entry.target.getAttribute('id');
      if (!id) return;
      if (entry.intersectionRatio > 0) {
        tocLinks.forEach((a) => a.classList.remove('is-active'));
        document.querySelector(`#TableOfContents a[href="#${id}"]`)?.classList.add('is-active');
      }
    });
  });

  document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]')
    .forEach((heading) => observer.observe(heading));
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
