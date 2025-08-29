import smtplib
from email.mime.text import MIMEText
from core.config.settings import settings
import traceback
from pydantic import EmailStr
import re
import dns.resolver
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def send_email_reminder(to_email: str, subject: str, content: str):
    """
    Try sending email via Gmail SMTP (preferred).
    If SMTP is not configured, fallback to SendGrid.
    """
    from_email = (
        settings.MAIL_FROM
        or settings.EMAILS_FROM_EMAIL
        or "no-reply@example.com"
    )

    # --- Option 1: Gmail SMTP ---
    if settings.EMAIL_HOST and settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD:
        try:
            message = MIMEText(content, "html")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email

            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                server.sendmail(from_email, [to_email], message.as_string())

            print("✅ Email sent successfully via Gmail SMTP.")
            return 200
        except Exception as e:
            print("❌ Failed to send email via Gmail SMTP.")
            traceback.print_exc()

    # --- Option 2: SendGrid ---
    if settings.SENDGRID_API_KEY:
        try:
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=content,
            )
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)

            if 200 <= response.status_code < 300:
                print("✅ Email sent successfully via SendGrid.")
            else:
                print(f"⚠️ SendGrid returned status code: {response.status_code}")
                print(f"Body: {response.body}")
                print(f"Headers: {response.headers}")

            return response.status_code
        except Exception as e:
            print("❌ Failed to send email via SendGrid.")
            traceback.print_exc()

    print("⚠️ No valid email configuration found.")
    return 500


def is_email_format_valid(email: str) -> bool:
    return EMAIL_REGEX.match(email) is not None


async def is_email_reachable(email: str) -> bool:
    """
    Check if the domain of the email has valid MX records (basic reachability).
    """
    if not is_email_format_valid(email):
        return False

    try:
        domain = email.split("@")[1]
        dns.resolver.resolve(domain, "MX")  # Query MX records
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return False
    except Exception:
        return False
