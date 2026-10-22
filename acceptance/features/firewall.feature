@strict
Feature: firewall
    Once the bot has an owner, the firewall drops messages from users below the authority configured
    for that kind of message. Here: group commands need "trusted", private commands need a "known"
    user, meaning one who shares a group with the bot or is trusted.

    Scenario: an untrusted user's group command is dropped
        Given a group chat with id -7100
        When user 7101 sends "/echo hello"
        Then the bot sends no reply

    Scenario: a trusted user's group command is answered
        Given a group chat with id -7100
        And user 7102 is a trusted user
        When user 7102 sends "/echo hello"
        Then the bot replies "hello"

    Scenario: a stranger's private command is dropped
        Given a private chat
        When user 7103 sends "/echo hello"
        Then the bot sends no reply

    Scenario: a user who shares a group with the bot may use private commands
        Given a private chat
        And user 7104 is known to the bot
        When user 7104 sends "/echo hello"
        Then the bot replies "hello"

    Scenario: leaving the group makes a user a stranger again
        Given a private chat
        And user 7105 is known to the bot
        And user 7105 has left the group
        When user 7105 sends "/echo hello"
        Then the bot sends no reply

    Scenario: trusted users may use private commands without sharing a group
        Given a private chat
        And user 7106 is a trusted user
        And user 7106 has left the group
        When user 7106 sends "/echo hello"
        Then the bot replies "hello"
