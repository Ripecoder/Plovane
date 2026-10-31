# local_backend (B03): built, recommendation path

**Owner:** Nirmal. **Status:** built for the recommendation path; diagram and
project submission are not routed yet.

The Python process that runs on the user's machine. The desktop app (B01),
the CLI (B02) and the MCP interface (B04) talk only to it. It talks to the
cloud server for anything that needs the library or an account.

## Contracts it must follow

| Connection | Transport | Handbook |
|---|---|---|
| Desktop GUI ↔ B03 | HTTP on `127.0.0.1`, prefix `/api/v1/`, `{"ok", "data", "error"}` envelope | §4.1, §5 |
| CLI ↔ B03 | not finalized; reuses the §5 operation schemas | §6 |
| MCP ↔ B03 | `{"operation", "input"}` in, §4.1 envelope out | §7 |
| B03 ↔ cloud server | HTTPS, JSON: recommendation §8.1/§8.2, login and registration §8.3 | §4.2, §8 |

Operations the app needs (§5): recommendation request/response (§5.1,
§5.2), diagram request/response (§5.3, §5.4), project submission (§5.5).
Error codes come from §16.1.

## What is built

`app.py` serves the §4.1 envelope on `127.0.0.1:8701`:

| Route | Handbook |
|---|---|
| `GET /api/v1/health` | §4.1 |
| `POST /api/v1/recommendations` | §5.1 in, §8.1 to the cloud, §8.2 back, §5.2 out |

`contracts.py` holds the §5.1 validation and the §8.1/§5.2 mapping, with no
Flask import, so it can be tested alone. `cloud.py` is the HTTPS client.
Cloud errors are mapped onto the §16.2 vocabulary (closes G9 for this path).

```sh
python -m backend.local_backend.app                              # 127.0.0.1:8701
PLOVANE_CLOUD_URL=http://127.0.0.1:8600 python -m backend.local_backend.app   # straight to B06
```

Caller identity is a placeholder until the §8.3 session decision: the
`X-Plovane-User` header, then `PLOVANE_USER`, then `"local"`.

## What already exists to build on

- `backend/whiteboard/server.py` already serves `/api/v1/whiteboard/...` on
  127.0.0.1 in the §4.1 envelope. B03 can mount its Flask app, or proxy to it.
- `ml/serving/service/` is the B06 HTTP service, and `contract.py` there maps
  the §8.1 body onto it.

## Open decisions

- Whether B03 and the whiteboard API run as one process or two (currently two).
- **G8:** project submission and diagram requests wait for the cloud route to B09.
- The §8.3 session mechanism, which also settles the `user_id` source above.
