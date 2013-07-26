#!/usr/bin/env python

from math import fabs

import ROOT

from lc2pxx import config, ntuples, plotting, fitting, utilities

def fit_systematics(mode, polarity, year):
    """Evaluate the systematic uncertainty of the fit model.

    Each signal shape in fitting.lambdac_mass.shapes_sig is fitted with each
    background shape in fitting.lambdac_mass.shapes_bkg. The systematic
    uncertainty is taken as the largest fractional deviation from the
    nominal yield, which is the yield obtained from the nominal fit
    shapes, defined by Lc2pXX.shapes_postselection in the Lc2pXX child
    classes.
    The systematic uncertainty for each mode is printed. This script
    is a good candidate for having it's output saved to a log file.
    """
    n = ntuples.get_ntuple(mode, polarity, year)
    sel_path = "{0}/selected-{1}.root".format(config.output_dir, n)
    sel_n = n.__class__("DecayTree", n.polarity, n.year)
    sel_n.add(sel_path)

    w_name = "{0}-{1}-{2}-workspace"
    # Nominal shapes
    # Nom nom nom
    nom_shape_sig, nom_shape_bkg = n.shapes_postselection
    nom_w_name = w_name.format(n, nom_shape_sig, nom_shape_bkg)

    # Store the workspaces
    f = ROOT.TFile("{0}/fits/systematics-{1}.root".format(
        config.output_dir, n
    ), "recreate")
    # Try all combinations of signal and background shapes
    yields = {}
    for shape_sig in fitting.lambdac_mass.shapes_sig:
        for shape_bkg in fitting.lambdac_mass.shapes_bkg:
            w = ROOT.RooWorkspace(w_name.format(
                n, shape_sig, shape_bkg
            ))
            # Unbinned fit
            fitting.lambdac_mass.fit(
                sel_n, w, (shape_sig, shape_bkg), bins=0
            )
            yields[w.GetName()] = fitting.lambdac_mass.yields(w)
            c = plotting.plot_fit(
                w, [
                    ("total_pdf", "Fit"),
                    ("signal_pdf", "Signal"),
                    ("background_pdf", "Background")
                ],
                "Lambdac_M",
                bins=140
            )
            c.SetName(w.GetName().replace("workspace", "plot"))
            f.cd()
            w.Write()
            c.Write()
    f.Close()

    nom_yield_sig, nom_yield_bkg = yields[nom_w_name]
    max_diff = -999
    max_diff_name = ""
    for k in yields:
        y = yields[k][0]
        diff = fabs(nom_yield_sig.nominal_value - y.nominal_value)
        if diff > max_diff:
            max_diff = diff
            max_diff_name = k
        print k, yields[k][0]
    max_diff_shape_sig = max_diff_name.split("-")[4]
    max_diff_shape_bkg = max_diff_name.split("-")[5]

    print "Fit systematic"
    print "=============="
    print "Nominal yield ({0}, {1}): {2}".format(
        nom_shape_sig, nom_shape_bkg, nom_yield_sig
    )
    print "Maximum deviation ({0}, {1}): {2}".format(
        max_diff_shape_sig, max_diff_shape_bkg, max_diff
    )
    print "Uncertainty: {0}".format(100.*max_diff/nom_yield_sig)
    raw_input()


if __name__ == "__main__":
    # Enable batch mode -> no X windows
    ROOT.gROOT.SetBatch(True)
    for mode in config.modes:
        fit_systematics(mode, config.magboth, 2011)

