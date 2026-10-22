"""Тести вкладки «Графи» і віджета PlaybackBar (без дисплея)."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PyQt5.QtWidgets")

from src.gui.step_player import StepPlayer  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def panel(app):
    from src.gui.panels.graph_panel import GraphPanel
    return GraphPanel()


def run_to_end(panel):
    while not panel._player.finished:
        panel.playback.step_forward()


class TestPlaybackBar:
    def test_buttons_follow_player(self, app):
        from src.gui.widgets.playback_bar import PlaybackBar
        player = StepPlayer([1, 2])
        bar = PlaybackBar(player)
        assert not bar.back_btn.isEnabled() and bar.step_btn.isEnabled()
        bar.step_forward()
        bar.step_forward()
        assert player.finished and not bar.step_btn.isEnabled()
        bar.step_back()
        assert player.index == 0
        bar.reset()
        assert player.index == -1

    def test_play_pause_emits(self, app):
        from src.gui.widgets.playback_bar import PlaybackBar
        bar = PlaybackBar(StepPlayer([1, 2, 3]))
        states = []
        bar.playingChanged.connect(states.append)
        bar.toggle_play()
        assert bar.is_playing
        bar.toggle_play()
        assert states == [True, False]

    def test_empty_player_disables_play(self, app):
        from src.gui.widgets.playback_bar import PlaybackBar
        bar = PlaybackBar(StepPlayer())
        assert not bar.play_btn.isEnabled()


class TestGraphPanel:
    def test_example_loaded(self, panel):
        assert panel.graph.size == 7
        assert panel.start_combo.count() == 7
        assert panel._player.total > 0

    def test_bfs_order(self, panel):
        run_to_end(panel)
        assert panel._player.current.visited == ["A", "B", "C", "D", "E", "F", "G"]
        assert panel.table.rowCount() == 7

    def test_dijkstra_path_on_click(self, panel):
        panel.algo_combo.setCurrentIndex(2)
        run_to_end(panel)
        panel._on_vertex_clicked("G")
        assert panel._player.current.distances["G"] == 14
        assert frozenset(("F", "G")) in panel.canvas._path_edges

    def test_click_empty_adds_vertex(self, panel):
        panel.clear_graph()
        panel._on_empty_clicked(0.2, 0.3)
        panel._on_empty_clicked(0.8, 0.3)
        assert panel.graph.vertices() == ["A", "B"]
        assert panel.positions["A"] == (0.2, 0.3)

    def test_two_clicks_add_edge(self, panel):
        panel.clear_graph()
        panel.add_vertex("X")
        panel.add_vertex("Y")
        panel.weight_spin.setValue(3)
        panel._on_vertex_clicked("X")
        panel._on_vertex_clicked("Y")
        assert panel.graph.weight("X", "Y") == 3
        assert panel._selected is None

    def test_same_vertex_twice_deselects(self, panel):
        panel._on_vertex_clicked("A")
        panel._on_vertex_clicked("A")
        assert panel._selected is None

    def test_remove_selected(self, panel):
        panel._on_vertex_clicked("G")
        panel.remove_selected()
        assert panel.graph.find("G") == -1
        assert "G" not in panel.positions

    def test_directed_toggle_keeps_edges(self, panel):
        edges = len(panel.graph.edges())
        panel.directed_check.setChecked(True)
        assert panel.graph.directed
        assert len(panel.graph.edges()) == edges
        assert panel.graph.has_edge("A", "B") and not panel.graph.has_edge("B", "A")

    def test_edge_from_inputs_creates_vertices(self, panel):
        panel.from_input.setText("P")
        panel.to_input.setText("Q")
        panel._add_edge_from_inputs()
        assert panel.graph.has_edge("P", "Q")

    def test_next_vertex_name_skips_used(self, panel):
        assert panel.next_vertex_name() == "H"

    def test_editing_disabled_while_playing(self, panel):
        panel.playback.toggle_play()
        assert not panel.algo_combo.isEnabled()
        panel._on_empty_clicked(0.5, 0.5)
        assert panel.graph.size == 7
        panel.playback.toggle_play()
        assert panel.algo_combo.isEnabled()
