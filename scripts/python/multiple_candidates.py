#!/usr/bin/env python

from lc2pxx import config, ntuples, utilities, Lc2pXX

def multiple_candidates(mode, polarity, year, selection=True):
    """Print the fraction of event containing multiple signal candidates.

    An event is one LHC bunch crossing. It is possible that two signal
    decays are detected during an event, but it is unlikely. It is often
    seen as more likely that a track has been cloned and two identical
    mothers have been formed, or that a background track forms a mother
    with two true tracks. This script calculates and displays the fraction
    of events containing more than one signal candidate. A high fraction
    (> O(1) %) probably indicates fake decays. It also displays the number
    of events with duplicate candidates, that is an event with at least
    Lambda_c decays with the same invariant mass.
    For an in-depth discussion, see http://cern.ch/go/9jLk.
    Keyword arguments:
    selection -- If True, run the full selection before checking
    """
    # We can't use the selected ntuple as it breaks the totCandidates
    # ordering
    n = ntuples.get_ntuple(mode, polarity, year)
    ntuples.add_metatree(n)
    n.activate_selection_branches()
    n.activate_branches([
        "Lambdac_M",
        "totCandidates"
    ], append=True)

    # Number of passing candidates
    passing_cands = 0
    # Number of events with at least two selected decays
    num_multiple = 0
    # Number of events with at least two selected decays sharing the
    # same Lambda_c mass, a sign of cloning somewhere
    num_duplicate = 0
    # Number of candidates remaining in the event
    total_cands = 0
    # List of per-event Lambda_c masses that pass full selection
    masses = []
    # List 
    print "Calculating multiple candidates for", n
    for entry in n:
        if total_cands == 0:
            total_cands = n.val("totCandidates")
            num_cands = len(masses)
            if num_cands > 1:
                if len(set(masses)) < num_cands:
                    num_duplicate += 1
                num_multiple += 1
            masses = []
        # +/- 18 MeV of the nominal Lambda_c mass
        lc_m = n.val("Lambdac_M")
        windowed = 2268. < lc_m < 2304.
        if n.passes_selection() and windowed:
            masses.append(lc_m)
            passing_cands += 1
        total_cands -= 1

    multiples = 100.*num_multiple/passing_cands
    duplicates = 100.*num_duplicate/passing_cands
    print "Number of passing candidates:", passing_cands
    print "Number of events with multiple candidates:", num_multiple
    print "Percentage of multiple candidates:", multiples
    print "Number of events with duplicate candidates:", num_duplicate
    print "Percentage of duplicate candidates:", duplicates


if __name__ == "__main__":
    for mode in config.modes:
        multiple_candidates(mode, config.magboth, 2011)

