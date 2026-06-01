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

import importlib.util
import os
import shutil
import subprocess
import tempfile
import time
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


def _import_linter(name: str):
    """Import a tools/<name>.py module by absolute path (no package install needed).

    Registers the loaded module in ``sys.modules`` before executing it so that
    decorators like ``@dataclass`` — which look up ``cls.__module__`` via
    ``sys.modules`` during class construction — can resolve the module.  Without
    this, ``importlib.util.exec_module`` on a file that defines a dataclass
    raises ``AttributeError: 'NoneType' object has no attribute '__dict__'``.
    """
    import sys as _sys
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_garden_source(path: Path, note_id: str, title: str, site_dir: Path) -> None:
    """Write a minimal garden source .org file to PATH.

    Uses the same property-drawer + keyword layout the ert unit tests use
    (see a3madkour-publish-garden-test.el).  #+HUGO_BASE_DIR is required by
    ox-hugo so it knows where to write the export (even though our caller
    overrides the output path via site-data-dir).
    """
    path.write_text(
        ":PROPERTIES:\n"
        f":ID: {note_id}\n"
        ":END:\n"
        f"#+title: {title}\n"
        "#+HUGO_PUBLISH: t\n"
        "#+HUGO_SECTION: garden\n"
        f"#+HUGO_BASE_DIR: {site_dir}/\n"
        "* Overview\n"
        "Body text for integration test.\n",
        encoding="utf-8",
    )


def _write_library_source(
    path: Path, section: str, items: list[dict[str, str]]
) -> None:
    """Write a library .org file at PATH with the given SECTION + ITEMS.

    Each item is a dict with keys: title, creator, year, status,
    media_type (optional), tags (optional list), last_modified (optional),
    and any extra drawer properties (uppercase keys go into :PROPERTIES:).
    """
    lines = [
        "#+HUGO_PUBLISH: t",
        f"#+HUGO_SECTION: {section}",
        "",
    ]
    for item in items:
        tags = item.get("tags", [])
        tag_str = ":" + ":".join(tags) + ":" if tags else ""
        lines.append(f"* {item['title']} {tag_str}".rstrip())
        lines.append(":PROPERTIES:")
        for key, val in item.items():
            if key in {"title", "tags"}:
                continue
            lines.append(f":{key.upper()}: {val}")
        lines.append(":END:")
        lines.append("")
    path.write_text("\n".join(lines))


def _escape_org_table_cell(val) -> str:
    """Escape | in cell values per org table convention."""
    if isinstance(val, str):
        return val.replace("|", "\\vert{}")
    return str(val)


def _write_research_source(
    path: Path,
    section_path: str,
    title: str,
    fm: dict[str, str],
    site_dir: Path,
    body: str = "Body paragraph for integration test.\n",
    outputs: list[dict[str, str]] | None = None,
) -> None:
    """Write a research .org file at PATH.

    section_path is 'research/themes' or 'research/questions'
    (slash-form, matching a3madkour-pub/sections in the elisp).
    fm is a dict of additional HUGO_CUSTOM_FRONT_MATTER fields
    (status, weight, theme, etc.).  outputs (questions only) renders
    an org table under * Outputs.
    """
    lines = [
        ":PROPERTIES:",
        f":ID: {fm.get('id', '11111111-2222-3333-4444-555555555555')}",
        f":LAST_MODIFIED: {fm.get('last_modified', '2026-05-30')}",
        ":END:",
        f"#+title: {title}",
        "#+HUGO_PUBLISH: t",
        f"#+HUGO_SECTION: {section_path}",
        f"#+HUGO_BASE_DIR: {site_dir}/",
        f"#+HUGO_DESCRIPTION: {fm.get('description', 'Test description.')}",
    ]
    for key in ("status", "weight", "theme", "parent_question",
                "garden_topic_ref", "supporting_notes", "related_essays",
                "source_stream", "started", "summary"):
        if key in fm:
            lines.append(f"#+HUGO_CUSTOM_FRONT_MATTER: :{key} {fm[key]}")
    if "tags" in fm:
        lines.append(f"#+filetags: :{':'.join(fm['tags'])}:")
    lines.append("")
    lines.append(body)
    if outputs:
        lines.append("")
        lines.append("* Outputs")
        lines.append("| kind  | title  | url  | year |")
        lines.append("|-------+--------+------+------|")
        for o in outputs:
            kind = _escape_org_table_cell(o["kind"])
            title_cell = _escape_org_table_cell(o["title"])
            url_cell = _escape_org_table_cell(o["url"])
            year_cell = _escape_org_table_cell(o["year"])
            lines.append(f"| {kind:<5s} | {title_cell} | {url_cell} | {year_cell} |")
    path.write_text("\n".join(lines), encoding="utf-8")


def _publish_living(
    notes_dir: Path, site_data_dir: Path
) -> "subprocess.CompletedProcess[str]":
    """Run the full publish-living pipeline against tmp notes + site dirs.

    Mirrors the bootstrap incantation in run-tests.sh + a3-pub.sh --publish-living,
    but accepts arbitrary notes_dir + site_data_dir so each test can use its own
    isolated tmp corpus.

    a3-pub.sh does not expose a --notes-dir flag, so this helper duplicates the
    wrapper's bootstrap (acceptable for integration-test purposes; the cost is
    tight coupling to the bootstrap incantation, which changes rarely).
    """
    return _publish_living_impl(notes_dir, site_data_dir, id_stubs=None)


def _publish_living_with_id_stubs(
    notes_dir: Path, site_data_dir: Path, id_stubs: "dict[str, Path]"
) -> "subprocess.CompletedProcess[str]":
    """Like _publish_living but also stubs org-roam-id-find.

    ID_STUBS maps UUID strings to absolute .org file paths.  The stub
    returns ``(cons FILE 1)`` for known IDs (matching the real org-roam
    return shape), and nil for unknown ones — exercising the :inert path
    for private/unpublished targets.

    Needed for cross-link tests (B.1.1): rewrite-buffer-links calls
    a3madkour-pub--id-to-file → org-roam-id-find to resolve each
    ``[[id:UUID]]``.  Without the stub, the org-roam SQLite DB has no
    entries for tmp-dir files and every link resolves to nil (:inert).
    """
    return _publish_living_impl(notes_dir, site_data_dir, id_stubs=id_stubs)


