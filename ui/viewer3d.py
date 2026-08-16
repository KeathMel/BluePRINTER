from pathlib import Path
from PyQt5.QtWidgets import QOpenGLWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QWidget, QSizePolicy
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
    marker_moved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
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
        layout.setSpacing(0)
        
        # OpenGL canvas - fills all available space
        self.gl_widget = GL3DCanvas()
        self.gl_widget.marker_selected.connect(self.on_marker_selected)
        self.gl_widget.marker_moved.connect(self.marker_moved.emit)
        layout.addWidget(self.gl_widget, 1)
        
        # Scale slider bar at bottom of canvas (initially hidden)
        scale_container = QWidget()
        scale_container.setMaximumHeight(40)
        scale_layout = QHBoxLayout(scale_container)
        scale_layout.setContentsMargins(8, 4, 8, 4)
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
        layout.addWidget(scale_container, 0)
    
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
    marker_moved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.model_vertices = None
        self.model_faces = None
        self.face_shades = None
        self.model_display_scale = 1.0
        self.camera_rot_x = 20
        self.camera_rot_y = 45
        self.camera_zoom = 12
        
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        self.setFormat(fmt)
        
        self.setMouseTracking(True)
        self.last_x = 0
        self.last_y = 0
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def initializeGL(self):
        glClearColor(0.239, 0.239, 0.239, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
    
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h else 1, 0.1, 1000)
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
        
        # Draw markers ALWAYS ON TOP - disable depth test so they're never
        # hidden inside the model, and make them big enough to see.
        glDisable(GL_DEPTH_TEST)
        glColor3f(0.933, 0.067, 0.067)  # Metro red #ee1111
        for marker in self.markers:
            x = marker.get('position', {}).get('x', 0)
            y = marker.get('position', {}).get('y', 0)
            z = marker.get('position', {}).get('z', 0)
            scale = marker.get('scale', 1.0)
            
            glPushMatrix()
            glTranslatef(x, y, z)
            quad = gluNewQuadric()
            gluSphere(quad, 0.25 * scale, 12, 12)
            glPopMatrix()
        glEnable(GL_DEPTH_TEST)
    
    def draw_model(self):
        # Solid filled triangles with precomputed shading
        if self.model_faces is None or self.face_shades is None:
            return
        glBegin(GL_TRIANGLES)
        for i, face in enumerate(self.model_faces):
            shade = self.face_shades[i]
            glColor3f(shade, shade, shade)
            v0 = self.model_vertices[int(face[0])]
            v1 = self.model_vertices[int(face[1])]
            v2 = self.model_vertices[int(face[2])]
            glVertex3f(float(v0[0]), float(v0[1]), float(v0[2]))
            glVertex3f(float(v1[0]), float(v1[1]), float(v1[2]))
            glVertex3f(float(v2[0]), float(v2[1]), float(v2[2]))
        glEnd()
    
    def load_file(self, file_path):
        if not HAS_TRIMESH:
            print("[3D] trimesh not available")
            return
        
        try:
            mesh = trimesh.load(str(file_path))
            
            if isinstance(mesh, trimesh.Scene):
                meshes = list(mesh.geometry.values())
                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
            elif isinstance(mesh, list):
                mesh = trimesh.util.concatenate(mesh)
            
            verts = np.array(mesh.vertices, dtype=np.float32)
            faces = np.array(mesh.faces, dtype=np.uint32)
            
            # Center on the median vertex (robust to outliers)
            center = np.median(verts, axis=0)
            verts = verts - center
            
            # Find the robust extent (2nd..98th percentile) to define what
            # "inside the real model" means, ignoring stray outlier vertices.
            lo = np.percentile(verts, 2, axis=0)
            hi = np.percentile(verts, 98, axis=0)
            extent = float(np.max(hi - lo))
            if extent <= 0:
                extent = 1.0
            
            # Mark vertices that sit far outside the real cluster as outliers.
            # Anything beyond 3x the robust extent from center is junk geometry.
            limit = extent * 3.0
            dist_from_center = np.linalg.norm(verts, axis=1)
            good_vertex = dist_from_center <= limit
            
            # Keep only faces whose ALL three vertices are good - this drops
            # the giant "wall" triangles that connect to outlier vertices.
            face_ok = good_vertex[faces[:, 0]] & good_vertex[faces[:, 1]] & good_vertex[faces[:, 2]]
            faces = faces[face_ok]
            
            # Scale the real model to 5 units
            verts = verts * (5.0 / extent)
            
            self.model_vertices = verts
            self.model_faces = faces
            self.model_display_scale = 1.0
            
            # Precompute flat shading per face (vectorized)
            v = self.model_vertices
            f = self.model_faces
            v0 = v[f[:, 0]]
            v1 = v[f[:, 1]]
            v2 = v[f[:, 2]]
            normals = np.cross(v1 - v0, v2 - v0)
            lengths = np.linalg.norm(normals, axis=1, keepdims=True)
            lengths[lengths == 0] = 1
            normals = normals / lengths
            light = np.array([0.3, 0.7, 0.5])
            light = light / np.linalg.norm(light)
            shades = np.abs(normals @ light)
            self.face_shades = (0.35 + 0.65 * shades).astype(np.float32)
            
            dropped = int((~face_ok).sum())
            print(f"[3D] Loaded: {len(self.model_vertices)} verts, {len(self.model_faces)} faces, dropped {dropped} outlier faces, extent={extent:.3f}")
            self.update()
        except Exception as e:
            import traceback
            print(f"[3D] LOAD ERROR: {e}")
            traceback.print_exc()
    
    def set_model_display_scale(self, scale):
        self.model_display_scale = scale / 100.0
        self.update()
    
    def project_to_screen(self, x, y, z):
        """Project a 3D world point to 2D screen coords using current matrices."""
        try:
            modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            sx, sy, sz = gluProject(x, y, z, modelview, projection, viewport)
            # OpenGL y is bottom-up; Qt y is top-down
            return sx, viewport[3] - sy, sz
        except Exception:
            return None

    def marker_at_screen(self, click_x, click_y):
        """Return the marker whose projected screen position is nearest the
        click within a pixel threshold, or None."""
        self.makeCurrent()
        # Re-run the same camera transform used in paintGL so projection matches
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0, 0, -self.camera_zoom)
        glRotatef(self.camera_rot_x, 1, 0, 0)
        glRotatef(self.camera_rot_y, 0, 1, 0)
        glScalef(self.model_display_scale, self.model_display_scale, self.model_display_scale)

        best = None
        best_dist = 24.0  # pixel radius for a hit
        for marker in self.markers:
            p = marker.get('position', {})
            screen = self.project_to_screen(p.get('x', 0), p.get('y', 0), p.get('z', 0))
            if screen is None:
                continue
            sx, sy, sz = screen
            d = ((sx - click_x) ** 2 + (sy - click_y) ** 2) ** 0.5
            if d < best_dist:
                best_dist = d
                best = marker

        glPopMatrix()
        return best

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            marker = {
                'title': 'Marker',
                'description': '',
                'position': {'x': 0, 'y': 0, 'z': 3.0},
                'scale': 1.0
            }
            self.markers.append(marker)
            self.selected_marker = marker
            self.marker_selected.emit(marker)
            self.update()
        elif event.button() == Qt.LeftButton:
            # Pick the actual marker under the cursor
            hit = self.marker_at_screen(event.x(), event.y())
            if hit is not None:
                self.selected_marker = hit
                self.dragging = True
                self.marker_selected.emit(hit)
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
            # regardless of how the camera is rotated. Derived from the inverse
            # of the view rotation (Rx * Ry), so screen X/Y map to world space.
            speed = 0.005 * self.camera_zoom / self.model_display_scale
            
            rx = np.radians(self.camera_rot_x)
            ry = np.radians(self.camera_rot_y)
            cx, sx = np.cos(rx), np.sin(rx)
            cy, sy = np.cos(ry), np.sin(ry)
            
            # (Rx @ Ry)^T columns give world-space screen-right and screen-up
            right = np.array([cy, 0.0, sy])
            up = np.array([sx * sy, cx, -sx * cy])
            
            move = right * (dx * speed) - up * (dy * speed)
            
            self.selected_marker['position']['x'] += float(move[0])
            self.selected_marker['position']['y'] += float(move[1])
            self.selected_marker['position']['z'] += float(move[2])
        
        self.last_x = event.x()
        self.last_y = event.y()
        self.update()
    
    def mouseReleaseEvent(self, event):
        was_dragging = self.dragging
        self.dragging = False
        if was_dragging and self.selected_marker is not None:
            self.marker_moved.emit()
    
    def wheelEvent(self, event):
        self.camera_zoom += event.angleDelta().y() / 120
        self.camera_zoom = max(2, min(self.camera_zoom, 100))
        self.update()
    
    def set_markers(self, markers):
        self.markers = markers
        self.update()
    
    def clear(self):
        self.model_vertices = None
        self.model_faces = None
        self.face_shades = None
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.update()
