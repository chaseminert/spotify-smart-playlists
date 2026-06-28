"""send notifications with pushover"""
import requests
import logging
from settings import get_settings
settings = get_settings()
from requests import HTTPError

logger = logging.getLogger(__name__)

PUSH_APP_TOKEN = settings.PUSH_APP_TOKEN
PUSH_USER_TOKEN = settings.PUSH_USER_TOKEN

def send_noti(title, message, priority=0) -> bool:
    """Send push notification and log the attempt. True if notification was sent. False otherwise"""
    if not PUSH_APP_TOKEN or not PUSH_USER_TOKEN:
        logger.debug("Skipping push notification since environment variables are not set")
        return False
    logger.info(f"Sending push notification: {title} - {message}")
    try:
        res = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSH_APP_TOKEN,
            "user": PUSH_USER_TOKEN,
            "title": title,
            "message": message,
            "priority": priority,
        })
        res.raise_for_status()  # will raise an error if it fails
        logger.info(f"Push notification sent successfully: {title}")
        return True
    except HTTPError as http_err:
        logger.exception(f"Push notification failed to send. (status code: {http_err.status_code})")
        return False
    except Exception as e:
        logger.exception("Push notification failed to send.")
        return False
