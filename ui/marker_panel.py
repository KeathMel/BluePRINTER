from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QSlider, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal

class MarkerPanel(QWidget):
    marker_changed = pyqtSignal(dict)
    marker_deleted = pyqtSignal(dict)
    marker_scale_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.selected_marker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        title_label = QLabel("MARKER")
        title_label.setStyleSheet("color: #2d89ef; font-weight: bold; font-size: 14pt;")
        layout.addWidget(title_label)
        
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.textChanged.connect(self._on_title_changed)
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(150)
        self.desc_input.textChanged.connect(self._on_desc_changed)
        layout.addWidget(self.desc_input)
        
        layout.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setValue(100)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setTickInterval(20)
        self.scale_slider.sliderMoved.connect(self._on_scale_changed)
        layout.addWidget(self.scale_slider)
        
        delete_btn = QPushButton("🗑 DELETE MARKER")
        delete_btn.setStyleSheet("QPushButton { background-color: #ee1111; color: white; padding: 8px; border: none; border-radius: 0px; } QPushButton:hover { background-color: #b91d47; }")
        delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        self.setVisible(False)
    
    def set_marker(self, marker):
        self.selected_marker = marker
        
        self.title_input.blockSignals(True)
        self.desc_input.blockSignals(True)
        self.scale_slider.blockSignals(True)
        
        self.title_input.setText(marker.get('title', ''))
        self.desc_input.setPlainText(marker.get('description', ''))
        self.scale_slider.setValue(int(marker.get('scale', 1.0) * 100))
        
        self.title_input.blockSignals(False)
        self.desc_input.blockSignals(False)
        self.scale_slider.blockSignals(False)
        
        self.setVisible(True)
    
    def _on_title_changed(self):
        if self.selected_marker:
            self.selected_marker['title'] = self.title_input.text()
            self.marker_changed.emit(self.selected_marker)
    
    def _on_desc_changed(self):
        if self.selected_marker:
            self.selected_marker['description'] = self.desc_input.toPlainText()
            self.marker_changed.emit(self.selected_marker)
    
    def _on_scale_changed(self):
        if self.selected_marker:
            scale = self.scale_slider.value() / 100.0
            self.selected_marker['scale'] = scale
            self.marker_scale_changed.emit(scale)
    
    def _on_delete(self):
        if not self.selected_marker:
            return
        
        reply = QMessageBox.question(self, "Delete Marker", 
                                     "Delete this marker?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            marker = self.selected_marker
            self.selected_marker = None
            self.clear()
            self.marker_deleted.emit(marker)
    
    def clear(self):
        self.selected_marker = None
        self.title_input.setText("")
        self.desc_input.setText("")
        self.scale_slider.setValue(100)
        self.setVisible(False)
