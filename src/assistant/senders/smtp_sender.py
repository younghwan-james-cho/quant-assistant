from __future__ import annotations
import os, smtplib, ssl
from email.mime.text import MIMEText

def send_email(to: str, subject: str, html_or_md: str):
    user = os.getenv("SMTP_USER"); pwd = os.getenv("SMTP_PASS")
    if not user or not pwd:
        raise RuntimeError("SMTP_USER/SMTP_PASS not configured")
    msg = MIMEText(html_or_md, "html")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    with smtplib.SMTP_SSL("smtp.office365.com", 465, context=ssl.create_default_context()) as s:
        s.login(user, pwd); s.sendmail(user, [to], msg.as_string())
