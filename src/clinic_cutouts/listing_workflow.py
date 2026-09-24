from __future__ import annotations

import base64
import binascii
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Protocol


class ImageCutoutClient(Protocol):
    async def remove_background(
        self, image: bytes, filename: str, *, request_id: str
    ) -> dict[str, object]: ...


class AppointmentState(StrEnum):
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"
    CANCELED = "canceled"


@dataclass
class CutoutRequest:
    listing_id: str
    image_base64: str
    filename: str
    appointment_state: AppointmentState

    def __post_init__(self) -> None:
        if not 1 <= len(self.listing_id) <= 80:
            raise ValueError("listing_id must contain between 1 and 80 characters")
        if not 1 <= len(self.filename) <= 160:
            raise ValueError("filename must contain between 1 and 160 characters")
        if not self.image_base64:
            raise ValueError("image_base64 must not be empty")
        try:
            base64.b64decode(self.image_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("image_base64 must contain valid base64") from exc


@dataclass
class PortalNotice:
    title: str
    body: str
    channel: str = "patient_portal"

    def model_dump_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))


@dataclass
class CutoutResult:
    listing_id: str
    listing_state: str
    cutout: dict[str, object]
    appointment_notice: PortalNotice


def appointment_notice(state: AppointmentState) -> PortalNotice:
    messages = {
        AppointmentState.SCHEDULED: "Your appointment is scheduled. Open the portal for details.",
        AppointmentState.RESCHEDULED: "Your appointment changed. Open the portal for details.",
        AppointmentState.CANCELED: "Your appointment was canceled. Open the portal for next steps.",
    }
    return PortalNotice(title="Appointment update", body=messages[state])


async def prepare_listing(
    request: CutoutRequest, images: ImageCutoutClient
) -> CutoutResult:
    image = base64.b64decode(request.image_base64, validate=True)
    cutout = await images.remove_background(
        image,
        request.filename,
        request_id=f"listing-{request.listing_id}",
    )
    return CutoutResult(
        listing_id=request.listing_id,
        listing_state="ready_for_review",
        cutout=cutout,
        appointment_notice=appointment_notice(request.appointment_state),
    )
