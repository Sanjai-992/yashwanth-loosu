import sqlite3
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "workforce.db"

# Employee mapping specification:
# Internal ID / Key: A to I
# Display Name: Arjun, Priya, Karthik, Divya, Rahul, Sneha, Vikram, Ananya, Sanjay
EMPLOYEE_SEEDS = [
    {"id": "A", "name": "Arjun",   "key": "A", "role": "Web Developer",         "skill": "Web Development", "workload": 30, "status": "Available", "task": "Web Portal Setup",       "required_role": "Web Developer"},
    {"id": "B", "name": "Priya",   "key": "B", "role": "Database Engineer",     "skill": "Database",        "workload": 80, "status": "Busy",      "task": "Database Module",         "required_role": "Database Engineer"},
    {"id": "C", "name": "Karthik", "key": "C", "role": "Python Developer",      "skill": "Python",          "workload": 40, "status": "Available", "task": "API Integration",         "required_role": "Python Developer"},
    {"id": "D", "name": "Divya",   "key": "D", "role": "QA Automation Engineer", "skill": "Testing",         "workload": 60, "status": "Available", "task": "QA Automation",           "required_role": "QA Automation Engineer"},
    {"id": "E", "name": "Rahul",   "key": "E", "role": "Frontend Developer",    "skill": "Frontend",        "workload": 25, "status": "Available", "task": "UI Dashboard",           "required_role": "Frontend Developer"},
    {"id": "F", "name": "Sneha",   "key": "F", "role": "Backend Architect",     "skill": "Backend",         "workload": 90, "status": "Busy",      "task": "Microservices Auth",      "required_role": "Backend Architect"},
    {"id": "G", "name": "Vikram",  "key": "G", "role": "Database Engineer",     "skill": "Database",        "workload": 35, "status": "Available", "task": "DB Optimization",         "required_role": "Database Engineer"},
    {"id": "H", "name": "Ananya",  "key": "H", "role": "Performance Engineer",  "skill": "Testing",         "workload": 50, "status": "Available", "task": "Load Testing",           "required_role": "Performance Engineer"},
    {"id": "I", "name": "Sanjay",  "key": "I", "role": "Fullstack Developer",   "skill": "Web Development", "workload": 20, "status": "Available", "task": "Landing Page",           "required_role": "Fullstack Developer"},
]

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(drop_first=False):
    """Creates tables, optionally dropping them first."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if drop_first:
            cursor.execute("DROP TABLE IF EXISTS employees")
            cursor.execute("DROP TABLE IF EXISTS tasks")
            cursor.execute("DROP TABLE IF EXISTS attendance")
            cursor.execute("DROP TABLE IF EXISTS reassignments")
            cursor.execute("DROP TABLE IF EXISTS cycle_meta")
            conn.commit()

        # 1. Employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rfid_key TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Engineer',
                skill TEXT NOT NULL,
                workload INTEGER NOT NULL DEFAULT 30,
                status TEXT NOT NULL DEFAULT 'Available',
                attendance_status TEXT NOT NULL DEFAULT 'WAITING FOR ATTENDANCE',
                attendance_time TEXT,
                last_reset_time TEXT
            )
        """)

        # 2. Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                assigned_employee_id TEXT NOT NULL,
                required_skill TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active'
            )
        """)

        # 3. Attendance log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                date TEXT NOT NULL,
                attendance_time TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        # 4. Reassignments history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reassignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                absent_employee_id TEXT NOT NULL,
                replacement_employee_id TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                reason TEXT NOT NULL,
                email_sent INTEGER DEFAULT 0
            )
        """)

        # 5. Metadata table for 24-hour cycle tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cycle_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()

def init_db():
    """Initializes the database schema and seeds initial data if table is empty."""
    create_tables(drop_first=False)
    with get_connection() as conn:
        count = conn.cursor().execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count == 0:
            seed_default_data()

