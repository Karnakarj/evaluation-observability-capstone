"""System 1 perturbation driver (no system code changed).
Feeds recorded model responses to the real extract_with_retry and prints what it returns.
Run from the policy solution dir:  PYTHONPATH=. .venv/bin/python perturbation_driver.py
"""
from policy_extractor.retry import extract_with_retry
from tests.conftest import RecordedClient, load_policy_text, make_tool_use_message

CONF = {"policy_type": 0.95, "premium_amount": 0.95, "deductible": 0.95,
        "coverage_limit": 0.9, "endorsements": 0.9, "exclusions": 0.9}


def response(**override):
    body = {"policy_type": "auto", "premium_amount": 1500.0, "deductible": 500.0,
            "coverage_limit": 100000.0, "endorsements": [{"name": "Roadside", "limit": None}],
            "exclusions": ["Racing"], "confidence": dict(CONF)}
    body.update(override)
    return make_tool_use_message("extract_policy", body)


def run(label, responses):
    client = RecordedClient(responses)
    result = extract_with_retry(client=client, policy_id="POL-2025-001",
                                document_text=load_policy_text("POL-2025-001"), max_retries=3)
    print(f"== {label}")
    print(f"   result type : {type(result).__name__}")
    print(f"   API calls   : {client.call_count}")
    print(f"   record      : {result!r}")
    print()


run("A. UNPERTURBED - well-formed response", [response()])
run("B. PERTURBED (recoverable) - premium_amount=-1500.0, then corrected",
    [response(premium_amount=-1500.0), response()])
run("C. PERTURBED (futile) - required field endorsements blanked to null",
    [response(endorsements=None, confidence={**CONF, "endorsements": 0.2})] * 4)
