from marketmesh import guardrails


def test_scan_detects_openai_key():
    findings = guardrails.scan_for_secrets("token " + "sk-" + "ABCDEFGHIJKLMNOP1234" + " here")
    assert findings


def test_scan_clean_text():
    assert guardrails.scan_for_secrets("a normal procurement justification") == []


def test_idempotency_key_stable():
    a = guardrails.idempotency_key("x", "y")
    b = guardrails.idempotency_key("x", "y")
    assert a == b and a.startswith("idem_")


def test_idempotency_store():
    store = guardrails.IdempotencyStore()
    assert store.get("k") is None
    store.put("k", "ord_1")
    assert store.get("k") == "ord_1"
