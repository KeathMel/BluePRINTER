# BluePRINTER

Annotate blueprints and 3D models. Drop an image or a model into a project,
right-click anywhere on it to drop a **marker**, and give that marker a title,
a description and a size. Text and code files open in a built-in editor that
saves as you type. Everything you add is copied into the app's own library, so
a project is a self-contained thing you can export, move and import again.

PyQt6, Python 3.9+. Linux (works anywhere Qt6 and OpenGL do).

---

## INSTALL

```
git clone https://github.com/KeathMel/BluePRINTER
cd BluePRINTER
./BluePRINTER
```

That's it. The launcher builds a venv on first run, installs the dependencies
into it, and starts the app. Every run after that just starts it.

To get a desktop entry as well:

```
bash install.sh
```

If something changed but doesn't show up, it's almost always stale bytecode:

```
find . -name __pycache__ -type d -exec rm -rf {} +
```

---

## HOW FILES WORK — read this first

**BluePRINTER imports and owns.** This is the single most important thing to
understand about it, and every question about "did that change my file?"
answers itself once you know it.

Adding a file **copies** it into `~/.blueprints/<project>/`. From that moment
there are two files: yours, wherever it was, and the app's copy. They have no
link to each other.

| What you do | What happens to your original |
|---|---|
| Add a file to a project | copied — original untouched |
| Edit a text file in the app | nothing — it edits the app's copy |
| Delete a file in the app | nothing — it deletes the app's copy |
| Delete a project | nothing — it deletes the app's folder |
| Export a file or project | nothing — it writes a new copy where you say |
| Import a project | nothing — the folder is copied in |

So the app can never damage your source files, and equally it will never pick
up a change you make to them outside it.

### Where things live

```
~/.blueprints/                    the library
  projects.json                   index of project names
  <project>/                      one folder per project
    <your files>                  copies, in whatever folders you make
    markers/
      <filename>.json             the markers for one file
```

Markers live **inside** the project folder, which is why exporting a project
and importing it somewhere else carries the annotations with it.

---

## USING IT

**Projects** — right-click empty space in the tree for `New Project` or
`Import Project…`. Right-click a project for `New File`, `Add Files`,
`Add Folder`, `Export Project…` and `Delete`.

**Markers** — open an image or a 3D model, then **right-click on the canvas**
to drop a marker. Left-click one to select it, drag to move it. The panel on
the right edits its title, description and scale. Everything saves as you go.

**3D navigation** — middle-drag orbits, scroll zooms, the slider under the
canvas scales the model.

**Text files** — open in the editor with a line-number gutter, and autosave as
you type. `New File` with no extension creates a `.txt`.

**Export** — the `SELECTED` block top-right exports the current file or the
whole project. Type a path or browse to it; it defaults to your Downloads
folder. Exporting a project writes `<folder you pick>/<project name>/`,
markers included.

**Import** — brings a folder in as a project. A project exported earlier comes
back complete. Guarded, see below.

---

## THE FILES

| File | What it does |
|---|---|
| `app.py` | The window and everything that coordinates: the project tree, which viewer to show, the right-click menus, and every import/export action. |
| `ui/project_manager.py` | `Project` and `ProjectManager` — creating, listing, deleting projects, and copying files into them. All filesystem, no Qt. |
| `ui/marker_manager.py` | Loads and saves a file's markers as JSON in the project's `markers/` folder. |
| `ui/viewer.py` | The 2D image viewer. Draws markers onto a copy of the pixmap, handles click-to-select and drag-to-move, converts screen coordinates to image coordinates. |
| `ui/viewer3d.py` | The 3D viewer: `Viewer3D` is the widget with its scale slider, `GL3DCanvas` is the OpenGL canvas underneath. Loads models with trimesh, draws them with smooth per-vertex shading, and projects/unprojects to place markers in 3D. |
| `ui/code_editor.py` | The text editor: line-number gutter, current-line highlight, row separators. |
| `ui/marker_panel.py` | The marker editor on the right — title, description, scale, delete. |
| `ui/file_panel.py` | The `SELECTED` block, plus `ExportDialog` and `FilePickDialog` — the app's own file browsers. |
| `ui/theme.py` | Every colour in the app, and the stylesheet built from them. |
| `BluePRINTER` | The launcher: builds the venv, installs deps, runs the app. |
| `install.sh` | One-time setup that also registers a desktop entry. |

---

## THE LOOK

**Cyanotype.** A blueprint is pale line work on deep blue paper, so the app is
a navy-black ground, drafting white text, one drafting blue for anything
interactive, and red reserved **exclusively** for markers — a marker should
never have to compete with a button for attention.

The geometry is flat and hard: no rounded corners, no gradients, no shadows.
`app.setStyle("Fusion")` in `main()` is load-bearing — native platform styles
re-round widgets regardless of the stylesheet.

**Every colour lives in `ui/theme.py`** and nothing else should hardcode one.
That includes the OpenGL clear colour and the marker colour, which are read
from the same palette and converted with `_rgb()` in `viewer3d.py`. Changing
the entire app's appearance is editing the palette block at the top of
`theme.py`.

```python
INK          # the app ground, deepest
PAPER        # panels, inputs, the drawing surface
RAISED       # tiles that sit above PAPER
LINE         # hairline borders
LINE_STRONG  # borders that need to read as an edge
TEXT         # drafting white
TEXT_DIM     # labels, line numbers, hints
TEXT_FAINT   # disabled
BLUE         # the accent
BLUE_BRIGHT  # hover
BLUE_DEEP    # pressed
BLUE_GHOST   # selection wash
MARKER       # markers only
```

