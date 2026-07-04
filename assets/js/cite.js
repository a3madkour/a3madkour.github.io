// Citation export runtime. Reads the inline .cite-data JSON blob,
// opens the modal on "Cite this X" / "Full citation" clicks, handles
// tab switching, copy-to-clipboard, and download links.
//
// Scoping (matters for garden stacked columns): the cite-data blob is
// emitted as `<script class="cite-data">` INSIDE each <article>. On a
// click we walk up to the containing article and find that article's
// own cite-data, so a button in a stacked column refers to that
// column's note — not the root.

const STORAGE_KEY = 'cite-format-pref';
const EXT_MAP = {
  bibtex: '.bib',
  apa: '.txt',
  chicago: '.txt',
  mla: '.txt',
  ris: '.ris',
};
const MIME_MAP = {
  bibtex: 'application/x-bibtex',
  apa: 'text/plain',
  chicago: 'text/plain',
  mla: 'text/plain',
  ris: 'application/x-research-info-systems',
};

let modal = null;
let titleEl = null;
let subtitleEl = null;
let outputEl = null;
let toastEl = null;
let downloadEl = null;
let sourceEl = null;
let noteEl = null;
let currentSource = null;

function parseScopedBlob(scope) {
  const root = scope || document;
  const el = root.querySelector('script.cite-data');
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    console.warn('cite: failed to parse .cite-data', e);
    return null;
  }
}

function loadFormatPref() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v && EXT_MAP[v]) return v;
  } catch (_) {}
  return 'bibtex';
}

function saveFormatPref(format) {
  try { localStorage.setItem(STORAGE_KEY, format); } catch (_) {}
}

function setActiveTab(format) {
  // A stored format pref (or a ref) may lack this format — fall back to the
  // first available one so we never render the literal string "undefined"
  // (nor a `data:` download of "undefined").
  if (!currentSource.formats || currentSource.formats[format] === undefined) {
    const available = currentSource.formats ? Object.keys(currentSource.formats) : [];
    if (available.length === 0) return;
    format = available.includes('bibtex') ? 'bibtex' : available[0];
  }
  modal.querySelectorAll('[role="tab"]').forEach((btn) => {
    const sel = btn.dataset.format === format;
    btn.setAttribute('aria-selected', sel ? 'true' : 'false');
    // Roving tabindex: only the selected tab is in the tab order (WAI-ARIA
    // tabs pattern); Arrow keys move between the others — see onKeydown.
    btn.tabIndex = sel ? 0 : -1;
  });
  const str = currentSource.formats[format];
  outputEl.textContent = str;
  const ext = EXT_MAP[format];
  const mime = MIME_MAP[format];
  const filename = `${currentSource.citekey}${ext}`;
  downloadEl.href = `data:${mime};charset=utf-8,${encodeURIComponent(str)}`;
  downloadEl.setAttribute('download', filename);
  downloadEl.textContent = `Download ${ext}`;
  saveFormatPref(format);
}

function setNavPill(el, href) {
  if (!href) {
    el.hidden = true;
    el.removeAttribute('href');
  } else {
    el.hidden = false;
    el.setAttribute('href', href);
  }
}

function openModal(source, title, subtitle) {
  if (!source) return;
  currentSource = source;
  titleEl.textContent = title || 'Cite';
  subtitleEl.textContent = subtitle || '';
  setNavPill(sourceEl, source.url);
  setNavPill(noteEl, source.notes_ref ? `/garden/${source.notes_ref}/` : '');
  const pref = loadFormatPref();
  setActiveTab(pref);
  if (typeof modal.showModal === 'function') {
    modal.showModal();
  } else {
    modal.setAttribute('open', '');
  }
}

function closeModal() {
  // <dialog>.showModal() makes the rest of the page inert; only .close()
  // unwinds that state. Removing the `open` attribute first short-circuits
  // .close() (it returns early thinking the dialog is already closed) and
  // leaves the inert state stuck — every page click then gets swallowed.
  if (typeof modal.close === 'function' && modal.open) {
    modal.close();
  } else if (modal.hasAttribute('open')) {
    modal.removeAttribute('open');
  }
}

