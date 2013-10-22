#!/usr/bin/env python

"""
cut_optimiser

A CROP clone in Python.
"""

from math import fabs, sqrt

import ROOT
import numpy as np
from uncertainties import ufloat

from lc2pxx import config, utilities, ntuples

class Cut:
    def __init__(self, variable, min, max, step):
        """Initialise an instance of the Cut class

        Keyword arguments:
        variable -- String of the variable to cut on
        min -- Minimum value to select candidates
        max -- Maximum value to select candidates
        step -- Amount to vary cut value by when optimising
        """
        # TODO if we want to implement a >/< choice, just add
        # an instance var here, then use it when necessary
        self.variable = variable
        self.min = min
        self.max = max
        self.step = step
        self.optimum_cut = min

    def __str__(self):
        """Pretty print the Cut instance."""
        return "{0} <= {1} < {2}, step size {3}, optimum {4}".format(
            self.min,
            self.variable,
            self.max,
            self.step,
            self.optimum_cut
        )


def get_yields(ntuple, variable, selection):
    """Return the yield of a selected ntuple.

    This is useful when the selection string contains a weighting
        selection="weight*(a < 10)"
    The yield returned is then the sum of the weights in the histogram, and
    the error on that yield is the sqrt of sum of the squares.
    Keyword arguments:
    ntuple -- Lc2pXX instance
    variable -- String of the variable in ntuple to be plotted
    selection -- String of the selection to apply to the ntuple
    """
    # TODO this is the bottle neck, takes just under 1s to run Draw
    tmp_name = utilities.random_str()
    ntuple.Draw("{0}>>{1}".format(selection, tmp_name), selection)
    tmp = ROOT.gPad.GetPrimitive(tmp_name)
    sum = tmp.GetSumOfWeights()
    sum_err = sqrt(tmp.GetSumw2().GetSum())
    tmp.Delete()
    return ufloat(sum, sum_err)


def ensemble_fom(ntuple, cuts, sig_pre, bkg_pre):
    """Return the FoM for the ntuple selected by the optimum cuts.

    Keyword arguments:
    ntuple -- Lc2pXX instance
    cuts -- List of Cut instances, cut value used is Cut.optimum_cut
    sig_pre -- Signal candidate preselection
    bkg_pre -- Background candidate preselection
    """
    cuts_selection = "&&".join([
        "({0} > {1})".format(
            cut.variable, cut.optimum_cut
        ) for cut in cuts
    ])
    sig_selection = "({0})*({1})".format(sig_pre, cuts_selection)
    bkg_selection = "({0})*({1})".format(bkg_pre, cuts_selection)
    # Dummy var to plot histos with
    plot_var = cuts[0].variable
    sig_yield = get_yields(ntuple, plot_var, sig_selection)
    bkg_yield = get_yields(ntuple, plot_var, bkg_selection)
    fom = utilities.significance(sig_yield, bkg_yield)
    return fom


