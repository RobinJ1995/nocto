"""Plumbing shared by the step modules: talking to the mocks and waiting on the bots."""
import base64
import itertools
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

import requests

TELEGRAM_MOCK_URL = os.environ.get("TELEGRAM_MOCK_URL", "http://telegram-mock:8081")
HTTP_MOCK_URL = os.environ.get("HTTP_MOCK_URL", "http://http-mock:8090")
REPLY_TIMEOUT = float(os.environ.get("REPLY_TIMEOUT", "15"))
NEGATIVE_GRACE = float(os.environ.get("NEGATIVE_GRACE", "2"))
POLL_INTERVAL = 0.2

OWNER = {"id": 1, "first_name": "Owner", "username": "owner"}
REPLY_METHODS = (
    "sendMessage", "sendPhoto", "sendDocument", "sendSticker", "sendAudio",
    "sendVoice", "sendVideo", "sendLocation", "forwardMessage",
)


@dataclass(frozen=True)
class Bot:
    name: str
    token: str
    username: str
    web: Optional[str]


BOTS = {
    "main": Bot("main", "1001:main", "nocto_main_bot", "http://nocto:3000"),
    "strict": Bot("strict", "1002:strict", "nocto_strict_bot", "http://nocto-strict:3000"),
    "pristine": Bot("pristine", "1003:pristine", "nocto_pristine_bot", None),
}

_message_ids = itertools.count(1)


def wait_until(predicate: Callable[[], Any], timeout: float = REPLY_TIMEOUT) -> Any:
    deadline = time.time() + timeout
    while True:
        result = predicate()
        if result or time.time() >= deadline:
            return result
        time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Telegram mock
# ---------------------------------------------------------------------------

def user_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"id": int(user["id"]), "is_bot": False, "first_name": user.get("first_name", "Tester")}
    if user.get("username"):
        payload["username"] = user["username"]
    return payload


def message(chat_id: int, user: Dict[str, Any], text: Optional[str] = None,
            date: Optional[int] = None, **extra: Any) -> Dict[str, Any]:
    msg: Dict[str, Any] = {
        "message_id": next(_message_ids),
        "date": int(time.time()) if date is None else date,
        "chat": {"id": int(chat_id), "type": "private" if chat_id >= 0 else "group"},
        "from": user_payload(user),
    }
    if text is not None:
        msg["text"] = text
    msg.update(extra)
    return msg


def inline_query(user: Dict[str, Any], query: str) -> Dict[str, Any]:
    return {
        "inline_query": {"id": str(next(_message_ids)), "from": user_payload(user), "query": query, "offset": ""},
    }


def inject(bot: Bot, *updates: Dict[str, Any]) -> List[int]:
    resp = requests.post(f"{TELEGRAM_MOCK_URL}/test/{bot.token}/updates", json=list(updates), timeout=5)
    resp.raise_for_status()
    return resp.json()["update_ids"]


def is_acked(bot: Bot, update_id: int) -> bool:
    resp = requests.get(f"{TELEGRAM_MOCK_URL}/test/{bot.token}/acked",
                        params={"update_id": update_id}, timeout=5)
    resp.raise_for_status()
    return resp.json()["acked"]


def wait_acked(bot: Bot, update_ids: Iterable[int]) -> None:
    last = max(update_ids)
    assert wait_until(lambda: is_acked(bot, last)), f"{bot.name} bot never picked up update {last}"


def calls(bot: Bot, chat_id: Optional[int] = None, method: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {}
    if chat_id is not None:
        params["chat_id"] = str(chat_id)
    if method is not None:
        params["method"] = method
    resp = requests.get(f"{TELEGRAM_MOCK_URL}/test/{bot.token}/calls", params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()["calls"]


def last_seq(bot: Bot) -> int:
    return max((c["seq"] for c in calls(bot)), default=0)


def replies_since(bot: Bot, chat_id: int, seq: int, methods: Iterable[str] = REPLY_METHODS) -> List[Dict[str, Any]]:
    return [c for c in calls(bot, chat_id) if c["seq"] > seq and c["method"] in methods]


def wait_for_reply(
    bot: Bot, chat_id: int, seq: int,
    methods: Iterable[str] = REPLY_METHODS, timeout: float = REPLY_TIMEOUT,
) -> Optional[Dict[str, Any]]:
    found = wait_until(lambda: replies_since(bot, chat_id, seq, methods), timeout)
    return found[0] if found else None


def settle(bot: Bot, update_ids: Iterable[int]) -> None:
    """Wait until the bot has fetched the updates, then long enough to have answered them."""
    wait_acked(bot, update_ids)
    time.sleep(NEGATIVE_GRACE)


def register_file(file_id: str, content: bytes, file_path: Optional[str] = None) -> None:
    body = {"file_id": file_id, "content_b64": base64.b64encode(content).decode()}
    if file_path:
        body["file_path"] = file_path
    requests.post(f"{TELEGRAM_MOCK_URL}/test/files", json=body, timeout=5).raise_for_status()


def file_downloads(file_id: str) -> int:
    resp = requests.get(f"{TELEGRAM_MOCK_URL}/test/files/{file_id}", timeout=5)
    resp.raise_for_status()
    return resp.json()["downloads"]


def reset_mocks() -> None:
    requests.post(f"{TELEGRAM_MOCK_URL}/test/reset", timeout=5).raise_for_status()
    requests.post(f"{HTTP_MOCK_URL}/test/reset", timeout=5).raise_for_status()


def next_reply(context: Any, timeout: float = REPLY_TIMEOUT) -> Dict[str, Any]:
    """Consume the bot's next message in the chat the last update was sent to."""
    reply = wait_for_reply(context.bot, context.reply_chat, context.cursor, ("sendMessage",), timeout)
    assert reply, f"Expected the {context.bot.name} bot to reply in chat {context.reply_chat}, but it stayed silent"
    context.cursor = reply["seq"]
    context.last_reply = reply
    return reply


def converse(
    bot: Bot, user: Dict[str, Any], chat_id: int, text: str,
    expect: Optional[Callable[[str], bool]] = None, timeout: float = REPLY_TIMEOUT,
) -> str:
    """Send a command and return the bot's first reply to it."""
    seq = last_seq(bot)
    inject(bot, message(chat_id, user, text))
    reply = wait_for_reply(bot, chat_id, seq, ("sendMessage",), timeout)
    assert reply, f"{bot.name} bot did not answer {text!r}"
    reply_text = reply["params"].get("text", "")
    assert expect is None or expect(reply_text), f"Unexpected answer to {text!r}: {reply_text!r}"
    return reply_text


# ---------------------------------------------------------------------------
# HTTP mock
# ---------------------------------------------------------------------------

def set_suggestions(query: str, **response: Any) -> None:
    requests.post(f"{HTTP_MOCK_URL}/test/suggest", json={"q": query, **response}, timeout=5).raise_for_status()


def suggest_requests(query: str) -> List[Dict[str, Any]]:
    resp = requests.get(f"{HTTP_MOCK_URL}/test/suggest/requests", params={"q": query}, timeout=5)
    resp.raise_for_status()
    return resp.json()["requests"]
