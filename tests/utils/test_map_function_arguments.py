import inspect

import pytest

from pactum._utils._map_function_arguments import map_function_arguments


def test_map_function_arguments():

    sig_0 = inspect.Signature()
    sig_1 = inspect.Signature(
        [inspect.Parameter(name="f", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    )
    sig_1p = inspect.Signature(
        [inspect.Parameter(name="f", kind=inspect.Parameter.POSITIONAL_ONLY)]
    )
    sig_1k = inspect.Signature(
        [inspect.Parameter(name="f", kind=inspect.Parameter.KEYWORD_ONLY)]
    )
    sig_1vp = inspect.Signature(
        [inspect.Parameter(name="f", kind=inspect.Parameter.VAR_POSITIONAL)]
    )
    sig_1vk = inspect.Signature(
        [inspect.Parameter(name="f", kind=inspect.Parameter.VAR_KEYWORD)]
    )
    sig_1p_1_1vp_1k_1vk = inspect.Signature(
        [
            inspect.Parameter(name="f", kind=inspect.Parameter.POSITIONAL_ONLY),
            inspect.Parameter(name="g", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(name="h", kind=inspect.Parameter.VAR_POSITIONAL),
            inspect.Parameter(name="i", kind=inspect.Parameter.KEYWORD_ONLY),
            inspect.Parameter(name="j", kind=inspect.Parameter.VAR_KEYWORD),
        ]
    )

    sig_1dp_1d_1vp_1k_1vk = inspect.Signature(
        [
            inspect.Parameter(
                name="f", kind=inspect.Parameter.POSITIONAL_ONLY, default=1
            ),
            inspect.Parameter(
                name="g", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, default=2
            ),
            inspect.Parameter(name="h", kind=inspect.Parameter.VAR_POSITIONAL),
            inspect.Parameter(name="i", kind=inspect.Parameter.KEYWORD_ONLY),
            inspect.Parameter(name="j", kind=inspect.Parameter.VAR_KEYWORD),
        ]
    )
    sig_1p_1d_1vp_1k_1vk = inspect.Signature(
        [
            inspect.Parameter(name="f", kind=inspect.Parameter.POSITIONAL_ONLY),
            inspect.Parameter(
                name="g", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, default=2
            ),
            inspect.Parameter(name="h", kind=inspect.Parameter.VAR_POSITIONAL),
            inspect.Parameter(name="i", kind=inspect.Parameter.KEYWORD_ONLY),
            inspect.Parameter(name="j", kind=inspect.Parameter.VAR_KEYWORD),
        ]
    )
    sig_1p_1_1vp_1dk_1vk = inspect.Signature(
        [
            inspect.Parameter(name="f", kind=inspect.Parameter.POSITIONAL_ONLY),
            inspect.Parameter(name="g", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(name="h", kind=inspect.Parameter.VAR_POSITIONAL),
            inspect.Parameter(name="i", kind=inspect.Parameter.KEYWORD_ONLY, default=4),
            inspect.Parameter(name="j", kind=inspect.Parameter.VAR_KEYWORD),
        ]
    )

    assert map_function_arguments(sig_0, tuple(), {}) == {}
    assert map_function_arguments(sig_1, (42,), {}) == {"f": 42}
    assert map_function_arguments(sig_1, tuple(), {"f": 42}) == {"f": 42}
    assert map_function_arguments(sig_1p, (42,), {}) == {"f": 42}
    assert map_function_arguments(sig_1k, tuple(), {"f": 42}) == {"f": 42}
    assert map_function_arguments(sig_1vp, tuple(), {}) == {"f": tuple()}
    assert map_function_arguments(sig_1vp, (42, 1, 2), {}) == {"f": (42, 1, 2)}
    assert map_function_arguments(sig_1vk, tuple(), {}) == {"f": {}}
    assert map_function_arguments(sig_1vk, tuple(), {"a": 1, "b": 2}) == {
        "f": {"a": 1, "b": 2}
    }
    assert map_function_arguments(sig_1p_1_1vp_1k_1vk, (1, 2, 3), {"i": 4, "a": 5}) == {
        "f": 1,
        "g": 2,
        "h": (3,),
        "i": 4,
        "j": {"a": 5},
    }
    assert map_function_arguments(
        sig_1p_1_1vp_1k_1vk, (1,), {"g": 2, "i": 3, "a": 4}
    ) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(
        sig_1dp_1d_1vp_1k_1vk, (1,), {"g": 2, "i": 3, "a": 4}
    ) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(
        sig_1dp_1d_1vp_1k_1vk, tuple(), {"g": 2, "i": 3, "a": 4}
    ) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(sig_1dp_1d_1vp_1k_1vk, tuple(), {"i": 3, "a": 4}) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(
        sig_1p_1d_1vp_1k_1vk, (1,), {"g": 2, "i": 3, "a": 4}
    ) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(sig_1p_1d_1vp_1k_1vk, (1,), {"i": 3, "a": 4}) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(
        sig_1p_1_1vp_1dk_1vk, (1,), {"g": 2, "i": 3, "a": 4}
    ) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 3,
        "j": {"a": 4},
    }
    assert map_function_arguments(sig_1p_1_1vp_1dk_1vk, (1,), {"g": 2, "a": 4}) == {
        "f": 1,
        "g": 2,
        "h": tuple(),
        "i": 4,
        "j": {"a": 4},
    }

    with pytest.raises(TypeError):
        map_function_arguments(sig_0, (1,), {})

    with pytest.raises(TypeError):
        map_function_arguments(sig_0, tuple(), {"a": 1})

    with pytest.raises(TypeError):
        map_function_arguments(sig_1, tuple(), {})

    with pytest.raises(TypeError):
        map_function_arguments(sig_1, (1, 2), {})

    with pytest.raises(TypeError):
        map_function_arguments(sig_1, (1,), {"f": 2})

    with pytest.raises(TypeError):
        map_function_arguments(sig_1, tuple(), {"f": 1, "g": 2})
