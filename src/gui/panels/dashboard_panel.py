from datetime import date, timedelta
from typing import Callable, List, Optional, Tuple

import networkx as nx

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)

from src.core.achievements import ACHIEVEMENTS
from src.core.analytics import ProgressTracker
from src.core.exercise import CodeExercise
from src.core.benchmark import INPUT_GENERATORS
from src.core.knowledge_graph import AVAILABLE, LOCKED, MASTERED, KnowledgeGraph
from src.gui.panels.benchmark_panel import display_name
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


def _style_axes(ax, theme: Theme, title: str, grid_axis: str = "y"):
    ax.set_facecolor(theme.surface)
    ax.set_title(title, color=theme.text, fontsize=10, loc="left")
    ax.tick_params(colors=theme.muted, labelsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme.border)
    ax.grid(axis=grid_axis, color=theme.border, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


class KnowledgeGraphChart(FigureCanvasQTAgg):
    """Граф знань, намальований networkx на полотні matplotlib (рівні - зліва направо)."""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 3.6), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self._theme = LIGHT
        self.positions = {}

    def set_theme(self, theme: Theme):
        self._theme = theme

    def status_colors(self) -> dict:
        t = self._theme
        return {MASTERED: t.done, AVAILABLE: t.accent, LOCKED: t.border}

    def plot(self, kg: KnowledgeGraph, tracker: ProgressTracker):
        t = self._theme
        self.figure.clear()
        self.figure.set_facecolor(t.surface)
        ax = self.figure.add_subplot(1, 1, 1)
        ax.set_facecolor(t.surface)
        ax.set_axis_off()

        graph = kg.graph.copy()
        for level, keys in enumerate(kg.levels()):
            for key in keys:
                graph.nodes[key]["level"] = level
        self.positions = nx.multipartite_layout(graph, subset_key="level")
        statuses = kg.statuses(tracker)
        colors = self.status_colors()
        nodes = list(graph.nodes)

        nx.draw_networkx_edges(graph, self.positions, ax=ax, edge_color=t.muted, width=1.2,
                               arrows=True, arrowsize=12, node_size=3300, alpha=0.7)
        nx.draw_networkx_nodes(graph, self.positions, ax=ax, nodelist=nodes, node_size=3300,
                               node_shape="o", node_color=[colors[statuses[k]] for k in nodes],
                               edgecolors=t.border, linewidths=1)
        labels = {}
        for key in nodes:
            topic = kg.topic(key)
            title = topic.title.replace(" ", "\n")
            if topic.is_theory:
                labels[key] = title
            else:
                done, total = kg.topic_progress(key, tracker)
                labels[key] = f"{title}\n{done}/{total}"
        label_colors = {MASTERED: "#ffffff", AVAILABLE: "#ffffff", LOCKED: t.text}
        for status in (MASTERED, AVAILABLE, LOCKED):
            subset = {k: v for k, v in labels.items() if statuses[k] == status}
            nx.draw_networkx_labels(graph, self.positions, labels=subset, ax=ax, font_size=6.5,
                                    font_color=label_colors[status])
        ax.margins(0.08, 0.15)
        handles = [Line2D([], [], marker="o", linestyle="", markersize=9, color=colors[s], label=label)
                   for s, label in ((MASTERED, "пройдено"), (AVAILABLE, "доступно"),
                                    (LOCKED, "заблоковано"))]
        legend = ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=False, ncol=3)
        for text in legend.get_texts():
            text.set_color(t.text)
        self.draw_idle()


class ActivityChart(FigureCanvasQTAgg):
    """Кількість спроб за кожен з останніх днів (стовпчики matplotlib)."""

    DAYS = 14

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(6, 3), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self._theme = LIGHT

    def set_theme(self, theme: Theme):
        self._theme = theme

    @classmethod
    def series(cls, tracker: ProgressTracker, today: Optional[date] = None) -> List[Tuple[date, int]]:
        today = today or date.today()
        activity = tracker.daily_activity()
        days = [today - timedelta(days=i) for i in range(cls.DAYS - 1, -1, -1)]
        return [(day, activity.get(day, 0)) for day in days]

    def plot(self, tracker: ProgressTracker, today: Optional[date] = None):
        t = self._theme
        self.figure.clear()
        self.figure.set_facecolor(t.surface)
        ax = self.figure.add_subplot(1, 1, 1)
        _style_axes(ax, t, f"Активність за {self.DAYS} днів")
        data = self.series(tracker, today)
        values = [count for _, count in data]
        positions = list(range(len(data)))
        ax.bar(positions, values, color=[t.accent if v else t.border for v in values], width=0.7)
        ax.set_xticks(positions)
        ax.set_xticklabels([day.strftime("%d.%m") for day, _ in data], rotation=45, fontsize=7,
                           color=t.muted)
        ax.set_ylim(0, max(values + [3]) + 1)
        ax.yaxis.get_major_locator().set_params(integer=True)
        ax.set_ylabel("Спроб", color=t.muted, fontsize=8)
        self.draw_idle()


