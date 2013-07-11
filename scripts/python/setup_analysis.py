#!/usr/bin/env python

import ROOT
import numpy as np

from lc2pxx import config, utilities, ntuples, fitting, plotting
from lc2pxx.Ntuple import Ntuple

def save_to_file(filename, objects):
    """Creates a TFile called filename, then writes each object to the file.

    Keyword arguments:
    filename -- Name of the filename the objects will be saved in to.
        If filename already exists, it is overwritten.
    objects -- List of objects implementing TObject.Write.
    """
    file = ROOT.TFile(filename, "recreate")
    for object in objects: object.Write()
    file.Write()
    file.Close()


def link_branches(source, destination, branches):
    """Links branches to source to new branches in destination.

    This method does not activate branches in source, and it only links
    activated branches. This can be quite useful as it allows one to
    activate the specific branches required, then pass the full list
    of branches.
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
        if type(b) is str:
            b_name = b
        else:
            b_name = b.GetName()
        # GetBranchStatus is 1 for an activated branch
        if source.GetBranchStatus(b_name) == 1:
            ref = source.val(b_name, reference=True)
            b_type = dtype_map[str(np.result_type(ref))]
            destination.Branch(
                b_name, ref, "{0}/{1}".format(b_name, b_type)
            )


def setup_analysis(mode, polarity, year):
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
    # Number of bins to create when plotting (fitting is unbinned)
    num_bins = 140
    mass_var = "Lambdac_M"

    n = ntuples.get_ntuple(mode, polarity, year)
    # Create a MetaTree if it doesn't exist
    if not ntuples.add_metatree(n):
        w = ntuples.create_metatree(n)
        c = plotting.plot_fit(
            w, [
                ("total_pdf", "Fit"),
                ("signal_pdf", "Signal"),
                ("background_pdf", "Background")
            ],
            mass_var,
            bins=140
        )
        save_to_file("{0}/fits/sWeights-{1}.root".format(
            config.output_dir, n
        ), [w, c])
        ntuples.add_metatree(n)
    n.activate_selection_branches()
    # Additional helpful branches to have
    n.activate_branches([
        "proton_PX",
        "proton_PY",
        "proton_PZ",
        "proton_PE",
        "h1_PX",
        "h1_PY",
        "h1_PZ",
        "h1_PE",
        "h2_PX",
        "h2_PY",
        "h2_PZ",
        "h2_PE",
        "totCandidates",
        "nCandidate",
        "Polarity",
        "nTracks"
    ], append=True)

    sel_path = "{0}/selected-{1}.root".format(config.output_dir, n)
    sel_name ="DecayTree"
    if not utilities.file_exists(sel_path):
        # Create selected ntuple containing all selection branches
        sel_f = ROOT.TFile(sel_path, "create")
        sel_t = ROOT.TTree(sel_name, sel_name)
        # Branches of the original ntuple
        ref_branches = list(n.GetListOfBranches())
        # Link branches from ntuple TTree to selected TTree
        link_branches(n, sel_t, ref_branches)
        # Link all activated branches from from trees, too
        friends = n.GetListOfFriends()
        for f in friends:
            friend_branches = list(f.GetTree().GetListOfBranches())
            link_branches(n, sel_t, friend_branches)
        print "Creating selected tree for", n
        for entry in n:
            if n.passes_selection():
                sel_t.Fill()
        sel_f.Write()
        sel_f.Close()

    sel_n = n.__class__(sel_name, n.polarity, n.year)
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
        mass_var,
        bins=num_bins
    )
    save_to_file("{0}/fits/selected-{1}.root".format(
        config.output_dir, n
    ), [w, c])

    # Print the sig and bkg yields and the significance sig/sqrt(sig + bkg)
    yields = fitting.lambdac_mass.yields(w)
    significance = utilities.significance(yields[0], yields[1])
    print "Yields:", yields
    print "Significance:", significance


if __name__ == "__main__":
    setup_analysis(config.pKK, config.magboth, 2011)
    exit()
    for mode in config.modes:
        setup_analysis(mode, config.magboth, 2011)

