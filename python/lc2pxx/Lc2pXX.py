import logging as log

from lc2pxx import config, utilities, Ntuple


class Lc2pXX(Ntuple.Ntuple):
    """Ntuple representing all Lambda_c to proton h^+ h^- decays."""
    # Mode-specific selection branches to activate
    # Should be filled by subclasses, if required
    mode_selection_branches = []
    # The variable describing the Lambda_c mass spectrum
    # Can be redefined by subclasses to use, for example, DTF variables
    Lc_M_fit_var = "Lambdac_M"
    # Fit range for the Lambda_c mass spectrum
    # It's in this file, rather than the fitter, as it's used in the selection
    Lc_M_lo = 2220.
    Lc_M_hi = 2360.
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new Lc2pXX object.

        Keyword Arguments:
        name -- Name of the TTree this object represents
        year -- Year the ntuple represents (attribute)
        polarity -- Magnet polarity the data were recorded with (attribute)
        mc -- Is the ntuple Monte Carlo data
        """
        log.info("Initialising Lc2pXX")
        super(Lc2pXX, self).__init__(name)
        self.year = year
        self.polarity = polarity
        self.stripping = config.stripping_years[self.year]
        self.mc = mc

        # Append the Lambdac mass window preselection,
        # which requires an instance of the class
        self.preselection += "&& ({1} < {0} && {0} < {2})".format(
            self.Lc_M_fit_var, self.Lc_M_lo, self.Lc_M_hi
        )

    @classmethod
    def from_ntuple(cls, ntuple):
        """Instantiate a new Lc2pXX from an existing one."""
        return cls(
            ntuple.GetName(), ntuple.polarity, ntuple.year, ntuple.mc
        )

    @classmethod
    def from_tree(cls, tree, polarity, year, mc=False):
        """Instantiate a new Lc2pXX from a TTree."""
        ntuple = cls(tree.GetName(), polarity, year, mc)
        # ROOT gymnastics
        ntuple.add(tree.GetCurrentFile().GetEndpointUrl().GetFile())
        return ntuple

    def __str__(self):
        """Filesystem-safe string describing this ntuple.

        Useful for identifying saved friend trees, plots, etc.
        The format of the string is {mode}-{year}-{stripping}-{polarity}.
        """
        s = "{0}-{1}-{2}-{3}".format(
            self.mode, self.year, self.stripping, self.polarity
        )
        if self.mc:
            s += "-mc"
        return s

    def trigger_requirements(self):
        """Return cut string of trigger requirements.

        Equal across all modes, dependent on stripping version as S17b
        ntuples have branch names in different formats.
        """
        return "({0})&&({1})&&({2})".format(
            "mu_L0MuonDecision_TOS",
            "mu_Hlt1TrackMuonDecision_TOS",
            "||".join([
                "Lambdab_Hlt2TopoMu2BodyBBDTDecision_TOS",
                "Lambdab_Hlt2TopoMu3BodyBBDTDecision_TOS",
                "Lambdab_Hlt2TopoMu4BodyBBDTDecision_TOS"
            ])
        )

    def passes_trigger(self):
        """Return True if current event passes trigger requirements."""
        l0 = self.val("mu_L0MuonDecision_TOS")
        hlt1 = self.val("mu_Hlt1TrackMuonDecision_TOS")
        hlt2 = (self.val("Lambdab_Hlt2TopoMu2BodyBBDTDecision_TOS") or
            self.val("Lambdab_Hlt2TopoMu3BodyBBDTDecision_TOS") or
            self.val("Lambdab_Hlt2TopoMu4BodyBBDTDecision_TOS"))
        return l0 and hlt1 and hlt2

    def passes_specific_preselection(self):
        """Return True if current event passes mode-specific preselection.

        To be implemented by child classes
        """
        log.error("Base Lc2pXX.passes_specific_offline_cuts called.")
        return True

    # This string should contain the equivalent cuts to the
    # passes_preselection method.
    # This should be overridden by child classes, appending the parent, e.g.
    #     class Lc2pYZ(Lc2pXX):
    #         preselection = "(0) && (cut<5)".format(Lc2pXX.preselection)
    # It is used in the creation of the meta friend tree.
    preselection = "&&".join([
        "5e3 < proton_P && proton_P < 1e5",
        "2.0 < proton_ETA && proton_ETA < 4.5",
        "nTracks > 0",
        "nTracks < 500",
        "proton_P > 9.3e3",
        "(proton_P > 15.6e3 || proton_ETA < 3.875)",
        "(proton_P < 29.8e3 || proton_ETA > 2.625)",
        "(proton_P < 51.4e3 || proton_ETA > 3.25)"
    ])
    def passes_preselection(self):
        """Return True if current event passes preselection cuts."""
        # Lc mass window cut prevents poor fitting due to outliers
        lc_mass = self.Lc_M_lo < self.val(self.Lc_M_fit_var) < self.Lc_M_hi
        # Proton momenta 5 < p < 100 GeV, eta 2 < n < 4.5
        # These are the limits imposed on the PID calibration samples,
        # so we must implement them too
        proton_P = self.val("proton_P")
        proton_ETA = self.val("proton_ETA")
        nTracks = self.val("nTracks")
        proton_veto = (
            (5e3 < proton_P < 1e5) and
            (2.0 < proton_ETA < 4.5) and
            (0 < nTracks < 500) and
            # Vetoes due to lack of PID calibration data in these regions
            (proton_P > 9.3e3) and
            (proton_P > 15.6e3 or proton_ETA < 3.875) and
            (proton_P < 29.8e3 or proton_ETA > 2.625) and
            (proton_P < 51.4e3 or proton_ETA > 3.25)
        )
        return (
            lc_mass and
            proton_veto and
            self.passes_specific_preselection()
        )

    def passes_offline_cuts(self):
        """Return True if the current event passes the offline selection
        criteria, excluding PID."""
        presel = self.passes_preselection()
        specific = self.passes_specific_offline_cuts()
        return presel and specific

    def passes_specific_offline_cuts(self):
        """Return True if the current event passes the offline selection
        criteria specific to an Lc decay modes.

        To be implemented by child classes.
        """
        log.error("Base Lc2pXX.passes_specific_offline_cuts called.")
        return True

    def passes_pid_cuts(self):
        """Return True if the current event passes PID selection criteria
        specific to an Lc decay modes.

        To be implemented by child classes.
        """
        log.error("Base Lc2pXX.passes_pid_cuts called.")
        return True

    def passes_selection(self):
        """Return True if the current event passes full selection."""
        trigger = self.passes_trigger()
        offline = self.passes_offline_cuts()
        pid = self.passes_pid_cuts()
        return trigger and offline and pid

    def activate_selection_branches(self):
        """Activate all branches required for selection."""
        branches = self.mode_selection_branches + [
            "Lambdac_M",
            # Doesn't matter if it's a duplicate, so add it just in case
            self.Lc_M_fit_var,
            "mu_P",
            "mu_ETA",
            "proton_P",
            "proton_ETA",
            "proton_ProbNNp",
            "proton_ProbNNk",
            "proton_ProbNNpi",
            "proton_PIDp",
            "proton_PIDK",
            "proton_PIDe",
            "proton_PIDmu",
            "h1_P",
            "h1_ETA",
            "h1_ProbNNp",
            "h1_ProbNNk",
            "h1_ProbNNpi",
            "h1_PIDp",
            "h1_PIDK",
            "h1_PIDe",
            "h1_PIDmu",
            "h2_P",
            "h2_ETA",
            "h2_ProbNNp",
            "h2_ProbNNk",
            "h2_ProbNNpi",
            "h2_PIDp",
            "h2_PIDK",
            "h2_PIDe",
            "h2_PIDmu",
            "mu_L0MuonDecision_TOS",
            "mu_Hlt1TrackMuonDecision_TOS",
            "Lambdab_Hlt2TopoMu2BodyBBDTDecision_TOS",
            "Lambdab_Hlt2TopoMu3BodyBBDTDecision_TOS",
            "Lambdab_Hlt2TopoMu4BodyBBDTDecision_TOS",
            "nTracks"
        ]
        if self.mc:
            # Background categories described in IBackgroundCategory
            # http://cern.ch/go/BJQ8
            branches += [
                "Lambdab_BKGCAT",
                "Lambdac_BKGCAT"
            ]
        # Only activate MetaTree branches if tree is attached
        if self.GetFriend(config.metatree_name) != None:
            branches += [
                "signal_sw",
                "background_sw",
                "accepted",
                "triggered",
                "h1_h2_M",
                "p_h1_M",
                "p_h2_M"
            ]
        self.activate_branches(branches)


class Lc2pKpi(Lc2pXX):
    """Wrapper class for Lc to pKpi decay ntuples."""
    mode = config.pKpi
    shapes_preselection = ("GCB", "EXP")
    shapes_postselection = ("GCB", "EXP")
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pKpi")
        super(Lc2pKpi, self).__init__(name, polarity, year, mc)

    preselection = "({0}) && ({1})".format(
        Lc2pXX.preselection,
        "&&".join([
            "5e3 < h1_P && h1_P < 1e5",
            "2.0 < h1_ETA && h1_ETA < 4.5",
            "5e3 < h2_P && h2_P < 1e5",
            "2.0 < h2_ETA && h2_ETA < 4.5",
            "nTracks > 0",
            "nTracks < 500"
        ])
    )
    def passes_specific_preselection(self):
        """Return True if current event passes mode-specific preselection.
        """
        h1_veto = 5e3 < self.val("h1_P") < 1e5
        h1_veto = h1_veto and 2.0 < self.val("h1_ETA") < 4.5
        h2_veto = 5e3 < self.val("h2_P") < 1e5
        h2_veto = h2_veto and 2.0 < self.val("h2_ETA") < 4.5
        nTracks = 0 < self.val("nTracks") < 500
        return h1_veto and h2_veto and nTracks

    def passes_specific_offline_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        return True

    def passes_pid_cuts(self):
        """True if current event passes mode-specific PID criteria."""
        if config.use_probnn:
            proton = self.val("proton_ProbNNp") > 0.5
            h1 = self.val("h1_ProbNNk") > 0.5
            h2 = self.val("h2_ProbNNpi") > 0.7
            pid = proton and h1 and h2
        else:
            proton_K = self.val("proton_PIDp") - self.val("proton_PIDK") > 9.
            proton_pi = self.val("proton_PIDp") > 20.
            h1 = self.val("h1_PIDK") > 10.
            h2 = self.val("h2_PIDK") < 10.
            pid = proton_K and proton_pi and h1 and h2
        return pid


class Lc2pKK(Lc2pXX):
    """Wrapper class for Lc to pKK decay ntuples."""
    mode = config.pKK
    shapes_preselection = ("SGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pKK")
        super(Lc2pKK, self).__init__(name, polarity, year, mc)

    preselection = "({0}) && ({1})".format(
        Lc2pXX.preselection,
        "&&".join([
            "5e3 < h1_P && h1_P < 1e5",
            "2.0 < h1_ETA && h1_ETA < 4.5",
            "5e3 < h2_P && h2_P < 1e5",
            "2.0 < h2_ETA && h2_ETA < 4.5",
            "nTracks > 0",
            "nTracks < 500"
        ])
    )
    def passes_specific_preselection(self):
        """Return True if current event passes mode-specific preselection.
        """
        h1_veto = 5e3 < self.val("h1_P") < 1e5
        h1_veto = h1_veto and 2.0 < self.val("h1_ETA") < 4.5
        h2_veto = 5e3 < self.val("h2_P") < 1e5
        h2_veto = h2_veto and 2.0 < self.val("h2_ETA") < 4.5
        nTracks = 0 < self.val("nTracks") < 500
        return h1_veto and h2_veto and nTracks

    def passes_specific_offline_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        return True

    def passes_pid_cuts(self):
        """True if current event passes mode-specific PID criteria."""
        if config.use_probnn:
            proton = self.val("proton_ProbNNp") > 0.5
            h1 = self.val("h1_ProbNNk") > 0.5
            h2 = self.val("h2_ProbNNk") > 0.5
            pid = proton and h1 and h2
        else:
            proton_K = self.val("proton_PIDp") - self.val("proton_PIDK") > 9.
            proton_pi = self.val("proton_PIDp") > 20.
            h1 = self.val("h1_PIDK") > 10.
            h2 = self.val("h2_PIDK") > 10.
            pid = proton_K and proton_pi and h1 and h2
        return pid


class Lc2ppipi(Lc2pXX):
    """Wrapper class for Lc to ppipi decay ntuples."""
    mode = config.ppipi
    shapes_preselection = ("SGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2ppipi")
        super(Lc2ppipi, self).__init__(name, polarity, year, mc)

    preselection = "({0}) && ({1})".format(
        Lc2pXX.preselection,
        "&&".join([
            "5e3 < h1_P && h1_P < 1e5",
            "2.0 < h1_ETA && h1_ETA < 4.5",
            "5e3 < h2_P && h2_P < 1e5",
            "2.0 < h2_ETA && h2_ETA < 4.5",
            "nTracks > 0",
            "nTracks < 500"
        ])
    )
    def passes_specific_preselection(self):
        """Return True if current event passes mode-specific preselection.
        """
        h1_veto = 5e3 < self.val("h1_P") < 1e5
        h1_veto = h1_veto and 2.0 < self.val("h1_ETA") < 4.5
        h2_veto = 5e3 < self.val("h2_P") < 1e5
        h2_veto = h2_veto and 2.0 < self.val("h2_ETA") < 4.5
        nTracks = 0 < self.val("nTracks") < 500
        return h1_veto and h2_veto and nTracks

    def passes_specific_offline_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        h1_h2_M = self.val("h1_h2_M")
        # Require pi+pi- invariant mass outside KS window
        ks = h1_h2_M < 480. or h1_h2_M > 520.
        return ks

    def passes_pid_cuts(self):
        """True if current event passes mode-specific PID criteria."""
        if config.use_probnn:
            proton = self.val("proton_ProbNNp") > 0.5
            h1 = self.val("h1_ProbNNpi") > 0.7
            h2 = self.val("h2_ProbNNpi") > 0.7
            pid = proton and h1 and h2
        else:
            proton_K = self.val("proton_PIDp") - self.val("proton_PIDK") > 9.
            proton_pi = self.val("proton_PIDp") > 20.
            h1 = self.val("h1_PIDK") < 0.
            h2 = self.val("h2_PIDK") < 0.
            pid = proton_K and proton_pi and h1 and h2
        return pid


class Lc2pKSLL(Lc2pXX):
    """Wrapper class for Lc to pKS (long-long KS to pipi) decay ntuples."""
    mode = config.pKSLL
    shapes_preselection = ("DGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    Lc_M_fit_var = "Lambdab_DTF_Lambdac_M"
    mode_selection_branches = [
        "Lambdab_DTF_CHI2"
    ]
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pKSLL")
        super(Lc2pKSLL, self).__init__(name, polarity, year, mc)

    # Although there are no offline PID cuts on the pions, there are
    # still the stripping DLL cuts, and these still need calibration
    preselection = "({0}) && ({1})".format(
        Lc2pXX.preselection,
        "&&".join([
            "5e3 < h1_P && h1_P < 1e5",
            "2.0 < h1_ETA && h1_ETA < 4.5",
            "5e3 < h2_P && h2_P < 1e5",
            "2.0 < h2_ETA && h2_ETA < 4.5",
            "nTracks > 0",
            "nTracks < 500"
        ])
    )
    def passes_specific_preselection(self):
        """Return True if current event passes mode-specific preselection.
        """
        h1_veto = 5e3 < self.val("h1_P") < 1e5
        h1_veto = h1_veto and 2.0 < self.val("h1_ETA") < 4.5
        h2_veto = 5e3 < self.val("h2_P") < 1e5
        h2_veto = h2_veto and 2.0 < self.val("h2_ETA") < 4.5
        nTracks = 0 < self.val("nTracks") < 500
        fit_quality = self.val("Lambdab_DTF_CHI2") >= 0
        return h1_veto and h2_veto and nTracks and fit_quality

    def passes_specific_offline_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        return True

    def passes_pid_cuts(self):
        """True if current event passes mode-specific PID criteria."""
        return True


class Lc2pKSDD(Lc2pXX):
    """Wrapper class for Lc to pKS (down-down KS to pipi) decay ntuples."""
    mode = config.pKSDD
    shapes_preselection = ("DGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    Lc_M_fit_var = "Lambdab_DTF_Lambdac_M"
    mode_selection_branches = [
        "Lambdab_DTF_CHI2"
    ]
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pKSDD")
        super(Lc2pKSDD, self).__init__(name, polarity, year, mc)

    # Although there are no offline PID cuts on the pions, there are
    # still the stripping DLL cuts, and these still need calibration
    preselection = "({0}) && ({1})".format(
        Lc2pXX.preselection,
        "&&".join([
            "5e3 < h1_P && h1_P < 1e5",
            "2.0 < h1_ETA && h1_ETA < 4.5",
            "5e3 < h2_P && h2_P < 1e5",
            "2.0 < h2_ETA && h2_ETA < 4.5",
            "nTracks > 0",
            "nTracks < 500"
        ])
    )
    def passes_specific_preselection(self):
        """Return True if current event passes mode-specific preselection.

        To be implemented by child classes
        """
        h1_veto = 5e3 < self.val("h1_P") < 1e5
        h1_veto = h1_veto and 2.0 < self.val("h1_ETA") < 4.5
        h2_veto = 5e3 < self.val("h2_P") < 1e5
        h2_veto = h2_veto and 2.0 < self.val("h2_ETA") < 4.5
        nTracks = 0 < self.val("nTracks") < 500
        fit_quality = self.val("Lambdab_DTF_CHI2") >= 0
        return h1_veto and h2_veto and nTracks and fit_quality

    def passes_specific_offline_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        return True

    def passes_pid_cuts(self):
        """True if current event passes mode-specific PID criteria."""
        return True


class Lc2pphi(Lc2pKK):
    """Wrapper class for Lc to pphi decay ntuples.

    Subclass of Lc2pKK as the final states are identical.
    """
    mode = config.pphi
    shapes_preselection = ("SGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    def __init__(self, name, polarity, year, mc=False):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pphi")
        super(Lc2pphi, self).__init__(name, polarity, year, mc)
