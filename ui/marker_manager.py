import json
from pathlib import Path

class MarkerManager:
    def __init__(self, project, current_file):
        self.project = project
        self.current_file = current_file
        self.markers = []
    
    def load_markers(self):
        if not self.current_file or not self.project:
            return []
        
        markers_folder = self.project.path / "markers"
        markers_folder.mkdir(exist_ok=True)
        
        file_hash = self.current_file.name.replace('.', '_')
        json_path = markers_folder / f"{file_hash}.json"
        
        if json_path.exists():
            with open(json_path) as f:
                self.markers = json.load(f)
        else:
            self.markers = []
        
        return self.markers
    
    def save_markers(self):
        if not self.current_file or not self.project:
            return
        
        markers_folder = self.project.path / "markers"
        markers_folder.mkdir(exist_ok=True)
        
        file_hash = self.current_file.name.replace('.', '_')
        json_path = markers_folder / f"{file_hash}.json"
        
        with open(json_path, 'w') as f:
            json.dump(self.markers, f, indent=2)
    
    def add_marker(self, x, y, z=0):
        marker = {
            'title': 'Marker',
            'description': '',
            'position': {'x': x, 'y': y, 'z': z},
            'scale': 1.0
        }
        self.markers.append(marker)
        self.save_markers()
        return marker
    
    def update_marker(self, marker, title=None, desc=None, scale=None):
        if title is not None:
            marker['title'] = title
        if desc is not None:
            marker['description'] = desc
        if scale is not None:
            marker['scale'] = scale
        self.save_markers()
    
    def delete_marker(self, marker):
        try:
            self.markers.remove(marker)
            self.save_markers()
            return True
        except ValueError:
            return False
