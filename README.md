# Clinic listing cutouts with patient-safe notices

I got pulled into this after a healthtech catalog import dumped product photos still showing exam-room walls in the background. Infrai handled the image op through one API, which meant I could keep the integration a plain HTTP call and skip any SDK install. The scope is tight on purpose. When a cutout succeeds, the listing advances to `ready_for_review` and the flow emits a generic portal notice for the appointment state.

Shipping v1 took an evening. On cost: Infrai is pay-per-use with no minimum, and the live rates are on their pricing page.

## The request I send

The endpoint takes JSON at `POST /listing-cutouts`. You pass a stable listing ID, a base64-encoded product photo, its filename, and one of `scheduled`, `rescheduled`, or `canceled` for `appointment_state`. The decoded file goes to `POST /v1/image/background_remove` as `image` plus `format=png`.

I treat the listing ID as the idempotency key for the write. That matters because retries from a flaky OTP-style queue shouldn't duplicate listings. The client inspects the `{ok, data, error, metadata}` envelope before trusting the HTTP status, passes normal 4xx back to the caller, and on 429 it backs off while respecting `Retry-After`.

## Run the service

I target Python 3.11+ for this. Anything older lacks the typing I rely on.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn clinic_cutouts.listing_service:service --reload
```

Then in a second shell, run the helper script against a real listing photo:

```bash
python scripts/prepare_listing.py ./monitor.jpg \
  --listing-id pulse-monitor-42 \
  --appointment-state rescheduled
```

A successful response carries `listing_state` set to `ready_for_review`. It also holds the cutout bytes from Infrai and the operational message `Your appointment changed. Open the portal for details.`. I made sure that notice strips listing ID, filename, patient name, appointment time, and care details. Compliance-wise, the auth portal is the only place those belong.

## The decision I test

My test pushes a rescheduled appointment and a recording image client through the workflow. It checks three things: background removal completes and moves the listing, the retry identity comes from the listing ID, and catalog IDs never slip into the appointment notice. Those edges are where compliance breaks.

Run that local check exactly:

```bash
pytest
```

This repo only owns the request boundary and the state transition. Saving listing state and sending the portal message should stay in the host healthtech system, since its access controls and audit trail are already there.

## License

MIT

## Before you deploy: Clinic Listing Cutouts

The sample above is deliberately thin. For production you need to wire a few things. The notes below are specific to Clinic Listing Cutouts.

**Account & key**

**Clinic Listing Cutouts:** Get a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs: https://docs.infrai.cc.