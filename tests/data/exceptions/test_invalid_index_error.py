import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pypana.data.exceptions.invalid_index_error import InvalidIndexError


@settings(max_examples=10)
@given(st.lists(st.integers(), max_size=10, unique=True) | st.none())
def test_invalid_index_error(indices: list[int] | None) -> None:
    """Test that supplied indices appear in textual output."""
    with pytest.raises(InvalidIndexError) as excinfo:
        raise InvalidIndexError(invalid_indices=indices)

    error_message = str(excinfo.value)

    if not indices:
        return

    for index in indices:
        assert str(index) in error_message
