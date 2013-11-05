#!/usr/bin/env python

"""
phase_space

Creates and saves phase spaces plots for each mode.
"""

from math import pi

import ROOT

from lc2pxx import (
    config,
    utilities,
    containers,
    ntuples,
    plotting,
    Ntuple
)

# TODO once this is in Urania, there's a service we can use to
# access particle data
# Particle masses in MeV/c^2
# These are, of course, subject to errors, but these are omitted here
# Source: 2012 PDG
# Lambda_c^+ (u d c)
LAMBDAC_MASS = 2286.46
# Proton (u u d)
PROTON_MASS = 938.27
# Charged kaon (u s-bar)
K_MASS = 493.68
# Charged pion (u d-bar)
PI_MASS = 139.57
# 3-tuples of the form (proton, h1, h2)
DAUGHTER_MASSES = {
    config.pKpi: (PROTON_MASS, K_MASS, PI_MASS),
    config.pKK: (PROTON_MASS, K_MASS, K_MASS),
    config.ppipi: (PROTON_MASS, PI_MASS, PI_MASS)
}

def phase_space(mode, polarity, year):
    """Create plots of the Lambda_c phase space.

    The 5D phase space is defined by the invariant mass of the charge-
    opposite daughter pairs and three angles. The initial paper describing
    the space by E791 is on arXiv as hep-ex/9912003.
    Patrick Spradlin has made similar plots, presented on 06/02/2013, at
    http://cern.ch/go/9zsg
    """
    n = ntuples.get_selected(mode, polarity, year)

    mother_M = LAMBDAC_MASS
    proton_M, h1_M, h2_M = DAUGHTER_MASSES[mode]
    # Dalitz plot limits on p.15 http://cern.ch/go/LSS7
    p_h1_M_lo = (proton_M + h1_M)*(proton_M + h1_M)
    p_h1_M_hi = (mother_M - h2_M)*(mother_M - h2_M)
    p_h2_M_lo = (proton_M + h2_M)*(proton_M + h2_M)
    p_h2_M_hi = (mother_M - h1_M)*(mother_M - h1_M)
    h1_h2_M_lo = (h1_M + h2_M)*(h1_M + h2_M)
    h1_h2_M_hi = (mother_M - proton_M)*(mother_M - proton_M)
    # Dalitz plot axis titles
    daughters_latex = config.daughters_latex[mode]
    p_h1_title = daughters_latex["proton"] + daughters_latex["h1"]
    p_h2_title = daughters_latex["proton"] + daughters_latex["h2"]
    h1_h2_title = daughters_latex["h1"] + daughters_latex["h2"]
    # Charge-opposite daughter pairs
    # Add padding to the limits as they are not perfectly valid for
    # baryonic mothers
    vars = {
        "p_h1_M": containers.HistoVar(
            "p_h1_M*p_h1_M",
            "m({0})^{{2}}".format(p_h1_title),
            0.95*p_h1_M_lo,
            1.1*p_h1_M_hi,
            "MeV/c^{2}",
            30
        ),
        "p_h2_M": containers.HistoVar(
            "p_h2_M*p_h2_M",
            "m({0})^{{2}}".format(p_h2_title),
            0.95*p_h2_M_lo,
            1.1*p_h2_M_hi,
            "MeV/c^{2}",
            30
        ),
        "h1_h2_M": containers.HistoVar(
            "h1_h2_M*h1_h2_M",
            "m({0})^{{2}}".format(h1_h2_title),
            0.95*h1_h2_M_lo,
            1.1*h1_h2_M_hi,
            "MeV/c^{2}",
            30
        ),
        # Phase space angles
        "proton_theta": containers.HistoVar(
            "proton_theta", "#theta_{p}", 0, pi
        ),
        "proton_phi": containers.HistoVar(
            "proton_phi", "#phi_{p}", -pi, pi
        ),
        "cos_h1_h2_phi": containers.HistoVar(
            "cos_h1_h2_phi", "cos #phi_{K^{+}K^{-}}", -1, 1
        )
    }

    ds = containers.DataStore(
        utilities.latex_mode(mode), n, "signal_sw"
    )
    output_dir = "{0}/phase_space".format(config.output_dir)
    output = ROOT.TFile("{0}/{1}.root".format(output_dir, n), "recreate")
    for var in vars:
        plotting.plot_variable(vars[var], [ds]).Write()
    # "Dalitz" plots
    c = plotting.plot_variable_2d(
        (vars["p_h1_M"], vars["h1_h2_M"]), ds
    )
    # Shift the palette axis up so it doesn't cover any x-axis exponents
    c.h.GetListOfFunctions().FindObject("palette").SetY1NDC(0.25)
    c.Write()
    c = plotting.plot_variable_2d(
        (vars["p_h2_M"], vars["h1_h2_M"]), ds
    )
    c.h.GetListOfFunctions().FindObject("palette").SetY1NDC(0.25)
    c.Write()
    c = plotting.plot_variable_2d(
        (vars["p_h1_M"], vars["p_h2_M"]), ds
    )
    c.h.GetListOfFunctions().FindObject("palette").SetY1NDC(0.25)
    c.Write()
    output.Close()


if __name__ == "__main__":
    # Stop canvases from popping
    ROOT.gROOT.SetBatch(True)
    for mode in config.modes:
        phase_space(mode, config.magboth, 2011)
