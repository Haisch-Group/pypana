from pypana.plots.utils import split_kwargs


def test_split_kwargs() -> None:
    kwargs = {
        "base_1234": "abc",
        "base_5": "def",
        "base_67": "ghi",
        "pool_a": "jkl",
        "pool_b": "mno",
        "tum_z": "pqr",
        "abc_": "stu",
    }

    base_kwargs, pool_kwargs, tum_kwargs, no_kwargs = split_kwargs(
        "base_", "pool_", "tum_", "no_", **kwargs
    )

    assert base_kwargs == {
        "1234": "abc",
        "5": "def",
        "67": "ghi",
    }

    assert pool_kwargs == {
        "a": "jkl",
        "b": "mno",
    }

    assert tum_kwargs == {
        "z": "pqr",
    }

    assert no_kwargs == {}
