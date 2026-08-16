from pathlib import Path
from PyQt5.QtWidgets import QOpenGLWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

# Monkey-patch pkgutil for Python 3.14 trimesh compatibility
import pkgutil
if not hasattr(pkgutil, 'find_loader'):
    def find_loader(name):
        spec = __import__('importlib.util').util.find_spec(name)
        return spec.loader if spec else None
    pkgutil.find_loader = find_loader

try:
    import trimesh
    HAS_TRIMESH = True
except:
    HAS_TRIMESH = False

class Viewer3D(QWidget):
    marker_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    # All marker state lives on the canvas - these delegate to it
    @property
    def markers(self):
        return self.gl_widget.markers
    
    @markers.setter
    def markers(self, value):
        self.gl_widget.markers = value
    
    @property
    def selected_marker(self):
        return self.gl_widget.selected_marker
    
    @selected_marker.setter
    def selected_marker(self, value):
        self.gl_widget.selected_marker = value
    
    @property
    def dragging(self):
        return self.gl_widget.dragging
    
    @dragging.setter
    def dragging(self, value):
        self.gl_widget.dragging = value
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # OpenGL canvas
        self.gl_widget = GL3DCanvas()
        self.gl_widget.marker_selected.connect(self.on_marker_selected)
        layout.addWidget(self.gl_widget)
        
        # Scale slider at bottom (initially hidden)
        scale_container = QWidget()
        scale_layout = QHBoxLayout(scale_container)
        scale_layout.setContentsMargins(5, 5, 5, 5)
        scale_layout.addWidget(QLabel("Model Size:"))
        
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(50)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setValue(100)
        self.scale_slider.setMaximumWidth(200)
        self.scale_slider.sliderMoved.connect(self.on_model_scale_changed)
        scale_layout.addWidget(self.scale_slider)
        
        scale_label = QLabel("100%")
        self.scale_slider.valueChanged.connect(lambda v: scale_label.setText(f"{v}%"))
        scale_layout.addWidget(scale_label)
        scale_layout.addStretch()
        
        scale_container.setStyleSheet("background-color: #F0F0F0;")
        scale_container.setVisible(False)
        self.scale_container = scale_container
        layout.addWidget(scale_container)
    
    def show_scale_slider(self):
        self.scale_container.setVisible(True)
    
    def hide_scale_slider(self):
        self.scale_container.setVisible(False)
    
    def on_model_scale_changed(self, value):
        self.gl_widget.set_model_display_scale(value)
    
    def on_marker_selected(self, marker):
        self.marker_selected.emit(marker)
    
    def load_file(self, file_path):
        self.gl_widget.load_file(file_path)
        self.show_scale_slider()
    
    def set_markers(self, markers):
        self.gl_widget.set_markers(markers)
    
    def clear(self):
        self.gl_widget.clear()
        self.hide_scale_slider()
    
    def update(self):
        self.gl_widget.update()

