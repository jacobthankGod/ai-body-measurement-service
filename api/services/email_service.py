"""
Brevo Email Service
==================
Handles all transactional and authentication emails via Brevo (formerly Sendinblue).
Extends to Unicorn Sync notifications.
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

    # ============================================================
    # UNICORN SYNC EMAIL METHODS (Phase 2)
    # ============================================================

    async def send_scan_completed_email(
        self,
        to_email: str,
        merchant_name: str,
        client_name: str,
        measurement_summary: dict,
        dashboard_url: str
    ):
        """Send notification when client scan completes"""
        # Build measurement summary HTML
        summary_html = ""
        for key, value in measurement_summary.items():
            summary_html += f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <span style="color: #A3A3A3;">{key}</span>
                <span style="color: #57D7C0; font-weight: 600;">{value}cm</span>
            </div>
            """

        html_content = self._get_base_template(f"""
            <h1>New Body Scan Received</h1>
            <p>You have a new scan from <strong>{client_name}</strong>.</p>
            
            <div style="background: rgba(255,255,255,0.03); border-radius: 16px; padding: 24px; margin: 24px 0; text-align: left;">
                {summary_html}
            </div>
            
            <a href="{dashboard_url}" class="btn">View in Dashboard</a>
            <p style="margin-top: 32px; font-size: 12px;">Measurement synced to your account.</p>
        """)

        try:
            email = SendSmtpEmail(
                to=[SendSmtpEmailTo(email=to_email)],
                sender=self.sender,
                subject=f"New scan from {client_name} | KORRA",
                html_content=html_content
            )
            self.email_api.send_transac_email(email)
            logger.info(f"Scan completed email sent to merchant: {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send scan completed email: {e}")
            return False

    async def send_scan_request_email(
        self,
        to_email: str,
        client_name: str,
        merchant_name: str,
        scan_url: str,
        specialty: str = 'standard',
        message: str = None
    ):
        """Send re-scan request to client"""
        specialty_display = {
            'standard': 'Standard Measurement',
            'agbada': 'Agbada/Igbo Traditional',
            'senator': 'Senator Wear',
            'kurta': 'Kurta/Pakistani',
            'abaya': 'Abaya/Arabian'
        }.get(specialty, specialty.title())

        message_html = f"""
            <p style="color: #A3A3A3; font-size: 14px; line-height: 1.6; margin: 24px 0;">
                {message}
            </p>
        """ if message else ""

        html_content = self._get_base_template(f"""
            <h1>Scan Request</h1>
            <p><strong>{merchant_name}</strong> has requested a new body scan.</p>
            {message_html}
            <p style="color: #A3A3A3; font-size: 14px; line-height: 1.6;">
                Category: <span style="color: #57D7C0;">{specialty_display}</span>
            </p>
            
            <a href="{scan_url}" class="btn">Start Scan</a>
            <p style="margin-top: 32px; font-size: 12px;">This request expires in 7 days.</p>
        """)

        try:
            email = SendSmtpEmail(
                to=[SendSmtpEmailTo(email=to_email)],
                sender=self.sender,
                subject=f"Scan Request from {merchant_name} | KORRA",
                html_content=html_content
            )
            self.email_api.send_transac_email(email)
            logger.info(f"Scan request email sent to client: {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send scan request email: {e}")
            return False

    async def send_measurement_shared_email(
        self,
        to_email: str,
        owner_name: str,
        merchant_name: str,
        measurement_summary: dict,
        view_url: str
    ):
        """Notify client their measurement was shared with a merchant"""
        summary_html = ""
        for key, value in measurement_summary.items():
            summary_html += f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                <span style="color: #A3A3A3;">{key}</span>
                <span style="color: #57D7C0; font-weight: 600;">{value}cm</span>
            </div>
            """

        html_content = self._get_base_template(f"""
            <h1>Measurement Shared</h1>
            <p>Your measurement profile has been shared with <strong>{merchant_name}</strong>.</p>
            
            <div style="background: rgba(255,255,255,0.03); border-radius: 16px; padding: 24px; margin: 24px 0; text-align: left;">
                {summary_html}
            </div>
            
            <a href="{view_url}" class="btn">View Profile</a>
            <p style="margin-top: 32px; font-size: 12px;">
                You can manage sharing in your Size Passport.
            </p>
        """)

        try:
            email = SendSmtpEmail(
                to=[SendSmtpEmailTo(email=to_email)],
                sender=self.sender,
                subject=f"Measurement shared with {merchant_name} | KORRA",
                html_content=html_content
            )
            self.email_api.send_transac_email(email)
            logger.info(f"Measurement shared email sent to: {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send measurement shared email: {e}")
            return False


# Singleton instance
email_service = EmailService()
