// Citation hover-card runtime. Singleton card cloned from #ref-<key>;
// hover/focus on desktop, two-tap on mobile (first = card, second = jump).
//
// Guards on .essay-body + at least one .citation; bails otherwise.

const MOBILE_BREAKPOINT = 720;
const HOVER_OPEN_DELAY_MS = 150;
const HOVER_CLOSE_DELAY_MS = 200;
const VIEWPORT_PAD = 8;

let card = null;
let cardBody = null;
let closeBtn = null;
let currentCitation = null;
let lastActivatedKey = null;
let openTimer = null;
let closeTimer = null;

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function isMobile() {
  return window.innerWidth <= MOBILE_BREAKPOINT;
}

function ensureCard() {
  if (card) return;
  card = document.createElement('aside');
  card.id = 'citation-card';
  card.className = 'citation-card';
  card.setAttribute('role', 'region');
  card.setAttribute('aria-label', 'Citation details');
  card.hidden = true;

  cardBody = document.createElement('div');
  cardBody.className = 'citation-card-body';

  closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'citation-card-close';
  closeBtn.setAttribute('aria-label', 'Close citation');
  closeBtn.textContent = '×';

  card.append(cardBody, closeBtn);
  document.body.appendChild(card);

  card.addEventListener('mouseenter', () => clearTimeout(closeTimer));
  card.addEventListener('mouseleave', () => scheduleClose());
  closeBtn.addEventListener('click', hideCard);
}

function getKey(citation) {
  return citation.getAttribute('data-cite-key');
}

function populate(citation) {
  const key = getKey(citation);
  if (!key) return false;
  const refLi = document.getElementById('ref-' + key);
  if (!refLi) return false;
  cardBody.innerHTML = refLi.innerHTML;
  citation.setAttribute('aria-describedby', 'citation-card');
  currentCitation = citation;
  return true;
}

function positionDesktop(citation) {
  card.style.opacity = '0';
  card.hidden = false;
  const rect = citation.getBoundingClientRect();
  const cardRect = card.getBoundingClientRect();
  const scrollY = window.scrollY;
  const scrollX = window.scrollX;

  // Default: above the citation
  let top = rect.top + scrollY - cardRect.height - VIEWPORT_PAD;
  if (top < scrollY + VIEWPORT_PAD) {
    // Flip below
    top = rect.bottom + scrollY + VIEWPORT_PAD;
  }

  // Horizontal: center on citation, clamp to viewport
  let left = rect.left + scrollX + rect.width / 2 - cardRect.width / 2;
  const minLeft = scrollX + VIEWPORT_PAD;
  const maxLeft = scrollX + window.innerWidth - cardRect.width - VIEWPORT_PAD;
  left = Math.max(minLeft, Math.min(left, maxLeft));

  card.style.top = top + 'px';
  card.style.left = left + 'px';

  // Force layout flush, then fade in (skip transition under reduced-motion)
  if (reducedMotion()) {
    card.style.opacity = '1';
  } else {
    requestAnimationFrame(() => { card.style.opacity = '1'; });
  }
}

function positionMobile() {
  // CSS handles positioning (position: fixed, left/right/bottom). Just clear inline.
  card.style.top = '';
  card.style.left = '';
  card.style.opacity = '1';
  card.hidden = false;
}

function showCard(citation) {
  ensureCard();
  if (!populate(citation)) return;
  if (isMobile()) {
    positionMobile();
  } else {
    positionDesktop(citation);
  }
}

function hideCard() {
  if (!card) return;
  card.hidden = true;
  card.style.opacity = '';
  if (currentCitation) {
    currentCitation.removeAttribute('aria-describedby');
    currentCitation = null;
  }
  lastActivatedKey = null;
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  openTimer = closeTimer = null;
}

function scheduleClose() {
  clearTimeout(closeTimer);
  closeTimer = setTimeout(hideCard, HOVER_CLOSE_DELAY_MS);
}

function scheduleOpen(citation) {
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  openTimer = setTimeout(() => showCard(citation), HOVER_OPEN_DELAY_MS);
}

function onPointerEnter(e) {
  if (isMobile()) return;
  const citation = e.target.closest('.citation');
  if (!citation) return;
  scheduleOpen(citation);
}

function onPointerLeave(e) {
  if (isMobile()) return;
  const citation = e.target.closest('.citation');
  if (!citation) return;
  clearTimeout(openTimer);
  scheduleClose();
}

function onFocusIn(e) {
  const a = e.target;
  const citation = a.closest && a.closest('.citation');
  if (!citation) return;
  clearTimeout(closeTimer);
  showCard(citation);
}

function onFocusOut(e) {
  const citation = e.target.closest && e.target.closest('.citation');
  if (!citation) return;
  // If focus moves into the card, keep open.
  if (card && card.contains(e.relatedTarget)) return;
  hideCard();
}

function onClick(e) {
  const citation = e.target.closest('.citation');
  if (!citation) return;
  const key = getKey(citation);
  if (!key) return;

  if (isMobile()) {
    if (lastActivatedKey === key) {
      // Second tap on same citation — let click pass through to jump.
      hideCard();
      return;
    }
    e.preventDefault();
    lastActivatedKey = key;
    showCard(citation);
    return;
  }
  // Desktop: click is the user opting for the jump. Hide card and pass through.
  hideCard();
}

function onDocumentClick(e) {
  if (!card || card.hidden) return;
  if (e.target.closest('.citation') || card.contains(e.target)) return;
  hideCard();
}

function onKeydown(e) {
  if (e.key !== 'Escape') return;
  if (!card || card.hidden) return;
  const toFocus = currentCitation && currentCitation.querySelector('a');
  hideCard();
  if (toFocus) toFocus.focus();
}

function onResize() {
  if (card && !card.hidden) hideCard();
}

export function setupCitationCards() {
  const body = document.querySelector('.essay-body');
  if (!body) return;
  const citations = body.querySelectorAll('.citation');
  if (citations.length === 0) return;

  body.addEventListener('mouseover', onPointerEnter);
  body.addEventListener('mouseout', onPointerLeave);
  body.addEventListener('focusin', onFocusIn);
  body.addEventListener('focusout', onFocusOut);
  body.addEventListener('click', onClick);
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeydown);
  window.addEventListener('resize', onResize, { passive: true });
}
