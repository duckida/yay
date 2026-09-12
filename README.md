# yay

An attachment for a 3D-printed :yay: emoji, that moves its arms when a :yay: is sent or reacted Slack!

![The yay moving its arms](yay-demo.gif)

The Slack bot code is based on [ArmDeveloperEcosystem/example-of-a-slackbot-for-pico-w](https://github.com/ArmDeveloperEcosystem/example-of-a-slackbot-for-pico-w/tree/main)

## setup instructions
### hardware

### bill of materials
| Product | Quantity | Price (GBP) | Link |
| :--- | :---: | :---: | :--- |
| ESP32 C3 SuperMini | 1 | 2.44 | [Link](https://www.aliexpress.com/item/1005008234672660.html?spm=a2g0o.productlist.main.4.deda6647XHU4Vi&aem_p4p_detail=202609120912169704214977795140000158710&algo_pvid=53ecbb60-9368-4579-b89d-fb3343f11cf6&algo_exp_id=53ecbb60-9368-4579-b89d-fb3343f11cf6-3&pdp_ext_f=%7B%22order%22%3A%222312%22%2C%22spu_best_type%22%3A%22price%22%2C%22eval%22%3A%221%22%2C%22fromPage%22%3A%22search%22%7D&pdp_npi=6%40dis%21GBP%212.61%212.60%21%21%213.42%213.41%21%402103842a17892295367764229e0f5a%2112000044321264943%21sea%21UK%216546500973%21ABX%211%210%21n_tag%3A-29910%3Bd%3A7683b1f4%3Bm03_new_user%3A-29895%3BpisId%3A5000000211438706&curPageLogUid=gSGXP5SobNPj&utparam-url=scene%3Asearch%7Cquery_from%3A%7Cx_object_id%3A1005008234672660%7C_p_origin_prod%3A&search_p4p_id=202609120912169704214977795140000158710_1) |
| SG90 Micro Servo | 1 | 4.00 | [Link](https://thepihut.com/products/towerpro-servo-motor-sg90-digital) |

You will need an ESP32 SuperMini and SG90 micro servo
- Wire a servo to GP4, 5V and GND of the ESP32 as shown in the diagram
- Install MicroPython to the ESP32 using esptool.py
- 3D-print the `servo-arm.stl`


### software
- Clone this repo: `git clone https://github.com/duckida/yay && cd yay`
- Copy all the `.py` files to the ESP
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
