def apply_iron_man_theme(app):
    """
    Windows 8.1 Metro (Microsoft Design Language) theme - hard flat edition.

    Metro is stark and geometric: NO rounded corners, NO gradients, NO shadows,
    high contrast, thick square accent borders, flat colored fills, Segoe UI.
    Pair this with app.setStyle("Fusion") so the native platform style doesn't
    re-round or smooth the widgets underneath the stylesheet.
    """
    METRO_BLUE      = "#2d89ef"
    METRO_DARK_BLUE = "#2b5797"
    METRO_RED       = "#ee1111"
    METRO_DARK_RED  = "#b91d47"
    BG              = "#ffffff"
    PANEL           = "#ebebeb"
    TEXT            = "#000000"
    LINE            = "#000000"   # Metro uses hard, visible edges
    HOVER           = "#2d89ef"

    stylesheet = f"""
    QMainWindow, QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: 'Segoe UI', 'Segoe UI Semilight', 'Arial', sans-serif;
        font-size: 10pt;
    }}

    /* Tree / file list - hard 1px black edge, square selection tiles */
    QTreeWidget {{
        background-color: {BG};
        border: 1px solid {LINE};
        color: {TEXT};
        font-size: 10pt;
        outline: 0;
        padding: 0px;
    }}
    QTreeWidget::item {{
        padding: 7px 4px;
        border: none;
    }}
    QTreeWidget::item:selected {{
        background-color: {METRO_BLUE};
        color: #ffffff;
    }}
    QTreeWidget::item:hover {{
        background-color: {HOVER};
        color: #ffffff;
    }}

    /* Buttons - flat square tiles, hard edge, solid color flip on hover */
    QPushButton {{
        background-color: {PANEL};
        border: 2px solid {LINE};
        color: {TEXT};
        padding: 9px 20px;
        border-radius: 0px;
        font-size: 10pt;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {METRO_BLUE};
        border: 2px solid {METRO_BLUE};
        color: #ffffff;
    }}
    QPushButton:pressed {{
        background-color: {METRO_DARK_BLUE};
        border: 2px solid {METRO_DARK_BLUE};
        color: #ffffff;
    }}

    /* Text inputs - square, hard border, THICK blue focus (very Metro) */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {BG};
        border: 2px solid {LINE};
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

    /* Sliders - flat square groove and blocky square handle */
    QSlider::groove:horizontal {{
        height: 4px;
        background: #bfbfbf;
        border: none;
    }}
    QSlider::sub-page:horizontal {{
        background: {METRO_BLUE};
        border: none;
    }}
    QSlider::add-page:horizontal {{
        background: #bfbfbf;
        border: none;
    }}
    QSlider::handle:horizontal {{
        background: {METRO_BLUE};
        border: none;
        width: 10px;
        height: 22px;
        margin: -9px 0;
        border-radius: 0px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {METRO_DARK_BLUE};
    }}

    /* Scrollbars - thin, flat, square, no arrows */
    QScrollBar:vertical {{
        background: {PANEL};
        width: 14px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #999999;
        border-radius: 0px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {METRO_BLUE};
    }}
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        background: none; height: 0px;
    }}
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        background: none; height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {PANEL};
        height: 14px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: #999999;
        border-radius: 0px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {METRO_BLUE};
    }}
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        background: none; width: 0px;
    }}
    QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
        background: none; width: 0px;
    }}

    /* Menus - flat, hard edge, square blue selection */
    QMenu {{
        background-color: {BG};
        color: {TEXT};
        border: 1px solid {LINE};
        padding: 0px;
    }}
    QMenu::item {{
        padding: 9px 26px;
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
        border-bottom: 2px solid {LINE};
        padding: 7px;
        font-weight: bold;
    }}
    """
    app.setStyleSheet(stylesheet)
