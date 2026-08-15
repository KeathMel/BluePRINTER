#!/usr/bin/env python3
"""
3D Annotation Blueprint Viewer
Iron Man themed desktop application
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, 
                             QFileDialog, QSplitter, QLabel, QLineEdit, QTextEdit,
                             QDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtOpenGL import QGLWidget

from ui.theme import apply_iron_man_theme
from ui.viewer import ViewerWidget
from ui.project_manager import ProjectManager

class BlueprintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueprint Viewer - Iron Man Edition")
        self.setGeometry(100, 100, 1600, 900)
        
        self.project_manager = ProjectManager()
        self.current_project = None
        self.current_file_index = 0
        self.current_files = []
        
        self.init_ui()
        apply_iron_man_theme(self)
        
    def init_ui(self):
        """Initialize UI components"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Left panel - Projects list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        title = QLabel("PROJECTS")
        title.setFont(QFont("Courier", 12, QFont.Bold))
        title.setStyleSheet("color: #00D9FF;")
        left_layout.addWidget(title)
        
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.open_project)
        left_layout.addWidget(self.projects_list)
        
        btn_new = QPushButton("+ NEW PROJECT")
        btn_new.clicked.connect(self.create_project)
        left_layout.addWidget(btn_new)
        
        # Center panel - File viewer
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # Top bar
        top_bar = QHBoxLayout()
        self.project_name = QLabel("No Project")
        self.project_name.setFont(QFont("Courier", 14, QFont.Bold))
        self.project_name.setStyleSheet("color: #00D9FF;")
        top_bar.addWidget(self.project_name)
        
        self.btn_add_file = QPushButton("+ ADD FILES")
        self.btn_add_file.clicked.connect(self.add_files)
        self.btn_add_file.setEnabled(False)
        top_bar.addWidget(self.btn_add_file)
        
        self.btn_view_planner = QPushButton("VIEW PLANNER")
        self.btn_view_planner.clicked.connect(self.toggle_view_planner)
        self.btn_view_planner.setEnabled(False)
        top_bar.addWidget(self.btn_view_planner)
        
        center_layout.addLayout(top_bar)
        
        # Viewer widget
        self.viewer = ViewerWidget()
        center_layout.addWidget(self.viewer)
        
        # Bottom navigation
        bottom_bar = QHBoxLayout()
        self.btn_prev = QPushButton("◀ PREV")
        self.btn_prev.clicked.connect(self.prev_file)
        bottom_bar.addWidget(self.btn_prev)
        
        self.file_label = QLabel("No files")
        self.file_label.setAlignment(Qt.AlignCenter)
        bottom_bar.addWidget(self.file_label)
        
        self.btn_next = QPushButton("NEXT ▶")
        self.btn_next.clicked.connect(self.next_file)
        bottom_bar.addWidget(self.btn_next)
        
        center_layout.addLayout(bottom_bar)
        
        # Right panel - Annotations
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        ann_title = QLabel("ANNOTATIONS")
        ann_title.setFont(QFont("Courier", 11, QFont.Bold))
        ann_title.setStyleSheet("color: #7D3AFF;")
        right_layout.addWidget(ann_title)
        
        right_layout.addWidget(QLabel("Title:"))
        self.marker_title = QLineEdit()
        self.marker_title.setPlaceholderText("Marker title...")
        right_layout.addWidget(self.marker_title)
        
        right_layout.addWidget(QLabel("Description:"))
        self.marker_desc = QTextEdit()
        self.marker_desc.setPlaceholderText("Marker description...")
        self.marker_desc.setMaximumHeight(150)
        right_layout.addWidget(self.marker_desc)
        
        btn_save = QPushButton("SAVE MARKER")
        btn_save.clicked.connect(self.save_marker)
        right_layout.addWidget(btn_save)
        
        btn_delete = QPushButton("DELETE SELECTED")
        btn_delete.clicked.connect(self.delete_marker)
        right_layout.addWidget(btn_delete)
        
        self.markers_list = QListWidget()
        right_layout.addWidget(self.markers_list)
        
        # Add all to main
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_panel, 3)
        main_layout.addWidget(right_panel, 1)
        
        self.refresh_projects()
        
    def refresh_projects(self):
        """Refresh projects list"""
        self.projects_list.clear()
        for proj in self.project_manager.get_projects():
            self.projects_list.addItem(QListWidgetItem(proj.name))
    
    def create_project(self):
        """Create new project"""
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
    
    def open_project(self, item):
        """Open selected project"""
        self.current_project = self.project_manager.get_project(item.text())
        self.project_name.setText(self.current_project.name)
        self.btn_add_file.setEnabled(True)
        self.btn_view_planner.setEnabled(True)
        self.refresh_files()
    
    def add_files(self):
        """Add files to project"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        for f in files:
            self.current_project.add_file(f)
        self.refresh_files()
    
    def refresh_files(self):
        """Refresh file list"""
        self.current_files = self.current_project.get_files()
        self.current_file_index = 0
        self.show_current_file()
    
    def show_current_file(self):
        """Display current file"""
        if not self.current_files:
            self.file_label.setText("No files")
            return
        
        file_path = self.current_files[self.current_file_index]
        self.file_label.setText(f"{self.current_file_index + 1} / {len(self.current_files)}")
        
        self.viewer.load_file(file_path)
        self.load_markers(file_path)
    
    def next_file(self):
        """Next file"""
        if self.current_files:
            self.current_file_index = (self.current_file_index + 1) % len(self.current_files)
            self.show_current_file()
    
    def prev_file(self):
        """Previous file"""
        if self.current_files:
            self.current_file_index = (self.current_file_index - 1) % len(self.current_files)
            self.show_current_file()
    
    def toggle_view_planner(self):
        """Toggle view planner"""
        self.viewer.toggle_planner()
    
    def load_markers(self, file_path):
        """Load markers for current file"""
        json_path = Path(str(file_path) + ".markers.json")
        self.markers_list.clear()
        self.viewer.markers = []
        
        if json_path.exists():
            with open(json_path) as f:
                markers = json.load(f)
                for m in markers:
                    self.markers_list.addItem(QListWidgetItem(m['title']))
                    self.viewer.markers.append(m)
    
    def save_marker(self):
        """Save marker for current file"""
        if not self.current_files:
            return
        
        file_path = self.current_files[self.current_file_index]
        json_path = Path(str(file_path) + ".markers.json")
        
        marker = {
            'title': self.marker_title.text(),
            'description': self.marker_desc.toPlainText(),
            'position': self.viewer.get_marker_position(),
        }
        
        markers = []
        if json_path.exists():
            with open(json_path) as f:
                markers = json.load(f)
        
        markers.append(marker)
        
        with open(json_path, 'w') as f:
            json.dump(markers, f, indent=2)
        
        self.load_markers(file_path)
        self.marker_title.clear()
        self.marker_desc.clear()
        QMessageBox.information(self, "Success", "Marker saved!")
    
    def delete_marker(self):
        """Delete selected marker"""
        current = self.markers_list.currentRow()
        if current >= 0 and self.current_files:
            file_path = self.current_files[self.current_file_index]
            json_path = Path(str(file_path) + ".markers.json")
            
            if json_path.exists():
                with open(json_path) as f:
                    markers = json.load(f)
                
                markers.pop(current)
                
                with open(json_path, 'w') as f:
                    json.dump(markers, f, indent=2)
                
                self.load_markers(file_path)

def main():
    app = QApplication(sys.argv)
    window = BlueprintApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
