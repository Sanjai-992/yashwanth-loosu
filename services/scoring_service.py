from database.models import PerformanceHistory, Skill, Employee
from config import Config

class ScoringService:
    @staticmethod
    def get_historical_performance(employee_id: int) -> float:
        """
        Dynamically calculates the average historical performance score
        from the performance_history table. Returns 0-100 float.
        """
        records = PerformanceHistory.query.filter_by(employee_id=employee_id).all()
        if not records:
            return 75.0  # Baseline for employees with no prior recorded tasks
        avg_score = sum(r.performance_score for r in records) / len(records)
        return round(avg_score, 1)

    @staticmethod
    def get_skill_score(employee_id: int, required_skill: str) -> float:
        """
        Finds the employee's skill level for the specified skill name.
        Returns 0-100 float.
        """
        skill = Skill.query.filter_by(employee_id=employee_id, skill_name=required_skill).first()
        if not skill:
            return 0.0
        return float(skill.skill_level)

    @staticmethod
    def calculate_workload_capacity_score(current_workload: int, max_workload: int) -> float:
        """
        Calculates workload capacity score:
        Capacity = (max_workload - current_workload) / max_workload * 100
        e.g. 40/80 -> (80-40)/80 * 100 = 50% capacity -> scaled to 0-100.
        Guideline:
        40/80 (50% used) -> high capacity (score 50.0)
        50/80 (62.5% used) -> good capacity (score 37.5)
        60/80 (75% used) -> medium capacity (score 25.0)
        70/80 (87.5% used) -> low capacity (score 12.5)
        >= 80 (100% used) -> 0 capacity
        """
        if max_workload <= 0:
            return 0.0
        remaining = max(0, max_workload - current_workload)
        capacity_score = (remaining / max_workload) * 100.0
        return round(capacity_score, 1)

    @staticmethod
    def calculate_availability_score(availability_status: str) -> float:
        """
        Available -> 100.0
        Busy/Other -> 50.0
        Absent/Unavailable -> 0.0
        """
        if availability_status == "Available":
            return 100.0
        elif availability_status == "Busy":
            return 50.0
        return 0.0

    @classmethod
    def calculate_candidate_score(cls, employee: Employee, required_skill: str, min_skill_level: int) -> dict:
        """
        Calculates the candidate score using the exact formula:
        final_score = (skill_score * 0.40) + (performance_score * 0.30) + 
                      (workload_capacity_score * 0.20) + (availability_score * 0.10)
        """
        skill_score = cls.get_skill_score(employee.id, required_skill)
        performance_score = cls.get_historical_performance(employee.id)
        workload_capacity_score = cls.calculate_workload_capacity_score(
            employee.current_workload, employee.maximum_workload
        )
        availability_score = cls.calculate_availability_score(employee.availability_status)

        final_score = (
            (skill_score * Config.WEIGHT_SKILL) +
            (performance_score * Config.WEIGHT_PERFORMANCE) +
            (workload_capacity_score * Config.WEIGHT_WORKLOAD) +
            (availability_score * Config.WEIGHT_AVAILABILITY)
        )

        return {
            "skill_score": round(skill_score, 1),
            "performance_score": round(performance_score, 1),
            "workload_capacity_score": round(workload_capacity_score, 1),
            "availability_score": round(availability_score, 1),
            "final_score": round(final_score, 1),
            "weights": {
                "skill": Config.WEIGHT_SKILL,
                "performance": Config.WEIGHT_PERFORMANCE,
                "workload": Config.WEIGHT_WORKLOAD,
                "availability": Config.WEIGHT_AVAILABILITY
            }
        }
