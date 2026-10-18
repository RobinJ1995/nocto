Feature: feed announcements
    Subscribed chats are told about entries published after they subscribed. The first check of a
    feed only records what's already there.

    Background:
        Given a group chat with id -2700
        And a user with id 2700 and first name "Tester"

    Scenario: a new entry is announced
        Given a feed "fa-news" titled "Acme News" with an entry "Old news"
        And the owner has registered the feed "fa-news"
        When the user sends "/sub fa-news"
        Then the bot replies "Subscribed to feed "fa-news"."
        When the feed "fa-news" has been checked
        And the feed "fa-news" publishes the entry "Big news" linking to "https://example.com/big" by "Jane Doe"
        Then the chat receives the announcement
            """
            » Jane Doe published on channel “Acme News”:
            Big news — https://example.com/big
            """

    Scenario: entries that were already there are not announced
        Given a feed "fa-quiet" titled "Quiet" with an entry "Already there"
        And the owner has registered the feed "fa-quiet"
        When the user sends "/sub fa-quiet"
        Then the bot replies "Subscribed to feed "fa-quiet"."
        And the chat receives no announcement after 3 more checks of "fa-quiet"

    Scenario: entries without an author
        Given a feed "fa-anon" titled "Anonymous" with an entry "Old"
        And the owner has registered the feed "fa-anon"
        When the user sends "/sub fa-anon"
        Then the bot replies "Subscribed to feed "fa-anon"."
        When the feed "fa-anon" has been checked
        And the feed "fa-anon" publishes the entry "Who wrote this?" linking to "https://example.com/anon"
        Then the chat receives the announcement
            """
            » New entry published on channel “Anonymous”:
            Who wrote this? — https://example.com/anon
            """

    Scenario: several new entries arrive in one message, oldest first
        Given a feed "fa-batch" titled "Batch" with an entry "Old"
        And the owner has registered the feed "fa-batch"
        When the user sends "/sub fa-batch"
        Then the bot replies "Subscribed to feed "fa-batch"."
        When the feed "fa-batch" has been checked
        And the feed "fa-batch" publishes these entries
            | title  | link                     |
            | First  | https://example.com/1    |
            | Second | https://example.com/2    |
        Then the chat receives the announcement
            """
            » New entry published on channel “Batch”:
            First — https://example.com/1

            » New entry published on channel “Batch”:
            Second — https://example.com/2
            """

    Scenario: a flood of entries is capped
        Given a feed "fa-flood" titled "Flood" with an entry "Old"
        And the owner has registered the feed "fa-flood"
        When the user sends "/sub fa-flood"
        Then the bot replies "Subscribed to feed "fa-flood"."
        When the feed "fa-flood" has been checked
        And the feed "fa-flood" publishes these entries
            | title | link                  |
            | 1     | https://example.com/1 |
            | 2     | https://example.com/2 |
            | 3     | https://example.com/3 |
            | 4     | https://example.com/4 |
            | 5     | https://example.com/5 |
            | 6     | https://example.com/6 |
            | 7     | https://example.com/7 |
        Then the chat receives the announcement
            """
            » New entry published on channel “Flood”:
            3 — https://example.com/3

            » New entry published on channel “Flood”:
            4 — https://example.com/4

            » New entry published on channel “Flood”:
            5 — https://example.com/5

            » New entry published on channel “Flood”:
            6 — https://example.com/6

            » New entry published on channel “Flood”:
            7 — https://example.com/7

            (2 older update(s) skipped)
            """

    Scenario: every subscribed chat is told
        Given a feed "fa-shared" titled "Shared" with an entry "Old"
        And the owner has registered the feed "fa-shared"
        When user 2701 sends "/sub fa-shared" in chat -2701
        Then the bot replies "Subscribed to feed "fa-shared"."
        When user 2702 sends "/sub fa-shared" in chat -2702
        Then the bot replies "Subscribed to feed "fa-shared"."
        When the feed "fa-shared" has been checked
        And the feed "fa-shared" publishes the entry "For everyone" linking to "https://example.com/all"
        Then chat -2701 receives an announcement containing "For everyone"
        And chat -2702 receives an announcement containing "For everyone"

    Scenario: unsubscribed chats are not told
        Given a feed "fa-gone" titled "Gone" with an entry "Old"
        And the owner has registered the feed "fa-gone"
        When the user sends "/sub fa-gone"
        Then the bot replies "Subscribed to feed "fa-gone"."
        When the feed "fa-gone" has been checked
        And the user sends "/unsub fa-gone"
        Then the bot replies "Unsubscribed from feed "fa-gone"."
        When the feed "fa-gone" publishes the entry "Missed it" linking to "https://example.com/missed"
        Then the chat receives no announcement within 3 seconds

    Scenario: removed feeds go quiet
        Given a feed "fa-removed" titled "Removed" with an entry "Old"
        And the owner has registered the feed "fa-removed"
        When the user sends "/sub fa-removed"
        Then the bot replies "Subscribed to feed "fa-removed"."
        When the feed "fa-removed" has been checked
        And the owner removes the feed "fa-removed"
        And the feed "fa-removed" publishes the entry "Nobody hears this" linking to "https://example.com/void"
        Then the chat receives no announcement within 3 seconds

    Scenario: entries published while a feed was failing are announced once it recovers
        Given a feed "fa-flaky" titled "Flaky" with an entry "Old"
        And the owner has registered the feed "fa-flaky"
        When the user sends "/sub fa-flaky"
        Then the bot replies "Subscribed to feed "fa-flaky"."
        When the feed "fa-flaky" has been checked
        And the feed "fa-flaky" starts failing with status 500
        And the feed "fa-flaky" publishes the entry "Back online" linking to "https://example.com/back"
        And the feed "fa-flaky" has been checked 2 more times
        And the feed "fa-flaky" recovers
        Then chat -2700 receives an announcement containing "Back online"

    Scenario: feeds with an ETag are fetched conditionally
        Given a feed "fa-etag" titled "Tagged" with an entry "Old"
        And the feed "fa-etag" uses ETags
        And the owner has registered the feed "fa-etag"
        When the user sends "/sub fa-etag"
        Then the bot replies "Subscribed to feed "fa-etag"."
        When the feed "fa-etag" has been checked 2 more times
        Then the latest request for "fa-etag" carried the header "If-None-Match"
        When the feed "fa-etag" publishes the entry "Changed" linking to "https://example.com/changed"
        Then chat -2700 receives an announcement containing "Changed"
