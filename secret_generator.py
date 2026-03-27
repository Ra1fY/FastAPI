import secrets
import string

secret = secrets.token_urlsafe(32)
print(secret)