#
# SPDX-FileCopyrightText: Copyright 2023 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-FileCopyrightText: Copyright 2026 duckida
# SPDX-License-Identifier: MIT
#


import network
from machine import Pin
from slack_bot import SlackBot
import time
import config

from picozero import Servo


print(f"Connecting to Wi-Fi SSID: {config.WIFI_SSID}")

# initialize the Wi-Fi interface
wlan = network.WLAN(network.STA_IF)

# activate and connect to the Wi-Fi network:
wlan.active(True)
wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

while not wlan.isconnected():
    time.sleep(0.5)

print(f"Connected to Wi-Fi SSID: {config.WIFI_SSID}")

slack_bot = SlackBot(config.SLACK_APP_TOKEN, config.SLACK_BOT_TOKEN)
print("Ready for events")

while True:
    event = slack_bot.poll()

    if event is None:
        continue

    event_type = event["type"]


    if event_type == "events_api":
        blocks = event["payload"]["event"]["blocks"]
        for block in blocks:
            for section in block["elements"]:
                for element in section["elements"]:
                    if element["type"] == "emoji":
                        servo = Servo(0) # init servo
                        if element["name"] == "yay" and event["retry_attempt"] == 0: # it's also the first one
                            print("YAY!")
                            for i in range(3):
                                servo.value = 0.8
                                time.sleep(0.2)
                                servo.value = 0
                                time.sleep(0.2)
                                servo.close() # close to remove jitter
                        elif element["name"] == "yayayayayay" and event["retry_attempt"] == 0: # yayayayay go faster
                            print("yayayayayay!")
                            for i in range(3):
                                servo.value = 0.8
                                time.sleep(0.15)
                                servo.value = 0
                                time.sleep(0.15)
                                servo.close()
