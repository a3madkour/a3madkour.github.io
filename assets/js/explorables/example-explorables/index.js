// assets/js/explorables/example-explorables/index.js
import { registerWidget } from '../runtime.js';
import { ReactiveValue } from '../lib/reactive-value.js';
import { ReactiveChart } from '../lib/reactive-chart.js';

registerWidget('k-square', (el) =>
  new ReactiveValue(el, {
    inputs: [{ name: 'k', min: 0, max: 10, default: 2, step: 0.1 }],
    render: ({ k }) => `f(k) = ${(k * k).toFixed(2)}`,
  })
);

registerWidget('gaussian', (el) =>
  new ReactiveChart(el, {
    inputs: [
      { name: 'sigma', min: 0.1, max: 3, default: 1, step: 0.1 },
      { name: 'mu', min: -3, max: 3, default: 0, step: 0.1 },
    ],
    fn: (x, { sigma, mu }) =>
      Math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * Math.sqrt(2 * Math.PI)),
    x: [-5, 5],
    y: [0, 0.8],
    xLabel: 'x',
    yLabel: 'p(x)',
  })
);

registerWidget('spinner', (el) => {
  const canvas = document.createElement('canvas');
  canvas.width = 200;
  canvas.height = 200;
  el.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = getComputedStyle(document.documentElement)
    .getPropertyValue('--color-burgundy')
    .trim() || '#7a0f2d';
  ctx.lineWidth = 3;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let t = 0;
  const tick = () => {
    ctx.clearRect(0, 0, 200, 200);
    ctx.beginPath();
    ctx.arc(100, 100, 60, t, t + Math.PI);
    ctx.stroke();
    t += 0.02;
    if (!reduced) requestAnimationFrame(tick);
  };
  tick();
});
