"""Hiding a secret that the API has to mention but must not send."""

MASK = "****"
# Enough of the end to recognise which key is set, too little to use it.
_VISIBLE_TAIL = 4


def mask_secret(secret: str) -> str:
    """Give back a form of `secret` that is safe to send to a client.

    An empty secret stays empty, so a client can tell "not set" from "set".
    A short secret shows nothing, because the tail of it would be most of
    it. Anything longer shows its last four characters, which is enough to
    recognise the key without being enough to use it.

    Args:
        secret (str): The value to hide, such as an API key.

    Returns:
        str: The masked value.
    """
    if not secret:
        return ""
    if len(secret) <= _VISIBLE_TAIL * 2:
        return MASK
    return f"{MASK}{secret[-_VISIBLE_TAIL:]}"
