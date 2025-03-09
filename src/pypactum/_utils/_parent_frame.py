from types import FrameType


def get_parent_frame(frame: FrameType | None) -> FrameType | None:
    """If `frame` is not None, returns its parent frame. Otherwise, returns None."""

    if frame is not None:
        return frame.f_back
    return frame
