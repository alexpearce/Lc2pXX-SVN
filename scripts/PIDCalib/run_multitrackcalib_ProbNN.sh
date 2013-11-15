#!/bin/bash

# Reference (our signal) location
signal_base=$WORK/OutputBackup/output_ProbNN
signal_tree=DecayTree
# For S20r1:
# stripping=20r1_MCTuneV2
# For S17b
# stripping=17

# Performance histograms directory
perf_hists="output_ProbNN/$stripping"
mkdir -p $perf_hists

# Cuts
K="ProbNNK > 0.5 && DLLK > 4"
Pi="ProbNNpi > 0.7 && DLLK < 10"
# ppipi pion cut is tighter than pKpi
# S20r1 loosens the ppipi PIDK cut from < 0 to < 4, comment out as appropriate
Pi_ppipi="ProbNNpi > 0.7 && DLLK < 4"
# Pi_ppipi="ProbNNpi > 0.7 && DLLK < 0"
P="ProbNNp > 0.5 && PIDp > 4 && PIDpK > 0"

# Ntuple particle branches
h1_K="[h1,K,$K]"
h2_K="[h2,K,$K]"
h1_Pi="[h1,Pi,$Pi]"
h2_Pi="[h2,Pi,$Pi]"
h1_Pi_ppipi="[h1,Pi,$Pi_ppipi]"
h2_Pi_ppipi="[h2,Pi,$Pi_ppipi]"
proton_P="[proton,P,$P]"

# Arguments:
# $1 -- Manget polarity (MagUp, MagDown)
# $2 -- Particle (K, P, Pi)
# $3 -- Cut string (e.g. "[ProbNNp > 0.5]"
run_makeperfhists() {
    python MakePerfHistsRunRange.py \
        -q \
        -o="$perf_hists" \
        -b="Lc2pXX_binning.py" \
        -s="Lc2pXX" \
        "$stripping" \
        "$1" \
        "$2" \
        "$3"
}

# Arguments:
# $1 -- Decay mode (pKpi, pKK, ppipi)
# $2 -- Manget polarity (MagUp, MagDown)
# $3 -- h1 track
# $4 -- h2 track
run_multitrackcalib() {
    # To change to S17b, change 20r1 in the signal and output paths to 17b
    python PerformMultiTrackCalib.py \
        -i="$perf_hists" \
        -x=P -y=ETA -z=nTracks \
        -q \
        -s P Lc2pXX \
        -s Pi Lc2pXX \
        -s K Lc2pXX \
        "$stripping" \
        "$2" \
        "$signal_base/selected-$1-2011-20r1-$2.root" \
        "$signal_tree" \
        "$perf_hists/CalibTree-$1-2011-20r1-$2.root" \
        "$proton_P" \
        "$3" \
        "$4"
}

run_makeperfhists MagUp   "K"  "[$K]"
run_makeperfhists MagDown "K"  "[$K]"
# You have to change line 344 in MakePerfHists... to "UPDATE", otherwise
# the next set of Pi calls will overwrite this one
run_makeperfhists MagUp   "Pi" "[$Pi]"
run_makeperfhists MagDown "Pi" "[$Pi]"
run_makeperfhists MagUp   "Pi" "[$Pi_ppipi]"
run_makeperfhists MagDown "Pi" "[$Pi_ppipi]"
run_makeperfhists MagUp   "P"  "[$P]"
run_makeperfhists MagDown "P"  "[$P]"

run_multitrackcalib pKpi  MagUp   "$h1_K"  "$h2_Pi"
run_multitrackcalib pKpi  MagDown "$h1_K"  "$h2_Pi"
run_multitrackcalib pKK   MagUp   "$h1_K"  "$h2_K"
run_multitrackcalib pKK   MagDown "$h1_K"  "$h2_K"
run_multitrackcalib ppipi MagUp   "$h1_Pi_ppipi" "$h2_Pi_ppipi"
run_multitrackcalib ppipi MagDown "$h1_Pi_ppipi" "$h2_Pi_ppipi"

# run_multitrackcalib pphi MagUp   "$h1_K" "$h2_K"
# run_multitrackcalib pphi MagDown "$h1_K" "$h2_K"
