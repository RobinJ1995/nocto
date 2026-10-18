@pristine
Feature: claiming ownership
  A freshly installed bot has no owner and lets everyone through its firewall. The first user to
  send /owner becomes the owner.

  This bot instance is never claimed anywhere else, so this is its only scenario.

  Scenario: the first user to claim the bot becomes its owner
    Given a private chat
    When user 3150 sends "/echo anyone can talk to me"
    Then the bot replies "anyone can talk to me"
    When user 3100 sends "/owner"
    Then the bot replies "You are now registered as my owner."
    When user 3150 sends "/owner" in chat -3100
    Then the bot replies "I already have an owner."
