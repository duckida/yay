# yay

An attachment for a 3D-printed :yay: emoji, that moves its arms when a :yay: is sent or reacted Slack!

![The yay moving its arms](yay-demo.gif)

The Slack bot code is based on [ArmDeveloperEcosystem/example-of-a-slackbot-for-pico-w](https://github.com/ArmDeveloperEcosystem/example-of-a-slackbot-for-pico-w/tree/main)

## setup instructions
### hardware
You will need a Pico W and SG90 micro servo
- Wire a servo to GP0, VBUS and GND of a Pico W as shown in the diagram
- Put the Pico W in BOOTSELL mode and install MicroPython
- 3D-print the `servo-arm.stl`

<img width="612" height="482" alt="image" src="https://github.com/user-attachments/assets/6d9a7eb9-28f2-4e57-8493-266a36b665c9" />


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
- Install the app in your workspace and add it to channels you want to use it in!

## AI usage declaration
AI was used to help me understand errors some if statements and for help with power brownouts.
