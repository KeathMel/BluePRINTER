from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QColor, QPainter, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, pyqtSignal
import math

class ViewerWidget(QWidget):
    marker_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.file_type = None
        self.markers = []
        self.dragging_marker = None
        self.image_pixmap = None
        
        self.viewer_label = QLabel()
        self.viewer_label.setAlignment(Qt.AlignCenter)
        self.viewer_label.setStyleSheet("background-color: #0A0E27;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.viewer_label)
        self.setStyleSheet("background-color: #0A0E27;")
        
        self.setMouseTracking(True)
        self.viewer_label.mouseMoveEvent = self.on_mouse_move
        self.viewer_label.mousePressEvent = self.on_mouse_press
        self.viewer_label.mouseReleaseEvent = self.on_mouse_release
    
    def load_file(self, file_path):
        self.current_file = Path(file_path)
        ext = self.current_file.suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            self.load_image(file_path)
            self.file_type = 'image'
        elif ext in ['.obj', '.glb', '.gltf']:
            self.load_3d(file_path)
            self.file_type = '3d'
        else:
            self.viewer_label.setText(f"Unsupported: {ext}")
    
    def load_image(self, file_path):
        pixmap = QPixmap(str(file_path))
        if pixmap.isNull():
            self.viewer_label.setText("Failed to load image")
            return
        
        scaled = pixmap.scaledToWidth(900, Qt.SmoothTransformation)
        self.image_pixmap = scaled
        self.refresh_display()
    
    def load_3d(self, file_path):
        self.viewer_label.setText(f"3D Model: {self.current_file.name}\n\n[3D viewer coming soon]")
        self.viewer_label.setStyleSheet("background-color: #0A0E27; color: #00D9FF; font-family: 'Courier New'; font-size: 14px;")
    
    def refresh_display(self):
        if not self.image_pixmap:
            return
        
        pixmap = self.image_pixmap.copy()
        painter = QPainter(pixmap)
        
        for marker in self.markers:
            x = marker.get('position', {}).get('x', 0)
            y = marker.get('position', {}).get('y', 0)
            
            painter.setPen(QPen(QColor(0, 217, 255), 2))
            painter.setBrush(QBrush(QColor(0, 217, 255, 100)))
            painter.drawEllipse(int(x - 15), int(y - 15), 30, 30)
            
            painter.setPen(QColor(0, 217, 255))
            painter.setFont(QFont("Courier", 8))
            painter.drawText(int(x + 20), int(y), marker.get('title', ''))
        
        painter.end()
        self.viewer_label.setPixmap(pixmap)
    
    def set_markers(self, markers):
        self.markers = markers
        self.refresh_display()
    
    def on_mouse_press(self, event):
        if self.file_type != 'image' or not self.image_pixmap:
            return
        
        pos = event.pos()
        
        for marker in self.markers:
            mx = marker.get('position', {}).get('x', 0)
            my = marker.get('position', {}).get('y', 0)
            
            dist = math.sqrt((pos.x() - mx)**2 + (pos.y() - my)**2)
            if dist < 30:
                self.marker_selected.emit(marker)
                self.dragging_marker = marker
                return
        
        marker = {
            'title': 'Marker',
            'description': '',
            'position': {'x': pos.x(), 'y': pos.y()}
        }
        self.markers.append(marker)
        self.refresh_display()
        self.marker_selected.emit(marker)
        self.dragging_marker = marker
    
    def on_mouse_move(self, event):
        if self.dragging_marker and self.file_type == 'image':
            pos = event.pos()
            self.dragging_marker['position']['x'] = pos.x()
            self.dragging_marker['position']['y'] = pos.y()
            self.refresh_display()
    
    def on_mouse_release(self, event):
        self.dragging_marker = None
    
    def clear(self):
        self.current_file = None
        self.markers = []
        self.image_pixmap = None
        self.viewer_label.setText("")
