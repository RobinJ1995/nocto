Feature: media permalinks
  The bot remembers the media shared in a chat. /permalink answers with a link on the bot's own
  web server that streams the file from Telegram.

  Background:
    Given a group chat with id -2400
    And a user with id 2400 and first name "Tester"

  Scenario: nothing has been shared
    When the user sends "/permalink"
    Then the bot sends no reply

  Scenario Outline: links reflect the kind of media (<kind>)
    When the user sends <media>
    And the user sends "/permalink"
    Then the permalink is "<path>"

    Examples:
      | kind                | media                                                                | path                           |
      | photo               | a photo "pl-photo"                                                   | /media/pl-photo.jpg            |
      | document            | a document "pl-doc" named "report.pdf" of type "application/pdf"     | /media/pl-doc/report.pdf       |
      | audio               | an audio file "pl-audio" titled "Song" by "Artist"                   | /media/pl-audio/Artist+-+Song.mp3 |
      | voice               | a voice message "pl-voice"                                           | /media/pl-voice.opus           |
      | voice with a type   | a voice message "pl-ogg" of type "audio/ogg"                         | /media/pl-ogg.ogg              |
      | video               | a video "pl-video" of type "video/mp4"                               | /media/pl-video.mp4            |
      | sticker             | a sticker "pl-sticker"                                               | /media/pl-sticker/sticker.webp |

  Scenario: older media can be reached with an offset
    When the user sends a photo "pl-first"
    And the user sends a photo "pl-second"
    And the user sends "/permalink 1"
    Then the permalink is "/media/pl-first.jpg"

  Scenario Outline: offsets that point nowhere (<offset>)
    Given a group chat with id -2401
    When the user sends a photo "pl-only"
    And the user sends "/permalink <offset>"
    Then the bot sends no reply

    Examples:
      | offset |
      | 1      |
      | 5      |
      | abc    |

  Scenario: links are remembered per chat
    Given a group chat with id -2402
    When the user sends a photo "pl-elsewhere"
    And user 2400 sends "/permalink" in chat -2403
    Then the bot sends no reply

  Scenario: links are sent without a preview
    When the user sends a photo "pl-preview"
    And the user sends "/permalink"
    Then the permalink is "/media/pl-preview.jpg"
    And the bot reply has no link preview

  Scenario: a permalink serves the file
    Given the file "pl-served" contains "%PDF-1.4 pretend this is a report"
    When the user sends a document "pl-served" named "report.pdf" of type "application/pdf"
    And the user sends "/permalink"
    And the permalink is downloaded
    Then the download contains the file "pl-served"
    And the download has content type "application/pdf" and is shown inline

  Scenario: photos are served as JPEG
    Given the file "pl-jpeg" contains "not really a jpeg"
    When the user sends a photo "pl-jpeg"
    And the user sends "/permalink"
    And the permalink is downloaded
    Then the download contains the file "pl-jpeg"
    And the download has content type "image/jpeg" and is shown inline

  Scenario: file lookups are cached
    Given the file "pl-cached" contains "cache me"
    When the user sends a photo "pl-cached"
    And the user sends "/permalink"
    And the permalink is downloaded
    And the permalink is downloaded
    Then the download contains the file "pl-cached"
    And the bot looked up the file "pl-cached" 1 time(s)

  Scenario: Telegram drops the download
    Given Telegram drops the connection when the file "pl-dropped" is downloaded
    When the user sends a photo "pl-dropped"
    And the user sends "/permalink"
    And the permalink is downloaded
    Then the download fails with status 502

  Scenario: a file Telegram doesn't know
    When "/media/pl-missing.jpg" is downloaded from the bot
    Then the download fails

  Scenario: anything else on the web server
    When "/nothing/here" is downloaded from the bot
    Then the download fails with status 404
