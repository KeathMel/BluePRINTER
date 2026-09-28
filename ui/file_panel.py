"""
file_panel.py — what's selected, and the ways out of the library.

BluePRINTER copies files in and owns them from then on, so it needs a door in
the other direction: export puts a copy back wherever you want, without
touching the one the app holds. This panel is that door, plus the name of
whatever is currently selected so there's never a doubt about what an action
will apply to.
"""
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QDialog, QTreeView)
# Qt6 moved QFileSystemModel from QtWidgets to QtGui
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import pyqtSignal, QDir

from . import theme


class FilePanel(QWidget):
    export_file = pyqtSignal()
    export_project = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._kind = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 10)
        lay.setSpacing(6)

        head = QLabel("SELECTED")
        head.setStyleSheet(
            f"color: {theme.TEXT_DIM}; font-family: {theme.MONO}; "
            "font-size: 9pt; letter-spacing: 2px;")
        lay.addWidget(head)

        self.name = QLabel("nothing selected")
        self.name.setWordWrap(True)
        self.name.setStyleSheet(
            f"color: {theme.TEXT}; font-family: {theme.MONO}; font-size: 11pt;")
        lay.addWidget(self.name)

        self.kind = QLabel("")
        self.kind.setStyleSheet(
            f"color: {theme.TEXT_DIM}; font-family: {theme.MONO}; font-size: 9pt;")
        lay.addWidget(self.kind)

        self.btn_file = QPushButton("⤓  EXPORT FILE")
        self.btn_file.setToolTip(
            "Save a copy of this file somewhere else. The copy BluePRINTER "
            "holds is left as it is.")
        self.btn_file.clicked.connect(self.export_file.emit)
        lay.addWidget(self.btn_file)

        self.btn_proj = QPushButton("⤓  EXPORT PROJECT")
        self.btn_proj.setToolTip(
            "Save the whole project — every file and its markers — into a "
            "folder you pick.")
        self.btn_proj.clicked.connect(self.export_project.emit)
        lay.addWidget(self.btn_proj)

        self.clear()

    # -- what's selected ----------------------------------------------------
    def show_file(self, path, project_name=None):
        self.name.setText(path.name)
        self.kind.setText(f"file in {project_name}" if project_name else "file")
        self.btn_file.setVisible(True)
        self.btn_proj.setVisible(bool(project_name))
        self.setVisible(True)

    def show_project(self, name, file_count):
        self.name.setText(name)
        self.kind.setText(f"project · {file_count} file{'s' if file_count != 1 else ''}")
        self.btn_file.setVisible(False)
        self.btn_proj.setVisible(True)
        self.setVisible(True)

    def clear(self):
        self.name.setText("nothing selected")
        self.kind.setText("")
        self.btn_file.setVisible(False)
        self.btn_proj.setVisible(False)
        self.setVisible(True)


class ExportDialog(QDialog):
    """Pick a destination: type it, or browse to it right here.

    The browser is a plain tree inside this dialog rather than QFileDialog.
    The system chooser opens a separate top-level window, which on this
    machine's Wayland/NVIDIA stack took the compositor down with it — and it
    ignored the starting folder anyway. This stays in one ordinary window.
    """

    def __init__(self, parent, title, default_path, pick_folder=False,
                 heading="EXPORT TO", hint=None, action="EXPORT",
                 must_exist=False):
        super().__init__(parent)
        self.pick_folder = pick_folder
        self.must_exist = must_exist
        self.setWindowTitle(title)
        self.setMinimumSize(640, 520)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        head = QLabel(heading)
        head.setStyleSheet(
            f"color: {theme.TEXT_DIM}; font-family: {theme.MONO}; "
            "font-size: 9pt; letter-spacing: 2px;")
        lay.addWidget(head)

        self.path_edit = QLineEdit(str(default_path))
        self.path_edit.returnPressed.connect(self.accept)
        self.path_edit.textEdited.connect(self._typed)
        lay.addWidget(self.path_edit)

        self.hint = QLabel(hint or ("The folder it goes into" if pick_folder
                                    else "Full path including the file name"))
        self._hint_css = (f"color: {theme.TEXT_DIM}; "
                          f"font-family: {theme.MONO}; font-size: 9pt;")
        self.hint.setStyleSheet(self._hint_css)
        lay.addWidget(self.hint)

        # ---- the browser ---------------------------------------------------
        self.model = QFileSystemModel()
        self.model.setRootPath(str(Path.home()))
        if pick_folder:
            self.model.setFilter(QDir.Filter.Dirs | QDir.Filter.Drives
                                 | QDir.Filter.NoDotAndDotDot)
        else:
            self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.Drives
                                 | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(Path.home())))
        # name column only — size/type/date are noise here
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.setHeaderHidden(True)
        self.tree.clicked.connect(self._picked)
        self.tree.doubleClicked.connect(self._entered)
        lay.addWidget(self.tree, 1)

        # ---- shortcuts to the places you actually go -----------------------
        quick = QHBoxLayout()
        quick.setSpacing(6)
        for label, target in self._quick_targets():
            b = QPushButton(label)
            b.clicked.connect(lambda _c=False, t=target: self._go(t))
            quick.addWidget(b)
        quick.addStretch()
        lay.addLayout(quick)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("CANCEL"); cancel.clicked.connect(self.reject)
        ok = QPushButton(action); ok.clicked.connect(self.accept)
        ok.setDefault(True)
        btns.addWidget(cancel); btns.addWidget(ok)
        lay.addLayout(btns)

        self._go(Path(str(default_path)).expanduser(), select=True)

    # -- navigation ---------------------------------------------------------
    def _quick_targets(self):
        home = Path.home()
        out = [("HOME", home)]
        for name in ("Downloads", "Documents", "Desktop"):
            d = home / name
            if d.is_dir():
                out.append((name.upper(), d))
        return out

    def _go(self, path, select=False):
        """Show `path`'s folder in the tree, optionally selecting the item."""
        path = Path(path).expanduser()
        folder = path if path.is_dir() else path.parent
        if not folder.is_dir():
            folder = Path.home()
        self.tree.setRootIndex(self.model.index(str(folder)))
        if not select and not self.pick_folder:
            # keep whatever file name was typed, just move the folder part
            self.path_edit.setText(str(folder / Path(self.path_edit.text()).name))
        elif not select:
            self.path_edit.setText(str(folder))

    def _picked(self, index):
        chosen = Path(self.model.filePath(index))
        if self.pick_folder and not chosen.is_dir():
            return
        if chosen.is_dir() or self.pick_folder:
            self.path_edit.setText(str(chosen))
        else:
            self.path_edit.setText(str(chosen))
        self._reset_hint()

    def _entered(self, index):
        chosen = Path(self.model.filePath(index))
        if chosen.is_dir():
            self.tree.setRootIndex(self.model.index(str(chosen)))
            self.path_edit.setText(
                str(chosen if self.pick_folder
                    else chosen / Path(self.path_edit.text()).name))

    def _typed(self, _text):
        self._reset_hint()

    def _reset_hint(self):
        self.hint.setStyleSheet(self._hint_css)

    # -- result -------------------------------------------------------------
    def accept(self):
        if self.must_exist and not self.path().exists():
            self.hint.setText("that path doesn't exist")
            self.hint.setStyleSheet(
                f"color: {theme.MARKER}; font-family: {theme.MONO}; font-size: 9pt;")
            return
        super().accept()

    def path(self):
        return Path(self.path_edit.text().strip()).expanduser()


