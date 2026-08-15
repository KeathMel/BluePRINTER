#!/usr/bin/env python3
import sys
import json
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QTextEdit,
                             QDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.theme import apply_iron_man_theme
from ui.viewer import ViewerWidget
from ui.project_manager import ProjectManager

class BlueprintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BluePRINTER")
        self.setGeometry(100, 100, 1800, 1000)
        
        self.project_manager = ProjectManager()
        self.current_project = None
        self.current_file = None
        self.selected_marker = None
        self.selected_item = None
        
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
        tree_title.setFont(QFont("Courier", 11, QFont.Bold))
        tree_title.setStyleSheet("color: #00D9FF;")
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
        
        # CENTER - Viewer (images, text files, 3D)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Image/3D viewer
        self.viewer = ViewerWidget()
        self.viewer.marker_selected.connect(self.on_marker_selected)
        center_layout.addWidget(self.viewer)
        
        # Text file editor
        self.text_editor = QTextEdit()
        self.text_editor.setVisible(False)
        self.text_editor.textChanged.connect(self.auto_save_text_file)
        center_layout.addWidget(self.text_editor)
        
        # RIGHT - Marker Panel (only for image annotations)
        self.marker_panel = QWidget()
        marker_layout = QVBoxLayout(self.marker_panel)
        
        marker_title = QLabel("MARKER")
        marker_title.setFont(QFont("Courier", 11, QFont.Bold))
        marker_title.setStyleSheet("color: #7D3AFF;")
        marker_layout.addWidget(marker_title)
        
        marker_layout.addWidget(QLabel("Title:"))
        self.marker_title = QLineEdit()
        self.marker_title.setPlaceholderText("Marker title...")
        self.marker_title.textChanged.connect(self.auto_save_marker)
        marker_layout.addWidget(self.marker_title)
        
        marker_layout.addWidget(QLabel("Description:"))
        self.marker_desc = QTextEdit()
        self.marker_desc.setPlaceholderText("Marker description...")
        self.marker_desc.setMaximumHeight(200)
        self.marker_desc.textChanged.connect(self.auto_save_marker)
        marker_layout.addWidget(self.marker_desc)
        
        marker_layout.addStretch()
        self.marker_panel.setLayout(marker_layout)
        self.marker_panel.setVisible(False)
        
        # Main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_widget, 3)
        main_layout.addWidget(self.marker_panel, 1)
        
        self.refresh_projects()
        
        # Key press events
        self.tree.keyPressEvent = self.on_key_press
        
    def refresh_projects(self):
        self.tree.clear()
        for proj in self.project_manager.get_projects():
            markers_folder = proj.path / "markers"
            markers_folder.mkdir(exist_ok=True)
            
            proj_item = QTreeWidgetItem(self.tree, [proj.name])
            proj_item.setData(0, Qt.UserRole, ('project', proj.name))
            self._add_tree_items(proj_item, proj.path)
        self.tree.expandAll()
    
    def _add_tree_items(self, parent, path):
        try:
            if not path.exists():
                return
            
            for item in sorted(path.iterdir()):
                try:
                    if item.name.startswith('.') or item.name == 'markers' or item.name.endswith('.markers.json'):
                        continue
                    
                    tree_item = QTreeWidgetItem(parent, [item.name])
                    
                    if item.is_dir():
                        tree_item.setData(0, Qt.UserRole, ('folder', str(item)))
                        self._add_tree_items(tree_item, item)
                    elif item.is_file():
                        tree_item.setData(0, Qt.UserRole, ('file', str(item)))
                except:
                    pass
        except:
            pass
    
    def on_item_selected(self, item):
        self.selected_item = item
        
        item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
        
        if item_type == 'project':
            self.current_project = self.project_manager.get_project(item_path)
            self.current_file = None
            self.viewer.clear()
            self.text_editor.setVisible(False)
            self.marker_panel.setVisible(False)
        elif item_type == 'file':
            self.current_file = Path(item_path)
            self.load_file_by_type()
    
    def load_file_by_type(self):
        if not self.current_file:
            return
        
        ext = self.current_file.suffix.lower()
        
        # Always clear text editor and marker panel first
        self.text_editor.blockSignals(True)
        self.text_editor.setText("")
        self.text_editor.blockSignals(False)
        self.text_editor.setVisible(False)
        self.marker_panel.setVisible(False)
        self.marker_title.blockSignals(True)
        self.marker_title.setText("")
        self.marker_title.blockSignals(False)
        self.marker_desc.blockSignals(True)
        self.marker_desc.setText("")
        self.marker_desc.blockSignals(False)
        
        if ext in ['.txt', '.py', '.js', '.md', '.json', '.xml', '.html', '.css']:
            self.load_text_file()
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            self.load_image_file()
        elif ext in ['.obj', '.glb', '.gltf']:
            self.load_3d_file()
        else:
            self.viewer.clear()
    
    def load_text_file(self):
        try:
            with open(self.current_file, 'r') as f:
                content = f.read()
            self.text_editor.blockSignals(True)
            self.text_editor.setText(content)
            self.text_editor.blockSignals(False)
            self.text_editor.setVisible(True)
            self.viewer.clear()
            self.marker_panel.setVisible(False)
        except:
            self.text_editor.setText("Error reading file")
            self.text_editor.setVisible(True)
    
    def auto_save_text_file(self):
        if not self.current_file:
            return
        
        ext = self.current_file.suffix.lower()
        if ext not in ['.txt', '.py', '.js', '.md', '.json', '.xml', '.html', '.css']:
            return
        
        try:
            with open(self.current_file, 'w') as f:
                f.write(self.text_editor.toPlainText())
        except:
            pass
    
    def load_image_file(self):
        self.text_editor.setVisible(False)
        self.marker_panel.setVisible(False)
        self.viewer.load_file(str(self.current_file), self.current_project)
        self.load_markers()
    
    def load_3d_file(self):
        self.text_editor.setVisible(False)
        self.marker_panel.setVisible(False)
        self.viewer.load_file(str(self.current_file), self.current_project)
    
    def on_right_click(self, pos):
        item = self.tree.itemAt(pos)
        
        menu = QMenu()
        
        if item:
            item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
            
            if item_type == 'project':
                add_files = menu.addAction("Add Files")
                add_files.triggered.connect(lambda: self.add_files_to_project(item))
                
                add_folder = menu.addAction("Add Folder")
                add_folder.triggered.connect(lambda: self.add_folder(item))
                
                menu.addSeparator()
                
                delete = menu.addAction("Delete Project")
                delete.triggered.connect(lambda: self.delete_item_popup(item))
            
            elif item_type == 'folder':
                add_files = menu.addAction("Add Files")
                add_files.triggered.connect(lambda: self.add_files_to_folder(item))
                
                add_folder = menu.addAction("Add Folder")
                add_folder.triggered.connect(lambda: self.add_folder(item))
                
                menu.addSeparator()
                
                delete = menu.addAction("Delete Folder")
                delete.triggered.connect(lambda: self.delete_item_popup(item))
            
            elif item_type == 'file':
                menu.addAction("Delete File").triggered.connect(lambda: self.delete_item_popup(item))
        else:
            new_proj = menu.addAction("New Project")
            new_proj.triggered.connect(self.create_project)
        
        menu.exec_(self.tree.mapToGlobal(pos))
    
    def on_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            if self.selected_item:
                self.delete_item_popup(self.selected_item)
        else:
            QTreeWidget.keyPressEvent(self.tree, event)
    
    def create_project(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Project")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Project Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        btn = QPushButton("Create")
        btn.clicked.connect(lambda: self._create_project(name_input.text(), dialog))
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _create_project(self, name, dialog):
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
        
        folder = Path(folder_path)
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        for f in files:
            shutil.copy(f, folder / Path(f).name)
        
        self.refresh_projects()
    
    def add_folder(self, item):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Folder")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Folder Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        btn = QPushButton("Create")
        btn.clicked.connect(lambda: self._add_folder(item, name_input.text(), dialog))
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _add_folder(self, item, folder_name, dialog):
        try:
            item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
            
            if not folder_name:
                dialog.close()
                return
            
            if item_type == 'project':
                project = self.project_manager.get_project(item_path)
                folder_path = project.path / folder_name
            elif item_type in ['folder', 'file']:
                if item_type == 'file':
                    folder_path = Path(item_path).parent / folder_name
                else:
                    folder_path = Path(item_path) / folder_name
            else:
                dialog.close()
                return
            
            folder_path.mkdir(parents=True, exist_ok=True)
            dialog.close()
            self.refresh_projects()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create folder: {e}")
            dialog.close()
    
    def delete_item_popup(self, item):
        item_type, item_path = item.data(0, Qt.UserRole) or (None, None)
        
        if item_type == 'project':
            reply = QMessageBox.question(self, "Delete Project", 
                                         f"Delete '{item_path}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.project_manager.delete_project(item_path)
                self.refresh_projects()
        
        elif item_type in ['file', 'folder']:
            reply = QMessageBox.question(self, "Delete", 
                                         f"Delete '{Path(item_path).name}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                path = Path(item_path)
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                self.refresh_projects()
    
    def on_marker_selected(self, marker_data):
        self.selected_marker = marker_data
        self.marker_title.blockSignals(True)
        self.marker_desc.blockSignals(True)
        
        self.marker_title.setText(marker_data.get('title', ''))
        self.marker_desc.setPlainText(marker_data.get('description', ''))
        
        self.marker_title.blockSignals(False)
        self.marker_desc.blockSignals(False)
        
        self.marker_panel.setVisible(True)
    
    def auto_save_marker(self):
        if not self.selected_marker or not self.current_file or not self.current_project:
            return
        
        self.selected_marker['title'] = self.marker_title.text()
        self.selected_marker['description'] = self.marker_desc.toPlainText()
        
        self.save_markers()
    
    def load_markers(self):
        if not self.current_file or not self.current_project:
            return
        
        markers_folder = self.current_project.path / "markers"
        markers_folder.mkdir(exist_ok=True)
        
        file_hash = self.current_file.name.replace('.', '_')
        json_path = markers_folder / f"{file_hash}.json"
        
        if json_path.exists():
            with open(json_path) as f:
                markers = json.load(f)
                self.viewer.set_markers(markers)
        else:
            self.viewer.set_markers([])
    
    def save_markers(self):
        if not self.current_file or not self.current_project:
            return
        
        markers_folder = self.current_project.path / "markers"
        markers_folder.mkdir(exist_ok=True)
        
        file_hash = self.current_file.name.replace('.', '_')
        json_path = markers_folder / f"{file_hash}.json"
        
        with open(json_path, 'w') as f:
            json.dump(self.viewer.markers, f, indent=2)

def main():
    app = QApplication(sys.argv)
    window = BlueprintApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
