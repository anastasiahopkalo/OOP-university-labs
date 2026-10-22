from typing import List, Optional

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox
)

from src.core.achievements import ACHIEVEMENTS
from src.core.analytics import ProgressTracker
from src.core.exercise import CodeExercise
from src.gui.styles import Theme, LIGHT


class StatCard(QFrame):
    """Картка з великим числом і підписом."""

    def __init__(self, caption: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        self.value_label = QLabel("—")
        self.value_label.setObjectName("cardValue")
        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("muted")
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, text: str):
        self.value_label.setText(text)


class ProgressChart(FigureCanvasQTAgg):
    """Два графіки matplotlib: бали за спробами і найкращий бал за вправами."""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 3.2), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self._theme = LIGHT

    def set_theme(self, theme: Theme):
        self._theme = theme

    def _style_axes(self, ax, title: str):
        t = self._theme
        ax.set_facecolor(t.surface)
        ax.set_title(title, color=t.text, fontsize=10, loc="left")
        ax.tick_params(colors=t.muted, labelsize=8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(t.border)
        ax.grid(axis="y" if title.startswith("Бали") else "x", color=t.border, linewidth=0.6, alpha=0.7)
        ax.set_axisbelow(True)

    def plot(self, tracker: ProgressTracker, exercise_titles: List[str]):
        t = self._theme
        self.figure.clear()
        self.figure.set_facecolor(t.surface)

        history = tracker.history()
        ax1 = self.figure.add_subplot(1, 2, 1)
        self._style_axes(ax1, "Бали за спробами")
        if history:
            xs = list(range(1, len(history) + 1))
            scores = [r["score"] for r in history]
            ax1.plot(xs, scores, color=t.accent, linewidth=2, zorder=2)
            ax1.scatter(xs, scores, zorder=3, s=28,
                        c=[t.done if r["passed"] else t.swap for r in history])
            ax1.set_xlim(0.5, max(len(xs), 2) + 0.5)
            ax1.xaxis.get_major_locator().set_params(integer=True)
        else:
            ax1.text(0.5, 0.5, "Ще немає спроб", ha="center", va="center",
                     color=t.muted, transform=ax1.transAxes)
        ax1.set_ylim(-5, 105)
        ax1.set_xlabel("Спроба", color=t.muted, fontsize=8)

        ax2 = self.figure.add_subplot(1, 2, 2)
        self._style_axes(ax2, "Найкращий бал за вправами")
        best = tracker.best_scores()
        values = [best.get(title) or 0 for title in exercise_titles]
        colors = [t.done if v == 100 else (t.compare if v > 0 else t.border) for v in values]
        positions = list(range(len(exercise_titles)))
        ax2.barh(positions, values, color=colors, height=0.6)
        ax2.set_yticks(positions)
        ax2.set_yticklabels(exercise_titles, fontsize=8, color=t.text)
        ax2.invert_yaxis()
        ax2.set_xlim(0, 100)
        self.draw_idle()


class DashboardPanel(QWidget):
    """Вкладка «Прогрес»: статистика, графіки і досягнення."""

    progressReset = pyqtSignal()

    def __init__(self, tracker: ProgressTracker, exercises: List[CodeExercise], parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.exercises = exercises
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Прогрес")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.reset_btn = QPushButton("Скинути прогрес")
        self.reset_btn.clicked.connect(self._confirm_reset)
        header.addWidget(self.reset_btn)
        layout.addLayout(header)

        cards = QHBoxLayout()
        self.solved_card = StatCard("вправ розв'язано")
        self.attempts_card = StatCard("спроб")
        self.average_card = StatCard("середній бал")
        self.success_card = StatCard("успішних спроб")
        self.streak_card = StatCard("днів поспіль")
        for card in (self.solved_card, self.attempts_card, self.average_card,
                     self.success_card, self.streak_card):
            cards.addWidget(card)
        layout.addLayout(cards)

        self.chart = ProgressChart(self)
        layout.addWidget(self.chart, stretch=2)

        self.achievements_title = QLabel()
        layout.addWidget(self.achievements_title)
        self.achievements = QListWidget()
        self.achievements.setMaximumHeight(170)
        layout.addWidget(self.achievements)

    @property
    def exercise_titles(self) -> List[str]:
        return [e.title for e in self.exercises]

    def refresh(self):
        tracker = self.tracker
        solved = len([t for t in tracker.solved_exercises() if t in self.exercise_titles])
        self.solved_card.set_value(f"{solved} / {len(self.exercises)}")
        self.attempts_card.set_value(str(tracker.total_attempts()))
        self.average_card.set_value(f"{tracker.average_score():.0f}")
        self.success_card.set_value(f"{tracker.success_rate() * 100:.0f}%")
        self.streak_card.set_value(f"🔥 {tracker.streak_days()}")
        self.chart.plot(tracker, self.exercise_titles)

        self.achievements.clear()
        unlocked_count = 0
        for achievement in ACHIEVEMENTS:
            is_unlocked = achievement.is_unlocked(tracker, len(self.exercises))
            unlocked_count += is_unlocked
            prefix = achievement.icon if is_unlocked else "🔒"
            item = QListWidgetItem(f"{prefix}  {achievement.title} - {achievement.description}")
            if not is_unlocked:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.achievements.addItem(item)
        self.achievements_title.setText(f"Досягнення: {unlocked_count} з {len(ACHIEVEMENTS)}")

    def reset_progress(self):
        self.tracker.completed_exercises.clear()
        self.tracker.total_time = 0.0
        self.refresh()
        self.progressReset.emit()

    def _confirm_reset(self):
        answer = QMessageBox.question(self, "Скинути прогрес",
                                      "Видалити всі спроби та досягнення? Цю дію не можна скасувати.")
        if answer == QMessageBox.Yes:
            self.reset_progress()

    def set_theme(self, theme: Theme):
        self.chart.set_theme(theme)
        self.refresh()
