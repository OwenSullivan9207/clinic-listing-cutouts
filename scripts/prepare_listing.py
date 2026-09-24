from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare one clinic listing image")
    parser.add_argument("image", type=Path)
    parser.add_argument("--listing-id", required=True)
    parser.add_argument(
        "--appointment-state",
        choices=("scheduled", "rescheduled", "canceled"),
        default="scheduled",
    )
    parser.add_argument(
        "--service-url",
        default=os.environ.get("CUTOUT_SERVICE_URL", "http://127.0.0.1:8000"),
    )
    args = parser.parse_args()

    payload = {
        "listing_id": args.listing_id,
        "image_base64": base64.b64encode(args.image.read_bytes()).decode("ascii"),
        "filename": args.image.name,
        "appointment_state": args.appointment_state,
    }
    response = httpx.request(
        method="POST",
        url=f"{args.service_url.rstrip('/')}/listing-cutouts",
        json=payload,
        timeout=45.0,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()

