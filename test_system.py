import unittest
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app
from database.database import db
from database.models import Employee, Task, Attendance, Reassignment
from database.seed import seed_database
from services.reassignment_service import ReassignmentService

class RfidAttendanceWorkflowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.app.app_context():
            seed_database()

    def test_01_nine_employees_initial_state(self):
        """Verify all 9 employees (A through I) are initialized in 'Waiting for Attendance' state."""
        with self.app.app_context():
            employees = Employee.query.order_by(Employee.name.asc()).all()
            self.assertEqual(len(employees), 9)
            names = [e.name for e in employees]
            self.assertEqual(names, ["A", "B", "C", "D", "E", "F", "G", "H", "I"])

            for emp in employees:
                self.assertEqual(emp.attendance_status, "Waiting for Attendance")
                self.assertEqual(emp.rfid_key, emp.name)

    def test_02_hackathon_demo_workflow(self):
        """
        Executes the exact hackathon demo flow:
        1. Press A, C, D, E, G, H, I keys -> Marked PRESENT.
        2. Do not press B and F -> Remain unverified.
        3. End attendance -> B and F become ABSENT.
        4. B's task ('Database Module') automatically reassigned to G (Database, 35% workload).
        5. Trigger email dispatch simulation.
        """
        # Step 1: Scan A, C, D, E, G, H, I
        present_keys = ["A", "C", "D", "E", "G", "H", "I"]
        for k in present_keys:
            res = self.client.post("/api/attendance", json={"key": k})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["employee"]["attendance_status"], "PRESENT")

        # Step 2: Verify B and F are still waiting
        with self.app.app_context():
            emp_b = Employee.query.filter_by(name="B").first()
            emp_f = Employee.query.filter_by(name="F").first()
            self.assertEqual(emp_b.attendance_status, "Waiting for Attendance")
            self.assertEqual(emp_f.attendance_status, "Waiting for Attendance")

        # Step 3: End Attendance Period
        end_res = self.client.post("/api/attendance/end")
        self.assertEqual(end_res.status_code, 200)
        end_data = end_res.get_json()

        self.assertEqual(end_data["metrics"]["present"], 7)
        self.assertEqual(end_data["metrics"]["absent"], 2)
        self.assertGreaterEqual(end_data["metrics"]["reassigned"], 1)

        # Step 4: Verify Database Module reassigned to G
        with self.app.app_context():
            task_db = Task.query.filter_by(task_name="Database Module").first()
            self.assertIsNotNone(task_db)
            self.assertEqual(task_db.assigned_employee, "G")
            self.assertEqual(task_db.status, "Reassigned")

            # Check reassignment log
            reassign_b = Reassignment.query.filter_by(absent_employee="B").first()
            self.assertIsNotNone(reassign_b)
            self.assertEqual(reassign_b.new_employee, "G")
            self.assertIn("Database", reassign_b.reason)

            # Step 5: Test send email
            email_res = self.client.post("/api/send-email", json={"reassignment_id": reassign_b.id})
            self.assertEqual(email_res.status_code, 200)
            email_data = email_res.get_json()
            self.assertEqual(email_data["email"]["status"], "Email Sent ✓")

    def test_03_dashboard_and_reset(self):
        """Test summary dashboard metrics and reset functionality."""
        dash = self.client.get("/api/dashboard").get_json()
        self.assertEqual(dash["metrics"]["total"], 9)

        reset = self.client.post("/api/reset").get_json()
        self.assertEqual(reset["status"], "success")

if __name__ == "__main__":
    unittest.main()
