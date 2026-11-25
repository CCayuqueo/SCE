from collections import deque
from hashlib import sha256
from threading import Lock
from time import monotonic

from app.core.errors import ApiError


class AuthRateLimiter:
    """Ventana móvil de intentos por cuenta e IP para el proceso web de SRC."""

    window = 300
    max_events = 10_000
    account_limit = 10
    ip_limit = 50

    def __init__(self) -> None:
        self.lock = Lock()
        self.events: deque[tuple[float, str, str]] = deque()
        self.accounts: dict[str, int] = {}
        self.ips: dict[str, int] = {}

    def check(self, operation: str, email: str, ip: str) -> None:
        account = sha256(f"{operation}:{email}".encode()).hexdigest()
        ip = f"{operation}:{ip}"
        with self.lock:
            now = monotonic()
            while self.events and now - self.events[0][0] >= self.window:
                _, old_account, old_ip = self.events.popleft()
                for counts, key in ((self.accounts, old_account), (self.ips, old_ip)):
                    counts[key] -= 1
                    if not counts[key]:
                        del counts[key]

            account_count = self.accounts.get(account, 0)
            ip_count = self.ips.get(ip, 0)
            if (
                account_count >= self.account_limit
                or ip_count >= self.ip_limit
                or len(self.events) >= self.max_events
            ):
                raise ApiError(
                    429,
                    "AUTH_RATE_LIMITED",
                    "Demasiados intentos. Intenta más tarde.",
                    {"Retry-After": str(self.window)},
                )
            self.events.append((now, account, ip))
            self.accounts[account] = account_count + 1
            self.ips[ip] = ip_count + 1