def seed_default_data():
    """Resets / seeds the 9 employees and their tasks in WAITING FOR ATTENDANCE state."""
    create_tables(drop_first=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Insert employees
        for emp in EMPLOYEE_SEEDS:
            cursor.execute("""
                INSERT INTO employees (id, name, rfid_key, role, skill, workload, status, attendance_status, attendance_time, last_reset_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'WAITING FOR ATTENDANCE', NULL, ?)
            """, (emp["id"], emp["name"], emp["key"], emp.get("role", "Engineer"), emp["skill"], emp["workload"], emp["status"], now_str))

        # Insert tasks
        for emp in EMPLOYEE_SEEDS:
            cursor.execute("""
                INSERT INTO tasks (task_name, assigned_employee_id, required_skill, status)
                VALUES (?, ?, ?, 'Active')
            """, (emp["task"], emp["id"], emp["skill"]))

        # Set 24h cycle start
        cursor.execute("""
            INSERT OR REPLACE INTO cycle_meta (key, value)
            VALUES ('cycle_start_time', ?)
        """, (now_str,))
        
        conn.commit()

def get_all_employees():
    """Retrieves all 9 employees with their current active task name."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, t.task_name as current_task
            FROM employees e
            LEFT JOIN tasks t ON e.id = t.assigned_employee_id AND t.status IN ('Active', 'Reassigned')
            ORDER BY e.id ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_employee_by_id(emp_id):
    """Retrieves a single employee by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def mark_attendance(key_or_id):
    """Marks an employee as PRESENT based on keypress or ID."""
    key = key_or_id.strip().upper()
    now_dt = datetime.now()
    date_str = now_dt.strftime("%Y-%m-%d")
    time_str = now_dt.strftime("%I:%M:%S %p")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE id = ? OR rfid_key = ?", (key, key))
        emp = cursor.fetchone()

        if not emp:
            return None

        # Update employee status
        cursor.execute("""
            UPDATE employees 
            SET attendance_status = 'PRESENT', attendance_time = ?
            WHERE id = ?
        """, (time_str, emp["id"]))

        # Record in attendance log
        cursor.execute("""
            INSERT INTO attendance (employee_id, employee_name, date, attendance_time, status)
            VALUES (?, ?, ?, ?, 'Present')
        """, (emp["id"], emp["name"], date_str, time_str))

        emp_dict = dict(emp)
        conn.commit()
        return {
            "id": emp_dict["id"],
            "name": emp_dict["name"],
            "key": emp_dict["rfid_key"],
            "role": emp_dict.get("role", "Engineer"),
            "skill": emp_dict["skill"],
            "time": time_str,
            "status": "PRESENT"
        }

def end_attendance_period():
    """Finalizes attendance: all employees still 'WAITING' are marked ABSENT."""
    now_dt = datetime.now()
    date_str = now_dt.strftime("%Y-%m-%d")
    time_str = now_dt.strftime("%I:%M:%S %p")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM employees WHERE attendance_status = 'WAITING FOR ATTENDANCE'")
        waiting_emps = cursor.fetchall()

        for emp in waiting_emps:
            cursor.execute("""
                UPDATE employees 
                SET attendance_status = 'ABSENT' 
                WHERE id = ?
            """, (emp["id"],))

            cursor.execute("""
                INSERT INTO attendance (employee_id, employee_name, date, attendance_time, status)
                VALUES (?, ?, ?, ?, 'Absent')
            """, (emp["id"], emp["name"], date_str, time_str))

        conn.commit()

def get_all_tasks():
    """Retrieves all tasks with assignee details."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, e.name as assigned_employee_name, e.role as assigned_employee_role
            FROM tasks t
            LEFT JOIN employees e ON t.assigned_employee_id = e.id
            ORDER BY t.id ASC
        """)
        return [dict(r) for r in cursor.fetchall()]

def get_absent_employees_with_tasks():
    """Finds all absent employees who have active assigned tasks."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id as absent_id, e.name as absent_name, e.role as absent_role, 
                   e.skill as absent_skill, e.workload as absent_workload,
                   t.id as task_id, t.task_name, t.required_skill
            FROM employees e
            JOIN tasks t ON e.id = t.assigned_employee_id
            WHERE e.attendance_status = 'ABSENT' AND t.status = 'Active'
        """)
        return [dict(r) for r in cursor.fetchall()]

def find_best_replacement(required_skill, absent_emp_id):
    """
    Calculates eligible replacement rankings based on:
    - Skill Match (100% exact, 80% related, 50% partial)
    - Role Match (YES, PARTIAL, NO)
    - Availability & Present status
    - Workload bandwidth score
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM employees
            WHERE attendance_status = 'PRESENT'
              AND id != ?
        """, (absent_emp_id,))
        present_emps = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM employees WHERE id = ?", (absent_emp_id,))
        absent_row = cursor.fetchone()
        absent_emp = dict(absent_row) if absent_row else None

        if not present_emps:
            return None

        ranked = []
        for emp in present_emps:
            # 1. Skill Match
            if emp["skill"].lower() == required_skill.lower():
                skill_match = 100
                skill_label = "100%"
            elif any(rel in emp["skill"].lower() for rel in ["python", "backend", "database", "web"]):
                skill_match = 80
                skill_label = "80%"
            else:
                skill_match = 50
                skill_label = "50%"

            # 2. Role Match
            absent_role = (absent_emp.get("role") or "").lower()
            cand_role = (emp.get("role") or "").lower()
            if absent_role and cand_role and absent_role == cand_role:
                role_match = "YES"
                role_reason = "Exact role alignment"
            elif any(w in cand_role for w in ["developer", "engineer", "architect"]) and any(w in absent_role for w in ["developer", "engineer", "architect"]):
                role_match = "PARTIAL"
                role_reason = "Related engineering domain"
            else:
                role_match = "NO"
                role_reason = "Cross-functional domain"

            # 3. Score calculation
            # Score = (Skill * 0.5) + ((100 - Workload) * 0.35) + Role Bonus (15/8/0)
            role_bonus = 15 if role_match == "YES" else (8 if role_match == "PARTIAL" else 0)
            score = int((skill_match * 0.5) + ((100 - emp["workload"]) * 0.35) + role_bonus)

            ranked.append({
                "id": emp["id"],
                "name": emp["name"],
                "role": emp.get("role", "Engineer"),
                "skill": emp["skill"],
                "workload": emp["workload"],
                "attendance_status": emp["attendance_status"],
                "availability": "YES",
                "skill_match": skill_label,
                "skill_pct": skill_match,
                "role_match": role_match,
                "role_reason": role_reason,
                "score": score
            })

        # Sort by score descending
        ranked.sort(key=lambda x: x["score"], reverse=True)
        best = ranked[0]

        reason = (
            f"{best['name']} possesses the verified required skill ({required_skill}), "
            f"matches role requirements ({best['role_match']}), is currently PRESENT, "
            f"and maintains the lowest workload ({best['workload']}%) with highest composite fit score ({best['score']}/100)."
        )

        return {
            "candidate": best,
            "reason": reason,
            "all_candidates": ranked,
            "absent_emp": absent_emp
        }

