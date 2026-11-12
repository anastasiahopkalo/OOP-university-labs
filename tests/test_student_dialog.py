"""GUI-тести профілів студентів: діалог і перемикання в головному вікні."""
import pytest

from src.core.analytics import ProgressTracker
from src.core.exercise import ExerciseResult
from src.database import JsonProgressRepository, SqlProgressRepository


@pytest.fixture
def repo(make_db):
    r = SqlProgressRepository(make_db())
    t = ProgressTracker("Анастасія")
    t.record_attempt("Максимальний елемент", ExerciseResult(True, 100, "", 0.1))
    r.save(t)
    r.create_student("Даніїл")
    return r


@pytest.fixture
def dialog(app, repo):
    from src.gui.student_dialog import StudentDialog
    return StudentDialog(repo, "Анастасія", confirm=lambda name: True)


class TestStudentDialog:
    def test_lists_students_and_marks_current(self, dialog):
        assert dialog.students() == ["Анастасія", "Даніїл"]
        assert "поточний" in dialog.list_widget.item(0).text()
        assert dialog.current_name() == "Анастасія"
        assert not dialog.delete_btn.isEnabled()  # поточного видаляти не можна

    def test_create(self, dialog, repo):
        dialog.name_input.setText("  Олег ")
        dialog.create()
        assert repo.list_students() == ["Анастасія", "Даніїл", "Олег"]
        assert dialog.current_name() == "Олег"
        assert dialog.name_input.text() == ""

    @pytest.mark.parametrize("name", ["", "Даніїл"])
    def test_create_errors_are_shown(self, dialog, repo, name):
        dialog.name_input.setText(name)
        dialog.create()
        assert dialog.error_label.text()
        assert len(repo.list_students()) == 2

    def test_delete(self, dialog, repo):
        dialog.list_widget.setCurrentRow(1)
        assert dialog.delete_btn.isEnabled()
        dialog.delete_selected()
        assert repo.list_students() == ["Анастасія"]

    def test_delete_cancelled(self, app, repo):
        from src.gui.student_dialog import StudentDialog
        d = StudentDialog(repo, "Анастасія", confirm=lambda name: False)
        d.list_widget.setCurrentRow(1)
        d.delete_selected()
        assert len(repo.list_students()) == 2

    def test_cannot_delete_current(self, dialog, repo):
        dialog.list_widget.setCurrentRow(0)
        dialog.delete_selected()
        assert len(repo.list_students()) == 2

    def test_choose(self, dialog):
        dialog.list_widget.setCurrentRow(1)
        dialog.choose()
        assert dialog.selected_student == "Даніїл"
        assert dialog.result() == dialog.Accepted

    def test_works_with_json_repository(self, app, tmp_path):
        from src.gui.student_dialog import StudentDialog
        d = StudentDialog(JsonProgressRepository(tmp_path / "p.json"), "Студент")
        assert d.students() == ["Студент"]  # поточний показується, навіть якщо ще не збережений
        d.name_input.setText("Новий")
        d.create()
        assert "Новий" in d.students()


class TestMainWindowStudents:
    def test_title_and_switch_through_dialog(self, app, repo):
        from src.gui.main_window import MainWindow
        window = MainWindow(repo, student="Анастасія")
        assert window.windowTitle().endswith("— Анастасія")
        dialog = window.open_student_dialog()
        dialog.list_widget.setCurrentRow(1)
        dialog.choose()
        app.processEvents()
        assert window.student_name == "Даніїл"
        assert window.windowTitle().endswith("— Даніїл")
        assert "Даніїл" in window.dashboard_panel.title_label.text()
        dialog.close()

    def test_closing_dialog_keeps_student_and_refreshes_leaderboard(self, app, repo):
        from src.gui.main_window import MainWindow
        window = MainWindow(repo, student="Анастасія")
        dialog = window.open_student_dialog()
        dialog.name_input.setText("Олег")
        dialog.create()
        dialog.reject()
        app.processEvents()
        assert window.student_name == "Анастасія"
        assert window.dashboard_panel.leaderboard_table.rowCount() == 3

    def test_student_menu_action(self, app, repo):
        from src.gui.main_window import MainWindow
        window = MainWindow(repo, student="Анастасія")
        actions = [a.text() for a in window.menuBar().actions()[0].menu().actions()]
        assert "Студент…" in actions
