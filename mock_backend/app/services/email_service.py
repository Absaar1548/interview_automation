import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.email_config import CREDENTIAL_RECEIVERS

logger = logging.getLogger(__name__)


class EmailService:
    """
    Sends candidate credentials via Gmail SMTP.
    Falls back to console logging if SMTP is not configured.
    """

    def _is_configured(self) -> bool:
        return bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)

    async def send_candidate_password_email(
        self, candidate_email: str, candidate_name: str, password: str
    ):
        """
        Send the candidate's login credentials to all addresses in
        CREDENTIAL_RECEIVERS (defined in app/core/email_config.py).
        """
        recipients = list(CREDENTIAL_RECEIVERS)  # copy so we don't mutate the original

        if not self._is_configured():
            logger.warning(
                "SMTP not configured (SMTP_USERNAME / SMTP_PASSWORD missing). "
                "Falling back to console output."
            )
            print("\n" + "=" * 50)
            print(f"  [FALLBACK EMAIL] To: {', '.join(recipients)}")
            print(f"  Candidate: {candidate_name} ({candidate_email})")
            print(f"  Password : {password}")
            print("=" * 50 + "\n")
            return True

        subject = (
            f"New Candidate Registered – {candidate_name} ({candidate_email})"
        )

        html_body = f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
  <h2 style="color: #2c3e50;">New Candidate Registered</h2>
  <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
    <tr>
      <td style="padding: 8px; font-weight: bold;">Name</td>
      <td style="padding: 8px;">{candidate_name}</td>
    </tr>
    <tr style="background: #f9f9f9;">
      <td style="padding: 8px; font-weight: bold;">Email</td>
      <td style="padding: 8px;">{candidate_email}</td>
    </tr>
    <tr>
      <td style="padding: 8px; font-weight: bold;">Username</td>
      <td style="padding: 8px;">{candidate_email.split('@')[0]}</td>
    </tr>
    <tr style="background: #f9f9f9;">
      <td style="padding: 8px; font-weight: bold;">Password</td>
      <td style="padding: 8px; font-family: monospace; font-size: 14px;">{password}</td>
    </tr>
  </table>
  <p style="margin-top: 16px; font-size: 12px; color: #999;">
    This is an automated message from the Interview Automation Platform.
  </p>
</body>
</html>
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())

            logger.info(
                f"Credential email for {candidate_email} sent to {recipients}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send credential email: {e}", exc_info=True)
            # Still print to terminal as safety net so credentials aren't lost
            print(f"\n[EMAIL FAILED] {candidate_email} — password: {password}\n")
            return False


email_service = EmailService()
