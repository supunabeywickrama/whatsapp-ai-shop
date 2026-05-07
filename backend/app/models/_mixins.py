import secrets


def cuid_pk() -> str:
    # Short, URL-safe, sortable-ish primary key.
    return "c" + secrets.token_hex(12)
