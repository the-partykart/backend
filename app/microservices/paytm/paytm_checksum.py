import base64
import hashlib
import hmac
import json

def generate_checksum(payload: dict, merchant_key: str) -> str:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return base64.b64encode(
        hmac.new(
            merchant_key.encode(),
            data.encode(),
            hashlib.sha256
        ).digest()
    ).decode()

def verify_checksum(payload: dict, checksum: str, merchant_key: str) -> bool:
    return generate_checksum(payload, merchant_key) == checksum
