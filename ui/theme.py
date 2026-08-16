def apply_iron_man_theme(app):
    stylesheet = """
    QMainWindow, QWidget {
        background-color: #F0F0F0;
        color: #333333;
    }
    
    QTreeWidget {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        color: #333333;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 10pt;
    }
    
    QTreeWidget::item:selected {
        background-color: #0078D4;
        color: #FFFFFF;
    }
    
    QTreeWidget::item:hover {
        background-color: #E8E8E8;
    }
    
    QPushButton {
        background-color: #E1E1E1;
        border: 1px solid #CCCCCC;
        color: #333333;
        padding: 6px 16px;
        border-radius: 2px;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 10pt;
    }
    
    QPushButton:hover {
        background-color: #D0D0D0;
        border: 1px solid #999999;
    }
    
    QPushButton:pressed {
        background-color: #0078D4;
        color: #FFFFFF;
        border: 1px solid #0078D4;
    }
    
    QLineEdit, QTextEdit {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        color: #333333;
        padding: 4px;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 10pt;
    }
    
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #0078D4;
        background-color: #FFFFFF;
    }
    
    QLabel {
        color: #333333;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 10pt;
    }
    
    QScrollBar:vertical {
        background: #F0F0F0;
        width: 12px;
        border: none;
    }
    
    QScrollBar::handle:vertical {
        background: #CCCCCC;
        border-radius: 0px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: #999999;
    }
    
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
        background: none;
    }
    
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
        background: none;
    }
    
    QMenu {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    
    QMenu::item:selected {
        background-color: #0078D4;
        color: #FFFFFF;
    }
    
    QDialog {
        background-color: #F0F0F0;
        color: #333333;
    }
    
    QMessageBox {
        background-color: #F0F0F0;
    }
    """
    app.setStyleSheet(stylesheet)
