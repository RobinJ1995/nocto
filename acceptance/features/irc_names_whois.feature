@irc
Feature: looking at IRC from Telegram
  /names lists who is in a bridged channel, /whois shows what the IRC server knows about a user.

  Background:
    Given a group chat with id -4101
    And a user with id 4400 and first name "Tester"

  Scenario: listing a channel's users
    Given "carol1" is in the IRC channel "#bridge-one"
    When the user sends "/names #bridge-one"
    Then the bot reply contains "Other users in channel #bridge-one: "
    And the bot's last reply lists "carol1" and "chanop" but not "nocto"

  Scenario: only channels bridged to this group
    When the user sends "/names #bridge-two"
    Then the bot replies "Channel #bridge-two is not associated with this group."

  Scenario: a group with several channels has to pick one
    Given a group chat with id -4105
    When the user sends "/names"
    Then the bot replies "Wrong number of arguments."

  Scenario: too many arguments
    When the user sends "/names #bridge-one #bridge-two"
    Then the bot replies "Wrong number of arguments."

  Scenario: looking up a user
    Given "carol2" is in the IRC channel "#bridge-one"
    When the user sends "/whois #bridge-one carol2"
    Then the bot reply contains ""realname": "Carol2 Realname""
    And the bot replies in Markdown

  Scenario: looking up someone who isn't there
    When the user sends "/whois #bridge-one ghost"
    Then the bot reply contains ""nick": "ghost""

  Scenario: whois takes a channel and a nick at most
    When the user sends "/whois #bridge-one carol2 extra"
    Then the bot replies "Wrong number of arguments."
