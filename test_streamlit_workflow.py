import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.db_helper import (
    init_db,
    seed_default_data,
    get_all_employees,
    get_employee_by_id,
    mark_attendance,
    end_attendance_period,
    get_all_tasks,
    get_absent_employees_with_tasks,
    find_best_replacement,
    confirm_task_reassignment,
    get_cycle_info,
    get_dashboard_metrics
)
from services.email_service import send_reassignment_email
from services.chatbot_service import build_digital_twin_context, query_workforce_x

class StreamlitWorkforceWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        seed_default_data()

    def test_01_nine_named_employees(self):
        """Verify the 9 employees with internal IDs A-I and respective display names."""
        employees = get_all_employees()
        self.assertEqual(len(employees), 9)
        
        expected_mapping = {
            "A": "Arjun",
            "B": "Priya",
            "C": "Karthik",
            "D": "Divya",
            "E": "Rahul",
            "F": "Sneha",
            "G": "Vikram",
            "H": "Ananya",
            "I": "Sanjay"
        }

        for emp in employees:
            self.assertEqual(emp["name"], expected_mapping[emp["id"]])
            self.assertEqual(emp["attendance_status"], "WAITING FOR ATTENDANCE")

    def test_02_attendance_flow_and_absence_detection(self):
        """
        Simulate hackathon attendance:
        - Check in A (Arjun), C (Karthik), D (Divya), E (Rahul), G (Vikram), H (Ananya), I (Sanjay).
        - Leave B (Priya) and F (Sneha) unchecked.
        - End attendance -> B and F become ABSENT.
        """
        for k in ["A", "C", "D", "E", "G", "H", "I"]:
            res = mark_attendance(k)
            self.assertIsNotNone(res)
            self.assertEqual(res["id"], k)

        # End attendance
        end_attendance_period()

        metrics = get_dashboard_metrics()
        self.assertEqual(metrics["present"], 7)
        self.assertEqual(metrics["absent"], 2)

        emp_b = get_employee_by_id("B")
        emp_f = get_employee_by_id("F")
        self.assertEqual(emp_b["attendance_status"], "ABSENT")
        self.assertEqual(emp_f["attendance_status"], "ABSENT")

    def test_03_smart_replacement_for_priya(self):
        """Verify Priya's 'Database Module' is smartly recommended to Vikram (G, 35% workload)."""
        # Mark all except B and F
        for k in ["A", "C", "D", "E", "G", "H", "I"]:
            mark_attendance(k)
        end_attendance_period()

        absent_tasks = get_absent_employees_with_tasks()
        self.assertGreaterEqual(len(absent_tasks), 1)

        # Find task for Priya
        priya_task = next(item for item in absent_tasks if item["absent_id"] == "B")
        self.assertEqual(priya_task["task_name"], "Database Module")
        self.assertEqual(priya_task["required_skill"], "Database")

        # Find best replacement
        rep_data = find_best_replacement(priya_task["required_skill"], "B")
        self.assertIsNotNone(rep_data)
        best_candidate = rep_data["candidate"]
        
        # Vikram (G) has Database skill and 35% workload
        self.assertEqual(best_candidate["id"], "G")
        self.assertEqual(best_candidate["name"], "Vikram")
        self.assertEqual(best_candidate["workload"], 35)

        # Confirm reassignment
        reassign_id = confirm_task_reassignment(
            task_id=priya_task["task_id"],
            absent_emp_id="B",
            replacement_emp_id="G",
            reason=rep_data["reason"]
        )
        self.assertIsNotNone(reassign_id)

    def test_04_email_service_and_digital_twin(self):
        """Verify email function structure, digital twin context string, and Ollama fallback."""
        email_res = send_reassignment_email(
            sender_email="test@gmail.com",
            app_password="test_password_123",
            target_recipient="manager@enterprise.com",
            absent_employee_id="B",
            halted_task="Database Module",
            replacement_id="G"
        )
        # Should not crash, returns dict with success boolean
        self.assertIn("success", email_res)

        # Test Digital Twin context builder
        context = build_digital_twin_context()
        self.assertIn("Arjun", context)
        self.assertIn("Priya", context)
        self.assertIn("Vikram", context)

        # Test chatbot query with offline fallback
        bot_response = query_workforce_x("Who is absent?")
        self.assertTrue(len(bot_response) > 0)

if __name__ == "__main__":
    unittest.main()