class GL3DCanvas(QOpenGLWidget):
    marker_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.model_vertices = None
        self.model_faces = None
        self.model_display_scale = 1.0
        self.camera_rot_x = 20
        self.camera_rot_y = 45
        self.camera_zoom = 60
        
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        self.setFormat(fmt)
        
        self.setMouseTracking(True)
        self.last_x = 0
        self.last_y = 0
    
    def initializeGL(self):
        glClearColor(0.239, 0.239, 0.239, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
    
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h else 1, 0.1, 500)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glTranslatef(0, 0, -self.camera_zoom)
        glRotatef(self.camera_rot_x, 1, 0, 0)
        glRotatef(self.camera_rot_y, 0, 1, 0)
        glScalef(self.model_display_scale, self.model_display_scale, self.model_display_scale)
        
        if self.model_vertices is not None:
            self.draw_model()
        
        # Draw markers
        glColor3f(0.9, 0.07, 0.14)
        for marker in self.markers:
            x = marker.get('position', {}).get('x', 0)
            y = marker.get('position', {}).get('y', 0)
            z = marker.get('position', {}).get('z', 0)
            scale = marker.get('scale', 1.0)
            
            glPushMatrix()
            glTranslatef(x, y, z)
            quad = gluNewQuadric()
            gluSphere(quad, 0.15 * scale, 8, 8)
            glPopMatrix()
    
    def draw_model(self):
        glLineWidth(1.2)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_LINES)
        
        drawn_edges = set()
        for face in self.model_faces:
            try:
                for i in range(len(face)):
                    v1_idx = int(face[i])
                    v2_idx = int(face[(i+1) % len(face)])
                    edge = tuple(sorted([v1_idx, v2_idx]))
                    
                    if edge not in drawn_edges:
                        drawn_edges.add(edge)
                        v1 = self.model_vertices[v1_idx]
                        v2 = self.model_vertices[v2_idx]
                        glVertex3f(float(v1[0]), float(v1[1]), float(v1[2]))
                        glVertex3f(float(v2[0]), float(v2[1]), float(v2[2]))
            except:
                pass
        
        glEnd()
        glLineWidth(1.0)
    
    def load_file(self, file_path):
        if not HAS_TRIMESH:
            return
        
        try:
            mesh = trimesh.load(str(file_path))
            
            if isinstance(mesh, trimesh.Scene):
                meshes = list(mesh.geometry.values())
                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
            elif isinstance(mesh, list):
                mesh = trimesh.util.concatenate(mesh)
            
            mesh.apply_translation(-mesh.centroid)
            bounds = mesh.bounds
            if (bounds[1] - bounds[0]).max() > 0:
                scale = 500.0 / (bounds[1] - bounds[0]).max()
                mesh.apply_scale(scale)
            
            self.model_vertices = np.array(mesh.vertices, dtype=np.float32)
            self.model_faces = np.array(mesh.faces, dtype=np.uint32)
            self.model_display_scale = 1.0
            self.update()
        except:
            pass
    
    def set_model_display_scale(self, scale):
        self.model_display_scale = scale / 100.0
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            marker = {
                'title': 'Marker',
                'description': '',
                'position': {'x': 0, 'y': 0, 'z': 0},
                'scale': 1.0
            }
            self.markers.append(marker)
            self.selected_marker = marker
            self.marker_selected.emit(marker)
        elif event.button() == Qt.LeftButton:
            if self.markers:
                for marker in reversed(self.markers):
                    self.selected_marker = marker
                    self.dragging = True
                    self.marker_selected.emit(marker)
                    break
            else:
                self.selected_marker = None
                self.dragging = False
        
        self.last_x = event.x()
        self.last_y = event.y()
    
    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_x
        dy = event.y() - self.last_y
        
        if event.buttons() & Qt.MiddleButton:
            self.camera_rot_y += dx * 0.5
            self.camera_rot_x += dy * 0.5
        elif event.buttons() & Qt.LeftButton and self.dragging and self.selected_marker:
            # Move marker in the camera's screen plane so it follows the cursor
            # regardless of how the camera is rotated.
            speed = 0.01 * self.camera_zoom / self.model_display_scale
            
            rx = np.radians(self.camera_rot_x)
            ry = np.radians(self.camera_rot_y)
            
            # Camera "right" vector in world space (screen X drag)
            right = np.array([np.cos(ry), 0, -np.sin(ry)])
            # Camera "up" vector in world space (screen Y drag)
            up = np.array([
                np.sin(ry) * np.sin(rx),
                np.cos(rx),
                np.cos(ry) * np.sin(rx),
            ])
            
            move = right * (dx * speed) - up * (dy * speed)
            
            self.selected_marker['position']['x'] += float(move[0])
            self.selected_marker['position']['y'] += float(move[1])
            self.selected_marker['position']['z'] += float(move[2])
        
        self.last_x = event.x()
        self.last_y = event.y()
        self.update()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def wheelEvent(self, event):
        self.camera_zoom += event.angleDelta().y() / 120
        self.camera_zoom = max(1, min(self.camera_zoom, 200))
        self.update()
    
    def set_markers(self, markers):
        self.markers = markers
        self.update()
    
    def clear(self):
        self.model_vertices = None
        self.model_faces = None
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.update()
