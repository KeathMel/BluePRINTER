"""
theme.py — BluePRINTER's look.

CYANOTYPE. A blueprint is pale line work on deep blue paper, and that is the
whole idea: a navy-black ground rather than a neutral one, drafting white for
text, one drafting blue for anything interactive, and red kept exclusively for
markers so a marker never competes with a button for attention.

The geometry is unchanged from before — hard flat edges, no rounding, no
gradients, no shadows. Pair it with app.setStyle("Fusion") so the platform
style doesn't re-round the widgets underneath the stylesheet.

Every colour lives here. Nothing else in the app should hardcode one.
"""

# ---- the palette, in one place -------------------------------------------
INK          = "#0b1119"   # deepest — the app ground
PAPER        = "#111a24"   # panels, inputs, the drawing surface
RAISED       = "#182430"   # tiles that sit above PAPER
LINE         = "#24333f"   # hairline borders
LINE_STRONG  = "#33475a"   # borders that need to read as an edge

TEXT         = "#d7e3ef"   # drafting white
TEXT_DIM     = "#7e93a6"   # labels, line numbers, hints
TEXT_FAINT   = "#4a5b6d"   # disabled

BLUE         = "#4f9fd4"   # the accent: drafting blue
BLUE_BRIGHT  = "#6fc0f0"   # hover
BLUE_DEEP    = "#2c6f9c"   # pressed
BLUE_GHOST   = "rgba(79,159,212,0.16)"   # selection wash

MARKER       = "#ff5c4d"   # markers only — never a button
MARKER_DEEP  = "#c9372c"

MONO    = "'JetBrains Mono', 'Consolas', 'DejaVu Sans Mono', monospace"
UI_FONT = "'Inter', 'Segoe UI', 'Cantarell', sans-serif"


def apply_theme(app):
    app.setStyleSheet(f"""
    QMainWindow, QWidget {{
        background-color: {INK};
        color: {TEXT};
        font-family: {UI_FONT};
        font-size: 10pt;
    }}

    /* ---- file tree ----------------------------------------------------- */
    QTreeWidget {{
        background-color: {PAPER};
        border: 1px solid {LINE};
        color: {TEXT};
        font-family: {MONO};
        font-size: 9.5pt;
        outline: 0;
    }}
    QTreeWidget::item {{ padding: 6px 4px; border: none; }}
    QTreeWidget::item:hover {{ background-color: {BLUE_GHOST}; color: {TEXT}; }}
    QTreeWidget::item:selected {{ background-color: {BLUE}; color: {INK}; }}

    /* ---- buttons: flat tiles, the accent arrives on hover --------------- */
    QPushButton {{
        background-color: {RAISED};
        border: 1px solid {LINE_STRONG};
        color: {TEXT};
        padding: 8px 18px;
        border-radius: 0px;
        font-family: {MONO};
        font-size: 9.5pt;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {BLUE};
        border: 1px solid {BLUE};
        color: {INK};
    }}
    QPushButton:pressed {{
        background-color: {BLUE_DEEP};
        border: 1px solid {BLUE_DEEP};
        color: {TEXT};
    }}
    QPushButton:disabled {{
        color: {TEXT_FAINT};
        border: 1px solid {LINE};
        background-color: transparent;
    }}

    /* ---- inputs -------------------------------------------------------- */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {PAPER};
        border: 1px solid {LINE_STRONG};
        color: {TEXT};
        padding: 6px;
        border-radius: 0px;
        font-family: {MONO};
        font-size: 9.5pt;
        selection-background-color: {BLUE};
        selection-color: {INK};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {BLUE};
    }}

    QLabel {{ color: {TEXT}; font-size: 10pt; background: transparent; }}

    /* ---- sliders: a thin rule with a square handle, like a drafting scale */
    QSlider::groove:horizontal {{ height: 2px; background: {LINE_STRONG}; border: none; }}
    QSlider::sub-page:horizontal {{ background: {BLUE}; border: none; }}
    QSlider::add-page:horizontal {{ background: {LINE_STRONG}; border: none; }}
    QSlider::handle:horizontal {{
        background: {BLUE};
        border: none;
        width: 8px;
        height: 18px;
        margin: -8px 0;
        border-radius: 0px;
    }}
    QSlider::handle:horizontal:hover {{ background: {BLUE_BRIGHT}; }}

    /* ---- scrollbars: thin, square, no arrows ---------------------------- */
    QScrollBar:vertical {{
        background: {INK}; width: 12px; border: none;
        border-left: 1px solid {LINE}; margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {LINE_STRONG}; border-radius: 0px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {BLUE}; }}
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        background: none; height: 0px;
    }}
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        background: none; height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {INK}; height: 12px; border: none;
        border-top: 1px solid {LINE}; margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {LINE_STRONG}; border-radius: 0px; min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {BLUE}; }}
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        background: none; width: 0px;
    }}
    QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
        background: none; width: 0px;
    }}

    /* ---- menus ---------------------------------------------------------- */
    QMenu {{
        background-color: {PAPER};
        color: {TEXT};
        border: 1px solid {LINE_STRONG};
        padding: 2px;
        font-family: {MONO};
        font-size: 9.5pt;
    }}
    QMenu::item {{ padding: 8px 22px; }}
    QMenu::item:selected {{ background-color: {BLUE}; color: {INK}; }}
    QMenu::separator {{ height: 1px; background: {LINE}; margin: 3px 0px; }}

    QDialog {{ background-color: {INK}; color: {TEXT}; }}
    QMessageBox {{ background-color: {INK}; }}

    QHeaderView::section {{
        background-color: {INK};
        color: {TEXT_DIM};
        border: none;
        border-bottom: 1px solid {LINE_STRONG};
        padding: 6px;
        font-family: {MONO};
        font-size: 9pt;
        letter-spacing: 1px;
    }}

    QToolTip {{
        background-color: {PAPER};
        color: {TEXT};
        border: 1px solid {BLUE};
        padding: 5px 7px;
        font-family: {MONO};
        font-size: 9pt;
    }}
    """)


# the app used to call this name; kept so nothing breaks
def apply_iron_man_theme(app):
    apply_theme(app)
