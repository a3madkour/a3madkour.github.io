// Streams entry — loaded on /streams/ (section index) AND /streams/<slug>/
// (single pages); scripts.html (Task 31) sets the load predicate.
// streams.js self-guards on its DOM selectors, so each entry point's
// no-op surface is silent.
import { initStreams } from './streams.js';
initStreams();
