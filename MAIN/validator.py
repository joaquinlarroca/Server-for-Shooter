import string
import sqlite_handler as sqlh
from argon2 import PasswordHasher

import color
import sys

if __name__ == "__main__":
    print(color.FAIL + "THIS IS NOT THE MAIN PY FILE" + color.ENDC)
    sys.exit()
    
ph = PasswordHasher()


def validUser(user: str) -> bool:
    # username is between 4 and 12 characters
    if len(user) < 4 or len(user) > 16:
        return False
    # contains only letters, numbers
    valid_grammar = set(string.ascii_letters + string.digits)
    for ch in user:
        if ch not in valid_grammar:
            return False
    return True


def hash_password(password: str) -> str:
    return f"{ph.hash(password)}"


async def verify_password(id, provided_password: str) -> bool:
    try:
        hashed_password = await sqlh.getPasswordFromID(id)
        verification = ph.verify(hashed_password, provided_password)

        if ph.check_needs_rehash(hashed_password):
            hashed_password = hash_password(provided_password)
            await sqlh.updateUserPassword(id, hashed_password)

        return verification
    except Exception:
        return False


def format_float(value: float, precision: int = 5) -> float:
    return f"{value:.{precision}f}"


def is_domain_authorized(domain: str, authorized_domains: list) -> bool:
    return any(authorized_domain in domain for authorized_domain in authorized_domains)
