@irc
Feature: relaying Telegram to IRC
  Messages in bridged Telegram groups are relayed to their IRC channels, with the sender's name in
  bold.

  Background:
    Given a group chat with id -4101
    And a user with id 4300 and first name "Tester" and username "tester"

  Scenario: messages
    Given "bob1" is in the IRC channel "#bridge-one"
    When the user sends "hello irc"
    Then "bob1" sees the bridge say "<tester> hello irc" in "#bridge-one"
    And "bob1" sees the bridge write "tester" in bold in "#bridge-one"

  Scenario: users without a username go by their first name
    Given "bob2" is in the IRC channel "#bridge-one"
    And a user with id 4301 and first name "Firstname" without a username
    When the user sends "no handle"
    Then "bob2" sees the bridge say "<Firstname> no handle" in "#bridge-one"

  Scenario: emoji are spelled out
    Given "bob3" is in the IRC channel "#bridge-one"
    When the user sends "pizza 🍕"
    Then "bob3" sees the bridge say "<tester> pizza :pizza:" in "#bridge-one"

  Scenario: /e keeps emoji as they are
    Given "bob4" is in the IRC channel "#bridge-one"
    When the user sends "/e pizza 🍕 👍#3"
    Then "bob4" sees the bridge say "<tester> pizza 🍕 👍🏼" in "#bridge-one"

  Scenario Outline: comments are not relayed (<comment>)
    Given "bob5" is in the IRC channel "#bridge-one"
    When the user sends "<comment>"
    And the user sends "after the comment"
    Then "bob5" sees the bridge say "<tester> after the comment" in "#bridge-one"
    And "bob5" does not see the bridge say anything containing "psst" in "#bridge-one"

    Examples:
      | comment  |
      | # psst   |
      | // psst  |
      | / psst   |
      | /c psst  |

  Scenario: every line of a multi-line message names the sender the same way
    Given "bob16" is in the IRC channel "#bridge-one"
    When the user sends these lines
      """
      first line
      second line
      third line
      """
    Then "bob16" sees the bridge write "tester" in bold on all 3 lines in "#bridge-one"

  Scenario: long messages are cut short
    Given "bob6" is in the IRC channel "#bridge-one"
    When the user sends these lines
      """
      one
      two
      three
      four
      five
      six
      seven
      """
    Then "bob6" sees the bridge say these lines in "#bridge-one"
      """
      <tester> one
      <tester> two
      <tester> three
      <tester> four
      <tester> five
      [2 more line(s) omitted]
      """

  Scenario: locations
    Given "bob7" is in the IRC channel "#bridge-one"
    When the user shares the location 52.37, 4.89
    Then "bob7" sees the bridge say "tester sent location: http://maps.google.com/maps?t=m&q=loc:52.37,4.89" in "#bridge-one"

  Scenario: contacts
    Given "bob8" is in the IRC channel "#bridge-one"
    When the user shares the contact "Jane" "Doe" with phone number "31612345678"
    Then "bob8" sees the bridge say "tester sent contact: Jane Doe, +31612345678" in "#bridge-one"

  Scenario: media are relayed as permalinks
    Given "bob9" is in the IRC channel "#bridge-one"
    When the user sends a photo "irc-photo"
    Then "bob9" sees the bridge say "tester sent http://nocto:3000/media/irc-photo.jpg" in "#bridge-one"

  Scenario: commands for other plugins are relayed as text
    Given "bob10" is in the IRC channel "#bridge-one"
    When the user sends "/echo both ways"
    Then "bob10" sees the bridge say "<tester> /echo both ways" in "#bridge-one"

  Scenario: private chats are never relayed
    Given "bob11" is in the IRC channel "#bridge-one"
    And a private chat
    When the user sends "just between us"
    Then "bob11" does not see the bridge say anything containing "just between us" in "#bridge-one"

  Scenario: relaying is one way for read-only channels
    Given "bob12" is in the IRC channel "#readonly"
    And a group chat with id -4106
    When the user sends "talking to myself"
    Then "bob12" does not see the bridge say anything containing "talking to myself" in "#readonly"

  Scenario: a group bridged to two channels speaks in both
    Given "bob13" is in the IRC channel "#multi-a"
    And "bob13" is in the IRC channel "#multi-b"
    And a group chat with id -4105
    When the user sends "stereo"
    Then "bob13" sees the bridge say "<tester> stereo" in "#multi-a"
    And "bob13" sees the bridge say "<tester> stereo" in "#multi-b"

  Scenario: backlog is not relayed
    Given "bob14" is in the IRC channel "#bridge-one"
    When the user sends "from the past" dated yesterday
    And the user sends "from the present"
    Then "bob14" sees the bridge say "<tester> from the present" in "#bridge-one"
    And "bob14" does not see the bridge say anything containing "from the past" in "#bridge-one"

  Scenario: banned users are not relayed
    Given "bob15" is in the IRC channel "#bridge-one"
    And a user with id 4315 and first name "Spammer" and username "spammer"
    And the user is known to the bot
    When the owner sends "/ban 4315"
    And the user sends "buy now"
    And user 4316 sends "legit"
    Then "bob15" sees the bridge say "<user4316> legit" in "#bridge-one"
    And "bob15" does not see the bridge say anything containing "buy now" in "#bridge-one"
