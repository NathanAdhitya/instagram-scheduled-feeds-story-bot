from gotify import Gotify

from dotenv import load_dotenv
import os
load_dotenv()

gotify = Gotify(
    base_url=os.environ.get("GOTIFY_BASE_URL"),
    app_token=os.environ.get("GOTIFY_TOKEN"),
)


def send_notification(message: str, title: str):
    gotify.create_message(
        message,
        title=title,
        priority=5,
    )
