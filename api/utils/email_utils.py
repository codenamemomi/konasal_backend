from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from core.config.settings import settings
import traceback
from pydantic import EmailStr
import re
import dns.resolver

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


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


def is_email_format_valid(email: str) -> bool:
    return EMAIL_REGEX.match(email) is not None

async def is_email_reachable(email: str) -> bool:
    """
    Check if the domain of the email has valid MX records (basic reachability).
    """
    if not is_email_format_valid(email):
        return False

    try:
        domain = email.split('@')[1]
        # Query MX records
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return False
    except Exception:
        # Fallback for unexpected errors — assume unreachable
        return False