class BenchmarkHistoryChart(FigureCanvasQTAgg):
    """Останні збережені заміри з вкладки «Порівняння»: середній час кожного алгоритму на найбільшому n."""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(7, 3), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self._theme = LIGHT
        self.bars: List[Tuple[str, float, int]] = []

    def set_theme(self, theme: Theme):
        self._theme = theme

    @staticmethod
    def summarize(runs) -> Tuple[Optional[str], List[Tuple[str, float, int]]]:
        """(тип вхідних даних, [(алгоритм, час у мс, n)]) для найсвіжішого типу вхідних даних.

        Для кожного алгоритму береться найбільше n, а серед однакових n - найпізніший замір.
        """
        if not runs:
            return None, []
        latest = max(runs, key=lambda r: (r.timestamp, r.id or 0))
        best = {}
        for run in runs:
            if run.input_kind != latest.input_kind:
                continue
            key = (run.size, run.timestamp, run.id or 0)
            if run.algorithm not in best or key > best[run.algorithm][0]:
                best[run.algorithm] = (key, run)
        bars = [(display_name(name), run.mean_time * 1000, run.size) for name, (_, run) in best.items()]
        return latest.input_kind, sorted(bars, key=lambda bar: bar[1])

    def plot(self, runs):
        t = self._theme
        self.figure.clear()
        self.figure.set_facecolor(t.surface)
        ax = self.figure.add_subplot(1, 1, 1)
        kind, self.bars = self.summarize(runs)
        title = "Порівняння алгоритмів"
        if kind is not None:
            title += f" · {INPUT_GENERATORS[kind].title.lower() if kind in INPUT_GENERATORS else kind} масив"
        _style_axes(ax, t, title, grid_axis="x")
        if not self.bars:
            ax.text(0.5, 0.5, "Ще немає замірів - запустіть їх у вкладці «Порівняння»", ha="center",
                    va="center", color=t.muted, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            self.draw_idle()
            return
        positions = list(range(len(self.bars)))
        times = [ms for _, ms, _ in self.bars]
        fastest = min(times)
        ax.barh(positions, times, height=0.6,
                color=[t.done if ms == fastest else t.accent for ms in times])
        ax.set_yticks(positions)
        ax.set_yticklabels([f"{name} (n={n})" for name, _, n in self.bars], fontsize=8, color=t.text)
        ax.invert_yaxis()
        for y, ms in zip(positions, times):
            ax.text(ms, y, f"  {ms:.1f} мс", va="center", fontsize=8, color=t.muted)
        ax.set_xlim(0, max(times) * 1.25)
        ax.set_xlabel("Середній час, мс", color=t.muted, fontsize=8)
        self.draw_idle()


class DashboardPanel(QWidget):
    """Вкладка «Прогрес»: статистика, графіки і досягнення."""

    progressReset = pyqtSignal()

    def __init__(self, tracker: ProgressTracker, exercises: List[CodeExercise],
                 leaderboard: Optional[Callable[[], List[tuple]]] = None,
                 knowledge_graph: Optional[KnowledgeGraph] = None,
                 run_history: Optional[Callable[[], list]] = None, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.exercises = exercises
        self._leaderboard = leaderboard
        self._run_history = run_history
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.title_label = QLabel("Прогрес")
        self.title_label.setObjectName("title")
        header.addWidget(self.title_label)
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

        self.sections = QTabWidget()
        layout.addWidget(self.sections, stretch=1)

        # «Результати»: бали і досягнення
        results = QWidget()
        results_layout = QVBoxLayout(results)
        self.chart = ProgressChart(self)
        results_layout.addWidget(self.chart, stretch=2)
        self.achievements_title = QLabel()
        results_layout.addWidget(self.achievements_title)
        self.achievements = QListWidget()
        self.achievements.setMaximumHeight(170)
        results_layout.addWidget(self.achievements)
        self.sections.addTab(results, "Результати")

        # «Граф знань»: теми курсу і рекомендація
        knowledge = QWidget()
        knowledge_layout = QVBoxLayout(knowledge)
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        knowledge_layout.addWidget(self.recommendation_label)
        self.knowledge_chart = KnowledgeGraphChart(self)
        knowledge_layout.addWidget(self.knowledge_chart, stretch=1)
        self.sections.addTab(knowledge, "Граф знань")

        # «Активність і рейтинг»
        activity = QWidget()
        activity_layout = QHBoxLayout(activity)
        self.activity_chart = ActivityChart(self)
        activity_layout.addWidget(self.activity_chart, stretch=3)
        board = QWidget()
        board_layout = QVBoxLayout(board)
        board_layout.setContentsMargins(0, 0, 0, 0)
        self.leaderboard_title = QLabel("Рейтинг студентів")
        board_layout.addWidget(self.leaderboard_title)
        self.leaderboard_table = QTableWidget(0, 4)
        self.leaderboard_table.setHorizontalHeaderLabels(["#", "Студент", "Бали", "Спроб"])
        self.leaderboard_table.verticalHeader().setVisible(False)
        self.leaderboard_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.leaderboard_table.setSelectionMode(QAbstractItemView.NoSelection)
        header_view = self.leaderboard_table.horizontalHeader()
        header_view.setMinimumSectionSize(40)
        header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        board_layout.addWidget(self.leaderboard_table)
        activity_layout.addWidget(board, stretch=2)
        board.setVisible(self._leaderboard is not None)
        self.sections.addTab(activity, "Активність і рейтинг")

        # «Порівняння алгоритмів»: історія замірів з БД
        history = QWidget()
        history_layout = QVBoxLayout(history)
        self.history_label = QLabel()
        self.history_label.setObjectName("muted")
        self.history_label.setWordWrap(True)
        history_layout.addWidget(self.history_label)
        self.history_chart = BenchmarkHistoryChart(self)
        history_layout.addWidget(self.history_chart, stretch=1)
        self.history_tab_index = self.sections.addTab(history, "Порівняння алгоритмів")
        self.sections.setTabVisible(self.history_tab_index, self._run_history is not None)

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
        self.title_label.setText(f"Прогрес · {tracker.student_name}")
        self.chart.plot(tracker, self.exercise_titles)
        self.knowledge_chart.plot(self.knowledge_graph, tracker)
        self.recommendation_label.setText(self.recommendation_text())
        self.activity_chart.plot(tracker)
        self._fill_leaderboard()
        self._fill_history()

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

    def recommendation_text(self) -> str:
        topic = self.knowledge_graph.next_recommended(self.tracker)
        if topic is None:
            return "Усі теми пройдено 🎓"
        if topic.is_theory:
            return (f"Вправи всіх доступних тем розв'язано. Рекомендовано далі: <b>{topic.title}</b> "
                    f"(вкладка «{topic.tab}»)")
        done, total = self.knowledge_graph.topic_progress(topic.key, self.tracker)
        left = [t for t in topic.exercises if t not in self.tracker.solved_exercises()]
        return (f"Рекомендовано далі: <b>{topic.title}</b> ({done}/{total}) · "
                f"вправи: {', '.join(left)} · теорія у вкладці «{topic.tab}»")

    def _fill_leaderboard(self):
        if self._leaderboard is None:
            return
        try:
            rows = self._leaderboard()
        except Exception as error:  # збій БД не повинен ламати дашборд
            self.leaderboard_title.setText(f"Рейтинг недоступний: {error}")
            return
        self.leaderboard_title.setText("Рейтинг студентів")
        self.leaderboard_table.setRowCount(len(rows))
        for row, (name, score, attempts) in enumerate(rows):
            cells = [str(row + 1), name, str(score), str(attempts)]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if name == self.tracker.student_name:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.leaderboard_table.setItem(row, col, item)

    def _fill_history(self):
        if self._run_history is None:
            return
        try:
            runs = self._run_history()
        except Exception as error:  # збій БД не повинен ламати дашборд
            self.history_label.setText(f"Історія замірів недоступна: {error}")
            self.history_chart.plot([])
            return
        self.history_chart.plot(runs)
        if self.history_chart.bars:
            fastest = min(self.history_chart.bars, key=lambda bar: bar[1])[0]
            self.history_label.setText(
                f"Збережених замірів: {len(runs)} · найшвидший в останньому порівнянні: {fastest}")
        else:
            self.history_label.setText("Збережених замірів поки немає.")

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
        for chart in (self.chart, self.knowledge_chart, self.activity_chart, self.history_chart):
            chart.set_theme(theme)
        self.refresh()
