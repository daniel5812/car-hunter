import httpx

from .config import ServiceError, required


def send(text: str) -> int:
    # Do not log raw exceptions: Telegram embeds the token in the request URL.
    url = "https://api.telegram.org/bot" + required("TELEGRAM_BOT_TOKEN") + "/sendMessage"
    with httpx.Client(timeout=25) as client:
        response = client.post(url, json={"chat_id": required("TELEGRAM_CHAT_ID"),
                                          "text": text[:4000], "link_preview_options": {"is_disabled": True}})
    if response.status_code != 200:
        raise ServiceError(f"Telegram HTTP {response.status_code}")
    data = response.json()
    if not data.get("ok"):
        raise ServiceError("Telegram rejected message")
    return data["result"]["message_id"]
