Feature: plugin control
    /plugins lists plugins for trusted users and lets administrators load, unload, enable, disable
    and reload them.

    Background:
        Given a group chat with id -2300

    Scenario: regular users may not list plugins
        When user 2300 sends "/plugins status"
        Then the bot replies "Sorry, you are not authorized to perform this operation."

    Scenario Outline: trusted users may list plugins (<command>)
        Given user 2301 is a trusted user
        When user 2301 sends "<command>"
        Then the bot reply matches "Ld/En/Name(\n(✔️|❌){2} \w+)+"

        Examples:
            | command          |
            | /plugins status  |
            | /plugins list    |
            | /plugin list     |
            | /PLUGINS STATUS  |

    Scenario: the status is the default operation
        Given user 2307 is a trusted user
        When user 2307 sends "/plugins"
        Then the bot reply matches "Ld/En/Name(\n(✔️|❌){2} \w+)+"

    Scenario Outline: the status shows what is loaded and enabled (<plugin>)
        Then the plugin status lists "<plugin>" as <state>

        Examples:
            | plugin        | state               |
            | echo          | loaded and enabled  |
            | timezone      | loaded and enabled  |
            | kuroshiro     | loaded and enabled  |
            | cowsay        | loaded and enabled  |
            | googlesuggest | loaded and enabled  |
            | feedannounce  | loaded and enabled  |
            | ircbridge     | loaded and enabled  |
            | stickersource | loaded but disabled |
            | trace         | loaded but disabled |

    Scenario: trusted users may not change plugins
        Given user 2302 is a trusted user
        When user 2302 sends "/plugins enable trace"
        Then the bot replies "Sorry, you are not authorized to perform this operation."

    Scenario: an administrator enables and disables a plugin
        Given user 2303 is an administrator
        When user 2303 sends "/plugins enable trace"
        Then the bot replies "✔️ Enable trace"
        And the plugin status lists "trace" as loaded and enabled
        When user 2303 sends "/plugins disable trace"
        Then the bot replies "✔️ Disable trace"
        And the plugin status lists "trace" as loaded but disabled

    Scenario: a disabled plugin stops answering
        Given the owner has disabled the "echo" plugin
        When user 2304 sends "/echo anyone there?"
        Then the bot sends no reply

    Scenario: a re-enabled plugin answers again
        Given the owner has disabled the "echo" plugin
        And the owner has enabled the "echo" plugin
        When user 2305 sends "/echo back again"
        Then the bot replies "back again"

    Scenario: unloading and loading a plugin
        When the owner sends "/plugins unload trace"
        Then the bot replies
            """
            ✔️ Disable trace
            ✔️ Unload trace
            """
        And the plugin status lists "trace" as not loaded
        When the owner sends "/plugins load trace"
        Then the bot replies "✔️ Load trace"
        And the plugin status lists "trace" as loaded but disabled

    Scenario: reloading a plugin keeps it working
        When the owner sends "/plugins reload echo"
        Then the bot replies
            """
            ✔️ Disable echo
            ✔️ Unload echo
            ✔️ Load echo
            ✔️ Enable echo
            """
        When user 2306 sends "/echo still here"
        Then the bot replies "still here"

    Scenario: loading a plugin that is already loaded
        When the owner sends "/plugins load echo"
        Then the bot replies "✔️ Load echo"

    Scenario: an unknown plugin
        When the owner sends "/plugins enable nope"
        Then the bot replies "Plugin "nope" not found"

    Scenario: nothing to do
        When the owner sends "/plugins enable"
        Then the bot replies "No operation performed"

    Scenario: the bot shows it is working on it
        When the owner sends "/plugins disable trace"
        Then the bot shows that it is typing