def create_plots(variable, cut_info):
    """Create a set of signal vs. background efficiency plots.

    Specifically, the following plots are created:
        * Variable vs. signal efficiency
        * Variables vs. background rejection efficiency
        * Variable vs. the product of the above
        * Signal efficiency vs. background rejection efficiency
    These are plotted on one canvas, which is returned.
    Keyword arguments:
    var -- String of the variable name
    var_cut_info: A dictionary of cuts on var pointing to the following:
        yields: 2-tuple of signal and background yields
        sig_eff: Signal efficiency
        bkg_eff: Background efficiency
        bkg_rej: 1 - bkg_eff
        fom: Figure of merit
    Each quantity is given as a ufloat
    """

    # List of cut values
    # Sorted as Python dictionaries aren't ordered by insertion
    cut_vals = np.sort(cut_info.keys())
    # Number of points in each TGraph
    l = len(cut_vals)
    # No error on the cut values
    cut_err = np.zeros(l)

    # Arrays to hold values and errors
    sig_eff = np.zeros(l)
    bkg_rej = np.zeros(l)
    fom = np.zeros(l)
    sig_eff_err = np.zeros(l)
    bkg_rej_err = np.zeros(l)
    fom_err = np.zeros(l)
    for i, cut_val in enumerate(cut_vals):
        sig_eff[i] = cut_info[cut_val]["sig_eff"].nominal_value
        bkg_rej[i] = cut_info[cut_val]["bkg_rej"].nominal_value
        fom[i] = cut_info[cut_val]["fom"].nominal_value
        sig_eff_err[i] = cut_info[cut_val]["sig_eff"].std_dev
        bkg_rej_err[i] = cut_info[cut_val]["bkg_rej"].std_dev
        fom_err[i] = cut_info[cut_val]["fom"].std_dev

    # The highest FoM and the index of that maximum
    max_fom = np.amax(fom)
    max_idx = np.where(fom == max_fom)[0][0]
    # Cut value, sig eff, and bkg rej at maximum FoM
    max_fom_cut = cut_vals[max_idx]
    max_fom_sig_eff = sig_eff[max_idx]
    max_fom_bkg_rej = bkg_rej[max_idx]

    # Graphs
    var_sig_eff = ROOT.TGraphErrors(
        l, cut_vals, sig_eff, cut_err, sig_eff_err
    )
    var_bkg_rej = ROOT.TGraphErrors(
        l, cut_vals, bkg_rej, cut_err, bkg_rej_err
    )
    var_fom = ROOT.TGraphErrors(
        l, cut_vals, fom, cut_err, fom_err
    )
    sig_eff_bkg_rej = ROOT.TGraphErrors(
        l, sig_eff, bkg_rej, sig_eff_err, bkg_rej_err
    )

    # Set graph titles
    var_sig_eff.SetTitle("{0} vs. signal efficiency".format(variable))
    var_bkg_rej.SetTitle("{0} vs. background rejection".format(variable))
    var_fom.SetTitle("{0} vs. figure of merit".format(variable))
    sig_eff_bkg_rej.SetTitle("Signal efficiency vs. background rejection")
    # Set axes labels
    var_sig_eff.GetXaxis().SetTitle(variable)
    var_sig_eff.GetYaxis().SetTitle("Signal efficiency")
    var_bkg_rej.GetXaxis().SetTitle(variable)
    var_bkg_rej.GetYaxis().SetTitle("Background rejection")
    var_fom.GetXaxis().SetTitle(variable)
    var_fom.GetYaxis().SetTitle("Figure of merit")
    sig_eff_bkg_rej.GetXaxis().SetTitle("Signal efficiency")
    sig_eff_bkg_rej.GetYaxis().SetTitle("Background rejection")

    lines = []

    c = ROOT.TCanvas(variable, variable, 600, 600)
    # Draw axes, a line through the points, errors, points
    opts = "alep"
    c.Divide(2, 2)
    c.cd(1)
    var_fom.Draw(opts)
    l = ROOT.TLine(
        var_fom.GetXaxis().GetXmin(), max_fom,
        max_fom_cut, max_fom
    )
    l.Draw()
    lines.append(l)
    l = ROOT.TLine(
        max_fom_cut, var_fom.GetYaxis().GetXmin(),
        max_fom_cut, max_fom
    )
    l.Draw()
    lines.append(l)
    c.cd(2)
    sig_eff_bkg_rej.Draw(opts)
    l = ROOT.TLine(
        max_fom_sig_eff, 0,
        max_fom_sig_eff, max_fom_bkg_rej
    )
    l.Draw()
    lines.append(l)
    l = ROOT.TLine(
        0, max_fom_bkg_rej,
        max_fom_sig_eff, max_fom_bkg_rej
    )
    l.Draw()
    lines.append(l)
    c.cd(3)
    var_sig_eff.Draw(opts)
    l = ROOT.TLine(
        max_fom_cut, 0,
        max_fom_cut, max_fom_sig_eff
    )
    l.Draw()
    lines.append(l)
    l = ROOT.TLine(
        var_sig_eff.GetXaxis().GetXmin(), max_fom_sig_eff,
        max_fom_cut, max_fom_sig_eff
    )
    l.Draw()
    lines.append(l)
    c.cd(4)
    var_bkg_rej.Draw(opts)
    l = ROOT.TLine(
        max_fom_cut, 0,
        max_fom_cut, max_fom_bkg_rej
    )
    l.Draw()
    lines.append(l)
    l = ROOT.TLine(
        var_bkg_rej.GetXaxis().GetXmin(), max_fom_bkg_rej,
        max_fom_cut, max_fom_bkg_rej
    )
    l.Draw()
    lines.append(l)
    # Set axis ranges, efficiencies should be [0, 1]
    var_sig_eff.GetYaxis().SetRangeUser(0, 1)
    var_bkg_rej.GetYaxis().SetRangeUser(0, 1)
    # Of *course* you have to use a different method for the x-axis!
    sig_eff_bkg_rej.GetXaxis().SetLimits(0, 1)
    sig_eff_bkg_rej.GetYaxis().SetRangeUser(0, 1)

    # Add graphs to the canvas to prevent them being GC'd
    c.var_sig_eff = var_sig_eff
    c.var_bkg_rej = var_bkg_rej
    c.var_fom = var_fom
    c.sig_eff_bkg_rej = sig_eff_bkg_rej
    for i, line in enumerate(lines):
        line.SetLineColor(ROOT.kRed)
        setattr(c, "line_{0}".format(i), line)

    return c


