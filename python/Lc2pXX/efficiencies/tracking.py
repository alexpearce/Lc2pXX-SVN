from math import sqrt

import ROOT
from uncertainties import ufloat

from lc2pxx import config, ntuples, utilities

def efficiency(mode, polarity, year):
    """Return the tracking efficiency.

    The tracking efficiency is the probability that, given a particle that
    leaves sufficient hits in the detector to be reconstructed, is in fact
    reconstructed. It is the ratio
        No. of tracks / No. of reconstructible tracks.
    As implemented here, we assume that the momentum and pseudorapity of
    all reconstructed tracks (K/pi/proton/muon) is well modelled in MC.
    This assumption needs to be shown.
    The tracking table used is ratio2011S20MC17 (http://cern.ch/go/r7sl).
    """

    tracking_table_f = ROOT.TFile("{0}/tracking_table.root".format(
        config.output_dir
    ))
    tracking_table = tracking_table_f.Get("Ratio")

    tracks = ("mu", "proton", "h1", "h2")
    # One p-eta spectrum per track, using the tracking table binnin
    spectra = {}
    branches = []
    for track in tracks:
        for var in ("P", "ETA"):
            branches.append("{0}_{1}".format(track, var))
        s = tracking_table.Clone("{0}_spectrum".format(track))
        s.Reset()
        spectra[track] = s

    mc_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    mc_ntuple.activate_branches(branches)

    # Tracking table has momentum in GeV, ntuples have it in MeV
    gev = 1000.

    print "Filling tracking efficiency spectra"
    for entry in mc_ntuple:
        # While we could loop through `tracks` and do string sub'ing here,
        # this loop is slow enough as it is, so be explict
        spectra["mu"].Fill(
            mc_ntuple.val("mu_P")/gev,
            mc_ntuple.val("mu_ETA")
        )
        spectra["proton"].Fill(
            mc_ntuple.val("proton_P")/gev,
            mc_ntuple.val("proton_ETA")
        )
        spectra["h1"].Fill(
            mc_ntuple.val("h1_P")/gev,
            mc_ntuple.val("h1_ETA")
        )
        spectra["h2"].Fill(
            mc_ntuple.val("h2_P")/gev,
            mc_ntuple.val("h2_ETA")
        )

    # TODO naive calculation, does not account for correlations
    total_efficiency = 1.
    effs = {}
    for track in tracks:
        eff = efficiency_from_spectrum(
            spectra[track],
            tracking_table
        )
        # eff = smeared_efficiency_from_spectrum(
        #     spectra[track],
        #     tracking_table
        # )
        total_efficiency *= eff
        effs[track] = eff
    tracking_table_f.Close()

    return total_efficiency


def efficiency_from_spectrum(spectrum, tracking_table):
    """Return the total tracking efficiency for the p-eta spectrum.

    Keyword arguments:
    spectrum -- Filled p-eta TH2F spectrum
    tracking_table -- Tracking efficiency TH2F in p-eta bins
    """
    bins_x = spectrum.GetNbinsX()
    bins_y = spectrum.GetNbinsY()
    # Sum of weights, i.e. number of events
    total_weight = 0.
    # Sum of weighted ratios
    total_ratio = 0.
    # Sum of squares of weighted errors on the ratio
    total_error = 0.
    for i in range(bins_x + 1):
        for j in range(bins_y + 1):
            p = spectrum.GetXaxis().GetBinCenter(i)
            eta = spectrum.GetYaxis().GetBinCenter(j)
            weight = spectrum.GetBinContent(i, j)
            eff_ratio = efficiency_for_p_eta(p, eta, tracking_table)
            ratio = eff_ratio.nominal_value
            error = eff_ratio.std_dev
            total_weight += weight
            total_ratio += weight*ratio
            total_error += (weight*error)*(weight*error)
    return ufloat(
        total_ratio/total_weight,
        sqrt(total_error)/total_weight
    )


def smeared_efficiency_from_spectrum(spectrum, tracking_table):
    """Explain eeeeverything."""
    bins_x = spectrum.GetNbinsX()
    bins_y = spectrum.GetNbinsY()
    total_ratio = 0.
    total_ratio2 = 0.
    # Random number generator
    rand = ROOT.TRandom3()
    num_toys = 10
    print "Generating smeared tracking efficiency toys"
    for seed in range(num_toys):
        utilities.progress_bar(seed/float(num_toys))
        events = 0
        mean_ratio = 0.
        for i in range(bins_x + 1):
            for j in range(bins_y + 1):
                p = spectrum.GetXaxis().GetBinCenter(i)
                eta = spectrum.GetYaxis().GetBinCenter(j)
                weight = spectrum.GetBinContent(i, j)
                for w in range(int(weight)):
                    events += 1
                    eff_ratio = efficiency_for_p_eta(p, eta, tracking_table)
                    ratio = eff_ratio.nominal_value
                    error = eff_ratio.std_dev
                    rand.SetSeed(seed + (int(abs(ratio - 1.0)*1e5)))
                    smeared_ratio = rand.Gaus(ratio, error)
                    mean_ratio = (smeared_ratio+mean_ratio*(events-1))/events
        total_ratio = (mean_ratio + (total_ratio*seed))/(seed + 1)
        total_ratio2 = (mean_ratio**2 + (total_ratio2*seed))/(seed + 1)
    # Clear progress bar
    print
    return ufloat(
        total_ratio,
        sqrt(total_ratio2 - (total_ratio*total_ratio))
    )


def efficiency_for_p_eta(p, eta, tracking_table):
    """Return the tracking efficiency ufloat at the given p-eta values.

    If the p-eta bin is outside the binning range, the efficiency returned
    is that in the nearest bin.
    Keyword arguments:
    p - Momentum to evaluate efficiency at
    eta - Pseudorapidty to evaluate efficiency at
    tracking_table - Tracking efficiency TH2F in p-eta bins
    """
    bin_i = tracking_table.GetXaxis().FindBin(p)
    bin_j = tracking_table.GetYaxis().FindBin(eta)
    max_i = tracking_table.GetNbinsX()
    max_j = tracking_table.GetNbinsY()
    # Protect against under- and overflow bins
    if bin_i == 0: bin_i = 1
    if bin_j == 0: bin_j = 1
    if bin_i == max_i: bin_i = max_i
    if bin_j == max_j: bin_j = max_j
    return ufloat(
        tracking_table.GetBinContent(bin_i, bin_j),
        tracking_table.GetBinError(bin_i, bin_j)
    )

