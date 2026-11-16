#
# SPDX-FileCopyrightText: Copyright 2023 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-FileCopyrightText: Copyright 2026 duckida
# SPDX-License-Identifier: MIT
#

import machine
import network
from machine import reset
from slack_bot import SlackBot
import time
import config

from servo import Servo

# SG90 calibration. These are the endpoints the model was built for on the
# original Pico version (picozero used 1.0-1.8 ms). If the arm buzzes or
# presses against the body at rest, adjust these two values.
SERVO_MIN_US = 1000
SERVO_MAX_US = 1800
REST_ANGLE = 0
YAY_ANGLE = 180

servo = Servo(4, min_us=SERVO_MIN_US, max_us=SERVO_MAX_US)

# If anything below blocks forever (network stall, bad TLS handshake), the
# watchdog reboots the board instead of leaving it dead until it is unplugged.
try:
    wdt = machine.WDT(timeout=60000)
except Exception as e:
    wdt = None
    print(f"Watchdog unavailable: {e}")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)


def connect_wifi(timeout=30):
    if wlan.isconnected():
        return True

    try:
        wlan.disconnect()
    except Exception:
        pass

    try:
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    except Exception as e:
        print(f"Wi-Fi connect error: {e}")
        return False

    start = time.ticks_ms()
    while not wlan.isconnected():
        if wdt is not None:
            wdt.feed()
        if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
            return False
        time.sleep(0.2)
    return True


print(f"Connecting to Wi-Fi SSID: {config.WIFI_SSID}")
while not connect_wifi(30):
    print("Wi-Fi connect failed; retrying in 5s")
    if wdt is not None:
        wdt.feed()
    time.sleep(5)
print(f"Connected to Wi-Fi SSID: {config.WIFI_SSID}")
try:
    print(f"IP {wlan.ifconfig()[0]} RSSI {wlan.status('rssi')}")
except Exception:
    pass

slack_bot = SlackBot(config.SLACK_APP_TOKEN, config.SLACK_BOT_TOKEN)
print("Ready for events")


def yay():
    for i in range(3):
        servo.write_angle(YAY_ANGLE)
        time.sleep(0.2)
        servo.write_angle(REST_ANGLE)
        time.sleep(0.2)

    # Stop sending pulses; otherwise the SG90 holds position and buzzes
    # continuously, drawing current and heating up between events.
    servo.off()


def yayayayayay():
    for i in range(3):
        servo.write_angle(YAY_ANGLE)
        time.sleep(0.15)
        servo.write_angle(REST_ANGLE)
        time.sleep(0.15)

    servo.off()


def contains_yay(event):
    names = []

    blocks = event.get("blocks") or []
    for block in blocks:
        for section in block.get("elements") or []:
            for element in section.get("elements") or []:
                if not isinstance(element, dict):
                    continue
                if element.get("type") == "emoji":
                    name = (element.get("name") or "").split("::")[0]
                    if name == "yay" or name == "yayayayayay":
                        names.append(name)

    if not names:
        # Messages from the API/webhooks (and some clients) have no rich_text
        # blocks, only text.
        text = event.get("text") or ""
        if ":yayayayayay:" in text:
            names.append("yayayayayay")
        elif ":yay:" in text:
            names.append("yay")

    return names


def process_event(event):
    if event.get("type") != "events_api":
        return

    payload = event.get("payload") or {}
    inner = payload.get("event") or {}
    event_type = inner.get("type")

    if event_type == "reaction_added":
        # Skin-tone variants arrive as e.g. "yay::skin-tone-3".
        reaction = (inner.get("reaction") or "").split("::")[0]
        if reaction == "yay":
            print("reaction: yay!")
            yay()
        elif reaction == "yayayayayay":
            print("reaction: yayayayayay!")
            yayayayayay()

    elif event_type == "message" or event_type == "app_mention":
        names = contains_yay(inner)
        if "yayayayayay" in names:
            print("message: yayayayayay!")
            yayayayayay()
        elif "yay" in names:
            print("message: yay!")
            yay()


def main():
    while True:
        if wdt is not None:
            wdt.feed()

        if not wlan.isconnected():
            print("Wi-Fi lost; reconnecting")
            slack_bot.close()
            while not connect_wifi(15):
                print("Wi-Fi reconnect failed; retrying in 2s")
                if wdt is not None:
                    wdt.feed()
                time.sleep(2)
            print("Wi-Fi reconnected")

        # poll for events
        try:
            event = slack_bot.poll()
        except Exception as e:
            print(f"error when polling: {e}")
            time.sleep(1)
            continue

        if event is None:
            # Don't spin at full CPU speed when the socket is idle.
            time.sleep(0.02)
            continue

        envelope_id = event.get("envelope_id")
        if envelope_id is not None:
            try:
                slack_bot.acknowledge_event(envelope_id, None)
            except Exception as e:
                print(f"error when acknowledging: {e}")
                slack_bot.close()
                time.sleep(0.5)
                continue

        try:
            process_event(event)
        except Exception as e:
            print(f"error when handling event: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Crashed:", e)
        time.sleep(1)
        reset()
