"""
ntuples
Methods for retrieving and manipulating ntuples, usually TTrees and TChains,
as well as classes representing such ntuples.
"""

import os
import logging as log
from math import fabs, atan2, asin

import ROOT
import numpy as np
from uncertainties import ufloat

from lc2pxx import config, utilities, fitting, Ntuple, Lc2pXX

def ntuple_path(polarity, year, mc, mode=None):
    """Return the path to the ntuple of the specified type.

    Keyword arguments:
    polarity -- One of lc2pxx.config.polarities
    year -- One of lc2pxx.config.years
    mc -- If True, use MC data, else collision
    mode -- One of lc2pxx.config.modes, only required if mc=True
    """
    if polarity is config.magboth:
        log.warning("Cannot return path for MagBoth polarity")
        return None

    # Local data, or over AFS?
    data_dir = [
        config.work_data_dir,
        config.scratch_data_dir
    ][config.use_scratch]
    # There's one MC ntuple per mode, but one for all modes for collision
    if mc is True:
        base = "{0}/{1}/{2}/{3}".format(
            data_dir,
            "MonteCarlo",
            year,
            config.mc_event_types[mode]
        )
    else:
        base = "{0}/{1}/{2}".format(
            data_dir,
            "Collision",
            year
        )
    filename = "{0}.{1}.{2}.{3}.root".format(
        config.ntuple_name,
        year,
        config.stripping_years[year],
        polarity
    )
    path = "{0}/{1}".format(base, filename)

    if not utilities.file_exists(path):
        log.error("File at `{0}` not found".format(path))

    return path


def get_ntuple(mode, polarity, year, mc=False, mc_type=None):
    """Return a TChain for the specified mode and polarity.

    Keyword arguments:
    mode -- One of lcp2xx.config.modes
    polarity -- One of lc2pxx.config.polarities
    year -- One of lc2pxx.config.years
    mc -- If True, use MC data, else collision (default False)
    mc_type -- One of config.mc_types, must be specified if mc=True
    """
    log.info("Retrieving ntuple for {0} {1} {2}".format(
        year, mode, polarity
    ))

    nickname = config.mc_nicknames[mode]
    decay_tree = "TupleLcTo{0}/DecayTree".format(mode)
    mc_tree = "MCTupleGenLcTo{0}/MCDecayTree".format(nickname)
    cheat_tree = "TupleCombineCheatedLb0TomuLcTo{0}/DecayTree".format(
        nickname
    )

    if not mc or mc_type is config.mc_stripped:
        tree_name = decay_tree
    else:
        if mc_type is config.mc_generated:
            tree_name = mc_tree
        elif mc_type is config.mc_cheated:
            tree_name = cheat_tree

    # Create an ntuple of the class corresponding to the decay mode
    # TODO use Ntuple class rather than Lc2pXX for MCDecayTree
    klass = getattr(Lc2pXX, "Lc2{0}".format(mode))
    ntuple = klass(tree_name, polarity, year)

    if polarity in (config.magup, config.magboth):
        ntuple.add(ntuple_path(config.magup, year, mc, mode))
    if polarity in (config.magdown, config.magboth):
        ntuple.add(ntuple_path(config.magdown, year, mc, mode))

    return ntuple


def luminosity(polarity, year, mc=False):
    """Calculates the luminosity for the given magnet polarity and year.

    The ufloat returned is given in inverse picobarns, and is calculated
    using the LumiTuple created in DaVinci.
    Luminosity is mode-independent.
    Keyword arguments:
    polarity -- One of lc2pxx.config.polarities
    year -- One of lc2pxx.config.years
    mc -- If True, use MC data, else collision (default False)
    """
    log.info("Calculating luminosity for {0} {1}".format(year, polarity))

    lumi_ntuple = Ntuple.Ntuple("GetIntegratedLuminosity/LumiTuple")

    if polarity in (config.magup, config.magboth):
        lumi_ntuple.add(ntuple_path(config.magup, year, mc))
    if polarity in (config.magdown, config.magboth):
        lumi_ntuple.add(ntuple_path(config.magdown, year, mc))

    total_lumi = 0.
    total_lumi_error = 0.
    log.info("Luminosity ntuple ({0} {1}) has {2} entries".format(
        year, polarity, lumi_ntuple.entries
    ))
    for entry in lumi_ntuple:
        total_lumi += lumi_ntuple.val("IntegratedLuminosity")
        total_lumi_error += lumi_ntuple.val("IntegratedLuminosityErr")

    return ufloat(total_lumi, total_lumi_error)


def metatree_path(ntuple):
    """Return path to meta friend tuple that belongs to ntuple."""
    return "{0}/meta-{1}.root".format(
        config.output_dir, ntuple
    )

