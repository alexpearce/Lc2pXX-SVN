from Configurables import (
    DecayTreeTuple,
    MCDecayTreeTuple,
    MCDecayFinder
)
from DecayTreeTuple.Configuration import *

def decay_tree_tuple(name, decay, mothers, daughters, inputs, mc=False):
    """Return a configured DecayTreeTuple instance.

    A DecayTreeTuple is configured with the given decay descriptor.
    The mothers dictionary is used to give exclusive tools to vertices,
    and it should be, as daughters, a dictionary of tuple branche names
    to branch descriptors. A typical call to this method might look like
        decay_tree_tuple(
            "TupleLc2pKK",
            "[Lambda_c+ -> ^p+ ^K- ^K+]cc",
            {
                "Lambdac": "[Lambda_c+]cc: [Lambda_c+ -> p+ %s %s]cc"
            },
            {
                "h1": "[Lambda_c+ -> p+ ^K- K+]cc",
                "h2": "[Lambda_c+ -> p+ K- ^K+]cc",
                "proton": "[Lambda_c+ -> ^p+ K- K+]cc"
            },
            "Phys/MyStrippingLine/Particles"
        )
    Keyword arguments:
    name -- TFile folder the DecayTree ntuple will be saved to
    decay -- LoKi-style decay finder (http://cern.ch/go/9bHt)
    mothers -- Branch descriptors to be added to the tuple as mothers,
        decaying particles
    daughters -- Branch descriptors to be added to the tuple as daughters,
        products of mother decays which are not themselves mothers
    branches -- Dictionary of branches to store in the ntuple
    inputs -- str or list of strs, as the value of DecayTreeTuple.Inputs
    mc -- If True, include some useful MC tuple tools
    """
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
    triggers = [
        "L0HadronDecision",
        "L0MuonDecision",
        "Hlt1TrackAllL0Decision",
        "Hlt1SingleMuonNoIPDecision",
        "Hlt1SingleMuonHighPTDecision",
        "Hlt1TrackMuonDecision",
        "Hlt2TopoMu2BodyBBDTDecision",
        "Hlt2TopoMu3BodyBBDTDecision",
        "Hlt2TopoMu4BodyBBDTDecision",
        "Hlt2Topo2BodyBBDTDecision",
        "Hlt2Topo3BodyBBDTDecision",
        "Hlt2Topo4BodyBBDTDecision",
        "Hlt2SingleMuonDecision",
        "Hlt2CharmHadD2HHHDecision"
    ]
    basic_loki_vars = {
        "ETA": "ETA",
        "Loki_MIPCHI2DV": "MIPCHI2DV(PRIMARY)",
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
    tuple_template = DecayTreeTuple(name)
    tuple_template.Inputs = inputs if type(inputs) is list else [inputs]
    tuple_template.Decay = decay
    # Merge the mother and daughter dictionaries
    tuple_template.addBranches(dict(mothers.items() + daughters.items()))
    # Tools for all branches
    tuple_template.ToolList = tuple_tools
    # Verbose reconstruction information
    tuple_template.addTupleTool("TupleToolRecoStats").Verbose = True
    # TISTOS trigger information
    tistos = tuple_template.addTupleTool("TupleToolTISTOS")
    tistos.TriggerList = triggers
    tistos.Verbose = True
    # Extra information from LoKi
    tuple_template.addTupleTool(
        "LoKi::Hybrid::TupleTool/basicLokiTT"
    ).Variables = basic_loki_vars
    for mother in mothers:
        m = getattr(tuple_template, mother)
        m.addTupleTool(
            "LoKi::Hybrid::TupleTool/{0}LokiTT".format(mother)
        ).Variables = mother_loki_vars
        if mc:
            # BKGCAT
            m.addTupleTool("TupleToolMCBackgroundInfo")

    return tuple_template


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
    tuple.addTool(MCDecayFinder())
    tuple.MCDecayFinder.ResonanceThreshold = 5e-10
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

