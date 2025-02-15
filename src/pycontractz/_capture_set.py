type CaptureSet = set[str] | dict[str, str]
"""A set of captured or cloned variables"""


def normalize_capture_set(capture: CaptureSet | None) -> dict[str, str]:
    """Makes sure the capture set is a dict"""

    match capture:
        case None:
            capture = {}
        case set():
            capture = {n: n for n in capture}
        case dict():
            pass
        case _:
            raise TypeError("Invalid capture set")
    return capture