function copyToClipboard(text) {
  const writeToast = (msg) => {
    toastEl.textContent = msg;
    setTimeout(() => { toastEl.textContent = ''; }, 2000);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(
      () => writeToast('Copied'),
      () => writeToast('Press Ctrl+C to copy'),
    );
  } else {
    writeToast('Press Ctrl+C to copy');
  }
}

function triggerDownload(filename, mime, text) {
  const url = `data:${mime};charset=utf-8,${encodeURIComponent(text)}`;
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function onDocumentClick(e) {
  const pageLink = e.target.closest('.cite-cta');
  if (pageLink) {
    e.preventDefault();
    const data = parseScopedBlob(pageLink.closest('article'));
    if (data) {
      openModal(data.self, pageLink.textContent.trim(), data.self.title);
    }
    return;
  }
  const fullBtn = e.target.closest('.ref-cite-full');
  if (fullBtn) {
    const data = parseScopedBlob(fullBtn.closest('article'));
    if (!data || !data.refs) return;
    const key = fullBtn.dataset.citeKey;
    const ref = data.refs[key];
    if (ref) {
      e.preventDefault();
      openModal(
        {
          citekey: key,
          title: ref.title,
          formats: ref.formats,
          url: ref.url,
          notes_ref: ref.notes_ref,
        },
        'Cite this reference',
        ref.title,
      );
    }
    return;
  }
  const copyBtn = e.target.closest('.ref-cite-copy');
  if (copyBtn) {
    const data = parseScopedBlob(copyBtn.closest('article'));
    if (!data || !data.refs) return;
    const key = copyBtn.dataset.citeKey;
    const fmt = copyBtn.dataset.format;
    const ref = data.refs[key];
    if (ref && ref.formats && ref.formats[fmt]) {
      copyToClipboard(ref.formats[fmt]);
    }
    return;
  }
  const bulkBtn = e.target.closest('.ref-cite-bulk-bib');
  if (bulkBtn) {
    e.preventDefault();
    const data = parseScopedBlob(bulkBtn.closest('article'));
    if (!data || !data.refs) return;
    const entries = Object.values(data.refs)
      .map((r) => r.formats && r.formats.bibtex)
      .filter(Boolean);
    if (!entries.length) return;
    const text = entries.join('\n\n');
    const filename = `${data.self.citekey}-references.bib`;
    triggerDownload(filename, MIME_MAP.bibtex, text);
    return;
  }
  const tab = e.target.closest('.cite-modal-tabs [role="tab"]');
  if (tab && modal.contains(tab)) {
    setActiveTab(tab.dataset.format);
    return;
  }
  if (e.target.closest('.cite-modal-close')) {
    closeModal();
    return;
  }
  if (e.target.closest('.cite-modal-copy')) {
    copyToClipboard(outputEl.textContent);
    return;
  }
  if (e.target === modal) {
    closeModal();
  }
}

function onKeydown(e) {
  if (!modal || !modal.hasAttribute('open')) return;
  if (e.key === 'Escape') {
    closeModal();
    return;
  }
  // WAI-ARIA tabs keyboard nav: Arrow/Home/End move + activate between tabs.
  const focused = e.target.closest && e.target.closest('.cite-modal-tabs [role="tab"]');
  if (!focused || !modal.contains(focused)) return;
  const tabs = Array.from(modal.querySelectorAll('.cite-modal-tabs [role="tab"]'));
  const i = tabs.indexOf(focused);
  let next = -1;
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (i + 1) % tabs.length;
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (i - 1 + tabs.length) % tabs.length;
  else if (e.key === 'Home') next = 0;
  else if (e.key === 'End') next = tabs.length - 1;
  if (next >= 0) {
    e.preventDefault();
    setActiveTab(tabs[next].dataset.format);
    tabs[next].focus();
  }
}

export function initCite() {
  modal = document.getElementById('cite-modal');
  if (!modal) return;
  // The cite-data blob is parsed lazily per click (so stacked garden
  // columns each refer to their own data), but we still need the modal
  // chrome wired up once.
  outputEl = document.getElementById('cite-modal-output');
  titleEl = document.getElementById('cite-modal-title');
  subtitleEl = document.getElementById('cite-modal-subtitle');
  toastEl = modal.querySelector('.cite-modal-toast');
  downloadEl = modal.querySelector('.cite-modal-download');
  sourceEl = document.getElementById('cite-modal-source');
  noteEl = document.getElementById('cite-modal-note');
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeydown);
}
