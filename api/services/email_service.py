"""
Brevo Email Service
==================
Handles all transactional and authentication emails via Brevo (formerly Sendinblue).
"""
import os
import logging
from typing import Dict, List, Optional
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail, SendSmtpEmailSender, SendSmtpEmailTo

from api.config import BREVO_API_KEY, BREVO_FROM_EMAIL, BREVO_FROM_NAME

logger = logging.getLogger("KORRA_EMAIL")

class EmailService:
    def __init__(self):
        self.config = Configuration()
        self.config.api_key['api-key'] = BREVO_API_KEY
        self.api_client = ApiClient(self.config)
        self.email_api = TransactionalEmailsApi(self.api_client)

        self.sender = SendSmtpEmailSender(
            name=BREVO_FROM_NAME,
            email=BREVO_FROM_EMAIL
        )

    def _get_base_template(self, content_html: str) -> str:
        """KORRA Branded Base Template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #000000; color: #FFFFFF; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .logo-mark {{ width: 40px; height: 40px; background-color: #57D7C0; border-radius: 8px; display: inline-block; transform: rotate(-8deg); }}
                .logo-text {{ font-size: 24px; font-weight: 900; color: #FFFFFF; display: inline-block; vertical-align: middle; margin-left: 12px; letter-spacing: -0.05em; }}
                .content {{ background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 40px; text-align: center; }}
                h1 {{ font-size: 28px; font-weight: 800; margin-bottom: 16px; letter-spacing: -0.03em; }}
                p {{ color: #A3A3A3; font-size: 16px; line-height: 1.6; margin-bottom: 32px; }}
                .btn {{ background-color: #57D7C0; color: #000000; padding: 16px 32px; border-radius: 12px; font-weight: 800; text-decoration: none; display: inline-block; text-transform: uppercase; font-size: 14px; letter-spacing: 0.1em; }}
                .footer {{ text-align: center; margin-top: 40px; color: #737373; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo-mark"></div>
                    <span class="logo-text">KORRA</span>
                </div>
                <div class="content">
                    {content_html}
                </div>
                <div class="footer">
                    &copy; 2026 KORRA AI. Scaling artisan infrastructure worldwide.
                </div>
            </div>
        </body>
        </html>
        """

    async def send_verification_email(self, to_email: str, user_name: str, verification_url: str):
        """Send branded verification email"""
        html_content = self._get_base_template(f"""
            <h1>Verify your precision workspace</h1>
            <p>Welcome to KORRA, {user_name}. Your industrial-grade biometrics portal is ready. Please verify your email to initialize your workspace.</p>
            <a href="{verification_url}" class="btn">Verify Portal</a>
            <p style="margin-top: 32px; font-size: 12px;">If you didn't request this, you can safely ignore this email.</p>
        """)

        try:
            email = SendSmtpEmail(
                to=[SendSmtpEmailTo(email=to_email)],
                sender=self.sender,
                subject="Verify your KORRA Portal",
                html_content=html_content
            )
            self.email_api.send_transac_email(email)
            logger.info(f"Verification email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False

    async def send_password_reset_email(self, to_email: str, reset_url: str):
        """Send branded password reset email"""
        html_content = self._get_base_template(f"""
            <h1>Reset your access key</h1>
            <p>We received a request to reset your password for your KORRA account. Click the button below to secure your identity.</p>
            <a href="{reset_url}" class="btn">Secure Identity</a>
            <p style="margin-top: 32px; font-size: 12px;">If you didn't request a password reset, please secure your account immediately.</p>
        """)

        try:
            email = SendSmtpEmail(
                to=[SendSmtpEmailTo(email=to_email)],
                sender=self.sender,
                subject="Secure your KORRA Identity",
                html_content=html_content
            )
            self.email_api.send_transac_email(email)
            logger.info(f"Password reset email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False