class FilePickDialog(QDialog):
    """Choose one or more files to bring in — same in-window tree as
    ExportDialog, with multi-select. Ctrl-click or shift-click for several."""

    def __init__(self, parent, start=None):
        super().__init__(parent)
        self.setWindowTitle("Select files")
        self.setMinimumSize(640, 520)
        start = Path(start).expanduser() if start else Path.home()
        if not start.is_dir():
            start = Path.home()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        head = QLabel("ADD FILES FROM")
        head.setStyleSheet(
            f"color: {theme.TEXT_DIM}; font-family: {theme.MONO}; "
            "font-size: 9pt; letter-spacing: 2px;")
        lay.addWidget(head)

        self.where = QLineEdit(str(start))
        self.where.returnPressed.connect(lambda: self._go(Path(self.where.text())))
        lay.addWidget(self.where)

        self.model = QFileSystemModel()
        self.model.setRootPath(str(start))
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.Drives
                             | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(start)))
        self.tree.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self._entered)
        self.tree.selectionModel().selectionChanged.connect(self._count)
        lay.addWidget(self.tree, 1)

        self.count = QLabel("nothing selected")
        self.count.setStyleSheet(
            f"color: {theme.TEXT_DIM}; font-family: {theme.MONO}; font-size: 9pt;")
        lay.addWidget(self.count)

        quick = QHBoxLayout(); quick.setSpacing(6)
        home = Path.home()
        targets = [("HOME", home)]
        for n in ("Downloads", "Documents", "Desktop"):
            if (home / n).is_dir():
                targets.append((n.upper(), home / n))
        for label, t in targets:
            b = QPushButton(label)
            b.clicked.connect(lambda _c=False, x=t: self._go(x))
            quick.addWidget(b)
        quick.addStretch()
        up = QPushButton("UP")
        up.clicked.connect(lambda: self._go(Path(self.where.text()).parent))
        quick.addWidget(up)
        lay.addLayout(quick)

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("CANCEL"); cancel.clicked.connect(self.reject)
        ok = QPushButton("ADD"); ok.clicked.connect(self.accept); ok.setDefault(True)
        btns.addWidget(cancel); btns.addWidget(ok)
        lay.addLayout(btns)

    def _go(self, folder):
        folder = Path(folder).expanduser()
        if folder.is_dir():
            self.tree.setRootIndex(self.model.index(str(folder)))
            self.where.setText(str(folder))

    def _entered(self, index):
        path = Path(self.model.filePath(index))
        if path.is_dir():
            self._go(path)

    def _count(self, *_a):
        n = len(self.files())
        self.count.setText(
            "nothing selected" if n == 0
            else f"{n} file{'s' if n != 1 else ''} selected")

    def files(self):
        out = []
        for idx in self.tree.selectionModel().selectedIndexes():
            if idx.column() != 0:
                continue
            p = Path(self.model.filePath(idx))
            if p.is_file():
                out.append(str(p))
        return out
