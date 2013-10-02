from uncertainties import ufloat

from lc2pxx import config, ntuples, utilities

def efficiency(mode, polarity, year):
    """Return the stripping efficiency.

    This efficiency represents the ratio
        No. of stripped candidates / No. of reconstructed candidates
    The MC ntuples are created with a modified version of the stripping
    lines that do not contain PID requirements. So the efficiency returned
    here is not the stripping efficiency in data, and the PID cuts applied
    in the collision stripping must be considered seperately.
    Candidates are truth matched.
    """
    truth_matching = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"

    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    stripped_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    num_reco = reco_ntuple.GetEntries(truth_matching)
    num_stripped = stripped_ntuple.GetEntries(truth_matching)

    return utilities.efficiency_from_yields(num_stripped, num_reco)


def efficiency_wrt_acceptance(mode, polarity, year):
    """Return the stripping efficiency.

    This efficiency represents the ratio
        No. of stripped candidates / No. of accepted candidates
    This is then similar to `efficiency`, but with respect to the number
    of generated signal decays, obtained from the bookkeeping.
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

    num_accepted = bk_numbers[year][mode][polarity]

    truth_matching = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"
    stripped_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    num_stripped = stripped_ntuple.GetEntries(truth_matching)

    return utilities.efficiency_from_yields(num_stripped, num_accepted)

