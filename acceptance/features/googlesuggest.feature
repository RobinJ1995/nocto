Feature: googlesuggest plugin
  /suggest lists Google search suggestions for a partial query.

  Background:
    Given a group chat with id -1600
    And a user with id 1600 and first name "Tester"

  Scenario: suggestions are listed one per line
    Given the suggestion service suggests for "nocto"
      | suggestion     |
      | nocto bot      |
      | nocto telegram |
    When the user sends "/suggest nocto"
    Then the bot replies
      """
      nocto bot
      nocto telegram
      """

  Scenario Outline: every alias works (<command>)
    Given the suggestion service suggests for "alias"
      | suggestion  |
      | alias works |
    When the user sends "<command> alias"
    Then the bot replies "alias works"

    Examples:
      | command        |
      | /suggest       |
      | /gsuggest      |
      | /googlesuggest |

  Scenario Outline: the language comes from the command suffix (<command>)
    When the user sends "<command> <query>"
    Then the suggestion service was asked for "<query>" in language "<language>"

    Examples:
      | command     | query | language |
      | /suggest    | bike  | en       |
      | /suggest_nl | fiets | nl       |
      | /suggestde  | auto  | de       |
      | /gsuggestfr | velo  | fr       |

  Scenario: the query itself is not suggested back
    Given the suggestion service suggests for "Echo"
      | suggestion  |
      | echo        |
      | echo chamber |
    When the user sends "/suggest Echo"
    Then the bot replies "echo chamber"

  Scenario: nothing to suggest
    When the user sends "/suggest qwxzv"
    Then the bot replies "No suggestions"

  Scenario: only the query itself comes back
    Given the suggestion service suggests for "lonely"
      | suggestion |
      | LONELY     |
    When the user sends "/suggest lonely"
    Then the bot replies "No suggestions"

  Scenario: no query given
    When the user sends "/suggest"
    Then the bot sends no reply

  Scenario: the bot shows it is working on it
    When the user sends "/suggest typing"
    Then the bot shows that it is typing

  Scenario: the service fails
    Given the suggestion service fails with status 503 for "broken"
    When the user sends "/suggest broken"
    Then the bot replies "Failed to fetch suggestions"

  Scenario: the service answers garbage
    Given the suggestion service answers "this is not xml" for "garbage"
    When the user sends "/suggest garbage"
    Then the bot replies "Failed to fetch suggestions"

  Scenario: the service can't be reached
    Given the suggestion service is unreachable for "offline"
    When the user sends "/suggest offline"
    Then the bot replies "Failed to fetch suggestions"
    When the user sends "/echo still alive"
    Then the bot replies "still alive"

  Scenario: the bot identifies itself
    When the user sends "/suggest whoami"
    Then the suggestion service was asked for "whoami" by a client identifying as "nocto/"
