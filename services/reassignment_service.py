from datetime import datetime, timezone
from database.models import Employee, Task, Attendance, Reassignment
from database.database import db

def get_current_time_str():
    return datetime.now().strftime("%I:%M:%S %p")

def get_current_date_str():
    return datetime.now().strftime("%Y-%m-%d")

class ReassignmentService:
    @staticmethod
    def mark_attendance(key_or_name: str) -> dict:
        """
        Marks an employee as PRESENT when their RFID key is pressed/scanned.
        """
        key_clean = key_or_name.strip().upper()
        emp = Employee.query.filter(
            (Employee.rfid_key == key_clean) | (Employee.name == key_clean)
        ).first()

        if not emp:
            raise ValueError(f"No employee found with RFID/Key '{key_clean}'")

        time_str = get_current_time_str()
        date_str = get_current_date_str()

        emp.attendance_status = "PRESENT"
        emp.attendance_time = time_str

        # Add attendance log
        att = Attendance(
            employee_name=emp.name,
            date=date_str,
            time=time_str,
            status="Present"
        )
        db.session.add(att)
        db.session.commit()

        return {
            "status": "success",
            "message": f"Employee {emp.name} marked PRESENT",
            "employee": emp.to_dict()
        }

    @classmethod
    def end_attendance_and_reassign(cls) -> dict:
        """
        Concludes attendance period:
        1. Marks any remaining 'Waiting for Attendance' staff as ABSENT.
        2. Detects affected tasks assigned to absent staff.
        3. Identifies present employees with matching skills.
        4. Selects the lowest workload eligible employee for each task.
        5. Reassigns the task and prepares email notifications.
        """
        date_str = get_current_date_str()
        time_str = get_current_time_str()

        # Step 1: Mark absent employees
        unmarked = Employee.query.filter_by(attendance_status="Waiting for Attendance").all()
        for emp in unmarked:
            emp.attendance_status = "ABSENT"
            att = Attendance(
                employee_name=emp.name,
                date=date_str,
                time=time_str,
                status="Absent"
            )
            db.session.add(att)

        db.session.commit()

        # Step 2: Get all present employees
        present_employees = Employee.query.filter_by(attendance_status="PRESENT").all()
        absent_employees = Employee.query.filter_by(attendance_status="ABSENT").all()

        # Step 3: Find tasks belonging to absent employees
        reassignments_made = []
        email_drafts = []

        for absent_emp in absent_employees:
            # Find active tasks assigned to this absent employee
            tasks = Task.query.filter_by(assigned_employee=absent_emp.name, status="Active").all()

            for task in tasks:
                # Skill matching & workload selection
                # Priority: Present + Matching Skill + Lowest Workload
                matching_skilled_workers = [
                    p for p in present_employees 
                    if p.skill.lower() == task.required_skill.lower()
                ]

                # Sort matching skilled workers by workload ascending
                matching_skilled_workers.sort(key=lambda x: x.workload)

                selected_worker = None
                reason = ""

                if matching_skilled_workers:
                    selected_worker = matching_skilled_workers[0]
                    reason = f"Skill match '{task.required_skill}' with lowest available workload ({selected_worker.workload}%)"
                else:
                    # Fallback if no exact skill match exists among present staff:
                    # Choose present worker with lowest overall workload
                    sorted_present = sorted(present_employees, key=lambda x: x.workload)
                    if sorted_present:
                        selected_worker = sorted_present[0]
                        reason = f"Cross-functional coverage (Lowest workload: {selected_worker.workload}%)"

                if selected_worker:
                    old_workload = selected_worker.workload
                    new_workload = min(100, old_workload + 15)  # Task addition impact

                    # Update task assignment
                    task.assigned_employee = selected_worker.name
                    task.status = "Reassigned"

                    # Update worker workload
                    selected_worker.workload = new_workload

                    # Record reassignment
                    reassign_entry = Reassignment(
                        task_id=task.id,
                        task_name=task.task_name,
                        required_skill=task.required_skill,
                        absent_employee=absent_emp.name,
                        new_employee=selected_worker.name,
                        workload_before=old_workload,
                        workload_after=new_workload,
                        reason=reason,
                        email_sent=False
                    )
                    db.session.add(reassign_entry)
                    db.session.flush()

                    reassign_dict = reassign_entry.to_dict()
                    reassignments_made.append(reassign_dict)

                    # Build email notification template
                    email_draft = {
                        "reassignment_id": reassign_entry.id,
                        "absent_employee": absent_emp.name,
                        "new_employee": selected_worker.name,
                        "task_name": task.task_name,
                        "required_skill": task.required_skill,
                        "workload": old_workload,
                        "subject": "New Task Assigned Due to Employee Absence",
                        "body": (
                            f"Hello {selected_worker.name},\n\n"
                            f"Employee {absent_emp.name} is absent today.\n\n"
                            f"You have been selected to handle the following task:\n\n"
                            f"Task: {task.task_name}\n"
                            f"Required Skill: {task.required_skill}\n\n"
                            f"Your current workload: {old_workload}%\n\n"
                            f"Please complete the task according to the project schedule.\n\n"
                            f"Thank you."
                        ),
                        "status": "Ready to Send"
                    }
                    email_drafts.append(email_draft)

        db.session.commit()

        total_emp = Employee.query.count()
        total_present = Employee.query.filter_by(attendance_status="PRESENT").count()
        total_absent = Employee.query.filter_by(attendance_status="ABSENT").count()
        total_reassigned = len(reassignments_made)

        return {
            "status": "success",
            "message": f"Attendance finalized. {total_present} Present, {total_absent} Absent. {total_reassigned} task(s) reassigned.",
            "metrics": {
                "total": total_emp,
                "present": total_present,
                "absent": total_absent,
                "reassigned": total_reassigned
            },
            "reassignments": reassignments_made,
            "emails": email_drafts
        }

    @staticmethod
    def send_task_email(reassignment_id: int) -> dict:
        """
        Simulates sending the task reassignment notification email.
        """
        reassign = db.session.get(Reassignment, reassignment_id)
        if not reassign:
            raise ValueError(f"Reassignment record with ID {reassignment_id} not found.")

        reassign.email_sent = True
        db.session.commit()

        email_content = {
            "reassignment_id": reassign.id,
            "recipient": reassign.new_employee,
            "absent_employee": reassign.absent_employee,
            "task_name": reassign.task_name,
            "required_skill": reassign.required_skill,
            "workload": reassign.workload_before,
            "subject": "New Task Assigned Due to Employee Absence",
            "body": (
                f"Hello {reassign.new_employee},\n\n"
                f"Employee {reassign.absent_employee} is absent today.\n\n"
                f"You have been selected to handle the following task:\n\n"
                f"Task: {reassign.task_name}\n"
                f"Required Skill: {reassign.required_skill}\n\n"
                f"Your current workload: {reassign.workload_before}%\n\n"
                f"Please complete the task according to the project schedule.\n\n"
                f"Thank you."
            ),
            "status": "Email Sent ✓",
            "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        }

        return {
            "status": "success",
            "message": f"Task assignment email successfully sent to Employee {reassign.new_employee}!",
            "email": email_content
        }
