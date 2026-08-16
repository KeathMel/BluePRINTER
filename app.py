#!/usr/bin/env python3
import sys
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QMenu, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.theme import apply_iron_man_theme
from ui.viewer import ViewerWidget
from ui.viewer3d import Viewer3D
from ui.marker_panel import MarkerPanel
from ui.project_manager import ProjectManager
from ui.marker_manager import MarkerManager

class BlueprintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BluePRINTER")
        self.setGeometry(100, 100, 1800, 1000)
        
        self.project_manager = ProjectManager()
        self.marker_manager = None
        self.current_project = None
        self.current_file = None
        
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
        tree_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        left_layout.addWidget(tree_title)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name"])
        self.tree.itemClicked.connect(self.on_item_selected)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
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
        center_layout.addWidget(self.text_editor)
        
        # RIGHT - Marker Panel
        self.marker_panel = MarkerPanel()
        self.marker_panel.marker_changed.connect(self.save_markers)
        self.marker_panel.marker_deleted.connect(self.on_marker_deleted)
        self.marker_panel.marker_scale_changed.connect(self.on_marker_scale_changed)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_widget, 3)
        main_layout.addWidget(self.marker_panel, 1)
        
        self.refresh_projects()
        self.tree.keyPressEvent = self.on_key_press
    
    def refresh_projects(self):
        self.tree.clear()
        for proj in self.project_manager.get_projects():
            (proj.path / "markers").mkdir(exist_ok=True)
            proj_item = QTreeWidgetItem(self.tree, [proj.name])
            proj_item.setData(0, Qt.UserRole, ('project', proj.name))
            self._add_tree_items(proj_item, proj.path)
        self.tree.expandAll()
    
    def _add_tree_items(self, parent, path):
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.') or item.name == 'markers':
                    continue
                
                tree_item = QTreeWidgetItem(parent, [item.name])
                
                if item.is_dir():
                    tree_item.setData(0, Qt.UserRole, ('folder', str(item)))
                    self._add_tree_items(tree_item, item)
                elif item.is_file():
                    tree_item.setData(0, Qt.UserRole, ('file', str(item)))
        except:
            pass
    
    def on_item_selected(self, item):
        item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
        
        if item_type == 'project':
            self.current_project = self.project_manager.get_project(item_path)
            self.current_file = None
            self.viewer.clear()
            self.viewer3d.clear()
            self.marker_panel.clear()
        elif item_type == 'file':
            # Walk up the tree to find the parent project
            parent = item.parent()
            while parent is not None:
                p_type, p_path = parent.data(0, Qt.UserRole) or (None, None)
                if p_type == 'project':
                    self.current_project = self.project_manager.get_project(p_path)
                    break
                parent = parent.parent()
            
            self.current_file = Path(item_path)
            self.load_file_by_type()
    
    def load_file_by_type(self):
        if not self.current_file or not self.current_project:
            return
        
        ext = self.current_file.suffix.lower()
        
        self.viewer.clear()
        self.viewer3d.clear()
        self.marker_panel.clear()
        self.text_editor.setVisible(False)
        
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
            self.viewer.setVisible(False)
            self.viewer3d.setVisible(False)
    
    def load_text_file(self):
        self.viewer.setVisible(False)
        self.viewer3d.setVisible(False)
        self.marker_panel.clear()
        
        try:
            with open(self.current_file, 'r') as f:
                content = f.read()
            self.text_editor.setPlainText(content)
        except:
            self.text_editor.setPlainText("Error reading file")
        
        self.text_editor.document().setDocumentMargin(8)
        self.text_editor.setVisible(True)
    
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
        print(f"[SAVE] {len(markers)} markers -> {self.marker_manager.current_file.name}")
    
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
    
    def on_right_click(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu()
        
        if item:
            item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
            
            if item_type == 'project':
                menu.addAction("Add Files", lambda: self.add_files_to_project(item))
                menu.addAction("Delete", lambda: self.delete_item(item))
            elif item_type == 'folder':
                menu.addAction("Add Files", lambda: self.add_files_to_folder(item))
                menu.addAction("Delete", lambda: self.delete_item(item))
            elif item_type == 'file':
                menu.addAction("Delete", lambda: self.delete_item(item))
        else:
            menu.addAction("New Project", self.create_project)
        
        menu.exec_(self.tree.mapToGlobal(pos))
    
    def on_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            item = self.tree.currentItem()
            if item:
                self.delete_item(item)
    
    def create_project(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton
        
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
        dialog.exec_()
    
    def _create_project_confirmed(self, name, dialog):
        if name:
            self.project_manager.create_project(name)
            self.refresh_projects()
            dialog.close()
    
    def add_files_to_project(self, proj_item):
        item_type, proj_name = proj_item.data(0, Qt.UserRole) or (None, None)
        if item_type != 'project':
            return
        
        project = self.project_manager.get_project(proj_name)
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        for f in files:
            project.add_file(f)
        
        self.refresh_projects()
    
    def add_files_to_folder(self, folder_item):
        item_type, folder_path = folder_item.data(0, Qt.UserRole) or (None, None)
        if item_type != 'folder':
            return
        
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        for f in files:
            import shutil
            shutil.copy(f, Path(folder_path) / Path(f).name)
        
        self.refresh_projects()
    
    def delete_item(self, item):
        item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
        
        reply = QMessageBox.question(self, "Delete", f"Delete {item.text(0)}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if item_type == 'project':
                self.project_manager.delete_project(item_path)
            elif item_type in ['file', 'folder']:
                import shutil
                path = Path(item_path)
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            
            self.refresh_projects()

def main():
    app = QApplication(sys.argv)
    # Fusion respects stylesheets literally (native styles round/smooth widgets
    # regardless of CSS), giving us true flat Metro rectangles.
    app.setStyle("Fusion")
    window = BlueprintApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
