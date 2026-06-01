"""All pypana exceptions in one place for easy imports."""

from pypana.data.exceptions.invalid_index_error import InvalidIndexError
from pypana.pana_error import IncompatibleArgumentError as IncompatibleArgumentError
from pypana.pana_error import ParticleAnalysisError

__all__ = [
    "ParticleAnalysisError",
    "InvalidIndexError",
    "IncompatibleArgumentError",
]
