"""Unit tests for OpenAPI spec generation for AI assistant integration.

Verifies the generated spec contains required endpoints, correct auth scheme,
and valid OpenAPI 3.1 format.
Per Constitution Principle II: Tests written BEFORE implementation.
"""


def _get_spec():
    """Import and generate the simplified OpenAPI spec."""
    from src.api.openapi_export import generate_gpt_actions_spec

    return generate_gpt_actions_spec()


class TestOpenAPISpecGeneration:
    """Tests for OpenAPI spec export for ChatGPT GPT Actions."""

    def test_spec_is_valid_openapi_31(self):
        spec = _get_spec()
        assert spec["openapi"].startswith("3.1")
        assert "info" in spec
        assert "paths" in spec

    def test_spec_info_section(self):
        spec = _get_spec()
        info = spec["info"]
        assert "title" in info
        assert "version" in info

    def test_spec_contains_create_transaction_endpoint(self):
        spec = _get_spec()
        paths = spec["paths"]
        # Should have a transaction creation endpoint
        tx_paths = [p for p in paths if "transaction" in p.lower()]
        assert len(tx_paths) > 0, "No transaction endpoint found"
        # At least one should support POST
        has_post = any("post" in paths[p] for p in tx_paths)
        assert has_post, "No POST endpoint for transactions"

    def test_spec_contains_list_transactions_endpoint(self):
        spec = _get_spec()
        paths = spec["paths"]
        tx_paths = [p for p in paths if "transaction" in p.lower()]
        # At least one should support GET
        has_get = any("get" in paths[p] for p in tx_paths)
        assert has_get, "No GET endpoint for transactions"

    def test_spec_contains_list_accounts_endpoint(self):
        spec = _get_spec()
        paths = spec["paths"]
        account_paths = [p for p in paths if "account" in p.lower()]
        assert len(account_paths) > 0, "No accounts endpoint found"

    def test_spec_contains_list_ledgers_endpoint(self):
        spec = _get_spec()
        paths = spec["paths"]
        ledger_paths = [p for p in paths if "ledger" in p.lower()]
        assert len(ledger_paths) > 0, "No ledgers endpoint found"

    def test_spec_has_auth_scheme(self):
        spec = _get_spec()
        # Should have securitySchemes defined
        components = spec.get("components", {})
        schemes = components.get("securitySchemes", {})
        assert len(schemes) > 0, "No security schemes defined"
        # Should have a Bearer or API key scheme
        has_bearer = any(
            s.get("type") == "http" and s.get("scheme") == "bearer" for s in schemes.values()
        )
        has_apikey = any(s.get("type") == "apiKey" for s in schemes.values())
        assert has_bearer or has_apikey, "No Bearer or API key auth scheme"

    def test_spec_has_global_security(self):
        spec = _get_spec()
        assert "security" in spec, "No global security requirement"
        assert len(spec["security"]) > 0

    def test_spec_does_not_include_internal_endpoints(self):
        """Internal endpoints like health, MCP, or admin should be excluded."""
        spec = _get_spec()
        paths = spec["paths"]
        for path in paths:
            assert "/health" not in path, "Health endpoint should be excluded"
            assert "/mcp" not in path, "MCP endpoint should be excluded"
            assert "/tokens" not in path, "Token management should be excluded"

    def test_spec_endpoints_have_descriptions(self):
        spec = _get_spec()
        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    assert "summary" in details or "description" in details, (
                        f"{method.upper()} {path} missing summary/description"
                    )
