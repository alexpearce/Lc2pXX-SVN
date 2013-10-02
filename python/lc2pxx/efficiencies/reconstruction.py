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
    truth = "Lambdac_BKGCAT < 20 && Lambdab_BKGCAT < 60"
    acc_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_generated
    )
    acc_num = acc_ntuple.GetEntries()
    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    reco_num = reco_ntuple.GetEntries(truth)

    return utilities.efficiency_from_yields(reco_num, acc_num)


def efficiency_from_bk(mode, polarity, year):
    """Return the efficiency of the reconstruction.

    This is similar to the `efficiency` method, except rather than using
    the number of accepted events from the generator-level ntuple, it
    uses the number from the bookkeeping.
    This method is here as a placeholder until I fix the MC options, as
    they are not currently selecting all generated decays.
    """
    bk_numbers = {
        2011: {
            config.pKpi: {
                config.magup: 1007497,
                config.magdown: 1017497
            },
            config.pKK: {
                config.magup: 1002245,
                config.magdown: 1013743
            },
            config.ppipi: {
                config.magup: 1015499,
                config.magdown: 1018996
            }
        },
        2012: {
            config.pKpi: {
                config.magup: 0,
                config.magdown: 0
            },
            config.pKK: {
                config.magup: 0,
                config.magdown: 0
            },
            config.ppipi: {
                config.magup: 0,
                config.magdown: 0
            }
        }
    }

    for y in bk_numbers:
        for m in bk_numbers[y]:
            effs = bk_numbers[y][m]
            up = effs[config.magup]
            down = effs[config.magdown]
            bk_numbers[y][m][config.magboth] = up + down

    acc_num = bk_numbers[year][mode][polarity]
    truth = "Lambdac_BKGCAT < 20 && Lambdab_BKGCAT < 60"
    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    reco_num = reco_ntuple.GetEntries(truth)

    return utilities.efficiency_from_yields(reco_num, acc_num)