def process_cut(ntuple, cut, sig_pre, bkg_pre, save_plots=False):
    """Process cut on the ntuple, returning a dictionary of data.

    The dictionary data contains statistics for each cut value:
        cut_value_one: {
            yields: (signal yield, background yield),
            sig_eff: signal efficiency,
            bkg_eff: background efficiency,
            bkg_rej: 1 - bkg_eff,
            sb: sig_eff*bkg_rej,
            significance: S/sqrt(S + B)
            fom: figure of merit
        },
        cut_value_two : {...}
    Keyword arguments:
    ntuple -- Lc2pXX instance to take events from
    cut -- Cut instance to process
    sig_pre -- String of cuts to apply when calculating signal yields
    bkg_pre -- String of cuts to apply when calculating background yields
    save_plot -- Boolean whether to save plots
    """
    # Dummy variable used for retrieving yields
    plot_var = cut.variable

    # Calculate initial yield
    sig_init = get_yields(ntuple, plot_var, sig_pre)
    bkg_init = get_yields(ntuple, plot_var, bkg_pre)

    cut_val = cut.min
    scan_info = {}
    while cut_val < cut.max:
        cut_str = "{0} > {1}".format(cut.variable, cut_val)
        sig = get_yields(ntuple, plot_var, "({0})*({1})".format(
            cut_str, sig_pre
        ))
        bkg = get_yields(ntuple, plot_var, "({0})*({1})".format(
            cut_str, bkg_pre
        ))
        # Calculate interesting yield-related properties, adding
        # them to a dictionary
        sig_eff = sig/sig_init
        bkg_eff = bkg/bkg_init
        bkg_rej = 1 - bkg_eff
        fom = sig/(sig + bkg)**0.5
        scan_info[cut_val] = {
            "yields": (sig, bkg),
            "sig_eff": sig_eff,
            "bkg_eff": bkg_eff,
            "bkg_rej": bkg_rej,
            "sb": sig_eff*bkg_rej,
            "significance": utilities.significance(sig, bkg),
            "fom": fom
        }
        cut_val += cut.step
    if save_plots:
        c = create_plots(cut.variable, scan_info)
        c.SaveAs("{0}/optimiser/{1}-{2}.pdf".format(
            config.output_dir, cut.variable, ntuple.meta_string()
        ))
    return scan_info


