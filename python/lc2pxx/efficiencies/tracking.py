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

    mc_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    tracks = ("mu", "proton", "h1", "h2")
    spectra = signal_spectra(mc_ntuple, tracks, tracking_table)

    # TODO naive calculation, does not account for correlations
    total_efficiency = 1.
    effs = {}
    for track in tracks:
        eff = efficiency_from_spectrum(spectra[track], tracking_table)
        total_efficiency *= eff
        effs[track] = eff
    tracking_table_f.Close()

    return total_efficiency


def efficiency_smeared(mode, polarity, year, toys=30):
    """Return the tracking efficiency form the "smearing" method.

    The smearing method proceeds in the same way as usual (see `efficiency),
    except in runs a number of experiments, in each case "smearing" the
    tracking table by its errors.
    This is done by copying the tracking table, and then changing the
    nominal values with
        smeared_nom_val = TRandom3.Gaus(nom_val, err_on_nom_val).
    The efficiency is then calculated with the smeared table.
    This process is repeated many times, with the final efficiency being
    the mean of the experiments, and the error the RMS.
    """
    tracking_table_f = ROOT.TFile("{0}/tracking_table.root".format(
        config.output_dir
    ))
    tracking_table = tracking_table_f.Get("Ratio")

    mc_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    tracks = ("mu", "proton", "h1", "h2")
    spectra = signal_spectra(mc_ntuple, tracks, tracking_table)

    # We use toys in division a lot, so make sure we're not doing integer
    # division
    f_toys = float(toys)
    smeared_effs = []
    print "Generating tracking efficiency toys"
    # Go from 1 as a seed of 0 is a "random seed", and so not deterministic
    for seed in range(1, toys + 1):
        utilities.progress_bar(seed/f_toys)
        smeared_table = smear_table(tracking_table, seed)
        total_eff = 1.
        for track in tracks:
            eff = efficiency_from_spectrum(spectra[track], tracking_table)
            total_eff *= eff
        # We're not worried about the error here, we'll derive it later
        smeared_effs.append(total_eff.nominal_value)
    # Clear progress bar
    print
    tracking_table_f.Close()

    # Tracking efficiency is mean of smeared efficiencies
    tracking_eff = sum(smeared_effs)/f_toys
    # Also calculate the mean of the squared smeared efficiencies
    tracking_eff_sq = sum([x*x for x in smeared_effs])/f_toys 
    # So the uncertainty is the standard deviation
    #   sigma = sqrt(variance) = sqrt(<x*x> - <x>*<x>)
    tracking_eff_err = sqrt(tracking_eff_sq - (tracking_eff*tracking_eff))

    return ufloat(tracking_eff, tracking_eff_err)


def signal_spectra(ntuple, tracks, spectrum):
    """Return dictionary of p-eta spectra for the tracks in ntuple.

    Keyword arguments:
    ntuple -- Ntuple instance
    tracks -- List of ntuple branches to fill spectra for
    spectrum -- Template TH2F spectrum to use. This method will copy and
      erase it
    """
    # Make sure the branches we need are active
    branches = []
    # Order here is order vars are passed to TH2F::Fill
    vars = ["P", "ETA"]
    spectra = {}
    for track in tracks:
        for var in vars:
            branches.append("{0}_{1}".format(track, var))
        s = spectrum.Clone("{0}_spectrum".format(track))
        s.Reset()
        spectra[track] = s
    ntuple.activate_branches(branches)

    # Tracking table has momentum in GeV, ntuples have it in MeV
    gev = 1000.

    print "Filling tracking efficiency spectra"

    refs = {}
    # Fill a dictionary with references to the ntuple branches
    # This saves us having to construct a branch name string each entry
    for track in tracks:
        refs[track] = []
        for var in vars:
            refs[track].append(
                ntuple.val("{0}_{1}".format(track, var), reference=True)
            )
    for entry in ntuple:
        for track in tracks:
            # The extra [0] accesses the value from the reference
            spectra[track].Fill(refs[track][0][0]/gev, refs[track][1][0])
    return spectra


def smear_table(spectrum, seed):
    """Return a clone of spectrum, smeared by its errors.

    Using TRandom3, set with a seed of `seed`, the new values are given by
        new_value = TRandom3.Gaus(value, value_err)
    in each bin.
    For the same seed and spectrum, this method will return the same
    smeared table (i.e. this method is deterministic, except when seed=0).
    Keyword arguments:
    spectrum -- Tracking efficiency spectrum to smear
    seed -- Seed to pass to TRandom3 instance
    """
    rnd = ROOT.TRandom3()
    rnd.SetSeed(seed)
    smeared = spectrum.Clone("smeared_{0}".format(spectrum.GetName()))
    for i in range(spectrum.GetNbinsX()):
        for j in range(spectrum.GetNbinsY()):
            weight = spectrum.GetBinContent(i, j)
            error = spectrum.GetBinError(i, j)
            new_weight = rnd.Gaus(weight, error)
            smeared.SetBinContent(i, j, new_weight)
    return smeared

def efficiency_from_spectrum(spectrum, tracking_table):
    """Return the total tracking efficiency for the p-eta spectrum.

    This is option two on the TrackingEffRatio page.
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

