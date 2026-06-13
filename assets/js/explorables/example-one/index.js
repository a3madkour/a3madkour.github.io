// assets/js/explorables/example-one/index.js
//
// Minimal mount — example-one is a frontmatter-shape fixture; the widget
// itself just confirms the per-essay-JS authoring path round-trips
// through the linter.
import { registerWidget } from '../runtime.js';

registerWidget('example-widget', (el) => {
  const p = document.createElement('p');
  p.textContent = '[example widget mounted]';
  p.style.fontFamily = 'var(--font-mono)';
  p.style.color = 'var(--color-ink-soft)';
  el.appendChild(p);
});
