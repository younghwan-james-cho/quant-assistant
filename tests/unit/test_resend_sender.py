from unittest.mock import patch, MagicMock
from assistant.senders.resend_sender import send_email_resend


def test_send_email_resend(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test_api_key")
    mock_resend = MagicMock()
    with patch("assistant.senders.resend_sender.Resend", return_value=mock_resend):
        send_email_resend(
            to="recipient@example.com",
            subject="Test Email",
            html_or_md="<p>Hello</p>",
            from_addr="sender@example.com",
        )
        mock_resend.emails.send.assert_called_once_with(
            from_="sender@example.com",
            to=["recipient@example.com"],
            subject="Test Email",
            html="<p>Hello</p>",
        )
