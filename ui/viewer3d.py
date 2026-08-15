from pathlib import Path
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math

try:
    import trimesh
except:
    trimesh = None

class Viewer3D(QOpenGLWidget):
    marker_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.markers = []
        self.dragging_marker = None
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
        
        if self.model_vertices is not None and self.model_faces is not None:
            self.draw_model()
        
        # Draw markers as small 3D balls
        glColor3f(0, 0.85, 1)
        for marker in self.markers:
            x = marker.get('position', {}).get('x', 0)
            y = marker.get('position', {}).get('y', 0)
            z = marker.get('position', {}).get('z', 0)
            
            glPushMatrix()
            glTranslatef(x, y, z)
            quad = gluNewQuadric()
            gluSphere(quad, 0.15, 6, 6)
            glPopMatrix()
    
    def draw_model(self):
        if self.model_vertices is None or self.model_faces is None:
            return
        
        glColor3f(0.2, 0.8, 1)
        glBegin(GL_TRIANGLES)
        
        for face in self.model_faces:
            try:
                for vertex_idx in face:
                    v = self.model_vertices[vertex_idx]
                    glVertex3f(float(v[0]), float(v[1]), float(v[2]))
            except:
                pass
        
        glEnd()
    
    def load_file(self, file_path):
        if not trimesh:
            return
        
        try:
            print(f"Loading 3D model: {file_path}")
            mesh = trimesh.load(str(file_path))
            print(f"Loaded mesh type: {type(mesh)}")
            
            # Handle different mesh types
            if isinstance(mesh, trimesh.Scene):
                print("Mesh is Scene, extracting geometry")
                meshes = list(mesh.geometry.values())
                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
            elif isinstance(mesh, list):
                print("Mesh is list, concatenating")
                mesh = trimesh.util.concatenate(mesh)
            
            print(f"Mesh vertices: {mesh.vertices.shape}, faces: {mesh.faces.shape}")
            
            # Center and normalize
            mesh.apply_translation(-mesh.centroid)
            bounds = mesh.bounds
            scale = 10.0 / (bounds[1] - bounds[0]).max()
            mesh.apply_scale(scale)
            
            # Store data
            self.model_vertices = np.array(mesh.vertices, dtype=np.float32)
            self.model_faces = np.array(mesh.faces, dtype=np.uint32)
            
            print(f"Successfully loaded 3D model")
            self.update()
        except Exception as e:
            print(f"Error loading 3D model: {e}")
            import traceback
            traceback.print_exc()
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
            self.dragging_marker = marker
        elif event.button() == Qt.LeftButton:
            # Check if clicking marker
            for marker in self.markers:
                mx = marker.get('position', {}).get('x', 0)
                my = marker.get('position', {}).get('y', 0)
                mz = marker.get('position', {}).get('z', 0)
                # Simple distance check in screen space
                self.dragging_marker = marker
                self.marker_selected.emit(marker)
                break
        
        self.last_x = event.x()
        self.last_y = event.y()
    
    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_x
        dy = event.y() - self.last_y
        
        if event.buttons() & Qt.MiddleButton:
            self.camera_rot_y += dx * 0.5
            self.camera_rot_x += dy * 0.5
        elif event.buttons() & Qt.LeftButton and self.dragging_marker:
            # Move marker in 3D space
            self.dragging_marker['position']['x'] += dx * 0.1
            self.dragging_marker['position']['y'] -= dy * 0.1
        
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
        self.model_vertices = None
        self.model_faces = None
        self.markers = []
        self.dragging_marker = None
        self.update()
