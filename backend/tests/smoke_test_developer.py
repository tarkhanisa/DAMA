from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA developer readiness smoke test started.")

    client = TestClient(app)

    print("Checking GET /developer/endpoint-map...")
    endpoint_map_response = client.get("/developer/endpoint-map")
    assert endpoint_map_response.status_code == 200, endpoint_map_response.text
    endpoint_map = endpoint_map_response.json()
    assert endpoint_map["total_endpoints"] > 0
    paths = {endpoint["path"] for endpoint in endpoint_map["endpoints"]}
    assert "/dashboard/summary" in paths
    assert "/developer/endpoint-map" in paths
    assert "/projects" in paths
    print("GET /developer/endpoint-map OK.")

    print("Checking GET /developer/frontend-contract...")
    contract_response = client.get("/developer/frontend-contract")
    assert contract_response.status_code == 200, contract_response.text
    contract = contract_response.json()
    assert contract["name"] == "DAMA Frontend Contract"
    assert contract["backend_base_url"] == "http://127.0.0.1:8000"
    assert contract["endpoint_count"] == endpoint_map["total_endpoints"]
    assert contract["recommended_frontend_sections"]
    print("GET /developer/frontend-contract OK.")

    print("Checking GET /developer/runbook...")
    runbook_response = client.get("/developer/runbook")
    assert runbook_response.status_code == 200, runbook_response.text
    runbook = runbook_response.json()
    assert runbook["name"] == "DAMA Local Operator Runbook"
    assert runbook["core_checks"]
    assert runbook["safe_workflow_order"]
    print("GET /developer/runbook OK.")

    print("DAMA developer readiness smoke test passed.")


if __name__ == "__main__":
    main()
