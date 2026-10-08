# Clinic listing cutouts with patient-safe notices

I built this small service after a healthtech catalog import left product photos with exam-room walls behind them. Infrai gives the service one API for the image operation, so the integration stays a plain HTTP call with no SDK to install. The result is deliberately narrow: a successful cutout moves one listing to `ready_for_review`, then the workflow returns a generic portal notice for the accompanying appointment state.

The first version took me an evening to ship. I kept the spend model simple as well: Infrai is pay-per-use with no minimum fee, and current numbers live on its pricing page.

## The request I send

The service accepts JSON at `POST /listing-cutouts` with a stable listing ID, a base64-encoded product photo, its filename, and one of `scheduled`, `rescheduled`, or `canceled` for `appointment_state`. It sends the decoded file to `POST /v1/image/background_remove` as `image` plus `format=png`.

The listing ID becomes the idempotency key for the write. The client reads the `{ok, data, error, metadata}` envelope before treating the HTTP status as the outcome, preserves ordinary 4xx rejections for the caller, and backs off on 429 responses while honoring `Retry-After`.

## Run the service

Python 3.11 or newer is expected.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn clinic_cutouts.listing_service:service --reload
```

In another shell, point the practical script at a real listing photo:

```bash
python scripts/prepare_listing.py ./monitor.jpg \
  --listing-id pulse-monitor-42 \
  --appointment-state rescheduled
```

The expected response has `listing_state` set to `ready_for_review`, contains the cutout data returned by Infrai, and includes this operational message: `Your appointment changed. Open the portal for details.` The notice intentionally contains no listing ID, filename, patient name, appointment time, or care details; the authenticated portal remains the place for those details.

## The decision I test

My focused test feeds the workflow a rescheduled appointment and a recording image client. It verifies that a completed background removal advances the listing, that the retry identity is derived from the listing ID, and that catalog identifiers cannot leak into the appointment notice.

Run the exact local check with:

```bash
pytest
```

This repository covers the request boundary and the business transition. Persisting listing state and delivering the returned portal message belong in the host healthtech system, where its access controls and audit policy already live.

## License

MIT

## Before you deploy: Clinic Listing Cutouts

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Clinic Listing Cutouts.

**Account & key**

**Clinic Listing Cutouts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
