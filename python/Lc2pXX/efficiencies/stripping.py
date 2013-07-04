from uncertainties import ufloat

from lc2pxx import config, ntuples, utilities

def efficiency(mode, polarity, year):
    """Return the stripping efficiency.

    This efficiency represents the ratio
        No. of stripped candidates / No. of triggered candidates
    The MC ntuples are created with a modified version of the stripping
    lines that do not contain PID requirements. So the efficiency returned
    here is not the stripping efficiency in data, and the PID cuts applied
    in the collision stripping must be considered seperately.
    Candidates are truth matched.
    """

    truth_matching = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"
    tos_selection = "({0}) && ({1})".format(
        truth_matching, config.trigger_requirements
    )

    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    stripped_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    num_tos = reco_ntuple.GetEntries(tos_selection)
    num_stripped = stripped_ntuple.GetEntries(tos_selection)

    return utilities.efficiency_from_yields(num_stripped, num_tos)

