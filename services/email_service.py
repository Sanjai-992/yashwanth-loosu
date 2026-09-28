import os
import smtplib
import json
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from database.db_helper import get_employee_by_id

try:
    import resend
    RESEND_INSTALLED = True
except ImportError:
    RESEND_INSTALLED = False


def _build_email_content(absent_employee_id: str, halted_task: str, replacement_id: str, reason: str = None) -> dict:
    """Generates both text and rich HTML email content for task reassignment."""
    absent_emp = get_employee_by_id(absent_employee_id)
    replacement_emp = get_employee_by_id(replacement_id)

    absent_name = absent_emp["name"] if absent_emp else absent_employee_id
    replacement_name = replacement_emp["name"] if replacement_emp else replacement_id

    absent_role = absent_emp.get("role", "Engineer") if absent_emp else "Engineer"
    replacement_role = replacement_emp.get("role", "Engineer") if replacement_emp else "Engineer"
    absent_skill = absent_emp.get("skill", "General") if absent_emp else "General"
    replacement_skill = replacement_emp.get("skill", "General") if replacement_emp else "General"
    replacement_workload = replacement_emp.get("workload", 30) if replacement_emp else 30

    decision_reason = reason or "Optimal skill match + present attendance + available workload bandwidth."
    subject = f"⚡ Urgent Operational Reassignment: Cover '{halted_task}'"

    text_body = f"""Dear {replacement_name},

This is an automated operational notice that the WORKFORCE-X Management System has assigned you to cover a halted task for an absent employee.

==================================================
TASK REASSIGNMENT & WORKING DETAILS
==================================================

• Absent Employee: {absent_name} (ID: {absent_employee_id})
• Absent Employee Role: {absent_role}
• Halted Task: {halted_task}
• Required Skill: {absent_skill}

• Replacement Employee: {replacement_name} (ID: {replacement_id})
• Replacement Role: {replacement_role}
• Current Workload: {replacement_workload}%
• Assignment Rationale: {decision_reason}

==================================================
ACTION REQUIRED:
Please review the specifications for '{halted_task}' and proceed with execution immediately to maintain project timeline.

Regards,
WORKFORCE-X Operations Engine
Automated Workforce Management
"""

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #0f172a; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06); }}
            .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #2563eb 100%); padding: 24px 28px; color: #ffffff; }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 20px; font-weight: 800; letter-spacing: -0.01em; }}
            .header p {{ margin: 0; font-size: 13px; color: #94a3b8; }}
            .badge {{ display: inline-block; background: #fee2e2; color: #dc2626; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 12px; }}
            .content {{ padding: 24px 28px; }}
            .detail-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 16px 0; }}
            .table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            .table td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; }}
            .table td.label {{ color: #64748b; font-weight: 600; width: 38%; }}
            .table td.val {{ color: #0f172a; font-weight: 700; }}
            .reason-box {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #1e40af; margin-top: 14px; }}
            .action-banner {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 14px; margin-top: 20px; color: #065f46; font-size: 13px; }}
            .footer {{ background: #f1f5f9; padding: 16px 28px; font-size: 11px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="badge">Operational Task Reassignment</span>
                <h1>⚡ Task Allocation Directive</h1>
                <p>WORKFORCE-X Automated Workforce Management Engine</p>
            </div>
            <div class="content">
                <p>Dear <b>{replacement_name}</b>,</p>
                <p>An unexpected absence has occurred. The operational intelligence engine has identified you as the optimal available specialist to assume responsibility for the halted task below.</p>
                
                <div class="detail-card">
                    <table class="table">
                        <tr>
                            <td class="label">Halted Task</td>
                            <td class="val" style="color: #2563eb; font-size: 14px;">{halted_task}</td>
                        </tr>
                        <tr>
                            <td class="label">Required Skill</td>
                            <td class="val">{absent_skill}</td>
                        </tr>
                        <tr>
                            <td class="label">Absent Personnel</td>
                            <td class="val" style="color: #dc2626;">{absent_name} ({absent_employee_id}) — {absent_role}</td>
                        </tr>
                        <tr>
                            <td class="label">Assigned Specialist</td>
                            <td class="val" style="color: #059669;">{replacement_name} ({replacement_id}) — {replacement_role}</td>
                        </tr>
                        <tr>
                            <td class="label">Current Workload</td>
                            <td class="val">{replacement_workload}%</td>
                        </tr>
                    </table>
                    
                    <div class="reason-box">
                        <b>Selection Rationale:</b> {decision_reason}
                    </div>
                </div>

                <div class="action-banner">
                    <b>Action Required:</b> Please log into your workstation, accept the handover notes for <b>{halted_task}</b>, and begin execution.
                </div>
            </div>
            <div class="footer">
                Automated notification dispatched via WORKFORCE-X Operations Hub &bull; Resend Email Integration
            </div>
        </div>
    </body>
    </html>
    """

    return {
        "subject": subject,
        "text": text_body,
        "html": html_body,
        "absent_name": absent_name,
        "replacement_name": replacement_name
    }


def send_via_resend(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    text: str,
    html: str
) -> dict:
    """
    Sends an email using the Resend API.
    Uses the official SDK if available, or direct REST API via requests.
    """
    if not api_key:
        return {
            "success": False,
            "provider": "resend",
            "message": "Resend API key is missing. Please provide your Resend API Key (starts with 're_')."
        }

    from_addr = from_email or "WORKFORCE-X Operations <onboarding@resend.dev>"
    recipient = to_email.strip() if to_email else "delivered@resend.dev"

    # Attempt official SDK first
    if RESEND_INSTALLED:
        try:
            resend.api_key = api_key
            params = {
                "from": from_addr,
                "to": [recipient],
                "subject": subject,
                "html": html,
                "text": text
            }
            res = resend.Emails.send(params)
            # res can be a dict or object with id
            res_id = getattr(res, "id", None) or (res.get("id") if isinstance(res, dict) else str(res))
            return {
                "success": True,
                "provider": "resend",
                "message_id": res_id,
                "message": f"Email successfully delivered via Resend API (ID: {res_id})",
                "recipient": recipient
            }
        except Exception as sdk_err:
            error_str = str(sdk_err)
            # If domain error, provide helpful instructions
            if "domain" in error_str.lower() or "verify" in error_str.lower():
                error_str += " (Tip: With onboarding@resend.dev, send only to your registered account email, or verify a custom domain at resend.com/domains)."
            return {
                "success": False,
                "provider": "resend",
                "message": f"Resend SDK error: {error_str}"
            }

    # REST fallback using requests
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": from_addr,
            "to": [recipient],
            "subject": subject,
            "html": html,
            "text": text
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=6.0)
        resp_data = resp.json() if resp.status_code != 204 else {}
        if resp.status_code in (200, 201):
            return {
                "success": True,
                "provider": "resend",
                "message_id": resp_data.get("id", "resend_ok"),
                "message": f"Email successfully delivered via Resend REST API (ID: {resp_data.get('id')})",
                "recipient": recipient
            }
        else:
            err_msg = resp_data.get("message", resp.text)
            return {
                "success": False,
                "provider": "resend",
                "message": f"Resend API error ({resp.status_code}): {err_msg}"
            }
    except Exception as http_err:
        return {
            "success": False,
            "provider": "resend",
            "message": f"Unable to reach Resend API: {str(http_err)}"
        }


def send_via_smtp(
    sender_email: str,
    app_password: str,
    to_email: str,
    subject: str,
    text: str,
    html: str
) -> dict:
    """Sends email via Gmail SMTP."""
    if not sender_email or not app_password:
        return {
            "success": False,
            "provider": "smtp",
            "message": "Gmail credentials not configured. Please provide Sender Email and App Password."
        }

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = to_email or sender_email
    message["Subject"] = subject

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=3.0)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(message)
        server.quit()
        return {
            "success": True,
            "provider": "smtp",
            "message": "Task reassignment email sent successfully via Gmail SMTP.",
            "recipient": to_email or sender_email
        }
    except Exception as e:
        return {
            "success": False,
            "provider": "smtp",
            "message": f"Unable to send email via SMTP. Error: {str(e)}"
        }


def send_reassignment_email(
    target_recipient: str = "",
    absent_employee_id: str = "B",
    halted_task: str = "Database Module",
    replacement_id: str = "G",
    reason: str = None,
    provider: str = "resend",
    resend_api_key: str = None,
    resend_from_email: str = None,
    sender_email: str = None,
    app_password: str = None
) -> dict:
    """
    Unified task reassignment notification dispatcher.
    Supports:
      - Resend API (default / recommended)
      - Gmail SMTP
      - Simulation / Offline mode
    """
    content = _build_email_content(absent_employee_id, halted_task, replacement_id, reason)
    prov = (provider or "resend").lower()

    if prov == "resend":
        api_key = resend_api_key or os.getenv("RESEND_API_KEY", "")
        from_email = resend_from_email or os.getenv("RESEND_FROM_EMAIL", "WORKFORCE-X Operations <onboarding@resend.dev>")
        result = send_via_resend(
            api_key=api_key,
            from_email=from_email,
            to_email=target_recipient,
            subject=content["subject"],
            text=content["text"],
            html=content["html"]
        )
        result["subject"] = content["subject"]
        result["body"] = content["text"]
        result["html"] = content["html"]
        return result

    elif prov == "smtp":
        s_email = sender_email or os.getenv("GMAIL_SENDER", "")
        pwd = app_password or os.getenv("GMAIL_APP_PASSWORD", "")
        result = send_via_smtp(
            sender_email=s_email,
            app_password=pwd,
            to_email=target_recipient,
            subject=content["subject"],
            text=content["text"],
            html=content["html"]
        )
        result["subject"] = content["subject"]
        result["body"] = content["text"]
        result["html"] = content["html"]
        return result

    else:
        # Simulation mode
        return {
            "success": True,
            "provider": "simulation",
            "message": "Simulated email notification prepared and logged successfully.",
            "subject": content["subject"],
            "body": content["text"],
            "html": content["html"],
            "recipient": target_recipient or "operations@enterprise.internal"
        }


def send_test_email(
    provider: str = "resend",
    resend_api_key: str = None,
    resend_from_email: str = None,
    to_email: str = None,
    sender_email: str = None,
    app_password: str = None
) -> dict:
    """Sends a quick diagnostic test email to verify credentials."""
    subject = "⚡ WORKFORCE-X: Test Email Notification"
    text = "This is a test notification from WORKFORCE-X verifying that your email dispatch pipeline is functional."
    html = """
    <div style="font-family:sans-serif; padding:20px; background:#f8fafc; border-radius:10px;">
        <h2 style="color:#2563eb; margin:0 0 10px 0;">⚡ WORKFORCE-X Test Notification</h2>
        <p style="color:#334155; font-size:14px;">Your email dispatch configuration is <b>active and operational</b>.</p>
        <div style="padding:10px; background:#ecfdf5; border-left:4px solid #10b981; color:#047857; font-size:13px; font-weight:600;">
            ✓ Verification completed successfully.
        </div>
    </div>
    """
    prov = (provider or "resend").lower()
    if prov == "resend":
        api_key = resend_api_key or os.getenv("RESEND_API_KEY", "")
        from_email = resend_from_email or os.getenv("RESEND_FROM_EMAIL", "WORKFORCE-X Operations <onboarding@resend.dev>")
        return send_via_resend(
            api_key=api_key,
            from_email=from_email,
            to_email=to_email or "delivered@resend.dev",
            subject=subject,
            text=text,
            html=html
        )
    elif prov == "smtp":
        s_email = sender_email or os.getenv("GMAIL_SENDER", "")
        pwd = app_password or os.getenv("GMAIL_APP_PASSWORD", "")
        return send_via_smtp(
            sender_email=s_email,
            app_password=pwd,
            to_email=to_email or s_email,
            subject=subject,
            text=text,
            html=html
        )
    else:
        return {
            "success": True,
            "provider": "simulation",
            "message": "Simulation test succeeded. Email dispatch pipeline ready."
        }
