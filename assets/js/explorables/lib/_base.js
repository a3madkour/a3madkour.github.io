// assets/js/explorables/lib/_base.js
//
// Internal helpers shared by library widgets. Not part of the public API.

export function clamp(v, lo, hi) {
  return v < lo ? lo : v > hi ? hi : v;
}

export function scale(v, [inLo, inHi], [outLo, outHi]) {
  if (inHi === inLo) return outLo;
  const t = (v - inLo) / (inHi - inLo);
  return outLo + t * (outHi - outLo);
}

// Build a row of slider controls. Returns { controlsEl, getState }.
// inputs: [{ name, min, max, default, step? }, ...]
// onChange: () => void  (called on any slider input event)
export function buildControls(inputs, onChange) {
  const state = {};
  for (const i of inputs) state[i.name] = i.default;

  const controlsEl = document.createElement('div');
  controlsEl.className = 'explorable-controls';

  for (const i of inputs) {
    const label = document.createElement('label');

    const nameSpan = document.createElement('span');
    nameSpan.className = 'explorable-label';
    nameSpan.textContent = i.name;
    label.appendChild(nameSpan);

    const range = document.createElement('input');
    range.type = 'range';
    range.min = String(i.min);
    range.max = String(i.max);
    range.step = String(i.step ?? 1);
    range.value = String(i.default);
    label.appendChild(range);

    const output = document.createElement('output');
    output.setAttribute('aria-live', 'polite');
    output.textContent = String(i.default);
    label.appendChild(output);

    range.addEventListener('input', () => {
      const v = Number(range.value);
      state[i.name] = v;
      output.textContent = String(v);
      onChange();
    });

    controlsEl.appendChild(label);
  }

  return { controlsEl, getState: () => ({ ...state }) };
}
