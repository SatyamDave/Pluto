from apps.api.utils.redaction import redact_text, redact_dict


def test_redact_text_email_phone_card_address():
    s = "Contact me at john.doe@example.com or +1 (555) 123-4567, card 4242 4242 4242 4242, 1 Infinite Loop Rd"
    r = redact_text(s)
    assert "[REDACTED]" in r
    assert "example.com" not in r


def test_redact_dict_nested():
    d = {
        "email": "a@b.com",
        "phone": "+44 123 456 7890",
        "nested": {"addr": "123 Market St"},
        "list": ["4242-4242-4242-4242", {"deep": "c@d.io"}],
    }
    r = redact_dict(d)
    assert r["email"] == "[REDACTED]"
    assert r["nested"]["addr"] == "[REDACTED]"
    assert r["list"][0] == "[REDACTED]"
