# Acceptance tests

Black-box tests written with [behave](https://behave.readthedocs.io/) and run with docker compose.
They drive the real bot image through Telegram updates and assert on the API calls it makes.
Every external service is faked.

## Running

```bash
cd acceptance
docker compose up --build --abort-on-container-exit --exit-code-from behave
docker compose down -v
```

The exit code is behave's. To run a single feature against an already running stack:

```bash
docker compose up -d --build telegram-mock http-mock ircd nocto nocto-strict nocto-pristine
docker compose run --rm --build behave behave features/echo.feature
```

Bots keep their state (owner, authorities, plugin state, throttling) until they're restarted, so
rerunning against the same stack can fail where a fresh run passes.

## Services

| Service          | Role |
|------------------|------|
| `telegram-mock`  | Fake Bot API. Serves the bots over HTTPS on 8443 with a certificate from a CA it writes to the `certs` volume; behave uses plain HTTP on 8081 to inject updates and read recorded calls. |
| `http-mock`      | Fake third-party HTTP services (Google suggestions), reachable as `suggest.nocto.test`. |
| `ircd`           | [Ergo](https://ergo.chat) IRC server for the ircbridge plugin. behave connects as plain IRC clients and becomes an operator for kicks, topics and modes. Features tagged `@irc` use it. |
| `nocto`          | Main bot: plugins enabled, web server and media permalinks on, `/` and `!` prefixes, bridged to `ircd`. |
| `nocto-strict`   | Strict firewall, throttling, encrypted permalinks. Features tagged `@strict` run against it. |
| `nocto-pristine` | Never claimed until `ownership.feature` does it. Features tagged `@pristine` run against it. |
| `behave`         | The test runner. |

All bots run the image built from the repository's `Dockerfile`, each with its own
`config/<name>.json` mounted as `config/local.json`. Their `persist/` is a tmpfs, so every run
starts clean.

## Conventions

- User 1 is the owner of `nocto` and `nocto-strict`; it's claimed in `before_all`.
- Group chats have negative ids; a private chat's id is the user's id.
- Each feature uses its own block of chat and user ids, since bot state carries over between
  scenarios.
- Scenarios that toggle plugins through `the owner has enabled/disabled …` are restored afterwards.
