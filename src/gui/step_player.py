from typing import List, Generic, TypeVar, Optional

S = TypeVar('S')


class StepPlayer(Generic[S]):
    """Програвач кроків алгоритму без залежності від Qt (тому його легко тестувати).

    Панелі GUI зберігають список кроків у StepPlayer і рухаються по ньому
    вперед/назад, а таймер Qt лише викликає next().
    """

    def __init__(self, steps: Optional[List[S]] = None):
        self._steps: List[S] = []
        self._index = -1
        self.load(steps or [])

    def load(self, steps: List[S]):
        self._steps = list(steps)
        self._index = -1

    @property
    def index(self) -> int:
        return self._index

    @property
    def total(self) -> int:
        return len(self._steps)

    @property
    def current(self) -> Optional[S]:
        if 0 <= self._index < len(self._steps):
            return self._steps[self._index]
        return None

    @property
    def finished(self) -> bool:
        return self._index >= len(self._steps) - 1

    @property
    def progress(self) -> float:
        """Частка пройдених кроків від 0.0 до 1.0."""
        if not self._steps:
            return 0.0
        return (self._index + 1) / len(self._steps)

    def next(self) -> Optional[S]:
        if not self.finished:
            self._index += 1
        return self.current

    def previous(self) -> Optional[S]:
        if self._index > -1:
            self._index -= 1
        return self.current

    def seek(self, index: int) -> Optional[S]:
        self._index = max(-1, min(index, len(self._steps) - 1))
        return self.current

    def reset(self):
        self._index = -1
