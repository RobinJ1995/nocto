"""A minimal IRC client for watching and talking to the bridge."""
import os
import re
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

IRC_HOST = os.environ.get("IRC_HOST", "ircd")
IRC_PORT = int(os.environ.get("IRC_PORT", "6667"))
IRC_OPER_PASSWORD = os.environ.get("IRC_OPER_PASSWORD", "acceptance")
TIMEOUT = 15.0
FORMATTING = re.compile(r"\x03(\d{1,2}(,\d{1,2})?)?|[\x02\x0f\x16\x1d\x1e\x1f\x11]")


def strip_formatting(text: str) -> str:
    return FORMATTING.sub("", text)


@dataclass
class Line:
    raw: str
    nick: str
    command: str
    params: List[str]

    @property
    def text(self) -> str:
        return self.params[-1] if self.params else ""


def parse(raw: str) -> Line:
    prefix, rest = "", raw
    if rest.startswith(":"):
        prefix, _, rest = rest[1:].partition(" ")
    rest, separator, trailing = rest.partition(" :")
    params = rest.split()
    command = params.pop(0) if params else ""
    if separator:
        params.append(trailing)
    return Line(raw, prefix.split("!")[0], command.upper(), params)


class IrcClient:
    def __init__(self, nick: str, realname: Optional[str] = None) -> None:
        self.nick = nick
        self.channels = set()
        self.lines: List[Line] = []
        self._cond = threading.Condition()
        self._sock = socket.create_connection((IRC_HOST, IRC_PORT), timeout=TIMEOUT)
        self._sock.settimeout(None)
        self._file = self._sock.makefile("rb")
        threading.Thread(target=self._read, daemon=True).start()
        self.send(f"NICK {nick}")
        self.send(f"USER {nick} 0 * :{realname or nick}")
        self.wait_for(lambda l: l.command == "001", "registration")

    def _read(self) -> None:
        for raw in self._file:
            line = parse(raw.decode("utf-8", "replace").rstrip("\r\n"))
            if line.command == "PING":
                self.send("PONG :" + line.text)
            with self._cond:
                self.lines.append(line)
                self._cond.notify_all()

    def send(self, line: str) -> None:
        self._sock.sendall((line + "\r\n").encode())

    def mark(self) -> int:
        with self._cond:
            return len(self.lines)

    def find(self, predicate: Callable[[Line], bool], since: int = 0) -> List[Line]:
        with self._cond:
            return [line for line in self.lines[since:] if predicate(line)]

    def wait_for(self, predicate: Callable[[Line], bool], what: str,
                 since: int = 0, timeout: float = TIMEOUT) -> Line:
        deadline = time.time() + timeout
        with self._cond:
            while True:
                found = [line for line in self.lines[since:] if predicate(line)]
                if found:
                    return found[0]
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise AssertionError(f"{self.nick} never saw {what}")
                self._cond.wait(remaining)

    def join(self, channel: str) -> None:
        since = self.mark()
        self.send(f"JOIN {channel}")
        self.wait_for(lambda l: l.command == "366" and l.params[1].lower() == channel.lower(),
                      f"the end of the names list for {channel}", since)
        self.channels.add(channel.lower())

    def say(self, channel: str, text: str) -> None:
        self.send(f"PRIVMSG {channel} :{text}")

    def oper(self) -> None:
        since = self.mark()
        self.send(f"OPER admin {IRC_OPER_PASSWORD}")
        self.wait_for(lambda l: l.command == "381", "the oper confirmation", since)

    def quit(self, reason: str = "") -> None:
        try:
            self.send(f"QUIT :{reason}")
            self._sock.close()
        except OSError:
            pass
