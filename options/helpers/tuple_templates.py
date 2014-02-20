from DecayTreeTuple.Configuration import *

def decay_tree_tuple(name, decay, mothers, daughters, inputs, mc):
    """Return a configured DecayTreeTuple instance.

    A DecayTreeTuple is configured with the given decay descriptor.
    The mothers dictionary is used to give exclusive tools to vertices,
    and it should be, as daughters, a dictionary of tuple branch names
    to branch descriptors. A typical call to this method might look like
        decay_tree_tuple(
            "TupleLc2pKK",
            "[Lambda_c+ -> ^p+ ^K- ^K+]CC",
            {
                "Lambdac": "[Lambda_c+ -> p+ K- K+]CC"
            },
            {
                "h1": "[Lambda_c+ -> p+ ^K- K+]CC",
                "h2": "[Lambda_c+ -> p+ K- ^K+]CC",
                "proton": "[Lambda_c+ -> ^p+ K- K+]CC"
            },
            "Phys/MyStrippingLine/Particles"
        )
    Keyword arguments:
    name -- TDirectory the DecayTree ntuple will be saved to
    decay -- LoKi-style decay finder (http://cern.ch/go/9bHt)
    mothers -- Branch descriptors to be added to the tuple as mothers,
        decaying particles
    daughters -- Branch descriptors to be added to the tuple as daughters,
        products of mother decays which are not themselves mothers
    inputs -- str or list of strs, as the value of DecayTreeTuple.Inputs
    mc -- If True, include some useful MC tuple tools
    """
    # Define tuple tools to add
    tuple_tools = [
        "TupleToolEventInfo",
        "TupleToolGeometry",
        "TupleToolKinematic",
        "TupleToolPid",
        "TupleToolPrimaries",
        "TupleToolTrackInfo"
    ]
    if mc:
        tuple_tools += [
            "TupleToolMCTruth"
        ]

    # Extra variables, added using LoKi hybrid tuple tools
    basic_loki_vars = {
        "ETA": "ETA",
        "Loki_BPVIPCHI2": "BPVIPCHI2()"
    }
    mother_loki_vars = {
        "Loki_BPVVDCHI2": "BPVVDCHI2",
        "Loki_BPVIPCHI2": "BPVIPCHI2()",
        "Loki_DOCAMAX": "DOCAMAX",
        "Loki_DOCACHI2MAX": "DOCACHI2MAX",
        "Loki_VCHI2": "VFASPF(VCHI2)",
        "Loki_VDOF": "VFASPF(VDOF)",
        "Loki_VX": "VFASPF(VX)",
        "Loki_VY": "VFASPF(VY)",
        "Loki_VZ": "VFASPF(VZ)",
        "Loki_SUMPT": "SUMTREE(PT,  ISBASIC)",
        "Loki_BPVLTIME": "BPVLTIME('PropertimeFitter/properTime:PUBLIC')"
    }

    # Template DecayTreeTuple
    t = DecayTreeTuple(name)
    # DecayTreeTuple.Inputs takes a list, but inputs might be a string
    # So try assign it, but wrap it in a list if we get a ValueError
    try:
        t.Inputs = inputs
    except ValueError:
        t.Inputs = [inputs]
    t.Decay = decay
    # Merge the mother and daughter dictionaries
    t.addBranches(dict(mothers.items() + daughters.items()))
    # Tools for all branches
    t.ToolList = tuple_tools
    # Verbose reconstruction information
    t.addTupleTool("TupleToolRecoStats").Verbose = True
    # Extra information from LoKi
    t.addTupleTool(
        "LoKi::Hybrid::TupleTool/basicLokiTT"
    ).Variables = basic_loki_vars
    # For each mother branch, add the LoKi tuple tool that adds mother-specific
    # vars
    for mother in mothers:
        m = getattr(t, mother)
        m.addTupleTool(
            "LoKi::Hybrid::TupleTool/{0}LokiTT".format(mother)
        ).Variables = mother_loki_vars
        if mc:
            # BKGCAT
            m.addTupleTool("TupleToolMCBackgroundInfo")

    return t


def lc2pxx_tuple(name, decay, mothers, daughters, inputs, mc=False):
    """Return a DecayTreeTuple suitable for an Lc2pXX analysis.

    See decay_tree_tuple for argument documentation.
    This tuple tool adds the trigger lines and some Lambda_c+ daughter pair masses.
    """
    t = decay_tree_tuple(name, decay, mothers, daughters, inputs, mc)
    muon_triggers = [
        "L0MuonDecision",
        "Hlt1TrackMuonDecision"
    ]
    lambdab_triggers = [
        "Hlt2TopoMu2BodyBBDTDecision",
        "Hlt2TopoMu3BodyBBDTDecision",
        "Hlt2TopoMu4BodyBBDTDecision",
        "Hlt2SingleMuonDecision"
    ]
    # TISTOS trigger information
    lambdab_tt = t.Lambdab.addTupleTool("TupleToolTISTOS")
    lambdab_tt.TriggerList = lambdab_triggers
    lambdab_tt.Verbose = True
    mu_tt = t.mu.addTupleTool("TupleToolTISTOS")
    mu_tt.TriggerList = muon_triggers
    mu_tt.Verbose = True
    # Invariant mass for all Lambda_c+ daughter pairs
    t.Lambdac.addTupleTool(
        "LoKi::Hybrid::TupleTool/twoBodyMassesLokiTT"
    ).Variables = {
        "p_h1_M": "MASS(1, 2)",
        "p_h2_M": "MASS(1, 3)",
        "h1_h2_M": "MASS(2, 3)"
    }
    return t


def mc_decay_tree_tuple(name, decay, mothers, daughters):
    """Return a configured MCDecayTreeTuple.

    See decay_tree_tuple for an method call. Unlike decay_tree_tuple,
    we don't require `inputs` because MCDecayTreeTuple doesn't need it.
    Keyword arguments --
    name -- TFile folder the DecayTree ntuple will be saved to
    decay -- LoKi-style decay finder (http://cern.ch/go/9bHt)
    mothers -- Branch descriptors to be added to the tuple as mothers,
        decaying particles
    daughters -- Branch descriptors to be added to the tuple as daughters,
        products of mother decays which are not themselves mothers
    branches -- Dictionary of branches to store in the ntuple
    """
    tuple = MCDecayTreeTuple(name)
    tuple.Decay = decay
    tuple.Branches = dict(mothers.items() + daughters.items())
    tuple.ToolList += [
        "MCTupleToolPID",
        "MCTupleToolKinematic",
        "MCTupleToolReconstructed",
        "MCTupleToolHierarchy",
        # Generation TT causes null event pointer failure
        # "TupleToolGeneration",
        "TupleToolEventInfo",
        "TupleToolPrimaries"
    ]

    return tuple
