#!/usr/bin/env python

from math import fabs

import ROOT

# TODO only using utilities.random_str(), shouldn't need it
from lc2pxx import config, Lc2pXX, fitting, plotting, utilities

# TODO Urania packages have access to a particle DB, use that
PROTON_M = 938.27
KAON_M = 493.67
PION_M = 139.57
LAMBDA_C_M = 2286.49
D_S_M = 1968.47

def format_particle(particle, idx=0):
    """Formats the particle as a TeX string.

    Keyword arguments:
    particle -- One of p, K, pi, Lc, or Ds
    idx -- Charge of the Lc daughter, 0 or 2 is +ve, 1 is -ve
        (as in the ntuples, proton (0) is +ve, h1 (1) is -ve, h2 (2) is +ve)
    """
    charge = ["+", "-", "+"][idx]
    format_map = {
        "p" : "p",
        "K" : "K^{{{0}}}".format(charge),
        "pi" : "#pi^{{{0}}}".format(charge),
        "Lc" : "#Lambda_{c}^{+}",
        "Ds" : "D_{s}^{+}"
    }
    return format_map[particle]

def format_reflections(pre_daughters, post_daughters):
    """Given two lists of daughters, formats a string of the changes.

    E.g. for pre_daughters=["a", "b", "c"], post_daughters=["a", "c", "b"],
    this method returns "b -> c, c -> b"
    Both arguments should be of the same length
    Keyword arguments:
    pre_daughters -- List of pre-reflection Lc daughters
    post_daughters -- List of post-reflection Lc daughters
    """
    if len(pre_daughters) is not len(post_daughters):
        raise ValueError("len(original) != len(reflected)")
    reflection_strs = []
    for i in range(len(pre_daughters)):
        pre_daughter = pre_daughters[i]
        post_daughter = post_daughters[i]
        if pre_daughter != post_daughter:
            pre_formatted = format_particle(pre_daughter, i)
            post_formatted = format_particle(post_daughter, i)
            reflection_strs.append("{0} #rightarrow {1}".format(
                pre_formatted, post_formatted
            ))
    return ", ".join(reflection_strs)


def format_decay(mother, daughters, escape=False):
    """Return a LaTeX string of the decay mother -> daughters.

    Keyword arguments:
    mother -- String of the mother particle
    daughters -- List of strings of the daughter particles
    escape -- If not True, remove TLatex markup from string
    """
    decay_str = "{0} to {1}{2}{3}".format(
        format_particle(mother),
        *[
            format_particle(daughter, idx)
            for idx, daughter in enumerate(daughters)
        ]
    )
    if escape:
        decay_str = utilities.sanitise(decay_str)
    return decay_str

