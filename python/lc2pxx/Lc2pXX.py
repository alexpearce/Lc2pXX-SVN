import logging as log

from lc2pxx import config, utilities, Ntuple

class Lc2pXX(Ntuple.Ntuple):
    """Ntuple representing all Lambda_c to proton h^+ h^- decays."""
    def __init__(self, name, polarity, year):
        """Initialiser for a new Lc2pXX object.

        Keyword Arguments:
        name -- Name of the TTree this object represents
        year -- Year the ntuple represents (attribute)
        polarity -- Magnet polarity the data were recorded with (attribute)
        """
        log.info("Initialising Lc2pXX")
        super(Lc2pXX, self).__init__(name)
        self.year = year
        self.polarity = polarity
        self.stripping = config.stripping_years[self.year]

    @classmethod
    def from_ntuple(cls, ntuple):
        """Instantiate a new Lc2pXX from an existing one."""
        return cls(ntuple.GetName(), ntuple.polarity, ntuple.year)

    @classmethod
    def from_tree(cls, tree, polarity, year):
        """Instantiate a new Lc2pXX from a TTree."""
        ntuple = cls(tree.GetName(), polarity, year)
        # ROOT gymnastics
        ntuple.add(tree.GetCurrentFile().GetEndpointUrl().GetFile())
        return ntuple

    def __str__(self):
        """Filesystem-safe string describing this ntuple.

        Useful for identifying saved friend trees, plots, etc.
        The format of the string is {mode}-{year}-{stripping}-{polarity}.
        """
        return "{0}-{1}-{2}-{3}".format(
            self.mode, self.year, self.stripping, self.polarity
        )

    def passes_trigger(self):
        """Return True if current event passes trigger requirements."""
        # The 17b ntuples are missing the _ seperator from trigger branches
        if self.stripping == "17b":
            l0 = self.val("muL0MuonDecision_TOS")
            hlt1 = self.val("muHlt1TrackMuonDecision_TOS")
            hlt2 = (self.val("LambdabHlt2TopoMu2BodyBBDTDecision_TOS") or
                self.val("LambdabHlt2TopoMu3BodyBBDTDecision_TOS") or
                self.val("LambdabHlt2TopoMu4BodyBBDTDecision_TOS"))
        else:
            l0 = self.val("mu_L0MuonDecision_TOS")
            hlt1 = self.val("mu_Hlt1TrackMuonDecision_TOS")
            hlt2 = (self.val("Lambdab_Hlt2TopoMu2BodyBBDTDecision_TOS") or
                self.val("Lambdab_Hlt2TopoMu3BodyBBDTDecision_TOS") or
                self.val("Lambdab_Hlt2TopoMu4BodyBBDTDecision_TOS"))
        return l0 and hlt1 and hlt2

    def passes_preselection(self):
        """Return True if current event passes preselection cuts."""
        # Lc mass window cut prevents poor fitting due to outliers
        lc_mass = config.lc_m_low < self.val("Lambdac_M") < config.lc_m_high
        return lc_mass

    def passes_common_cuts(self):
        """Return True if the current event passes selection criteria
        common to all decay modes."""
        # TODO kinematic vetoes, but they might be better in preselection
        presel = self.passes_trigger() and self.passes_preselection()
        probnn = self.val("proton_ProbNNp") > 0.5
        doca = self.val("Lambdac_Loki_DOCAMAX") < 0.4
        vertex = self.val("Lambdac_ENDVERTEX_CHI2") < 15
        return presel and probnn and doca and vertex

    def passes_specific_cuts(self):
        """Return True if the current event passes selection criteria
        specific to an Lc decay modes.

        To be implemented by child classes.
        """
        log.error("Base Lc2pXX.passes_specific_cuts called.")
        return True

    def passes_selection(self):
        """Return True if the current event passes full selection."""
        return self.passes_common_cuts() and self.passes_specific_cuts()

    def activate_selection_branches(self):
        """Activate all branches required for selection."""
        branches = [
            "Lambdac_M",
            "proton_ProbNNp",
            "proton_ProbNNk",
            "proton_ProbNNpi",
            "h1_ProbNNp",
            "h1_ProbNNk",
            "h1_ProbNNpi",
            "h2_ProbNNp",
            "h2_ProbNNk",
            "h2_ProbNNpi",
            "Lambdac_Loki_DOCAMAX",
            "Lambdac_ENDVERTEX_CHI2"
        ]
        if self.stripping == "17b":
            branches += [
                "muL0MuonDecision_TOS",
                "muHlt1TrackMuonDecision_TOS",
                "LambdabHlt2TopoMu2BodyBBDTDecision_TOS",
                "LambdabHlt2TopoMu3BodyBBDTDecision_TOS",
                "LambdabHlt2TopoMu4BodyBBDTDecision_TOS"
            ]
        else:
            branches += [
                "mu_L0MuonDecision_TOS",
                "mu_Hlt1TrackMuonDecision_TOS",
                "Lambdab_Hlt2TopoMu2BodyBBDTDecision_TOS",
                "Lambdab_Hlt2TopoMu3BodyBBDTDecision_TOS",
                "Lambdab_Hlt2TopoMu4BodyBBDTDecision_TOS"
            ]
        # Only activate MetaTree branches if tree is attached
        if self.GetFriend(config.metatree_name) != None:
            branches += [
                "signal_sw",
                "background_sw",
                "accepted",
                "triggered"
            ]
        self.activate_branches(branches)


class Lc2pKpi(Lc2pXX):
    """Wrapper class for Lc to pKpi decay ntuples."""
    mode = config.pKpi
    shapes_preselection = ("DGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    def __init__(self, name, polarity, year):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pKpi")
        super(Lc2pKpi, self).__init__(name, polarity, year)

    def passes_specific_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        h1 = self.val("h1_ProbNNk") > 0.5
        h2 = self.val("h2_ProbNNpi") > 0.7
        probnn = h1 and h2
        return probnn


class Lc2pKK(Lc2pXX):
    """Wrapper class for Lc to pKK decay ntuples."""
    mode = config.pKK
    shapes_preselection = ("SGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    def __init__(self, name, polarity, year):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2pKK")
        super(Lc2pKK, self).__init__(name, polarity, year)

    def passes_specific_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        h1 = self.val("h1_ProbNNk") > 0.5
        h2 = self.val("h2_ProbNNk") > 0.5
        probnn = h1 and h2
        return probnn


class Lc2ppipi(Lc2pXX):
    """Wrapper class for Lc to ppipi decay ntuples."""
    mode = config.ppipi
    shapes_preselection = ("SGS", "EXP")
    shapes_postselection = ("DGS", "EXP")
    def __init__(self, name, polarity, year):
        """Initialiser for a new TChain. See Lc2pXX.__init__"""
        log.info("Initialising Lc2ppipi")
        super(Lc2ppipi, self).__init__(name, polarity, year)

    def passes_specific_cuts(self):
        """True if current event passes mode-specific selection criteria."""
        # TODO pipi inv. mass cut to remove K*
        h1 = self.val("h1_ProbNNpi") > 0.7
        h2 = self.val("h2_ProbNNpi") > 0.7
        probnn = h1 and h2
        return probnn

