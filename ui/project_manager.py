"""Projects and the library they live in. All filesystem, no Qt.

The library lives INSIDE the BluePRINTER folder (BluePRINTER/library/), so
the app, its projects and their markers move together as one folder. It
used to be ~/.blueprints; the first run after the move copies that across
once and leaves the old folder where it was.

Adding a file always COPIES it in. Your original is never opened for
writing, and a name that's already taken gets " (2)", " (3)"... instead of
overwriting the copy you've been editing.
"""
import json
import re
import shutil
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
LIBRARY = APP_DIR / "library"
OLD_LIBRARY = Path.home() / ".blueprints"


def unique_path(dest):
    """dest if it's free, otherwise 'name (2).ext', 'name (3).ext'..."""
    dest = Path(dest)
    if not dest.exists():
        return dest
    n = 2
    while True:
        cand = dest.with_name(f"{dest.stem} ({n}){dest.suffix}")
        if not cand.exists():
            return cand
        n += 1


def _companions(src):
    """Files a model needs next to it: .mtl + textures for .obj, buffers +
    images for .gltf. Relative paths as the model refers to them. (.glb is
    self-contained.) Without these a copied model loads grey or not at all."""
    src = Path(src)
    ext = src.suffix.lower()
    found = []
    try:
        if ext == ".obj":
            for line in src.read_text(errors="ignore").splitlines():
                if line.strip().startswith("mtllib"):
                    for name in line.split()[1:]:
                        found.append(name)
                        mtl = src.parent / name
                        if mtl.is_file():
                            for l in mtl.read_text(errors="ignore").splitlines():
                                parts = l.split()
                                if parts and re.match(r"^(map_\w+|bump|disp|decal|norm|refl)$",
                                                      parts[0], re.I) and len(parts) > 1:
                                    found.append(parts[-1])
        elif ext == ".gltf":
            data = json.loads(src.read_text(errors="ignore"))
            for key in ("buffers", "images"):
                for entry in data.get(key, []):
                    uri = entry.get("uri", "")
                    if uri and not uri.startswith("data:"):
                        found.append(uri)
    except Exception:
        pass
    return found


def import_file(src, dest_dir):
    """Copy one file (plus whatever a model needs) into dest_dir.

    Returns (dest_path, notes) — notes is a list of human-readable lines
    about anything that didn't go the obvious way.
    """
    src = Path(src)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    notes = []

    dest = unique_path(dest_dir / src.name)
    if dest.name != src.name:
        notes.append(f"{src.name} was already there, added as {dest.name}")
    shutil.copy2(src, dest)

    for rel in _companions(src):
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            notes.append(f"{src.name}: '{rel}' is outside its folder, not copied")
            continue
        c_src = src.parent / rel_path
        c_dest = dest_dir / rel_path
        if not c_src.is_file():
            notes.append(f"{src.name}: needs '{rel}' but it isn't there")
            continue
        if c_dest.exists():
            continue    # never overwrite — it may be another model's, or edited
        c_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(c_src, c_dest)
    return dest, notes


class Project:
    def __init__(self, name, path):
        self.name = name
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def add_file(self, file_path, dest_dir=None):
        return import_file(file_path, dest_dir or self.path)

    def get_files(self):
        files = []
        for ext in ['*.jpg', '*.png', '*.jpeg', '*.obj', '*.glb', '*.gltf', '*.txt', '*.py', '*.js', '*.md']:
            files.extend(self.path.glob(ext))
        return sorted(files)


class ProjectManager:
    def __init__(self):
        self.projects_dir = LIBRARY
        self._migrate_old_library()
        self.projects_dir.mkdir(exist_ok=True)
        self.config_file = self.projects_dir / "projects.json"

    def _migrate_old_library(self):
        """One-time copy from ~/.blueprints. Copy, not move: if anything goes
        wrong the old library is still there untouched."""
        if self.projects_dir.exists() or not OLD_LIBRARY.is_dir():
            return
        try:
            shutil.copytree(OLD_LIBRARY, self.projects_dir, symlinks=True)
            print(f"[BluePRINTER] copied your library from {OLD_LIBRARY} "
                  f"to {self.projects_dir} (the old one is untouched)")
        except Exception as e:
            shutil.rmtree(self.projects_dir, ignore_errors=True)
            print(f"[BluePRINTER] couldn't copy {OLD_LIBRARY}: {e}")

    def create_project(self, name):
        proj_path = self.projects_dir / name
        proj = Project(name, proj_path)
        self._save_project_index(name)
        return proj

    def get_project(self, name):
        return Project(name, self.projects_dir / name)

    def get_projects(self):
        projects = []
        for d in self.projects_dir.iterdir():
            if d.is_dir() and d.name != ".git":
                projects.append(Project(d.name, d))
        return sorted(projects, key=lambda p: p.name)

    def delete_project(self, name):
        proj_path = self.projects_dir / name
        if proj_path.exists():
            shutil.rmtree(proj_path)

    def _save_project_index(self, name):
        projects = []
        if self.config_file.exists():
            with open(self.config_file) as f:
                projects = json.load(f)

        if name not in projects:
            projects.append(name)

        with open(self.config_file, 'w') as f:
            json.dump(projects, f, indent=2)
