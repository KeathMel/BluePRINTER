#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QMenu, QMessageBox, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.theme import apply_iron_man_theme
from ui.viewer import ViewerWidget
from ui.viewer3d import Viewer3D
from ui.marker_panel import MarkerPanel
from ui.project_manager import ProjectManager
from ui.marker_manager import MarkerManager
from ui.file_panel import FilePanel, ExportDialog, FilePickDialog

def downloads_dir():
    """Where exports should land by default.

    Honours the XDG setting first, since a localised desktop calls it
    Téléchargements or Downloads depending on the system, then the plain
    ~/Downloads, and falls back to home if neither exists.
    """
    import os, subprocess
    try:
        out = subprocess.run(["xdg-user-dir", "DOWNLOAD"],
                             capture_output=True, text=True, timeout=2).stdout.strip()
        if out and Path(out).is_dir() and Path(out) != Path.home():
            return Path(out)
    except Exception:
        pass
    env = os.environ.get("XDG_DOWNLOAD_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    d = Path.home() / "Downloads"
    return d if d.is_dir() else Path.home()


class BlueprintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BluePRINTER")
        self.setGeometry(100, 100, 1800, 1000)
        
        self.project_manager = ProjectManager()
        self.marker_manager = None
        self.current_project = None
        self.current_file = None
        self.text_editor_file = None
        
        self.init_ui()
        apply_iron_man_theme(self)
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # LEFT - Projects/Files Tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        tree_title = QLabel("PROJECTS & FILES")
        tree_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        left_layout.addWidget(tree_title)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name"])
        self.tree.itemClicked.connect(self.on_item_selected)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_right_click)
        left_layout.addWidget(self.tree)
        
        btn_new_proj = QPushButton("+ NEW PROJECT")
        btn_new_proj.clicked.connect(self.create_project)
        left_layout.addWidget(btn_new_proj)
        
        # CENTER - Viewers
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.viewer = ViewerWidget()
        self.viewer.marker_selected.connect(self.on_marker_selected)
        self.viewer.marker_moved.connect(self.save_markers)
        center_layout.addWidget(self.viewer)
        
        self.viewer3d = Viewer3D()
        self.viewer3d.marker_selected.connect(self.on_marker_selected)
        self.viewer3d.marker_moved.connect(self.save_markers)
        self.viewer3d.setVisible(False)
        center_layout.addWidget(self.viewer3d)
        
        from ui.code_editor import CodeEditor
        self.text_editor = CodeEditor()
        self.text_editor.setVisible(False)
        self.text_editor.textChanged.connect(self.auto_save_text)
        center_layout.addWidget(self.text_editor)
        
        # RIGHT - what's selected, then the marker editor beneath it
        self.file_panel = FilePanel()
        self.file_panel.export_file.connect(self.export_current_file)
        self.file_panel.export_project.connect(self.export_current_project)

        self.marker_panel = MarkerPanel()
        self.marker_panel.marker_changed.connect(self.save_markers)
        self.marker_panel.marker_deleted.connect(self.on_marker_deleted)
        self.marker_panel.marker_scale_changed.connect(self.on_marker_scale_changed)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(4)
        right_layout.addWidget(self.file_panel)
        right_layout.addWidget(self.marker_panel)
        right_layout.addStretch()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_widget, 3)
        main_layout.addWidget(right_panel, 1)
        
        self.refresh_projects()
        self.tree.keyPressEvent = self.on_key_press
    
    def refresh_projects(self):
        self.tree.clear()
        for proj in self.project_manager.get_projects():
            (proj.path / "markers").mkdir(exist_ok=True)
            proj_item = QTreeWidgetItem(self.tree, [proj.name])
            proj_item.setData(0, Qt.ItemDataRole.UserRole, ('project', proj.name))
            self._add_tree_items(proj_item, proj.path)
        self.tree.expandAll()
    
    def _add_tree_items(self, parent, path):
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.') or item.name == 'markers':
                    continue
                
                tree_item = QTreeWidgetItem(parent, [item.name])
                
                if item.is_dir():
                    tree_item.setData(0, Qt.ItemDataRole.UserRole, ('folder', str(item)))
                    self._add_tree_items(tree_item, item)
                elif item.is_file():
                    tree_item.setData(0, Qt.ItemDataRole.UserRole, ('file', str(item)))
        except:
            pass
    
    def on_item_selected(self, item):
        item_type, item_path = item.data(0, Qt.ItemDataRole.UserRole) or (None, None)
        
        if item_type == 'project':
            self.current_project = self.project_manager.get_project(item_path)
            self.current_file = None
            self.viewer.clear()
            self.viewer3d.clear()
            self.marker_panel.clear()
            self.text_editor.setVisible(False)
            self.file_panel.show_project(
                self.current_project.name, len(self.current_project.get_files()))
        elif item_type == 'file':
            # Walk up the tree to find the parent project
            parent = item.parent()
            while parent is not None:
                p_type, p_path = parent.data(0, Qt.ItemDataRole.UserRole) or (None, None)
                if p_type == 'project':
                    self.current_project = self.project_manager.get_project(p_path)
                    break
                parent = parent.parent()
            
            self.current_file = Path(item_path)
            self.file_panel.show_file(
                self.current_file,
                self.current_project.name if self.current_project else None)
            self.load_file_by_type()
    
    def load_file_by_type(self):
        if not self.current_file or not self.current_project:
            return
        
        ext = self.current_file.suffix.lower()
        
        self.viewer.clear()
        self.viewer3d.clear()
        self.marker_panel.clear()
        self.text_editor.setVisible(False)
        self.text_editor_file = None
        
        self.marker_manager = MarkerManager(self.current_project, self.current_file)
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            self.viewer.load_file(str(self.current_file), self.current_project)
            self.viewer.setVisible(True)
            self.viewer3d.setVisible(False)
            self.load_markers()
        elif ext in ['.obj', '.glb', '.gltf']:
            self.viewer3d.load_file(str(self.current_file))
            self.viewer3d.setVisible(True)
            self.viewer.setVisible(False)
            self.load_markers()
        elif ext in ['.txt', '.py', '.js', '.md', '.json', '.xml', '.html', '.css']:
            self.load_text_file()
        else:
            # Unknown extension - try to open it as text; if it's binary, say so
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    f.read(1024)  # test it's readable text
                self.load_text_file()
            except Exception:
                self.viewer.setVisible(False)
                self.viewer3d.setVisible(False)
                self.text_editor.blockSignals(True)
                self.text_editor.setPlainText(
                    f"Cannot preview this file type: {ext}\n\n{self.current_file.name}"
                )
                self.text_editor.blockSignals(False)
                self.text_editor_file = None
                self.text_editor.setVisible(True)
    
    def load_text_file(self):
        self.viewer.setVisible(False)
        self.viewer3d.setVisible(False)
        self.marker_panel.clear()
        
        # Block auto-save while we populate the editor with the file's content
        self.text_editor.blockSignals(True)
        try:
            with open(self.current_file, 'r') as f:
                content = f.read()
            self.text_editor.setPlainText(content)
            self.text_editor_file = self.current_file
        except:
            self.text_editor.setPlainText("Error reading file")
            self.text_editor_file = None
        self.text_editor.blockSignals(False)
        
        self.text_editor.document().setDocumentMargin(8)
        self.text_editor.setVisible(True)
    
    def auto_save_text(self):
        # Only save when the editor is showing a real file and is visible
        if not getattr(self, 'text_editor_file', None):
            return
        if not self.text_editor.isVisible():
            return
        try:
            with open(self.text_editor_file, 'w') as f:
                f.write(self.text_editor.toPlainText())
        except Exception as e:
            print(f"[TEXT SAVE ERROR] {e}")
    
    def load_markers(self):
        if not self.marker_manager:
            return
        
        markers = self.marker_manager.load_markers()
        
        if self.viewer3d.isVisible():
            self.viewer3d.set_markers(markers)
        else:
            self.viewer.set_markers(markers)
    
    def save_markers(self):
        if not self.marker_manager:
            return
        
        markers = self.viewer3d.markers if self.viewer3d.isVisible() else self.viewer.markers
        self.marker_manager.markers = markers
        self.marker_manager.save_markers()
    
    def on_marker_selected(self, marker):
        self.marker_panel.set_marker(marker)
        # Persist immediately - covers newly created markers
        self.save_markers()
    
    def on_marker_deleted(self, marker):
        active = self.viewer3d if self.viewer3d.isVisible() else self.viewer
        
        # Remove by identity match
        active.markers = [m for m in active.markers if m is not marker]
        active.selected_marker = None
        active.dragging = False
        
        self.save_markers()
        
        if active is self.viewer3d:
            self.viewer3d.set_markers(active.markers)
        else:
            self.viewer.refresh_display()
    
    def on_marker_scale_changed(self, scale):
        self.save_markers()
        self.viewer.refresh_display()
        self.viewer3d.update()
    
    def export_current_file(self):
        """Copy the selected file back out to a path you type. The library's
        copy is untouched — this is a way OUT, not a move."""
        if not self.current_file:
            QMessageBox.information(
                self, "Nothing selected",
                "Click a file in the tree on the left first, then export it.")
            return
        if not self.current_file.exists():
            QMessageBox.warning(
                self, "File is gone",
                f"{self.current_file} is no longer on disk.")
            return

        dlg = ExportDialog(self, "Export file",
                           downloads_dir() / self.current_file.name)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        dest = dlg.path()
        if not str(dest).strip():
            return
        # a folder given instead of a file path: keep the original name
        if dest.is_dir():
            dest = dest / self.current_file.name

        import shutil
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.current_file, dest)
        except Exception as e:
            QMessageBox.warning(self, "Export failed", f"Could not write it:\n{e}")
            return
        QMessageBox.information(self, "Exported", f"Saved to\n{dest}")

    def export_current_project(self):
        """Copy the whole project — files and their markers — into a folder
        you type. It lands as <that folder>/<project name>/."""
        project = self.current_project or self._project_of(self.current_file)
        if not project:
            QMessageBox.information(
                self, "No project selected",
                "Click a project (or a file inside one) first.")
            return

        dlg = ExportDialog(self, "Export project", downloads_dir(),
                           pick_folder=True)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        folder = dlg.path()
        if not str(folder).strip():
            return

        import shutil
        dest = folder / project.name
        if dest.exists():
            reply = QMessageBox.question(
                self, "Already there",
                f"{dest} already exists. Replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                shutil.rmtree(dest)
            except Exception as e:
                QMessageBox.warning(self, "Export failed", f"Could not replace it:\n{e}")
                return
        try:
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copytree(project.path, dest)
        except Exception as e:
            QMessageBox.warning(self, "Export failed", f"Could not write it:\n{e}")
            return
        QMessageBox.information(self, "Exported", f"Saved to\n{dest}")

    # importing copies a whole folder tree, so it gets hard limits: without
    # them, pointing it at $HOME or / copies everything into ~/.blueprints
    # until the disk fills, and a symlink pointing upward loops forever.
    MAX_IMPORT_FILES = 5000
    MAX_IMPORT_BYTES = 2 * 1024 * 1024 * 1024      # 2 GB

    def _survey_folder(self, src):
        """Count what an import would copy, giving up early once it is clearly
        too big. Returns (files, bytes, too_big). Never follows symlinks."""
        files = 0
        total = 0
        for root, dirs, names in os.walk(src, followlinks=False):
            # don't descend into linked directories at all
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for n in names:
                fp = os.path.join(root, n)
                if os.path.islink(fp):
                    continue
                files += 1
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
                if files > self.MAX_IMPORT_FILES or total > self.MAX_IMPORT_BYTES:
                    return files, total, True
        return files, total, False

    def _import_refusal(self, src):
        """Why this folder must not be imported, or None if it is fine."""
        home = Path.home().resolve()
        root = self.project_manager.projects_dir.resolve()
        try:
            s = src.resolve()
        except Exception:
            return "that path can't be resolved."

        if not s.is_dir():
            return f"{s} isn't a folder."
        if s == Path(s.anchor):
            return "that's the root of the filesystem."
        if s == home:
            return ("that's your home folder — importing it would copy your "
                    "entire account into the library.")
        if s in home.parents:
            return "that folder contains your home folder."
        if s == root or root in s.parents or s in root.parents:
            return ("that folder is where BluePRINTER keeps its own projects — "
                    "importing it into itself would never finish.")
        return None

    def import_project(self):
        """Bring a folder in from disk as a whole project.

        The counterpart to Export Project: a folder exported earlier comes back
        complete, markers and all. The folder on disk is copied, not moved.

        Everything is checked BEFORE a single byte is copied — where it is, how
        big it is, and how many files — because a runaway copy here fills the
        disk and takes the desktop session with it."""
        dlg = ExportDialog(
            self, "Import project", downloads_dir(),
            pick_folder=True, heading="IMPORT FROM", action="IMPORT",
            hint="The folder to bring in — it becomes a project",
            must_exist=True)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        src = dlg.path()

        refusal = self._import_refusal(src)
        if refusal:
            QMessageBox.warning(self, "Can't import that", refusal)
            return

        files, total, too_big = self._survey_folder(src)
        if too_big:
            QMessageBox.warning(
                self, "Too big to import",
                f"{src}\n\nis over the limit "
                f"({self.MAX_IMPORT_FILES} files or "
                f"{self.MAX_IMPORT_BYTES // (1024**3)} GB).\n\n"
                "Pick the actual project folder rather than a folder that "
                "contains many of them.")
            return
        if files == 0:
            QMessageBox.warning(self, "Nothing in there",
                                f"{src} has no files to import.")
            return

        mb = total / (1024 * 1024)
        confirm = QMessageBox.question(
            self, "Import this folder?",
            f"{src}\n\n{files} file{'s' if files != 1 else ''}, {mb:.1f} MB\n\n"
            "It will be copied into your projects. The original stays put.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return

        name = src.name
        dest = self.project_manager.projects_dir / name
        if dest.exists():
            from PyQt6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(
                self, "Name taken",
                f"A project called '{src.name}' already exists.\nName it:",
                text=f"{src.name}-2")
            if not ok or not name.strip():
                return
            name = name.strip().replace('/', '_')
            dest = self.project_manager.projects_dir / name
            if dest.exists():
                QMessageBox.warning(self, "Still taken",
                                    f"'{name}' exists too. Nothing imported.")
                return

        import shutil
        try:
            # symlinks=True copies links AS links: it never follows one out of
            # the tree, and never loops on one pointing at a parent
            shutil.copytree(src, dest, symlinks=True)
        except Exception as e:
            # a half-copied project is worse than none
            shutil.rmtree(dest, ignore_errors=True)
            QMessageBox.warning(self, "Import failed", f"Could not copy it:\n{e}")
            return

        self.project_manager._save_project_index(name)
        self.refresh_projects()
        project = self.project_manager.get_project(name)
        self.current_project = project
        self.current_file = None
        self.file_panel.show_project(name, len(project.get_files()))
        QMessageBox.information(
            self, "Imported",
            f"'{name}' is in your projects now.\nThe folder at {src} is untouched.")

    def _project_of(self, path):
        """Which project does this file belong to? Derived from where it sits
        on disk, so the export works even when the tree selection and the
        remembered project have drifted apart."""
        if not path:
            return None
        root = self.project_manager.projects_dir
        try:
            rel = Path(path).resolve().relative_to(Path(root).resolve())
        except Exception:
            return None
        if not rel.parts:
            return None
        return self.project_manager.get_project(rel.parts[0])

    def new_text_file(self, item):
        """Create an empty file inside the project and open it. Everything
        else here arrives by import; this is the way to start one from
        nothing."""
        from PyQt6.QtWidgets import QInputDialog
        item_type, item_data = item.data(0, Qt.ItemDataRole.UserRole) or (None, None)

        if item_type == 'project':
            project = self.project_manager.get_project(item_data)
            parent_path = project.path
        elif item_type == 'folder':
            parent_path = Path(item_data)
            project = self.current_project
        else:
            return

        name, ok = QInputDialog.getText(
            self, "New file", "File name:", text="notes.txt")
        if not ok or not name.strip():
            return
        name = name.strip()
        # no extension given: it's a text file, say so in the name
        if '.' not in name:
            name += '.txt'

        path = parent_path / name
        if path.exists():
            QMessageBox.warning(self, "Already exists",
                                f"{name} is already in there.")
            return
        try:
            path.touch()
        except Exception as e:
            QMessageBox.warning(self, "Could not create", str(e))
            return

        self.refresh_projects()
        # open it straight away so you can start typing
        if project is not None:
            self.current_project = project
        self.current_file = path
        self.file_panel.show_file(
            path, self.current_project.name if self.current_project else None)
        self.load_file_by_type()
        self.text_editor.setFocus()

    def on_right_click(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu()
        
        if item:
            item_type, item_path = item.data(0, Qt.ItemDataRole.UserRole) or (None, None)
            
            if item_type == 'project':
                menu.addAction("New File", lambda: self.new_text_file(item))
                menu.addAction("Import Project…", self.import_project)
                menu.addAction("Add Files", lambda: self.add_files_to_project(item))
                menu.addAction("Add Folder", lambda: self.add_folder(item))
                menu.addSeparator()
                menu.addAction("Export Project…", self.export_current_project)
                menu.addAction("Delete", lambda: self.delete_item(item))
            elif item_type == 'folder':
                menu.addAction("New File", lambda: self.new_text_file(item))
                menu.addAction("Add Files", lambda: self.add_files_to_folder(item))
                menu.addAction("Add Folder", lambda: self.add_folder(item))
                menu.addSeparator()
                menu.addAction("Delete", lambda: self.delete_item(item))
            elif item_type == 'file':
                menu.addAction("Export…", self.export_current_file)
                menu.addAction("Delete", lambda: self.delete_item(item))
        else:
            menu.addAction("New Project", self.create_project)
            menu.addAction("Import Project…", self.import_project)
        
        menu.exec(self.tree.mapToGlobal(pos))
    
    def on_key_press(self, event):
        if event.key() == Qt.Key.Key_Delete:
            item = self.tree.currentItem()
            if item:
                self.delete_item(item)
    
    def create_project(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("New Project")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Project Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        btn = QPushButton("Create")
        btn.clicked.connect(lambda: self._create_project_confirmed(name_input.text(), dialog))
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _create_project_confirmed(self, name, dialog):
        if name:
            self.project_manager.create_project(name)
            self.refresh_projects()
            dialog.close()
    
    def add_files_to_project(self, proj_item):
        item_type, proj_name = proj_item.data(0, Qt.ItemDataRole.UserRole) or (None, None)
        if item_type != 'project':
            return
        
        project = self.project_manager.get_project(proj_name)
        dlg = FilePickDialog(self, downloads_dir())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        files = dlg.files()
        added = 0
        for f in files:
            try:
                project.add_file(f)
                added += 1
            except Exception as e:
                QMessageBox.warning(self, "Add File Failed", f"Could not add {Path(f).name}:\n{e}")
        
        self.refresh_projects()
    
    def add_files_to_folder(self, folder_item):
        item_type, folder_path = folder_item.data(0, Qt.ItemDataRole.UserRole) or (None, None)
        if item_type != 'folder':
            return
        
        import shutil
        dlg = FilePickDialog(self, downloads_dir())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        files = dlg.files()
        for f in files:
            try:
                shutil.copy(f, Path(folder_path) / Path(f).name)
            except Exception as e:
                QMessageBox.warning(self, "Add File Failed", f"Could not add {Path(f).name}:\n{e}")
        
        self.refresh_projects()
    
    def add_folder(self, item):
        from PyQt6.QtWidgets import QInputDialog
        item_type, item_data = item.data(0, Qt.ItemDataRole.UserRole) or (None, None)
        
        # Resolve the parent directory
        if item_type == 'project':
            project = self.project_manager.get_project(item_data)
            parent_path = project.path
        elif item_type == 'folder':
            parent_path = Path(item_data)
        else:
            return
        
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name.strip():
            new_folder = parent_path / name.strip()
            new_folder.mkdir(parents=True, exist_ok=True)
            self.refresh_projects()
    
    def delete_item(self, item):
        item_type, item_path = item.data(0, Qt.ItemDataRole.UserRole) or (None, None)
        
        reply = QMessageBox.question(self, "Delete", f"Delete {item.text(0)}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if item_type == 'project':
                self.project_manager.delete_project(item_path)
            elif item_type in ['file', 'folder']:
                import shutil
                path = Path(item_path)
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            
            self.file_panel.clear()
            self.refresh_projects()

def main():
    # The GL format has to be the application default BEFORE QApplication is
    # constructed — a format set only on the widget comes too late, and the
    # context creation fails with EGL_BAD_MATCH on Wayland.
    from PyQt6.QtGui import QSurfaceFormat
    from ui.viewer3d import default_gl_format
    QSurfaceFormat.setDefaultFormat(default_gl_format())

    app = QApplication(sys.argv)
    # Fusion respects stylesheets literally (native styles round and smooth
    # widgets regardless of CSS), which is what keeps the flat cyanotype
    # geometry actually flat. Load-bearing — see the theme notes in README.
    app.setStyle("Fusion")
    window = BlueprintApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
