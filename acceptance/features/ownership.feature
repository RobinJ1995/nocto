@pristine
Feature: claiming ownership
  A freshly installed bot has no owner and lets everyone through its firewall. The first user to
  send /owner becomes the owner, after which the firewall applies. Here private commands need a
  trusted user.

  This bot instance is never claimed anywhere else, so this is its only scenario. The owner
  deliberately isn't the first user the bot ever saw.

  Scenario: the first user to claim the bot becomes its owner
    Given a private chat
    When user 3150 sends "/echo anyone can talk to me"
    Then the bot replies "anyone can talk to me"
    When user 3100 sends "/owner"
    Then the bot replies "You are now registered as my owner."
    When user 3150 sends "/owner" in chat -3100
    Then the bot replies "I already have an owner."
    When user 3150 sends "/echo now I need permission"
    Then the bot sends no reply
    When user 3100 sends "/echo but I don't"
    Then the bot replies "but I don't"
    When user 3160 sends "/echo hello" in chat -3100
    Then the bot replies "hello"
    When user 3100 sends "/ban 3160" in chat -3100
    Then the bot replies "Authority level set to "blacklisted"."
    When user 3160 sends "/echo hello again" in chat -3100
    Then the bot sends no reply
