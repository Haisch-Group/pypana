"""Base exception definition for the pypana package.

This module provides the root Exception class from which all package-specific errors must inherit.
No further logic is implemented, but all pypana related errors can be caught with one type.
"""


class ParticleAnalysisError(Exception):
    """Base Exception for this package."""

    pass
