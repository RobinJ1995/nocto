"""Fetching media through the bot's built-in web server."""
import re

import requests
from behave import then, when, use_step_matcher
from behave.runner import Context

import helpers

use_step_matcher("parse")


def _fetch(context: Context, url: str) -> None:
    context.download = requests.get(url, timeout=10)


def _permalink(context: Context) -> str:
    if context.last_reply is None:
        helpers.next_reply(context)
    text = context.last_reply["params"].get("text", "")
    assert re.match(r"^https?://", text), f"Expected a permalink, got {text!r}"
    return text


@when("the permalink is downloaded")
def step_download_permalink(context: Context) -> None:
    _fetch(context, _permalink(context))


@when('the permalink is remembered as "{name}"')
def step_remember_permalink(context: Context, name: str) -> None:
    context.permalinks = getattr(context, "permalinks", {})
    context.permalinks[name] = _permalink(context)


@when('the permalink "{name}" is downloaded')
def step_download_remembered(context: Context, name: str) -> None:
    _fetch(context, context.permalinks[name])


@when('"{path}" is downloaded from the bot')
def step_download_path(context: Context, path: str) -> None:
    _fetch(context, context.bot.web + path)


@then('the permalink is "{path}"')
def step_permalink_is(context: Context, path: str) -> None:
    expected = context.bot.web + path
    actual = _permalink(context)
    assert actual == expected, f"Expected permalink {expected!r}, got {actual!r}"


@then('the download contains the file "{file_id}"')
def step_download_contains(context: Context, file_id: str) -> None:
    assert context.download.status_code == 200, f"Download failed with {context.download.status_code}"
    assert context.download.content == context.files[file_id], "Downloaded bytes differ from the file"


@then('the download has content type "{content_type}" and is shown inline')
def step_download_type(context: Context, content_type: str) -> None:
    headers = context.download.headers
    assert headers.get("content-type", "").startswith(content_type), \
        f"Expected content type {content_type!r}, got {headers.get('content-type')!r}"
    assert headers.get("content-disposition") == "inline", \
        f"Expected inline disposition, got {headers.get('content-disposition')!r}"


@then("the download fails")
def step_download_fails(context: Context) -> None:
    assert context.download.status_code >= 400, f"Expected an error, got {context.download.status_code}"


@then("the download fails with status {status:d}")
def step_download_fails_with(context: Context, status: int) -> None:
    assert context.download.status_code == status, \
        f"Expected status {status}, got {context.download.status_code}"


@then('the bot looked up the file "{file_id}" {count:d} time(s)')
def step_file_lookups(context: Context, file_id: str, count: int) -> None:
    lookups = [c for c in helpers.calls(context.bot, method="getFile") if c["params"].get("file_id") == file_id]
    assert len(lookups) == count, f"Expected {count} lookups of {file_id}, got {len(lookups)}"


@then('the permalink does not reveal "{file_id}"')
def step_permalink_hides(context: Context, file_id: str) -> None:
    assert file_id not in _permalink(context), "The permalink exposes the Telegram file id"


@then('the permalinks "{first}" and "{second}" differ')
def step_permalinks_differ(context: Context, first: str, second: str) -> None:
    assert context.permalinks[first] != context.permalinks[second], "Both permalinks are identical"
