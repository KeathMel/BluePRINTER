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

        self.viewer_label = QLabel()
        self.viewer_label.setAlignment(Qt.AlignCenter)
        self.viewer_label.setStyleSheet("background-color: #F0F0F0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewer_label)
        self.setStyleSheet("background-color: #F0F0F0;")

        # All mouse handling goes through the label
        self.viewer_label.setMouseTracking(True)
        self.viewer_label.mousePressEvent = self.on_mouse_press
        self.viewer_label.mouseMoveEvent = self.on_mouse_move
        self.viewer_label.mouseReleaseEvent = self.on_mouse_release

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
        self.display_pixmap = pixmap.scaledToWidth(900, Qt.SmoothTransformation)
        self.scale_x = self.original_pixmap.width() / self.display_pixmap.width()
        self.scale_y = self.original_pixmap.height() / self.display_pixmap.height()
        self.refresh_display()

    def refresh_display(self):
        if not self.display_pixmap:
            return
        pixmap = self.display_pixmap.copy()
        painter = QPainter(pixmap)
        for marker in self.markers:
            ox = marker['position']['x']
            oy = marker['position']['y']
            scale = marker.get('scale', 1.0)
            x = ox / self.scale_x
            y = oy / self.scale_y
            r = int(15 * scale)
            painter.setPen(QPen(QColor(232, 17, 35), 2))
            painter.setBrush(QBrush(QColor(232, 17, 35, 150)))
            painter.drawEllipse(int(x - r), int(y - r), r * 2, r * 2)
            painter.setPen(QColor(232, 17, 35))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(int(x + r + 5), int(y), marker.get('title', ''))
        painter.end()
        self.viewer_label.setPixmap(pixmap)

    def screen_to_image_coords(self, sx, sy):
        # Compute the pixmap's offset within the label LIVE, so it's always
        # correct even right after load before layout settles.
        pm = self.viewer_label.pixmap()
        if pm and not pm.isNull():
            lr = self.viewer_label.rect()
            xo = (lr.width() - pm.width()) / 2
            yo = (lr.height() - pm.height()) / 2
        else:
            xo, yo = 0, 0
        px = sx - xo
        py = sy - yo
        return px * self.scale_x, py * self.scale_y

    def find_marker_at(self, ox, oy):
        # Return the topmost marker within its own visual radius, else None
        for marker in reversed(self.markers):
            mx = marker['position']['x']
            my = marker['position']['y']
            r = 15 * marker.get('scale', 1.0) * self.scale_x + 10 * self.scale_x
            if math.sqrt((ox - mx) ** 2 + (oy - my) ** 2) <= r:
                return marker
        return None

    def set_markers(self, markers):
        self.markers = markers
        self.selected_marker = None
        self.dragging = False
        self.refresh_display()

    def on_mouse_press(self, event):
        if self.file_type != 'image' or not self.display_pixmap:
            return

        ox, oy = self.screen_to_image_coords(event.pos().x(), event.pos().y())

        if event.button() == Qt.RightButton:
            # Create a new marker and select it
            marker = {
                'title': 'Marker',
                'description': '',
                'position': {'x': ox, 'y': oy},
                'scale': 1.0,
            }
            self.markers.append(marker)
            self.selected_marker = marker
            self.dragging = False
            self.refresh_display()
            self.marker_selected.emit(marker)
            return

        if event.button() == Qt.LeftButton:
            hit = self.find_marker_at(ox, oy)
            if hit is not None:
                self.selected_marker = hit
                self.dragging = True
                self.marker_selected.emit(hit)
            else:
                self.selected_marker = None
                self.dragging = False

    def on_mouse_move(self, event):
        if self.dragging and self.selected_marker and self.file_type == 'image':
            ox, oy = self.screen_to_image_coords(event.pos().x(), event.pos().y())
            self.selected_marker['position']['x'] = ox
            self.selected_marker['position']['y'] = oy
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
