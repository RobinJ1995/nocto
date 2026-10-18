Feature: echo plugin
    /echo repeats its argument, applying skin tone suffixes to emoji that support them.

    Background:
        Given a group chat with id -1200
        And a user with id 1200 and first name "Tester"

    Scenario: echoing text
        When the user sends "/echo Hello, world!"
        Then the bot replies "Hello, world!"

    Scenario: echoing in a private chat
        Given a private chat
        When the user sends "/echo just between us"
        Then the bot replies "just between us"

    Scenario: nothing to echo
        When the user sends "/echo"
        Then the bot sends no reply

    Scenario: the command name is case-insensitive
        When the user sends "/ECHO loud"
        Then the bot replies "loud"

    Scenario Outline: skin tone suffix <input>
        When the user sends "/echo <input>"
        Then the bot replies "<output>"

        Examples:
            | input       | output    |
            | 👍#1        | 👍🏻      |
            | 👍#3        | 👍🏼      |
            | 👋#6        | 👋🏿      |
            | hi 👍#3👋#5 | hi 👍🏼👋🏾 |

    Scenario Outline: suffixes that are left alone: <input>
        When the user sends "/echo <input>"
        Then the bot replies "<input>"

        Examples:
            | input  |
            | 🍕#3   |
            | a#3    |
            | 👍#7   |
            | #3     |
