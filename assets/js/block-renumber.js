/**
 * D.1 section-prefixed numbering — Tier 2.3.
 *
 * Gate: <main data-block-numbering="section-prefixed">. Set by the essay
 * frontmatter `block_numbering: "section-prefixed"` via baseof.html.
 *
 * Hugo cannot section-prefix server-side because shortcodes run before
 * Goldmark — at theorem-render time the H2 has not yet been processed.
 * This module post-processes the rendered DOM:
 *   1. Walk <h2> elements in <main>, assign section indices (1, 2, ...).
 *   2. Walk .block-* containers in document order; for each, find the
 *      nearest preceding H2 to get its section, increment the per-section
 *      counter for the block's family (theorem-family or per-kind),
 *      rewrite the .block-header leading "Kind N" to "Kind M.N".
 *   3. Walk .ref-block links and update their text to match the
 *      now-renumbered targets. Resolves any .ref-block-unresolved that
 *      pointed at on-page block ids.
 *
 * Roadmap row 2.3. Bails cleanly on pages without the data-attribute.
 */

// Kinds whose counter is shared across the theorem-family.
const FAMILY_KINDS = new Set([
  'theorem', 'lemma', 'corollary', 'proposition',
]);

// Independent-counter kinds. proof is unnumbered and excluded.
const SOLO_KINDS = new Set([
  'definition', 'remark', 'example', 'note',
  'claim', 'conjecture', 'axiom',
]);

const ALL_KINDS = new Set([...FAMILY_KINDS, ...SOLO_KINDS]);

function capitalize(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}

function extractKind(blockEl) {
  for (const c of blockEl.classList) {
    if (!c.startsWith('block-')) continue;
    const name = c.slice('block-'.length);
    if (ALL_KINDS.has(name)) return name;
  }
  return null;
}

/** Replace the leading "Kind N" in the header's text nodes with "Kind M.N". */
function rewriteHeaderLabel(header, kind, newLabel) {
  const re = new RegExp(`${capitalize(kind)} \\d+`);
  const walker = document.createTreeWalker(header, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (re.test(node.nodeValue)) {
      node.nodeValue = node.nodeValue.replace(re, newLabel);
      return true;
    }
  }
  return false;
}

export function setupBlockRenumber() {
  const main = document.querySelector('main');
  if (!main || main.dataset.blockNumbering !== 'section-prefixed') return;

  // Collect H2s and block containers in one ordered pass.
  const items = main.querySelectorAll(
    'h2[id], div[class*="block-theorem"], div[class*="block-lemma"], '
    + 'div[class*="block-corollary"], div[class*="block-proposition"], '
    + 'div[class*="block-definition"], div[class*="block-remark"], '
    + 'div[class*="block-example"], div[class*="block-note"], '
    + 'div[class*="block-claim"], div[class*="block-conjecture"], '
    + 'div[class*="block-axiom"]'
  );

  let section = 0;
  // counters[family] -> integer, reset at each H2.
  let counters = {};
  // id -> new label (used by the ref-block pass below).
  const labelMap = {};

  for (const el of items) {
    if (el.tagName === 'H2') {
      section += 1;
      counters = {};
      continue;
    }
    const kind = extractKind(el);
    if (!kind || section === 0) continue;
    const family = FAMILY_KINDS.has(kind) ? 'theorem-family' : kind;
    counters[family] = (counters[family] || 0) + 1;
    const n = counters[family];
    const newLabel = `${capitalize(kind)} ${section}.${n}`;
    const header = el.querySelector('.block-header');
    if (header) rewriteHeaderLabel(header, kind, newLabel);
    if (el.id) labelMap[el.id] = newLabel;
  }

  // Second pass: rewrite ref-block text + resolve any unresolved that now match.
  for (const ref of main.querySelectorAll('.ref-block')) {
    const href = ref.getAttribute('href') || '';
    if (!href.startsWith('#')) continue;
    const id = href.slice(1);
    const label = labelMap[id];
    if (label) {
      ref.textContent = label;
      ref.classList.remove('ref-block-unresolved');
      ref.removeAttribute('data-ref-id');
      ref.removeAttribute('title');
    }
  }
}
