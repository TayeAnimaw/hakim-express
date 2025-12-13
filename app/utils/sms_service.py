
from twilio.rest import Client
from app.core.config import settings
def send_sms(phone_number: str, otp: str) -> dict:
    
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=otp,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False
