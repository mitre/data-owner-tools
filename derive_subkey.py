import hmac
import hashlib


def derive_subkey(secret, context):
    if context not in ["individuals", "households"]:
        raise ValueError("Invalid subkey context: Use 'individuals' or 'households'")

    h = hmac.new(str.encode(secret), str.encode(context), hashlib.sha256)
    return h.hexdigest()
