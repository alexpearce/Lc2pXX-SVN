from Configurables import DecayTreeTuple
from DecayTreeTuple.Configuration import *

def add_tistos(branch, triggers):
    """Adds the TISTOS tuple tool to the branch.

    Usage:
        tuple = DecayTreeTuple("MyTuple")
        tuple.Decay = "J/psi(1S) -> ^mu- ^mu+"
        tuple.addBranches({"mum": ..., "mup": ...})
        add_tistos(tupleTool.mum, [...])
        add_tistos(tupleTool.mup, [...])
    Keyword arguments:
    branch -- Instance of TupleToolDecay
    triggers -- List of strings of triggers to record TISTOS info for
    """
    tistos = branch.addTupleTool("TupleToolTISTOS")
    tistos.TriggerList = triggers
    tistos.Verbose = True


def decay_tree_tuple(name):
    """Return a configured DecayTreeTuple instance.

    Details.
    """
    decay_descriptor = "[Lambda_b0 -> (^Lambda_c+ -> ^p+ ^{0} ^{1}) ^{2}]cc"
    branches = {
        "Lambdab": "[Lambda_b0]cc: [Lambda_b0 -> (Lambda_c+ -> p+ {0} {1}) {2}]cc",
        "mu": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} {1}) ^{2}]cc",
        "Lambdac": "[Lambda_b0 -> (^Lambda_c+ -> p+ {0} {1}) {2}]cc",
        "h1": "[Lambda_b0 -> (Lambda_c+ -> p+ ^{0} {1}) {2}]cc",
        "h2": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} ^{1}) {2}]cc",
        "proton": "[Lambda_b0 -> (Lambda_c+ -> ^p+ {0} {1}) {2}]cc"
    }
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
    baryon_loki_vars = {
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
    tuple_template.Decay = decay_descriptor
    tuple_template.addBranches(branches)
    # Tools for all branches
    tuple_template.ToolList = [
        "TupleToolEventInfo",
        "TupleToolGeometry",
        "TupleToolKinematic",
        "TupleToolPid",
        "TupleToolPrimaries",
        "TupleToolTrackInfo"
    ]
    # Verbose reconstruction information
    tuple_template.addTupleTool("TupleToolRecoStats").Verbose = True
    # Add triggers to mothers and muon
    add_tistos(tuple_template.Lambdab, triggers)
    add_tistos(tuple_template.Lambdac, triggers)
    add_tistos(tuple_template.mu, triggers)
    # Extra information from LoKi
    tuple_template.addTupleTool(
        "LoKi::Hybrid::TupleTool/basicLokiTT"
    ).Variables = basic_loki_vars
    tuple_template.Lambdab.addTupleTool(
        "LoKi::Hybrid::TupleTool/lbLokiTT"
    ).Variables = baryon_loki_vars
    tuple_template.Lambdac.addTupleTool(
        "LoKi::Hybrid::TupleTool/lcLokiTT"
    ).Variables = baryon_loki_vars

    return tuple_template

