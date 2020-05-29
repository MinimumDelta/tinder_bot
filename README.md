# tldr
A Tinder swiping and data harvesting bot.

# setup
1. Install required packages
2. Run tinder_bot.py

# requirements
A Tinder account tied to a phone number.
Currently the only way to authenticate (log in) is to use a phone number to receive a text message. This is all done through tinder_bot and the auth code is stored automatically in a separate file for later use so a user only needs to authenticate once (until auth code expires, a long time).

# features
This bot can harvest profile data including name, age, distance (from swiper), bio, profile pictures, and instagram pictures. By default, it will harvest everything.
The bot can also swipe on users based on a given criteria (age, distance, number of profile pictures).
Most features are configurable. Image harvesting can be configured to only download profile pictures and/or instagram pictures, and can be capped at a specific age (for example, only downloading images of users below age 28).

# future
The bot will use computer vision to make better swiping and image downloading decisions.
A better way to sort through the harvested data will be created at some point.