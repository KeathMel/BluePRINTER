def apply_iron_man_theme(app):
    """
    Windows 8.1 Metro (Microsoft Design Language) theme.

    Metro principles applied:
      - Completely FLAT: no gradients, no shadows, no pseudo-3D, ZERO rounded corners
      - "Content before chrome": minimal borders, lots of whitespace
      - Segoe UI typography as the primary visual element
      - Authentic Metro accent palette (Metro Blue #2d89ef)
      - Sharp geometric rectangular shapes
    """
    # Authentic Metro palette
    METRO_BLUE      = "#2d89ef"   # primary accent
    METRO_DARK_BLUE = "#2b5797"   # pressed / darker accent
    METRO_TEAL      = "#00aba9"
    METRO_RED       = "#ee1111"
    BG              = "#ffffff"   # Metro favors white/very light backgrounds
    PANEL           = "#f2f2f2"   # subtle panel separation
    TEXT            = "#1d1d1d"   # Metro "darken"
    SUBTLE_LINE     = "#e6e6e6"   # hairline separators
    HOVER           = "#e5f1fb"   # light blue hover wash

    stylesheet = f"""
    QMainWindow, QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: 'Segoe UI', 'Segoe UI Light', 'Arial', sans-serif;
        font-size: 10pt;
    }}

    /* Tree / file list - flat, hairline border */
    QTreeWidget {{
        background-color: {BG};
        border: 1px solid {SUBTLE_LINE};
        color: {TEXT};
        font-size: 10pt;
        outline: 0;
        padding: 2px;
    }}
    QTreeWidget::item {{
        padding: 6px 4px;
        border: none;
    }}
    QTreeWidget::item:selected {{
        background-color: {METRO_BLUE};
        color: #ffffff;
    }}
    QTreeWidget::item:hover {{
        background-color: {HOVER};
        color: {TEXT};
    }}
    QTreeWidget::branch {{
        background: transparent;
    }}

    /* Buttons - hard rectangles, no radius, flat fill */
    QPushButton {{
        background-color: {PANEL};
        border: 1px solid {SUBTLE_LINE};
        color: {TEXT};
        padding: 8px 18px;
        border-radius: 0px;
        font-size: 10pt;
    }}
    QPushButton:hover {{
        background-color: {METRO_BLUE};
        border: 1px solid {METRO_BLUE};
        color: #ffffff;
    }}
    QPushButton:pressed {{
        background-color: {METRO_DARK_BLUE};
        border: 1px solid {METRO_DARK_BLUE};
        color: #ffffff;
    }}

    /* Text inputs - flat, thin border, blue focus */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {BG};
        border: 1px solid #cccccc;
        color: {TEXT};
        padding: 6px;
        border-radius: 0px;
        font-size: 10pt;
        selection-background-color: {METRO_BLUE};
        selection-color: #ffffff;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {METRO_BLUE};
    }}

    QLabel {{
        color: {TEXT};
        font-size: 10pt;
        background: transparent;
    }}

    /* Sliders - flat rectangular groove and handle */
    QSlider::groove:horizontal {{
        height: 4px;
        background: #cccccc;
        border: none;
    }}
    QSlider::sub-page:horizontal {{
        background: {METRO_BLUE};
        border: none;
    }}
    QSlider::handle:horizontal {{
        background: {METRO_BLUE};
        border: none;
        width: 12px;
        height: 20px;
        margin: -8px 0;
        border-radius: 0px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {METRO_DARK_BLUE};
    }}

    /* Scrollbars - thin, flat, no arrows (Metro style) */
    QScrollBar:vertical {{
        background: {BG};
        width: 12px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #cdcdcd;
        border-radius: 0px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {METRO_BLUE};
    }}
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        background: none;
        height: 0px;
    }}
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        background: none;
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {BG};
        height: 12px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: #cdcdcd;
        border-radius: 0px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {METRO_BLUE};
    }}
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        background: none;
        width: 0px;
    }}
    QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
        background: none;
        width: 0px;
    }}

    /* Menus - flat, sharp, blue selection */
    QMenu {{
        background-color: {BG};
        color: {TEXT};
        border: 1px solid #cccccc;
        padding: 2px;
    }}
    QMenu::item {{
        padding: 8px 24px;
    }}
    QMenu::item:selected {{
        background-color: {METRO_BLUE};
        color: #ffffff;
    }}

    QDialog {{
        background-color: {BG};
        color: {TEXT};
    }}
    QMessageBox {{
        background-color: {BG};
    }}

    QHeaderView::section {{
        background-color: {PANEL};
        color: {TEXT};
        border: none;
        border-bottom: 1px solid {SUBTLE_LINE};
        padding: 6px;
        font-weight: bold;
    }}
    """
    app.setStyleSheet(stylesheet)