---

# NOTES FOR WHOEVER WORKS ON THIS NEXT

Everything below was learned the hard way. Where something says a thing
breaks, it broke, and the fix in the code is the one that made it stop.

## This is PyQt6, and it was ported from PyQt5

If you find PyQt5 patterns in a snippet somewhere, these are the differences
that actually bite:

- **Enums are namespaced.** `Qt.LeftButton` → `Qt.MouseButton.LeftButton`,
  `Qt.UserRole` → `Qt.ItemDataRole.UserRole`, `Qt.AlignCenter` →
  `Qt.AlignmentFlag.AlignCenter`, and so on for every enum.
- **`exec_()` → `exec()`**.
- **`event.x()` and `event.y()` were REMOVED.** Not renamed — removed.
  `event.position()` returns a float `QPointF`. `GL3DCanvas._pos()` exists to
  convert it back to the ints the projection maths wants. The 2D viewer uses
  `event.position()` directly.
- **Two classes moved modules**: `QOpenGLWidget` from `QtWidgets` to
  `QtOpenGLWidgets`, and `QFileSystemModel` from `QtWidgets` to `QtGui`.
  Both produce a confusing `ImportError` naming a class that plainly exists.

## The OpenGL context is fragile, and the format matters

The 3D viewer draws with **fixed-function OpenGL** — `glBegin`/`glEnd`,
`gluSphere`, `glTranslatef`. That only exists in a **desktop GL compatibility
context**. It does not exist in OpenGL ES.

On Wayland, Qt6 goes through EGL, and unless you state the renderable type and
profile explicitly it will try to give you an ES context, which EGL then
rejects with `EGL_BAD_MATCH` — printed as `Failed to create context: 3009`,
and the viewer is simply black.

`default_gl_format()` in `viewer3d.py` states all three (renderable type,
compatibility profile, version 2.1). It must be applied as the **application
default before `QApplication` is constructed** — `main()` does this. Setting
the format on the widget alone is too late.

If you ever rewrite the 3D drawing in modern shader-based GL, this whole
constraint goes away and the format request can be dropped.

## Do not use QFileDialog in this app

`QFileDialog` — native or not — **crashed the compositor** on the development
machine (Hyprland + NVIDIA, SEGV, session dropped to its fallback config). The
native path also routes through the desktop portal, which opens at its own
last-used folder and ignores the directory you pass it, so it was doing the
wrong thing even when it did not crash.

Every picker in this app is therefore built from ordinary widgets —
`QTreeView` over a `QFileSystemModel`, inside a normal `QDialog`:

- `ExportDialog` — a typed path plus a browsable tree, used for both export
  and import (it is parameterised: `heading`, `action`, `pick_folder`,
  `must_exist`).
- `FilePickDialog` — the same thing with multi-select, for `Add Files`.

Both are in `ui/file_panel.py`. **Adding a `QFileDialog` call back into this
codebase will reintroduce the crash.**

## Import is guarded, and the guards are not decoration

`import_project()` copies an entire folder tree. Before the first byte is
copied it checks:

1. **Where it is.** Home, `/`, anything containing home, and the library
   folder itself are refused by name. Without this, picking home copies your
   whole account into `~/.blueprints` until the disk fills.
2. **How big.** `_survey_folder()` counts first and gives up at
   `MAX_IMPORT_FILES` (5000) or `MAX_IMPORT_BYTES` (2 GB).
3. **Symlinks.** The survey never follows them (`os.walk(followlinks=False)`,
   and linked directories are pruned), and `copytree(symlinks=True)` stores
   links as links. A folder containing a link to its own parent would
   otherwise copy forever.
4. **Your confirmation**, showing the path, file count and size.

A failed copy removes the half-written folder rather than leaving a broken
project behind.

## Never fail silently

An early `return` in a button handler is indistinguishable from a broken app,
and cost real debugging time here. Every action that can decline to run says
why, with a `QMessageBox`. Keep it that way.

## Where the app's state lives, and how it drifts

`self.current_project` and `self.current_file` are set by
`on_item_selected()`. They can get out of step with what is on screen, which
is why `export_current_project()` falls back to `_project_of(path)` — working
the project out from where the file actually sits on disk rather than trusting
the remembered value. Prefer deriving state from the filesystem over trusting
these two attributes.

---

## KNOWN ISSUE

**Markers key on the filename only, not the path.** `MarkerManager` builds the
JSON name as `self.current_file.name.replace('.', '_')`, so `plan.png`
anywhere in a project maps to `markers/plan_png.json`. Two files with the same
name in different folders of one project **share the same markers** — annotate
one and they appear on the other.

The fix is to include the path relative to the project root in that name. It
is not done yet because changing the key orphans every marker file that
already exists, so it needs a migration that renames the old files as it goes.

---

## ADDING THINGS

**A new file type** — `load_file_by_type()` in `app.py` dispatches on the
extension. Add yours to the right branch, or to a new one with its own viewer
widget. Anything unrecognised is sniffed as text and shows a "cannot preview"
message if it is binary.

**A new marker field** — markers are plain dicts
(`title`, `description`, `position`, `scale`), saved as a JSON list. Add a key,
add a widget to `MarkerPanel`, and have it emit `marker_changed`. Old marker
files stay readable because every read uses `.get()` with a default.

**A colour** — add it to the palette in `theme.py` and reference it. Do not
hardcode one in a widget.
