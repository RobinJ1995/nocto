@irc
Feature: copying between IRC channels
    A channel can be copied to a channel on another IRC server, next to being relayed to Telegram.

    Scenario: messages are copied
        Given "erin1" is in the IRC channel "#copy-dst"
        When "frank1" says "copy that" in "#copy-src"
        Then "erin1" sees "noctob" say "<frank1@#copy-src> copy that" in "#copy-dst"
        And group -4107 receives "<frank1@#copy-src> copy that"

    Scenario: events are copied
        Given "erin2" is in the IRC channel "#copy-dst"
        When "frank2" joins "#copy-src"
        Then "erin2" sees "noctob" say "User frank2 joined channel #copy-src" in "#copy-dst"
