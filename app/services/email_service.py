# app/services/email_service.py
from fastapi_mail import FastMail, MessageSchema
from app.core.config.settings import settings
from app.core.email import get_email_conf


class EmailService:
    def __init__(self):
        conf = get_email_conf(settings)
        self.fm = FastMail(conf)
    async def send_otp(self, email: str, otp: str):
        
        message = MessageSchema(
            subject="Your OTP Code",
            recipients=['linhdevios@gmail.com'],
            body=f"""
                <h2>Your OTP: {otp}</h2>
                <p>This code expires in 5 minutes.</p>
            """,
            subtype="html",
        )
        await self.fm.send_message(message)

    async def send_reset_link(self, email: str, token: str):
        link = f"https://frenzy-wrinkly-stellar.ngrok-free.dev/reset-password?token={token}"

        message = MessageSchema(
            subject="Reset Password",
            recipients=[email],
            body=f"""
                <p>Click below to reset password:</p>
                <a href="{link}">Reset Password</a>
            """,
            subtype="html",
        )
        await self.fm.send_message(message)