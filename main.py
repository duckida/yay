#
# SPDX-FileCopyrightText: Copyright 2023 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-FileCopyrightText: Copyright 2026 duckida
# SPDX-License-Identifier: MIT
#


import network
from machine import Pin, reset
from slack_bot import SlackBot
import time
import config

from picozero import Servo
servo = Servo(0)

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

def yay():
    for i in range(3):
        servo.value = 0.8
        time.sleep(0.2)
        servo.value = 0
        time.sleep(0.2)

    servo.off() # close to remove jitter

def yayayayayay():
    for i in range(3):
        servo.value = 0.8
        time.sleep(0.15)
        servo.value = 0
        time.sleep(0.15)

    servo.off()

def main():
    while True:
        event = slack_bot.poll()

        if event is None:
            continue

        print(event)

        event_type = event["type"]

        envelope_id = event.get("envelope_id")
        if envelope_id is not None:
            slack_bot.acknowledge_event(envelope_id, None)


        if event_type == "events_api":

            if event["payload"]["event"]["type"] == "reaction_added": # reactino of :yay:
                if event["payload"]["event"]["reaction"] == "yay": # and event["retry_attempt"] == 0:
                    print("reaction: yay!")
                    yay()
                elif event["payload"]["event"]["reaction"] == "yayayayayay": # and event["retry_attempt"] == 0:
                    print("reaction: yayayayayay!")
                    yayayayayay()

            elif event["payload"]["event"]["type"] == "message": # text message containing :yay:
                blocks = event["payload"]["event"]["blocks"]
                for block in blocks:
                    for section in block["elements"]:
                        for element in section["elements"]:
                            if element["type"] == "emoji": # it's an emoji
                                if element["name"] == "yay":# and event["retry_attempt"] == 0: # it's also the first one
                                    print("message: yay!")
                                    yay()

                                elif element["name"] == "yayayayayay":# and event["retry_attempt"] == 0: # yayayayay go faster
                                    print("message: yayayayayay!")
                                    yayayayayay()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Crashed:", e)
        time.sleep(1)
        reset()
