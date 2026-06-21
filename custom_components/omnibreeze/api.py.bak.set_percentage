from __future__ import annotations

import base64
import hashlib
import json
import random
import socket
import ssl
import string
import time
from dataclasses import dataclass
from typing import Any

import httpx
import websocket
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .const import API_BASE, MQTT_URL


ACTIONS = {
    "on": (0x0009, None),
    "off": (0x0008, None),
    "sound_on": (0x0069, None),
    "sound_off": (0x0068, None),
    "osc_on": (0x0029, None),
    "osc_off": (0x0028, None),
    "mode_normal": (0x0012, 0),
    "mode_natural": (0x0012, 1),
    "mode_sleep": (0x0012, 2),
    "mode_auto": (0x0012, 3),
    "display_off": (0x0078, None),
    "display_on": (0x0079, None),
    "countdown_cancel": (0x00B2, 0),
    "countdown_1h": (0x00B2, 1),
    "countdown_2h": (0x00B2, 2),
    "countdown_3h": (0x00B2, 3),
    "countdown_4h": (0x00B2, 4),
    "countdown_5h": (0x00B2, 5),
    "countdown_6h": (0x00B2, 6),
    "countdown_7h": (0x00B2, 7),
    "countdown_8h": (0x00B2, 8),
    "countdown_9h": (0x00B2, 9),
    "countdown_10h": (0x00B2, 10),
    "countdown_11h": (0x00B2, 11),
    "countdown_12h": (0x00B2, 12),
}


@dataclass
class OmniBreezeDevice:
    device_key: str
    name: str
    product_key: str
    product_name: str | None = None
    online: bool = False
    state: dict[str, Any] | None = None


class OmniBreezeApiError(Exception):
    pass


