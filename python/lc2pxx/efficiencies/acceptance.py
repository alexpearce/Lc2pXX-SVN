from uncertainties import ufloat

from lc2pxx import config

def efficiency(mode, polarity, year):
    """Return the generator-level efficiency from Monte Carlo logs.

    This efficiency represents the ratio
        No. passing generator level cuts / No. generated.
    The generator level cut is DaughtersInLHCb for pKK and ppipi, which
    asserts[1]:
        * Charged daughters fly within 10 and 400 mrad;
        * Neutral daughters fly within 5 and 400 mrad;
        * No cut on neutrinos or Lambda and K_s daughters; and
        * Only cut on photons from neutral pions or etas.
    The pKpi generator level cut is LHCbAcceptance, which asserts[1]:
        * Signal flight direction (Lambda_b) within 0 and 400 mrad.
    The pKpi generator cut is therefore looser, and so the acceptance
    efficiency is higher, but the reconstruction efficiency will be lower.
    The efficiency cannot be calculated from ntuples, only from Gauss logs
    produced during MC generation, hence they are hardcoded in to this file.
    The original logs may be obtained using production IDs[2][3]:

        Mode  | EventType | MagUp | MagDown
        ------------------------------------
        pKpi  | 15874000  | 25244 | 25252
        pKK   | 15674000  | 25242 | 25250
        ppipi | 15674010  | 25246 | 25248

    The HTML statistics pages, produced by the MCStatTools package, provide
    particle/anti-particle signal counters. Each efficiency below is the
    average of these two numbers, with the error as the sum in quadrature.
    The numbers below are taken from the statistics pages generated by
    the Charm WG MC liason[3].

    [1] - http://cern.ch/go/n6DX (P. Robbe, Gauss Generation slides)
    [2] - http://cern.ch/go/t9mH (Dirac requests monitor web page)
    [3] - http://cern.ch/go/6mLt (Build statistics HTML instructions)
    [3] - http://cern.ch/go/rCD6 (HTML generator statistics)
    """
    efficiencies_2011 = {
        config.pKpi: {
            config.magup: ufloat(0.3347, 0.000779),
            config.magdown: ufloat(0.3347, 0.000776)
        },
        config.pKK: {
            config.magup: ufloat(0.1946, 0.000498),
            config.magdown: ufloat(0.1930, 0.000495)
        },
        config.ppipi: {
            config.magup: ufloat(0.1691, 0.000439),
            config.magdown: ufloat(0.1691, 0.000440)
        }
    }
    for m in config.modes:
        effs = efficiencies_2011[m]
        up = effs[config.magup]
        down = effs[config.magdown]
        effs[config.magboth] = (up + down)/2

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

    return efficiencies[year][mode][polarity]

