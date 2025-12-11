
from twilio.rest import Client
from app.core.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

def send_sms(phone_number: str, otp: str) -> dict:
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your OTP code is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False
