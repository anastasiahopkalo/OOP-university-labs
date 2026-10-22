"""Smoke-тести GUI. Працюють без дисплея завдяки платформі Qt "offscreen"."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PyQt5.QtWidgets")

from src.gui.styles import DARK, LIGHT  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def sorting_panel(app):
    from src.gui.panels.sorting_panel import SortingPanel
    panel = SortingPanel()
    panel.set_data([5, 1, 4, 2, 3])
    return panel


class TestSortingPanel:
    def test_steps_loaded(self, sorting_panel):
        assert sorting_panel._player.total > 0
        assert sorting_panel._player.index == -1

    def test_step_forward_back(self, sorting_panel):
        sorting_panel.step_forward()
        sorting_panel.step_forward()
        assert sorting_panel._player.index == 1
        sorting_panel.step_back()
        assert sorting_panel._player.index == 0

    def test_runs_to_sorted_result(self, sorting_panel):
        while not sorting_panel._player.finished:
            sorting_panel.step_forward()
        assert sorting_panel._player.current.snapshot == [1, 2, 3, 4, 5]
        assert not sorting_panel.step_btn.isEnabled()

    @pytest.mark.parametrize("index", range(5))
    def test_every_algorithm_sorts(self, sorting_panel, index):
        sorting_panel.algo_combo.setCurrentIndex(index)
        assert sorting_panel._player.seek(10**6).snapshot == [1, 2, 3, 4, 5]

    def test_play_pause(self, sorting_panel):
        sorting_panel.toggle_play()
        assert sorting_panel._timer.isActive()
        sorting_panel.toggle_play()
        assert not sorting_panel._timer.isActive()

    def test_custom_data(self, sorting_panel):
        sorting_panel.custom_input.setText("9, 8, 7")
        sorting_panel._apply_custom_data()
        assert sorting_panel._data == [9, 8, 7]

    def test_reset(self, sorting_panel):
        sorting_panel.step_forward()
        sorting_panel.reset()
        assert sorting_panel._player.index == -1


class TestMainWindow:
    def test_tabs_and_theme(self, app):
        from src.gui.main_window import MainWindow
        window = MainWindow()
        assert window.tabs.count() >= 5
        window.apply_theme(DARK)
        assert window.sorting_panel.canvas.theme is DARK
        window.apply_theme(LIGHT)
        assert window.sorting_panel.canvas.theme is LIGHT
