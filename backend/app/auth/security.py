from hashlib import sha256
from hmac import digest
from secrets import token_urlsafe

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id. Se limita la memoria por operación para controlar concurrencia.
hasher = PasswordHasher(time_cost=3, memory_cost=19_456, parallelism=1)
dummy_hash = hasher.hash(token_urlsafe(32))


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def csrf_token(session_token: str) -> str:
    return digest(session_token.encode(), b"SRC:v1:csrf", "sha256").hex()
