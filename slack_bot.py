import gc
import json
import time

import websocket_client

from requests import request


class SlackBot:
    def __init__(self, app_token, bot_token):
        self._app_token = app_token
        self._bot_token = bot_token
        self._ws = None
        self._retry_at = 0
        self._retry_delay = 1

    def close(self):
        ws = self._ws
        self._ws = None
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    def _failed(self):
        self.close()
        self._retry_at = time.ticks_ms() + self._retry_delay * 1000
        self._retry_delay = min(self._retry_delay * 2, 60)

    def _connect(self):
        # Close first: never overlap two TLS sessions on this small heap.
        self.close()
        gc.collect()

        response = None
        try:
            response = request(
                "POST",
                "https://slack.com/api/apps.connections.open",
                headers={"Authorization": f"Bearer {self._app_token}"},
                timeout=10,
            )
            open_json = response.json()
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

        if not open_json.get("ok"):
            raise Exception(
                f"apps.connections.open failed: {open_json.get('error', 'unknown')}"
            )

        ws_url = open_json.get("url")
        if not ws_url:
            raise Exception("apps.connections.open returned no url")

        ws = websocket_client.WebSocket()
        try:
            ws.connect(ws_url, timeout=10)
        except Exception:
            ws.close()
            raise

        self._ws = ws
        self._retry_at = 0
        self._retry_delay = 1
        print("slack: connected")

    def poll(self):
        if self._retry_at:
            if time.ticks_diff(time.ticks_ms(), self._retry_at) < 0:
                return None
            self._retry_at = 0

        if self._ws is None or not self._ws.connected():
            try:
                self._connect()
            except Exception as e:
                print(f"slack: connect error: {e}")
                self._failed()
                return None

        try:
            rx, rx_type = self._ws.recv()
        except Exception as e:
            print(f"slack: recv error: {e}")
            self._failed()
            raise

        if rx is None:
            if not self._ws.connected():
                print("slack: connection closed")
            return None

        if rx_type == websocket_client.TYPE_PING:
            # received ping, response with pong
            try:
                self._ws.send(rx, websocket_client.TYPE_PONG)
            except Exception as e:
                print(f"slack: pong error: {e}")
                self._failed()
                raise
            return None

        if rx_type == websocket_client.TYPE_CONNECTION_CLOSE:
            self.close()
            return None

        try:
            event = json.loads(rx)
        except Exception as e:
            print(f"slack: bad json: {e}")
            self._failed()
            raise

        if event.get("type") == "disconnect":
            # Slack asks us to reconnect (e.g. server maintenance). Give the
            # old connection a moment to be released before opening a new one.
            print(f"slack: disconnect: {event.get('reason')}")
            self.close()
            self._retry_at = time.ticks_ms() + 2000
            return None

        if event.get("type") == "hello":
            print("slack: hello")

        return event

    def acknowledge_event(self, envelope_id, payload=None):
        if self._ws is None or not self._ws.connected():
            raise OSError("WebSocket is not connected")

        msg = {"envelope_id": envelope_id}

        if payload is not None:
            msg["payload"] = payload

        self._ws.send(json.dumps(msg), websocket_client.TYPE_TEXT)
