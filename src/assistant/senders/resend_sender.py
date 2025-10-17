from __future__ import annotations
import os
from typing import Optional

try:
    from resend import Resend
except ImportError:
    Resend = None  # type: ignore


def send_email_resend(
    to: str, subject: str, html_or_md: str, from_addr: Optional[str] = None
) -> None:
    """
    Send an email using the Resend API. Requires RESEND_API_KEY env var.

    - RESEND_API_KEY must be set in the environment.
    - If the `resend` package is not available, this will raise.
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY not configured")

    if Resend is None:
        raise RuntimeError("resend package not available")

    client = Resend(api_key)
    from_addr = (
        from_addr or os.getenv("SMTP_USER") or f"no-reply@{os.getenv('DOMAIN', 'example.com')}"
    )
    # Resend expects to receive HTML in the `html` field.
    client.emails.send(
        from_=from_addr,
        to=[to],
        subject=subject,
        html=html_or_md,
    )
