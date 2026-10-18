Feature: command handling
    Messages starting with a configured prefix are commands. Commands sent before the bot started
    polling are backlog and get ignored.

    Background:
        Given a group chat with id -1100
        And a user with id 1100 and first name "Tester"

    Scenario Outline: commands work with every configured prefix (<prefix>)
        When the user sends "<prefix>echo prefixed"
        Then the bot replies "prefixed"

        Examples:
            | prefix |
            | /      |
            | !      |

    Scenario: text without a prefix is not a command
        When the user sends "echo not a command"
        Then the bot sends no reply

    Scenario: a command addressed to this bot is handled
        When the user sends "/echo@nocto_main_bot addressed"
        Then the bot replies "addressed"

    Scenario: a command addressed to another bot is ignored
        When the user sends "/echo@some_other_bot not for you"
        Then the bot sends no reply

    Scenario: the bot's username is matched case-insensitively
        When the user sends "/echo@Nocto_Main_Bot shouting"
        Then the bot replies "shouting"

    Scenario: an unknown command is ignored
        When the user sends "/frobnicate now"
        Then the bot sends no reply

    Scenario Outline: backlog commands are ignored (<command>)
        When the user sends "<command>" dated yesterday
        Then the bot sends no reply

        Examples:
            | command             |
            | /echo old news      |
            | !echo old news      |
            | /tz utc             |
            | /suggest old        |
            | /authority 1        |
            | /owner              |
            | /plugins status     |
            | /sub                |
            | /permalink          |
