from __future__ import annotations
import os
import smtplib
import ssl
import time
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

    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))  # default to STARTTLS port
    use_ssl = _bool(os.getenv("SMTP_USE_SSL", "false"), default=False)
    use_starttls = _bool(os.getenv("SMTP_STARTTLS", "true"), default=True)
    timeout = float(os.getenv("SMTP_TIMEOUT", "15"))  # seconds
    debug = int(os.getenv("SMTP_DEBUG", "0"))

    from_addr = from_addr or user

    msg = MIMEText(html_or_md, "html")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    attempts = int(os.getenv("SMTP_RETRIES", "3"))
    backoff = float(os.getenv("SMTP_BACKOFF", "1.5"))

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            if use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as s:
                    if debug:
                        s.set_debuglevel(1)
                    s.login(user, pwd)
                    s.sendmail(from_addr, [to], msg.as_string())
                    return
            else:
                with smtplib.SMTP(host, port, timeout=timeout) as s:
                    if debug:
                        s.set_debuglevel(1)
                    if use_starttls:
                        s.starttls(context=ssl.create_default_context())
                    s.login(user, pwd)
                    s.sendmail(from_addr, [to], msg.as_string())
                    return
        except Exception as e:
            last_exc = e
            if attempt < attempts:
                time.sleep(backoff * attempt)
            else:
                raise
