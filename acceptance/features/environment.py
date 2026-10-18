import os
import sys
import time

import requests
from behave.model import Feature, Scenario
from behave.runner import Context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "steps"))
import helpers  # noqa: E402
from irc_client import IrcClient  # noqa: E402

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


def before_feature(context: Context, feature: Feature) -> None:
    if "irc" not in feature.tags:
        return
    # A channel operator for kicks, topics and modes. Joining also proves the bridge is in place.
    context.chanop = IrcClient("chanop", "Channel Operator")
    context.chanop.oper()
    for chan in ("#bridge-one", "#bridge-two", "#bridge-shared", "#multi-a", "#multi-b",
                 "#readonly", "#copy-src", "#copy-dst"):
        _join_with_bridge(context.chanop, chan)
        context.chanop.send(f"SAMODE {chan} +o chanop")
    time.sleep(1)


def _join_with_bridge(client: IrcClient, chan: str) -> None:
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        since = client.mark()
        client.join(chan)
        names = " ".join(l.text for l in client.find(lambda l: l.command == "353", since))
        if any(nick.lstrip("@+").startswith("nocto") for nick in names.split()):
            return
        client.send(f"PART {chan}")
        time.sleep(1)
    raise RuntimeError(f"The bridge never joined {chan}")


def after_feature(context: Context, feature: Feature) -> None:
    if "irc" in feature.tags:
        context.chanop.quit()
        time.sleep(1)


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
    context.irc = {}


def after_scenario(context: Context, scenario: Scenario) -> None:
    for irc in context.irc.values():
        irc.quit()
    if context.irc:
        # Let the bridge relay the quits before the next scenario resets the mocks.
        time.sleep(1.5)
    for bot, plugin, operation in reversed(context.plugin_toggles):
        helpers.converse(bot, helpers.OWNER, helpers.OWNER["id"], f"/plugins {operation} {plugin}")
