import inspect


def find_outer_stack_frame(func) -> inspect.FrameInfo | None:
    """Finds the calling stack frame"""

    unwrapped = inspect.unwrap(func)
    for frame in inspect.stack():
        if frame.frame.f_code.co_filename is unwrapped.__code__.co_filename:
            return frame
    return None
