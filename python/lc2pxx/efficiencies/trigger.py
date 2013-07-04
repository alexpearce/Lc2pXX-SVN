from uncertainties import ufloat

from lc2pxx import config, ntuples, utilities

def efficiency(mode, polarity, year):
    """Return the efficiency of the TOS trigger chain.

    This could be done by exploiting the TIS/TOS relationship
        efficiency = TOS&&TIS/TOS,
    but the TIS efficiency is very poor, and so the yields from the pKK
    fit are unstable. Monte Carlo is used instead, where the trigger
    efficiency is simply the ratio
        No. of triggered candidates / No. of reconstructed candidates.
    Candidates are truth matched.
    """

    truth_matching = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"
    tos_selection = "({0}) && ({1})".format(
        truth_matching, config.trigger_requirements
    )

    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    num_pre = reco_ntuple.GetEntries()
    num_tos = reco_ntuple.GetEntries(tos_selection)

    return utilities.efficiency_from_yields(num_tos, num_pre)

