#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, 
                             QFileDialog, QLabel, QLineEdit, QTextEdit,
                             QDialog, QMessageBox, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QBrush, QPen, QColor

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
        
        self.init_ui()
        apply_iron_man_theme(self)
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # LEFT - Projects
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        proj_title = QLabel("PROJECTS")
        proj_title.setFont(QFont("Courier", 11, QFont.Bold))
        proj_title.setStyleSheet("color: #00D9FF;")
        left_layout.addWidget(proj_title)
        
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.open_project)
        left_layout.addWidget(self.projects_list)
        
        proj_buttons = QHBoxLayout()
        btn_new = QPushButton("+ NEW")
        btn_new.clicked.connect(self.create_project)
        proj_buttons.addWidget(btn_new)
        
        btn_delete = QPushButton("🗑")
        btn_delete.setMaximumWidth(50)
        btn_delete.clicked.connect(self.delete_project)
        proj_buttons.addWidget(btn_delete)
        proj_buttons.addStretch()
        
        left_layout.addLayout(proj_buttons)
        
        # CENTER-LEFT - File Tree
        tree_panel = QWidget()
        tree_layout = QVBoxLayout(tree_panel)
        
        tree_title = QLabel("FILES")
        tree_title.setFont(QFont("Courier", 10, QFont.Bold))
        tree_title.setStyleSheet("color: #7D3AFF;")
        tree_layout.addWidget(tree_title)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name"])
        self.file_tree.itemClicked.connect(self.on_file_selected)
        tree_layout.addWidget(self.file_tree)
        
        btn_add_file = QPushButton("+ ADD FILE")
        btn_add_file.clicked.connect(self.add_files_to_project)
        tree_layout.addWidget(btn_add_file)
        
        # CENTER - Viewer
        self.viewer = ViewerWidget()
        self.viewer.marker_selected.connect(self.on_marker_selected)
        
        # RIGHT - Annotations (hidden by default)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        
        ann_title = QLabel("MARKER")
        ann_title.setFont(QFont("Courier", 11, QFont.Bold))
        ann_title.setStyleSheet("color: #7D3AFF;")
        right_layout.addWidget(ann_title)
        
        right_layout.addWidget(QLabel("Title:"))
        self.marker_title = QLineEdit()
        self.marker_title.setPlaceholderText("Marker title...")
        self.marker_title.textChanged.connect(self.auto_save_marker)
        right_layout.addWidget(self.marker_title)
        
        right_layout.addWidget(QLabel("Description:"))
        self.marker_desc = QTextEdit()
        self.marker_desc.setPlaceholderText("Marker description...")
        self.marker_desc.setMaximumHeight(200)
        self.marker_desc.textChanged.connect(self.auto_save_marker)
        right_layout.addWidget(self.marker_desc)
        
        btn_delete_marker = QPushButton("DELETE MARKER")
        btn_delete_marker.clicked.connect(self.delete_marker)
        right_layout.addWidget(btn_delete_marker)
        
        right_layout.addStretch()
        self.right_panel.setVisible(False)
        
        # Main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(tree_panel, 1)
        main_layout.addWidget(self.viewer, 3)
        main_layout.addWidget(self.right_panel, 1)
        
        self.refresh_projects()
        
    def refresh_projects(self):
        self.projects_list.clear()
        for proj in self.project_manager.get_projects():
            self.projects_list.addItem(QListWidgetItem(proj.name))
    
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
    
    def delete_project(self):
        current = self.projects_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Select a project first")
            return
        
        reply = QMessageBox.question(self, "Delete Project", 
                                     f"Delete '{current.text()}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.project_manager.delete_project(current.text())
            self.current_project = None
            self.file_tree.clear()
            self.viewer.clear()
            self.refresh_projects()
    
    def open_project(self, item):
        self.current_project = self.project_manager.get_project(item.text())
        self.load_file_tree()
        self.viewer.clear()
    
    def load_file_tree(self):
        self.file_tree.clear()
        
        if not self.current_project:
            return
        
        root = QTreeWidgetItem(self.file_tree, [self.current_project.name])
        self._add_tree_items(root, self.current_project.path)
        self.file_tree.expandAll()
    
    def _add_tree_items(self, parent, path):
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                tree_item = QTreeWidgetItem(parent, [item.name])
                
                if item.is_dir():
                    self._add_tree_items(tree_item, item)
        except:
            pass
    
    def on_file_selected(self, item):
        if not self.current_project:
            return
        
        # Build full path from tree hierarchy
        path_parts = []
        current = item
        while current:
            path_parts.insert(0, current.text())
            current = current.parent()
        
        # Skip root project name
        path_parts = path_parts[1:]
        if not path_parts:
            return
            
        file_path = self.current_project.path
        for part in path_parts:
            file_path = file_path / part
        
        if file_path.is_file():
            self.current_file = file_path
            self.viewer.load_file(str(file_path))
            self.load_markers()
            self.right_panel.setVisible(False)
    
    def add_files_to_project(self):
        if not self.current_project:
            QMessageBox.warning(self, "Error", "Select a project first")
            return
        
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        for f in files:
            self.current_project.add_file(f)
        
        self.load_file_tree()
    
    def on_marker_selected(self, marker_data):
        self.selected_marker = marker_data
        self.marker_title.blockSignals(True)
        self.marker_desc.blockSignals(True)
        
        self.marker_title.setText(marker_data.get('title', ''))
        self.marker_desc.setPlainText(marker_data.get('description', ''))
        
        self.marker_title.blockSignals(False)
        self.marker_desc.blockSignals(False)
        
        self.right_panel.setVisible(True)
    
    def auto_save_marker(self):
        if not self.selected_marker or not self.current_file:
            return
        
        self.selected_marker['title'] = self.marker_title.text()
        self.selected_marker['description'] = self.marker_desc.toPlainText()
        
        self.save_markers()
    
    def load_markers(self):
        if not self.current_file:
            return
        
        json_path = Path(str(self.current_file) + ".markers.json")
        
        if json_path.exists():
            with open(json_path) as f:
                markers = json.load(f)
                self.viewer.set_markers(markers)
    
    def save_markers(self):
        if not self.current_file:
            return
        
        json_path = Path(str(self.current_file) + ".markers.json")
        
        with open(json_path, 'w') as f:
            json.dump(self.viewer.markers, f, indent=2)
    
    def delete_marker(self):
        if self.selected_marker and self.current_file:
            self.viewer.markers.remove(self.selected_marker)
            self.save_markers()
            self.viewer.refresh_display()
            self.right_panel.setVisible(False)
            self.selected_marker = None

def main():
    app = QApplication(sys.argv)
    window = BlueprintApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
