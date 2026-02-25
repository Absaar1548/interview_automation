class MockEmailService:
    """
    Mock Service for sending emails to candidates (logs to console).
    """
    
    async def send_candidate_password_email(self, candidate_email: str, candidate_name: str, password: str):
        """
        Simulate sending password email to candidate.
        """
        print("\n" + "="*50)
        print(f" [MOCK EMAIL] To: {candidate_email}")
        print(f" Subject: Welcome to Interview Automation Platform - Your Login Credentials")
        print(f" Body: Dear {candidate_name}, Your password is: {password}")
        print("="*50 + "\n")
        return True

email_service = MockEmailService()
