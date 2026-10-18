Feature: stickersource plugin
  Stickers are converted to PNG documents, images to stickers.

  Background:
    Given the owner has enabled the "stickersource" plugin
    And a group chat with id -2500
    And a user with id 2500 and first name "Tester"

  Scenario: a photo becomes a sticker
    Given the file "ss-photo" is the image "photo.jpg"
    When the user sends a photo "ss-photo"
    Then the bot sends a sticker in WebP format

  Scenario: an image document becomes a sticker
    Given the file "ss-png" is the image "image.png"
    When the user sends a document "ss-png" named "image.png" of type "image/png"
    Then the bot sends a sticker in WebP format

  Scenario: a sticker becomes a PNG document
    Given the file "ss-sticker" is the image "sticker.webp"
    When the user sends a sticker "ss-sticker"
    Then the bot sends the document "sticker.png" in PNG format

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
