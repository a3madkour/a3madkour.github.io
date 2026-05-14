// Garden-section entry — loaded only on /garden/ list, /garden/<slug>/, and
// /garden/graph/. Pulls the filter-chips runtime, the stacked-column app, and
// the force-directed graph (with the ~95 KB of vendored d3 modules that
// garden-graph.js dynamically imports). Each child module owns its own
// selector guards so they no-op on pages where their selectors don't match.
import './garden.js';
import './garden-stack.js';
import './garden-graph.js';
import './garden-recent-paths.js';
import './garden-pathlog-popover.js';
