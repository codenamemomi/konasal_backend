from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from core.config.settings import settings
import traceback
from pydantic import EmailStr

def send_email_reminder(to_email: str, subject: str, content: str):
    from_email = settings.MAIL_FROM or settings.EMAILS_FROM_EMAIL or "no-reply@example.com"

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if 200 <= response.status_code < 300:
            print("✅ Email sent successfully via SendGrid.")
        else:
            print(f"⚠️ Email sent but got status code: {response.status_code}")
            print(f"Body: {response.body}")
            print(f"Headers: {response.headers}")

        return response.status_code
    except Exception as e:
        print("❌ Failed to send email via SendGrid.")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"From: {from_email}")
        print(f"SENDGRID_API_KEY present: {'Yes' if settings.SENDGRID_API_KEY else 'No'}")
        traceback.print_exc()
        raise