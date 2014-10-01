#!/usr/bin/env python

from math import sqrt

import ROOT

from lc2pxx import config, ntuples, utilities

# Maps the ntuple branches for each mode to the PIDCalib particle name
mode_particle_map = {
    config.pKpi: {
        "proton": "P",
        "h1": "K",
        "h2": "Pi"
    },
    config.pKK: {
        "proton": "P",
        "h1": "K",
        "h2": "K"
    },
    config.ppipi: {
        "proton": "P",
        "h1": "Pi",
        "h2": "Pi"
    }
}

# Define PID selection cuts
p_cut = "ProbNNp > 0.5"
k_cut = "ProbNNK > 0.5"
pi_cut = "ProbNNpi > 0.7"
# Maps the ntuple branches for each mode to the PID cut on that branch
mode_cut_map = {
    config.pKpi: {
        "proton": p_cut,
        "h1": k_cut,
        "h2": pi_cut
    },
    config.pKK: {
        "proton": p_cut,
        "h1": k_cut,
        "h2": k_cut
    },
    config.ppipi: {
        "proton": p_cut,
        "h1": pi_cut,
        "h2": pi_cut
    }
}

def pidcalib_study(mode, polarity, year, particle, cut, verbose=False):
    """Compare kinematic distributions of our signal and PIDCalib tracks.

    The 2D p-eta efficiencies distributions generated by the PIDCalib script
    `MakePerfHistsRunRange.py` are plotted, then areas with invalid
    efficiencies are removed, and the histo is replotted.
    Then the distributions of our signal are plotted, and a message is
    printed if there are significant numbers of signal events in the
    invalid efficiency bins.
    """
    output_dir = "{0}/pidcalib_study".format(config.output_dir)
    # Get the PIDCalib name for our ntuple branch name
    pid_particle = mode_particle_map[mode][particle]
    # No stats box
    ROOT.gStyle.SetOptStat(0)

    # Get the efficiency histograms, draw and save them
    input_path = "/afs/cern.ch/user/a/apearce/cmtuser/Urania_v1r1/PIDCalib/PIDPerfScripts/scripts/python/MultiTrack/P-ETA-nTracks"
    f_name = "PerfHists_{0}_Strip20r1_MCTuneV2_MagDown_3D.root"
    f = ROOT.TFile("{0}/{1}".format(
        input_path, f_name.format(pid_particle)
    ))
    h_3d = f.Get("{0}_{1}_All".format(pid_particle, cut))
    # Project in momentum and pseudorapidity
    h_2d = h_3d.Project3D("xy")
    h_2d.SetTitle("{0} PID efficiencies".format(pid_particle))
    # The projection sums the bins in the z-axis, so scale to "unity"
    h_2d.Scale(1./h_3d.GetZaxis().GetNbins())
    c_name = "{0}_{1}".format(mode, particle)
    c = ROOT.TCanvas(c_name, c_name, 400, 400)
    h_2d.Draw("colztext")
    c.SaveAs("{0}/{1}_{2}_spectrum_dirty.pdf".format(
        output_dir, mode, particle
    ))

    # Ntuple branch names of the pseudorapidity and lab momentum
    particle_eta = "{0}_ETA".format(particle)
    particle_p = "{0}_P".format(particle)
    # Clone eff histos, filling them with our selected signal
    n = ntuples.get_selected(mode, polarity, year)
    # n = ntuples.get_ntuple(mode, polarity, year)
    ntuples.add_metatree(n)
    h_2d_signal = h_2d.Clone()
    h_2d_signal.Reset()
    for entry in n:
        h_2d_signal.Fill(
            n.val(particle_eta),
            n.val(particle_p),
            n.val("signal_sw")
        )
    c.cd()
    h_2d_signal.Draw("colztext")
    c.SaveAs("{0}/{1}_{2}_spectrum_signal.pdf".format(
        output_dir, mode, particle
    ))

    # Loop over the bins and print occupied signal bins that have invalid
    # efficiencies
    # Modify the efficiency histogram so that invalid bins are empty
    h_2d_x = h_2d.GetXaxis()
    h_2d_y = h_2d.GetYaxis()
    e_bins = h_2d_x.GetNbins()
    p_bins = h_2d_y.GetNbins()
    # Total number of entries
    tot = 0.
    tot_err = 0.
    # Total number of entries in invalid efficiency bins
    tot_invalid = 0.
    tot_invalid_err = 0.
    for e_bin in range(1, e_bins + 1):
        for p_bin in range(1, p_bins + 1):
            # Kinematic values of the bin
            e = h_2d_x.GetBinCenter(e_bin)
            p = h_2d_y.GetBinCenter(p_bin)
            # Efficiency of the PID cut in the bin
            eff = h_2d.GetBinContent(e_bin, p_bin)
            eff_err = h_2d.GetBinError(e_bin, p_bin)
            # Number of signal candidates in the bin
            entries = h_2d_signal.GetBinContent(e_bin, p_bin)
            entries_err = h_2d_signal.GetBinError(e_bin, p_bin)
            tot += entries
            tot_err = sqrt(tot_err**2 + entries_err**2)
            # An invalid efficiency is arbitrarily defined as below 0.1
            if eff > 0.1: continue
            tot_invalid += entries
            tot_invalid_err = sqrt(tot_invalid_err**2 + entries_err**2)
            b = h_2d.GetBin(e_bin, p_bin)
            h_2d.SetBinContent(b, 0.0)
            if verbose:
                print "== Invalid Bin Found =="
                print "p: {0}, eta: {1}".format(p, e)
                print "eff: {0} +/- {1}".format(eff, eff_err)
                print "signal entries: {0} +/- {1}".format(
                    entries, entries_err
                )
    print "== {0} {1} Results ({2}) ==".format(mode, pid_particle, cut)
    print "Entries: {0:.2f} +/- {1:.2f}".format(tot, tot_err)
    print "Invalid entries: {0:.2f} +/- {1:.2f} ({2:.2f}%)".format(
        tot_invalid, tot_invalid_err, 100.*tot_invalid/tot
    )
    # Save the efficiency histogram with invalid bins removed
    h_2d.Draw("colztext")
    c.SaveAs("{0}/{1}_{2}_spectrum_clean.pdf".format(
        output_dir, mode, particle
    ))

if __name__ == "__main__":
    utilities.quiet_mode()

    # Define ntuples we'll use
    polarity = config.magboth
    year = 2011
    for mode in (config.pKpi, config.pKK, config.ppipi):
        pidcalib_study(
            mode, polarity, year, "proton", mode_cut_map[mode]["proton"]
        )
        pidcalib_study(
            mode, polarity, year, "h1", mode_cut_map[mode]["h1"]
        )
        pidcalib_study(
            mode, polarity, year, "h2", mode_cut_map[mode]["h2"]
        )