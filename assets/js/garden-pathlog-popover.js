// Popover off the path-log "N in stack" count on garden note pages.
// Desktop only — mobile bypasses entirely.

import { readHistory, dedupe, renderPath } from './garden-history.js';

const MOBILE_QUERY = '(max-width: 720px)';

function init() {
  if (window.matchMedia(MOBILE_QUERY).matches) return;

  const trigger = document.querySelector('.path-log-count');
  if (!trigger) return;
  if (trigger.tagName !== 'SPAN') return; // belt + braces — already promoted?

  // Identify current page's root slug from the active path-log crumb.
  const activeCrumb = document.querySelector('.path-log-crumb.is-active[data-slug]');
  const rootSlug = activeCrumb ? activeCrumb.dataset.slug : null;

  const all = dedupe(readHistory());
  // Drop the current session (the newest one whose root matches rootSlug).
  const currentIdx = rootSlug ? all.findIndex(s => s.root === rootSlug) : -1;
  const others = all.filter((_, i) => i !== currentIdx).slice(0, 4);

  if (others.length === 0) return;

  // Promote span → button.
  const button = document.createElement('button');
  button.type = 'button';
  button.className = trigger.className;
  if (trigger.dataset.stackCount) button.dataset.stackCount = trigger.dataset.stackCount;
  button.textContent = `${trigger.textContent.trim()} ▾`;
  button.setAttribute('aria-expanded', 'false');
  button.setAttribute('aria-controls', 'path-log-popover');
  trigger.parentNode.replaceChild(button, trigger);

  // Build popover DOM.
  const popover = document.createElement('div');
  popover.id = 'path-log-popover';
  popover.setAttribute('role', 'dialog');
  popover.setAttribute('aria-labelledby', 'path-log-popover-heading');
  popover.hidden = true;
  popover.innerHTML = `
    <h3 id="path-log-popover-heading">Recent paths</h3>
    <ol class="popover-paths"></ol>
    <a class="popover-history-link" href="/garden/history/">full history</a>
  `;
  button.insertAdjacentElement('afterend', popover);

  const list = popover.querySelector('.popover-paths');
  others.forEach(s => {
    const li = document.createElement('li');
    li.appendChild(renderPath(s));
    list.appendChild(li);
  });

  const focusableSelector = 'a, button';

  function open() {
    popover.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    const first = popover.querySelector(focusableSelector);
    if (first) first.focus();
  }
  function close() {
    popover.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    button.focus();
  }
  function isOpen() { return !popover.hidden; }

  button.addEventListener('click', () => {
    if (isOpen()) close();
    else open();
  });

  document.addEventListener('mousedown', (e) => {
    if (!isOpen()) return;
    if (popover.contains(e.target) || button.contains(e.target)) return;
    close();
  }, true);

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!isOpen()) return;
    e.stopImmediatePropagation();
    close();
  });

  // Focus trap inside the popover.
  popover.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const focusables = Array.from(popover.querySelectorAll(focusableSelector));
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
