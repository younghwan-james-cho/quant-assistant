from __future__ import annotations
import os, smtplib, ssl
from email.mime.text import MIMEText

def _bool(s: str, default=False):
    if s is None: return default
    return s.strip().lower() in ("1","true","yes","on")

def send_email(to: str, subject: str, html_or_md: str):
    user = os.getenv("SMTP_USER"); pwd = os.getenv("SMTP_PASS")
    if not user or not pwd:
        raise RuntimeError("SMTP_USER/SMTP_PASS not configured")

    host = os.getenv("SMTP_HOST", "smtp.office365.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    use_ssl = _bool(os.getenv("SMTP_USE_SSL", "true"), default=True)
    use_starttls = _bool(os.getenv("SMTP_STARTTLS", "false"), default=False)

    msg = MIMEText(html_or_md, "html")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
            s.login(user, pwd)
            s.sendmail(user, [to], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            if use_starttls:
                s.starttls(context=ssl.create_default_context())
            s.login(user, pwd)
            s.sendmail(user, [to], msg.as_string())
