// Core entry — runs on every page. Theme toggle (with FOUC-prevention head
// script doing the early apply) and the TOC active-link highlighter, which
// bails immediately on pages without a TOC. Section-specific bundles are
// emitted by scripts.html based on .Section.
import './toggle-theme.js';
import './nav.js';
