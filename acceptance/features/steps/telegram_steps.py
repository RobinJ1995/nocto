"""Talking to the bot as Telegram users and asserting on what it sends back.

Uses the regex matcher (anchored at both ends) so generic steps such as
'the user sends "..."' can't swallow their more specific variants.
"""
import datetime
import os
import re
import time
import zoneinfo
from typing import Any, Dict, List, Optional

from behave import given, then, when, use_step_matcher
from behave.runner import Context

import helpers

use_step_matcher("re")

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
MAGIC = {
    "WebP": lambda m: m.startswith("52494646") and m[16:24] == "57454250",
    "PNG": lambda m: m.startswith("89504e47"),
}


def _user(user_id: str, first_name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
    uid = int(user_id)
    return {"id": uid, "first_name": first_name or f"User{uid}", "username": username or f"user{uid}"}


def _chat_for(context: Context, user: Dict[str, Any]) -> int:
    return user["id"] if getattr(context, "private", False) else context.chat_id


def send(context: Context, user: Dict[str, Any], *messages: Dict[str, Any]) -> None:
    context.cursor = helpers.last_seq(context.bot)
    context.last_reply = None
    context.reply_chat = messages[0]["chat"]["id"]
    context.sent_messages = list(messages)
    context.sent = helpers.inject(context.bot, *messages)


def send_text(context: Context, user: Dict[str, Any], text: str, **extra: Any) -> None:
    send(context, user, helpers.message(_chat_for(context, user), user, text, **extra))


def reply_text(context: Context, timeout: float = helpers.REPLY_TIMEOUT) -> str:
    return helpers.next_reply(context, timeout)["params"].get("text", "")


def last_reply(context: Context) -> Dict[str, Any]:
    if context.last_reply is None:
        helpers.next_reply(context)
    return context.last_reply


def texts_since(context: Context, chat_id: int, seq: int) -> List[str]:
    return [c["params"].get("text", "") for c in helpers.replies_since(context.bot, chat_id, seq, ("sendMessage",))]


# ---------------------------------------------------------------------------
# Given: who is talking, and where
# ---------------------------------------------------------------------------

@given(r"the (?P<name>main|strict|pristine) bot")
def step_bot(context: Context, name: str) -> None:
    context.bot = helpers.BOTS[name]


@given(r"a group chat with id (?P<chat_id>-\d+)")
def step_group_chat(context: Context, chat_id: str) -> None:
    context.chat_id = int(chat_id)
    context.private = False


@given(r"a private chat")
def step_private_chat(context: Context) -> None:
    context.private = True


@given(r'a user with id (?P<user_id>\d+) and first name "(?P<name>[^"]*)"')
def step_user(context: Context, user_id: str, name: str) -> None:
    context.user = _user(user_id, name, name.lower())


@given(r'a user with id (?P<user_id>\d+) and first name "(?P<name>[^"]*)" without a username')
def step_user_without_username(context: Context, user_id: str, name: str) -> None:
    context.user = {"id": int(user_id), "first_name": name}


@given(r'a user with id (?P<user_id>\d+) and first name "(?P<name>[^"]*)" and username "(?P<username>[^"]*)"')
def step_user_with_username(context: Context, user_id: str, name: str, username: str) -> None:
    context.user = _user(user_id, name, username)


@given(r"the user is the owner")
def step_user_is_owner(context: Context) -> None:
    context.user = dict(helpers.OWNER)


@given(r'the file "(?P<file_id>[^"]*)" contains "(?P<content>[^"]*)"')
def step_file_contains(context: Context, file_id: str, content: str) -> None:
    helpers.register_file(file_id, content.encode())
    context.files = getattr(context, "files", {})
    context.files[file_id] = content.encode()


@given(r'the file "(?P<file_id>[^"]*)" is the image "(?P<fixture>[^"]*)"')
def step_file_is_image(context: Context, file_id: str, fixture: str) -> None:
    with open(os.path.join(FIXTURES, fixture), "rb") as fh:
        helpers.register_file(file_id, fh.read())


@given(r'Telegram drops the connection when the file "(?P<file_id>[^"]*)" is downloaded')
def step_file_drops(context: Context, file_id: str) -> None:
    helpers.register_file(file_id, b"never arrives", drop=True)


# ---------------------------------------------------------------------------
# When: sending messages
# ---------------------------------------------------------------------------

@when(r'the user sends "(?P<text>[^"]*)"')
def step_user_sends(context: Context, text: str) -> None:
    send_text(context, context.user, text)


@when(r'user (?P<user_id>\d+) sends "(?P<text>[^"]*)"')
def step_other_user_sends(context: Context, user_id: str, text: str) -> None:
    send_text(context, _user(user_id), text)


@when(r'user (?P<user_id>\d+) sends "(?P<text>[^"]*)" in chat (?P<chat_id>-?\d+)')
def step_other_user_sends_in_chat(context: Context, user_id: str, text: str, chat_id: str) -> None:
    send(context, _user(user_id), helpers.message(int(chat_id), _user(user_id), text))


@when(r'the owner sends "(?P<text>[^"]*)"')
def step_owner_sends(context: Context, text: str) -> None:
    send_text(context, helpers.OWNER, text)


@when(r'the user sends "(?P<text>[^"]*)" dated yesterday')
def step_user_sends_backlog(context: Context, text: str) -> None:
    send_text(context, context.user, text, date=int(time.time()) - 86400)


@when(r"the user sends these lines")
def step_user_sends_lines(context: Context) -> None:
    send_text(context, context.user, context.text)


@when(r"(?:the user|user (?P<user_id>\d+)) quickly sends")
def step_user_sends_batch(context: Context, user_id: Optional[str] = None) -> None:
    user = _user(user_id) if user_id else context.user
    chat_id = _chat_for(context, user)
    send(context, user, *(helpers.message(chat_id, user, row["text"]) for row in context.table))


@when(r'the user sends a photo "(?P<file_id>[^"]*)"(?P<backlog> dated yesterday)?')
def step_send_photo(context: Context, file_id: str, backlog: Optional[str]) -> None:
    sizes = [
        {"file_id": f"{file_id}-small", "width": 90, "height": 90},
        {"file_id": file_id, "width": 800, "height": 800},
    ]
    date = int(time.time()) - 86400 if backlog else None
    send_text(context, context.user, None, photo=sizes, date=date)


@when(r'the user sends a sticker "(?P<file_id>[^"]*)"')
def step_send_sticker(context: Context, file_id: str) -> None:
    send_text(context, context.user, None, sticker={"file_id": file_id, "width": 512, "height": 512})


@when(r'the user sends a document "(?P<file_id>[^"]*)" named "(?P<name>[^"]*)" of type "(?P<mime>[^"]*)"')
def step_send_document(context: Context, file_id: str, name: str, mime: str) -> None:
    send_text(context, context.user, None, document={"file_id": file_id, "file_name": name, "mime_type": mime})


@when(r'the user sends an audio file "(?P<file_id>[^"]*)" titled "(?P<title>[^"]*)" by "(?P<performer>[^"]*)"')
def step_send_audio(context: Context, file_id: str, title: str, performer: str) -> None:
    send_text(
        context, context.user, None,
        audio={"file_id": file_id, "title": title, "performer": performer, "mime_type": "audio/mpeg"},
    )


@when(r'the user sends a voice message "(?P<file_id>[^"]*)"(?: of type "(?P<mime>[^"]*)")?')
def step_send_voice(context: Context, file_id: str, mime: Optional[str]) -> None:
    voice = {"file_id": file_id, "duration": 3}
    if mime:
        voice["mime_type"] = mime
    send_text(context, context.user, None, voice=voice)


@when(r'the user sends a video "(?P<file_id>[^"]*)" of type "(?P<mime>[^"]*)"')
def step_send_video(context: Context, file_id: str, mime: str) -> None:
    send_text(context, context.user, None, video={"file_id": file_id, "mime_type": mime})


@when(r'the user types the inline query "(?P<query>[^"]*)"')
def step_inline_query(context: Context, query: str) -> None:
    context.cursor = helpers.last_seq(context.bot)
    update = helpers.inline_query(context.user, query)
    context.inline_query_id = update["inline_query"]["id"]
    context.sent = helpers.inject(context.bot, update)


# ---------------------------------------------------------------------------
# Then: replies
# ---------------------------------------------------------------------------

@then(r'the bot replies "(?P<expected>.*)"')
def step_replies(context: Context, expected: str) -> None:
    actual = reply_text(context)
    assert actual == expected, f"Expected reply {expected!r} but got {actual!r}"


@then(r'the bot replies "(?P<expected>.*)" immediately')
def step_replies_immediately(context: Context, expected: str) -> None:
    found = helpers.wait_until(lambda: expected in texts_since(context, context.reply_chat, context.cursor), 2)
    assert found, f"Expected {expected!r} within 2s, got {texts_since(context, context.reply_chat, context.cursor)!r}"


@then(r"the bot replies")
def step_replies_text(context: Context) -> None:
    actual = reply_text(context)
    assert actual == context.text, f"Expected reply {context.text!r} but got {actual!r}"


def _clock(moment: datetime.datetime) -> str:
    return f"{moment.hour % 12 or 12}:{moment.minute:02d}{'am' if moment.hour < 12 else 'pm'}"


@then(r'the bot replies with the current time in (?P<zone>\S+)')
def step_replies_current_time(context: Context, zone: str) -> None:
    actual = reply_text(context)
    now = datetime.datetime.now(zoneinfo.ZoneInfo(zone))
    expected = [f"{zone}: {_clock(now - datetime.timedelta(minutes=delta))}" for delta in (0, 1)]
    assert actual in expected, f"Expected one of {expected!r}, got {actual!r}"


@then(r'the bot reply contains "(?P<expected>.*)"')
def step_reply_contains(context: Context, expected: str) -> None:
    actual = reply_text(context)
    assert expected in actual, f"Expected reply to contain {expected!r}, got {actual!r}"


@then(r'the bot reply matches "(?P<pattern>[^"]*)"')
def step_reply_matches(context: Context, pattern: str) -> None:
    actual = reply_text(context)
    assert re.fullmatch(pattern, actual), f"Expected reply to match {pattern!r}, got {actual!r}"


@then(r'the bot eventually replies "(?P<expected>.*)"')
def step_eventually_replies(context: Context, expected: str) -> None:
    found = helpers.wait_until(lambda: expected in texts_since(context, context.reply_chat, context.cursor))
    assert found, f"Expected {expected!r} eventually, got {texts_since(context, context.reply_chat, context.cursor)!r}"


@then(r'the bot never replies "(?P<unexpected>.*)"')
def step_never_replies(context: Context, unexpected: str) -> None:
    helpers.settle(context.bot, context.sent)
    texts = texts_since(context, context.reply_chat, context.cursor)
    assert unexpected not in texts, f"Did not expect {unexpected!r}, got {texts!r}"


@then(r"the bot sends no reply")
def step_no_reply(context: Context) -> None:
    helpers.settle(context.bot, context.sent)
    sent = helpers.replies_since(context.bot, context.reply_chat, context.cursor)
    assert not sent, f"Expected no reply, got {[(c['method'], c['params'].get('text')) for c in sent]!r}"


@then(r"the bot quotes the user's message")
def step_quotes(context: Context) -> None:
    expected = str(context.sent_messages[-1]["message_id"])
    actual = str(last_reply(context)["params"].get("reply_to_message_id"))
    assert actual == expected, f"Expected a reply to message {expected}, got {actual}"


@then(r"the bot does not quote the user's message")
def step_does_not_quote(context: Context) -> None:
    actual = last_reply(context)["params"].get("reply_to_message_id")
    assert actual is None, f"Expected a plain message, got a reply to {actual}"


@then(r'the bot reply offers the button "(?P<label>[^"]*)"')
def step_offers_button(context: Context, label: str) -> None:
    keyboard = last_reply(context)["params"].get("reply_markup", {}).get("keyboard", [])
    labels = [button for row in keyboard for button in row]
    assert label in labels, f"Expected a {label!r} button, got {labels!r}"


@then(r'the bot reply does not offer the button "(?P<label>[^"]*)"')
def step_does_not_offer_button(context: Context, label: str) -> None:
    keyboard = last_reply(context)["params"].get("reply_markup", {}).get("keyboard", [])
    labels = [button for row in keyboard for button in row]
    assert label not in labels, f"Did not expect a {label!r} button among {labels!r}"


@then(r"the reply keyboard is one-time, selective and resized")
def step_keyboard_flags(context: Context) -> None:
    markup = last_reply(context)["params"].get("reply_markup", {})
    flags = {key: markup.get(key) for key in ("one_time_keyboard", "selective", "resize_keyboard")}
    assert all(flags.values()), f"Unexpected keyboard flags {flags!r}"


@then(r"the bot reply has no link preview")
def step_no_preview(context: Context) -> None:
    value = last_reply(context)["params"].get("disable_web_page_preview")
    assert value in ("true", True), f"Expected link preview to be disabled, got {value!r}"


@then(r"the bot shows that it is typing")
def step_typing(context: Context) -> None:
    found = helpers.wait_until(lambda: [
        c for c in helpers.replies_since(context.bot, context.reply_chat, 0, ("sendChatAction",))
        if c["params"].get("action") == "typing"
    ])
    assert found, "Expected a typing indicator"


@then(r'user (?P<user_id>\d+) is told privately "(?P<expected>.*)" once')
def step_told_privately_once(context: Context, user_id: str, expected: str) -> None:
    def matching() -> List[str]:
        return [t for t in texts_since(context, int(user_id), 0) if t == expected]
    assert helpers.wait_until(matching), f"User {user_id} was never told {expected!r}"
    helpers.settle(context.bot, context.sent)
    assert len(matching()) == 1, f"User {user_id} was told {expected!r} {len(matching())} times"


def _upload(context: Context, method: str) -> Dict[str, Any]:
    call = helpers.wait_for_reply(context.bot, context.reply_chat, context.cursor, (method,))
    assert call, f"Expected the bot to call {method}"
    return call


@then(r"the bot sends a sticker in (?P<kind>WebP) format")
def step_sends_sticker(context: Context, kind: str) -> None:
    upload = _upload(context, "sendSticker")["files"]["sticker"]
    assert MAGIC[kind](upload["magic"]), f"The sticker is not {kind}: {upload!r}"


@then(r'the bot sends the document "(?P<name>[^"]*)" in (?P<kind>PNG) format')
def step_sends_document(context: Context, name: str, kind: str) -> None:
    upload = _upload(context, "sendDocument")["files"]["document"]
    assert upload["filename"] == name, f"Expected {name!r}, got {upload['filename']!r}"
    assert MAGIC[kind](upload["magic"]), f"The document is not {kind}: {upload!r}"


# ---------------------------------------------------------------------------
# Then: inline query answers
# ---------------------------------------------------------------------------

def inline_results(context: Context) -> List[Dict[str, Any]]:
    def answer() -> Optional[Dict[str, Any]]:
        for call in helpers.calls(context.bot, method="answerInlineQuery"):
            if str(call["params"].get("inline_query_id")) == context.inline_query_id:
                return call
        return None
    call = helpers.wait_until(answer)
    assert call, "The inline query was never answered"
    return call["params"].get("results") or []


def _titles(raw: str) -> List[str]:
    return re.findall(r'"([^"]*)"', raw)


@then(r"the inline query is answered with no results")
def step_inline_empty(context: Context) -> None:
    results = inline_results(context)
    assert results == [], f"Expected no results, got {[r.get('title') for r in results]!r}"


@then(r"the first inline results are titled (?P<titles>.+)")
def step_inline_first_titles(context: Context, titles: str) -> None:
    expected = _titles(titles)
    actual = [r.get("title") for r in inline_results(context)]
    assert actual[:len(expected)] == expected, f"Expected results to start with {expected!r}, got {actual!r}"


@then(r"the inline results are titled exactly (?P<titles>.+)")
def step_inline_exact_titles(context: Context, titles: str) -> None:
    expected = _titles(titles)
    actual = [r.get("title") for r in inline_results(context)]
    assert actual == expected, f"Expected results {expected!r}, got {actual!r}"


@then(r'no inline result is titled "(?P<title>[^"]*)"')
def step_inline_not_titled(context: Context, title: str) -> None:
    actual = [r.get("title") for r in inline_results(context)]
    assert title not in actual, f"Did not expect {title!r} among {actual!r}"


@then(r"every inline result has a unique id")
def step_inline_unique_ids(context: Context) -> None:
    ids = [r.get("id") for r in inline_results(context)]
    assert ids and len(ids) == len(set(ids)), f"Inline result ids are not unique: {ids!r}"


@then(r'every inline result shows the cow saying "(?P<text>[^"]*)" in a Markdown code block')
def step_inline_cow_says(context: Context, text: str) -> None:
    for result in inline_results(context):
        content = result.get("input_message_content", {})
        body = content.get("message_text", "")
        assert content.get("parse_mode") == "Markdown", f"{result.get('title')} is not Markdown"
        assert body.startswith("```\n") and body.endswith("\n```"), f"Not a code block: {body!r}"
        assert text in body, f"{result.get('title')} does not say {text!r}: {body!r}"


@then(r'the inline result "(?P<title>[^"]*)" has the thumbnail "(?P<url>[^"]*)"')
def step_inline_thumbnail(context: Context, title: str, url: str) -> None:
    result = next((r for r in inline_results(context) if r.get("title") == title), None)
    assert result, f"No inline result titled {title!r}"
    actual = result.get("thumbnail_url")
    assert actual == url, f"Expected thumbnail {url!r}, got {actual!r}"
