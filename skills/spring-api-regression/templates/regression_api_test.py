#!/usr/bin/env python3
"""Spring Web API regression runner template."""

from __future__ import annotations

import json
from typing import Any

import requests


TIMEOUT_SECONDS = 30

TEST_CONFIG: dict[str, Any] = {
    "base_url": "http://127.0.0.1:8080",
    "variables": {
        "token": "replace-with-real-token",
        "tenant_id": "demo-tenant",
        "user_id": 10001,
    },
    "default_headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{token}}",
        "X-Tenant-Id": "{{tenant_id}}",
    },
    "cases": [
        {
            "name": "get user detail",
            "method": "GET",
            "path": "/api/users/{{user_id}}",
            "headers": {},
            "query": {},
            "body": None,
            "expected_status": 200,
            "expected_contains": [
                "\"code\": 0",
                "\"id\": 10001",
            ],
        },
        {
            "name": "create order",
            "method": "POST",
            "path": "/api/orders",
            "headers": {},
            "query": {},
            "body": {
                "userId": "{{user_id}}",
                "skuCode": "SKU-001",
                "count": 1,
            },
            "expected_status": 200,
            "expected_contains": [
                "\"success\": true",
            ],
        },
    ],
}


def replace_placeholders(value: Any, variables: dict[str, Any]) -> Any:
    """Replace {{placeholder}} tokens in nested JSON-friendly data."""
    if isinstance(value, str):
        resolved = value
        for key, replacement in variables.items():
            resolved = resolved.replace(f"{{{{{key}}}}}", str(replacement))
        return resolved

    if isinstance(value, list):
        return [replace_placeholders(item, variables) for item in value]

    if isinstance(value, dict):
        return {
            key: replace_placeholders(item, variables)
            for key, item in value.items()
        }

    return value


def build_url(base_url: str, path: str) -> str:
    """Join the base URL and request path without duplicate slashes."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def pretty_json(value: Any) -> str:
    """Render JSON data in a stable and readable format."""
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def print_request_log(case_name: str, method: str, url: str, headers: dict[str, Any],
                      query: dict[str, Any], body: Any) -> None:
    """Print the final request payload after placeholder replacement."""
    print("========== CASE START ==========")
    print(f"CASE: {case_name}")
    print("========== CASE START ==========")
    print("🍀 REQUEST")
    print(f"METHOD: {method}")
    print(f"URL: {url}")
    print("HEADERS:")
    print(pretty_json(headers or {}))
    print("QUERY:")
    print(pretty_json(query or {}))
    print("BODY:")
    if body is None:
        print("null")
    else:
        print(pretty_json(body))


def print_response_log(response: requests.Response) -> None:
    """Print the response in a readable way for debugging and comparison."""
    print("🍀 RESPONSE")
    print(f"STATUS: {response.status_code}")
    print("HEADERS:")
    print(pretty_json(dict(response.headers)))
    print("BODY:")
    try:
        print(pretty_json(response.json()))
    except ValueError:
        print(response.text)
    print("=========== CASE END ===========")
    print()


def send_case(session: requests.Session, base_url: str, default_headers: dict[str, Any],
              global_variables: dict[str, Any], case: dict[str, Any]) -> requests.Response:
    """Prepare and send one case."""
    case_variables = {**global_variables, **case.get("variables", {})}
    method = str(case["method"]).upper()
    url = build_url(base_url, replace_placeholders(case["path"], case_variables))
    headers = replace_placeholders({**default_headers, **case.get("headers", {})}, case_variables)
    query = replace_placeholders(case.get("query", {}), case_variables)
    body = replace_placeholders(case.get("body"), case_variables)

    print_request_log(case["name"], method, url, headers, query, body)

    return session.request(
        method=method,
        url=url,
        headers=headers,
        params=query,
        json=body,
        timeout=TIMEOUT_SECONDS,
    )


def evaluate_case(case: dict[str, Any], response: requests.Response) -> tuple[bool, list[str]]:
    """Keep verification lightweight and readable by default."""
    reasons: list[str] = []
    passed = True

    expected_status = case.get("expected_status")
    if expected_status is not None and response.status_code != expected_status:
        passed = False
        reasons.append(
            f"expected status {expected_status}, actual {response.status_code}"
        )

    expected_contains = case.get("expected_contains", [])
    if expected_contains:
        response_text = response.text
        for expected_fragment in expected_contains:
            if expected_fragment not in response_text:
                passed = False
                reasons.append(f"missing response fragment: {expected_fragment}")

    return passed, reasons


def main() -> int:
    """Run all API regression cases from the inline test configuration."""
    config = TEST_CONFIG
    base_url = config["base_url"]
    default_headers = config.get("default_headers", {})
    global_variables = config.get("variables", {})
    cases = config.get("cases", [])

    success_count = 0
    with requests.Session() as session:
        for case in cases:
            response = send_case(
                session=session,
                base_url=base_url,
                default_headers=default_headers,
                global_variables=global_variables,
                case=case,
            )
            print_response_log(response)

            passed, reasons = evaluate_case(case, response)
            if passed:
                success_count += 1
                print(f"✅[PASS] {case['name']}")
            else:
                print(f"❌[FAIL] {case['name']}")
                for reason in reasons:
                    print(f"  - {reason}")
            print()

    total = len(cases)
    print("========== SUMMARY ==========")
    print(f"PASSED: {success_count}/{total}")
    return 0 if success_count == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
