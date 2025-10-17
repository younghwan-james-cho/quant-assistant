import sys

print("PYTHONPATH during test execution:", sys.path)

from assistant.senders.smtp_sender import send_email

# Replace with your test values
to_email = "recipient@example.com"
subject = "Test Email"
html_content = "<h1>This is a test email</h1>"

try:
    send_email(to=to_email, subject=subject, html_or_md=html_content)
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
