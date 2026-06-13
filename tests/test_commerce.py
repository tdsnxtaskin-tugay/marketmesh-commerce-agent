import pytest

from marketmesh import guardrails
from marketmesh.commerce import ApprovalError, CommerceEngine
from marketmesh.config import CommerceConfig
from marketmesh.models import Quote, QuoteLine


def _quote(annual=10000.0):
    q = Quote(currency="USD")
    q.lines.append(
        QuoteLine(
            sku_id="s1", sku_name="S1", vendor_id="v", vendor_name="V",
            seats=10, term_months=12, add_on_ids=[], list_annual_usd=annual,
            capabilities=["c1"],
        )
    )
    return q


def _engine(dry_run=True, cap=1_000_000.0):
    return CommerceEngine(CommerceConfig(dry_run=dry_run, max_transaction_usd=cap))


def test_happy_path_simulated_order():
    eng = _engine()
    q = _quote()
    req = eng.request_approval(q, "renewal for design team")
    token = eng.approve(req.id, "boss@example.com")
    order = eng.checkout(q, token, remaining_budget_usd=50000)
    assert order.status == "SIMULATED"
    assert order.approver == "boss@example.com"


def test_idempotent_replay_returns_same_order():
    eng = _engine()
    q = _quote()
    token = eng.approve(eng.request_approval(q, "ok").id, "boss@example.com")
    o1 = eng.checkout(q, token, remaining_budget_usd=50000)
    o2 = eng.checkout(q, token, remaining_budget_usd=50000)
    assert o1.id == o2.id  # no double charge


def test_spend_cap_blocks():
    eng = _engine(cap=5000.0)
    q = _quote(annual=10000.0)
    token = eng.approve(eng.request_approval(q, "ok").id, "boss@example.com")
    with pytest.raises(guardrails.GuardrailError):
        eng.checkout(q, token, remaining_budget_usd=1_000_000)


def test_budget_blocks():
    eng = _engine()
    q = _quote(annual=10000.0)
    token = eng.approve(eng.request_approval(q, "ok").id, "boss@example.com")
    with pytest.raises(guardrails.GuardrailError):
        eng.checkout(q, token, remaining_budget_usd=5000)


def test_token_must_match_quote():
    eng = _engine()
    q = _quote(annual=10000.0)
    token = eng.approve(eng.request_approval(q, "ok").id, "boss@example.com")
    tampered = _quote(annual=20000.0)  # cart changed after approval
    with pytest.raises(ApprovalError):
        eng.checkout(tampered, token, remaining_budget_usd=1_000_000)


def test_empty_approver_rejected():
    eng = _engine()
    q = _quote()
    req = eng.request_approval(q, "ok")
    with pytest.raises(ApprovalError):
        eng.approve(req.id, "   ")


def test_secret_in_justification_blocked():
    eng = _engine()
    q = _quote()
    with pytest.raises(guardrails.GuardrailError):
        eng.request_approval(q, "use key " + "sk-" + "abcdefghij1234567890" + " to pay")
