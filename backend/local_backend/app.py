"""B03, the local Python backend the desktop app and CLI talk to.

    python -m backend.local_backend.app     # 127.0.0.1:8701

Handbook §4.1: HTTP on 127.0.0.1, JSON, prefix ``/api/v1/``, every response
is the ``{"ok", "data", "error"}`` envelope.

    GET  /api/v1/health           liveness
    POST /api/v1/recommendations  §5.1 in, §5.2 out, via the cloud's §8.1/§8.2

Implemented: the recommendation path. Diagram requests (§5.3/§5.4) and
project submission (§5.5) are not routed yet: their cloud route to B09 is
still gap G8.

Caller identity is a placeholder until the §8.3 session decision is made:
the ``X-Plovane-User`` header, then ``PLOVANE_USER``, then ``"local"``.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Protocol

from flask import Flask, jsonify, request

from backend.local_backend.cloud import CloudError, HttpCloudClient
from backend.local_backend.contracts import (
    ContractError,
    cloud_request,
    error,
    new_request_id,
    ok,
    recommendation_data,
    status_for_code,
    validate_recommendation_request,
)


# Input: body (dict[str, Any])
# Output: dict[str, Any]
# Processing: The cloud call B03 makes; injected in tests.
# Changed by: Nirmal
# Date: 2026-10-31
class Recommender(Protocol):
    def post_recommendation(self, body: dict[str, Any]) -> dict[str, Any]:
        ...


# Input: cloud (Recommender | None), user_id (str | None)
# Output: Flask
# Processing: Build the local API, defaulting to the real cloud client.
# Changed by: Nirmal
# Date: 2026-10-31
def create_app(cloud: Recommender | None = None, user_id: str | None = None) -> Flask:
    app = Flask("plovane-local-backend")
    cloud_of = cloud or HttpCloudClient(
        os.environ.get("PLOVANE_CLOUD_URL", "http://127.0.0.1:8500")
    )

    # Input: none
    # Output: str
    # Processing: Who the local backend acts for: header, then config, then "local".
    # Changed by: Nirmal
    # Date: 2026-10-31
    def caller_id() -> str:
        return (request.headers.get("X-Plovane-User") or user_id
                or os.environ.get("PLOVANE_USER") or "local")

    # Input: none
    # Output: Response
    # Processing: Liveness; it does not call the cloud.
    # Changed by: Nirmal
    # Date: 2026-10-31
    @app.get("/api/v1/health")
    def health():
        return jsonify(ok({"status": "ok"}))

    # Input: none
    # Output: Response
    # Processing: §5.1 -> §8.1 -> cloud -> §5.2, all inside the §4.1 envelope.
    # Changed by: Nirmal
    # Date: 2026-10-31
    @app.post("/api/v1/recommendations")
    def recommendations():
        try:
            local = validate_recommendation_request(request.get_json(silent=True))
            body = cloud_request(local, new_request_id(), caller_id())
            data = recommendation_data(cloud_of.post_recommendation(body))
        except ContractError as exc:
            return jsonify(error(exc.code, str(exc))), status_for_code(exc.code)
        except CloudError as exc:
            status = exc.status if exc.status in (400, 401, 403, 404, 409, 429, 503, 504) else 502
            return jsonify(error(exc.code, str(exc))), status
        return jsonify(ok(data))

    return app


# Input: argv (list[str] | None)
# Output: None
# Processing: Run the development server on the loopback interface only.
# Changed by: Nirmal
# Date: 2026-10-31
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plovane local backend (development server)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8701)
    parser.add_argument("--cloud", default=os.environ.get("PLOVANE_CLOUD_URL", "http://127.0.0.1:8500"),
                        help="base URL of the cloud server (B05)")
    args = parser.parse_args(argv)
    create_app(HttpCloudClient(args.cloud)).run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