class OmniBreezeApi:
    def __init__(
        self,
        email: str,
        password: str,
        user_domain: str,
        user_domain_secret: str,
    ) -> None:
        self.email = email
        self.password = password
        self.user_domain = user_domain
        self.user_domain_secret = user_domain_secret

        self.access_token: str | None = None
        self.expiration_time: int = 0
        self.uid: str | None = None
        self.fid: str | None = None
        self.devices: dict[str, OmniBreezeDevice] = {}

    def generate_login_random(self) -> str:
        chars = string.digits + string.ascii_uppercase[:25] + string.ascii_lowercase[:25]
        return "".join(random.SystemRandom().choice(chars) for _ in range(16))

    def md5_upper(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest().upper()

    def sha256_lower(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def encrypt_password(self, password: str, random_value: str) -> str:
        key_source = self.md5_upper(random_value)[8:24]
        iv = key_source[8:16] + key_source[0:8]

        cipher = AES.new(
            key_source.encode("utf-8"),
            AES.MODE_CBC,
            iv.encode("utf-8"),
        )

        encrypted = cipher.encrypt(pad(password.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    def jwt_payload(self, token: str) -> dict[str, Any]:
        if token.startswith("Bearer "):
            token = token.split(" ", 1)[1]

        try:
            middle = token.split(".")[1]
            middle += "=" * (-len(middle) % 4)
            return json.loads(base64.urlsafe_b64decode(middle.encode()).decode())
        except Exception:
            return {}

    def login_payload(self) -> dict[str, str]:
        random_value = self.generate_login_random()
        encrypted_pwd = self.encrypt_password(self.password, random_value)

        signature = self.sha256_lower(
            self.email + encrypted_pwd + random_value + self.user_domain_secret
        )

        return {
            "email": self.email,
            "pwd": encrypted_pwd,
            "random": random_value,
            "signature": signature,
            "userDomain": self.user_domain,
        }

    def headers(self, auth: bool = True) -> dict[str, str]:
        headers = {
            "appsystemtype": "ios",
            "appid": "584",
            "accept": "application/json",
            "appversion": "3.6.0",
            "accept-language": "en-US;q=1",
            "user-agent": "Landbook/3.6.0 (iPhone; iOS 26.1; Scale/3.00)",
            "x-q-language": "EN",
            "app-info": "[iPhone][26.1]",
        }

        if auth:
            headers["authorization"] = self.get_auth_header()

        return headers

    def login(self) -> None:
        url = f"{API_BASE}/v2/enduser/enduserapi/emailPwdLogin"

        headers = self.headers(auth=False)
        headers["content-type"] = "application/x-www-form-urlencoded"

        with httpx.Client(http2=True, timeout=20) as client:
            r = client.post(url, headers=headers, data=self.login_payload())
            r.raise_for_status()
            data = r.json()

        if data.get("code") != 200:
            raise OmniBreezeApiError(f"Login failed: {data}")

        token_data = data["data"]["accessToken"]
        self.access_token = token_data["token"]
        self.expiration_time = int(token_data["expirationTime"])

        uid = self.jwt_payload(self.access_token).get("uid")
        if uid:
            self.uid = uid

    def get_auth_header(self) -> str:
        now = int(time.time())

        if not self.access_token or now > self.expiration_time - 300:
            self.login()

        if not self.access_token:
            raise OmniBreezeApiError("No access token after login")

        return self.access_token

    def find_first_string_key(self, obj: Any, keys: list[str]) -> str | None:
        if isinstance(obj, dict):
            for key in keys:
                value = obj.get(key)
                if isinstance(value, str) and value:
                    return value

            for value in obj.values():
                found = self.find_first_string_key(value, keys)
                if found:
                    return found

        elif isinstance(obj, list):
            for item in obj:
                found = self.find_first_string_key(item, keys)
                if found:
                    return found

        return None

    def get_fid(self) -> str:
        if self.fid:
            return self.fid

        endpoints = [
            "/v2/family/enduserapi/getCurrentFamily",
            "/v2/family/enduserapi/getFamilyList",
        ]

        with httpx.Client(http2=True, timeout=15) as client:
            for endpoint in endpoints:
                r = client.get(f"{API_BASE}{endpoint}", headers=self.headers())
                r.raise_for_status()
                data = r.json()

                if data.get("code") != 200:
                    continue

                fid = self.find_first_string_key(data, ["fid", "familyId", "familyID"])
                if fid:
                    self.fid = fid
                    return fid

        raise OmniBreezeApiError("Could not autodetect family ID")

    def get_devices(self) -> list[OmniBreezeDevice]:
        params = {
            "fid": self.get_fid(),
            "isGroupDeviceShow": "1",
            "page": "1",
            "pageSize": "20",
        }

        with httpx.Client(http2=True, timeout=15) as client:
            r = client.get(
                f"{API_BASE}/v2/family/enduserapi/getCommonUsedDeviceList",
                headers=self.headers(),
                params=params,
            )
            r.raise_for_status()
            data = r.json()

        if data.get("code") != 200:
            raise OmniBreezeApiError(f"Device list failed: {data}")

        devices: list[OmniBreezeDevice] = []

        for item in (data.get("data") or {}).get("list") or []:
            device_key = item.get("deviceKey")
            product_key = item.get("productKey")

            if not device_key or not product_key:
                continue

            previous_state = {}
            if device_key in self.devices and self.devices[device_key].state:
                previous_state = dict(self.devices[device_key].state or {})

            device = OmniBreezeDevice(
                device_key=device_key,
                name=item.get("deviceName") or device_key,
                product_key=product_key,
                product_name=item.get("productName"),
                online=bool(item.get("onlineStatus")),
                state=previous_state,
            )

            self.devices[device_key] = device
            devices.append(device)

        return devices

    def parse_bool(self, value: Any) -> bool:
        return str(value).strip().lower() in ("true", "1", "yes", "on")

    def parse_int(self, value: Any, default: Any = None) -> Any:
        try:
            return int(value)
        except Exception:
            return default

    def get_business_attributes(self, device: OmniBreezeDevice) -> dict[str, Any]:
        params = {
            "dk": device.device_key,
            "pk": device.product_key,
        }

        with httpx.Client(http2=True, timeout=15) as client:
            r = client.get(
                f"{API_BASE}/v2/binding/enduserapi/getDeviceBusinessAttributes",
                headers=self.headers(),
                params=params,
            )
            r.raise_for_status()
            data = r.json()

        if data.get("code") != 200:
            raise OmniBreezeApiError(f"Business attributes failed: {data}")

        device_data = (data.get("data") or {}).get("deviceData") or {}
        tsl_items = (data.get("data") or {}).get("customizeTslInfo") or []

        attrs = {}
        for item in tsl_items:
            code = item.get("resourceCode")
            if code:
                attrs[code] = item.get("resourceValce")

        mode_value = self.parse_int(
            attrs.get("working_mode"),
            (device.state or {}).get("mode", 0),
        )

        state = {
            "online": device.online,
            "product_key": device.product_key,
            "product_name": device.product_name,
            "temperature": self.parse_int(attrs.get("temperature")),
            "power": "on" if self.parse_bool(attrs.get("switch")) else "off",
            "speed": self.parse_int(attrs.get("wind_speed"), 0),
            "oscillation": "on" if self.parse_bool(attrs.get("swing_wind")) else "off",
            "sound": "on" if self.parse_bool(attrs.get("sound")) else "off",
            "light": "on" if self.parse_bool(attrs.get("screen_display")) else "off",
            "countdown": self.parse_int(attrs.get("countdown"), 0),
            "mode": mode_value,
            "battery": device_data.get("battery"),
            "voltage": device_data.get("voltage"),
            "signal_strength": device_data.get("signalStrength"),
            "firmware": device_data.get("version"),
        }

        device.state = state
        return state

    def refresh_all(self) -> dict[str, OmniBreezeDevice]:
        devices = self.get_devices()

        for device in devices:
            try:
                self.get_business_attributes(device)
            except Exception as exc:
                device.state = device.state or {}
                device.state["error"] = str(exc)

        return self.devices

    def enc_remaining_length(self, length: int) -> bytes:
        out = bytearray()

        while True:
            digit = length % 128
            length //= 128

            if length > 0:
                digit |= 0x80

            out.append(digit)

            if length == 0:
                break

        return bytes(out)

    def utf8_field(self, text: str) -> bytes:
        data = text.encode("utf-8")
        return len(data).to_bytes(2, "big") + data

    def mqtt_connect_packet(self, client_id: str, password: str) -> bytes:
        variable_header = (
            self.utf8_field("MQTT")
            + bytes([0x04])
            + bytes([0x42])
            + (40).to_bytes(2, "big")
        )
        payload = self.utf8_field(client_id) + self.utf8_field(password)
        body = variable_header + payload
        return bytes([0x10]) + self.enc_remaining_length(len(body)) + body

    def mqtt_subscribe_packet(self, packet_id: int, topics: list[str]) -> bytes:
        body = packet_id.to_bytes(2, "big")

        for topic in topics:
            body += self.utf8_field(topic) + b"\x00"

        return bytes([0x82]) + self.enc_remaining_length(len(body)) + body

    def mqtt_publish_packet(self, packet_id: int, topic: str, payload: bytes) -> bytes:
        body = self.utf8_field(topic) + packet_id.to_bytes(2, "big") + payload
        return bytes([0x33]) + self.enc_remaining_length(len(body)) + body

    def build_payload(
        self,
        control_id: int,
        value: int | None = None,
        msg_type: int = 0x0013,
    ) -> bytes:
        seq = int(time.time() * 1000) & 0xFFFF
        body_without_checksum = (
            seq.to_bytes(2, "big")
            + msg_type.to_bytes(2, "big")
            + control_id.to_bytes(2, "big")
        )

        if value is not None:
            body_without_checksum += value.to_bytes(2, "big")

        checksum = sum(body_without_checksum) & 0xFF
        body = bytes([checksum]) + body_without_checksum

        return b"\xaa\xaa" + len(body).to_bytes(2, "big") + body

    def send_action(self, device: OmniBreezeDevice, action: str) -> None:
        if action.startswith("speed:"):
            speed = int(action.split(":", 1)[1])
            control_id = 0x001A
            value = speed
        else:
            if action not in ACTIONS:
                raise OmniBreezeApiError(f"Unknown action: {action}")
            control_id, value = ACTIONS[action]

        payload = self.build_payload(control_id, value)

        device_prefix = f"qd{device.product_key}{device.device_key}"
        publish_topic = f"q/1/d/{device_prefix}/bus"
        sub_topics = [
            f"q/2/d/{device_prefix}/ack_",
            f"q/2/d/{device_prefix}/bus",
            f"q/2/d/{device_prefix}/onl_",
        ]

        if not self.uid:
            self.get_auth_header()

        if not self.uid:
            raise OmniBreezeApiError("Could not autodetect UID")

        client_id = f"qu_{self.uid}_{int(time.time() * 1000)}"
        password = self.get_auth_header()

        ws = websocket.create_connection(
            MQTT_URL,
            subprotocols=["mqtt"],
            origin="https://iot-south.netprisma.us:8443",
            sslopt={"cert_reqs": ssl.CERT_REQUIRED},
            timeout=10,
        )

        try:
            ws.send_binary(self.mqtt_connect_packet(client_id, password))

            data = ws.recv()
            if isinstance(data, str):
                data = data.encode()

            if data != b"\x20\x02\x00\x00":
                raise OmniBreezeApiError(f"MQTT connect failed: {data.hex()}")

            ws.send_binary(self.mqtt_subscribe_packet(1, sub_topics))
            time.sleep(0.25)
            ws.send_binary(self.mqtt_publish_packet(8, publish_topic, payload))

            end = time.time() + 5
            while time.time() < end:
                try:
                    ws.settimeout(2)
                    data = ws.recv()
                    if isinstance(data, str):
                        data = data.encode()

                    if data and (data[0] >> 4) == 3:
                        # For MVP, assume command was accepted if we receive publish traffic.
                        break

                except (websocket.WebSocketTimeoutException, socket.timeout):
                    ws.send_binary(b"\xc0\x00")

        finally:
            try:
                ws.send_binary(b"\xe0\x00")
            except Exception:
                pass
            ws.close()
    def send_action_with_optional_mute(
        self,
        device: OmniBreezeDevice,
        action: str,
        auto_mute: bool = True,
    ) -> None:
        """Send a fan command, then optionally turn the fan beep/sound off.

        This keeps normal fan controls quiet after the first command.
        We intentionally do not auto-mute sound_off itself.
        """
        self.send_action(device, action)

        if auto_mute and action != "sound_off":
            time.sleep(0.35)
            self.send_action(device, "sound_off")
