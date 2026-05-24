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
        "-l", "a3madkour-publish-unpublish.el",
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

    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_unpublish_removed_note(self):
        """Publish two notes, unpublish one, re-run finish-publish; assert
        bundle deleted + manifest entry state=removed."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            (content / "garden" / "keep").mkdir(parents=True)
            (content / "garden" / "gone").mkdir(parents=True)
            (content / "garden" / "keep" / "index.md").write_text("# keep\n")
            (content / "garden" / "gone" / "index.md").write_text("# gone\n")
            data.mkdir()
            manifest_path = data / "url-history.yaml"
            # Seed manifest with both notes live.
            manifest_path.write_text(
                "notes:\n"
                "  - id: keep-id-1\n"
                "    current_url: /garden/keep/\n"
                "    history: []\n"
                "    state: live\n"
                "  - id: gone-id-1\n"
                "    current_url: /garden/gone/\n"
                "    history: []\n"
                "    state: live\n"
            )
            # Source corpus: only "keep" has HUGO_PUBLISH; "gone" doesn't.
            (notes / "keep.org").write_text(
                ":PROPERTIES:\n:ID: keep-id-1\n:END:\n"
                "#+TITLE: Keep\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
                "body\n"
            )
            (notes / "gone.org").write_text(
                ":PROPERTIES:\n:ID: gone-id-1\n:END:\n"
                "#+TITLE: Gone\n"  # No HUGO_PUBLISH — note unpublished.
                "body\n"
            )
            forms = [
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                # Stub org-roam-db-sync (no real db) + override manifest-path.
                f'(cl-letf (((symbol-function (quote org-roam-db-sync)) (lambda () nil))'
                f'          ((symbol-function (quote a3madkour-pub-history--manifest-path))'
                f'           (lambda () "{manifest_path}")))'
                f'  (a3madkour-pub/begin-publish)'
                f'  (princ (format "%S\\n" (a3madkour-pub/finish-publish))))',
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            # Bundle for "gone" deleted.
            self.assertFalse((content / "garden" / "gone").exists())
            # Bundle for "keep" remains.
            self.assertTrue((content / "garden" / "keep").exists())
            # Manifest mutated: gone-id-1 state == removed.
            updated = manifest_path.read_text()
            self.assertIn("gone-id-1", updated)
            self.assertIn("state: removed", updated)
            self.assertIn("reason: removed", updated)

    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_slug_shift_renames_assets(self):
        """Publish note with /garden/foo/ + asset → change HUGO_SLUG to foo-v2;
        finish-publish renames asset dir + rewrites .org source link."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            asset_root = workdir / "asset-root"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            data.mkdir()
            (asset_root / "page" / "foo").mkdir(parents=True)
            (asset_root / "page" / "foo" / "x.png").write_bytes(b"PNGDATA")
            (content / "garden" / "foo").mkdir(parents=True)
            (content / "garden" / "foo" / "index.md").write_text("# foo\n")
            manifest_path = data / "url-history.yaml"
            manifest_path.write_text(
                "notes:\n"
                "  - id: shift-id-1\n"
                "    current_url: /garden/foo/\n"
                "    history: []\n"
                "    state: live\n"
            )
            # Source has HUGO_SLUG: foo-v2 → new URL = /garden/foo-v2/.
            (notes / "note.org").write_text(
                ":PROPERTIES:\n:ID: shift-id-1\n:END:\n"
                "#+TITLE: Foo\n#+HUGO_PUBLISH: t\n"
                "#+HUGO_SECTION: garden\n#+HUGO_SLUG: foo-v2\n"
                "See [[./assets/page/foo/x.png][x]]\n"
            )
            forms = [
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-canonical-asset-root "{asset_root}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                # Stub org-roam-db-sync + override manifest-path + stub vc-backend
                # (so the asset-rename helper uses rename-file, not git mv).
                #
                # Standalone-mode flow: empty accumulator → finish-publish walks
                # org-notes-dir, parses note.org, derives new URL from
                # `#+HUGO_SLUG: foo-v2`, compares against manifest's /garden/foo/
                # → slug-shift detected → Step B renames asset + rewrites source.
                #
                # Then simulate B's per-note record-publish call (with
                # :had-slug-override-p t) to write the `slug_override` history
                # event to the manifest. In real B-coupled mode B would call
                # this BEFORE finish-publish, but doing so here would mutate
                # current_url ahead of the diff and defeat slug-shift detection
                # (the standalone walk reads source-derived URLs, not manifest).
                f'(cl-letf (((symbol-function (quote org-roam-db-sync)) (lambda () nil))'
                f'          ((symbol-function (quote a3madkour-pub-history--manifest-path))'
                f'           (lambda () "{manifest_path}"))'
                f'          ((symbol-function (quote vc-backend)) (lambda (_) nil)))'
                f'  (a3madkour-pub/begin-publish)'
                f'  (princ (format "%S\\n" (a3madkour-pub/finish-publish)))'
                f'  (a3madkour-pub-history/record-publish "shift-id-1" "/garden/foo-v2/" (quote live) :had-slug-override-p t))',
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            # Asset dir renamed: old gone, new exists.
            self.assertFalse((asset_root / "page" / "foo").exists())
            self.assertTrue((asset_root / "page" / "foo-v2" / "x.png").exists())
            # Source link rewritten in .org file.
            rewritten = (notes / "note.org").read_text()
            self.assertIn("./assets/page/foo-v2/x.png", rewritten)
            self.assertNotIn("./assets/page/foo/x.png", rewritten)
            # Manifest: slug_override event recorded.
            updated = manifest_path.read_text()
            self.assertIn("slug_override", updated)

    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_republish_after_removal(self):
        """Publish → unpublish → republish → history shows {removed, republished}
        events; current_url restored; aliases include the prior URL."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            data.mkdir()
            manifest_path = data / "url-history.yaml"
            # Seed manifest: already in `state: removed' with one history entry.
            manifest_path.write_text(
                "notes:\n"
                "  - id: rep-id-1\n"
                "    current_url: null\n"
                "    history:\n"
                "      - url: /garden/old-name/\n"
                "        replaced_at: '2026-05-22T10:00:00Z'\n"
                "        reason: removed\n"
                "    state: removed\n"
            )
            # Source: now published again at /garden/new-name/.
            (notes / "note.org").write_text(
                ":PROPERTIES:\n:ID: rep-id-1\n:END:\n"
                "#+TITLE: New name\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
                "body\n"
            )
            forms = [
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                f'(cl-letf (((symbol-function (quote org-roam-db-sync)) (lambda () nil))'
                f'          ((symbol-function (quote a3madkour-pub-history--manifest-path))'
                f'           (lambda () "{manifest_path}")))'
                f'  (a3madkour-pub/begin-publish)'
                # Simulate B's per-note record-publish call — flips state, appends republished event.
                f'  (a3madkour-pub-history/record-publish "rep-id-1" "/garden/new-name/" (quote live))'
                f'  (princ (format "%S\\n" (a3madkour-pub/finish-publish)))'
                # Print aliases for verification.
                f'  (princ (format "aliases: %S\\n" (a3madkour-pub-history/aliases-for "rep-id-1"))))',
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            updated = manifest_path.read_text()
            # State flipped back to live.
            self.assertIn("state: live", updated)
            # Current URL updated (yaml emits quoted strings).
            self.assertIn('current_url: "/garden/new-name/"', updated)
            # Both events present.
            self.assertIn("reason: removed", updated)      # original
            self.assertIn("reason: republished", updated)  # new
            # Prior URL surfaces via aliases-for.
            self.assertIn("/garden/old-name/", proc.stdout)

    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_link_into_removed_target_warns(self):
        """Publish two notes A → B; unpublish B; finish-publish emits a WARN
        in :orphan-warnings naming A's outgoing link into B."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            data.mkdir()
            (content / "garden" / "src").mkdir(parents=True)
            (content / "garden" / "tgt").mkdir(parents=True)
            (content / "garden" / "src" / "index.md").write_text("# src\n")
            (content / "garden" / "tgt" / "index.md").write_text("# tgt\n")
            manifest_path = data / "url-history.yaml"
            manifest_path.write_text(
                "notes:\n"
                "  - id: src-id-1\n"
                "    current_url: /garden/src/\n"
                "    history: []\n"
                "    state: live\n"
                "  - id: tgt-id-1\n"
                "    current_url: /garden/tgt/\n"
                "    history: []\n"
                "    state: live\n"
            )
            # Source A links to B via [[id:tgt-id-1]]; B is no longer HUGO_PUBLISH.
            (notes / "src.org").write_text(
                ":PROPERTIES:\n:ID: src-id-1\n:END:\n"
                "#+TITLE: Source\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
                "See [[id:tgt-id-1][gone target]]\n"
            )
            (notes / "tgt.org").write_text(
                ":PROPERTIES:\n:ID: tgt-id-1\n:END:\n"
                "#+TITLE: Target\n"  # No HUGO_PUBLISH → tgt-id-1 will be classified :removed.
                "body\n"
            )
            forms = [
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                # Stub org-roam-db-sync + manifest-path + org-roam-id-find (point at the .org files).
                f'(cl-letf (((symbol-function (quote org-roam-db-sync)) (lambda () nil))'
                f'          ((symbol-function (quote a3madkour-pub-history--manifest-path))'
                f'           (lambda () "{manifest_path}"))'
                f'          ((symbol-function (quote org-roam-id-find))'
                f'           (lambda (id &optional _)'
                f'             (cond ((equal id "src-id-1") (cons "{notes}/src.org" 1))'
                f'                   ((equal id "tgt-id-1") (cons "{notes}/tgt.org" 1))))))'
                f'  (a3madkour-pub/begin-publish)'
                f'  (princ (format "%S\\n" (a3madkour-pub/finish-publish))))',
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            # WARN in stdout: should mention both src-id-1 (outgoing) and tgt-id-1 (target).
            self.assertIn("src-id-1", proc.stdout)
            self.assertIn("tgt-id-1", proc.stdout)
            self.assertIn("republish recommended", proc.stdout)


if __name__ == "__main__":
    unittest.main()
