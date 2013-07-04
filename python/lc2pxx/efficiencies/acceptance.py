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
    The original logs may be obtained using production IDs[2]:

        Mode  | EventType | MagUp     | MagDown
        -----------------------------------------
        pKpi  | 15874000  | 2524{4,5} | 2525{2,3}
        pKK   | 15674000  | 2524{2,3} | 2525{0,1}
        ppipi | 15674010  | 2524{6,7} | 2524{8,9)

    The HTML statistics pages, produced by the MCStatTools package, provide
    particle/anti-particle signal counters. Each efficiency below is the
    average of these two numbers, with the error as the sum in quadrature.

    [1] - http://cern.ch/go/n6DX (P. Robbe, Gauss Generation slides)
    [2] - http://cern.ch/go/t9mH (Dirac requests monitor web page)
    """
    # TODO Gauss logs for the S20r1 Sim08 MC aren't yet available
    # These values are from the old S17b Sim05a generation in
    #   /afs/cern.ch/user/s/sogilvy/public/genLevelEffs/SL
    efficiencies_2011 = {
        config.pKpi: {
            config.magup: ufloat(0.3329, 0.00198),
            config.magdown: ufloat(0.3333, 0.00198)
        },
        config.pKK: {
            config.magup: ufloat(0.1815, 0.00120),
            config.magdown: ufloat(0.1815, 0.00114)
        },
        config.ppipi: {
            config.magup: ufloat(0.1569, 0.00103),
            config.magdown: ufloat(0.1564, 0.00102)
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

    return efficiencies[year][mode][polarity]

