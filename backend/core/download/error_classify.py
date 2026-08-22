"""Classify yt-dlp errors into plain-language reasons with a fix.

yt-dlp failures reach users as raw tracebacks ("HTTP Error 403",
"Sign in to confirm you're not a bot"). The known signatures map to a
short reason that names the fix, stored in the attempt's ``last_error``
and shown in the UI and logs. Unknown errors pass through unchanged.
"""

# (signature fragments, classified reason) — first match wins.
# Fragments are matched case-insensitively against the full error text.
_SIGNATURES: list[tuple[tuple[str, ...], str]] = [
    (
        (
            "sign in to confirm you're not a bot",
            "sign in to confirm your age",
            "please sign in",
            "login required",
            "use --cookies",
        ),
        (
            "YouTube requires a sign-in for this download. Set up a cookies"
            " file on Settings > Health."
        ),
    ),
    (
        ("http error 403", "http error 429", "too many requests"),
        (
            "YouTube is rate-limiting or blocking downloads from this"
            " address. Wait a while, or set up a cookies file on"
            " Settings > Health."
        ),
    ),
    (
        (
            "nsig extraction failed",
            "signature extraction failed",
            "unable to decode n-parameter",
            "some formats may be missing",
            "failed to extract any player response",
        ),
        (
            "YouTube changed its player and this yt-dlp version cannot read"
            " it. Update yt-dlp, and make sure a JavaScript runtime (Deno)"
            " is available."
        ),
    ),
    (
        ("requested format is not available",),
        (
            "No matching video format. This usually means yt-dlp has no"
            " JavaScript runtime (Deno) or is outdated."
        ),
    ),
    (
        (
            "age-restricted",
            "age restricted",
            "inappropriate for some users",
            "confirm your age",
        ),
        (
            "The video is age-restricted. Set up a cookies file on"
            " Settings > Health to download it."
        ),
    ),
    (
        (
            "video unavailable",
            "this video is not available",
            "private video",
            "video has been removed",
            "http error 410",
            "removed by the uploader",
        ),
        (
            "The video is unavailable (removed, private, or region-locked)."
            " A search will pick a different video on the next run."
        ),
    ),
    (
        (
            "unable to download webpage",
            "network is unreachable",
            "temporary failure in name resolution",
            "connection refused",
        ),
        (
            "Trailarr could not reach YouTube. Check the network and DNS of"
            " the container."
        ),
    ),
]


def classify_ytdlp_error(error_text: str | None) -> str | None:
    """Return the plain-language reason for a known yt-dlp error.

    Args:
        error_text: The raw yt-dlp output or exception text.

    Returns:
        The classified reason, or None when no signature matches.
    """
    if not error_text:
        return None
    lowered = error_text.lower()
    for fragments, reason in _SIGNATURES:
        if any(fragment in lowered for fragment in fragments):
            return reason
    return None


def classified_error(error_text: str) -> str:
    """Classified reason followed by the raw error's first meaningful line.

    Used when storing ``last_error``: the user sees the reason first,
    and the raw line stays available for bug reports.
    """
    reason = classify_ytdlp_error(error_text)
    if reason is None:
        return error_text
    lines = [line.strip() for line in error_text.splitlines() if line.strip()]
    raw = lines[-1] if lines else ""
    return f"{reason} [{raw}]" if raw else reason
