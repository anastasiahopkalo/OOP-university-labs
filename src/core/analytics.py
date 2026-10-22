import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class ProgressTracker:
    def __init__(self, student_name: str):
        self.student_name = student_name
        # назва вправи -> список спроб (словники passed / score / time / timestamp)
        self.completed_exercises: Dict[str, List[dict]] = {}
        self.total_time = 0.0

    def record_attempt(self, exercise_name: str, result, timestamp: Optional[datetime] = None):
        if exercise_name not in self.completed_exercises:
            self.completed_exercises[exercise_name] = []

        self.completed_exercises[exercise_name].append({
            "passed": result.passed,
            "score": result.score,
            "time": result.execution_time,
            "timestamp": timestamp or datetime.now()
        })
        self.total_time += result.execution_time

    def get_statistics(self):
        completed = sum(1 for v in self.completed_exercises.values()
                        if v and v[-1]["passed"])
        total = len(self.completed_exercises)
        return {
            "student": self.student_name,
            "completed": completed,
            "total": total,
            "completion_rate": f"{(completed / total * 100):.1f}%" if total > 0 else "0%",
            "attempts": self.total_attempts(),
            "average_score": round(self.average_score(), 1),
            "streak_days": self.streak_days(),
        }

    # ---------- аналітика для дашборду ----------

    def history(self) -> List[dict]:
        """Усі спроби в хронологічному порядку, з назвою вправи."""
        records = [dict(attempt, exercise=name)
                   for name, attempts in self.completed_exercises.items()
                   for attempt in attempts]
        return sorted(records, key=lambda r: r["timestamp"])

    def best_score(self, exercise_name: str) -> Optional[int]:
        attempts = self.completed_exercises.get(exercise_name)
        return max(a["score"] for a in attempts) if attempts else None

    def best_scores(self) -> Dict[str, int]:
        return {name: self.best_score(name) for name in self.completed_exercises}

    def solved_exercises(self) -> List[str]:
        """Вправи, які хоча б раз розв'язано повністю."""
        return [name for name, attempts in self.completed_exercises.items()
                if any(a["passed"] for a in attempts)]

    def total_attempts(self) -> int:
        return sum(len(a) for a in self.completed_exercises.values())

    def average_score(self) -> float:
        scores = [a["score"] for a in self.history()]
        return sum(scores) / len(scores) if scores else 0.0

    def success_rate(self) -> float:
        """Частка успішних спроб від 0.0 до 1.0."""
        history = self.history()
        return sum(a["passed"] for a in history) / len(history) if history else 0.0

    def daily_activity(self) -> Dict[date, int]:
        activity: Dict[date, int] = {}
        for record in self.history():
            day = record["timestamp"].date()
            activity[day] = activity.get(day, 0) + 1
        return activity

    def streak_days(self, today: Optional[date] = None) -> int:
        """Скільки днів поспіль (до сьогодні або вчора включно) була хоча б одна спроба."""
        days = set(self.daily_activity())
        if not days:
            return 0
        current = today or date.today()
        if current not in days:
            current -= timedelta(days=1)
        streak = 0
        while current in days:
            streak += 1
            current -= timedelta(days=1)
        return streak

    # ---------- збереження ----------

    def to_dict(self) -> dict:
        return {
            "student_name": self.student_name,
            "total_time": self.total_time,
            "exercises": {
                name: [dict(a, timestamp=a["timestamp"].isoformat()) for a in attempts]
                for name, attempts in self.completed_exercises.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressTracker":
        tracker = cls(data.get("student_name", "Студент"))
        tracker.total_time = data.get("total_time", 0.0)
        for name, attempts in data.get("exercises", {}).items():
            tracker.completed_exercises[name] = [
                dict(a, timestamp=datetime.fromisoformat(a["timestamp"])) for a in attempts
            ]
        return tracker

    def save(self, path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path, student_name: str = "Студент") -> "ProgressTracker":
        """Завантажує прогрес з файлу; якщо файлу немає або він пошкоджений - новий трекер."""
        try:
            return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError, TypeError):
            return cls(student_name)
