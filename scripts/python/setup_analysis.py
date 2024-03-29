#!/usr/bin/env python

import ROOT
import numpy as np

from lc2pxx import config, utilities, ntuples, fitting, plotting
from lc2pxx.Ntuple import Ntuple

def link_branches(source, destination, branches):
    """Links branches from source to new branches in destination.

    This method does not activate branches in source, and it only links
    activated branches. This can be quite useful as it allows one to
    activate the specific branches required, then pass
    source.GetListOfBranches().
    Keyword arguments:
    source -- Ntuple instance to retrieve branch references from
    destination -- TTree (or derived) instance to create branches on
    branches -- List of strings or TBranch instances to transfer
    """
    # Maps NumPy array types to ROOT branch types by inverting
    # Ntuple.types_map
    dtype_map = dict((v, k) for k, v in Ntuple.types_map.iteritems())
    # Link all activated branches in the original to the selected
    for b in branches:
        # If branches is a list of TBranchs, get the name, else just use
        # the string
        try:
            b_name = b.GetName()
        except AttributeError:
            b_name = b
        # GetBranchStatus is 1 for an activated branch
        if source.GetBranchStatus(b_name) == 1:
            ref = source.val(b_name, reference=True)
            b_type = dtype_map[str(np.result_type(ref))]
            destination.Branch(
                b_name, ref, "{0}/{1}".format(b_name, b_type)
            )

def create_metatree(mode, polarity, year, mc):
    """Creates friend tree containing meta branches, saving sWeight plot.

    Doesn't live inside `setup_analysis` as it causes weird branch problems
    when creating the selected ntuple.
    """
    n = ntuples.get_ntuple(
        mode, polarity, year, mc=mc, mc_type=config.mc_stripped
    )
    w = ntuples.create_metatree(n)
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
    utilities.save_to_file("{0}/fits/sWeights-{1}.root".format(
        config.output_dir, n
    ), [w, c])

def setup_analysis(mode, polarity, year, mc=False):
    """Creates ntuples and plots in preparation for the analysis.

    Two ntuples are created
    1. A friend tuple to the MagBoth ntuple, containing metadata such as
       sWeights, daughter invariant mass pairs, and phase space angles
    2. An ntuple containing only the candidates which pass the full
       selection.
    It also creates a number of plots
    1. A fit to the Lambda_c mass used to create the sWeights
    2. A fit to the Lambda_c mass after full selection
    Before this script, there was, of course, a process of finding the
    best cuts for the selection, and few other cross checks.
    """
    n = ntuples.get_ntuple(
        mode, polarity, year, mc=mc, mc_type=config.mc_stripped
    )
    # Create a MetaTree if it doesn't exist
    if not ntuples.add_metatree(n):
        create_metatree(mode, polarity, year, mc)
        ntuples.add_metatree(n)
    # Additional helpful branches to have
    friend_branches = [
        b.GetName()
        for f in n.GetListOfFriends()
        for b in f.GetTree().GetListOfBranches()
    ]
    more_branches = [
        "{0}_{1}".format(particle, variable)
        for particle in ("Lambdac", "proton", "h1", "h2")
        for variable in ("P", "PX", "PY", "PZ", "PE", "ETA")
    ]
    more_branches += [
        "totCandidates",
        "nCandidate",
        "Polarity",
        "nTracks"
    ]
    n.activate_selection_branches()
    n.activate_branches(more_branches + friend_branches, append=True)

    sel_path = "{0}/selected-{1}.root".format(config.output_dir, n)
    sel_name ="DecayTree"
    if not utilities.file_exists(sel_path):
        # Create selected ntuple containing all selection branches
        sel_f = ROOT.TFile(sel_path, "create")
        sel_t = ROOT.TTree(sel_name, sel_name)
        # Branches of the original ntuple (does not including the friend)
        ref_branches = list(n.GetListOfBranches())
        # Link branches from ntuple TTree (and its friend) to selected TTree
        link_branches(n, sel_t, ref_branches + friend_branches)
        print "Creating selected tree for", n
        for entry in n:
            if n.passes_selection():
                sel_t.Fill()
        sel_f.Write()
        sel_f.Close()

    sel_n = n.__class__(sel_name, n.polarity, n.year, n.mc)
    sel_n.add(sel_path)

    # Fit with final selection
    w = ROOT.RooWorkspace("{0}-workspace".format(n))
    # Unbinned fit
    fitting.lambdac_mass.fit(
        sel_n, w, n.shapes_postselection, bins=0
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
    # Uncomment to save a fit with log scale y-axis
    # c.cd(1)
    # ROOT.gPad.SetLogy()
    # ROOT.gPad.Draw()
    utilities.save_to_file("{0}/fits/selected-{1}.root".format(
        config.output_dir, n
    ), [w, c])

    # Print the sig and bkg yields and the significance sig/sqrt(sig + bkg)
    yields = fitting.lambdac_mass.yields(w)
    significance = utilities.significance(yields[0], yields[1])
    print "Yields:", yields
    print "Significance:", significance


if __name__ == "__main__":
    utilities.quiet_mode()
    # for mode in config.modes:
    for mode in (config.pKpi, config.pKK, config.ppipi):
        for polarity in config.polarities:
            setup_analysis(mode, polarity, 2011, mc=False)
            setup_analysis(mode, polarity, 2011, mc=True)
