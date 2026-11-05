#!/usr/bin/env python3
"""Run the native collector and forward each normalized JSON event securely."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request


def send(url: str, agent_id: str, signing_key: str, body: bytes) -> None:
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    message = f"{timestamp}\n{nonce}\n{hashlib.sha256(body).hexdigest()}".encode()
    signature = hmac.new(bytes.fromhex(signing_key), message, hashlib.sha256).hexdigest()
    request = urllib.request.Request(url.rstrip("/") + "/api/v1/events", data=body, method="POST",
        headers={"Content-Type": "application/json", "X-Agent-Id": agent_id,
                 "X-Agent-Timestamp": timestamp, "X-Agent-Nonce": nonce,
                 "X-Agent-Signature": signature})
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 202:
            raise RuntimeError(f"backend returned {response.status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collector", required=True)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--signing-key", required=True, help="one-time signing key returned at enrollment")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    command = [args.collector] + (["--once"] if args.once else [])
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=sys.stderr, text=True, encoding="utf-8")
    assert process.stdout is not None
    for line in process.stdout:
        try:
            payload = json.loads(line)
            body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
            send(args.backend, args.agent_id, args.signing_key, body)
        except (ValueError, urllib.error.URLError, RuntimeError) as error:
            print(f"uploader: event rejected: {error}", file=sys.stderr)
    return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())

