"""Тести контролерів і вкладки «Структури даних» (без дисплея)."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PyQt5.QtWidgets")

from src.gui.structure_controllers import (  # noqa: E402
    parse_value, BSTController, HeapController, HashTableController,
    StackController, QueueController, LinkedListController,
)


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_parse_value():
    assert parse_value(" 42 ") == 42
    assert parse_value("-7") == -7
    assert parse_value("apple") == "apple"


class TestBSTController:
    @pytest.fixture
    def ctrl(self, app):
        c = BSTController()
        for v in [50, 30, 70, 60]:
            c.insert(v)
        return c

    def test_find_highlights_path(self, ctrl):
        message = ctrl.find(60)
        assert "Знайдено" in message
        assert ctrl.canvas._highlight == {50: "path", 70: "path", 60: "found"}

    def test_find_missing(self, ctrl):
        assert "Не знайдено" in ctrl.find(65)
        assert 65 not in ctrl.canvas._highlight

    def test_duplicate_and_delete(self, ctrl):
        assert "вже є" in ctrl.insert(50)
        assert ctrl.structure.size == 4
        ctrl.delete(30)
        assert ctrl.structure.get_all() == [50, 60, 70]
        assert "немає" in ctrl.delete(999)

    def test_layout_x_follows_inorder(self, ctrl):
        nodes = ctrl.canvas._layout()
        xs = [x for _, _, x, _, _ in sorted(nodes, key=lambda n: n[0])]
        assert xs == sorted(xs)


class TestHeapController:
    def test_min_heap_extracts_in_order(self, app):
        c = HeapController()
        for v in [5, 1, 4, 2]:
            c.insert(v)
        assert [c.delete() for _ in range(4)] == ["Видобуто 1", "Видобуто 2", "Видобуто 4", "Видобуто 5"]
        assert c.delete() == "Купа порожня"

    def test_max_heap_title_and_layout(self, app):
        c = HeapController(max_heap=True)
        for v in [1, 9, 3]:
            c.insert(v)
        assert c.structure.peek() == 9
        assert "max" in c.delete_text
        depths = [depth for _, _, _, depth, _ in c.canvas._layout()]
        assert depths == [0, 1, 1]


class TestHashTableController:
    def test_key_value_insert_and_find(self, app):
        c = HashTableController()
        c.insert("apple=5")
        assert c.structure.get("apple") == 5
        assert "значення: 5" in c.find("apple")
        assert c.canvas._highlight == {"apple": "found"}

    def test_resize_message(self, app):
        c = HashTableController()
        messages = [c.insert(i) for i in range(7)]
        assert any("розширено" in m for m in messages)

    def test_delete(self, app):
        c = HashTableController()
        c.insert("k")
        assert "Видалено" in c.delete("k")
        assert "немає" in c.delete("k")


class TestSequenceControllers:
    def test_stack(self, app):
        c = StackController()
        c.insert(1)
        c.insert(2)
        assert c.canvas._items == [2, 1]
        assert c.canvas._labels == {0: "top"}
        assert c.delete() == "Pop → 2"

    def test_queue_labels(self, app):
        c = QueueController()
        c.insert(1)
        assert c.canvas._labels == {0: "head / tail"}
        c.insert(2)
        assert c.canvas._labels == {0: "head", 1: "tail"}
        assert c.delete() == "Dequeue → 1"

    def test_linked_list_appends_and_deletes_by_value(self, app):
        c = LinkedListController()
        for v in [3, 1, 2]:
            c.insert(v)
        assert c.structure.get_all() == [3, 1, 2]
        c.delete(1)
        assert c.structure.get_all() == [3, 2]
        assert "немає" in c.delete(42)

    @pytest.mark.parametrize("cls", [StackController, QueueController, LinkedListController,
                                     BSTController, HeapController])
    def test_fill_random_and_clear(self, app, cls):
        c = cls()
        c.fill_random(5)
        assert c.structure.size > 0
        c.clear()
        assert c.structure.size == 0


class TestDataStructuresPanel:
    @pytest.fixture
    def panel(self, app):
        from src.gui.panels.data_structures_panel import DataStructuresPanel
        return DataStructuresPanel()

    def test_switching_updates_buttons(self, panel):
        titles = [panel.structure_combo.itemText(i) for i in range(panel.structure_combo.count())]
        panel.structure_combo.setCurrentIndex(titles.index("Стек (LIFO)"))
        assert panel.insert_btn.text() == "Push"
        assert panel.canvas_stack.currentWidget() is panel.controller.canvas

    def test_insert_via_input(self, panel):
        panel.value_input.setText("42")
        panel.insert()
        assert panel.controller.structure.get_all() == [42]
        assert panel.value_input.text() == ""
        assert "42" in panel.status_label.text()

    def test_non_numeric_rejected_for_bst(self, panel, monkeypatch):
        monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *a, **k: None)
        panel.value_input.setText("abc")
        panel.insert()
        assert panel.controller.structure.size == 0

    def test_pop_without_value(self, panel):
        panel.structure_combo.setCurrentIndex(1)  # Min-купа
        panel.value_input.setText("7")
        panel.insert()
        panel.delete()
        assert panel.controller.structure.size == 0
