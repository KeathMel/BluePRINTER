from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QColor, QPainter, QFont, QTextFormat


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint(event)


class CodeEditor(QPlainTextEdit):
    """A retro flat code editor with a line-number gutter and row separators."""

    # Warm retro palette
    PAPER      = QColor("#eceae2")   # old-monitor off-white
    GUTTER     = QColor("#dcdad0")   # slightly darker gutter
    GUTTER_TXT = QColor("#6b6a63")   # muted line numbers
    ROW_LINE   = QColor("#dedcd2")   # faint separator between rows
    TEXT       = QColor("#1d1d1d")
    CUR_LINE   = QColor("#e2ded2")   # current-line highlight
    ACCENT     = QColor("#2d89ef")   # Metro blue

    def __init__(self):
        super().__init__()
        self.line_area = LineNumberArea(self)

        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        self.blockCountChanged.connect(self.update_line_area_width)
        self.updateRequest.connect(self.update_line_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.update_line_area_width(0)
        self.highlight_current_line()

        self.setStyleSheet(
            f"QPlainTextEdit {{"
            f" background-color: {self.PAPER.name()};"
            f" color: {self.TEXT.name()};"
            f" border: 2px solid #000000;"
            f" border-radius: 0px;"
            f" padding: 4px;"
            f" selection-background-color: {self.ACCENT.name()};"
            f" selection-color: #ffffff;"
            f"}}"
        )

    def line_number_area_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 16 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_area.setGeometry(QRect(cr.left(), cr.top(),
                                         self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(self.CUR_LINE)
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    def line_number_area_paint(self, event):
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), self.GUTTER)

        # vertical divider between gutter and text
        painter.setPen(QColor("#000000"))
        painter.drawLine(self.line_area.width() - 1, event.rect().top(),
                         self.line_area.width() - 1, event.rect().bottom())

        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(self.GUTTER_TXT)
                painter.drawText(0, top, self.line_area.width() - 8,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num += 1

    def paintEvent(self, event):
        # Draw faint horizontal separators between every text row first
        painter = QPainter(self.viewport())
        block = self.firstVisibleBlock()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        painter.setPen(self.ROW_LINE)
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawLine(0, bottom - 1, self.viewport().width(), bottom - 1)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
        painter.end()
        super().paintEvent(event)
