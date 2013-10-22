#!/usr/bin/env python

import ROOT
from uncertainties import ufloat

from lc2pxx import config, ntuples, fitting, utilities
from lc2pxx.efficiencies import (
    acceptance,
    reconstruction,
    tracking,
    trigger,
    stripping,
    offline,
    pid
)

def yields(mode, polarity, year):
    """Return the +/- 3 sigma yields from the (precomputed) fit.

    This uses the "selected" fit, which is generated by `setup_analysis.py`.
    """
    n = ntuples.get_selected(mode, polarity, year)
    f = ROOT.TFile("{0}/fits/selected-{1}.root".format(
        config.output_dir, n
    ))
    w = f.Get("{0}-workspace".format(n))
    yields = fitting.lambdac_mass.yields(w)
    f.Close()
    return yields


def efficiencies(mode, polarity, year):
    """Return a dictionary of detection and selection efficiencies."""
    return {
        "Acceptance": acceptance.efficiency(mode, polarity, year),
        "Reconstruction": reconstruction.efficiency(mode, polarity, year),
        "Tracking": tracking.efficiency_smeared(mode, polarity, year),
        "Stripping": stripping.efficiency(mode, polarity, year),
        "Trigger": trigger.efficiency_post_stripping(mode, polarity, year),
        "Offline": offline.efficiency_mc(mode, polarity, year),
        "PID": pid.efficiency(mode, polarity, year)
    }


def branching_fractions(polarity, year, plots=True, verbose=True):
    """Print the relative pKK and ppipi branching fractions, wrt pKpi."""
    # Dictionary of efficiencies, one key per eff in our chain,
    # and one key for total efficiency as the product of these
    effs = {}
    # Yield from the fit to candidates passing full selection
    raw_yields = {}
    # Yield divided by total efficiency
    prod_yields = {}
    modes = (config.pKpi, config.pKK, config.ppipi)
    for mode in modes:
        mode_effs = efficiencies(mode, polarity, year)
        # Holds the product of all the efficiencies
        total_eff = 1.
        for eff in mode_effs:
            total_eff *= mode_effs[eff]
        effs[mode] = mode_effs
        mode_effs["Total"] = total_eff
        # Index zero for the signal yield
        raw_yields[mode] = yields(mode, polarity, year)[0]
        prod_yields[mode] = raw_yields[mode]/effs[mode]["Total"]

    # PDG July 2012 measurement
    pKpi_abs = ufloat(5e-2, 1.3e-2)

    pKK_rel = prod_yields[config.pKK]/prod_yields[config.pKpi]
    pKK_abs = pKK_rel*pKpi_abs
    ppipi_rel = prod_yields[config.ppipi]/prod_yields[config.pKpi]
    ppipi_abs = ppipi_rel*pKpi_abs

    print
    print "== Measurements for {0} {1} == ".format(polarity, year)
    print
    # Print the individual efficiencies and yields if verbose
    if verbose:
        for mode in modes:
            mode_effs = effs[mode]
            print "-- Efficiencies for {0} --".format(mode)
            for eff in mode_effs:
                print "{0}: {1}".format(eff, mode_effs[eff])
            print
            print "-- Yields for {0} --".format(mode)
            print "Raw:", raw_yields[mode]
            print "Production:", prod_yields[mode]
            print
    print "-- Relative Branching Fractions (10^-2) --"
    print "pKK/pKpi:  ", 1e2*pKK_rel
    print "ppipi/pKpi:", 1e2*ppipi_rel
    print
    print "-- Absolute Branching Fractions (%) --"
    print "pKpi (PDG):", 1e2*pKpi_abs
    print "pKK:  ", 1e2*pKK_abs
    print "ppipi:", 1e2*ppipi_abs
    print

    return effs


if __name__ == "__main__":
    utilities.quiet_mode()
    effs = {}
    # Exclude the pKS mode; we're not interested in it here
    config.modes = (config.pKpi, config.pKK, config.ppipi)
    for polarity in config.polarities:
        branching_fractions(polarity, 2011)

