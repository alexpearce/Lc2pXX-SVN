from uncertainties import ufloat

from lc2pxx import config

def efficiency(mode, polarity, year):
    """Return the PID efficiency from PIDCalib.

    Instructions on how we run PIDCalib.
    """
    efficiencies_2011 = {
        config.pKpi: {
            config.magup: ufloat(0.40271, 0.00013),
            config.magdown: ufloat(0.40824, 0.00011)
        },
        config.pKK: {
            config.magup: ufloat(0.35087, 0.00007),
            config.magdown: ufloat(0.35466, 0.00006)
        },
        config.ppipi: {
            config.magup: ufloat(0.46807, 0.00010),
            config.magdown: ufloat(0.47014, 0.00009)
        }
    }

    efficiencies_2012 = {
        config.pKpi: {
            config.magup: ufloat(1.0, 1.0),
            config.magdown: ufloat(1.0, 1.0)
        },
        config.pKK: {
            config.magup: ufloat(1.0, 1.0),
            config.magdown: ufloat(1.0, 1.0)
        },
        config.ppipi: {
            config.magup: ufloat(1.0, 1.0),
            config.magdown: ufloat(1.0, 1.0)
        }
    }

    efficiencies = {
        2011: efficiencies_2011,
        2012: efficiencies_2012
    }

    # Add the MagBoth key as the average of up and down
    for y in config.years:
        for m in config.modes:
            effs = efficiencies[y][m]
            up = effs[config.magup]
            down = effs[config.magdown]
            effs[config.magboth] = (up + down)/2

    return efficiencies[year][mode][polarity]