def iteration(ntuple, cuts, sig_pre,bkg_pre, first=False):
    """Perform one optimisation iteration, cuts ordered by SB

    Keyword arguments:
    ntuple -- Lc2pXX instances
    cuts -- List of Cut instances to optimise
    sig_pre -- String of Preselection cuts to apply to signal candidates
    bkg_pre -- String of Preselection cuts to apply to background candidates
    first -- Boolean denoting whether this is the first iteration.
        If True, cuts are optimised with out any of the other cuts present
        and plots are printed of the optimisation.
    """
    # Cut value with highest optim_param is consider optimal
    optim_param = "fom"
    # Cuts are sorted for sort_param after each iteration
    sort_param = "sb"
    # A list of 2-tuples: (idx of cuts list, value of sort_param for idx)
    sort_indices = []
    for i, cut in enumerate(cuts):
        if not first:
            # Only vary one cut at a time now, so don't vary any others
            # but add then to the preselection cut
            const_cuts = cuts[0:i] + cuts[i+1:]
            cut_sel = "&&".join([
                "({0} > {1})".format(
                    c.variable, c.optimum_cut
                ) for c in const_cuts
            ])
            new_sig_pre = "({0})*({1})".format(sig_pre, cut_sel)
            new_bkg_pre = "({0})*({1})".format(bkg_pre, cut_sel)
        else:
            new_sig_pre = sig_pre
            new_bkg_pre = bkg_pre
        scan_info = process_cut(ntuple, cut, new_sig_pre, new_bkg_pre)
        # Update the optimum cut
        print "Before optim: ", cut.variable, cut.optimum_cut
        # Find the cut value which gives the highest optim_param
        optim_cut = max(scan_info, key=lambda x: scan_info[x][optim_param])
        cut.optimum_cut = optim_cut
        print "After optim: ", cuts[i].variable, cuts[i].optimum_cut
        sort_val = scan_info[optim_cut][sort_param]
        sort_indices.append((i, sort_val))
    # Sort cuts in ascending sort parameter values
    sorted_indices = sorted(sort_indices, key=lambda x: x[1])
    sorted_cuts = []
    for idx, sort_val in sorted_indices:
        sorted_cuts.append(cuts[idx])
    return sorted_cuts


def print_cuts(cuts):
    """Pretty prints a list of cuts."""
    for cut in cuts:
        print cut

def cut_optimiser(mode, polarity, year):
    """Print string of cuts which give the highest significance."""
    ntuple = ntuples.get_ntuple(mode, polarity, year)
    ntuples.add_metatree(ntuple)
    ntuple.activate_selection_branches()

    # Calculate errors correctly when using weights
    ROOT.TH1.SetDefaultSumw2(True)

    cuts = [
        Cut("proton_ProbNNp", 0., 1.0, 0.05),
        Cut("h1_ProbNNpi", 0., 1.0, 0.05),
        Cut("h2_ProbNNpi", 0., 1.0, 0.05)
    ]

    # Preselection cuts
    sig_pre = "signal_sw*(accepted && triggered)"
    bkg_pre = "background_sw*(accepted && triggered)"

    print_cuts(cuts)
    initial_fom = ensemble_fom(ntuple, cuts, sig_pre, bkg_pre)
    cuts = iteration(ntuple, cuts, sig_pre, bkg_pre, first=True)
    new_fom = ensemble_fom(ntuple, cuts, sig_pre, bkg_pre)
    print "Initial FoM:", initial_fom
    print "New FoM:", new_fom
    i = 1
    while fabs((initial_fom - new_fom).nominal_value) > 0.1:
        initial_fom = new_fom
        print "Iteration:", i
        print_cuts(cuts)
        cuts = iteration(ntuple, cuts, sig_pre, bkg_pre)
        new_fom = ensemble_fom(ntuple, cuts, sig_pre, bkg_pre)
        print "New FoM:", new_fom
        i += 1
    # TODO Save the optimum autistic plots, then the same after
    # convergence. Also plot the FoM for each step
    print "FoM converged:", new_fom
    print_cuts(cuts)


if __name__ == "__main__":
    """
    cut_optimiser

    Finds the set of cuts which optimises the signal significance.
    The significance is found using a binned extended maximum likelihood
    fit.
    """
    cut_optimiser(config.pKSDD, config.magboth, 2011)

