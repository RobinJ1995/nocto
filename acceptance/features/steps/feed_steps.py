"""Driving the fake feeds that feedannounce polls."""
import time
from typing import List

from behave import given, then, when, use_step_matcher
from behave.runner import Context

import helpers

use_step_matcher("parse")


def feed_url(name: str) -> str:
    return f"http://feeds.nocto.test:8090/feeds/{name}.xml"


@given('a feed "{name}" titled "{title}" with an entry "{entry}"')
def step_feed_with_entry(context: Context, name: str, title: str, entry: str) -> None:
    helpers.configure_feed(name, title=title)
    helpers.publish_entries(name, [{"title": entry, "link": f"https://example.com/{name}/old"}])


@given('the feed "{name}" uses ETags')
def step_feed_etags(context: Context, name: str) -> None:
    helpers.configure_feed(name, etag=True)


@given('the feed "{name}" uses Last-Modified dates')
def step_feed_last_modified(context: Context, name: str) -> None:
    helpers.configure_feed(name, last_modified=True)


@given('the owner has registered the feed "{name}"')
def step_register_feed(context: Context, name: str) -> None:
    helpers.converse(
        context.bot, helpers.OWNER, helpers.OWNER["id"], f"/addfeed {name} {feed_url(name)}",
        lambda reply: reply == f'Feed "{name}" registered.',
    )


@when('the owner removes the feed "{name}"')
def step_remove_feed(context: Context, name: str) -> None:
    helpers.converse(
        context.bot, helpers.OWNER, helpers.OWNER["id"], f"/delfeed {name}",
        lambda reply: reply == f'Feed "{name}" removed.',
    )


@when('the feed "{name}" has been checked')
def step_feed_checked(context: Context, name: str) -> None:
    helpers.wait_feed_checked(name)


@when('the feed "{name}" has been checked {times:d} more times')
def step_feed_checked_times(context: Context, name: str, times: int) -> None:
    helpers.wait_feed_checked(name, times)


@when('the feed "{name}" publishes the entry "{title}" linking to "{link}" by "{author}"')
def step_publish_with_author(context: Context, name: str, title: str, link: str, author: str) -> None:
    helpers.publish_entries(name, [{"title": title, "link": link, "author": author}])


@when('the feed "{name}" publishes the entry "{title}" linking to "{link}"')
def step_publish(context: Context, name: str, title: str, link: str) -> None:
    helpers.publish_entries(name, [{"title": title, "link": link}])


@when('the feed "{name}" publishes these entries')
def step_publish_table(context: Context, name: str) -> None:
    helpers.publish_entries(name, [{"title": row["title"], "link": row["link"]} for row in context.table])


@when('the feed "{name}" starts failing with status {status:d}')
def step_feed_fails(context: Context, name: str, status: int) -> None:
    helpers.configure_feed(name, status=status)


@when('the feed "{name}" recovers')
def step_feed_recovers(context: Context, name: str) -> None:
    helpers.configure_feed(name, status=200)


@when("{seconds:d} seconds pass")
def step_seconds_pass(context: Context, seconds: int) -> None:
    time.sleep(seconds)


def _announcements(context: Context, chat_id: int) -> List[str]:
    return [c["params"].get("text", "")
            for c in helpers.replies_since(context.bot, chat_id, context.cursor, ("sendMessage",))]


@then("the chat receives the announcement")
def step_receives_announcement(context: Context) -> None:
    actual = helpers.next_reply(context)["params"].get("text", "")
    assert actual == context.text, f"Expected announcement {context.text!r}, got {actual!r}"


@then('chat {chat_id:d} receives an announcement containing "{text}"')
def step_chat_receives(context: Context, chat_id: int, text: str) -> None:
    found = helpers.wait_until(lambda: any(text in t for t in _announcements(context, chat_id)))
    assert found, f"Chat {chat_id} got no announcement containing {text!r}: {_announcements(context, chat_id)!r}"


@then('the chat receives no announcement after {times:d} more checks of "{name}"')
def step_no_announcement(context: Context, times: int, name: str) -> None:
    helpers.wait_feed_checked(name, times)
    time.sleep(helpers.NEGATIVE_GRACE)
    sent = _announcements(context, context.reply_chat)
    assert not sent, f"Expected no announcement, got {sent!r}"


@then('chat {chat_id:d} receives no announcement after {times:d} more checks of "{name}"')
def step_chat_no_announcement(context: Context, chat_id: int, times: int, name: str) -> None:
    helpers.wait_feed_checked(name, times)
    time.sleep(helpers.NEGATIVE_GRACE)
    sent = _announcements(context, chat_id)
    assert not sent, f"Expected no announcement in chat {chat_id}, got {sent!r}"


@then("the chat receives no announcement within {seconds:d} seconds")
def step_no_announcement_within(context: Context, seconds: int) -> None:
    time.sleep(seconds)
    sent = _announcements(context, context.reply_chat)
    assert not sent, f"Expected no announcement, got {sent!r}"


@then('the latest request for "{name}" carried the header "{header}"')
def step_request_header(context: Context, name: str, header: str) -> None:
    latest = helpers.feed_requests(name)[-1]["headers"]
    assert header in latest, f"Expected a {header} header, got {sorted(latest)!r}"
