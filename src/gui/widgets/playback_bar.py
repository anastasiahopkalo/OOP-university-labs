from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSlider

from src.gui.step_player import StepPlayer


class PlaybackBar(QWidget):
    """Кнопки Назад / Старт / Крок / Скинути, повзунок швидкості і таймер.

    Сама рухає переданий StepPlayer і повідомляє про зміну кроку сигналом
    stepChanged - панелі лише перемальовують стан.
    """

    stepChanged = pyqtSignal()
    playingChanged = pyqtSignal(bool)

    def __init__(self, player: StepPlayer, parent=None):
        super().__init__(parent)
        self._player = player
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.back_btn = QPushButton("⏮ Назад")
        self.back_btn.clicked.connect(self.step_back)
        self.play_btn = QPushButton("▶ Старт")
        self.play_btn.clicked.connect(self.toggle_play)
        self.step_btn = QPushButton("⏭ Крок")
        self.step_btn.clicked.connect(self.step_forward)
        self.reset_btn = QPushButton("🔄 Скинути")
        self.reset_btn.clicked.connect(self.reset)
        for btn in (self.back_btn, self.play_btn, self.step_btn, self.reset_btn):
            layout.addWidget(btn)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Швидкість:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.setMaximumWidth(200)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_slider)
        layout.addStretch()
        self.update_buttons()

    @property
    def is_playing(self) -> bool:
        return self._timer.isActive()

    def interval_ms(self) -> int:
        # 1 -> 1500 мс, 100 -> ~30 мс
        return int(1500 * (0.961 ** self.speed_slider.value()))

    def _on_speed_changed(self, _value):
        if self._timer.isActive():
            self._timer.setInterval(self.interval_ms())

    def _on_tick(self):
        self.step_forward()
        if self._player.finished:
            self.stop()

    def toggle_play(self):
        if self._timer.isActive():
            self.stop()
            return
        if self._player.finished:
            self._player.reset()
        self._timer.start(self.interval_ms())
        self.play_btn.setText("⏸ Пауза")
        self.playingChanged.emit(True)
        self.update_buttons()

    def stop(self):
        was_playing = self._timer.isActive()
        self._timer.stop()
        self.play_btn.setText("▶ Старт")
        if was_playing:
            self.playingChanged.emit(False)
        self.update_buttons()

    def step_forward(self):
        self._player.next()
        self.stepChanged.emit()
        self.update_buttons()

    def step_back(self):
        self._player.previous()
        self.stepChanged.emit()
        self.update_buttons()

    def reset(self):
        self.stop()
        self._player.reset()
        self.stepChanged.emit()
        self.update_buttons()

    def update_buttons(self):
        has_steps = self._player.total > 0
        self.back_btn.setEnabled(self._player.index >= 0)
        self.step_btn.setEnabled(has_steps and not self._player.finished)
        self.play_btn.setEnabled(has_steps)
        self.reset_btn.setEnabled(has_steps)
