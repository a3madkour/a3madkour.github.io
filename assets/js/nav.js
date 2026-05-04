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
