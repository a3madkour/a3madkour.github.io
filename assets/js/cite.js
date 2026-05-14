// Citation export runtime. Reads the inline #cite-data JSON blob,
// opens the modal on "Cite this page" / "Full citation" clicks, handles
// tab switching, copy-to-clipboard, and download links.
//
// Bails silently if #cite-data is absent (page isn't citable).

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

let citeData = null;
let modal = null;
let outputEl = null;
let subtitleEl = null;
let toastEl = null;
let downloadEl = null;
let sourceEl = null;
let noteEl = null;
let currentSource = null;

function parseDataBlob() {
  const el = document.getElementById('cite-data');
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    console.warn('cite: failed to parse #cite-data', e);
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
  modal.querySelectorAll('[role="tab"]').forEach((btn) => {
    btn.setAttribute('aria-selected', btn.dataset.format === format ? 'true' : 'false');
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

function openModal(source, subtitle) {
  if (!source) return;
  currentSource = source;
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

function onDocumentClick(e) {
  const pageLink = e.target.closest('.cite-cta');
  if (pageLink) {
    e.preventDefault();
    openModal(citeData.self, 'This page');
    return;
  }
  const fullBtn = e.target.closest('.ref-cite-full');
  if (fullBtn) {
    const key = fullBtn.dataset.citeKey;
    const ref = citeData.refs && citeData.refs[key];
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
        `Reference: ${ref.title}`,
      );
    }
    return;
  }
  const copyBtn = e.target.closest('.ref-cite-copy');
  if (copyBtn) {
    const key = copyBtn.dataset.citeKey;
    const fmt = copyBtn.dataset.format;
    const ref = citeData.refs && citeData.refs[key];
    if (ref && ref.formats && ref.formats[fmt]) {
      copyToClipboard(ref.formats[fmt]);
    }
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
  if (e.key === 'Escape' && modal && modal.hasAttribute('open')) {
    closeModal();
  }
}

export function initCite() {
  citeData = parseDataBlob();
  if (!citeData) return;
  modal = document.getElementById('cite-modal');
  if (!modal) return;
  outputEl = document.getElementById('cite-modal-output');
  subtitleEl = document.getElementById('cite-modal-subtitle');
  toastEl = modal.querySelector('.cite-modal-toast');
  downloadEl = modal.querySelector('.cite-modal-download');
  sourceEl = document.getElementById('cite-modal-source');
  noteEl = document.getElementById('cite-modal-note');
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeydown);
}
