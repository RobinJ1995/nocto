Feature: user authority
    Users have an authority level, from blacklisted up to owner. /authority shows or changes it.

    Background:
        Given a group chat with id -2100

    Scenario: the bot already has an owner
        When user 2100 sends "/owner"
        Then the bot replies "I already have an owner."

    Scenario Outline: looking up an unknown user (<command>)
        When the owner sends "<command>"
        Then the bot replies "I do not know of this user. Make sure it is a valid numerical ID or @username."

        Examples:
            | command             |
            | /authority          |
            | /authority 999999   |
            | /authority @nobody  |

    Scenario: looking up a user by id
        Given user 2101 is known to the bot
        When user 2190 sends "/authority 2101"
        Then the bot replies "That user's authority is "user" (level 1, symbol '-')."

    Scenario: looking up a user by username
        Given user 2102 is known to the bot
        When user 2190 sends "/authority @user2102"
        Then the bot replies "That user's authority is "user" (level 1, symbol '-')."

    Scenario: looking up the owner
        When user 2190 sends "/authority 1"
        Then the bot replies "That user's authority is "owner" (level 6, symbol '~')."

    Scenario: an invalid level
        Given user 2103 is known to the bot
        When the owner sends "/authority 2103 wizard"
        Then the bot replies "Invalid authority specification. Try one of: blacklisted user trusted half-operator operator administrator owner"

    Scenario: regular users cannot change levels
        Given user 2104 is known to the bot
        When user 2105 sends "/authority 2104 trusted"
        Then the bot replies "You must be half-operator or higher to set authority levels."

    Scenario Outline: the owner sets a level by <kind>
        Given user <user> is known to the bot
        When the owner sends "/authority <user> <level>"
        Then the bot replies "Authority level set to "<name>"."
        When the owner sends "/authority <user>"
        Then the bot replies "That user's authority is "<name>" (level <number>, symbol '<symbol>')."

        Examples:
            | kind       | user | level         | name          | number | symbol |
            | name       | 2110 | trusted       | trusted       | 2      | +      |
            | symbol     | 2111 | @             | operator      | 4      | @      |
            | number     | 2112 | 3             | half-operator | 3      | %      |
            | upper case | 2113 | ADMINISTRATOR | administrator | 5      | &      |

    Scenario: a half-operator cannot appoint another half-operator
        Given user 2120 is a half-operator
        And user 2121 is known to the bot
        When user 2120 sends "/authority 2121 half-operator"
        Then the bot replies "Your own authority is insufficient to grant this authority."

    Scenario: a half-operator can make a user trusted
        Given user 2122 is a half-operator
        And user 2123 is known to the bot
        When user 2122 sends "/authority 2123 trusted"
        Then the bot replies "Authority level set to "trusted"."

    Scenario: an operator can appoint a half-operator
        Given user 2124 is an operator
        And user 2125 is known to the bot
        When user 2124 sends "/authority 2125 half-operator"
        Then the bot replies "Authority level set to "half-operator"."

    Scenario: an operator cannot appoint an administrator
        Given user 2126 is an operator
        And user 2127 is known to the bot
        When user 2126 sends "/authority 2127 administrator"
        Then the bot replies "Your own authority is insufficient to grant this authority."

    Scenario: a half-operator cannot change an operator
        Given user 2128 is a half-operator
        And user 2129 is an operator
        When user 2128 sends "/authority 2129 user"
        Then the bot replies "Your target must not have a higher authority than you do."

    Scenario: an administrator cannot demote the owner
        Given user 2130 is an administrator
        When user 2130 sends "/authority 1 user"
        Then the bot replies "Your target must not have a higher authority than you do."

    Scenario Outline: object properties are not users (<target>)
        When the owner sends "/authority <target>"
        Then the bot replies "I do not know of this user. Make sure it is a valid numerical ID or @username."

        Examples:
            | target      |
            | constructor |
            | __proto__   |
            | toString    |

    Scenario Outline: object properties are not levels (<level>)
        Given user 2140 is known to the bot
        When the owner sends "/authority 2140 <level>"
        Then the bot replies "Invalid authority specification. Try one of: blacklisted user trusted half-operator operator administrator owner"

        Examples:
            | level       |
            | length      |
            | constructor |
            | __proto__   |
            | 7           |
