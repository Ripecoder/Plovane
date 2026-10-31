"""B03's handbook contracts, kept free of Flask so they can be tested alone.

The local API uses the §4.1 envelope. A recommendation arrives as §5.1, is
rewritten for the cloud as §8.1, and the cloud's §8.2 answer is trimmed back
to the §5.2 shape the GUI and CLI expect.

Errors use the §16.2 object. The cloud has no error format of its own (gap
G9), so it is mapped onto the same vocabulary here.
"""

from __future__ import annotations

import uuid
from typing import Any

# Input: none
# Output: str
# Processing: A fresh opaque request identifier for §8.1.
# Changed by: Nirmal
# Date: 2026-10-31
def new_request_id() -> str:
    return "req_" + uuid.uuid4().hex


# Input: data (Any)
# Output: dict[str, Any]
# Processing: A successful §4.1 envelope.
# Changed by: Nirmal
# Date: 2026-10-31
def ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data, "error": None}


# Input: code (str), message (str)
# Output: dict[str, Any]
# Processing: A failed §4.1 envelope.
# Changed by: Nirmal
# Date: 2026-10-31
def error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}


# Input: message (str), code (str)
# Output: ContractError
# Processing: A request that breaks a handbook contract, with its §16.2 code.
# Changed by: Nirmal
# Date: 2026-10-31
class ContractError(ValueError):
    """A request that breaks a contract. ``code`` is a §16.2 error code."""

    def __init__(self, message: str, code: str = "INVALID_REQUEST") -> None:
        super().__init__(message)
        self.code = code


# Input: raw (Any)
# Output: dict[str, Any]
# Processing: Validate and normalise a §5.1 recommendation request.
# Changed by: Nirmal
# Date: 2026-10-31
def validate_recommendation_request(raw: Any) -> dict[str, Any]:
    """Check §5.1 and return only the fields the contract defines."""
    if not isinstance(raw, dict):
        raise ContractError("the body must be a JSON object")

    if "project_id" not in raw:
        raise ContractError("project_id is required (a string or null)")
    project_id = raw.get("project_id")
    if project_id is not None and not isinstance(project_id, str):
        raise ContractError("project_id must be a string or null")

    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ContractError("description is required and must be a non-empty string")

    language = raw.get("language")
    if not isinstance(language, str) or not language.strip():
        raise ContractError("language is required and must be a non-empty string")

    tech_stack = raw.get("tech_stack")
    if not isinstance(tech_stack, list) or not all(isinstance(t, str) for t in tech_stack):
        raise ContractError("tech_stack is required and must be an array of strings")

    if "context_code" not in raw:
        raise ContractError("context_code is required (a string or null)")
    context_code = raw.get("context_code")
    if context_code is not None and not isinstance(context_code, str):
        raise ContractError("context_code must be a string or null")

    requested_count = raw.get("requested_count")
    if (not isinstance(requested_count, int) or isinstance(requested_count, bool)
            or requested_count <= 0):
        raise ContractError("requested_count is required and must be a positive integer")

    return {
        "project_id": project_id,
        "description": description,
        "language": language,
        "tech_stack": list(tech_stack),
        "context_code": context_code,
        "requested_count": requested_count,
    }


# Input: local (dict[str, Any]), request_id (str), user_id (str)
# Output: dict[str, Any]
# Processing: Turn a §5.1 request into the §8.1 cloud request.
# Changed by: Nirmal
# Date: 2026-10-31
def cloud_request(local: dict[str, Any], request_id: str, user_id: str) -> dict[str, Any]:
    return {"request_id": request_id, "user_id": user_id, **local}


# Input: cloud (Any)
# Output: dict[str, Any]
# Processing: Trim a §8.2 cloud answer to the §5.2 data object.
# Changed by: Nirmal
# Date: 2026-10-31
def recommendation_data(cloud: Any) -> dict[str, Any]:
    if not isinstance(cloud, dict):
        raise ContractError("the cloud response must be a JSON object", "INTERNAL_ERROR")
    recommendations = cloud.get("recommendations")
    if not isinstance(recommendations, list):
        raise ContractError("the cloud response has no recommendations array", "INTERNAL_ERROR")
    return {"recommendations": recommendations}


# Input: status (int)
# Output: str
# Processing: The §16.2 code that best matches an HTTP status.
# Changed by: Nirmal
# Date: 2026-10-31
def code_for_status(status: int) -> str:
    return {
        400: "INVALID_REQUEST",
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        413: "INVALID_REQUEST",
        422: "INVALID_REQUEST",
        429: "RATE_LIMITED",
    }.get(status, "INTERNAL_ERROR")


# Input: code (str)
# Output: int
# Processing: The HTTP status the local API should send for a §16.2 code.
# Changed by: Nirmal
# Date: 2026-10-31
def status_for_code(code: str) -> int:
    return {
        "INVALID_REQUEST": 400,
        "UNAUTHENTICATED": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404,
        "CONFLICT": 409,
        "RATE_LIMITED": 429,
        "INTERNAL_ERROR": 500,
        "UNAVAILABLE": 503,
    }.get(code, 500)
