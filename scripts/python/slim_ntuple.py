import ROOT
import numpy as np

from lc2pxx import config, ntuples, utilities
from lc2pxx.Ntuple import Ntuple

def slim_ntuple(name, ntuple, branches, selection_func):
    """Writes a tree of all candidates in ntuple passing selection_func.

    This method will activate the branches to be exported automatically,
    but it cannot activate those required for selection_func, which must be
    done by the user.
    Keyword arguments:
    name -- Prefix of TFile name the output TTree is saved to
    ntuple -- ntuple to select candidates from
    branches -- List of branches in ntuple to write to the output
    selection_func -- Function accepting an Ntuple instance. Called for each
    candidate, if the function returns True, the candidate is saved
    """
    print "Creating {0} ntuple for {1}".format(name, ntuple)
    # Make sure export branches are activated
    ntuple.activate_branches(branches, append=True)
    # Maps NumPy array types to ROOT branch types by inverting
    # Ntuple.types_map
    dtype_map = dict((v, k) for k, v in Ntuple.types_map.iteritems())

    f = ROOT.TFile("{0}/{1}-{2}.root".format(
        config.output_dir, name, ntuple
    ), "recreate")
    t = ROOT.TTree("DecayTree", "DecayTree")
    for branch in branches:
        ref = ntuple.val(branch, reference=True)
        btype = dtype_map[str(np.result_type(ref))]
        t.Branch(branch, ref, "{0}/{1}".format(branch, btype))

    passed = 0
    for entry in ntuple:
        if selection_func(ntuple):
            passed += 1
            t.Fill()
    print "Passed:", passed
    print "Failed:", ntuple.entries - passed
    t.Write()
    f.Close()
    print "{0} ntuple written for {1}".format(name, ntuple)


def pidcalib_ntuple(mode, polarity, year):
    """Create an ntuple for use with PIDCalib."""
    def pidcalib_selection(ntuple):
        """Return True if the current ntuple event passes selection."""
        truth = ntuple.val("Lambdac_BKGCAT") < 20 and ntuple.val("Lambdab_BKGCAT") < 60
        return ntuple.val("accepted") and ntuple.val("triggered") and truth
    branches = [
        "Lambdac_M",
        "proton_P",
        "proton_ETA",
        "proton_ProbNNp",
        "proton_ProbNNk",
        "proton_ProbNNpi",
        "proton_PIDp",
        "proton_PIDK",
        "h1_P",
        "h1_ETA",
        "h1_ProbNNp",
        "h1_ProbNNk",
        "h1_PIDp",
        "h1_PIDK",
        "h1_PIDe",
        "h1_ProbNNpi",
        "h2_P",
        "h2_ETA",
        "h2_ProbNNp",
        "h2_ProbNNk",
        "h2_ProbNNpi",
        "h2_PIDp",
        "h2_PIDK",
        "h2_PIDe",
        "nTracks",
        "accepted",
        "triggered",
        "signal_sw",
        "background_sw"
    ]
    n = ntuples.get_ntuple(mode, polarity, year, mc=True, mc_type=config.mc_stripped)
    ntuples.add_metatree(n)
    n.activate_branches(branches)
    slim_ntuple("PIDCalib", n, branches, pidcalib_selection)


def selected_ntuple(mode, polarity, year):
    """Create an ntuple of only fully selected candidates."""
    def full_selection(ntuple):
        return ntuple.passes_selection()
    branches = [
        "Lambdac_M"
    ]
    n = ntuples.get_ntuple(mode, polarity, year)
    ntuples.add_metatree(n)
    n.activate_selection_branches()
    slim_ntuple("selected", n, branches, full_selection)


def phi_ntuple(polarity, year):
    """Create an ntuple containing (mostly) Lambda_c -> p phi candidates.

    This is done by cutting +/- 3 widths (about 4MeV) around the phi(1020)
    mass in the KK mass spectrum. The sample will contain some
    non-resonant contribution, but it is small.
    Saved candidates also pass the full selection
    """
    def phi_selection(ntuple):
        """Parameters used:
            M(phi(1020)) = 1019.5 MeV
            Gamma(phi(1020)) = 4.3 MeV
        phi peak is cut +/- 3 widths around the nominal mass.
        """
        is_phi = 1006.6 < ntuple.val("h1_h2_M") < 1032.4
        return is_phi
    n = ntuples.get_selected(config.pKK, polarity, year)
    # Copy all branches
    branches = [b.GetName() for b in n.GetListOfBranches()]
    slim_ntuple("selected-pphi", n, branches, phi_selection)


if __name__ == "__main__":
    utilities.quiet_mode()
    """
    Create a slim ntuple of your choice, e.g.
        for mode in (config.pKpi, config.pKK, config.ppipi):
            pidcalib_ntuple(mode, config.magup, 2011)
            pidcalib_ntuple(mode, config.magdown, 2011)
    """

