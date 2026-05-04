"""All pypana exceptions in one place for easy imports."""

from pypana._pana_error import IncompatibleArgumentError as IncompatibleArgumentError
from pypana._pana_error import ParticleAnalysisError
from pypana.data.exceptions.invalid_index_error import InvalidIndexError

__all__ = [
    "ParticleAnalysisError",
    "InvalidIndexError",
    "IncompatibleArgumentError",
]
