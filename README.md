# Smart Employee Attendance & Automatic Task Reassignment System ⚡

A modern, clean, beginner-friendly web application for **RFID-Style Keyboard Employee Attendance and Automatic Task Reassignment**. 

Each employee is mapped to a dedicated keyboard key that acts as their personal RFID badge. When employees check in, the system marks them **PRESENT**. At the close of attendance, unverified employees become **ABSENT**, and their critical tasks are automatically analyzed, matched by skill, balanced by lowest workload, and reassigned to eligible present colleagues with simulated email dispatch.

---

## 👥 Employee Roster & RFID Keyboard Key Mapping

| Employee | RFID Key | Primary Skill | Initial Workload | Status | Default Assigned Task |
| :---: | :---: | :--- | :---: | :---: | :--- |
| **A** | <kbd>A</kbd> | Web Development | 30% | Available | Web Portal Setup |
| **B** | <kbd>B</kbd> | Database | 80% | Busy | Database Module |
| **C** | <kbd>C</kbd> | Python | 40% | Available | API Integration |
| **D** | <kbd>D</kbd> | Testing | 60% | Available | QA Automation |
| **E** | <kbd>E</kbd> | Frontend | 25% | Available | UI Dashboard |
| **F** | <kbd>F</kbd> | Backend | 90% | Busy | Microservices Auth |
| **G** | <kbd>G</kbd> | Database | 35% | Available | DB Optimization |
| **H** | <kbd>H</kbd> | Testing | 50% | Available | Load Testing |
| **I** | <kbd>I</kbd> | Web Development | 20% | Available | Landing Page |

---

## 🎯 Hackathon Demonstration Steps

1. **Step 1**: Start the application and open [http://127.0.0.1:5000](http://127.0.0.1:5000).
2. **Step 2**: All 9 employee cards show `Waiting for Attendance` (Orange badge).
3. **Step 3**: Press keyboard keys: <kbd>A</kbd>, <kbd>C</kbd>, <kbd>D</kbd>, <kbd>E</kbd>, <kbd>G</kbd>, <kbd>H</kbd>, and <kbd>I</kbd> (or click their on-screen keys).
   - Each pressed key turns green (`PRESENT` with attendance timestamp).
4. **Step 4**: Leave <kbd>B</kbd> and <kbd>F</kbd> unpressed.
5. **Step 5**: Click **"End Attendance Period"**.
6. **Step 6**: 
   - Employees **B** and **F** are automatically marked **🔴 ABSENT**.
   - The system detects **B**'s task **"Database Module"** (Required Skill: *Database*).
   - Evaluates present staff with *Database* skill → Finds **Employee G** (Skill: *Database*, Workload: *35%*).
   - Task **"Database Module"** is automatically reassigned to **Employee G**.
7. **Step 7**: 
   - View the generated **Task Reassignment Card** & **Email Notification Draft**.
   - Click **"Send Task Assignment Email"** to trigger simulated email delivery (`Email Sent ✓`).

---

## 🚀 Running on Windows

### Quick Launch
Double-click `run_app.bat` or execute in PowerShell:
```powershell
.\run_app.ps1
```

### Manual Execution
```powershell
cd smart-task-reassignment
python database/seed.py
python app.py
```

Open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📡 REST API Endpoints

- `POST /api/attendance` — Scans an RFID key (`{"key": "A"}`) and marks employee present.
- `POST /api/attendance/end` — Closes attendance, marks unverified employees absent, and triggers smart task reassignments.
- `GET /api/employees` — Retrieves all 9 employees with status, workload, and skill data.
- `GET /api/tasks` — Retrieves all tasks and assigned employees.
- `POST /api/send-email` — Simulates sending the task reassignment email notification.
- `POST /api/reset` — Resets the database to the initial clean attendance state.
