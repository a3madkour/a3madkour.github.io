// Synced-poetry runtime. Spec: docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md §6.
// DOM-first: Hugo emits .poem-synced with data-t spans + data-duration; this
// module builds the player (so no-JS readers see nothing broken), drives the
// reveal from audio.timeupdate (audio mode) or requestAnimationFrame
// (animation mode), and supports seek + reset + show-all.

const FLOURISH_MS = 600;

function fmt(t) {
  t = Math.max(0, Math.floor(t));
  const m = Math.floor(t / 60);
  const s = t % 60;
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function setupOne(wrap) {
  const wordSel = wrap.querySelectorAll('.poem-word[data-t]');
  const spans = Array.from(
    wordSel.length ? wordSel : wrap.querySelectorAll('.poem-line[data-t]')
  ).map((el) => ({ el, t: parseFloat(el.getAttribute('data-t')) || 0 }))
   .sort((a, b) => a.t - b.t);

  const flourishTimers = new Map(); // span-record → pending setTimeout id

  let duration = parseFloat(wrap.getAttribute('data-duration')) || 0;
  const src = wrap.getAttribute('data-audio-src');

  // --- player DOM (built in JS so no-JS readers never see broken controls) ---
  const player = document.createElement('div');
  player.className = 'poem-player';
  player.innerHTML =
    '<button type="button" class="poem-player-btn poem-player-btn--primary" ' +
    'data-act="play" aria-label="Play">▶</button>' +
    '<button type="button" class="poem-player-btn" data-act="reset" ' +
    'aria-label="Reset">↻</button>' +
    '<div class="poem-player-progress" role="slider" aria-label="Seek" ' +
    'tabindex="0" aria-valuemin="0">' +
    '<div class="poem-player-progress-fill"></div>' +
    '<div class="poem-player-progress-thumb"></div></div>' +
    '<span class="poem-player-time">0:00 / 0:00</span>' +
    '<button type="button" class="poem-player-show-all" data-act="showall" ' +
    'aria-pressed="false" aria-label="Show all verses">' +
    '<span aria-hidden="true">👁</span> Show all</button>';
  wrap.parentNode.insertBefore(player, wrap);

  const playBtn = player.querySelector('[data-act="play"]');
  const resetBtn = player.querySelector('[data-act="reset"]');
  const showAllBtn = player.querySelector('[data-act="showall"]');
  const bar = player.querySelector('.poem-player-progress');
  const fill = player.querySelector('.poem-player-progress-fill');
  const thumb = player.querySelector('.poem-player-progress-thumb');
  const timeEl = player.querySelector('.poem-player-time');

  let mode = src ? 'audio' : 'anim';
  let audio = null;
  let playing = false;
  let elapsed = 0;       // anim-mode seconds
  let startedAt = 0;     // performance.now() at last play
  let rafId = 0;

  if (mode === 'audio') {
    audio = new Audio(src);
    audio.preload = 'none';
    audio.addEventListener('loadedmetadata', () => {
      if (isFinite(audio.duration) && audio.duration > 0) duration = audio.duration;
      render(currentTime());
    });
    audio.addEventListener('timeupdate', () => render(currentTime()));
    audio.addEventListener('ended', () => { playing = false; syncPlayBtn(); });
    audio.addEventListener('error', () => {
      console.warn('[poem-synced] audio failed to load; falling back to animation mode', src);
      mode = 'anim';
      audio = null;
      duration = parseFloat(wrap.getAttribute('data-duration')) || duration;
      stop();
      render(0);
    });
  }

  function currentTime() {
    if (mode === 'audio' && audio) return audio.currentTime || 0;
    if (playing) return elapsed + (performance.now() - startedAt) / 1000;
    return elapsed;
  }

  function syncPlayBtn() {
    playBtn.textContent = playing ? '⏸' : '▶';
    playBtn.setAttribute('aria-label', playing ? 'Pause' : 'Play');
  }

  function render(now) {
    for (const s of spans) {
      if (s.t <= now) {
        if (!s.el.classList.contains('is-visible') &&
            !s.el.classList.contains('is-current')) {
          s.el.classList.add('is-current');
          const tid = setTimeout(() => {
            flourishTimers.delete(s);
            s.el.classList.remove('is-current');
            s.el.classList.add('is-visible');
          }, FLOURISH_MS);
          flourishTimers.set(s, tid);
        }
      } else {
        const tid = flourishTimers.get(s);
        if (tid !== undefined) { clearTimeout(tid); flourishTimers.delete(s); }
        s.el.classList.remove('is-current', 'is-visible');
      }
    }
    const pct = duration > 0 ? Math.min(1, now / duration) * 100 : 0;
    fill.style.width = pct + '%';
    thumb.style.left = pct + '%';
    timeEl.textContent = `${fmt(now)} / ${fmt(duration)}`;
    bar.setAttribute('aria-valuemax', String(Math.floor(duration)));
    bar.setAttribute('aria-valuenow', String(Math.floor(now)));
    bar.setAttribute('aria-valuetext', `${fmt(now)} of ${fmt(duration)}`);
  }

  function tick() {
    if (!playing) return;
    const now = currentTime();
    render(now);
    if (now >= duration) { playing = false; syncPlayBtn(); return; }
    rafId = requestAnimationFrame(tick);
  }

  function play() {
    if (playing) return;
    playing = true;
    syncPlayBtn();
    if (mode === 'audio' && audio) {
      audio.play().catch(() => {});
    } else {
      startedAt = performance.now();
      rafId = requestAnimationFrame(tick);
    }
  }

  function pause() {
    if (!playing) return;
    if (mode === 'audio' && audio) {
      audio.pause();
    } else {
      elapsed = currentTime();
      cancelAnimationFrame(rafId);
    }
    playing = false;
    syncPlayBtn();
  }

  function stop() {
    cancelAnimationFrame(rafId);
    playing = false;
    syncPlayBtn();
  }

  function reset() {
    stop();
    if (mode === 'audio' && audio) { audio.pause(); audio.currentTime = 0; }
    elapsed = 0;
    render(0);
  }

  function seek(clientX) {
    const r = bar.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - r.left) / r.width));
    const target = ratio * duration;
    if (mode === 'audio' && audio) {
      audio.currentTime = target;
    } else {
      elapsed = target;
      if (playing) startedAt = performance.now();
    }
    render(target);
  }

  playBtn.addEventListener('click', () => (playing ? pause() : play()));
  resetBtn.addEventListener('click', reset);
  showAllBtn.addEventListener('click', () => {
    const on = wrap.classList.toggle('is-show-all');
    showAllBtn.classList.toggle('is-active', on);
    showAllBtn.setAttribute('aria-pressed', String(on));
  });

  let dragging = false;
  bar.addEventListener('pointerdown', (e) => {
    dragging = true;
    bar.setPointerCapture(e.pointerId);
    seek(e.clientX);
  });
  bar.addEventListener('pointermove', (e) => { if (dragging) seek(e.clientX); });
  bar.addEventListener('pointerup', () => { dragging = false; });
  bar.addEventListener('pointercancel', () => { dragging = false; });
  bar.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      const step = e.key === 'ArrowRight' ? 5 : -5;
      const t = Math.max(0, Math.min(duration, currentTime() + step));
      if (mode === 'audio' && audio) audio.currentTime = t;
      else { elapsed = t; if (playing) startedAt = performance.now(); }
      render(t);
    }
  });

  render(0);
}

export function initPoemSynced() {
  const wraps = document.querySelectorAll('.poem-synced');
  if (!wraps.length) return;
  wraps.forEach(setupOne);
}
