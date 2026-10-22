import keyword
import re

from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QFontDatabase
from PyQt5.QtWidgets import QPlainTextEdit

from src.gui.styles import Theme, LIGHT, DARK

# Кольори підсвічування для кожної теми
SYNTAX_COLORS = {
    LIGHT.name: {"keyword": "#cf222e", "string": "#0a3069", "comment": "#6e7781",
                 "number": "#0550ae", "builtin": "#8250df"},
    DARK.name: {"keyword": "#ff7b72", "string": "#a5d6ff", "comment": "#8b949e",
                "number": "#79c0ff", "builtin": "#d2a8ff"},
}

BUILTINS = ["len", "range", "print", "list", "dict", "set", "tuple", "int", "str", "float",
            "enumerate", "zip", "min", "max", "sum", "abs", "sorted", "reversed", "isinstance"]


class PythonHighlighter(QSyntaxHighlighter):
    """Просте підсвічування Python: ключові слова, вбудовані функції, рядки, числа, коментарі."""

    RULES = [
        ("keyword", r"\b(" + "|".join(keyword.kwlist) + r")\b"),
        ("builtin", r"\b(" + "|".join(BUILTINS) + r")\b"),
        ("number", r"\b\d+(\.\d+)?\b"),
        ("string", r"(\"[^\"\n]*\"|'[^'\n]*')"),
        ("comment", r"#[^\n]*"),
    ]

    def __init__(self, document, theme: Theme = LIGHT):
        super().__init__(document)
        self._rules = [(name, re.compile(pattern)) for name, pattern in self.RULES]
        self._formats = {}
        self.set_theme(theme)

    def set_theme(self, theme: Theme):
        colors = SYNTAX_COLORS.get(theme.name, SYNTAX_COLORS[LIGHT.name])
        self._formats = {}
        for name, color in colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if name == "keyword":
                fmt.setFontWeight(QFont.Bold)
            if name == "comment":
                fmt.setFontItalic(True)
            self._formats[name] = fmt
        self.rehighlight()

    def highlightBlock(self, text: str):
        # Пізніші правила (рядки, коментарі) перекривають ранні
        for name, pattern in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self._formats[name])


class CodeEditor(QPlainTextEdit):
    """Редактор коду: моноширинний шрифт, Tab = 4 пробіли, підсвічування синтаксису."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = PythonHighlighter(self.document())

    def keyPressEvent(self, event):
        from PyQt5.QtCore import Qt
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Автовідступ: зберігаємо відступ рядка і додаємо 4 пробіли після ':'
            line = self.textCursor().block().text()
            indent = line[:len(line) - len(line.lstrip(" "))]
            if line.rstrip().endswith(":"):
                indent += "    "
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
        super().keyPressEvent(event)

    def set_theme(self, theme: Theme):
        self.highlighter.set_theme(theme)
