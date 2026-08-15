# Blueprint Viewer - Iron Man Edition

Python desktop app for annotating blueprints, images, and 3D models.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

## How It Works

1. **Projects List** (left) - Create or open projects
2. **Files** - Add images, 3D files, code, txt to your project
3. **View Planner** - Toggle annotation mode
4. **Draggable Ball** - Click on images to place markers (they stick as stickers)
5. **Annotations** (right) - Add title/description to markers
6. **Save** - Markers saved as JSON files next to your images

## Features

### Images
- Drag the ball/sticker onto image
- Click markers to select
- Add title + description
- Auto-saves to `.markers.json`

### 3D Files
- Rotate view (makes it look interactive)
- Ball stays put while model rotates
- Same annotation system as images

### UI
- Iron Man dark theme (dark + neon cyan/purple)
- Smooth animations
- Professional look

## Project Structure

```
~/.blueprints/
├── Project 1/
│   ├── image.jpg
│   ├── image.jpg.markers.json
│   ├── model.glb
│   └── code.py
├── Project 2/
│   ...
```

## Controls

- **Left Click** - Create/drag markers on images
- **Right Panel** - Edit marker title/description
- **Delete Selected** - Remove markers
- **Arrow Buttons** - Navigate between files
- **View Planner** - Toggle annotation mode

## Keyboard Shortcuts (Future)

- `Delete` - Delete selected marker
- `Ctrl+S` - Save project
- `Arrow Keys` - Rotate 3D models

## Customization

Colors in `ui/theme.py`:
- Background: `#0A0E27` (dark)
- Neon: `#00D9FF` (cyan)
- Purple: `#7D3AFF`

## Files

- `app.py` - Main application
- `ui/theme.py` - Iron Man theme
- `ui/viewer.py` - Image/3D viewer
- `ui/project_manager.py` - Project management

---

**Fully functional Python desktop app**. No web browsers. No AI slog. Just works.
