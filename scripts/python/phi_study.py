#!/usr/bin/env python

import ROOT
from uncertainties import ufloat

from lc2pxx import config, fitting, plotting, Lc2pXX, utilities
from lc2pxx.efficiencies import (
    acceptance,
    reconstruction,
    tracking,
    trigger,
    stripping,
    offline,
    pid
)

import branching_fractions

def phi_study(polarity, year):
    """Calculate and print the branching fraction for Lambda_c -> p phi.

    This uses an ntuple produced by the `phi_ntuple` method in
    `slim_ntuple.py`. If fits the Lambda_c mass spectrum of the decay
    and saves the workspace and plot.
    It then calculates the efficiencies from MC for the decay by applying
    a the phi requirement on the KK mass, using the passing candidates as
    the inputs to the efficiency methods.
    """
    # Fetch the ntuple, created using `phi_ntuple` in `slim_ntuple.py`
    n = Lc2pXX.Lc2pphi("DecayTree", polarity, year, mc=False)
    n.add("{0}/selected-pphi-{1}.root".format(
        config.output_dir, str(n).replace(config.pphi, config.pKK)
    ))

    # Unbinned fit
    w = ROOT.RooWorkspace("{0}-workspace".format(n))
    fitting.lambdac_mass.fit(
        n, w, n.shapes_postselection, bins=0
    )
    c = plotting.plot_fit(
        w, [
            ("total_pdf", "Fit"),
            ("signal_pdf", "Signal"),
            ("background_pdf", "Background")
        ],
        "Lambdac_M",
        bins=140
    )
    c.SetName(w.GetName().replace("workspace", "canvas"))
    utilities.save_to_file("{0}/fits/selected-{1}.root".format(
        config.output_dir, n
    ), [w, c])

    # Print the stats
    pphi_yields = fitting.lambdac_mass.yields(w)
    pphi_significance = utilities.significance(
        pphi_yields[0], pphi_yields[1]
    )
    print "Yields:", pphi_yields
    print "Significance:", pphi_significance

    # What follows in very similar in style to `branching_fractions.py`,
    # so check that out for a more in-depth explanation
    year = 2011
    m = config.pphi
    # We can proceed two ways - calculate the reco eff. wrt acc., then
    # stripping wrt reco, or just stripping wrt acc.
    pphi_effs = {
        "Acceptance": acceptance.efficiency(m, polarity, year),
        # "Reconstruction": reconstruction.efficiency(m, polarity, year),
        "Tracking": tracking.efficiency_smeared(m, polarity, year),
        # "Stripping": stripping.efficiency(m, polarity, year),
        "Stripping": stripping.efficiency_no_reco(m, polarity, year),
        "Trigger": trigger.efficiency_post_stripping(m, polarity, year),
        "Offline": offline.efficiency_mc(m, polarity, year),
        "PID": pid.efficiency(m, polarity, year)
    }

    # What follows here is very similar in style to `branching_fractions.py`
    # so check that out for a more in-depth explanation
    effs = {}
    raw_yields = {}
    prod_yields = {}
    modes = (config.pKpi, config.pphi)

    effs[config.pphi] = pphi_effs
    effs[config.pKpi] = branching_fractions.efficiencies(
        config.pKpi, polarity, year
    )
    # Add the "Total" key
    for mode in modes:
        mode_effs = effs[mode]
        total_eff = 1.
        for eff in mode_effs:
            total_eff *= mode_effs[eff]
        effs[mode]["Total"] = total_eff

    raw_yields[config.pphi] = pphi_yields[0]
    raw_yields[config.pKpi] = branching_fractions.yields(
        config.pKpi, polarity, year
    )[0]
    prod_yields[config.pphi] = raw_yields[config.pphi]/effs[config.pphi]["Total"]
    prod_yields[config.pKpi] = raw_yields[config.pKpi]/effs[config.pKpi]["Total"]

    # PDG July 2012 measurement
    pKpi_abs = ufloat(5e-2, 1.3e-2)

    pphi_rel = prod_yields[config.pphi]/prod_yields[config.pKpi]
    pphi_abs = pphi_rel*pKpi_abs

    print
    print "== Measurements for {0} {1} == ".format(polarity, year)
    print
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
    print "pphi/pKpi:  ", 1e2*pphi_rel
    print
    print "-- Absolute Branching Fractions (%) --"
    print "pKpi (PDG):", 1e2*pKpi_abs
    print "pphi:  ", 1e2*pphi_abs
    print


if __name__ == "__main__":
    utilities.quiet_mode()
    config.modes = (config.pKpi, config.pKK, config.pphi)
    for polarity in config.polarities:
        phi_study(polarity, 2011)

