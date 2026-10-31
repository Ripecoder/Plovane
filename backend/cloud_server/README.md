# cloud_server (B05, B07): B05 partly built

**Owner:** Nirmal. **Status:** B05 rate limiting and §8.1 forwarding are
built; auth (§8.3) and B07 are not started.

The Flask server in the cloud. It has two jobs:

- **B05 rate limiter and auth.** It authenticates the local backend's
  requests and limits each user, then forwards them. Login and registration
  payloads are in §8.3.
- **B07 verified-library access.** It reads and writes library blocks in
  B08 for the recommender and for verification.

## Contracts it must follow

| Connection | Handbook | Status |
|---|---|---|
| B03 → B05 recommendation | §8.1 request, §8.2 response | proposed |
| B03 → B05 login, registration | §8.3 | proposed; the session mechanism needs review |
| B05 → B06 recommender | none in the handbook (**gap G2**) | `ml/serving/service/contract.py` proposes the mapping |
| B06 ↔ B07, B07 ↔ B08 | §5.2 code-block shape only (**gap G3**: no lookup payloads) | open |
| B05 → B09 project ingestion | route not specified (**gap G8**) | open |

## What is built

`app.py` runs on `127.0.0.1:8500`:

| Route | Handbook |
|---|---|
| `POST /v1/recommend` | §8.1 in, §8.2 out; forwarded unchanged to B06 |
| `GET /healthz` | liveness |

Errors use `{"request_id", "error": {"code", "message"}}` with the §16.2
vocabulary (gap G9). `rate_limit.py` is a token bucket per `user_id`
(`RATE_LIMITED`, 429). It is in memory, so run one B05 process or move the
counters to Redis before scaling out. `upstream.py` is the B06 client.

```sh
python -m backend.cloud_server.app                               # 127.0.0.1:8500
python -m ml.serving.service.app                                 # B06 on 127.0.0.1:8600
```

Auth is deliberately absent: the §8.3 session mechanism is an open decision
(OD-4), so do not expose this server publicly until it exists.

## What already exists to build on

- **B06 is built.** `POST /v1/recommend` takes §8.1 and returns §8.2, and
  `POST /v1/feedback` records accept and reject (`ml/serving/service/app.py`).
  B05 forwards to it after its rate check.
- `ml/serving/service/contract.py` is the accepted G2 mapping, so B05 passes
  the §8.1 body through unchanged instead of reshaping it.

## Suggested shape (still open)

Login and registration (§8.3): hash passwords with argon2 and issue session
tokens. Use one gunicorn worker per CPU for B05, and run B06 as its own
service, because each B06 worker holds about 2 GB of models.
