from __future__ import annotations
import os
import smtplib
import ssl
from email.mime.text import MIMEText

def _bool(s: str | None, default: bool = False) -> bool:
    if s is None:
        return default
    return s.strip().lower() in {"1", "true", "yes", "on"}

# Circuit breaker state to track consecutive failures
# Note: Not thread-safe - suitable for single-threaded applications only
class _CircuitBreaker:
    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self.consecutive_failures = 0
        self.is_open = False
    
    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.is_open = False
    
    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_failures:
            self.is_open = True
            print(f"[error] SMTP circuit breaker opened after {self.consecutive_failures} consecutive failures")
    
    def reset(self) -> None:
        self.consecutive_failures = 0
        self.is_open = False

# Global circuit breaker instance
_circuit_breaker = _CircuitBreaker()

def _validate_smtp_config() -> None:
    """Pre-flight check to validate all required SMTP environment variables."""
    required_vars = ["SMTP_USER", "SMTP_PASS"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required SMTP environment variables: {', '.join(missing_vars)}"
        print(f"[error] {error_msg}")
        raise RuntimeError(error_msg)

def send_email(to: str, subject: str, html_or_md: str, from_addr: str | None = None) -> None:
    # Check if circuit breaker is open
    if _circuit_breaker.is_open:
        error_msg = "SMTP circuit breaker is open - too many consecutive failures"
        print(f"[error] {error_msg}")
        raise RuntimeError(error_msg)
    
    # Pre-flight check for required environment variables
    try:
        _validate_smtp_config()
    except RuntimeError:
        _circuit_breaker.record_failure()
        raise
    
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")

    host = os.getenv("SMTP_HOST", "smtp.office365.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    use_ssl = _bool(os.getenv("SMTP_USE_SSL", "true"), default=True)
    use_starttls = _bool(os.getenv("SMTP_STARTTLS", "false"), default=False)

    from_addr = from_addr or user

    msg = MIMEText(html_or_md, "html")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    try:
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
        
        # Record success to reset circuit breaker
        _circuit_breaker.record_success()
        
    except Exception as e:
        # Log the failure and record it in circuit breaker
        print(f"[error] SMTP send failed: {e}")
        _circuit_breaker.record_failure()
        raise
