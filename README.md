# yay

This is a mod for the physical 3D-printed :yay: emoji, which moves it up and down using a servo when a message containing :yay: is sent on Slack!

it's mostly based on [ArmDeveloperEcosystem/example-of-a-slackbot-for-pico-w](https://github.com/ArmDeveloperEcosystem/example-of-a-slackbot-for-pico-w/tree/main)

## setup instructions
### hardware
You will need a Pico W and SG90 micro servo
- Wire a servo to GP0, 5V and GND of a Pico W
- Put the Pico W in BOOTSELL mode and install MicroPython

### software
- Clone this repo: `git clone https://github.com/duckida/yay && cd yay`
- Copy all the `.py` files to the Pico
- Fill in your WiFi details in `config.py`

### Slack bot setup
Don't forget to save changes as you go!
- Visit https://api.slack.com/apps and create a new app
- Fill in the basic details like name and description
- Under Settings→Socket Mode turn on Socket Mode
- Under Features→OAuth and Permissions, scroll to Scopes, and add `app_mentions:read`, `channels:history`, and `reactions:read`
- Copy the Bot User OAuth Token and paste it in `config.py` as the bot token
- Under Features→Event Subscriptions, under Subscribe to Bot Events, enable `app_mention`, `message.channels`, and `reaction_added`
- Go to Settings→Basic Information, scroll to App-Level Tokens, create one, and copy that into `config.py` as the app token
