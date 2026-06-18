import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from api.services.email_service import EmailService

async def test_email():
    print("Initializing EmailService...")
    service = EmailService()

    test_email_addr = os.environ.get("TEST_EMAIL", "test@example.com")
    print(f"Sending test email to: {test_email_addr}")

    success = await service.send_verification_email(
        to_email=test_email_addr,
        user_name="Test User",
        verification_url="https://korra.work/verify?token=test_token"
    )

    if success:
        print("SUCCESS: Email dispatched via Brevo!")
    else:
        print("FAILURE: Email dispatch failed.")

if __name__ == "__main__":
    if not os.environ.get("BREVO_API_KEY"):
        print("ERROR: BREVO_API_KEY environment variable is not set.")
    else:
        asyncio.run(test_email())
