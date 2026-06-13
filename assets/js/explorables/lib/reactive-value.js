// assets/js/explorables/lib/reactive-value.js
import { buildControls } from './_base.js';

export class ReactiveValue {
  constructor(el, { inputs, render }) {
    el.classList.add('explorable', 'explorable-value');

    const out = document.createElement('p');
    out.className = 'explorable-output';
    out.setAttribute('aria-live', 'polite');

    const rerender = () => {
      out.textContent = render(getState());
    };

    const { controlsEl, getState } = buildControls(inputs, rerender);
    el.appendChild(controlsEl);
    el.appendChild(out);

    rerender();
  }
}
