"""OpenAPI spec export for ChatGPT GPT Actions and other AI assistants.

Generates a simplified OpenAPI 3.1 spec from the FastAPI app,
filtering to essential endpoints and adding API key auth.
"""

import copy
from typing import Any

from src.api.main import app

# Endpoints to include (prefix match)
INCLUDED_PREFIXES = [
    "/api/v1/ledgers",
]

# Endpoints to exclude even if they match includes
EXCLUDED_SUBSTRINGS = [
    "/health",
    "/mcp",
    "/tokens",
    "/channels",
    "/import",
    "/export",
    "/recurring",
    "/installments",
    "/dashboard",
    "/users",
    "/chat",
    "/tags",
    "/templates",
    "/utils",
]


def generate_gpt_actions_spec() -> dict[str, Any]:
    """Generate a simplified OpenAPI spec for ChatGPT GPT Actions.

    Filters the full FastAPI spec to essential accounting endpoints
    and adds Bearer token auth scheme.
    """
    full_spec = copy.deepcopy(app.openapi())

    filtered_paths: dict[str, Any] = {}
    for path, methods in full_spec.get("paths", {}).items():
        if not any(path.startswith(prefix) for prefix in INCLUDED_PREFIXES):
            continue
        if any(excluded in path for excluded in EXCLUDED_SUBSTRINGS):
            continue
        filtered_paths[path] = methods

    spec: dict[str, Any] = {
        "openapi": full_spec.get("openapi", "3.1.0"),
        "info": {
            "title": "LedgerOne Accounting API",
            "description": "Personal accounting API for AI assistant integration. "
            "Supports creating transactions, querying accounts, and managing ledgers.",
            "version": full_spec.get("info", {}).get("version", "1.0.0"),
        },
        "paths": filtered_paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API token created from LedgerOne settings page",
                }
            },
            # Preserve schemas referenced by the filtered endpoints
            "schemas": full_spec.get("components", {}).get("schemas", {}),
        },
        "security": [{"BearerAuth": []}],
    }

    return spec
