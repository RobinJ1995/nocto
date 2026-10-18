"""Controlling the fake Google suggestion service."""
from behave import given, then, use_step_matcher
from behave.runner import Context

import helpers

use_step_matcher("parse")


@given('the suggestion service suggests for "{query}"')
def step_suggests(context: Context, query: str) -> None:
    helpers.set_suggestions(query, suggestions=[row["suggestion"] for row in context.table])


@given('the suggestion service fails with status {status:d} for "{query}"')
def step_suggest_fails(context: Context, status: int, query: str) -> None:
    helpers.set_suggestions(query, status=status)


@given('the suggestion service is unreachable for "{query}"')
def step_suggest_unreachable(context: Context, query: str) -> None:
    helpers.set_suggestions(query, unreachable=True)


@given('the suggestion service answers "{body}" for "{query}"')
def step_suggest_body(context: Context, body: str, query: str) -> None:
    helpers.set_suggestions(query, body=body)


def _requests(query: str) -> list:
    found = helpers.wait_until(lambda: helpers.suggest_requests(query))
    assert found, f"The suggestion service was never asked for {query!r}"
    return found


@then('the suggestion service was asked for "{query}" in language "{language}"')
def step_suggest_language(context: Context, query: str, language: str) -> None:
    actual = _requests(query)[-1]["args"].get("hl")
    assert actual == language, f"Expected language {language!r}, got {actual!r}"


@then('the suggestion service was asked for "{query}" by a client identifying as "{prefix}"')
def step_suggest_user_agent(context: Context, query: str, prefix: str) -> None:
    actual = _requests(query)[-1]["headers"].get("User-Agent", "")
    assert actual.startswith(prefix), f"Expected a User-Agent starting with {prefix!r}, got {actual!r}"
