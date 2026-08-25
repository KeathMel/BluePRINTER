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
        self.drag_depth = 0.5
        self.model_vertices = None
        self.model_faces = None
        self.vertex_shades = None
        self.vertex_normals = None
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
        # Solid triangles with smooth per-vertex shading
        if self.model_faces is None or self.vertex_shades is None:
            return
        glBegin(GL_TRIANGLES)
        for face in self.model_faces:
            for idx in (int(face[0]), int(face[1]), int(face[2])):
                s = self.vertex_shades[idx]
                glColor3f(s, s, s)
                vtx = self.model_vertices[idx]
                glVertex3f(float(vtx[0]), float(vtx[1]), float(vtx[2]))
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
            
            # Center and scale using the true bounding box. Works correctly for
            # any shape, including long/thin models (swords, rods, blueprints).
            bmin = verts.min(axis=0)
            bmax = verts.max(axis=0)
            center = (bmin + bmax) / 2.0
            verts = verts - center
            extent = float(np.max(bmax - bmin))
            if extent <= 0:
                extent = 1.0
            verts = verts * (5.0 / extent)
            
            self.model_vertices = verts
            self.model_faces = faces
            self.model_display_scale = 1.0
            
            # SMOOTH per-vertex shading (like Blender's smooth shading) so curved
            # surfaces read as curved instead of faceted.
            v = self.model_vertices
            f = self.model_faces
            v0 = v[f[:, 0]]
            v1 = v[f[:, 1]]
            v2 = v[f[:, 2]]
            
            # Face normals (weighted by area via the un-normalized cross product)
            face_normals = np.cross(v1 - v0, v2 - v0)
            
            # Accumulate face normals onto each vertex, then normalize -> smooth normals
            vertex_normals = np.zeros_like(v)
            np.add.at(vertex_normals, f[:, 0], face_normals)
            np.add.at(vertex_normals, f[:, 1], face_normals)
            np.add.at(vertex_normals, f[:, 2], face_normals)
            vn_len = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
            vn_len[vn_len == 0] = 1
            vertex_normals = vertex_normals / vn_len
            self.vertex_normals = vertex_normals.astype(np.float32)
            
            # Per-vertex brightness from a directional light + ambient floor.
            # No abs(): back-facing areas genuinely fall into shadow, giving form.
            light = np.array([0.4, 0.8, 0.6])
            light = light / np.linalg.norm(light)
            diffuse = np.clip(vertex_normals @ light, 0.0, 1.0)
            ambient = 0.35
            self.vertex_shades = (ambient + (1.0 - ambient) * diffuse).astype(np.float32)
            
            print(f"[3D] Loaded: {len(self.model_vertices)} verts, {len(self.model_faces)} faces, extent={extent:.3f}")
            self.update()
        except Exception as e:
            import traceback
            print(f"[3D] LOAD ERROR: {e}")
            traceback.print_exc()
    
    def set_model_display_scale(self, scale):
        self.model_display_scale = scale / 100.0
        self.update()
    
    def _camera_matrices(self):
        """Build modelview (M), projection (P), viewport as numpy - matching paintGL."""
        w = max(1, self.width())
        h = max(1, self.height())

        # Modelview: translate then rotX then rotY then scale (same order as paintGL)
        def translate(tx, ty, tz):
            m = np.eye(4)
            m[0, 3] = tx; m[1, 3] = ty; m[2, 3] = tz
            return m
        def rot_x(a):
            c, s = np.cos(a), np.sin(a)
            return np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]], dtype=float)
        def rot_y(a):
            c, s = np.cos(a), np.sin(a)
            return np.array([[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]], dtype=float)
        def scale(sv):
            m = np.eye(4)
            m[0,0] = m[1,1] = m[2,2] = sv
            return m

        M = translate(0, 0, -self.camera_zoom)
        M = M @ rot_x(np.radians(self.camera_rot_x))
        M = M @ rot_y(np.radians(self.camera_rot_y))
        M = M @ scale(self.model_display_scale)

        # Projection: gluPerspective(45, aspect, 0.1, 1000)
        fov = np.radians(45.0)
        aspect = w / h
        near, far = 0.1, 1000.0
        f = 1.0 / np.tan(fov / 2.0)
        P = np.zeros((4, 4))
        P[0, 0] = f / aspect
        P[1, 1] = f
        P[2, 2] = (far + near) / (near - far)
        P[2, 3] = (2 * far * near) / (near - far)
        P[3, 2] = -1.0

        return M, P, w, h

    def project_to_screen(self, x, y, z):
        """World point -> (screen_x_topdown, screen_y_topdown, ndc_depth)."""
        M, P, w, h = self._camera_matrices()
        clip = P @ M @ np.array([x, y, z, 1.0])
        if abs(clip[3]) < 1e-9:
            return None
        ndc = clip[:3] / clip[3]
        sx = (ndc[0] * 0.5 + 0.5) * w
        sy = (ndc[1] * 0.5 + 0.5) * h
        # ndc[1] is bottom-up; convert to Qt top-down
        return sx, h - sy, ndc[2]

    def marker_screen_pos(self, x, y, z):
        return self.project_to_screen(x, y, z)

    def marker_at_screen(self, click_x, click_y):
        best = None
        best_dist = 24.0
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
        return best

    def unproject_at_depth(self, screen_x, screen_y, depth):
        """Screen point + ndc depth -> world point (inverse of project_to_screen)."""
        M, P, w, h = self._camera_matrices()
        # Convert Qt top-down screen coords back to NDC
        ndc_x = (screen_x / w) * 2.0 - 1.0
        ndc_y = ((h - screen_y) / h) * 2.0 - 1.0
        ndc = np.array([ndc_x, ndc_y, depth, 1.0])
        try:
            inv = np.linalg.inv(P @ M)
        except np.linalg.LinAlgError:
            return None
        world = inv @ ndc
        if abs(world[3]) < 1e-9:
            return None
        return world[:3] / world[3]

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
                # Capture the marker's screen depth so we can unproject the
                # cursor to the same depth while dragging (marker sticks to mouse)
                p = hit.get('position', {})
                screen = self.marker_screen_pos(p.get('x', 0), p.get('y', 0), p.get('z', 0))
                self.drag_depth = screen[2] if screen else 0.5
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
            # Unproject the cursor at the marker's captured screen depth so the
            # marker sticks exactly under the mouse.
            world = self.unproject_at_depth(event.x(), event.y(), self.drag_depth)
            if world is not None:
                self.selected_marker['position']['x'] = float(world[0])
                self.selected_marker['position']['y'] = float(world[1])
                self.selected_marker['position']['z'] = float(world[2])
        
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
        self.vertex_shades = None
        self.vertex_normals = None
        self.markers = []
        self.selected_marker = None
        self.dragging = False
        self.update()
