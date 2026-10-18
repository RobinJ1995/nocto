Feature: cowsay plugin
    Inline queries are answered with the text spoken by every available cow.

    Background:
        Given a user with id 1500 and first name "Tester"

    Scenario: an empty query gets no results
        When the user types the inline query ""
        Then the inline query is answered with no results

    Scenario: the classic cow and Tux come first
        When the user types the inline query "moo"
        Then the first inline results are titled "Cow", "Tux"
        And every inline result has a unique id

    Scenario: blacklisted cows are never offered
        When the user types the inline query "baa"
        Then no inline result is titled "Sheep"

    Scenario: every cow says the query in a code block
        When the user types the inline query "moo"
        Then every inline result shows the cow saying "moo" in a Markdown code block

    Scenario: results carry a thumbnail
        When the user types the inline query "moo"
        Then the inline result "Cow" has the thumbnail "https://cows.nocto.test/default.png"

    Scenario: text too long for a message gets no results
        When the user types the inline query "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
        Then the inline query is answered with no results

    Scenario: text that would break the code block gets no results
        When the user types the inline query "```"
        Then the inline query is answered with no results

    @strict
    Scenario: a whitelist limits the cows on offer
        Given a user with id 7400 and first name "Tester"
        When the user types the inline query "moo"
        Then the inline results are titled exactly "Cow", "Tux", "Moose"
