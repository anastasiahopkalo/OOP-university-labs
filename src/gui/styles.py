from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Кольори, якими малюють полотна візуалізації (QPainter) - окремо від QSS."""
    name: str
    background: str
    surface: str
    text: str
    muted: str
    accent: str
    border: str
    # Кольори елементів візуалізації
    element: str
    compare: str
    swap: str
    done: str


LIGHT = Theme(
    name="light",
    background="#f5f6f8",
    surface="#ffffff",
    text="#1f2328",
    muted="#656d76",
    accent="#2f6feb",
    border="#d0d7de",
    element="#6e9bd8",
    compare="#e3a008",
    swap="#d1495b",
    done="#2da44e",
)

DARK = Theme(
    name="dark",
    background="#1b1f24",
    surface="#24292f",
    text="#e6edf3",
    muted="#8d96a0",
    accent="#4c8dff",
    border="#3d444d",
    element="#5b8fd6",
    compare="#f0b429",
    swap="#ef6461",
    done="#3fb950",
)

THEMES = {LIGHT.name: LIGHT, DARK.name: DARK}


def stylesheet(theme: Theme) -> str:
    """Генерує QSS для всього застосунку з кольорів теми."""
    t = theme
    return f"""
        QWidget {{
            background-color: {t.background};
            color: {t.text};
            font-size: 13px;
        }}
        QTabWidget::pane {{
            border: 1px solid {t.border};
            background: {t.surface};
            border-radius: 6px;
        }}
        QTabBar::tab {{
            background: {t.background};
            color: {t.muted};
            padding: 8px 18px;
            border: none;
            border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:selected {{
            color: {t.text};
            border-bottom: 2px solid {t.accent};
        }}
        QPushButton {{
            background-color: {t.accent};
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 5px;
            font-weight: bold;
        }}
        QPushButton:disabled {{
            background-color: {t.border};
            color: {t.muted};
        }}
        QPushButton:hover:!disabled {{
            background-color: {t.element};
        }}
        QComboBox, QSpinBox, QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {{
            background: {t.surface};
            border: 1px solid {t.border};
            border-radius: 4px;
            padding: 4px;
        }}
        QProgressBar {{
            background: {t.surface};
            border: 1px solid {t.border};
            border-radius: 4px;
            text-align: center;
            height: 14px;
        }}
        QProgressBar::chunk {{
            background-color: {t.accent};
            border-radius: 4px;
        }}
        QMenuBar, QMenu, QStatusBar {{
            background: {t.surface};
            color: {t.text};
        }}
        QMenu::item:selected {{
            background: {t.accent};
            color: white;
        }}
        QLabel#title {{
            font-size: 16px;
            font-weight: bold;
        }}
        QLabel#muted {{
            color: {t.muted};
        }}
    """
