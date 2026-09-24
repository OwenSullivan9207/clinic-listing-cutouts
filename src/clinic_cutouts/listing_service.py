from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .infrai_images import InfraiError, InfraiImages
from .listing_workflow import CutoutRequest, CutoutResult, prepare_listing


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before starting the service")
    app.state.images = InfraiImages(api_key)
    yield
    await app.state.images.close()


service = FastAPI(title="Clinic listing cutouts", lifespan=lifespan)


@service.exception_handler(InfraiError)
async def handle_infrai_error(_: Request, exc: InfraiError):
    client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
    return JSONResponse(
        status_code=client_status,
        content={
            "detail": {
                "code": exc.code,
                "message": str(exc.details.get("message", "Request rejected")),
            }
        },
    )


@service.post("/listing-cutouts", response_model=CutoutResult)
async def create_listing_cutout(request: CutoutRequest) -> CutoutResult:
    return await prepare_listing(request, service.state.images)
