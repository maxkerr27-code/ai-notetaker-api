import os
from twilio.rest import Client

# Environment variables from Render
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")  # <- use this name everywhere
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")          # your Twilio purchased number

def send_sms(to_phone: str, message: str):
    try:
        print("Sending SMS via Twilio:", to_phone, message)
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=to_phone,
        )
        print("📨 SMS sent — SID:", msg.sid)
    except Exception as e:
        print("❌ SMS ERROR:", e)