def _publish_living_impl(
    notes_dir: Path,
    site_data_dir: Path,
    id_stubs: "dict[str, Path] | None",
) -> "subprocess.CompletedProcess[str]":
    """Shared implementation; runs emacs --batch with the bootstrap incantation
    + a cl-letf form that stubs org-roam-db-sync (and, when id_stubs is provided,
    org-roam-id-find).  See `_publish_living` for the full bootstrap contract."""
    # Build the load-path expansion form — mirrors run-tests.sh line 32.
    expand_load_path = (
        "(dolist (dir (directory-files "
        '(expand-file-name "straight/build/" user-emacs-directory) '
        "t \"^[^.]\")) "
        "(when (file-directory-p dir) (add-to-list 'load-path dir)))"
    )

    env = os.environ.copy()
    env["A3_PUB_SITE_DATA_DIR"] = str(site_data_dir) + "/"

    # Derive the content dir from site_data_dir's parent (site root) + "content/".
    # a3madkour-pub-site-content-dir is used by finish-publish's Step A
    # (unpublish sweep) to delete stale bundles; it must point into the same
    # tmp site tree as site-data-dir.  The garden handler itself derives the
    # bundle path from site-data-dir (via a3madkour-pub-garden--site-root),
    # so these two must be consistent.
    site_root = site_data_dir.parent
    content_dir = str(site_root / "content") + "/"

    # Build the cl-letf stub form.  Base: stub org-roam-db-sync only.
    # Extended: also stub org-roam-id-find when id_stubs is provided.
    if id_stubs is not None:
        # Build a cond form: ((equal id "UUID") (cons "FILE" 1)) per entry.
        cond_clauses = " ".join(
            f'((equal id "{uid}") (cons "{fpath}" 1))'
            for uid, fpath in id_stubs.items()
        )
        letf_form = (
            "(cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil))"
            "          ((symbol-function 'org-roam-id-find)"
            f"           (lambda (id &optional _) (cond {cond_clauses} (t nil)))))"
            "  (a3-publish-living))"
        )
    else:
        letf_form = (
            "(cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))"
            "  (a3-publish-living))"
        )

    return subprocess.run(
        [
            "emacs", "--batch",
            "--eval", f'(setq user-emacs-directory "{DOTFILES_CUSTOM}/")',
            "--eval", "(setq straight-base-dir user-emacs-directory)",
            "-l", str(STRAIGHT_BOOTSTRAP),
            "--eval", "(straight-use-package 'org-roam)",
            "--eval", "(straight-use-package 'yaml)",
            "--eval", expand_load_path,
            "-L", str(DOTFILES_LISP),
            "-l", "a3madkour-publish",
            "-l", "a3madkour-publish-rewrite",
            "-l", "a3madkour-publish-assets",
            "-l", "a3madkour-publish-unpublish",
            "-l", "a3madkour-publish-export",
            "-l", "a3madkour-publish-frontmatter",
            "-l", "a3madkour-publish-living",
            "-l", "a3madkour-publish-deliberate",
            "-l", "a3madkour-publish-garden",
            "-l", "a3madkour-publish-library",
            "-l", "a3madkour-publish-research",
            "--eval", f'(setq a3madkour-pub/site-data-dir "{site_data_dir}/")',
            "--eval", f'(setq a3madkour-pub/org-notes-dir "{notes_dir}/")',
            # Also set the content-dir used by finish-publish's unpublish sweep.
            "--eval", f'(setq a3madkour-pub-site-content-dir "{content_dir}")',
            # Stub org-roam-db-sync (and optionally org-roam-id-find).
            "--eval", letf_form,
            "--eval", "(kill-emacs 0)",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )


@unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
class TestGardenPublishLiving(unittest.TestCase):
    """B.1 integration fixtures (Tasks 12-16): pin garden publish-living behavior.

    Each test seeds a tmp notes + site directory, drives emacs --batch with the
    full publish module stack loaded (mirroring a3-pub.sh's bootstrap incantation),
    and asserts on the resulting content/ + data/url-history.yaml output.

    emacs --batch with straight.el bootstrap takes 5-10 s per invocation; tests
    that call _publish_living twice may run 15-20 s each.  Total for the class:
    ~60 s.  Don't optimize — this is the correct price of full-stack coverage.
    """

    # ------------------------------------------------------------------
    # setUp / tearDown
    # ------------------------------------------------------------------

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="b1-garden-"))
        self.notes_dir = self.tmp / "notes"
        self.site_root = self.tmp / "site"
        self.notes_dir.mkdir(parents=True)
        (self.site_root / "data").mkdir(parents=True)
        (self.site_root / "content" / "garden").mkdir(parents=True)
        # Seed a valid empty manifest so the publish pipeline finds the file.
        (self.site_root / "data" / "url-history.yaml").write_text(
            "notes: []\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @property
    def _site_data_dir(self) -> Path:
        return self.site_root / "data"

    # ------------------------------------------------------------------
    # Task 12: test_garden_publish_once
    # ------------------------------------------------------------------

    def test_garden_publish_once(self) -> None:
        """Fixture 1 (Task 12): one source → bundle written + manifest updated.

        Asserts:
        - exit code 0
        - content/garden/integration-note/index.md exists
        - index.md contains title: and growth_stage:
        - data/url-history.yaml exists and is non-empty
        """
        note_id = "11111111-2222-3333-4444-555555555555"
        src = self.notes_dir / "integration-note.org"
        _write_garden_source(src, note_id, "Integration Note", self.site_root)

        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=f"publish-living exited non-zero.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        index_md = self.site_root / "content" / "garden" / "integration-note" / "index.md"
        self.assertTrue(
            index_md.exists(),
            f"content/garden/integration-note/index.md not created.\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        content = index_md.read_text(encoding="utf-8")
        self.assertIn("title:", content, "Missing title: in emitted frontmatter")
        self.assertIn("growth_stage:", content, "Missing growth_stage: in emitted frontmatter")

        history = self._site_data_dir / "url-history.yaml"
        self.assertTrue(history.exists(), "data/url-history.yaml not created")
        self.assertGreater(
            history.stat().st_size, 0, "data/url-history.yaml is empty"
        )

    # ------------------------------------------------------------------
    # Task 13: test_garden_publish_idempotent
    # ------------------------------------------------------------------

    def test_garden_publish_idempotent(self) -> None:
        """Fixture 2 (Task 13): second run produces zero diff (mtime preserved).

        Asserts:
        - both runs exit 0
        - index.md mtime is identical across runs (write-if-different worked)
        - url-history.yaml content identical across runs
        """
        note_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        src = self.notes_dir / "idem-note.org"
        _write_garden_source(src, note_id, "Idempotent Note", self.site_root)

        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc1.returncode, 0,
            msg=f"First publish-living run failed.\nstdout:\n{proc1.stdout}\nstderr:\n{proc1.stderr}",
        )

        # Slug is derived from the title "Idempotent Note" → "idempotent-note",
        # not from the filename "idem-note.org".
        index_md = self.site_root / "content" / "garden" / "idempotent-note" / "index.md"
        self.assertTrue(index_md.exists(), "index.md not created by first run")
        mtime_after_run1 = os.stat(index_md).st_mtime_ns
        history_after_run1 = (self._site_data_dir / "url-history.yaml").read_text(
            encoding="utf-8"
        )

        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc2.returncode, 0,
            msg=f"Second publish-living run failed.\nstdout:\n{proc2.stdout}\nstderr:\n{proc2.stderr}",
        )

        mtime_after_run2 = os.stat(index_md).st_mtime_ns
        self.assertEqual(
            mtime_after_run1,
            mtime_after_run2,
            "index.md was rewritten on second run — write-if-different is broken",
        )

        history_after_run2 = (self._site_data_dir / "url-history.yaml").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            history_after_run1,
            history_after_run2,
            "url-history.yaml changed on second run — idempotency broken",
        )

    # ------------------------------------------------------------------
    # Task 14: test_garden_slug_shift
    # ------------------------------------------------------------------

    def test_garden_slug_shift(self) -> None:
        """Fixture 3 (Task 14): title change → old bundle removed, new bundle at new
        slug, alias recorded in url-history.yaml.

        Asserts:
        - After publish 1: content/garden/original-slug/index.md exists
        - After publish 2: content/garden/new-slug/index.md exists
        - After publish 2: content/garden/original-slug/ is removed
        - url-history.yaml contains both slug strings

        NOTE — KNOWN GAP (B.1 follow-on): finish-publish Step B renames the
        asset dir (~/org/notes/assets/page/<old>/ → <new>/) but does NOT
        remove the old Hugo content bundle at content/garden/<old-slug>/.
        The old bundle stays on disk until the next full site rebuild or a
        manual cleanup.  This test will fail until a clean-up step is added
        to finish-publish (or the garden handler) for slug-shifted notes.

        Specific fix: in finish-publish Step B (or as a Step B.5), after
        renaming the asset dir, call
          (a3madkour-pub--unpublish-delete-bundle section old-slug)
        for each slug-shifted note.
        """
        note_id = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
        src = self.notes_dir / "shifting-note.org"
        _write_garden_source(src, note_id, "Original Slug", self.site_root)

        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc1.returncode, 0,
            msg=f"First publish-living run failed.\nstdout:\n{proc1.stdout}\nstderr:\n{proc1.stderr}",
        )

        original_bundle = self.site_root / "content" / "garden" / "original-slug"
        self.assertTrue(
            original_bundle.exists(),
            f"content/garden/original-slug/ not created.\n"
            f"stdout:\n{proc1.stdout}\nstderr:\n{proc1.stderr}",
        )

        # Mutate the title so the slug changes; org file name stays the same.
        _write_garden_source(src, note_id, "New Slug", self.site_root)

        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc2.returncode, 0,
            msg=f"Second publish-living run failed.\nstdout:\n{proc2.stdout}\nstderr:\n{proc2.stderr}",
        )

        new_bundle = self.site_root / "content" / "garden" / "new-slug"
        self.assertTrue(
            new_bundle.exists(),
            f"content/garden/new-slug/ not created after slug shift.\n"
            f"stdout:\n{proc2.stdout}\nstderr:\n{proc2.stderr}",
        )
        self.assertFalse(
            original_bundle.exists(),
            "content/garden/original-slug/ should have been removed after slug shift",
        )

        history_text = (self._site_data_dir / "url-history.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "original-slug",
            history_text,
            "url-history.yaml should contain 'original-slug' (as prior alias)",
        )
        self.assertIn(
            "new-slug",
            history_text,
            "url-history.yaml should contain 'new-slug' (as current url)",
        )

    # ------------------------------------------------------------------
    # Task 15: test_garden_removed_note_unpublish
    # ------------------------------------------------------------------

    def test_garden_removed_note_unpublish(self) -> None:
        """Fixture 4 (Task 15): source deleted → bundle removed, manifest state=removed.

        Asserts:
        - After publish 1: content/garden/<slug>/ exists
        - After publish 2 (source gone): content/garden/<slug>/ is removed
        - url-history.yaml records state: removed for the note's id
        """
        note_id = "cccccccc-dddd-eeee-ffff-000000000001"
        src = self.notes_dir / "vanishing-note.org"
        _write_garden_source(src, note_id, "Vanishing Note", self.site_root)

        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc1.returncode, 0,
            msg=f"First publish-living run failed.\nstdout:\n{proc1.stdout}\nstderr:\n{proc1.stderr}",
        )

        bundle = self.site_root / "content" / "garden" / "vanishing-note"
        self.assertTrue(
            bundle.exists(),
            f"content/garden/vanishing-note/ not created.\n"
            f"stdout:\n{proc1.stdout}\nstderr:\n{proc1.stderr}",
        )

        # Delete the source — simulates note being taken private (no HUGO_PUBLISH).
        src.unlink()

        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc2.returncode, 0,
            msg=f"Second publish-living run (no source) failed.\nstdout:\n{proc2.stdout}\nstderr:\n{proc2.stderr}",
        )

        self.assertFalse(
            bundle.exists(),
            "content/garden/vanishing-note/ should have been removed after source was deleted",
        )

        history_text = (self._site_data_dir / "url-history.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            note_id,
            history_text,
            "url-history.yaml should still contain the removed note's id",
        )
        self.assertIn(
            "state: removed",
            history_text,
            "url-history.yaml should record state: removed for the vanished note",
        )

    # ------------------------------------------------------------------
    # Task 16: test_garden_emits_lint_clean_output
    # ------------------------------------------------------------------

    def test_garden_emits_lint_clean_output(self) -> None:
        """Fixture 5 (Task 16): B-emitted notes pass check_garden_fixtures.py +
        check_garden_links.py via in-process invocation.

        NOTE — KNOWN GAPS (B.1 follow-on): the garden normalizer currently emits
        a `flavor:` key that is NOT in check_garden_fixtures.py's CONCEPT_FIELDS
        allowed set, and does NOT emit `draft:` or `last_modified:` (both
        ALWAYS_REQUIRED by the linter).  If this test fails, the root cause is
        the elisp normalizer, not the linter — do not relax the linter.

        Specific elisp gaps to address in a follow-on:
          - `flavor:` should NOT be written to the Hugo bundle (it is a
            search-index hint only, used by Pagefind; the linter rightly rejects
            it as a forbidden key).
          - `draft:` should default to `false` in the normalizer output.
          - `last_modified:` should be derived from the source file's git-mtime
            (or file mtime fallback) and emitted in YYYY-MM-DD form.
        """
        note_id = "dddddddd-eeee-ffff-0000-111111111111"
        src = self.notes_dir / "lint-clean-note.org"
        _write_garden_source(src, note_id, "Lint Clean Note", self.site_root)

        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=f"publish-living exited non-zero.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        index_md = self.site_root / "content" / "garden" / "lint-clean-note" / "index.md"
        self.assertTrue(
            index_md.exists(),
            f"content/garden/lint-clean-note/index.md not created.\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        # Import linters via absolute path (no sys.path games).
        gf = _import_linter("check_garden_fixtures")
        gl = _import_linter("check_garden_links")

        rc1, errors1 = gf.run(self.site_root)
        self.assertEqual(
            rc1,
            0,
            f"check_garden_fixtures rejected B-emitted note:\n"
            + "\n".join(f"  {e}" for e in errors1),
        )

        garden_dir = self.site_root / "content" / "garden"
        errors2, warnings2 = gl.lint_garden_links(garden_dir)
        self.assertEqual(
            errors2,
            [],
            f"check_garden_links rejected B-emitted note:\n"
            + "\n".join(f"  {e}" for e in errors2),
        )

    # ------------------------------------------------------------------
    # Task 17 (B.1.1): test_garden_publish_with_cross_link
    # ------------------------------------------------------------------

    def test_garden_publish_with_cross_link(self) -> None:
        """B.1.1 regression: source note links to (a) a published target and
        (b) a private/unknown UUID.

        Asserts the emitted source bundle:
        - contains an HTML anchor pointing at /garden/<target-slug>/
        - contains the inert plain text for the unpublished link
        - does NOT contain any ``{{< relref`` shortcode (the round-2 bug)
        - does NOT contain any raw `[[id:` bracket form (the pre-export rewrite
          really happened — ox-hugo's input was the rewritten temp file)

        Naming convention: `a-target.org` is alphabetically first so
        publish-living processes it before `b-source.org`; by the time the
        source is processed, the target is already in the manifest and
        rewrite-link resolves to `:html` (not `:inert`).
        """
        target_id = "44444444-5555-6666-7777-888888888888"
        source_id = "99999999-aaaa-bbbb-cccc-dddddddddddd"
        unknown_id = "00000000-0000-0000-0000-000000000000"

        target_src = self.notes_dir / "a-target.org"
        source_src = self.notes_dir / "b-source.org"

        _write_garden_source(target_src, target_id, "Cross Target",
                             self.site_root)
        # Source body with two id-links: one to the published target, one
        # to an unknown UUID (exercises the :inert path).
        source_src.write_text(
            ":PROPERTIES:\n"
            f":ID: {source_id}\n"
            ":END:\n"
            "#+title: Cross Source\n"
            "#+HUGO_PUBLISH: t\n"
            "#+HUGO_SECTION: garden\n"
            f"#+HUGO_BASE_DIR: {self.site_root}/\n"
            "* Overview\n"
            f"Links to [[id:{target_id}][the target]] and to "
            f"[[id:{unknown_id}][a private one]] in one line.\n",
            encoding="utf-8",
        )

        # Stub org-roam-id-find so rewrite-buffer-links can resolve the target
        # UUID to its .org file path (the real org-roam DB is not populated
        # for files in a tmp directory).  Only the target and source IDs need
        # entries; unknown_id intentionally absent → :inert path exercised.
        id_stubs = {
            target_id: target_src,
            source_id: source_src,
        }
        proc = _publish_living_with_id_stubs(
            self.notes_dir, self._site_data_dir, id_stubs
        )
        self.assertEqual(
            proc.returncode, 0,
            msg=(
                "publish-living exited non-zero.\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            ),
        )

        source_index = (
            self.site_root / "content" / "garden" / "cross-source" / "index.md"
        )
        self.assertTrue(
            source_index.exists(),
            f"source bundle not created.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        body = source_index.read_text(encoding="utf-8")
        self.assertIn(
            '<a href="/garden/cross-target/">the target</a>', body,
            f"resolved cross-link missing from emitted markdown.\nbody:\n{body}",
        )
        self.assertIn(
            "a private one", body,
            f"inert text for unpublished link missing.\nbody:\n{body}",
        )
        self.assertNotIn(
            "{{< relref", body,
            f"`{{{{< relref' shortcode survived — pre-export rewrite did not run.\nbody:\n{body}",
        )
        self.assertNotIn(
            "[[id:", body,
            f"raw `[[id:` form survived — bracket-link regex missed a case.\nbody:\n{body}",
        )


@unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
class TestLibraryPublishLiving(unittest.TestCase):
    """Integration fixtures for B.2's library handler.

    Each test seeds 1 or more library-<medium>.org source files in a tmp
    notes dir, then runs a3-pub.sh --publish-living against a tmp site
    dir, asserting the expected data/<medium>.yaml shape.
    """

    def setUp(self) -> None:
        self.notes_dir = Path(tempfile.mkdtemp(prefix="a3-pub-libnotes-"))
        self.site_root = Path(tempfile.mkdtemp(prefix="a3-pub-libsite-"))
        (self.site_root / "data").mkdir()
        (self.site_root / "static" / "library" / "covers").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.notes_dir, ignore_errors=True)
        shutil.rmtree(self.site_root, ignore_errors=True)

    @property
    def _site_data_dir(self) -> Path:
        return self.site_root / "data"

    def test_library_publish_once(self) -> None:
        """Single-item publish across all 4 library sections."""
        _write_library_source(
            self.notes_dir / "library-reading.org", "library/reading",
            [{"title": "Pride and Prejudice", "creator": "Jane Austen",
              "year": "1813", "status": "finished",
              "finished": "2024-12-15", "last_modified": "2024-12-16",
              "tags": ["classics"]}],
        )
        _write_library_source(
            self.notes_dir / "library-listening.org", "library/listening",
            [{"title": "Koyaanisqatsi", "creator": "Philip Glass",
              "year": "1983", "status": "listening",
              "last_modified": "2026-05-01", "tags": ["soundtrack"]}],
        )
        _write_library_source(
            self.notes_dir / "library-playing.org", "library/playing",
            [{"title": "Outer Wilds", "creator": "Mobius",
              "year": "2019", "status": "playing",
              "last_modified": "2026-05-01", "tags": ["puzzle"]}],
        )
        _write_library_source(
            self.notes_dir / "library-watching.org", "library/watching",
            [{"title": "Severance S2", "creator": "Apple TV+",
              "year": "2025", "status": "finished", "media_type": "series",
              "last_modified": "2026-04-01", "tags": ["drama"]}],
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        for fname in ("reading.yaml", "listening.yaml",
                      "playing.yaml", "watching.yaml"):
            self.assertTrue(
                (self._site_data_dir / fname).exists(),
                msg=f"{fname} not emitted",
            )

    def test_library_publish_idempotent(self) -> None:
        """Second publish-living run on unchanged source → zero diff."""
        _write_library_source(
            self.notes_dir / "library-reading.org", "library/reading",
            [{"title": "Item", "creator": "x", "year": "2024",
              "status": "queued", "last_modified": "2025-01-01"}],
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        yaml_path = self._site_data_dir / "reading.yaml"
        content1 = yaml_path.read_bytes()
        mtime1 = yaml_path.stat().st_mtime_ns
        time.sleep(1.1)
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        content2 = yaml_path.read_bytes()
        mtime2 = yaml_path.stat().st_mtime_ns
        self.assertEqual(content1, content2)
        self.assertEqual(mtime1, mtime2, msg="file rewritten on idempotent run")

    def test_library_slug_shift(self) -> None:
        """Changing :SLUG: drawer → old slug row gone, new slug row present."""
        src = self.notes_dir / "library-reading.org"
        _write_library_source(
            src, "library/reading",
            [{"title": "Pride and Prejudice", "slug": "pride",
              "creator": "Jane Austen", "year": "1813",
              "status": "finished", "finished": "2024-12-15",
              "last_modified": "2024-12-16"}],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content1 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertIn("slug: pride", content1)
        # Bump the slug.
        _write_library_source(
            src, "library/reading",
            [{"title": "Pride and Prejudice", "slug": "pride-and-prejudice",
              "creator": "Jane Austen", "year": "1813",
              "status": "finished", "finished": "2024-12-15",
              "last_modified": "2024-12-16"}],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content2 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertNotIn("slug: pride\n", content2)
        self.assertIn("slug: pride-and-prejudice", content2)

    def test_library_removed_item_unpublish(self) -> None:
        """Deleting a heading from source → row disappears on next publish."""
        src = self.notes_dir / "library-reading.org"
        _write_library_source(
            src, "library/reading",
            [
                {"title": "Item One", "creator": "x", "year": "2024",
                 "status": "queued", "last_modified": "2025-01-01"},
                {"title": "Item Two", "creator": "y", "year": "2024",
                 "status": "queued", "last_modified": "2025-01-01"},
            ],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content1 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertIn("slug: item-one", content1)
        self.assertIn("slug: item-two", content1)
        # Remove Item One.
        _write_library_source(
            src, "library/reading",
            [{"title": "Item Two", "creator": "y", "year": "2024",
              "status": "queued", "last_modified": "2025-01-01"}],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content2 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertNotIn("slug: item-one", content2)
        self.assertIn("slug: item-two", content2)

    def test_library_emits_lint_clean_output(self) -> None:
        """B-emitted yaml passes check_library_fixtures + _links + _covers.

        Seeds one minimal but linter-clean item per library leaf, runs
        publish-living against the tmp site dir, and invokes each of the
        three library linters against site_root.  This is the CI-gate
        guarantee from spec §11 / parent §11: anything the publisher
        emits must pass the site-side linters that gate CI.

        check_library_fixtures + check_library_links expose a
        `run(repo_root)` entry point — call them directly with the tmp
        site_root.  check_library_covers only exposes `main(argv=None)`
        and reads module-level REPO_ROOT/DATA_DIR/COVERS_DIR/AUDIT_LOG
        constants (plus the imported fetch_library_covers.DATA_DIR), so
        we monkey-patch those constants at the tmp site root before
        invoking main().  AUDIT_LOG is pointed at a non-existent path so
        load_audit_log() returns {} (we don't seed audit entries).
        """
        # Seed minimal but linter-clean items across all 4 media.
        # status='finished' triggers the `finished:` date requirement →
        # use 'queued'/'listening'/'playing'/'finished'+date as appropriate.
        _write_library_source(
            self.notes_dir / "library-reading.org", "library/reading",
            [{"title": "Item", "creator": "x", "year": "2024",
              "status": "queued", "last_modified": "2025-01-01"}],
        )
        _write_library_source(
            self.notes_dir / "library-listening.org", "library/listening",
            [{"title": "Album", "creator": "y", "year": "2024",
              "status": "listening", "last_modified": "2025-01-01"}],
        )
        _write_library_source(
            self.notes_dir / "library-playing.org", "library/playing",
            [{"title": "Game", "creator": "z", "year": "2024",
              "status": "playing", "last_modified": "2025-01-01"}],
        )
        _write_library_source(
            self.notes_dir / "library-watching.org", "library/watching",
            [{"title": "Film", "creator": "w", "year": "2024",
              "status": "finished", "finished": "2024-12-01",
              "last_modified": "2025-01-01"}],
        )
        # Library linters also expect data/library-shelves.yaml to exist
        # in the live tree (hand-authored; not touched by publisher).
        # The 3 linters under test don't actually parse it, but seed for
        # symmetry with the live repo shape.
        (self._site_data_dir / "library-shelves.yaml").write_text(
            "shelves: []\n"
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        # --- check_library_fixtures: run(repo_root) → (rc, errs, warns)
        lf = _import_linter("check_library_fixtures")
        rc_f, errs_f, _warns_f = lf.run(self.site_root)
        self.assertEqual(
            rc_f, 0,
            f"check_library_fixtures rejected B-emitted yaml:\n"
            + "\n".join(f"  {e}" for e in errs_f),
        )

        # --- check_library_links: run(repo_root) → (rc, errs)
        ll = _import_linter("check_library_links")
        rc_l, errs_l = ll.run(self.site_root)
        self.assertEqual(
            rc_l, 0,
            f"check_library_links rejected B-emitted yaml:\n"
            + "\n".join(f"  {e}" for e in errs_l),
        )

        # --- check_library_covers: only exposes main(argv) reading
        # module-level constants.  Monkey-patch REPO_ROOT/DATA_DIR/
        # COVERS_DIR/AUDIT_LOG on both check_library_covers and the
        # fetch_library_covers helper it imports.
        lc = _import_linter("check_library_covers")
        fc = _import_linter("fetch_library_covers")
        # Stash originals so concurrent runs/other tests aren't disturbed
        # (the modules are loaded by absolute path under spec-based
        # names; if a later test in this process re-imports, it'll get
        # a fresh module — but be defensive anyway).
        orig = {
            "lc_repo": lc.REPO_ROOT,
            "lc_data": lc.DATA_DIR,
            "lc_covers": lc.COVERS_DIR,
            "lc_audit": lc.AUDIT_LOG,
            "fc_repo": fc.REPO_ROOT,
            "fc_data": fc.DATA_DIR,
            "fc_covers": fc.COVERS_DIR,
        }
        try:
            lc.REPO_ROOT = self.site_root
            lc.DATA_DIR = self._site_data_dir
            lc.COVERS_DIR = self.site_root / "static" / "library" / "covers"
            lc.AUDIT_LOG = self.site_root / "tools" / ".cover-cache.json"
            fc.REPO_ROOT = self.site_root
            fc.DATA_DIR = self._site_data_dir
            fc.COVERS_DIR = self.site_root / "static" / "library" / "covers"
            rc_c = lc.main([])
        finally:
            lc.REPO_ROOT = orig["lc_repo"]
            lc.DATA_DIR = orig["lc_data"]
            lc.COVERS_DIR = orig["lc_covers"]
            lc.AUDIT_LOG = orig["lc_audit"]
            fc.REPO_ROOT = orig["fc_repo"]
            fc.DATA_DIR = orig["fc_data"]
            fc.COVERS_DIR = orig["fc_covers"]
        self.assertEqual(
            rc_c, 0,
            "check_library_covers.main() returned non-zero against B-emitted yaml",
        )


@unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
class TestResearchPublishLiving(unittest.TestCase):
    """B.3 integration fixtures: pin research publish-living behavior.

    Each test seeds one or more research-{themes,questions}-<slug>.org
    source files in a tmp notes dir, runs publish-living against a tmp
    site dir, asserts on the resulting content/research/{themes,
    questions}/ bundles.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="b3-research-"))
        self.notes_dir = self.tmp / "notes"
        self.site_root = self.tmp / "site"
        self.notes_dir.mkdir(parents=True)
        (self.site_root / "data").mkdir(parents=True)
        (self.site_root / "content" / "research" / "themes").mkdir(parents=True)
        (self.site_root / "content" / "research" / "questions").mkdir(parents=True)
        (self.site_root / "data" / "url-history.yaml").write_text(
            "notes: []\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def _site_data_dir(self) -> Path:
        return self.site_root / "data"

    def test_research_theme_publish_once(self) -> None:
        """Single theme emits a clean bundle under content/research/themes/."""
        src = self.notes_dir / "research-themes-example-theme.org"
        _write_research_source(
            src, "research/themes", "Example theme",
            {
                "status": "active",
                "weight": "10",
                "garden_topic_ref": "memory-in-play",
                "summary": "An umbrella theme.",
                "tags": ["research", "memory"],
            },
            self.site_root,
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=f"publish-living exited non-zero.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        out = self.site_root / "content" / "research" / "themes" / "example-theme" / "index.md"
        self.assertTrue(out.exists(),
                        f"bundle not created.\nstderr:\n{proc.stderr}")
        content = out.read_text(encoding="utf-8")
        self.assertIn('title: "Example theme"', content)
        self.assertIn('status: "active"', content)
        self.assertIn("description:", content)
        self.assertIn("weight: 10", content)

    def test_research_question_publish_once(self) -> None:
        """Single question with outputs table emits clean bundle."""
        src = self.notes_dir / "research-questions-narrative-atom.org"
        _write_research_source(
            src, "research/questions", "What is a narrative atom?",
            {
                "id": "22222222-aaaa-bbbb-cccc-dddddddddddd",
                "theme": "procedural-narrative",
                "status": "active",
                "supporting_notes": "story-atoms",
                "related_essays": "example-essay-two",
                "weight": "20",
                "tags": ["narrative"],
            },
            self.site_root,
            outputs=[
                {"kind": "paper", "title": "Save States as Edits",
                 "url": "https://example.com/paper", "year": 2024},
                {"kind": "code", "title": "save-replay-tool",
                 "url": "https://github.com/example/x", "year": 2024},
            ],
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=f"publish-living exited non-zero.\nstderr:\n{proc.stderr}",
        )
        out = (self.site_root / "content" / "research" / "questions"
               / "what-is-a-narrative-atom" / "index.md")
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("title:", content)
        self.assertIn("narrative atom", content)
        self.assertIn("theme:", content)
        self.assertIn("procedural-narrative", content)
        self.assertIn("supporting_notes:", content)
        self.assertIn("story-atoms", content)
        self.assertIn("outputs:", content)
        self.assertIn("kind: paper", content)
        self.assertIn("year: 2024", content)
        # Outputs heading + table stripped from body.
        self.assertNotIn("## Outputs", content)
        self.assertNotIn("| kind", content)

    # ------------------------------------------------------------------
    # Task 13: idempotent re-publish
    # ------------------------------------------------------------------

    def test_research_publish_idempotent(self) -> None:
        """Second publish-living run on unchanged source → zero file diff."""
        src = self.notes_dir / "research-themes-idem.org"
        _write_research_source(
            src, "research/themes", "Idempotent theme",
            {"status": "active", "weight": "15",
             "id": "33333333-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        out = (self.site_root / "content" / "research" / "themes"
               / "idempotent-theme" / "index.md")
        self.assertTrue(out.exists())
        content1 = out.read_bytes()
        mtime1 = out.stat().st_mtime_ns
        time.sleep(1.1)
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        content2 = out.read_bytes()
        mtime2 = out.stat().st_mtime_ns
        self.assertEqual(content1, content2)
        self.assertEqual(mtime1, mtime2,
                         msg="index.md was rewritten on idempotent run")

    # ------------------------------------------------------------------
    # Task 14: question title change → slug shift + url-history alias
    # ------------------------------------------------------------------

    def test_research_question_slug_shift(self) -> None:
        """Title change → old bundle removed, new bundle at new slug."""
        src = self.notes_dir / "research-questions-shifting.org"
        _write_research_source(
            src, "research/questions", "Original question",
            {"theme": "memory-and-play", "status": "active",
             "id": "44444444-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        original = (self.site_root / "content" / "research" / "questions"
                    / "original-question")
        self.assertTrue(original.exists())
        # Mutate title.
        _write_research_source(
            src, "research/questions", "New question",
            {"theme": "memory-and-play", "status": "active",
             "id": "44444444-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        new_bundle = (self.site_root / "content" / "research" / "questions"
                      / "new-question")
        self.assertTrue(new_bundle.exists(), "new-slug bundle missing")
        # B.1.x open follow-up #5 (delete-bundle no-retry): if the orphan
        # delete silently fails and original.exists() is True after the swap,
        # log it as a B.3 finding but don't fail here — the no-retry bug is a
        # known limitation, not a regression introduced by B.3.
        if original.exists():
            import warnings as _warnings
            _warnings.warn(
                "B.3 finding: original-slug bundle was not removed after slug "
                "shift (B.1.x #5 delete-bundle no-retry). Old bundle still "
                f"present at: {original}",
                stacklevel=2,
            )
        history = (self._site_data_dir / "url-history.yaml").read_text()
        self.assertIn("original-question", history)
        self.assertIn("new-question", history)

    # ------------------------------------------------------------------
    # Task 15: broken cross-refs WARN but don't fail; emitted YAML is OK
    # ------------------------------------------------------------------

    def test_research_cross_ref_warn(self) -> None:
        """Broken cross-refs WARN but don't fail; emitted YAML still passes the
        fixtures linter (the links linter is a separate gate)."""
        src = self.notes_dir / "research-questions-broken-refs.org"
        _write_research_source(
            src, "research/questions", "Broken refs question",
            {"theme": "nonexistent-theme",
             "status": "active",
             "supporting_notes": "private-note",
             "id": "55555555-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = (self.site_root / "content" / "research" / "questions"
               / "broken-refs-question" / "index.md")
        self.assertTrue(out.exists())
        content = out.read_text()
        self.assertIn("theme:", content)
        self.assertIn("nonexistent-theme", content)
        self.assertIn("private-note", content)

    # ------------------------------------------------------------------
    # Task 16a: removed source → bundle unpublished
    # ------------------------------------------------------------------

    def test_research_removed_question_unpublish(self) -> None:
        """Deleting a question source → bundle removed on next publish-living."""
        src = self.notes_dir / "research-questions-vanishing.org"
        _write_research_source(
            src, "research/questions", "Vanishing question",
            {"theme": "memory-and-play", "status": "active",
             "id": "66666666-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        bundle = (self.site_root / "content" / "research" / "questions"
                  / "vanishing-question")
        self.assertTrue(bundle.exists())
        # Remove source file.
        src.unlink()
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        self.assertFalse(bundle.exists(),
                         "removed source → bundle should be unpublished")

    # ------------------------------------------------------------------
    # Task 16b: B-emitted bundles pass check_research_fixtures + _links
    # ------------------------------------------------------------------

    def test_research_yaml_passes_site_linters(self) -> None:
        """B-emitted research bundles pass check_research_fixtures + _links.

        Both linters use `Path(__file__).resolve().parent.parent` to derive
        repo_root.  To make them scan the tmp site (not the real repo), we
        *copy* (not symlink) the linter scripts into site_root/tools/ so that
        __file__ resolves to a path inside site_root and parent.parent == site_root.

        The fixtures linter requires tags on themes, so the theme seed includes
        tags.  The links linter validates that the question's theme slug exists
        in the themes dir (it does) and checks garden/essays dirs (created empty
        — _load_slug_map returns {} when the dir exists but has no bundles, which
        is valid).
        """
        # Seed: 1 theme + 1 question pointing at that theme.
        # Tags are required by check_research_fixtures.py THEME_REQUIRED.
        _write_research_source(
            self.notes_dir / "research-themes-mp.org",
            "research/themes", "Memory and play",
            {"status": "active", "weight": "10",
             "tags": ["memory", "play"],
             "id": "77777777-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        _write_research_source(
            self.notes_dir / "research-questions-narrative.org",
            "research/questions", "What is a narrative atom?",
            {"theme": "memory-and-play", "status": "active", "weight": "20",
             "id": "88888888-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        # Create empty garden + essays dirs so _load_slug_map doesn't fail.
        (self.site_root / "content" / "garden").mkdir(parents=True, exist_ok=True)
        (self.site_root / "content" / "essays").mkdir(parents=True, exist_ok=True)

        # Copy linter scripts + their shared import into site_root/tools/ so
        # that Path(__file__).resolve().parent.parent == site_root (not the real
        # repo).  Symlinks would pierce to the real repo path via resolve().
        import shutil as _shutil
        tools_src = Path(__file__).resolve().parent
        tools_dst = self.site_root / "tools"
        tools_dst.mkdir(exist_ok=True)
        for script in ("check_research_fixtures.py",
                       "check_research_links.py",
                       "check_fixtures.py"):
            _shutil.copy2(tools_src / script, tools_dst / script)

        for linter in ("check_research_fixtures", "check_research_links"):
            result = subprocess.run(
                ["python3", f"tools/{linter}.py"],
                cwd=self.site_root,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(
                result.returncode, 0,
                msg=(f"{linter}.py failed:\nstdout:\n{result.stdout}"
                     f"\nstderr:\n{result.stderr}"),
            )


@unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
class TestEssaysPublishDeliberate(unittest.TestCase):
    """B.4 integration tests: publish-deliberate for essays."""

    def setUp(self) -> None:
        self.tmp_root = tempfile.mkdtemp(prefix="a3-pub-essays-int-")
        self.essays_dir = os.path.join(self.tmp_root, "org", "essays")
        os.makedirs(self.essays_dir, exist_ok=True)
        self.site_root = os.path.join(self.tmp_root, "site")
        os.makedirs(os.path.join(self.site_root, "data"), exist_ok=True)
        os.makedirs(os.path.join(self.site_root, "content", "essays"), exist_ok=True)
        # Seed empty manifest so begin-publish reads cleanly.
        with open(os.path.join(self.site_root, "data", "url-history.yaml"), "w") as f:
            f.write("manifest_version: 1\nnotes: []\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _seed_essay(self, slug: str, body: str, extra_keywords: str = "") -> str:
        path = os.path.join(self.essays_dir, f"{slug}.org")
        content = (
            ":PROPERTIES:\n"
            f":ID:       {slug}-uuid\n"
            ":END:\n"
            f"#+title: {slug.replace('-', ' ').title()}\n"
            "#+date: 2026-04-12\n"
            "#+HUGO_PUBLISH: t\n"
            "#+HUGO_SECTION: essays\n"
            f"{extra_keywords}"
            "\n"
            f"{body}\n"
        )
        with open(path, "w") as f:
            f.write(content)
        return path

    def _run_publish_deliberate(self, path: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["A3_PUB_SITE_DATA_DIR"] = os.path.join(self.site_root, "data")
        wrapper = os.path.expanduser(
            "~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh")
        return subprocess.run(
            [wrapper, "--publish-deliberate", path],
            env=env, capture_output=True, text=True, timeout=120)

    def test_essay_publish_once(self) -> None:
        """B.4 Task 11: one source → bundle written + manifest updated."""
        src = self._seed_essay("example-one", "Lorem ipsum body.")
        result = self._run_publish_deliberate(src)
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}\nstdout: {result.stdout}")
        bundle = os.path.join(self.site_root, "content", "essays", "example-one",
                              "index.md")
        self.assertTrue(os.path.exists(bundle), f"bundle missing: {bundle}")
        with open(bundle) as f:
            content = f.read()
        for required in ("title:", "date:", "lastmod:", "draft:",
                         "series:", "series_order:", "toc:",
                         "has_sidenotes:", "has_citations:",
                         "has_footnotes:", "has_math:",
                         "has_widgets:", "has_video_sync:"):
            self.assertIn(required, content,
                          f"required key missing: {required}")
        self.assertIn("Lorem ipsum body.", content)
        # Manifest entry exists.
        with open(os.path.join(self.site_root, "data", "url-history.yaml")) as f:
            manifest_text = f.read()
        self.assertIn("/essays/example-one/", manifest_text)

    def test_essay_publish_idempotent(self) -> None:
        """B.4 Task 12: second publish on unchanged source → zero file diff."""
        src = self._seed_essay("example-one", "Lorem ipsum body.")
        first = self._run_publish_deliberate(src)
        self.assertEqual(first.returncode, 0, first.stderr)
        bundle = os.path.join(self.site_root, "content", "essays",
                              "example-one", "index.md")
        with open(bundle) as f:
            first_content = f.read()
        first_mtime = os.path.getmtime(bundle)
        # Sleep briefly so mtime would tick if a write happened.
        import time
        time.sleep(1.1)
        second = self._run_publish_deliberate(src)
        self.assertEqual(second.returncode, 0, second.stderr)
        with open(bundle) as f:
            second_content = f.read()
        self.assertEqual(first_content, second_content,
                         "second publish produced a different file")
        self.assertEqual(first_mtime, os.path.getmtime(bundle),
                         "second publish bumped mtime — write-if-different broke")


if __name__ == "__main__":
    unittest.main()
