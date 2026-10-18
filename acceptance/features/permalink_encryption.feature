@strict
Feature: encrypted media permalinks
  With file id encryption on, permalinks don't expose Telegram file ids. Only trusted users may
  ask for them here.

  Background:
    Given a private chat

  Scenario: untrusted users get no permalink
    Given a user with id 7301 and first name "Agent"
    And the user is known to the bot
    When the user sends a photo "EncUntrusted"
    And the user sends "/permalink"
    Then the bot sends no reply

  Scenario: the permalink hides the file id and still serves the file
    Given a user with id 7302 and first name "Agent"
    And the user is a half-operator
    And the file "EncSecretAAA" contains "classified"
    When the user sends a document "EncSecretAAA" named "secret.txt" of type "text/plain"
    And the user sends "/permalink"
    Then the permalink does not reveal "EncSecretAAA"
    When the permalink is downloaded
    Then the download contains the file "EncSecretAAA"

  Scenario: every share gets its own link to the same file
    Given a user with id 7303 and first name "Agent"
    And the user is a half-operator
    And the file "EncTwiceAAAA" contains "same bytes"
    When the user sends a photo "EncTwiceAAAA"
    And the user sends "/permalink"
    And the permalink is remembered as "first"
    And the user sends a photo "EncTwiceAAAA"
    And the user sends "/permalink"
    And the permalink is remembered as "second"
    Then the permalinks "first" and "second" differ
    When the permalink "first" is downloaded
    Then the download contains the file "EncTwiceAAAA"
    When the permalink "second" is downloaded
    Then the download contains the file "EncTwiceAAAA"

  Scenario: a tampered link doesn't resolve
    When "/media/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.jpg" is downloaded from the bot
    Then the download fails