def create_metatree(ntuple):
    """Create a friend tree with several useful attributes for ntuple.

    The five phase space variables are included in the friend tree.
    These are two daughter-pair invariant masses and three angles, first
    defined by E791 (arXiv hep-ex/9912003).
    The LHCb (lab) coordinate system is defined as:
        * x increasing from the VELO to the cavern access entrance;
        * y increasing opposite gravity; and
        * z increasing from the VELO to the RICHes.

    The created MetaTree TTree contains the following branches for
    each entry:
    random -- Float, random number in the range [0, 1]
    accepted -- Boolean, does the event pass the preselection?
    triggered -- Boolean, does the event pass the trigger requirements?
    signal_sw -- Float, signal sWeights from fit
    background_sw -- Float, background sWeights from fit
    Returns the workspace used to perform the fit.
    Keyword Arguments:
    ntuple -- Lc2pXX instance to which the friend is to be associated
    """
    meta_path = metatree_path(ntuple)
    # Check if MetaTree already exists
    if utilities.file_exists(meta_path):
        resp = raw_input("File {0} exists, overwrite? ".format(meta_path))
        if resp is not "y":
            raise IOError("MetaTree file already exists.")

    log.info("Creating MetaTree at {0}".format(meta_path))

    # Create file and tree
    t_name = config.metatree_name
    f = ROOT.TFile(meta_path, "recreate")
    t = ROOT.TTree(t_name, t_name)

    # Array pointers to branch values
    # dtype=float is default for np.zeros
    lc_m = np.zeros(1)
    random = np.zeros(1)
    accepted = np.zeros(1, dtype=int)
    triggered = np.zeros(1, dtype=int)
    p_h1_M = np.zeros(1)
    p_h2_M = np.zeros(1)
    h1_h2_M = np.zeros(1)
    proton_theta = np.zeros(1)
    proton_phi = np.zeros(1)
    cos_h1_h2_phi = np.zeros(1)
    signal_sw = np.zeros(1)
    background_sw = np.zeros(1)
    sum_sw = np.zeros(1)
    # Bind branches to pointers
    t.Branch("Lambdac_M", lc_m, "Lambdac_M/D")
    t.Branch("random", random, "random/D")
    t.Branch("accepted", accepted, "accepted/I")
    t.Branch("triggered", triggered, "triggered/I")
    t.Branch("p_h1_M", p_h1_M, "p_h1_M/D")
    t.Branch("p_h2_M", p_h2_M, "p_h2_M/D")
    t.Branch("h1_h2_M", h1_h2_M, "h1_h2_M/D")
    t.Branch("proton_theta", proton_theta, "proton_theta/D")
    t.Branch("proton_phi", proton_phi, "proton_phi/D")
    t.Branch("cos_h1_h2_phi", cos_h1_h2_phi, "cos_h1_h2_phi/D")
    t.Branch("signal_sw", signal_sw, "signal_sw/D")
    t.Branch("background_sw", background_sw, "background_sw/D")
    t.Branch("sum_sw", sum_sw, "sum_sw/D")

    # Make sure the branches we need are active
    ntuple.activate_selection_branches()
    selection = "({0}) && ({1})".format(
        config.trigger_requirements, config.lc_m_window
    )
    # Generate sWeights
    with ntuple.copy_selected(selection) as nt:
        workspace = ROOT.RooWorkspace("sweights_workspace")
        # Unbinned fit
        fitting.lambdac_mass.fit(
            nt, workspace, ntuple.shapes_preselection
        )
        sweights = fitting.lambdac_mass.sweights(workspace)
    # Dataset holding the sWeights and Lc_M variables
    sweights_ds = sweights.GetSDataSet()
    sw_argset = sweights_ds.get()
    sw_lc_m = sw_argset.find("Lambdac_M")
    sw_sig = sw_argset.find("{0}_sw".format(
        fitting.lambdac_mass.consts["yield_sig"]
    ))
    sw_bkg = sw_argset.find("{0}_sw".format(
        fitting.lambdac_mass.consts["yield_bkg"]
    ))
    # As we only create sWeights for accepted and triggered events,
    # we must have a counter for the sWeight dataset
    sw_entry = 0

    # Mersenne Twistor
    # Seed of zero guarantees unique space-time sequences
    # If sequences are required to be the same over multiple generations,
    # set this to something other than zero
    generator = ROOT.TRandom3(0)

    # 4-vectors for calculating phase space angles
    lb_lab = ROOT.TLorentzVector()
    lc_lab = ROOT.TLorentzVector()
    proton_lab = ROOT.TLorentzVector()
    h1_lab = ROOT.TLorentzVector()
    h2_lab = ROOT.TLorentzVector()
    mom_branches = []
    for particle in ("Lambdac", "Lambdab", "proton", "h1", "h2"):
        for comp in ("X", "Y", "Z", "E"):
            mom_branches.append("{0}_P{1}".format(particle, comp))
    ntuple.activate_branches(mom_branches, append=True)

    # Fill the ouput tree
    for entry in ntuple:
        lc_m[0] = ntuple.val("Lambdac_M")
        random[0] = generator.Rndm()
        accepted[0] = ntuple.passes_preselection()
        triggered[0] = ntuple.passes_trigger()
        # Add non-zero sWeights to triggered events
        if triggered[0] and accepted[0]:
            sweights_ds.get(sw_entry)
            # Check the index is OK
            if fabs(lc_m[0] - sw_lc_m.getVal()) > 0.1:
                raise ValueError("sWeights mismatch: {0} - {1}".format(
                    lc_m[0], sw_lc_m.getVal()
                ))
            signal_sw[0] = sw_sig.getVal()
            background_sw[0] = sw_bkg.getVal()
            sum_sw[0] = sweights.GetSumOfEventSWeight(sw_entry)
            sw_entry += 1
        else:
            signal_sw[0] = background_sw[0] = sum_sw[0] = 0

        # Fill 4-vectors with momentum in the lab frame
        lb_lab.SetPxPyPzE(
            ntuple.val("Lambdab_PX"),
            ntuple.val("Lambdab_PY"),
            ntuple.val("Lambdab_PZ"),
            ntuple.val("Lambdab_PE")
        )
        lc_lab.SetPxPyPzE(
            ntuple.val("Lambdac_PX"),
            ntuple.val("Lambdac_PY"),
            ntuple.val("Lambdac_PZ"),
            ntuple.val("Lambdac_PE")
        )
        proton_lab.SetPxPyPzE(
            ntuple.val("proton_PX"),
            ntuple.val("proton_PY"),
            ntuple.val("proton_PZ"),
            ntuple.val("proton_PE")
        )
        h1_lab.SetPxPyPzE(
            ntuple.val("h1_PX"),
            ntuple.val("h1_PY"),
            ntuple.val("h1_PZ"),
            ntuple.val("h1_PE")
        )
        h2_lab.SetPxPyPzE(
            ntuple.val("h2_PX"),
            ntuple.val("h2_PY"),
            ntuple.val("h2_PZ"),
            ntuple.val("h2_PE")
        )

        # Daughter pair 2-body invariant masses
        p_h1_M[0] = (proton_lab + h1_lab).M()
        p_h2_M[0] = (proton_lab + h2_lab).M()
        h1_h2_M[0] = (h1_lab + h2_lab).M()

        # What we do here is a little nifty
        # First, find the rotation needed to align the Lc flight direction
        # with the lab x-axis
        # This is a rotation about y then z through angles alpha then beta
        # Next, rotate everything with the above and boost in to the Lc
        # rest frame
        # Finally, rotate the Lc polarization axis, defined as the cross
        # product of the Lb and Lc flight directions, on to the lab z-axis
        alpha = atan2(lc_lab.Z(), lc_lab.X())
        # Rho, in spherical coordinates, is the 3-vector magnitude
        beta = -asin(lc_lab.Y()/lc_lab.Rho())
        rotation = ROOT.TRotation()
        rotation.RotateY(alpha)
        rotation.RotateZ(beta)

        # Rotate everything
        lb_rest = ROOT.TLorentzVector(lb_lab)
        lc_rest = ROOT.TLorentzVector(lc_lab)
        proton_rest = ROOT.TLorentzVector(proton_lab)
        h1_rest = ROOT.TLorentzVector(h1_lab)
        h2_rest = ROOT.TLorentzVector(h2_lab)
        lb_rest.Transform(rotation)
        lc_rest.Transform(rotation)
        proton_rest.Transform(rotation)
        h1_rest.Transform(rotation)
        h2_rest.Transform(rotation)

        # Boost to the Lc rest frame
        boost = -lc_rest.BoostVector()
        lb_rest.Boost(boost)
        lc_rest.Boost(boost)
        proton_rest.Boost(boost)
        h1_rest.Boost(boost)
        h2_rest.Boost(boost)

        # At this point, we're in the Lc rest frame is whose x-axis is
        # pointing along the lab x-axis
        # We now align the polarization axis,
        # Lb flight dir. x Lc flight dir., with the lab z-axis
        pol_axis = lb_rest.Vect().Cross(lc_rest.Vect())
        gamma = atan2(pol_axis.Y(), pol_axis.Z())
        lb_rest.RotateX(gamma)
        lc_rest.RotateX(gamma)
        proton_rest.RotateX(gamma)
        h1_rest.RotateX(gamma)
        h2_rest.RotateX(gamma)

        # Three phase space angles, in the Lc rest frame
        # Angle between polarization axis and proton direction
        proton_theta[0] = proton_rest.Theta()
        # Angle between Lc direction and proton direction
        proton_phi[0] = proton_rest.Phi()
        # Angle between proton-polarization plane and h1-h2 plane,
        # which is equal to the angle between the normals of the planes
        proton_pol_norm = proton_rest.Vect().Cross(pol_axis).Unit()
        h1_h2_norm = h1_rest.Vect().Cross(h2_rest.Vect()).Unit()
        cos_h1_h2_phi[0] = proton_pol_norm.Dot(h1_h2_norm)

        t.Fill()
    f.cd()
    t.Write()
    f.Close()

    return workspace

def add_metatree(ntuple):
    """Add a meta friend tuple to ntupl, returning True if it exists."""
    path = metatree_path(ntuple)
    exists = utilities.file_exists(path)
    if exists:
        ntuple.add_friend(config.metatree_name, path)
    return exists

