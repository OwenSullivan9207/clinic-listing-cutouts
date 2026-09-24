import asyncio
import base64

from clinic_cutouts.listing_workflow import (
    AppointmentState,
    CutoutRequest,
    prepare_listing,
)


class RecordingImages:
    def __init__(self) -> None:
        self.request_id = ""

    async def remove_background(
        self, image: bytes, filename: str, *, request_id: str
    ) -> dict[str, object]:
        assert image == b"clinic-product-photo"
        assert filename == "monitor.jpg"
        self.request_id = request_id
        return {"id": "cutout_123", "format": "png"}


def test_completed_cutout_advances_listing_and_keeps_notice_patient_safe() -> None:
    images = RecordingImages()
    request = CutoutRequest(
        listing_id="pulse-monitor-42",
        image_base64=base64.b64encode(b"clinic-product-photo").decode("ascii"),
        filename="monitor.jpg",
        appointment_state=AppointmentState.RESCHEDULED,
    )

    result = asyncio.run(prepare_listing(request, images))

    assert result.listing_state == "ready_for_review"
    assert result.cutout == {"id": "cutout_123", "format": "png"}
    assert images.request_id == "listing-pulse-monitor-42"
    assert result.appointment_notice.body == (
        "Your appointment changed. Open the portal for details."
    )
    serialized_notice = result.appointment_notice.model_dump_json()
    assert "pulse-monitor-42" not in serialized_notice
    assert "monitor.jpg" not in serialized_notice
