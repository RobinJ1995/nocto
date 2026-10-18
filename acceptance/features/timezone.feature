Feature: timezone plugin
  /tz, /time and /timezone tell the current time in a timezone, looked up by IANA name or city.

  Background:
    Given a group chat with id -1300
    And a user with id 1300 and first name "Tester"

  Scenario: no timezone given
    When the user sends "/tz"
    Then the bot replies "No timezone specified"

  Scenario Outline: every alias works (<command>)
    When the user sends "<command> utc"
    Then the bot reply matches "UTC: \d{1,2}:\d{1,2}(am|pm)"

    Examples:
      | command   |
      | /tz       |
      | /time     |
      | /timezone |

  Scenario Outline: looking up "<input>"
    When the user sends "/tz <input>"
    Then the bot reply matches "<zone>: \d{1,2}:\d{1,2}(am|pm)"

    Examples:
      | input               | zone                |
      | europe/amsterdam    | Europe/Amsterdam    |
      | amsterdam           | Europe/Amsterdam    |
      | new_york            | America/New_York    |
      | america/los_angeles | America/Los_Angeles |
      | tokyo               | Asia/Tokyo          |

  Scenario: an unknown timezone
    When the user sends "/tz atlantis"
    Then the bot replies "Unknown timezone"

  Scenario Outline: lookups ignore case (<input>)
    When the user sends "/tz <input>"
    Then the bot reply matches "<zone>: \d{1,2}:\d{1,2}(am|pm)"

    Examples:
      | input            | zone             |
      | Europe/Amsterdam | Europe/Amsterdam |
      | AMSTERDAM        | Europe/Amsterdam |
      | Amsterdam        | Europe/Amsterdam |
      | New_York         | America/New_York |
      | UTC              | UTC              |

  Scenario Outline: object properties are not timezones (<input>)
    When the user sends "/tz <input>"
    Then the bot replies "Unknown timezone"

    Examples:
      | input          |
      | constructor    |
      | __proto__      |
      | hasOwnProperty |

  # Half-hour and three-quarter offsets put single-digit minutes somewhere for half of every hour.
  Scenario Outline: the time is shown with zero-padded minutes (<zone>)
    When the user sends "/tz <zone>"
    Then the bot replies with the current time in <zone>

    Examples:
      | zone           |
      | UTC            |
      | Asia/Kolkata   |
      | Asia/Kathmandu |