def confirm_task_reassignment(task_id, absent_emp_id, replacement_emp_id, reason):
    """
    Confirms the reassignment:
    - Updates task assigned_employee_id
    - Updates replacement employee workload (+15%)
    - Records entry in reassignments table
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get task name
        cursor.execute("SELECT task_name FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        task_name = task["task_name"] if task else "Task"

        # Update task
        cursor.execute("""
            UPDATE tasks
            SET assigned_employee_id = ?, status = 'Reassigned'
            WHERE id = ?
        """, (replacement_emp_id, task_id))

        # Update replacement workload
        cursor.execute("""
            UPDATE employees
            SET workload = MIN(100, workload + 15)
            WHERE id = ?
        """, (replacement_emp_id,))

        # Record reassignment
        cursor.execute("""
            INSERT INTO reassignments (absent_employee_id, replacement_employee_id, task_id, task_name, timestamp, reason, email_sent)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (absent_emp_id, replacement_emp_id, task_id, task_name, now_str, reason))
        
        reassign_id = cursor.lastrowid
        conn.commit()
        return reassign_id

def mark_email_sent(reassign_id):
    """Updates the reassignments record to mark email as sent."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reassignments SET email_sent = 1 WHERE id = ?", (reassign_id,))
        conn.commit()

def get_reassignments_history():
    """Retrieves all reassignments with employee display names."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, 
                   e_abs.name as absent_name, 
                   e_rep.name as replacement_name,
                   e_rep.workload as replacement_workload
            FROM reassignments r
            LEFT JOIN employees e_abs ON r.absent_employee_id = e_abs.id
            LEFT JOIN employees e_rep ON r.replacement_employee_id = e_rep.id
            ORDER BY r.id DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

def get_cycle_info():
    """Returns the 24-hour cycle start time and computes elapsed time / time remaining."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM cycle_meta WHERE key = 'cycle_start_time'")
        row = cursor.fetchone()
        
        if not row:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT OR REPLACE INTO cycle_meta (key, value) VALUES ('cycle_start_time', ?)", (now_str,))
            conn.commit()
            cycle_start = datetime.now()
        else:
            try:
                cycle_start = datetime.strptime(row["value"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                cycle_start = datetime.now()

        cycle_end = cycle_start + timedelta(hours=24)
        now = datetime.now()
        
        # Check if 24 hours have elapsed
        if now >= cycle_end:
            # Auto-reset cycle
            reset_24h_cycle()
            cycle_start = datetime.now()
            cycle_end = cycle_start + timedelta(hours=24)

        remaining = max(timedelta(0), cycle_end - now)
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_remaining_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return {
            "start_time": cycle_start.strftime("%H:%M"),
            "end_time": cycle_end.strftime("%H:%M"),
            "time_remaining": time_remaining_str,
            "seconds_remaining": int(remaining.total_seconds())
        }

def reset_24h_cycle():
    """
    Resets the current 24-hour attendance cycle:
    - All employees return to 'WAITING FOR ATTENDANCE'
    - Historical attendance records remain preserved
    - New cycle start timestamp is recorded
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees
            SET attendance_status = 'WAITING FOR ATTENDANCE', attendance_time = NULL
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO cycle_meta (key, value)
            VALUES ('cycle_start_time', ?)
        """, (now_str,))
        conn.commit()

def get_dashboard_metrics():
    """Aggregates real-time top-level metric counters."""
    with get_connection() as conn:
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        present = cursor.execute("SELECT COUNT(*) FROM employees WHERE attendance_status = 'PRESENT'").fetchone()[0]
        absent = cursor.execute("SELECT COUNT(*) FROM employees WHERE attendance_status = 'ABSENT'").fetchone()[0]
        reassigned = cursor.execute("SELECT COUNT(*) FROM reassignments").fetchone()[0]
        
        # Calculate workforce utilization (average workload)
        cursor.execute("SELECT AVG(workload) FROM employees")
        avg_workload = cursor.fetchone()[0] or 0.0

        return {
            "total": total,
            "present": present,
            "absent": absent,
            "reassigned": reassigned,
            "utilization": round(float(avg_workload), 1)
        }
