"""
SMS alert dispatch.

Real mode: Twilio.
Mock mode: logs the message instead of sending (returned in the response so
tests/demos can assert on it).
"""
import logging
from app.config import TWILIO_ENABLED, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

logger = logging.getLogger("mehfooz.sms")


def send_alert_sms(to_phone: str, message: str, lake_lat: float, lake_lon: float) -> dict:
    full_message = f"{message}\nLocation: {lake_lat}, {lake_lon}"

    if TWILIO_ENABLED:
        return _send_real(to_phone, full_message)
    return _send_mock(to_phone, full_message)


def _send_real(to_phone: str, full_message: str) -> dict:
    from twilio.rest import Client

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(body=full_message, from_=TWILIO_PHONE_NUMBER, to=to_phone)
    return {"status": "sent", "sid": msg.sid, "to": to_phone}


def _send_mock(to_phone: str, full_message: str) -> dict:
    logger.info("MOCK SMS to %s: %s", to_phone, full_message)
    return {"status": "mock_logged", "to": to_phone, "body": full_message}
