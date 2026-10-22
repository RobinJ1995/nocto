@irc
Feature: relaying IRC to Telegram
    The bridge relays what happens in bridged IRC channels to their Telegram groups.

    Scenario: messages
        When "alice1" says "hello from irc" in "#bridge-one"
        Then group -4101 receives "<alice1@#bridge-one> hello from irc"

    Scenario: actions
        When "alice2" performs the action "waves" in "#bridge-one"
        Then group -4101 receives "** alice2@#bridge-one waves"

    Scenario: notices
        When "alice3" sends the notice "heads up" to "#bridge-one"
        Then group -4101 receives "<alice3@#bridge-one> heads up"

    Scenario: joins
        When "alice4" joins "#bridge-one"
        Then group -4101 receives "User alice4 joined channel #bridge-one"

    Scenario: parts
        Given "alice5" is in the IRC channel "#bridge-one"
        When "alice5" leaves "#bridge-one" saying "bye"
        Then group -4101 receives "User alice5 left channel #bridge-one (reason: "bye")"

    Scenario: quits
        Given "alice6" is in the IRC channel "#bridge-one"
        When "alice6" quits IRC saying "gone"
        Then group -4101 receives a message containing "User alice6 disconnected (reason: "
        And group -4101 receives a message containing "gone") and is no longer in channel(s) #bridge-one"

    Scenario: kicks
        Given "alice7" is in the IRC channel "#bridge-one"
        When the channel operator kicks "alice7" from "#bridge-one" because "spam"
        Then group -4101 receives "User alice7 was kicked from channel #bridge-one by chanop (reason: "spam")"

    Scenario: nick changes
        Given "alice8" is in the IRC channel "#bridge-one"
        When "alice8" changes nick to "alice8b"
        Then group -4101 receives "User alice8 is now known as alice8b in channel(s) #bridge-one"

    Scenario: topics
        When the channel operator sets the topic of "#bridge-one" to "Release day"
        Then group -4101 receives "Topic for #bridge-one is "Release day" (set by chanop)"

    Scenario: modes
        Given "alice9" is in the IRC channel "#bridge-one"
        When the channel operator sets mode "+v alice9" on "#bridge-one"
        Then group -4101 receives "chanop applied mode +v alice9 to channel #bridge-one"

    Scenario: emoji names become emoji
        When "alice10" says "pizza time :pizza:" in "#bridge-one"
        Then group -4101 receives "<alice10@#bridge-one> pizza time 🍕"

    Scenario: skin tone suffixes are applied
        When "alice11" says "nice 👍#4" in "#bridge-one"
        Then group -4101 receives "<alice11@#bridge-one> nice 👍🏽"

    Scenario: a channel can feed several groups
        When "alice12" says "for both of you" in "#bridge-shared"
        Then group -4103 receives "<alice12@#bridge-shared> for both of you"
        And group -4104 receives "<alice12@#bridge-shared> for both of you"

    Scenario: other channels stay out
        When "alice13" says "wrong room" in "#bridge-two"
        Then group -4102 receives "<alice13@#bridge-two> wrong room"
        And group -4101 receives nothing containing "wrong room"