def reflections(mode, polarity, year):
    """Create reflection plots, i.e. wrong invariant mass hypotheses."""
    klass = getattr(Lc2pXX, "Lc2{0}".format(mode))
    n = klass("DecayTree", polarity, year)
    n.add("{0}/selected-{1}.root".format(config.output_dir, n))
    branches = ["Lambdac_M"]
    for p in ("proton", "h1", "h2"):
        for v in ("PX", "PY", "PZ", "PE"):
            branches.append("{0}_{1}".format(p, v))
    n.activate_branches(branches)

    # Map modes to daughters
    mode_daughters = {
        config.pKpi: ("p", "K", "pi"),
        config.pKK: ("p", "K", "K"),
        config.ppipi: ("p", "pi", "pi")
    }
    pre_daughters = mode_daughters[mode]
    # Map particles to their masses
    daughter_masses = {
        "p": PROTON_M,
        "K": KAON_M,
        "pi": PION_M
    }
    # Lambda_c^+ (udc), D_s^+ (cs)
    mother_masses = {
        "Lc": {
            "mass": LAMBDA_C_M,
            "mass_low": LAMBDA_C_M - 50,
            "mass_high": LAMBDA_C_M + 50
        },
        "Ds": {
            "mass": D_S_M,
            "mass_low": D_S_M - 50,
            "mass_high": D_S_M + 50
        }
    }
    # Lc mass window in which to select candidates to check
    lc_mass_window = 15.
    # Must follow the mode_daughters ordering convention,
    # e.g. the first particle will be swapped with the proton candidate
    mothers = {
        "Ds" : [
            # Ds to KKK
            ("K", "K", "K"),
            # Ds to KKpi
            ("K", "K", "pi"),
            ("pi", "K", "K"),
            ("K", "pi", "K"),
            # Ds to Kpipi
            ("K", "pi", "pi"),
            ("pi", "K", "pi"),
            ("pi", "pi", "K"),
            # Ds to pipipi
            ("pi", "pi", "pi")
        ],
        "Lc" : [
            # Lc to pKpi
            ("p", "K", "pi"),
            ("p", "pi", "K"),
            ("pi", "p", "K"),
            ("pi", "K", "p"),
            ("K", "p", "pi"),
            ("K", "pi", "p"),
            # Lc to pKK
            ("p", "K", "K"),
            ("K", "p", "K"),
            ("K", "K", "p"),
            # Lc to ppipi
            ("p", "pi", "pi"),
            ("pi", "p", "pi"),
            ("pi", "pi", "p")
        ]
    }

    histograms = []
    num_bins = 50
    units = "MeV/#font[12]{c^{2}}"
    for mother, decays in mothers.items():

        # Histogram variables shared by all decays of the mother
        limit_low = mother_masses[mother]["mass_low"]
        limit_high = mother_masses[mother]["mass_high"]
        bin_width = float(limit_high - limit_low)/num_bins
        y_axis_title = "Candidates / ({0} {1})".format(bin_width, units)

        mother_histograms = []
        for daughters in decays:
            decay_name = format_decay(mother, daughters, True)
            decay_title = format_decay(mother, daughters)
            histogram = ROOT.TH1F(
                decay_name,
                "{0} ({1})".format(
                    decay_title,
                    format_reflections(pre_daughters, daughters)
                ),
                num_bins, limit_low, limit_high
            )
            histogram.GetXaxis().SetTitle("m({0}) [{1}]".format(
                decay_title.split(" ")[-1], units
            ))
            histogram.GetYaxis().SetTitle(y_axis_title)
            mother_histograms.append(histogram)

        proton = ROOT.TLorentzVector(0, 0, 0, 0)
        h1 = ROOT.TLorentzVector(0, 0, 0, 0)
        h2 = ROOT.TLorentzVector(0, 0, 0, 0)

        entry = 0
        print "Filling {0} reflection histograms for {1}".format(
            mother, n
        )
        for entry in n:
            # Only plot candidates inside the Lc window
            if fabs(n.Lambdac_M - LAMBDA_C_M) > lc_mass_window:
                continue

            for idx, daughters in enumerate(decays):
                proton.SetXYZM(
                    n.val("proton_PX"),
                    n.val("proton_PY"),
                    n.val("proton_PZ"),
                    daughter_masses[daughters[0]]
                )
                h1.SetXYZM(
                    n.val("h1_PX"),
                    n.val("h1_PY"),
                    n.val("h1_PZ"),
                    daughter_masses[daughters[1]]
                )
                h2.SetXYZM(
                    n.val("h2_PX"),
                    n.val("h2_PY"),
                    n.val("h2_PZ"),
                    daughter_masses[daughters[2]]
                )
                mother_histograms[idx].Fill((proton + h1 + h2).M())

        histograms.append(mother_histograms)

    # TODO create pretty plots of these histograms
    # could store them in the same file...
    f = ROOT.TFile("{0}/reflections/reflections-{1}.root".format(
        config.output_dir, n
    ), "recreate")
    for mother_histograms in histograms:
        for h in mother_histograms:
                h.Write()
    f.Write()

    # Save the plots
    plotting.get_style().cd()
    for idx, key in enumerate(f.GetListOfKeys()):
        h = key.ReadObj()
        h_name = h.GetName()
        # Only save the interesting histograms
        if h.GetSumOfWeights() < 10: continue
        # Thanks to Tom Bird for his help here
        if h_name.startswith("d_s"):
            fn = ROOT.TF1(
                "func11",
                "gaus(0)+expo(3)",
                D_S_M - 30,
                D_S_M + 30
            )
            # Fix to the PDG mass and rough LHCb D_s resolution
            fn.FixParameter(1, D_S_M)
            fn.FixParameter(2, 3)
        elif h_name.startswith("lambda"):
            fn = ROOT.TF1(
                "func11",
                "gaus(0)+expo(3)",
                LAMBDA_C_M - 30,
                LAMBDA_C_M + 30
            )
            fn.FixParameter(1, LAMBDA_C_M)
            # Fix to the PDG mass and rough LHCb Lambda_c resolution
            fn.FixParameter(2, 5)
        # Parameters name, numbered from zero
        fn.SetParNames(
            "Gauss constant",
            "Gauss mean",
            "Gauss width",
            "Exp. constant",
            "Exp. slope"
        )
        fn.SetParameter(0, 20)
        # Don't allow negative yields
        fn.SetParLimits(0, 0, 1e5)
        fn.SetParameter(3, 5)
        fn.SetParameter(4, 1e-3)
        h.Fit(fn, "R")
        num_candidates = fn.GetParameter(0)
        err_candidates = fn.GetParError(0)
        print "{0} +/- {1}".format(num_candidates, err_candidates)
        c_name = "canvas_{0}".format(idx)
        # Plot to canvas
        c = ROOT.TCanvas(c_name, c_name, 600, 600)
        h.Draw("e1")
        h.GetXaxis().SetTitleOffset(1.2)
        h.GetYaxis().SetTitleOffset(1.2)
        c.Print("{0}/reflections/plots/{1}-{2}.pdf".format(
            config.output_dir, h_name, n
        ))

    f.Close()


if __name__ == "__main__":
    for mode in config.modes:
        reflections(mode, config.magboth, 2011)
