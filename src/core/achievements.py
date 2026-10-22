from dataclasses import dataclass
from typing import Callable, List

from src.core.analytics import ProgressTracker


@dataclass(frozen=True)
class Achievement:
    icon: str
    title: str
    description: str
    # Умова отримання: (трекер, кількість усіх вправ) -> bool
    condition: Callable[[ProgressTracker, int], bool]

    def is_unlocked(self, tracker: ProgressTracker, total_exercises: int) -> bool:
        return self.condition(tracker, total_exercises)


ACHIEVEMENTS: List[Achievement] = [
    Achievement("🚀", "Перший крок", "Зробити першу спробу",
                lambda t, n: t.total_attempts() >= 1),
    Achievement("✅", "Перший розв'язок", "Повністю розв'язати будь-яку вправу",
                lambda t, n: len(t.solved_exercises()) >= 1),
    Achievement("🎯", "З першої спроби", "Розв'язати вправу з першої ж спроби",
                lambda t, n: any(a[0]["passed"] for a in t.completed_exercises.values() if a)),
    Achievement("💪", "Наполегливість", "Зробити 10 спроб",
                lambda t, n: t.total_attempts() >= 10),
    Achievement("🔥", "Серія 3 дні", "Займатися 3 дні поспіль",
                lambda t, n: t.streak_days() >= 3),
    Achievement("🏆", "Половина шляху", "Розв'язати половину вправ",
                lambda t, n: n > 0 and len(t.solved_exercises()) * 2 >= n),
    Achievement("🎓", "Майстер алгоритмів", "Розв'язати всі вправи",
                lambda t, n: n > 0 and len(t.solved_exercises()) >= n),
]


def unlocked(tracker: ProgressTracker, total_exercises: int) -> List[Achievement]:
    return [a for a in ACHIEVEMENTS if a.is_unlocked(tracker, total_exercises)]
