"""Image and 3D viewer with annotations"""

from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QColor, QPainter, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtOpenGL import QGLWidget
import math

class ViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.file_type = None
        self.markers = []
        self.dragging_marker = None
        self.dragging_pos = None
        self.planner_mode = False
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = 1.0
        
        # Image viewer
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: rgba(26, 31, 58, 0.8); border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        self.setStyleSheet("background-color: #0A0E27;")
        
        # Mouse tracking
        self.setMouseTracking(True)
        self.image_label.mouseMoveEvent = self.on_mouse_move
        self.image_label.mousePressEvent = self.on_mouse_press
        self.image_label.mouseReleaseEvent = self.on_mouse_release
        self.image_label.wheelEvent = self.on_wheel
    
    def load_file(self, file_path):
        """Load image or 3D file"""
        self.current_file = Path(file_path)
        ext = self.current_file.suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            self.load_image(file_path)
            self.file_type = 'image'
        elif ext in ['.obj', '.glb', '.gltf']:
            self.load_3d(file_path)
            self.file_type = '3d'
        else:
            self.image_label.setText(f"File type not supported: {ext}")
    
    def load_image(self, file_path):
        """Load and display image"""
        pixmap = QPixmap(str(file_path))
        if pixmap.isNull():
            self.image_label.setText("Failed to load image")
            return
        
        # Scale to fit
        scaled = pixmap.scaledToWidth(800, Qt.SmoothTransformation)
        self.image_pixmap = scaled
        self.update_image_display()
    
    def load_3d(self, file_path):
        """Load 3D model"""
        # For now, show placeholder
        self.image_label.setText(f"3D Model: {self.current_file.name}\n\nDrag the ball around.\nRight side shows rotated view.")
        self.image_label.setStyleSheet("background-color: rgba(26, 31, 58, 0.8); border-radius: 8px; color: #00D9FF; font-family: 'Courier New'; font-size: 14px;")
    
    def update_image_display(self):
        """Update image with markers"""
        if not hasattr(self, 'image_pixmap'):
            return
        
        pixmap = self.image_pixmap.copy()
        painter = QPainter(pixmap)
        
        # Draw markers (balls/stickers)
        for marker in self.markers:
            x = marker.get('position', {}).get('x', 0)
            y = marker.get('position', {}).get('y', 0)
            
            # Draw glow circle
            painter.setPen(QPen(QColor(0, 217, 255), 2))
            painter.setBrush(QBrush(QColor(0, 217, 255, 100)))
            painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)
            
            # Draw title
            painter.setPen(QColor(0, 217, 255))
            painter.setFont(QFont("Courier", 8, QFont.Bold))
            painter.drawText(int(x + 25), int(y), marker.get('title', ''))
        
        painter.end()
        self.image_label.setPixmap(pixmap)
    
    def on_mouse_press(self, event):
        """Mouse press"""
        if self.file_type != 'image':
            return
        
        pos = event.pos()
        
        # Check if clicked on marker
        for i, marker in enumerate(self.markers):
            mx = marker.get('position', {}).get('x', 0)
            my = marker.get('position', {}).get('y', 0)
            
            dist = math.sqrt((pos.x() - mx)**2 + (pos.y() - my)**2)
            if dist < 30:
                self.dragging_marker = i
                self.dragging_pos = pos
                return
        
        # Create new marker
        marker = {
            'title': 'Marker',
            'description': '',
            'position': {'x': pos.x(), 'y': pos.y()}
        }
        self.markers.append(marker)
        self.update_image_display()
    
    def on_mouse_move(self, event):
        """Mouse move - drag markers"""
        if self.dragging_marker is not None and self.file_type == 'image':
            pos = event.pos()
            marker = self.markers[self.dragging_marker]
            marker['position']['x'] = pos.x()
            marker['position']['y'] = pos.y()
            self.update_image_display()
    
    def on_mouse_release(self, event):
        """Mouse release"""
        self.dragging_marker = None
    
    def on_wheel(self, event):
        """Mouse wheel - zoom for 3D"""
        if self.file_type == '3d':
            delta = event.angleDelta().y()
            self.zoom += delta / 1000.0
            self.zoom = max(0.1, min(self.zoom, 10.0))
    
    def toggle_planner(self):
        """Toggle planner mode"""
        self.planner_mode = not self.planner_mode
        if self.planner_mode:
            self.image_label.setText("VIEW PLANNER ENABLED\n\nDrag markers on images\nRotate 3D models with arrow keys\n\nPress again to disable")
        else:
            if self.file_type == 'image':
                self.load_image(str(self.current_file))
            else:
                self.load_3d(str(self.current_file))
    
    def get_marker_position(self):
        """Get position of last marker"""
        if self.markers:
            return self.markers[-1]['position']
        return {'x': 0, 'y': 0}
