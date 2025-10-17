from unittest.mock import patch, MagicMock


from assistant.senders.smtp_sender import send_email


def test_send_email_uses_smtp_flow(monkeypatch):
    # Configure env to force non-SSL + starttls branch
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USE_SSL", "false")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setenv("SMTP_TIMEOUT", "5")
    monkeypatch.setenv("SMTP_DEBUG", "0")
    monkeypatch.setenv("SMTP_RETRIES", "1")  # keep test fast
    monkeypatch.setenv("SMTP_BACKOFF", "0")

    host = "smtp.example.com"
    port = 587

    with patch("smtplib.SMTP") as mock_smtp:
        # Ensure the context manager returns a mock instance
        mock_conn = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_conn

        # Call the function under test
        send_email(to="dest@example.com", subject="Hi", html_or_md="<p>ok</p>")

        # Assert SMTP was instantiated with expected args (host, port, timeout)
        mock_smtp.assert_called()
        called_args, called_kwargs = mock_smtp.call_args
        assert called_args[0] == host
        assert int(called_args[1]) == port
        assert "timeout" in called_kwargs

        # Assert starttls was called (since SMTP_STARTTLS = true)
        assert mock_conn.starttls.called, "expected starttls() to be called"

        # Assert login was called with env creds
        mock_conn.login.assert_called_with("user@example.com", "secret")

        # Assert sendmail was called with sender and recipient
        assert mock_conn.sendmail.called, "expected sendmail() to be called"
        send_args, _ = mock_conn.sendmail.call_args
        assert send_args[0] == "user@example.com"
        assert send_args[1] == ["dest@example.com"]
