"""Talking to the bridge from the IRC side, and watching what it relays."""
import re
import time
from typing import List

from behave import given, then, when, use_step_matcher
from behave.runner import Context

import helpers
from irc_client import IrcClient, Line, strip_formatting

use_step_matcher("parse")

BRIDGE = re.compile(r"^nocto\d*$")
# Telegram groups each bridged channel relays to, mirroring config/main.json.
RELAY_TO = {
    "#bridge-one": [-4101], "#bridge-two": [-4102], "#bridge-shared": [-4103, -4104],
    "#multi-a": [-4105], "#multi-b": [-4105], "#readonly": [-4106], "#copy-src": [-4107],
    "#renames": [-4108],
}


def client(context: Context, nick: str) -> IrcClient:
    if nick not in context.irc:
        context.irc[nick] = IrcClient(nick, f"{nick.capitalize()} Realname")
    return context.irc[nick]


def member(context: Context, nick: str, chan: str) -> IrcClient:
    irc = client(context, nick)
    if chan.lower() not in irc.channels:
        irc.join(chan)
        wait_for_relay(context, chan, f"User {nick} joined channel {chan}")
    return irc


def wait_for_relay(context: Context, chan: str, text: str) -> None:
    for group in RELAY_TO.get(chan.lower(), []):
        assert helpers.wait_until(lambda: text in group_texts(context, group, 0)), \
            f"Group {group} was never told {text!r}"


def group_texts(context: Context, group: int, seq: int) -> List[str]:
    return [c["params"].get("text", "") for c in helpers.replies_since(context.bot, group, seq, ("sendMessage",))]


def from_bridge(line: Line, chan: str, bridge: re.Pattern = BRIDGE) -> bool:
    return line.command == "PRIVMSG" and bool(bridge.match(line.nick)) and line.params[0].lower() == chan.lower()


def bridge_lines(watcher: IrcClient, chan: str, bridge: re.Pattern = BRIDGE) -> List[Line]:
    return watcher.find(lambda l: from_bridge(l, chan, bridge))


def irc_event(context: Context) -> None:
    context.cursor = helpers.last_seq(context.bot)


# ---------------------------------------------------------------------------
# Given / When: IRC users doing things
# ---------------------------------------------------------------------------

@given('"{nick}" is in the IRC channel "{chan}"')
def step_in_channel(context: Context, nick: str, chan: str) -> None:
    member(context, nick, chan)


@when('"{nick}" joins "{chan}"')
def step_joins(context: Context, nick: str, chan: str) -> None:
    irc_event(context)
    client(context, nick).join(chan)


@when('"{nick}" says "{text}" in "{chan}"')
def step_says(context: Context, nick: str, text: str, chan: str) -> None:
    irc = member(context, nick, chan)
    irc_event(context)
    irc.say(chan, text)


@when('"{nick}" performs the action "{text}" in "{chan}"')
def step_action(context: Context, nick: str, text: str, chan: str) -> None:
    irc = member(context, nick, chan)
    irc_event(context)
    irc.say(chan, f"\x01ACTION {text}\x01")


@when('"{nick}" sends the notice "{text}" to "{chan}"')
def step_notice(context: Context, nick: str, text: str, chan: str) -> None:
    irc = member(context, nick, chan)
    irc_event(context)
    irc.send(f"NOTICE {chan} :{text}")


@when('"{nick}" leaves "{chan}" saying "{reason}"')
def step_part(context: Context, nick: str, chan: str, reason: str) -> None:
    irc_event(context)
    client(context, nick).send(f"PART {chan} :{reason}")


@when('"{nick}" quits IRC saying "{reason}"')
def step_quit(context: Context, nick: str, reason: str) -> None:
    irc_event(context)
    context.irc.pop(nick).quit(reason)


@when('"{nick}" changes nick to "{new_nick}"')
def step_nick(context: Context, nick: str, new_nick: str) -> None:
    irc_event(context)
    irc = context.irc.pop(nick)
    irc.send(f"NICK {new_nick}")
    irc.nick = new_nick
    context.irc[new_nick] = irc


@when('the channel operator sets the topic of "{chan}" to "{topic}"')
def step_topic(context: Context, chan: str, topic: str) -> None:
    irc_event(context)
    context.chanop.send(f"TOPIC {chan} :{topic}")


@when('the channel operator kicks "{nick}" from "{chan}" because "{reason}"')
def step_kick(context: Context, nick: str, chan: str, reason: str) -> None:
    irc_event(context)
    context.chanop.send(f"KICK {chan} {nick} :{reason}")


@when('the channel operator sets mode "{mode}" on "{chan}"')
def step_mode(context: Context, mode: str, chan: str) -> None:
    irc_event(context)
    context.chanop.send(f"MODE {chan} {mode}")


