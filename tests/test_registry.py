from marketmesh.vendor_registry import RegistrationError, VendorRegistry


def test_register_real_brand_gets_disclaimer():
    r = VendorRegistry()
    v = r.register_vendor({"id": "acme", "name": "Acme", "is_real_brand": True})
    assert v.disclaimer  # auto-populated illustrative-data disclaimer
    assert "Illustrative" in v.disclaimer


def test_register_dict_and_lookup():
    r = VendorRegistry()
    r.register_vendor(
        {
            "id": "acme",
            "name": "Acme",
            "products": [
                {"id": "p1", "vendor_id": "acme", "name": "P1", "capabilities": ["crm"]}
            ],
        }
    )
    assert len(r) == 1
    assert r.product("p1").name == "P1"
    assert r.vendor_name("acme") == "Acme"


def test_duplicate_sku_rejected():
    r = VendorRegistry()
    try:
        r.register_vendor(
            {
                "id": "acme",
                "name": "Acme",
                "products": [
                    {"id": "p1", "vendor_id": "acme", "name": "A"},
                    {"id": "p1", "vendor_id": "acme", "name": "B"},
                ],
            }
        )
        raise AssertionError("expected RegistrationError")
    except RegistrationError:
        pass


def test_missing_id_rejected():
    r = VendorRegistry()
    try:
        r.register_vendor({"name": "NoId"})
        raise AssertionError("expected RegistrationError")
    except (RegistrationError, KeyError):
        pass


def test_sku_vendor_id_normalised():
    r = VendorRegistry()
    r.register_vendor(
        {"id": "acme", "name": "Acme", "products": [{"id": "p1", "vendor_id": "wrong", "name": "P"}]}
    )
    assert r.product("p1").vendor_id == "acme"
