Feature: stickersource plugin
    Stickers are converted to PNG documents, images to stickers.

    Background:
        Given the owner has enabled the "stickersource" plugin
        And a group chat with id -2500
        And a user with id 2500 and first name "Tester"

    Scenario: an image that can't be converted
        Given the file "ss-broken-photo" contains "this is not an image"
        When the user sends a photo "ss-broken-photo"
        Then the bot replies "Failed to convert image, details have been logged."

    Scenario: a sticker that can't be converted
        Given the file "ss-broken-sticker" contains "this is not a sticker"
        When the user sends a sticker "ss-broken-sticker"
        Then the bot replies "Failed to convert sticker, details have been logged."

    Scenario: backlog media is ignored
        Given the file "ss-old-photo" contains "this is not an image"
        When the user sends a photo "ss-old-photo" dated yesterday
        Then the bot sends no reply
