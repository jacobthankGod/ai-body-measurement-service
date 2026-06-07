"""
KORRA Communications Engine | PHASE 16: AUTOMATED EMAILS
======================================================
Industrial-grade email infrastructure for merchant engagement.
Pluggable architecture supporting Resend, SendGrid, or Mock.
"""
import os
import logging

logger = logging.getLogger("KORRA_COMM")

class EmailService:
    @staticmethod
    async def send_welcome_email(email: str, name: str):
        """Sends the 'Digital Artisan Infrastructure' onboarding welcome."""
        subject = "Welcome to KORRA | Your 3D Workbench is Ready"
        html_content = f"""
        <div style="background:#000; color:#fff; padding:40px; font-family:sans-serif; border:1px solid #57D7C0; border-radius:24px;">
            <div style="width:32px; height:32px; background:#57D7C0; border-radius:8px; margin-bottom:20px;"></div>
            <h1 style="color:#57D7C0; font-size:24px; font-weight:900;">WELCOME, {name.upper()}</h1>
            <p style="color:#A3A3A3; font-size:16px; line-height:1.6;">
                You are now connected to the world's first Digital Artisan Infrastructure.
                Your biometrics vault is active and your Merchant API keys have been provisioned.
            </p>
            <div style="background:#111; padding:20px; border-radius:12px; margin:20px 0;">
                <p style="margin:0; font-size:14px;"><b>NEXT STEPS:</b></p>
                <ul style="color:#57D7C0; font-size:13px; font-weight:700;">
                    <li>Run your first benchmark in the Testing Lab</li>
                    <li>Download your first 3D Digital Twin</li>
                    <li>Integrate your API key into your workshop flow</li>
                </ul>
            </div>
            <a href="https://korra.ai/dashboard" style="display:inline-block; padding:12px 24px; background:#57D7C0; color:#000; text-decoration:none; border-radius:8px; font-weight:800; font-size:13px;">ENTER WORKBENCH</a>
            <p style="font-size:10px; color:#737373; margin-top:40px;">© 2026 KORRA AI | London • Lagos</p>
        </div>
        """
        return await EmailService._dispatch(email, subject, html_content)

    @staticmethod
    async def send_low_credit_alert(email: str, current_balance: int):
        """Notifies merchant when technical quotas are low."""
        subject = "CRITICAL: KORRA Scan Credits Low"
        html_content = f"""
        <div style="background:#000; color:#fff; padding:40px; font-family:sans-serif; border:1px solid #D63031; border-radius:24px;">
            <h1 style="color:#D63031; font-size:20px; font-weight:900;">CREDIT REPLENISHMENT REQUIRED</h1>
            <p style="color:#A3A3A3;">Your current balance has dropped to <b>{current_balance} scans</b>.</p>
            <p style="color:#A3A3A3; font-size:14px;">To avoid interruption in your technical workshop flow, please top up your vault now.</p>
            <a href="https://korra.ai/dashboard#vault" style="display:inline-block; padding:12px 24px; background:#D63031; color:#fff; text-decoration:none; border-radius:8px; font-weight:800; font-size:13px;">TOP UP VAULT</a>
        </div>
        """
        return await EmailService._dispatch(email, subject, html_content)

    @staticmethod
    async def _dispatch(email: str, subject: str, html: str):
        """Private dispatcher handles the physical API handshake."""
        api_key = os.environ.get("RESEND_API_KEY")

        if not api_key:
            logger.info(f"MOCK EMAIL to {email}: {subject}")
            # print(html) # Debug only
            return {"success": True, "mode": "mock"}

        # In production, we'd use 'resend' or 'sendgrid' libraries here
        try:
            import resend
            resend.api_key = api_key
            r = resend.Emails.send({
                "from": "KORRA AI <onboarding@korra.ai>",
                "to": [email],
                "subject": subject,
                "html": html
            })
            return {"success": True, "resend_id": r['id']}
        except Exception as e:
            logger.error(f"Email Dispatch Failed: {e}")
            return {"success": False, "error": str(e)}
