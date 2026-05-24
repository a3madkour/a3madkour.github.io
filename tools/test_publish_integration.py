"""End-to-end integration tests for the elisp publish pipeline.

Each test sets up a tmp `~/org/notes/`-shaped corpus, invokes the elisp
publisher via `emacs --batch` (bootstrapped via straight.el, mirroring
`run-tests.sh`), and asserts on the resulting `content/`, `static/notes-shared/`,
and captured stderr/stdout.

Lands in A.1.c (was a parent-spec §11 placeholder until now).  Initial
fixture set covers A.1.c's asset-handling scope; future slices append.

Implementation notes
--------------------
- `a3madkour-publish-id.el` has `(require 'org-roam)` at load time, so the
  emacs batch session must bootstrap straight.el (same as `run-tests.sh`) to
  put org-roam on the load-path.
- `asset-validate-and-copy` calls `rewrite-asset-link` with the fake ID
  `"from-validate"`.  With no org-roam DB in the tmp workspace the lookup
  returns nil → `source-slug` is nil → any page-kind asset looks
  cross-namespace.  Each test therefore wraps its call in a `cl-letf*` form
  that stubs `a3madkour-pub/note-slug` (returning the expected slug) and
  `a3madkour-pub--id-to-file` (returning the org file path), exactly as the
  paired ert unit tests do.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


# Matches the LISP_DIR / CUSTOM_DIR layout in run-tests.sh.
_HOME = Path.home()
DOTFILES_CUSTOM = _HOME / "dotfiles" / "emacs-configs" / "custom"
DOTFILES_LISP = DOTFILES_CUSTOM / "lisp"
STRAIGHT_BOOTSTRAP = DOTFILES_CUSTOM / "straight" / "repos" / "straight.el" / "bootstrap.el"

# Skip the whole module if the emacs publish library isn't present.
_MISSING_PREREQS = not DOTFILES_LISP.exists() or not STRAIGHT_BOOTSTRAP.exists()
_SKIP_REASON = (
    f"elisp publish library not found at {DOTFILES_LISP} "
    f"or straight bootstrap not found at {STRAIGHT_BOOTSTRAP}"
)


def _emacs_eval(forms: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run `emacs --batch` with straight.el bootstrapped and FORMS evaluated.

    Mirrors `run-tests.sh`: sets user-emacs-directory to the custom dir,
    bootstraps straight, makes org-roam available, adds the lisp dir to
    load-path, then loads the publish library files before evaluating FORMS.
    """
    # Build the load-path expansion form (mirrors run-tests.sh line 32).
    expand_load_path = (
        "(dolist (dir (directory-files "
        '(expand-file-name "straight/build/" user-emacs-directory) '
        "t \"^[^.]\")) "
        "(when (file-directory-p dir) (add-to-list 'load-path dir)))"
    )

    args = [
        "emacs", "--batch",
        "--eval", f'(setq user-emacs-directory "{DOTFILES_CUSTOM}/")',
        "--eval", f'(setq straight-base-dir user-emacs-directory)',
        "-l", str(STRAIGHT_BOOTSTRAP),
        "--eval", "(straight-use-package 'org-roam)",
        "--eval", expand_load_path,
        "-L", str(DOTFILES_LISP),
        "-l", "a3madkour-publish.el",
        "-l", "a3madkour-publish-id.el",
        "-l", "a3madkour-publish-rewrite.el",
        "-l", "a3madkour-publish-assets.el",
    ]
    for form in forms:
        args.extend(["--eval", form])
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, timeout=120
    )


def _call_with_stubs(
    org_file: Path,
    bundle: Path,
    slug: str,
    canonical_asset_root: Path,
    shared_static_dir: Path,
) -> str:
    """Return an elisp form that stubs note-slug/id-to-file and calls
    `asset-validate-and-copy`, printing the result to stderr via `message`.

    The cl-letf* stubs mirror the pattern used in the paired ert unit tests
    (a3madkour-publish-assets-test.el) to avoid hitting the org-roam DB.
    """
    return (
        "(progn"
        f'  (setq a3madkour-pub-canonical-asset-root "{canonical_asset_root}")'
        f'  (setq a3madkour-pub-notes-shared-static-dir "{shared_static_dir}")'
        "  (cl-letf*"
        "    (((symbol-function 'a3madkour-pub--id-to-file)"
        f'      (lambda (_) "{org_file}"))'
        "     ((symbol-function 'a3madkour-pub/note-slug)"
        f'      (lambda (_) "{slug}")))'
        f'    (message "%S" (a3madkour-pub/asset-validate-and-copy "{org_file}" "{bundle}"))))'
    )


@unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
class TestAssetHandling(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="a3-pub-integ-"))
        self.notes_root = self.tmp / "notes"
        self.assets_root = self.notes_root / "assets"
        self.site_root = self.tmp / "site"
        self.bundle = self.site_root / "content" / "garden" / "foo"
        self.shared_static = self.site_root / "static" / "notes-shared"
        for p in (self.notes_root, self.assets_root, self.bundle, self.shared_static):
            p.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_canonical_page_asset_lands_in_bundle(self) -> None:
        """Page-scoped asset (assets/page/foo/diagram.png) → copied into bundle dir."""
        asset_dir = self.assets_root / "page" / "foo"
        asset_dir.mkdir(parents=True, exist_ok=True)
        asset = asset_dir / "diagram.png"
        asset.write_bytes(b"\x89PNG\r\n")

        org = self.notes_root / "foo.org"
        org.write_text("Note text.\n[[./assets/page/foo/diagram.png][Diagram]]\n",
                       encoding="utf-8")

        result = _emacs_eval(
            [_call_with_stubs(org, self.bundle, "foo",
                              self.assets_root, self.shared_static)],
            cwd=self.tmp,
        )
        self.assertTrue(
            (self.bundle / "diagram.png").exists(),
            f"diagram.png not in bundle.\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )

    def test_shared_asset_lands_in_notes_shared(self) -> None:
        """Shared asset (assets/shared/common.svg) → copied into static/notes-shared/."""
        shared_dir = self.assets_root / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        asset = shared_dir / "common.svg"
        asset.write_text("<svg/>", encoding="utf-8")

        org = self.notes_root / "foo.org"
        org.write_text("Note text.\n[[./assets/shared/common.svg][Shared]]\n",
                       encoding="utf-8")

        result = _emacs_eval(
            [_call_with_stubs(org, self.bundle, "foo",
                              self.assets_root, self.shared_static)],
            cwd=self.tmp,
        )
        self.assertTrue(
            (self.shared_static / "common.svg").exists(),
            f"common.svg not in notes-shared.\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )
        self.assertFalse(
            (self.bundle / "common.svg").exists(),
            "common.svg must NOT be in the bundle (shared assets go to notes-shared only)",
        )

    def test_stale_asset_removed(self) -> None:
        """Bundle file not referenced by the org note is removed; index.md is preserved."""
        org = self.notes_root / "foo.org"
        org.write_text("No asset refs.\n", encoding="utf-8")

        # Pre-existing stale asset + index.md in the bundle:
        (self.bundle / "index.md").write_text("doc", encoding="utf-8")
        (self.bundle / "stale.png").write_bytes(b"old")

        result = _emacs_eval(
            [_call_with_stubs(org, self.bundle, "foo",
                              self.assets_root, self.shared_static)],
            cwd=self.tmp,
        )
        self.assertFalse(
            (self.bundle / "stale.png").exists(),
            f"stale.png should have been removed.\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )
        self.assertTrue(
            (self.bundle / "index.md").exists(),
            "index.md must be preserved by cleanup",
        )

    def test_missing_asset_emits_warning(self) -> None:
        """A link to a non-existent asset emits a warning in the return value."""
        org = self.notes_root / "foo.org"
        org.write_text(
            "[[./assets/page/foo/never-existed.png][broken]]\n", encoding="utf-8"
        )

        result = _emacs_eval(
            [_call_with_stubs(org, self.bundle, "foo",
                              self.assets_root, self.shared_static)],
            cwd=self.tmp,
        )
        combined = result.stderr + result.stdout
        self.assertIn(
            "does not exist",
            combined,
            f"Expected 'does not exist' warning.\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
