from uncertainties import ufloat

from lc2pxx import config, ntuples, utilities

def efficiency(mode, polarity, year):
    """Return the efficiency of the reconstruction algorithm.

    This efficiency represents the ratio
        No. of reconstructed candidates / No. of accepted candidates.
    It is calculated from Monte Carlo as the ratio of events which
    pass the generator level cut to those which are reconstructible, as
    determined using the mcMatch LoKi predicate. mcMatch searches MC
    truth information in *reconstructed* particles.
    The product of the acceptance and reconstruction efficiency, as
    calculated by this package, is equal to the ratio of accepted candidates
    to stripped candidates, so one may quote a combined "reconstruction and
    stripping" efficiency , or a combined "acceptance and reconstruction"
    efficiency.
    """
    acc_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_generated
    )
    acc_num = acc_ntuple.GetEntries()
    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    reco_num = reco_ntuple.GetEntries()

    return utilities.efficiency_from_yields(reco_num, acc_num)

