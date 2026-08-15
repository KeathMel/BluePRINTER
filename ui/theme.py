"""Iron Man themed UI"""

def apply_iron_man_theme(app):
    """Apply dark neon Iron Man theme"""
    stylesheet = """
    QMainWindow, QWidget {
        background-color: #0A0E27;
        color: #E8E8E8;
    }
    
    QListWidget {
        background-color: rgba(26, 31, 58, 0.6);
        border: 1px solid rgba(0, 217, 255, 0.2);
        border-radius: 6px;
        color: #E8E8E8;
    }
    
    QListWidget::item:selected {
        background-color: rgba(0, 217, 255, 0.3);
        border-left: 3px solid #00D9FF;
    }
    
    QPushButton {
        background-color: rgba(0, 217, 255, 0.1);
        border: 1px solid rgba(0, 217, 255, 0.4);
        color: #00D9FF;
        padding: 8px 16px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    QPushButton:hover {
        background-color: rgba(0, 217, 255, 0.2);
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.4);
    }
    
    QPushButton:pressed {
        background-color: rgba(0, 217, 255, 0.3);
    }
    
    QLineEdit, QTextEdit {
        background-color: rgba(0, 217, 255, 0.05);
        border: 1px solid rgba(0, 217, 255, 0.3);
        color: #E8E8E8;
        padding: 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #00D9FF;
        background-color: rgba(0, 217, 255, 0.1);
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.3);
    }
    
    QLabel {
        color: #E8E8E8;
        font-family: 'Courier New', monospace;
    }
    
    QScrollBar:vertical {
        background: rgba(0, 217, 255, 0.05);
        width: 8px;
        border-radius: 4px;
    }
    
    QScrollBar::handle:vertical {
        background: rgba(0, 217, 255, 0.3);
        border-radius: 4px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: rgba(0, 217, 255, 0.5);
    }
    
    QDialog {
        background-color: #0A0E27;
    }
    """
    app.setStyleSheet(stylesheet)
