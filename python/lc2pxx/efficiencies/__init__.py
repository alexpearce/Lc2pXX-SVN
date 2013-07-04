"""
efficiencies

Holds scripts for calculating efficiencies for Lc decay modes.
See the docs for each efficiency for their motivation and calculation.

Each script represents one type of efficiency. It is expected to implement
an `efficiency` function which takes a mode, polarity and year as arguments
and returns an uncertainties.ufloat of the efficiency for those arguments.
The returned efficiency should be fractional, e.g. a 50% efficiency is 0.5.
"""

__all__ = [
    "acceptance",
    "reconstruction",
    "tracking",
    "stripping",
    "trigger",
    "pid",
    "offline"
]
