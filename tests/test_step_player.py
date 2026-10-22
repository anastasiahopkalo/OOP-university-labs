from src.gui.step_player import StepPlayer


class TestStepPlayer:
    def test_empty(self):
        player = StepPlayer()
        assert player.current is None
        assert player.finished
        assert player.progress == 0.0
        assert player.next() is None

    def test_forward_and_back(self):
        player = StepPlayer(["a", "b", "c"])
        assert player.current is None and player.index == -1
        assert player.next() == "a"
        assert player.next() == "b"
        assert player.previous() == "a"
        assert player.previous() is None
        assert player.previous() is None
        assert player.index == -1

    def test_finish_and_progress(self):
        player = StepPlayer([1, 2, 3, 4])
        for _ in range(10):
            player.next()
        assert player.finished
        assert player.current == 4
        assert player.progress == 1.0

    def test_seek_is_clamped(self):
        player = StepPlayer([1, 2, 3])
        assert player.seek(100) == 3
        assert player.seek(-50) is None
        assert player.seek(1) == 2

    def test_reset_and_load(self):
        player = StepPlayer([1, 2])
        player.next()
        player.reset()
        assert player.index == -1
        player.load([9])
        assert player.total == 1 and player.next() == 9
