"""Classify yt-dlp errors into plain-language reasons with a fix.

yt-dlp failures reach users as raw tracebacks ("HTTP Error 403",
"Sign in to confirm you're not a bot"). The known signatures map to a
short reason that names the fix, stored in the attempt's ``last_error``
and shown in the UI and logs. Unknown errors pass through unchanged.
"""

import errno


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
            " it. Update yt-dlp. Check that a JavaScript runtime (Deno)"
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


# A write that the media folder refuses says nothing about the video. The
# download path reads this before it retries, so it does not burn through
# the other candidates, and the attempt names the folder and the fix.
_FOLDER_ERRNOS: dict[int, str] = {
    errno.EACCES: (
        "Trailarr cannot write to the folder '{folder}'. Check the owner"
        " and the permissions of the folder, and the PUID and PGID of the"
        " container."
    ),
    errno.EPERM: (
        "Trailarr cannot write to the folder '{folder}'. Check the owner"
        " and the permissions of the folder, and the PUID and PGID of the"
        " container."
    ),
    errno.EROFS: "The folder '{folder}' is on a read-only file system.",
    errno.ENOSPC: "The disk that holds '{folder}' is full.",
    errno.EDQUOT: "The disk that holds '{folder}' is full.",
}


def classify_folder_error(exc: BaseException) -> str | None:
    """The reason with the fix when the error is about the media folder.

    Args:
        exc: The exception a download raised.

    Returns:
        A sentence that names the folder and the fix, or None when the
        error is not a refused write, a read-only mount, or a full disk.
    """
    if not isinstance(exc, OSError) or exc.errno not in _FOLDER_ERRNOS:
        return None
    folder = str(exc.filename or exc.filename2 or "").strip() or "the media folder"
    return _FOLDER_ERRNOS[exc.errno].format(folder=folder)


def error_text(exc: BaseException) -> str:
    """The message of an exception followed by its notes.

    A yt-dlp failure keeps the tool's output in a note. The attempt record
    stores this text, and the signatures above match against it, so the
    notes have to be part of it.
    """
    text = str(exc) or type(exc).__name__
    notes = [n for n in getattr(exc, "__notes__", []) if n]
    return "\n".join([text, *notes]) if notes else text


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


# A video that cannot be read says nothing about whether yt-dlp and the
# network work: the video was removed, made private, or is region locked.
# The health test tells this apart from a real failure, because blaming a
# user's setup for someone else deleting a video sends them hunting for a
# problem they do not have.
_UNAVAILABLE_FRAGMENTS = (
    "video unavailable",
    "this video is unavailable",
    "video is private",
    "private video",
    "has been removed",
    "removed by the uploader",
    "no longer available",
    "this video is not available",
    # A deleted video also comes back as a plain 410 from the API.
    "http error 410",
    # YouTube words the geo-block two ways: "is not available in your
    # country" and "has not made this video available in your country".
    "available in your country",
    "unavailable in your country",
)


def is_video_unavailable(error_text: str | None) -> bool:
    """Whether the error is about one video rather than about yt-dlp.

    Args:
        error_text: The raw yt-dlp output or exception text.

    Returns:
        bool: True when the video could not be read, and everything else
            about the setup looks fine.
    """
    if not error_text:
        return False
    lowered = error_text.lower()
    return any(f in lowered for f in _UNAVAILABLE_FRAGMENTS)
