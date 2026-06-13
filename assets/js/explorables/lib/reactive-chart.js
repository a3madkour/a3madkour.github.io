// assets/js/explorables/lib/reactive-chart.js
import { buildControls, scale } from './_base.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

export class ReactiveChart {
  constructor(el, opts) {
    const {
      inputs,
      fn,
      x: [xMin, xMax],
      y: [yMin, yMax],
      samples = 100,
      width = 480,
      height = 200,
      xLabel = 'x',
      yLabel = 'y',
    } = opts;

    el.classList.add('explorable', 'explorable-chart');

    const figure = document.createElement('figure');
    figure.className = 'explorable-figure';

    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      preserveAspectRatio: 'xMidYMid meet',
      role: 'img',
      'aria-label': `${yLabel} as a function of ${xLabel}`,
    });

    const PAD = 24;

    // Static axis chrome (drawn once)
    const axes = svgEl('g', { class: 'explorable-axes' });
    axes.appendChild(svgEl('line', {
      x1: PAD, y1: height - PAD, x2: width - PAD, y2: height - PAD,
    }));
    axes.appendChild(svgEl('line', {
      x1: PAD, y1: PAD, x2: PAD, y2: height - PAD,
    }));
    // 4 tick labels: x-min, x-mid, x-max; y-min, y-max
    const xMid = (xMin + xMax) / 2;
    const yMid = (yMin + yMax) / 2;
    const xTickPx = (vx) => scale(vx, [xMin, xMax], [PAD, width - PAD]);
    const yTickPx = (vy) => scale(vy, [yMin, yMax], [height - PAD, PAD]);

    for (const [vx, anchor] of [[xMin, 'start'], [xMid, 'middle'], [xMax, 'end']]) {
      const t = svgEl('text', {
        x: xTickPx(vx), y: height - PAD + 14,
        'text-anchor': anchor, class: 'explorable-tick',
      });
      t.textContent = String(vx);
      axes.appendChild(t);
    }
    for (const [vy, baseline] of [[yMin, 'auto'], [yMax, 'hanging']]) {
      const t = svgEl('text', {
        x: PAD - 6, y: yTickPx(vy),
        'text-anchor': 'end', 'dominant-baseline': baseline, class: 'explorable-tick',
      });
      t.textContent = String(vy);
      axes.appendChild(t);
    }
    svg.appendChild(axes);

    // Reactive path
    const path = svgEl('path', { class: 'explorable-line', fill: 'none' });
    svg.appendChild(path);

    figure.appendChild(svg);

    const caption = document.createElement('figcaption');
    caption.className = 'explorable-axes-caption';
    caption.textContent = `${xLabel}: ${xMin} to ${xMax}, ${yLabel}: ${yMin} to ${yMax}`;
    figure.appendChild(caption);

    const rerender = () => {
      const state = getState();
      let d = '';
      for (let i = 0; i < samples; i++) {
        const x = xMin + (i / (samples - 1)) * (xMax - xMin);
        const y = fn(x, state);
        const px = xTickPx(x);
        const py = yTickPx(y);
        d += (i === 0 ? 'M' : 'L') + px.toFixed(2) + ' ' + py.toFixed(2) + ' ';
      }
      path.setAttribute('d', d.trimEnd());
    };

    const { controlsEl, getState } = buildControls(inputs, rerender);
    el.appendChild(controlsEl);
    el.appendChild(figure);

    rerender();
  }
}
