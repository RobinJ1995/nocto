"""Setting up users and plugins through the bot's owner."""
import time
from typing import Dict

from behave import given, then, use_step_matcher
from behave.runner import Context

import helpers

use_step_matcher("re")

ADMIN_GROUP = -1
LEVELS = {"trusted user": "trusted", "half-operator": "half-operator",
          "operator": "operator", "administrator": "administrator"}
STATUS = {"loaded and enabled": (True, True), "loaded but disabled": (True, False),
          "not loaded": (False, False)}


def make_known(context: Context, user_id: int) -> None:
    # A join announced by the owner registers the user without the user spending throttle tokens.
    joiner = {"id": user_id, "is_bot": False, "first_name": f"User{user_id}", "username": f"user{user_id}"}
    ids = helpers.inject(context.bot, helpers.message(ADMIN_GROUP, helpers.OWNER, new_chat_participant=joiner))
    helpers.wait_acked(context.bot, ids)
    time.sleep(0.5)


def owner_command(context: Context, text: str, expected_prefix: str) -> str:
    return helpers.converse(context.bot, helpers.OWNER, helpers.OWNER["id"], text,
                            lambda reply: reply.startswith(expected_prefix))


@given(r"(?:the user|user (?P<user_id>\d+)) is known to the bot")
def step_known(context: Context, user_id: str = None) -> None:
    make_known(context, int(user_id or context.user["id"]))


@given(r"user (?P<user_id>\d+) has left the group")
def step_left(context: Context, user_id: str) -> None:
    leaver = {"id": int(user_id), "is_bot": False, "first_name": f"User{user_id}", "username": f"user{user_id}"}
    ids = helpers.inject(context.bot, helpers.message(ADMIN_GROUP, helpers.OWNER, left_chat_participant=leaver))
    helpers.wait_acked(context.bot, ids)
    time.sleep(0.5)


@given(r"(?:the user|user (?P<user_id>\d+)) is an? (?P<level>trusted user|half-operator|operator|administrator)")
def step_user_level(context: Context, level: str, user_id: str = None) -> None:
    user_id = int(user_id or context.user["id"])
    make_known(context, user_id)
    owner_command(context, f"/authority {user_id} {LEVELS[level]}", "Authority level set to")


@given(r'the owner has (?P<operation>enabled|disabled) the "(?P<plugin>[^"]*)" plugin')
def step_toggle_plugin(context: Context, operation: str, plugin: str) -> None:
    verb = operation[:-1]
    owner_command(context, f"/plugins {verb} {plugin}", "")
    context.plugin_toggles.append((context.bot, plugin, "disable" if verb == "enable" else "enable"))


def plugin_status(context: Context) -> Dict[str, tuple]:
    reply = owner_command(context, "/plugins status", "Ld/En/Name")
    status = {}
    for line in reply.splitlines()[1:]:
        flags, _, name = line.replace("️", "").partition(" ")
        status[name] = tuple(flag == "✔" for flag in flags)
    return status


@then(r'the plugin status lists "(?P<plugin>[^"]*)" as (?P<state>loaded and enabled|loaded but disabled|not loaded)')
def step_plugin_status(context: Context, plugin: str, state: str) -> None:
    actual = plugin_status(context).get(plugin)
    assert actual == STATUS[state], f"{plugin} status is {actual!r}, expected {state}"
