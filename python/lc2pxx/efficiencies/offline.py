import ROOT

from lc2pxx import config, ntuples, fitting, utilities

def efficiency(mode, polarity, year):
    """Return the efficiency of the offline cuts, without PID.

    The "offline cuts" are defined as all selection criteria applied after
    ntuple creation that is not a trigger or PID requirement.
    This maps to the Lc2pXX method `passes_offline_selection`, which
    implictly includes `passes_specific_offline_selection`.
    The efficiency is taken as the ratio
        No. passing all selection / No. passing all selection but offline
    The numbers are retrieved from data with unbinned fits to Lambdac_M.
    """
    n = ntuples.get_ntuple(mode, config.magboth, year)
    ntuples.add_metatree(n)
    n.activate_selection_branches()
    n.activate_branches([
        "Polarity"
    ], append=True)
    polarity_int = [-1, 1][polarity == config.magup]

    temp_name = "TempTree"
    mass_var = "Lambdac_M"
    # Temp file to hold candidates passing all-but-offline selection
    temp_f_pre = utilities.create_temp_file()
    temp_t_pre = ROOT.TTree(temp_name, temp_name)
    temp_t_pre.Branch(
        mass_var, n.val(mass_var, reference=True), "{0}/D".format(mass_var)
    )
    # Temp file to hold candidates passing all selection
    temp_f_post = utilities.create_temp_file()
    temp_t_post = ROOT.TTree(temp_name, temp_name)
    temp_t_post.Branch(
        mass_var, n.val(mass_var, reference=True), "{0}/D".format(mass_var)
    )

    print "Creating temporary trees for offline selection efficiency."
    for entry in n:
        # Check the polarity matches the argument, unless it's magboth
        # in which case any polarity here is good
        is_polarity = n.val("Polarity") == polarity_int
        if not is_polarity and not polarity == config.magboth:
            continue
        trigger = n.passes_trigger()
        pid = n.passes_pid_cuts()
        offline = n.passes_offline_cuts()
        if trigger and pid:
            temp_t_pre.Fill()
            if offline:
                temp_t_post.Fill()
    temp_f_pre.Write()
    temp_f_post.Write()

    temp_n_pre = n.__class__.from_tree(temp_t_pre, n.polarity, n.year)
    temp_n_post = n.__class__.from_tree(temp_t_post, n.polarity, n.year)
    w_pre = ROOT.RooWorkspace("{0}-pre-workspace".format(n))
    w_post = ROOT.RooWorkspace("{0}-post-workspace".format(n))
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

    utilities.delete_temp_file(temp_f_pre)
    utilities.delete_temp_file(temp_f_post)

    return yields_post[0]/yields_pre[0]


def efficiency_mc(mode, polarity, year):
    """Return the offline selection efficiency, minus PID, from MC.

    This effectively merges the MC stripping efficiency with the vetoes
    and vertex cuts, then the trigger efficiencies will be wrt to these
    cuts. The TISTOS data cross check should then be after stripping and
    offline cuts.
    There is no weighting here: we assume that track momentum and
    psuedorapdity distributions, as well the vertex variables, are well
    modelled in MC.
    """
    ntuple = ntuples.get_ntuple(
        mode, polarity, year, mc=True, mc_type=config.mc_stripped
    )
    ntuples.add_metatree(ntuple)
    ntuple.activate_selection_branches()
    truth_str = "Lambdab_BKGCAT < 60 && Lambdac_BKGCAT < 20"
    num_stripped = 0

    num_offline = 0
    print "Calculating offline selection efficiency in MC"
    for entry in ntuple:
        lb_truth = ntuple.val("Lambdab_BKGCAT") < 60
        lc_truth = ntuple.val("Lambdac_BKGCAT") < 20
        truth = lb_truth and lc_truth
        offline = ntuple.passes_offline_cuts()
        if truth:
            num_stripped += 1
            if offline:
                num_offline += 1

    return utilities.efficiency_from_yields(num_offline, num_stripped)
