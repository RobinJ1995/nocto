@irc
Feature: IRC preferences
    Telegram users choose the alias and colour they appear with on IRC, and whether they're relayed
    at all.

    Background:
        Given a group chat with id -4101

    Scenario: setting an alias
        Given "dave1" is in the IRC channel "#bridge-one"
        And a user with id 4501 and first name "Robin"
        When the user sends "/setalias RobinJ"
        Then the bot replies "Alias set to "RobinJ"."
        When the user sends "who am I"
        Then "dave1" sees the bridge say "<RobinJ> who am I" in "#bridge-one"

    Scenario Outline: invalid aliases (<alias>)
        Given a user with id 4502 and first name "Tester"
        When the user sends "/setalias <alias>"
        Then the bot replies "Not a valid IRC nickname."

        Examples:
            | alias                           |
            | 9lives                          |
            | way_too_long_for_an_irc_nick_ok |
            | héhé                            |

    Scenario: listing the available colours
        Given a user with id 4503 and first name "Tester"
        When the user sends "/setcolor"
        Then the bot reply contains "Available colors: "
        And the reply also contains "light_red"

    Scenario: an unknown colour lists the available ones
        Given a user with id 4504 and first name "Tester"
        When the user sends "/setcolor chartreuse"
        Then the bot reply contains "Available colors: "

    Scenario: picking a colour
        Given "dave2" is in the IRC channel "#bridge-one"
        And a user with id 4505 and first name "Tester" and username "painter"
        When the user sends "/setcolor LIGHT_RED"
        Then the bot replies "Nickname color set to "light_red"."
        When the user sends "in colour"
        Then "dave2" sees the bridge write "painter" in colour 4 in "#bridge-one"

    Scenario Outline: opting out of relaying (<value>)
        Given "dave3" is in the IRC channel "#bridge-one"
        And a user with id <user> and first name "Shy"
        When the user sends "/setrelay <value>"
        Then the bot replies "Your messages will NOT be relayed."
        When the user sends "keep this to Telegram <user>"
        Then "dave3" does not see the bridge say anything containing "keep this to Telegram <user>" in "#bridge-one"

        Examples:
            | value | user |
            | off   | 4506 |
            | 0     | 4507 |
            | false | 4508 |

    Scenario: checking whether you're relayed after opting out
        Given a user with id 4509 and first name "Shy"
        When the user sends "/setrelay off"
        Then the bot replies "Your messages will NOT be relayed."
        When the user sends "/setrelay"
        Then the bot replies "Your messages are currently NOT being relayed."

    Scenario: opting back in
        Given "dave4" is in the IRC channel "#bridge-one"
        And a user with id 4510 and first name "Fickle" and username "fickle"
        When the user sends "/setrelay off"
        Then the bot replies "Your messages will NOT be relayed."
        When the user sends "/setrelay on"
        Then the bot replies "Your messages will be relayed to #bridge-one."
        When the user sends "I'm back"
        Then "dave4" sees the bridge say "<fickle> I'm back" in "#bridge-one"

    Scenario: checking whether you're relayed
        Given a user with id 4512 and first name "Tester"
        When the user sends "/setrelay"
        Then the bot replies "Your messages are currently being relayed to #bridge-one."

    Scenario: a group bridged to two channels is relayed to both
        Given a group chat with id -4105
        And a user with id 4513 and first name "Tester"
        When the user sends "/setrelay"
        Then the bot replies "Your messages are currently being relayed to #multi-a, #multi-b."

    Scenario: an answer that is neither yes nor no
        Given a user with id 4511 and first name "Tester"
        When the user sends "/setrelay maybe"
        Then the bot replies "Invalid value. Yes or no?"
