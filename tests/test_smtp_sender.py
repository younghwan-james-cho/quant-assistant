# tests/test_smtp_sender.py
import os
import importlib


def test_validate_smtp_config_missing_vars(monkeypatch):
    """Test that pre-flight check raises error when required vars are missing."""
    smtp = importlib.import_module("assistant.senders.smtp_sender")
    
    # Remove required environment variables
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    
    try:
        smtp._validate_smtp_config()
        assert False, "expected RuntimeError when SMTP_USER/SMTP_PASS missing"
    except RuntimeError as e:
        assert "Missing required SMTP environment variables" in str(e)


def test_validate_smtp_config_with_vars(monkeypatch):
    """Test that pre-flight check passes when required vars are present."""
    smtp = importlib.import_module("assistant.senders.smtp_sender")
    
    monkeypatch.setenv("SMTP_USER", "test@example.com")
    monkeypatch.setenv("SMTP_PASS", "testpass")
    
    # Should not raise
    smtp._validate_smtp_config()


def test_circuit_breaker_opens_after_failures():
    """Test that circuit breaker opens after 3 consecutive failures."""
    smtp = importlib.import_module("assistant.senders.smtp_sender")
    
    # Reset circuit breaker
    smtp._circuit_breaker.reset()
    
    assert not smtp._circuit_breaker.is_open
    assert smtp._circuit_breaker.consecutive_failures == 0
    
    # Record 3 failures
    smtp._circuit_breaker.record_failure()
    assert smtp._circuit_breaker.consecutive_failures == 1
    assert not smtp._circuit_breaker.is_open
    
    smtp._circuit_breaker.record_failure()
    assert smtp._circuit_breaker.consecutive_failures == 2
    assert not smtp._circuit_breaker.is_open
    
    smtp._circuit_breaker.record_failure()
    assert smtp._circuit_breaker.consecutive_failures == 3
    assert smtp._circuit_breaker.is_open


def test_circuit_breaker_resets_on_success():
    """Test that circuit breaker resets on successful send."""
    smtp = importlib.import_module("assistant.senders.smtp_sender")
    
    # Reset circuit breaker
    smtp._circuit_breaker.reset()
    
    # Record some failures
    smtp._circuit_breaker.record_failure()
    smtp._circuit_breaker.record_failure()
    assert smtp._circuit_breaker.consecutive_failures == 2
    assert not smtp._circuit_breaker.is_open
    
    # Record success
    smtp._circuit_breaker.record_success()
    assert smtp._circuit_breaker.consecutive_failures == 0
    assert not smtp._circuit_breaker.is_open


def test_send_email_blocked_by_open_circuit_breaker(monkeypatch):
    """Test that send_email raises error when circuit breaker is open."""
    smtp = importlib.import_module("assistant.senders.smtp_sender")
    
    # Set up environment
    monkeypatch.setenv("SMTP_USER", "test@example.com")
    monkeypatch.setenv("SMTP_PASS", "testpass")
    
    # Open the circuit breaker
    smtp._circuit_breaker.reset()
    smtp._circuit_breaker.record_failure()
    smtp._circuit_breaker.record_failure()
    smtp._circuit_breaker.record_failure()
    assert smtp._circuit_breaker.is_open
    
    try:
        smtp.send_email("to@example.com", "Test", "Body")
        assert False, "expected RuntimeError when circuit breaker is open"
    except RuntimeError as e:
        assert "circuit breaker is open" in str(e)
    finally:
        # Reset for other tests
        smtp._circuit_breaker.reset()


def test_send_email_validates_config_first(monkeypatch):
    """Test that send_email validates config before attempting to send."""
    smtp = importlib.import_module("assistant.senders.smtp_sender")
    
    # Reset circuit breaker
    smtp._circuit_breaker.reset()
    
    # Remove required environment variables
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    
    try:
        smtp.send_email("to@example.com", "Test", "Body")
        assert False, "expected RuntimeError when SMTP config missing"
    except RuntimeError as e:
        assert "Missing required SMTP environment variables" in str(e)
    
    # Check that failure was recorded in circuit breaker
    assert smtp._circuit_breaker.consecutive_failures == 1
    
    # Reset for other tests
    smtp._circuit_breaker.reset()