@when('an IRC operator renames "{nick}" to "{new_nick}"')
def step_sanick(context: Context, nick: str, new_nick: str) -> None:
    irc_event(context)
    since = context.chanop.mark()
    context.chanop.send(f"SANICK {nick} {new_nick}")
    context.chanop.wait_for(lambda l: l.command == "NICK" and l.nick == nick and l.text == new_nick,
                            f"{nick} become {new_nick}", since)


# ---------------------------------------------------------------------------
# Then: what reached Telegram
# ---------------------------------------------------------------------------

@then('group {group:d} receives "{text}"')
def step_group_receives(context: Context, group: int, text: str) -> None:
    found = helpers.wait_until(lambda: text in group_texts(context, group, context.cursor))
    assert found, f"Group {group} never got {text!r}: {group_texts(context, group, context.cursor)!r}"


@then('group {group:d} receives a message containing "{text}"')
def step_group_receives_containing(context: Context, group: int, text: str) -> None:
    found = helpers.wait_until(lambda: any(text in t for t in group_texts(context, group, context.cursor)))
    assert found, f"Group {group} got nothing containing {text!r}: {group_texts(context, group, context.cursor)!r}"


@then('group {group:d} receives nothing containing "{text}"')
def step_group_receives_nothing(context: Context, group: int, text: str) -> None:
    time.sleep(helpers.NEGATIVE_GRACE)
    texts = group_texts(context, group, context.cursor)
    assert not any(text in t for t in texts), f"Group {group} unexpectedly got {texts!r}"


# ---------------------------------------------------------------------------
# Then: what reached IRC
# ---------------------------------------------------------------------------

@then('"{nick}" sees the bridge say "{text}" in "{chan}"')
def step_sees_bridge_say(context: Context, nick: str, text: str, chan: str) -> None:
    watcher = client(context, nick)
    watcher.wait_for(
        lambda l: from_bridge(l, chan) and strip_formatting(l.text) == text,
        f"the bridge say {text!r} in {chan}",
    )


@then('"{nick}" sees "{bridge}" say "{text}" in "{chan}"')
def step_sees_other_bridge_say(context: Context, nick: str, bridge: str, text: str, chan: str) -> None:
    watcher = client(context, nick)
    pattern = re.compile(rf"^{re.escape(bridge)}\d*$")
    watcher.wait_for(
        lambda l: from_bridge(l, chan, pattern) and strip_formatting(l.text) == text,
        f"{bridge} say {text!r} in {chan}",
    )


@then('"{nick}" sees the bridge say these lines in "{chan}"')
def step_sees_bridge_lines(context: Context, nick: str, chan: str) -> None:
    watcher = client(context, nick)
    expected = context.text.splitlines()
    def matches() -> bool:
        said = [strip_formatting(l.text) for l in bridge_lines(watcher, chan)]
        return any(said[i:i + len(expected)] == expected for i in range(len(said)))
    assert helpers.wait_until(matches), \
        f"Expected {expected!r}, got {[strip_formatting(l.text) for l in bridge_lines(watcher, chan)]!r}"


@then('"{nick}" does not see the bridge say anything containing "{text}" in "{chan}"')
def step_does_not_see(context: Context, nick: str, text: str, chan: str) -> None:
    watcher = client(context, nick)
    time.sleep(helpers.NEGATIVE_GRACE)
    said = [strip_formatting(l.text) for l in bridge_lines(watcher, chan)]
    assert not any(text in s for s in said), f"Did not expect {text!r} in {said!r}"


@then('"{nick}" sees the bridge write "{name}" in bold in "{chan}"')
def step_sees_bold(context: Context, nick: str, name: str, chan: str) -> None:
    watcher = client(context, nick)
    watcher.wait_for(
        lambda l: from_bridge(l, chan) and l.text.startswith(f"<\x02{name}\x0f>"),
        f"{name} in bold in {chan}",
    )


@then('"{nick}" sees the bridge write "{name}" in bold on all {count:d} lines in "{chan}"')
def step_sees_bold_everywhere(context: Context, nick: str, name: str, count: int, chan: str) -> None:
    watcher = client(context, nick)
    assert helpers.wait_until(lambda: len(bridge_lines(watcher, chan)) >= count), \
        f"{nick} saw fewer than {count} lines from the bridge"
    prefixes = [line.text.partition(">")[0] + ">" for line in bridge_lines(watcher, chan)]
    assert all(p == f"<\x02{name}\x0f>" for p in prefixes), f"Inconsistent name formatting: {prefixes!r}"


@then('"{nick}" sees the bridge write "{name}" in colour {code:d} in "{chan}"')
def step_sees_colour(context: Context, nick: str, name: str, code: int, chan: str) -> None:
    watcher = client(context, nick)
    watcher.wait_for(
        lambda l: from_bridge(l, chan) and l.text.startswith(f"<\x03{code:02d}\x02{name}\x0f\x0f>"),
        f"{name} in colour {code} in {chan}",
    )
