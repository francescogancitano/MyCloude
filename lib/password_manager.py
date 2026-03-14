from argon2 import PasswordHasher 
from argon2.exceptions import VerifyMismatchError
from .logger import log

log = log()
ph = PasswordHasher()

def hashPassword(password_user):
    """hashes the given password using argon2."""
    return ph.hash(password_user)

def checkPassword(password_db, password_entered):
    """verifies if a password matches the hash from the database."""
    try:
        ph.verify(password_db, password_entered)
    except VerifyMismatchError: 
        # incorrect password
        log.error("the provided passwords do not match")
        return False

    # passwords match
    log.info("the provided passwords match")
    return True