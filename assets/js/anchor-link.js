// anchor-link.js — click-to-copy + banner for §-glyph deep-link affordance.
// Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §3.4.

const BANNER_ID = 'anchor-link-banner';
const BANNER_TIMEOUT_MS = 2200;
let bannerEl = null;
let hideTimer = null;

function ensureBanner() {
  if (bannerEl) return bannerEl;
  bannerEl = document.createElement('div');
  bannerEl.id = BANNER_ID;
  bannerEl.setAttribute('role', 'status');
  bannerEl.setAttribute('aria-live', 'polite');
  bannerEl.hidden = true;
  const span = document.createElement('span');
  span.className = 'banner-text';
  bannerEl.appendChild(span);
  document.body.appendChild(bannerEl);
  return bannerEl;
}

function showBanner(text) {
  const el = ensureBanner();
  el.querySelector('.banner-text').textContent = text;
  el.hidden = false;
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = setTimeout(() => { el.hidden = true; }, BANNER_TIMEOUT_MS);
}

function handleClick(e) {
  const anchor = e.target.closest('a.anchor-link');
  if (!anchor) return;
  e.preventDefault();
  const absoluteUrl = new URL(anchor.getAttribute('href'), location.href).toString();
  const title = anchor.dataset.anchorTitle || 'this section';
  navigator.clipboard.writeText(absoluteUrl).then(
    () => showBanner(`Link to "${title}" copied`),
    () => {
      location.hash = anchor.getAttribute('href');
      showBanner('Link in address bar — copy from there');
    }
  );
}

function handleEscape(e) {
  // Skip when a <dialog> is open — the dialog owns Escape (native cancel).
  if (e.key !== 'Escape') return;
  if (document.querySelector('dialog[open]')) return;
  if (!bannerEl || bannerEl.hidden) return;
  bannerEl.hidden = true;
  if (hideTimer) clearTimeout(hideTimer);
}

const main = document.querySelector('main');
if (main) main.addEventListener('click', handleClick);
document.addEventListener('keydown', handleEscape);
