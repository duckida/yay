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
try:
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.2)
        print(".")

    print(f"Connected to Wi-Fi SSID: {config.WIFI_SSID}")
except Exception as e:
    print("failed to connect")

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

        # poll for events
        try:
            event = slack_bot.poll()

            if event is None:
                continue

            # print(event) # removed for prod as it uses a lot of serial bandwidth

            event_type = event.get("type", [])

            envelope_id = event.get("envelope_id")
            if envelope_id is not None:
                slack_bot.acknowledge_event(envelope_id, None)
        except Exception as e:
            print(f"error when polling: {e}")
            continue


        if event_type == "events_api":
            if event.get("payload",[]).get("event",[]).get("type",[]) == "reaction_added": # reactino of :yay:
                if event.get("payload",[]).get("event",[]).get("reaction",[]) == "yay" and event["retry_attempt"] == 0:
                    print("reaction: yay!")
                    yay()
                elif event.get("payload",[]).get("event",[]).get("reaction",[]) == "yayayayayay" and event["retry_attempt"] == 0:
                    print("reaction: yayayayayay!")
                    yayayayayay()

            elif event.get("payload",[]).get("event",[]).get("type",[]) == "message": # text message containing :yay:
                blocks = event.get("payload",[]).get("event",[]).get("blocks",[])
                for block in blocks:
                    for section in block.get("elements", []):
                        for element in section.get("elements", []):
                            if element.get("type",[]) == "emoji": # it's an emoji
                                if element.get("name",[]) == "yay" and event["retry_attempt"] == 0: # it's also the first one
                                    print("message: yay!")
                                    yay()

                                elif element.get("name",[]) == "yayayayayay" and event["retry_attempt"] == 0: # yayayayay go faster
                                    print("message: yayayayayay!")
                                    yayayayayay()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Crashed:", e)
        time.sleep(1)
        reset()
