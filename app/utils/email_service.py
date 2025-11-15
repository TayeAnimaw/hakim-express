# app/utils/email_service.py

from email.message import EmailMessage
import aiosmtplib
from app.core.config import settings

async def send_email_async(subject: str, recipient: str, body: str):
    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_ADDRESS}>"
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.MAIL_HOST,
            port=settings.MAIL_PORT,
            username=settings.MAIL_USERNAME,
            password=settings.MAIL_PASSWORD,
            use_tls=(settings.MAIL_ENCRYPTION == "ssl")
        )
        print("emial sent successfully")
        return {"message": "Email sent successfully"}
    except Exception as e:
        print(f"================= {e} =============")
        return {"error": str(e)}


def normalize_email(email: str) -> str:
    if not email:
        return ""
    return email.strip().lower()
