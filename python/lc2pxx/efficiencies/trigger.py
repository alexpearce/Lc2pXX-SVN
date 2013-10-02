import ROOT

from lc2pxx import config, ntuples, fitting, plotting, utilities

def efficiency(mode, polarity, year):
    """Return the efficiency of the TOS trigger chain, wrt stripping.

    This performs the same measurement as `efficiency`, but selects TOS
    candidates with respect to stripped candidates, rather than
    reconstructed candidates.
    """
    strip_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    truth_matching = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"
    tos_selection = "({0}) && ({1})".format(
        truth_matching, strip_ntuple.trigger_requirements
    )
    num_pre = strip_ntuple.GetEntries(truth_matching)
    num_tos = strip_ntuple.GetEntries(tos_selection)

    return utilities.efficiency_from_yields(num_tos, num_pre)


def efficiency_post_stripping(mode, polarity, year):
    """Return the efficiency of the TOS trigger chain after stripping.

    This is like `efficiency`, but includes the "offline" kinematic vetoes
    and vertex cuts.
    """
    ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    ntuples.add_metatree(ntuple)
    ntuple.activate_selection_branches()
    truth_str = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"

    num_offline = 0
    num_trigger = 0
    print "Calculating post-offline trigger efficiency in MC"
    for entry in ntuple:
        lb_truth = ntuple.val("Lambdab_BKGCAT") < 60
        lc_truth = ntuple.val("Lambdac_BKGCAT") < 20
        truth = lb_truth and lc_truth
        offline = ntuple.passes_offline_cuts()
        trigger = ntuple.passes_trigger()
        if offline and truth:
            num_offline += 1
            if trigger:
                num_trigger += 1

    return utilities.efficiency_from_yields(num_trigger, num_offline)


def efficiency_pre_stripping(mode, polarity, year):
    """Return the efficiency of the TOS trigger chain.

    This could be done by exploiting the TIS/TOS relationship
        efficiency = TOS&&TIS/TIS,
    but the TIS efficiency is very poor, and so the yields from the pKK
    fit are unstable. Monte Carlo is used instead, where the trigger
    efficiency is simply the ratio
        No. of triggered candidates / No. of reconstructed candidates.
    Candidates are truth matched.
    """
    reco_ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_cheated
    )
    truth_matching = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"
    tos_selection = "({0}) && ({1})".format(
        truth_matching, reco_ntuple.trigger_requirements
    )
    num_pre = reco_ntuple.GetEntries(truth_matching)
    num_tos = reco_ntuple.GetEntries(tos_selection)

    return utilities.efficiency_from_yields(num_tos, num_pre)


def efficiency_tistos(mode, polarity, year):
    """Return the TISTOS efficiency of the TOS trigger chain.

    This is done by using the TIS chain as a reasonably unbiased source
    with which to measure the signal efficiency of the TOS chain.
    The efficiency return is
        TOS && TIS / TIS,
    where TOS/TIS is the yield returned by applying the respective trigger
    chain to the data, after stripping and PID selection, but before
    offline.
    """
    n = ntuples.get_ntuple(mode, polarity, year)
    ntuples.add_metatree(n)
    n.activate_selection_branches()
    n.activate_branches([
        "mu_L0MuonDecision_TIS",
        "mu_Hlt1TrackMuonDecision_TIS",
        "Lambdab_Hlt2TopoMu2BodyBBDTDecision_TIS",
        "Lambdab_Hlt2TopoMu3BodyBBDTDecision_TIS",
        "Lambdab_Hlt2TopoMu4BodyBBDTDecision_TIS"
    ], append=True)

    temp_name = "TempTree"
    mass_var = "Lambdac_M"
    # Temp file to hold TIS candidates
    temp_f_pre = utilities.create_temp_file()
    temp_t_pre = ROOT.TTree(temp_name, temp_name)
    temp_t_pre.Branch(
        mass_var, n.val(mass_var, reference=True), "{0}/D".format(mass_var)
    )
    # Temp file to hold TIS && TOS candidates
    temp_f_post = utilities.create_temp_file()
    temp_t_post = ROOT.TTree(temp_name, temp_name)
    temp_t_post.Branch(
        mass_var, n.val(mass_var, reference=True), "{0}/D".format(mass_var)
    )

    print "Creating temporary trees for trigger selection efficiency."
    for entry in n:
        trigger_tis = (n.val("mu_L0MuonDecision_TIS") and
            n.val("mu_Hlt1TrackMuonDecision_TIS") and
            (n.val("Lambdab_Hlt2TopoMu2BodyBBDTDecision_TIS") or
            n.val("Lambdab_Hlt2TopoMu3BodyBBDTDecision_TIS") or
            n.val("Lambdab_Hlt2TopoMu4BodyBBDTDecision_TIS"))
        )
        trigger_tos = n.passes_trigger()
        # pid = n.passes_pid_cuts()
        pid = n.passes_offline_cuts()
        if trigger_tis and pid:
            temp_t_pre.Fill()
            if trigger_tos:
                temp_t_post.Fill()
    temp_f_pre.Write()
    temp_f_post.Write()

    temp_n_pre = n.__class__.from_tree(temp_t_pre, n.polarity, n.year)
    temp_n_post = n.__class__.from_tree(temp_t_post, n.polarity, n.year)
    w_pre = ROOT.RooWorkspace("{0}-tis-workspace".format(n))
    w_post = ROOT.RooWorkspace("{0}-tistos-workspace".format(n))
    # Unbinned fit
    fitting.lambdac_mass.fit(
        temp_n_pre, w_pre, n.shapes_postselection, bins=0
    )
    fitting.lambdac_mass.fit(
        temp_n_post, w_post, n.shapes_postselection, bins=0
    )
    yields_pre = fitting.lambdac_mass.yields(w_pre)
    yields_post = fitting.lambdac_mass.yields(w_post)
    print yields_pre
    print yields_post

    c_pre = plotting.plot_fit(
        w_pre, [
            ("total_pdf", "Fit"),
            ("signal_pdf", "Signal"),
            ("background_pdf", "Background")
        ],
        mass_var,
        bins=140
    )
    c_post = plotting.plot_fit(
        w_post, [
            ("total_pdf", "Fit"),
            ("signal_pdf", "Signal"),
            ("background_pdf", "Background")
        ],
        mass_var,
        bins=140
    )

    utilities.save_to_file("{0}/fits/tistos-{1}.root".format(
        config.output_dir, n
    ), [w_pre, w_post, c_pre, c_post])


    utilities.delete_temp_file(temp_f_pre)
    utilities.delete_temp_file(temp_f_post)

    return yields_post[0]/yields_pre[0]

