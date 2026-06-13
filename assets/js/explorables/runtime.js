// assets/js/explorables/runtime.js
//
// Explorables runtime. Per-essay modules import { registerWidget } from
// this file and call registerWidget(id, mountFn) at top level. On
// DOMContentLoaded, the runtime sweeps every [data-widget-id] in the
// document, looks up its mount fn, removes data-widget-fallback (so CSS
// hides the no-JS caption), and calls fn(el). Errors are isolated per
// widget — one broken mount doesn't break the page.

const registry = new Map();

export function registerWidget(id, mountFn) {
  if (registry.has(id)) {
    console.warn(`[explorables] duplicate registerWidget for id="${id}"`);
  }
  registry.set(id, mountFn);
}

document.addEventListener('DOMContentLoaded', () => {
  for (const el of document.querySelectorAll('[data-widget-id]')) {
    const id = el.getAttribute('data-widget-id');
    const fn = registry.get(id);
    if (!fn) {
      console.warn(`[explorables] no widget registered for id="${id}"`);
      continue;
    }
    el.removeAttribute('data-widget-fallback');
    try {
      fn(el);
    } catch (err) {
      console.error(`[explorables] mount failed for "${id}":`, err);
    }
  }
});
