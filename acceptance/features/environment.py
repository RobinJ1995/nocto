import os
import sys
import time

import requests
from behave.model import Scenario
from behave.runner import Context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "steps"))
import helpers  # noqa: E402

STARTUP_TIMEOUT = 120


def _wait_for_health(url: str) -> None:
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            if requests.get(url, timeout=3).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"{url} never became healthy")


def _until_answered(bot: helpers.Bot, user: dict, text: str, accept: set) -> None:
    # Retried because messages sent before the bot starts polling are stale and ignored.
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        seq = helpers.last_seq(bot)
        helpers.inject(bot, helpers.message(user["id"], user, text))
        if helpers.wait_until(
            lambda: any(c["params"].get("text") in accept
                        for c in helpers.replies_since(bot, user["id"], seq, ("sendMessage",))),
            timeout=3,
        ):
            return
    raise RuntimeError(f"{bot.name} bot never answered {text!r}")


def before_all(context: Context) -> None:
    _wait_for_health(f"{helpers.TELEGRAM_MOCK_URL}/test/health")
    _wait_for_health(f"{helpers.HTTP_MOCK_URL}/test/health")
    claimed = {"You are now registered as my owner.", "I already have an owner."}
    for name in ("main", "strict"):
        _until_answered(helpers.BOTS[name], helpers.OWNER, "/owner", claimed)
    _until_answered(helpers.BOTS["pristine"], {"id": 2, "first_name": "Warmup"}, "/echo warmup", {"warmup"})
    helpers.reset_mocks()


def before_scenario(context: Context, scenario: Scenario) -> None:
    helpers.reset_mocks()
    tags = set(scenario.effective_tags)
    context.bot = helpers.BOTS[next((name for name in ("strict", "pristine") if name in tags), "main")]
    context.user = {"id": 5000, "first_name": "Tester", "username": "tester"}
    context.chat_id = -5000
    context.cursor = 0
    context.sent = []
    context.last_reply = None
    context.plugin_toggles = []


def after_scenario(context: Context, scenario: Scenario) -> None:
    for bot, plugin, operation in reversed(context.plugin_toggles):
        helpers.converse(bot, helpers.OWNER, helpers.OWNER["id"], f"/plugins {operation} {plugin}")
