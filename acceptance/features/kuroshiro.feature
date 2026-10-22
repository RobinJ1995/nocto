Feature: kuroshiro plugin
    Converts Japanese text between kanji, hiragana, katakana and romaji.

    Background:
        Given a group chat with id -1400
        And a user with id 1400 and first name "Tester"

    Scenario Outline: /<command> <input>
        When the user sends "/<command> <input>"
        Then the bot replies "<output>"

        Examples:
            | command  | input      | output     |
            | hiragana | 漢字       | かんじ     |
            | katakana | 漢字       | カンジ     |
            | romaji   | 漢字       | kanji      |
            | hiragana | 東京       | とうきょう |
            | romaji   | 東京       | toukyou    |
            | kana     | konnichiwa | こんにちわ |

    Scenario: nothing to convert
        When the user sends "/romaji"
        Then the bot sends no reply
