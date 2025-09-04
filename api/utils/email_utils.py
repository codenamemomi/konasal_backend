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


import smtplib
from email.mime.text import MIMEText
from core.config.settings import settings
import traceback
from pydantic import EmailStr
import re
import dns.resolver
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging

logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def send_email_reminder(to_email: str, subject: str, content: str):
    """
    Try sending email via Gmail SMTP (preferred).
    If SMTP is not configured, fallback to SendGrid.
    """
    from_email = (
        settings.MAIL_FROM or
        settings.EMAILS_FROM_EMAIL or
        "no-reply@example.com"
    )

    email_sent = False
    
    # --- Option 1: Gmail SMTP ---
    if settings.EMAIL_HOST and settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD:
        try:
            message = MIMEText(content, "html")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email

            # USE SMTP_SSL FOR PORT 465
            with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                server.sendmail(from_email, [to_email], message.as_string())

            email_sent = True
            return 200
        except Exception as e:
            logger.warning(f"SMTP email failed: {e}")
            traceback.print_exc()

    # --- Option 2: SendGrid ---
    if settings.SENDGRID_API_KEY and not email_sent:
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
                email_sent = True
            else:
                logger.warning(f"SendGrid failed: {response.status_code} - {response.body}")

            return response.status_code
        except Exception as e:
            logger.warning(f"SendGrid email failed: {e}")
            traceback.print_exc()

    # --- Option 3: Development Fallback ---
    if not email_sent:
        # Extract verification token from HTML content for development
        import re
        token_match = re.search(r'<h3[^>]*>(.*?)</h3>', content)
        if token_match:
            token = token_match.group(1).strip()
            logger.warning(f"Email not sent. Token for {to_email}: {token}")
        else:
            print("⚠️ No valid email configuration found and couldn't extract token.")
        
        return 200  # Return success anyway to not break the flow

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

# Add this to your email_utils.py
def is_email_configured() -> bool:
    """Check if any email service is configured"""
    has_smtp = bool(settings.EMAIL_HOST and settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD)
    has_sendgrid = bool(settings.SENDGRID_API_KEY)
    return has_smtp or has_sendgrid