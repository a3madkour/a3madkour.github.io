// Poetry-section entry — loaded only on /works/poetry/<slug>/ single pages.
// poem-synced.js owns its own .poem-synced guard, so non-synced poems no-op.
import { initPoemSynced } from './poem-synced.js';
initPoemSynced();
