/**
 * Smart Employee Attendance & Task Reassignment System
 * Frontend Controller & Keyboard RFID Listener
 */

const App = {
    state: {
        employees: [],
        tasks: [],
        metrics: { total: 9, present: 0, absent: 0, reassigned: 0 },
        reassignments: [],
        emails: []
    },

    init() {
        this.bindEvents();
        this.loadDashboard();
    },

    bindEvents() {
        // Physical Keyboard Event Listener (Keys A to I)
        window.addEventListener("keydown", (e) => {
            const key = e.key.toUpperCase();
            if (["A", "B", "C", "D", "E", "F", "G", "H", "I"].includes(key)) {
                this.handleKeyPress(key);
            }
        });

        // Clickable On-Screen Key Buttons
        document.querySelectorAll(".key-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const key = btn.getAttribute("data-key");
                this.handleKeyPress(key);
            });
        });

        // End Attendance Button
        const endBtn = document.getElementById("btn-end-attendance");
        if (endBtn) {
            endBtn.addEventListener("click", () => {
                this.endAttendance();
            });
        }

        // Reset System Button
        const resetBtn = document.getElementById("btn-reset");
        if (resetBtn) {
            resetBtn.addEventListener("click", () => {
                this.resetSystem();
            });
        }
    },

    showToast(message, type = "info") {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span>${type === 'success' ? '✓' : 'ℹ️'}</span>
            <div>${message}</div>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    },

    async handleKeyPress(key) {
        // Highlight on-screen key button
        const keyEl = document.getElementById(`key-${key}`);
        if (keyEl) {
            keyEl.classList.add("active-key");
            setTimeout(() => keyEl.classList.remove("active-key"), 200);
        }

        try {
            const res = await fetch("/api/attendance", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ key: key })
            });

            const data = await res.json();
            if (data.status === "success") {
                const emp = data.employee;
                if (keyEl) {
                    keyEl.classList.add("key-checked");
                    keyEl.classList.remove("key-absent");
                }

                // Update live feedback banner
                const banner = document.getElementById("live-attendance-banner");
                banner.className = "live-banner banner-present";
                banner.innerHTML = `<span>🟢</span> <strong>RFID Scanned:</strong> Employee ${emp.name} marked PRESENT at ${emp.attendance_time}`;

                this.showToast(`Employee ${emp.name} marked PRESENT (${emp.attendance_time})`, "success");
                this.loadDashboard();
            }
        } catch (err) {
            console.error("Attendance scan failed:", err);
        }
    },

    async loadDashboard() {
        try {
            const [dashRes, empRes] = await Promise.all([
                fetch("/api/dashboard"),
                fetch("/api/employees")
            ]);

            const dashData = await dashRes.json();
            const empData = await empRes.json();

            if (dashData.status === "success") {
                const m = dashData.metrics;
                this.state.metrics = m;
                document.getElementById("metric-total").textContent = m.total;
                document.getElementById("metric-present").textContent = m.present;
                document.getElementById("metric-absent").textContent = m.absent;
                document.getElementById("metric-reassigned").textContent = m.reassigned;
            }

            if (empData.status === "success") {
                this.state.employees = empData.employees;
                this.renderEmployeeCards(empData.employees);
                this.renderWorkloadTable(empData.employees);
                this.updateKeypadState(empData.employees);
            }
        } catch (err) {
            console.error("Dashboard refresh error:", err);
        }
    },

    renderEmployeeCards(employees) {
        const container = document.getElementById("employee-cards-container");
        if (!container) return;

        container.innerHTML = employees.map(emp => {
            let badgeClass = "badge-pending";
            let statusText = "Waiting for Attendance";
            let dot = "⏳";

            if (emp.attendance_status === "PRESENT") {
                badgeClass = "badge-present";
                statusText = `PRESENT (${emp.attendance_time || 'Recorded'})`;
                dot = "🟢";
            } else if (emp.attendance_status === "ABSENT") {
                badgeClass = "badge-absent";
                statusText = "ABSENT";
                dot = "🔴";
            }

            let progressClass = "progress-green";
            if (emp.workload >= 75) progressClass = "progress-red";
            else if (emp.workload >= 50) progressClass = "progress-yellow";

            return `
                <div class="emp-card" id="card-${emp.name}">
                    <div class="emp-card-header">
                        <div class="emp-identity">
                            <div class="emp-avatar">${emp.name}</div>
                            <div class="emp-name-row">
                                <h3>Employee ${emp.name}</h3>
                                <span class="key-pill">RFID Key: [${emp.rfid_key}]</span>
                            </div>
                        </div>
                        <span class="badge ${badgeClass}">${dot} ${statusText}</span>
                    </div>

                    <div>
                        <div class="emp-meta-row" style="margin-bottom: 0.25rem;">
                            <span>Current Workload:</span>
                            <strong>${emp.workload}%</strong>
                        </div>
                        <div class="progress-wrap">
                            <div class="progress-fill ${progressClass}" style="width: ${emp.workload}%;"></div>
                        </div>
                    </div>

                    <div class="emp-meta-row">
                        <span>Skill:</span>
                        <strong>${emp.skill}</strong>
                    </div>

                    <div class="emp-meta-row">
                        <span>Current Task:</span>
                        <strong style="color: var(--primary);">${emp.current_task}</strong>
                    </div>

                    <div class="emp-meta-row">
                        <span>Status:</span>
                        <span><strong class="${emp.status === 'Available' ? 'text-success' : ''}">${emp.status}</strong></span>
                    </div>
                </div>
            `;
        }).join("");
    },

    renderWorkloadTable(employees) {
        const tbody = document.getElementById("workload-table-body");
        if (!tbody) return;

        const presentStaff = employees.filter(e => e.attendance_status === "PRESENT");
        
        if (presentStaff.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No employees marked PRESENT yet. Use keys A–I to record attendance.</td></tr>`;
            return;
        }

        tbody.innerHTML = presentStaff.map(emp => `
            <tr>
                <td><strong>Employee ${emp.name}</strong></td>
                <td><kbd>${emp.rfid_key}</kbd></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div class="progress-wrap" style="width: 70px;">
                            <div class="progress-fill ${emp.workload >= 75 ? 'progress-red' : (emp.workload >= 50 ? 'progress-yellow' : 'progress-green')}" style="width: ${emp.workload}%;"></div>
                        </div>
                        <strong>${emp.workload}%</strong>
                    </div>
                </td>
                <td>${emp.skill}</td>
                <td><span class="badge badge-info">${emp.status}</span></td>
                <td><strong>${emp.current_task}</strong></td>
            </tr>
        `).join("");
    },

    updateKeypadState(employees) {
        employees.forEach(emp => {
            const keyEl = document.getElementById(`key-${emp.name}`);
            if (!keyEl) return;

            if (emp.attendance_status === "PRESENT") {
                keyEl.classList.add("key-checked");
                keyEl.classList.remove("key-absent");
            } else if (emp.attendance_status === "ABSENT") {
                keyEl.classList.add("key-absent");
                keyEl.classList.remove("key-checked");
            } else {
                keyEl.classList.remove("key-checked");
                keyEl.classList.remove("key-absent");
            }
        });
    },

    async endAttendance() {
        try {
            const res = await fetch("/api/attendance/end", { method: "POST" });
            const data = await res.json();

            if (data.status === "success") {
                this.showToast(data.message, "success");

                const banner = document.getElementById("live-attendance-banner");
                banner.className = "live-banner banner-absent";
                banner.innerHTML = `<span>⚠️</span> <strong>Attendance Ended:</strong> ${data.metrics.present} Present, ${data.metrics.absent} Absent. Automatically reassigned ${data.metrics.reassigned} task(s).`;

                this.renderReassignmentsAndEmails(data.reassignments, data.emails);
                this.loadDashboard();
            }
        } catch (err) {
            console.error("End attendance error:", err);
            this.showToast("Failed to finalize attendance", "danger");
        }
    },

    renderReassignmentsAndEmails(reassignments, emails) {
        const container = document.getElementById("reassignments-list");
        if (!container) return;

        if (!reassignments || reassignments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">✓</div>
                    <h3>All Assigned Tasks Covered</h3>
                    <p>No absent employees with active tasks required reallocation.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = reassignments.map((r, idx) => {
            const email = emails[idx] || {};
            return `
                <div class="reassign-card" id="reassign-card-${r.id}">
                    <div class="reassign-header">
                        <div>
                            <span class="badge badge-info">AUTOMATIC TASK REALLOCATION</span>
                            <h3 style="font-size: 1.15rem; margin-top: 0.3rem;">${r.task_name}</h3>
                        </div>
                        <span id="email-badge-${r.id}" class="badge ${r.email_sent ? 'badge-present' : 'badge-pending'}">
                            ${r.email_sent ? 'Email Sent ✓' : 'Email Ready'}
                        </span>
                    </div>

                    <div class="reassign-grid">
                        <div class="reassign-item">
                            <span class="reassign-label">Absent Employee</span>
                            <span class="reassign-value" style="color: var(--danger);">Employee ${r.absent_employee}</span>
                        </div>
                        <div class="reassign-item">
                            <span class="reassign-label">Task</span>
                            <span class="reassign-value">${r.task_name}</span>
                        </div>
                        <div class="reassign-item">
                            <span class="reassign-label">Required Skill</span>
                            <span class="reassign-value">${r.required_skill}</span>
                        </div>
                        <div class="reassign-item">
                            <span class="reassign-label">Eligible Employee</span>
                            <span class="reassign-value" style="color: var(--success);">Employee ${r.new_employee}</span>
                        </div>
                        <div class="reassign-item">
                            <span class="reassign-label">Current Workload</span>
                            <span class="reassign-value">${r.workload_before}%</span>
                        </div>
                        <div class="reassign-item">
                            <span class="reassign-label">Selection Rationale</span>
                            <span class="reassign-value" style="font-size: 0.85rem; font-weight: normal; color: var(--text-muted);">${r.reason}</span>
                        </div>
                    </div>

                    <!-- Email Preview Section -->
                    <div class="email-preview-box">
                        <div class="email-header-line">
                            <strong>Subject:</strong> ${email.subject || 'New Task Assigned Due to Employee Absence'} &nbsp;|&nbsp; 
                            <strong>To:</strong> Employee ${r.new_employee}
                        </div>
                        <div class="email-body">${email.body || `Hello ${r.new_employee},\n\nEmployee ${r.absent_employee} is absent today.\nYou have been selected to handle the task: ${r.task_name}.\n\nThank you.`}</div>
                    </div>

                    <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
                        <button id="send-email-btn-${r.id}" class="btn ${r.email_sent ? 'btn-outline' : 'btn-primary'}" onclick="App.sendEmailNotification(${r.id})">
                            ${r.email_sent ? '✓ Email Sent' : '✉️ Send Task Assignment Email'}
                        </button>
                    </div>
                </div>
            `;
        }).join("");
    },

    async sendEmailNotification(reassignId) {
        const btn = document.getElementById(`send-email-btn-${reassignId}`);
        if (btn) btn.disabled = true;

        try {
            const res = await fetch("/api/send-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reassignment_id: reassignId })
            });

            const data = await res.json();
            if (data.status === "success") {
                this.showToast(data.message, "success");
                
                const badge = document.getElementById(`email-badge-${reassignId}`);
                if (badge) {
                    badge.className = "badge badge-present";
                    badge.textContent = "Email Sent ✓";
                }

                if (btn) {
                    btn.className = "btn btn-outline";
                    btn.textContent = "✓ Email Sent";
                }
            }
        } catch (err) {
            console.error("Email send error:", err);
            this.showToast("Failed to send email", "danger");
            if (btn) btn.disabled = false;
        }
    },

    async resetSystem() {
        if (!confirm("Reset all employee attendance and task assignments back to the initial state?")) {
            return;
        }

        try {
            const res = await fetch("/api/reset", { method: "POST" });
            const data = await res.json();
            if (data.status === "success") {
                this.showToast(data.message, "success");
                
                const banner = document.getElementById("live-attendance-banner");
                banner.className = "live-banner banner-idle";
                banner.innerHTML = `<span>📡</span> <span>System reset. Press keys <kbd>A</kbd>, <kbd>C</kbd>, <kbd>D</kbd>, <kbd>E</kbd>, <kbd>G</kbd>, <kbd>H</kbd>, <kbd>I</kbd> for demo.</span>`;

                const reassignList = document.getElementById("reassignments-list");
                if (reassignList) {
                    reassignList.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon">⏳</div>
                            <h3>No Active Reassignments Yet</h3>
                            <p>Check in employees using keys and click <strong>"End Attendance Period"</strong> to trigger automated task reallocation for absent staff.</p>
                        </div>
                    `;
                }

                this.loadDashboard();
            }
        } catch (err) {
            this.showToast("Reset failed", "danger");
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    App.init();
});
