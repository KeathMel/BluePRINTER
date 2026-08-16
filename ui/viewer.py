from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QColor, QPainter, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QRect
import math

class ViewerWidget(QWidget):
    marker_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_project = None
        self.file_type = None
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.original_pixmap = None
        self.display_pixmap = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.pixmap_rect = QRect()
        
        self.viewer_label = QLabel()
        self.viewer_label.setAlignment(Qt.AlignCenter)
        self.viewer_label.setStyleSheet("background-color: #F0F0F0;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewer_label)
        self.setStyleSheet("background-color: #F0F0F0;")
        
        self.setMouseTracking(True)
        self.viewer_label.mouseMoveEvent = self.on_mouse_move
        self.viewer_label.mousePressEvent = self.on_mouse_press
        self.viewer_label.mouseReleaseEvent = self.on_mouse_release
        self.viewer_label.contextMenuEvent = self.on_right_click
    
    def load_file(self, file_path, project=None):
        self.current_file = Path(file_path)
        self.current_project = project
        ext = self.current_file.suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            self.load_image(file_path)
            self.file_type = 'image'
        else:
            self.viewer_label.setText(f"Unsupported: {ext}")
    
    def load_image(self, file_path):
        pixmap = QPixmap(str(file_path))
        if pixmap.isNull():
            self.viewer_label.setText("Failed to load image")
            return
        
        self.original_pixmap = pixmap
        scaled = pixmap.scaledToWidth(900, Qt.SmoothTransformation)
        self.display_pixmap = scaled
        
        self.scale_x = self.original_pixmap.width() / self.display_pixmap.width()
        self.scale_y = self.original_pixmap.height() / self.display_pixmap.height()
        
        self.refresh_display()
    
    def refresh_display(self):
        print(f"[DEBUG] refresh_display called, display_pixmap={self.display_pixmap is not None}")
        if not self.display_pixmap:
            print("[ERROR] No display pixmap!")
            return
        
        pixmap = self.display_pixmap.copy()
        painter = QPainter(pixmap)
        
        for marker in self.markers:
            orig_x = marker.get('position', {}).get('x', 0)
            orig_y = marker.get('position', {}).get('y', 0)
            scale = marker.get('scale', 1.0)
            
            x = orig_x / self.scale_x
            y = orig_y / self.scale_y
            marker_size = int(15 * scale)
            
            painter.setPen(QPen(QColor(232, 17, 35), 2))
            painter.setBrush(QBrush(QColor(232, 17, 35, 150)))
            painter.drawEllipse(int(x - marker_size), int(y - marker_size), marker_size * 2, marker_size * 2)
            
            painter.setPen(QColor(232, 17, 35))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(int(x + marker_size + 5), int(y), marker.get('title', ''))
        
        painter.end()
        self.viewer_label.setPixmap(pixmap)
        
        pm = self.viewer_label.pixmap()
        if pm:
            label_rect = self.viewer_label.rect()
            pm_width = pm.width()
            pm_height = pm.height()
            x_offset = (label_rect.width() - pm_width) / 2
            y_offset = (label_rect.height() - pm_height) / 2
            self.pixmap_rect = QRect(int(x_offset), int(y_offset), pm_width, pm_height)
    
    def screen_to_image_coords(self, screen_x, screen_y):
        pm_x = screen_x - self.pixmap_rect.x()
        pm_y = screen_y - self.pixmap_rect.y()
        
        orig_x = pm_x * self.scale_x
        orig_y = pm_y * self.scale_y
        
        return orig_x, orig_y
    
    def set_markers(self, markers):
        self.markers = markers
        self.refresh_display()
    
    def on_mouse_press(self, event):
        if self.file_type != 'image' or not self.display_pixmap:
            return
        
        orig_x, orig_y = self.screen_to_image_coords(event.pos().x(), event.pos().y())
        
        # Check from newest to oldest marker
        for marker in reversed(self.markers):
            mx = marker.get('position', {}).get('x', 0)
            my = marker.get('position', {}).get('y', 0)
            
            dist = math.sqrt((orig_x - mx)**2 + (orig_y - my)**2)
            if dist < 50 * self.scale_x:
                self.selected_marker = marker
                self.dragging = True
                self.marker_selected.emit(marker)
                return
    
    def on_right_click(self, event):
        if self.file_type != 'image' or not self.display_pixmap:
            return
        
        orig_x, orig_y = self.screen_to_image_coords(event.pos().x(), event.pos().y())
        
        marker = {
            'title': 'Marker',
            'description': '',
            'position': {'x': orig_x, 'y': orig_y},
            'scale': 1.0
        }
        self.markers.append(marker)
        self.refresh_display()
        self.marker_selected.emit(marker)
    
    def on_mouse_move(self, event):
        if self.dragging and self.selected_marker and self.file_type == 'image':
            orig_x, orig_y = self.screen_to_image_coords(event.pos().x(), event.pos().y())
            
            self.selected_marker['position']['x'] = orig_x
            self.selected_marker['position']['y'] = orig_y
            self.refresh_display()
            self.marker_selected.emit(self.selected_marker)
    
    def on_mouse_release(self, event):
        self.dragging = False
    
    def clear(self):
        self.current_file = None
        self.current_project = None
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.original_pixmap = None
        self.display_pixmap = None
        self.file_type = None
        self.viewer_label.setText("")
        self.viewer_label.setPixmap(QPixmap())
