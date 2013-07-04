"""
lc2pxx
This module provides helper methods for the analysis of Lambda_c baryons
decaying to the SCS modes pK+K- and ppi+pi- and the CF mode pK-pi+.
"""

import logging

__all__ = [
    "config",
    "Ntuple",
    "Lc2pXX",
    "ntuples",
    "utilities",
    "containers",
    "plotting",
    "fitting",
    "efficiencies"
]

logging.basicConfig(
    # Prints the logging level in blue, then the message
    format="\033[0;34m%(levelname)s\033[0m: %(message)s",
    # Uncomment for INFO level messages; defaults to WARNING and above
    # level=0
)

