@irc
Feature: restarting the bridge
    Disabling and re-enabling ircbridge reconnects it to IRC with all its routes.

    Scenario: the bridge works again after a restart
        Given "gina1" is in the IRC channel "#bridge-one"
        And a group chat with id -4101
        When the owner disables and re-enables the "ircbridge" plugin
        Then group -4101 receives "I am now attached to channel #bridge-one"
        When "gina1" says "still there?" in "#bridge-one"
        Then group -4101 receives "<gina1@#bridge-one> still there?"

    Scenario: the bridge doesn't announce its own nick changes
        Given a group chat with id -4108
        When an IRC operator renames "noctoc" to "noctoc_renamed"
        Then group -4108 receives nothing containing "is now known as"
