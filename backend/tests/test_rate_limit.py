import pytest

from app.auth import rate_limit
from app.core.errors import ApiError


def test_account_ip_limits_and_expiration(monkeypatch):
    clock = [100]
    monkeypatch.setattr(rate_limit, "monotonic", lambda: clock[0])
    limiter = rate_limit.AuthRateLimiter()
    limiter.account_limit = 1
    limiter.ip_limit = 2
    limiter.check("login", "first@example.com", "ip-a")
    with pytest.raises(ApiError, match="Demasiados intentos"):
        limiter.check("login", "first@example.com", "ip-b")
    limiter.check("login", "second@example.com", "ip-a")
    with pytest.raises(ApiError, match="Demasiados intentos"):
        limiter.check("login", "third@example.com", "ip-a")
    clock[0] += limiter.window
    limiter.check("login", "first@example.com", "ip-a")
