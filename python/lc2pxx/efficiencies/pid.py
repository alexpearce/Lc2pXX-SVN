from uncertainties import ufloat

from lc2pxx import config

def efficiency(mode, polarity, year):
    """Return the PID efficiency from PIDCalib.

    Instructions on how we run PIDCalib.
    """
    # With mcMatch ntuple
    efficiencies_2011_20r1 = {
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
        },
        config.pphi: {
            config.magup: ufloat(0.34985, 0.00012),
            config.magdown: ufloat(0.35816, 0.00010)
        }
    }
    # Without mcMatch ntuple
    # efficiencies_2011_20r1 = {
    #     config.pKpi: {
    #         config.magup: ufloat(0.41808, 0.00012),
    #         config.magdown: ufloat(0.42376, 0.00010)
    #     },
    #     config.pKK: {
    #         config.magup: ufloat(0.36190, 0.00007),
    #         config.magdown: ufloat(0.36487, 0.00006)
    #     },
    #     config.ppipi: {
    #         config.magup: ufloat(0.48830, 0.00009),
    #         config.magdown: ufloat(0.48895, 0.00008)
    #     },
    #     config.pphi: {
    #         config.magup: ufloat(0.35987, 0.00012),
    #         config.magdown: ufloat(0.36749, 0.00010)
    #     }
    # }
    # Stripping 17b with reco MC ntuple
    efficiencies_2011_17b = {
        config.pKpi: {
            config.magup: ufloat(0.38016, 0.00006),
            config.magdown: ufloat(0.38131, 0.00008)
        },
        config.pKK: {
            config.magup: ufloat(0.35378, 0.00012),
            config.magdown: ufloat(0.35893, 0.00017)
        },
        config.ppipi: {
            config.magup: ufloat(0.39228, 0.00014),
            config.magdown: ufloat(0.39182, 0.00015)
        },
        config.pphi: {
            config.magup: ufloat(0.35814, 0.00020),
            config.magdown: ufloat(0.36267, 0.00023)
        }
    }

    if config.stripping_years[2011] is "17b":
        efficiencies_2011 = efficiencies_2011_17b
    else:
        efficiencies_2011 = efficiencies_2011_20r1

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

    efficiencies_2012[config.pphi] = efficiencies_2012[config.pKK]

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

