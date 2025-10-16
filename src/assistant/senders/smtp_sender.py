from __future__ import annotations
import os
import smtplib
import ssl
from email.mime.text import MIMEText

def _bool(s: str | None, default: bool = False) -> bool:
    if s is None:
        return default
    return s.strip().lower() in {"1", "true", "yes", "on"}

def send_email(to: str, subject: str, html_or_md: str, from_addr: str | None = None) -> None:
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    if not user or not pwd:
        raise RuntimeError("SMTP_USER/SMTP_PASS not configured")

    host = os.getenv("SMTP_HOST", "smtp.office365.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    use_ssl = _bool(os.getenv("SMTP_USE_SSL", "true"), default=True)
    use_starttls = _bool(os.getenv("SMTP_STARTTLS", "false"), default=False)

    from_addr = from_addr or user

    msg = MIMEText(html_or_md, "html")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as s:
            s.login(user, pwd)
            s.sendmail(from_addr, [to], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            if use_starttls:
                s.starttls(context=ssl.create_default_context())
            s.login(user, pwd)
            s.sendmail(from_addr, [to], msg.as_string())
