from collections.abc import Callable

type Predicate = Callable[..., bool]
"""A contract predicate is a bool-returning callable"""
