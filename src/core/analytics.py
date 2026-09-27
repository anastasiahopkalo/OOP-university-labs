from datetime import datetime


class ProgressTracker:
    def __init__(self, student_name: str):
        self.student_name = student_name
        self.completed_exercises = {}
        self.total_time = 0.0

    def record_attempt(self, exercise_name: str, result):
        if exercise_name not in self.completed_exercises:
            self.completed_exercises[exercise_name] = []

        self.completed_exercises[exercise_name].append({
            "passed": result.passed,
            "score": result.score,
            "time": result.execution_time,
            "timestamp": datetime.now()
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
            "completion_rate": f"{(completed / total * 100):.1f}%" if total > 0 else "0%"
        }