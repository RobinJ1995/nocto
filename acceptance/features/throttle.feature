@strict
Feature: throttling
  Users below half-operator get a burst of 2 messages, then 1 message per 3 seconds. One message
  may wait for its turn; anything beyond that is dropped and the user is warned once, privately.

  Background:
    Given a group chat with id -7200

  Scenario: a burst beyond the limit is delayed, then dropped
    Given user 7201 is a trusted user
    When user 7201 quickly sends
      | text        |
      | /echo one   |
      | /echo two   |
      | /echo three |
      | /echo four  |
      | /echo five  |
    Then the bot replies "one" immediately
    And the bot replies "two" immediately
    And the bot eventually replies "three"
    And the bot never replies "four"
    And the bot never replies "five"
    And user 7201 is told privately "Slow down, some of your messages are being ignored." once

  Scenario: half-operators are never throttled
    Given user 7202 is a half-operator
    When user 7202 quickly sends
      | text        |
      | /echo one   |
      | /echo two   |
      | /echo three |
      | /echo four  |
    Then the bot replies "one" immediately
    And the bot replies "two" immediately
    And the bot replies "three" immediately
    And the bot replies "four" immediately

  Scenario: each user has their own allowance
    Given user 7203 is a trusted user
    And user 7204 is a trusted user
    When user 7203 quickly sends
      | text        |
      | /echo one   |
      | /echo two   |
      | /echo three |
    And user 7204 sends "/echo someone else"
    Then the bot replies "someone else" immediately
