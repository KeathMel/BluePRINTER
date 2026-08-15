"""Project management"""

import json
from pathlib import Path

class Project:
    def __init__(self, name, path):
        self.name = name
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
    
    def add_file(self, file_path):
        """Copy file to project"""
        import shutil
        dest = self.path / Path(file_path).name
        shutil.copy(file_path, dest)
    
    def get_files(self):
        """Get all files in project"""
        files = []
        for ext in ['*.jpg', '*.png', '*.jpeg', '*.obj', '*.glb', '*.gltf', '*.txt', '*.py', '*.js', '*.md']:
            files.extend(self.path.glob(ext))
        return sorted(files)

class ProjectManager:
    def __init__(self):
        self.projects_dir = Path.home() / ".blueprints"
        self.projects_dir.mkdir(exist_ok=True)
        self.config_file = self.projects_dir / "projects.json"
    
    def create_project(self, name):
        """Create new project"""
        proj_path = self.projects_dir / name
        proj = Project(name, proj_path)
        self._save_project_index(name)
        return proj
    
    def get_project(self, name):
        """Get project by name"""
        return Project(name, self.projects_dir / name)
    
    def get_projects(self):
        """Get all projects"""
        projects = []
        for d in self.projects_dir.iterdir():
            if d.is_dir() and d.name != ".git":
                projects.append(Project(d.name, d))
        return sorted(projects, key=lambda p: p.name)
    
    def _save_project_index(self, name):
        """Save project to index"""
        projects = []
        if self.config_file.exists():
            with open(self.config_file) as f:
                projects = json.load(f)
        
        if name not in projects:
            projects.append(name)
        
        with open(self.config_file, 'w') as f:
            json.dump(projects, f, indent=2)
