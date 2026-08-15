from pathlib import Path
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

try:
    import trimesh
except:
    trimesh = None

class Viewer3D(QOpenGLWidget):
    marker_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.markers = []
        self.model = None
        self.model_vertices = None
        self.model_faces = None
        self.camera_rot_x = 20
        self.camera_rot_y = 45
        self.camera_zoom = 50
        
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        self.setFormat(fmt)
        
        self.setMouseTracking(True)
        self.last_x = 0
        self.last_y = 0
    
    def initializeGL(self):
        glClearColor(0.039, 0.055, 0.153, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        light_pos = [5, 5, 5, 0]
        glLight(GL_LIGHT0, GL_POSITION, light_pos)
    
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
        
        if self.model_vertices is not None:
            self.draw_model()
        else:
            self.draw_default_cube()
        
        # Draw markers as SMALL 3D balls
        glColor3f(0, 0.85, 1)
        for marker in self.markers:
            x = marker.get('position', {}).get('x', 0)
            y = marker.get('position', {}).get('y', 0)
            z = marker.get('position', {}).get('z', 0)
            
            glPushMatrix()
            glTranslatef(x, y, z)
            quad = gluNewQuadric()
            gluSphere(quad, 0.2, 6, 6)  # Smaller size
            glPopMatrix()
    
    def draw_model(self):
        if self.model_vertices is None or self.model_faces is None:
            return
        
        glColor3f(0.2, 0.8, 1)
        glBegin(GL_TRIANGLES)
        
        for face in self.model_faces:
            for vertex_idx in face:
                if vertex_idx < len(self.model_vertices):
                    v = self.model_vertices[vertex_idx]
                    glVertex3f(v[0], v[1], v[2])
        
        glEnd()
    
    def draw_default_cube(self):
        glColor3f(0, 0.85, 1)
        vertices = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        
        glBegin(GL_LINES)
        for edge in edges:
            for vertex_idx in edge:
                glVertex3fv(vertices[vertex_idx])
        glEnd()
    
    def load_file(self, file_path):
        if not trimesh:
            return
        
        try:
            mesh = trimesh.load(str(file_path))
            
            # Handle mesh collections
            if isinstance(mesh, trimesh.Scene):
                mesh = mesh.geometry[next(iter(mesh.geometry))]
            
            # Center and scale model
            mesh.apply_translation(-mesh.centroid)
            
            # Store vertices and faces
            self.model_vertices = np.array(mesh.vertices, dtype=np.float32)
            self.model_faces = np.array(mesh.faces, dtype=np.uint32)
            
            self.update()
        except Exception as e:
            print(f"Error loading 3D model: {e}")
            self.model_vertices = None
            self.model_faces = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            marker = {
                'title': 'Marker',
                'description': '',
                'position': {'x': 0, 'y': 0, 'z': 0}
            }
            self.markers.append(marker)
            self.marker_selected.emit(marker)
        
        self.last_x = event.x()
        self.last_y = event.y()
    
    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_x
        dy = event.y() - self.last_y
        
        if event.buttons() & Qt.MiddleButton:
            self.camera_rot_y += dx * 0.5
            self.camera_rot_x += dy * 0.5
        
        self.last_x = event.x()
        self.last_y = event.y()
        self.update()
    
    def wheelEvent(self, event):
        self.camera_zoom += event.angleDelta().y() / 120
        self.camera_zoom = max(1, min(self.camera_zoom, 200))
        self.update()
    
    def set_markers(self, markers):
        self.markers = markers
        self.update()
    
    def clear(self):
        self.model = None
        self.model_vertices = None
        self.model_faces = None
        self.markers = []
        self.update()
