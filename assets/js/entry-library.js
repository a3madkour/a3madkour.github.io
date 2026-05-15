// Library section entry — loaded on /library/ umbrella + /library/<leaf>/ pages.
import { setupFilterChips } from "./filter-chips.js";
import { initLibraryShelfNav } from "./library-shelf-nav.js";

const hook = document.querySelector("[data-library-page]");
const page = hook?.dataset?.libraryPage;
if (page) {
  setupFilterChips({
    containerSelector: `.library-chips[data-page="${page}"]`,
    cardSelector: ".library-row",
    sectionSelector: ".library-year",
    emptyStateSelector: ".library-empty",
  });
}

initLibraryShelfNav();
