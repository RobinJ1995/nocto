Feature: blacklisting users
    /ban and /blacklist set a user's authority to blacklisted; the firewall then drops everything
    they send.

    Background:
        Given a group chat with id -2200

    Scenario: a banned user is ignored
        Given user 2201 is known to the bot
        When the owner sends "/ban 2201"
        Then the bot replies "Authority level set to "blacklisted"."
        When user 2201 sends "/echo let me in"
        Then the bot sends no reply

    Scenario: blacklisting by username
        Given user 2202 is known to the bot
        When the owner sends "/blacklist @user2202"
        Then the bot replies "Authority level set to "blacklisted"."
        When user 2202 sends "/echo let me in"
        Then the bot sends no reply

    Scenario: lifting a ban
        Given user 2203 is known to the bot
        When the owner sends "/ban 2203"
        Then the bot replies "Authority level set to "blacklisted"."
        When the owner sends "/authority 2203 user"
        Then the bot replies "Authority level set to "user"."
        When user 2203 sends "/echo I'm back"
        Then the bot replies "I'm back"

    Scenario: regular users cannot ban
        Given user 2204 is known to the bot
        When user 2205 sends "/ban 2204"
        Then the bot replies "You must be half-operator or higher to set authority levels."

    Scenario: banning nobody
        When the owner sends "/ban"
        Then the bot replies "I do not know of this user. Make sure it is a valid numerical ID or @username."

    Scenario: a half-operator cannot ban an operator
        Given user 2206 is a half-operator
        And user 2207 is an operator
        When user 2206 sends "/ban 2207"
        Then the bot replies "Your target must not have a higher authority than you do."
