from PIDPerfScripts.binning import (
    AddBinScheme,
    AddBinBoundary,
    AddUniformBins
)
from PIDPerfScripts.RunRangeFuncs import GetRICHPIDPartTypes

name = "Lc2pXX"

# These cuts should match the vetoes made to the signal samples
# Momentum in MeV
p = "P"
min_mom = 5e3
max_mom = 100e3
# Pseudorapidity
eta = "ETA"
min_eta = 2.
max_eta = 4.5
# Event track multiplicity
ntracks = "nTrack"
min_ntracks = 0
max_ntracks = 500

for t in GetRICHPIDPartTypes():
    AddBinScheme(t, p, name, min_mom, max_mom)
    # RICH1 K+/K- threshold
    AddBinBoundary(t, p, name, 9.3e3)
    # RICH2 K+/K- threshold
    AddBinBoundary(t, p, name, 15.6e3)
    AddUniformBins(t, p, name, 15, 19e3, 100e3)

    AddBinScheme(t, eta, name, min_eta, max_eta)
    AddUniformBins(t, eta, name, 4, min_eta, max_eta)

    AddBinScheme(t, ntracks, name, min_ntracks, max_ntracks)
    AddBinBoundary(t, ntracks, name, 50)
    AddBinBoundary(t, ntracks, name, 200)
    AddBinBoundary(t, ntracks, name, 300)

