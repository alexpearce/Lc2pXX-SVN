"""
config
Holds various constants the program depends on.
Mostly, this module is here to prevent a multitude of magic strings
littering other modules and scripts. It does make things quite a bit more
verbose, but I think it's worthwhile trade-off.
"""

import os
import platform

# We include this here rather than in lc2pxx.utilities as it has
# no use outside of this module
def _get_environment_var(name):
    """Return environment variable name, or None if it doesn't exist."""
    var = os.environ.get(name)
    if var is None:
        log.warning("Could not retrieve environment variable " + name)
    return var


# Lambda_c decays modes of interest
pKpi = "pKpi"
pKK = "pKK"
ppipi = "ppipi"
pKSDD = "pKSDD"
pKSLL = "pKSLL"
modes = (pKpi, pKK, ppipi)

# Map modes to Monte Carlo event types
# http://cern.ch/go/Fkl8
mc_event_types = {
    pKpi: 15874000,
    pKK: 15674000,
    ppipi: 15674010
}
# Types of Monte Carlo ntuple produced
mc_generated = "generated"
mc_cheated = "cheated"
mc_stripped = "stripped"
mc_types = (mc_generated, mc_cheated, mc_stripped)

# TLatex strings
# The #font[122]{-} string makes the minus sign a better length
kp_latex = "K^{+}"
km_latex = "K^{#font[122]{-}}"
pip_latex = "#pi^{+}"
pim_latex = "#pi^{#font[122]{-}}"
proton_latex = "p"
lambdac_latex = "#Lambda_{c}^{+}"
daughters = ("proton", "h1", "h2")
daughters_latex = {
    pKpi: {
        "proton": proton_latex,
        "h1": km_latex,
        "h2": pip_latex
    },
    pKK: {
        "proton": proton_latex,
        "h1": km_latex,
        "h2": kp_latex
    },
    ppipi: {
        "proton": proton_latex,
        "h1": pim_latex,
        "h2": pip_latex
    }
}
modes_latex = {}
for mode in modes:
    ds = [daughters_latex[mode][d] for d in daughters]
    modes_latex[mode] = "#font[12]{{{0}}}".format("".join(ds))
del daughters

# Magnet polarities
magup = "MagUp"
magdown = "MagDown"
magboth = "Combined"
polarities = (magup, magdown, magboth)

# Default number of bins when plotting histograms
# This should be used very sparingly; generally histograms should have
# the number of bins carefully chosen
num_bins = 50

ntuple_name = "DVntuple"
metatree_name = "MetaTree"

# Years we have data for
years = (2011, 2012)
# Stripping versions for a given year
stripping_years = {
    2011: "20r1",
    2012: "20"
}

# Important paths
_home_dir = _get_environment_var("AFS")
_work_dir = _get_environment_var("WORK")
_scratch_dir = _get_environment_var("SCRATCH")
work_data_dir = _work_dir + "/Lc2pXX"
scratch_data_dir = _scratch_dir + "/Lc2pXX"
project_dir = os.getcwd()
output_dir = project_dir + "/output"

_hostname = platform.node()
use_scratch = _hostname.startswith("pclbral05")

# Cut strings
# Triggers
sep = ["_", ""][stripping_years[2011] == "17b"]
_trigger_l0 = "mu{0}L0MuonDecision_TOS".format(sep)
_trigger_hlt1 = "mu{0}Hlt1TrackMuonDecision_TOS".format(sep)
_trigger_hlt2 = "||".join([
    "Lambdab{0}Hlt2TopoMu2BodyBBDTDecision_TOS".format(sep),
    "Lambdab{0}Hlt2TopoMu3BodyBBDTDecision_TOS".format(sep),
    "Lambdab{0}Hlt2TopoMu4BodyBBDTDecision_TOS".format(sep),
])
trigger_requirements = "({0})&&({1})&&({2})".format(
    _trigger_l0, _trigger_hlt1, _trigger_hlt2
)
# Lc mass window
lc_m_low = 2220
lc_m_high = 2360
lc_m_window = "({0} < Lambdac_M) && (Lambdac_M < {1})".format(
    lc_m_low, lc_m_high
)
# Kinematic vetoes to match PID calibration samples
kinematic_vetoes = "&&".join([
    "2e3 < mu_P && mu_P < 1e5",
    "1.5 < mu_ETA && mu_ETA < 5",
    "2e3 < proton_P && proton_P < 1e5",
    "1.5 < proton_ETA && proton_ETA < 5",
    "2e3 < h1_P && h1_P < 1e5",
    "1.5 < h1_ETA && h1_ETA < 5",
    "2e3 < h2_P && h2_P < 1e5",
    "1.5 < h2_ETA && h2_ETA < 5"
])

