"""
config
Holds various constants the program depends on.
Mostly, this module is here to prevent a multitude of magic strings
littering other modules and scripts. It does make things quite a bit more
verbose, but I think it's worthwhile trade-off.
"""

import os

from lc2pxx.utilities import file_exists

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
pphi = "pphi"
modes = (pKpi, pKK, ppipi, pKSLL, pKSDD, pphi)

# Map modes to Monte Carlo event types
# http://cern.ch/go/Fkl8
mc_event_types = {
    pKpi: 15874000,
    pKK: 15674000,
    ppipi: 15674010,
    # This is a fake EventType, the decay file does not exist
    pphi: 15674001
}
# Types of Monte Carlo ntuple produced
mc_generated = "generated"
mc_cheated = "cheated"
mc_stripped = "stripped"
mc_types = (mc_generated, mc_cheated, mc_stripped)

# LaTeX strings
kp_latex = r"K^{+}"
km_latex = r"K^{-}"
pip_latex = r"\pi^{+}"
pim_latex = r"\pi^{-}"
ks_latex = r"K_{S}^{0}"
phi_latex = r"\phi"
proton_latex = r"p"
lambdac_latex = r"\Lambda_{c}^{+}"
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
    },
    pKSLL: {
        "proton": proton_latex,
        "h1": ks_latex,
        "h2": "(LL)"
    },
    pKSDD: {
        "proton": proton_latex,
        "h1": ks_latex,
        "h2": "(DD)"
    },
    pphi: {
        "proton": proton_latex,
        "h1": phi_latex,
        "h2": ""
    }
}
modes_latex = {}
for mode in modes:
    ds = [daughters_latex[mode][d] for d in daughters]
    modes_latex[mode] = "${0}$".format("".join(ds))
del daughters
# Units
mev = r"MeV"
mevc = r"MeV/$c$"
mevcsq = r"MeV/$c^{2}$"

# Magnet polarities
magup = "MagUp"
magdown = "MagDown"
magboth = "Combined"
polarities = (magup, magdown, magboth)

ntuple_name = "DVntuple"
metatree_name = "MetaTree"

# Years we have data for
years = (2011, 2012)
# Stripping versions for a given year
stripping_years = {
    2011: "20r1",
    2012: "20r0"
}

# If True, use ProbNN PID variables offline,
# else use DLL
use_probnn = True

# Important paths
_home_dir = _get_environment_var("AFS")
_work_dir = _get_environment_var("WORK")
_scratch_dir = _get_environment_var("SCRATCH")
work_data_dir = _work_dir + "/Lc2pXX"
scratch_data_dir = _scratch_dir + "/Lc2pXX"
project_dir = os.getcwd()
output_dir = project_dir + "/output"

use_scratch = file_exists(scratch_data_dir)
