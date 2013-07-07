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
    n = ntuples.get_ntuple(mode, polarity, year)
    ntuples.add_metatree(n)
    n.activate_selection_branches()

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

