"""B05, the cloud Flask server in front of the B06 recommender.

    python -m backend.cloud_server.app        # 127.0.0.1:8500

Handbook §4.2 is established: HTTPS and JSON, operation-specific schemas.
The handbook gives the cloud no universal envelope (gap G9), so errors use
the §16.2 object as ``{"request_id", "error": {"code", "message"}}``, the
same shape ``ml/serving/service`` already sends.

    POST /v1/recommend   §8.1 in, §8.2 out; rate-limited per user_id
    GET  /healthz        liveness

Login and registration (§8.3) are not routed yet: the session mechanism is
still an open decision (OD-4), so this server forwards without requiring a
token. Do not deploy it public until that decision is made.
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from flask import Flask, jsonify, request

from backend.cloud_server.rate_limit import RateLimiter
from backend.cloud_server.upstream import HttpRecommender, Recommender, UpstreamError


# Input: request_id (Any), code (str), message (str)
# Output: dict[str, Any]
# Processing: The cloud error body used until §4.2 defines one (gap G9).
# Changed by: Nirmal
# Date: 2026-10-31
def error_body(request_id: Any, code: str, message: str) -> dict[str, Any]:
    return {"request_id": request_id if isinstance(request_id, str) else None,
            "error": {"code": code, "message": message}}


# Input: upstream (Recommender | None), limiter (RateLimiter | None)
# Output: Flask
# Processing: Build the cloud app, defaulting to the real B06 client.
# Changed by: Nirmal
# Date: 2026-10-31
def create_app(upstream: Recommender | None = None, limiter: RateLimiter | None = None) -> Flask:
    app = Flask("plovane-cloud-server")
    upstream_of = upstream or HttpRecommender(
        os.environ.get("PLOVANE_MODEL_URL", "http://127.0.0.1:8600")
    )
    limiter_of = limiter or RateLimiter()

    # Input: raw (dict[str, Any])
    # Output: str
    # Processing: Rate-limit on the user, falling back to the peer address.
    # Changed by: Nirmal
    # Date: 2026-10-31
    def caller_key(raw: dict[str, Any]) -> str:
        user_id = raw.get("user_id")
        if isinstance(user_id, str) and user_id:
            return user_id
        return request.remote_addr or "anonymous"

    # Input: none
    # Output: Response
    # Processing: Liveness; it does not call the recommender.
    # Changed by: Nirmal
    # Date: 2026-10-31
    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True})

    # Input: none
    # Output: Response
    # Processing: Rate-limit, then forward §8.1 and return §8.2 unchanged.
    # Changed by: Nirmal
    # Date: 2026-10-31
    @app.post("/v1/recommend")
    def recommend():
        raw = request.get_json(silent=True)
        if not isinstance(raw, dict):
            return jsonify(error_body(None, "INVALID_REQUEST",
                                      "send a JSON object with Content-Type: application/json")), 400
        if not limiter_of.allow(caller_key(raw)):
            return jsonify(error_body(raw.get("request_id"), "RATE_LIMITED",
                                      "too many requests; slow down")), 429
        try:
            reply = upstream_of.recommend(raw)
        except UpstreamError as exc:
            status = exc.status if exc.status in (400, 401, 403, 404, 409, 429, 503, 504) else 502
            return jsonify(error_body(raw.get("request_id"), exc.code, str(exc))), status
        return jsonify(reply)

    return app


# Input: argv (list[str] | None)
# Output: None
# Processing: Run the development server.
# Changed by: Nirmal
# Date: 2026-10-31
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plovane cloud server (development server)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8500)
    parser.add_argument("--model-url", default=os.environ.get("PLOVANE_MODEL_URL", "http://127.0.0.1:8600"),
                        help="base URL of the B06 recommender")
    args = parser.parse_args(argv)
    create_app(HttpRecommender(args.model_url)).run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
