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

// Page sidebar — section observer + click handler.
// Activates on any page that calls partials/page-sidebar.html.
window.addEventListener('DOMContentLoaded', () => {
  const sidebarLinks = document.querySelectorAll('.page-sidebar a[href^="#"]');
  if (sidebarLinks.length === 0) return;

  // Active zone is the top 10% of viewport. A section "becomes active"
  // once its top edge crosses into that band — so clicking an anchor
  // (which scrolls the target's top to y=0) lands the clicked section
  // in the active zone, not the section after it.
  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      sidebarLinks.forEach((a) => {
        a.classList.toggle('is-active', a.getAttribute('href') === `#${id}`);
      });
    });
  }, { rootMargin: '0px 0px -90% 0px' });

  sidebarLinks.forEach((a) => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) sectionObserver.observe(target);
  });

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
