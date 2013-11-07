#!/bin/bash

# Reference (our signal) location
signal_base=$HOME/cmtuser/Urania_v2r1/Phys/Lc2pXX/scripts/python/output
signal_tree=DecayTree
# For S20r1:
# stripping=20r1_MCTuneV2
# For S17b
# stripping=17

# Performance histograms directory
perf_hists="output_ProbNN/$stripping"
mkdir -p $perf_hists

# Cuts
K="ProbNNK > 0.5"
Pi="ProbNNpi > 0.7"
P="ProbNNp > 0.5"
# Ntuple particle branches
h1_K="[h1,K,$K]"
h2_K="[h2,K,$K]"
h1_Pi="[h1,Pi,$Pi]"
h2_Pi="[h2,Pi,$Pi]"
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
        "$signal_base/selected-$1-2011-17b-$2.root" \
        "$signal_tree" \
        "$perf_hists/CalibTree-$1-2011-17b-$2-mc.root" \
        "$proton_P" \
        "$3" \
        "$4"
    # So we can read the values before the next call
    sleep 10
}

run_makeperfhists MagUp   "K"  "[$K]"
run_makeperfhists MagDown "K"  "[$K]"
run_makeperfhists MagUp   "Pi" "[$Pi]"
run_makeperfhists MagDown "Pi" "[$Pi]"
run_makeperfhists MagUp   "P"  "[$P]"
run_makeperfhists MagDown "P"  "[$P]"

run_multitrackcalib pKpi  MagUp   "$h1_K"  "$h2_Pi"
run_multitrackcalib pKpi  MagDown "$h1_K"  "$h2_Pi"
run_multitrackcalib pKK   MagUp   "$h1_K"  "$h2_K"
run_multitrackcalib pKK   MagDown "$h1_K"  "$h2_K"
run_multitrackcalib ppipi MagUp   "$h1_Pi" "$h2_Pi"
run_multitrackcalib ppipi MagDown "$h1_Pi" "$h2_Pi"

run_multitrackcalib pphi MagUp   "$h1_K" "$h2_K"
run_multitrackcalib pphi MagDown "$h1_K" "$h2_K"
