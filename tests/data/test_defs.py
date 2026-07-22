"""Round-trip and sync guards for the data-type definitions."""

import numpy as np
import pytest
from hypothesis import given, settings

from data.strategies import populated_measurement
from pypana.data.defs import VALID_DATA_TYPES, DataType, Normalization, Quantity
from pypana.data.measurement import Measurement

ALL_DATA_TYPES = [
    DataType(quantity=q, normalization=n) for q in Quantity for n in Normalization
]


class TestDataTypeRoundTrip:
    """`DataType` spelling and parsing are inverse operations."""

    @pytest.mark.parametrize("dt", ALL_DATA_TYPES)
    def test_str_parse_round_trip(self, dt: DataType) -> None:
        """`parse(str(dt))` reproduces the DataType."""
        assert DataType.parse(str(dt)) == dt

    @pytest.mark.parametrize("dt", ALL_DATA_TYPES)
    def test_spelling_is_listed(self, dt: DataType) -> None:
        """Every (quantity, normalization) spelling is a known data-type string."""
        assert str(dt) in VALID_DATA_TYPES

    def test_valid_data_types_in_sync(self) -> None:
        """`VALID_DATA_TYPES` is exactly the set of spellings — nothing stale or missing."""
        assert {str(dt) for dt in ALL_DATA_TYPES} == set(VALID_DATA_TYPES)


class TestDataTypeParse:
    """`parse` accepts the documented input forms and rejects the rest."""

    def test_parse_passthrough_data_type(self) -> None:
        """A DataType is returned unchanged (identity)."""
        dt = DataType(quantity=Quantity.VOLUME, normalization=Normalization.DLOG_DP)

        assert DataType.parse(dt) is dt

    def test_parse_bare_quantity(self) -> None:
        """A bare Quantity parses to the un-normalized DataType."""
        assert DataType.parse(Quantity.SURFACE) == DataType(
            quantity=Quantity.SURFACE, normalization=Normalization.NONE
        )

    @pytest.mark.parametrize("spelling", ["dN", "DN", " dn ", "N", "n"])
    def test_parse_case_and_prefix_insensitive(self, spelling: str) -> None:
        """Symbol case, surrounding space, and the leading 'd' are all optional."""
        assert DataType.parse(spelling) == DataType(
            quantity=Quantity.NUMBER, normalization=Normalization.NONE
        )

    def test_parse_unknown_raises(self) -> None:
        """An unknown spelling raises ValueError."""
        with pytest.raises(ValueError):
            DataType.parse("dX")


class TestNormalizationConversion:
    """Δ ↔ Δ/dlog d_p is a lossless conversion through the axis."""

    @settings(max_examples=20)
    @given(m=populated_measurement(seed="delta"))
    def test_delta_to_dlogdp_and_back(self, m: Measurement) -> None:
        """`delta_dlogdp * Δlog d_p` reproduces `delta`."""
        np.testing.assert_allclose(m["dN/dlogdp"] * m.delta_log_d_p, m["dN"])


class TestDerivationLockIn:
    """Cross-quantity derivation is intentionally not implemented yet."""

    @settings(max_examples=10)
    @given(m=populated_measurement(quantity=Quantity.NUMBER))
    def test_filter_missing_quantity_raises(self, m: Measurement) -> None:
        """Filtering to an unmeasured quantity would require derivation."""
        with pytest.raises(NotImplementedError):
            _ = m[Quantity.VOLUME]

    @settings(max_examples=10)
    @given(m=populated_measurement(quantity=Quantity.NUMBER))
    def test_value_missing_quantity_raises(self, m: Measurement) -> None:
        """Reading an unmeasured quantity's values would require derivation."""
        with pytest.raises(NotImplementedError):
            _ = m["dV"]
