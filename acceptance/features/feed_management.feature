Feature: managing feeds
    Administrators register shared RSS/Atom feeds; any chat can subscribe to them.

    Background:
        Given a group chat with id -2600

    Scenario Outline: usage help (<command>)
        When the owner sends "<command>"
        Then the bot replies "Usage: <command> <label> <url>"

        Examples:
            | command  |
            | /addfeed |
            | /newfeed |

    Scenario Outline: malformed registrations (<arguments>)
        When the owner sends "/addfeed <arguments>"
        Then the bot replies "Please specifiy a valid feed label and URL."

        Examples:
            | arguments                                      |
            | headlines                                      |
            | http://feeds.nocto.test/feeds/a.xml            |
            | news http://feeds.nocto.test/feeds/a.xml extra |

    Scenario: registering a feed
        When the owner sends "/addfeed fm-register http://feeds.nocto.test/feeds/register.xml"
        Then the bot replies "Feed "fm-register" registered."
        And the bot quotes the user's message

    Scenario: labels are unique
        When the owner sends "/addfeed fm-dupe http://feeds.nocto.test/feeds/dupe.xml"
        Then the bot replies "Feed "fm-dupe" registered."
        When the owner sends "/addfeed fm-dupe http://feeds.nocto.test/feeds/other.xml"
        Then the bot replies "A feed with this label already exists."

    Scenario Outline: only administrators manage feeds (<command>)
        When user 2601 sends "<command>"
        Then the bot replies "Sorry, you are not authorized to perform this operation."

        Examples:
            | command                                                   |
            | /addfeed fm-denied http://feeds.nocto.test/feeds/denied.xml |
            | /delfeed fm-denied                                        |

    Scenario: removing a feed that doesn't exist
        When the owner sends "/delfeed nope"
        Then the bot replies "There is no feed labeled "nope"."

    Scenario Outline: removing a feed (<command>)
        When the owner sends "/addfeed fm-<command> http://feeds.nocto.test/feeds/remove.xml"
        Then the bot replies "Feed "fm-<command>" registered."
        When the owner sends "/<command> fm-<command>"
        Then the bot replies "Feed "fm-<command>" removed."

        Examples:
            | command    |
            | delfeed    |
            | deletefeed |
            | rmfeed     |
            | remfeed    |
            | removefeed |

    Scenario: picking a feed to remove
        When the owner sends "/addfeed fm-pick http://feeds.nocto.test/feeds/pick.xml"
        Then the bot replies "Feed "fm-pick" registered."
        When the owner sends "/delfeed"
        Then the bot replies "Which feed would you like to remove?"
        And the bot reply offers the button "/delfeed fm-pick"

    Scenario Outline: subscribing (<command>)
        Given a group chat with id <chat>
        When the owner sends "/addfeed fm-<command> http://feeds.nocto.test/feeds/sub.xml"
        Then the bot replies "Feed "fm-<command>" registered."
        When user 2602 sends "/<command> fm-<command>"
        Then the bot replies "Subscribed to feed "fm-<command>"."
        And the bot quotes the user's message

        Examples:
            | command   | chat  |
            | sub       | -2610 |
            | subscribe | -2611 |

    Scenario: picking a feed to subscribe a group to
        Given a group chat with id -2612
        When the owner sends "/addfeed fm-group-pick http://feeds.nocto.test/feeds/pick.xml"
        Then the bot replies "Feed "fm-group-pick" registered."
        When user 2603 sends "/sub"
        Then the bot replies "Which feed do you wish to subscribe this group to?"
        And the bot reply offers the button "/sub fm-group-pick"
        And the reply keyboard is one-time, selective and resized

    Scenario: picking a feed to subscribe to privately
        Given a private chat
        When the owner sends "/addfeed fm-private-pick http://feeds.nocto.test/feeds/pick.xml"
        Then the bot replies "Feed "fm-private-pick" registered."
        When user 2604 sends "/sub"
        Then the bot replies "Which feed do you wish to subscribe to?"
        And the bot reply offers the button "/sub fm-private-pick"
        And the bot does not quote the user's message

    Scenario: feeds already subscribed to are not offered again
        Given a group chat with id -2613
        When the owner sends "/addfeed fm-taken http://feeds.nocto.test/feeds/taken.xml"
        Then the bot replies "Feed "fm-taken" registered."
        When user 2605 sends "/sub fm-taken"
        Then the bot replies "Subscribed to feed "fm-taken"."
        When user 2605 sends "/sub"
        Then the bot reply does not offer the button "/sub fm-taken"

    Scenario: subscribing to a feed that doesn't exist
        When user 2606 sends "/sub nope"
        Then the bot replies "There is no feed labeled "nope"."

    Scenario: subscribing to an arbitrary URL
        When user 2607 sends "/sub http://feeds.nocto.test/feeds/custom.xml"
        Then the bot replies "Custom subcriptions are not supported yet."

    Scenario: unsubscribing without any subscriptions
        Given a group chat with id -2614
        When user 2608 sends "/unsub"
        Then the bot replies "You are not subscribed to any feeds."

    Scenario Outline: unsubscribing (<command>)
        Given a group chat with id <chat>
        When the owner sends "/addfeed fm-<command> http://feeds.nocto.test/feeds/unsub.xml"
        Then the bot replies "Feed "fm-<command>" registered."
        When user 2609 sends "/sub fm-<command>"
        Then the bot replies "Subscribed to feed "fm-<command>"."
        When user 2609 sends "/<command> fm-<command>"
        Then the bot replies "Unsubscribed from feed "fm-<command>"."

        Examples:
            | command     | chat  |
            | unsub       | -2615 |
            | unsubscribe | -2616 |

    Scenario: picking a feed to unsubscribe from
        Given a group chat with id -2617
        When the owner sends "/addfeed fm-leave http://feeds.nocto.test/feeds/leave.xml"
        Then the bot replies "Feed "fm-leave" registered."
        When user 2610 sends "/sub fm-leave"
        Then the bot replies "Subscribed to feed "fm-leave"."
        When user 2610 sends "/unsub"
        Then the bot replies "Which feed would you like to unsubscribe from?"
        And the bot reply offers the button "/unsub fm-leave"

    Scenario: unsubscribing from a feed that doesn't exist
        Given a group chat with id -2618
        When the owner sends "/addfeed fm-real http://feeds.nocto.test/feeds/real.xml"
        Then the bot replies "Feed "fm-real" registered."
        When user 2611 sends "/sub fm-real"
        Then the bot replies "Subscribed to feed "fm-real"."
        When user 2611 sends "/unsub nope"
        Then the bot replies "There is no feed labeled "nope"."

    @strict
    Scenario: no feeds to remove
        Given a private chat
        When the owner sends "/delfeed"
        Then the bot replies "There are no shared feeds to remove."

    @strict
    Scenario: no feeds to subscribe to
        Given a private chat
        When the owner sends "/sub"
        Then the bot replies "There are no more shared feeds you can subscribe to."
