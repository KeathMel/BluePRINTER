#!/usr/bin/env bash
# One-time installer: makes BluePRINTER a real desktop app.
# Run once: bash install.sh

set -e
cd "$(dirname "$(readlink -f "$0")")"

echo "Setting up BluePRINTER..."

# 1. Build the venv and install deps
if [ ! -d "venv" ]; then
    python -m venv venv
fi
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 2. Make the launcher executable
chmod +x BluePRINTER

# 3. Install the desktop entry so it shows in your app menu
APPDIR="$HOME/.local/share/applications"
mkdir -p "$APPDIR"
# Point the desktop entry at this actual install location
INSTALL_PATH="$(pwd)"
cat > "$APPDIR/blueprinter.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=BluePRINTER
Comment=Blueprint and 3D model annotation tool
Exec=bash -c "cd '$INSTALL_PATH' && ./BluePRINTER"
Icon=applications-graphics
Terminal=false
Categories=Graphics;Utility;
EOF

chmod +x "$APPDIR/blueprinter.desktop"
update-desktop-database "$APPDIR" 2>/dev/null || true

echo ""
echo "Done! BluePRINTER is now installed."
echo "  - Launch it from your application menu (search 'BluePRINTER'), OR"
echo "  - Double-click the 'BluePRINTER' file in this folder, OR"
echo "  - Run ./BluePRINTER from here."
echo ""
echo "No venv activation needed ever again."
