import aiosmtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.core.config import settings

class EmailService:
    """
    Service for sending emails to candidates.
    """
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
    
    async def send_candidate_password_email(self, candidate_email: str, candidate_name: str, password: str):
        """
        Send password email to candidate after registration.
        """
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Welcome to Interview Automation Platform - Your Login Credentials"
            message["From"] = self.from_email
            message["To"] = candidate_email
            
            # Create the HTML email content
            html_content = f"""
            <html>
              <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #4F46E5;">Welcome to Interview Automation Platform!</h2>
                  <p>Dear {candidate_name},</p>
                  <p>Your account has been successfully created on our Interview Automation Platform.</p>
                  <p><strong>Please use the following credentials to log in:</strong></p>
                  <div style="background-color: #EEF2FF; border: 2px solid #4F46E5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #4F46E5; margin-top: 0;">Your Login Credentials</h3>
                    <div style="background-color: #FFFFFF; padding: 15px; border-radius: 5px; margin: 10px 0;">
                      <p style="margin: 8px 0;"><strong style="color: #374151;">Email:</strong> <span style="color: #1F2937; font-family: monospace;">{candidate_email}</span></p>
                      <p style="margin: 8px 0;"><strong style="color: #374151;">Password:</strong> <span style="color: #1F2937; font-family: monospace;">{password}</span></p>
                    </div>
                  </div>
                  <p style="color: #DC2626; font-weight: bold;">⚠️ Please keep these credentials secure and do not share them with anyone.</p>
                  <p>You can now log in to the platform and start your interview process.</p>
                  <p>Best regards,<br>Interview Automation Team</p>
                </div>
              </body>
            </html>
            """
            
            text_content = f"""
            Welcome to Interview Automation Platform!
            
            Dear {candidate_name},
            
            Your account has been successfully created on our Interview Automation Platform.
            
            ============================================
            YOUR LOGIN CREDENTIALS
            ============================================
            Email: {candidate_email}
            Password: {password}
            ============================================
            
            ⚠️ Please keep these credentials secure and do not share them with anyone.
            
            You can now log in to the platform and start your interview process.
            
            Best regards,
            Interview Automation Team
            """
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True,
            )
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            # For development, we'll still return True even if email fails
            # In production, you might want to handle this differently
            return False

email_service = EmailService()

