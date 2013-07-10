from Configurables import (
    DaVinci,
    FilterDesktop,
    GaudiSequencer,
    DecayTreeTuple
)
from DecayTreeTuple.Configuration import *

from lc2pxx import config
from lc2pxx.booking import davinci, tuple_templates

year = 2011
mc = False

davinci.configure(year, mc)

lines = {
    "LcTo{0}".format(config.pKpi): {
        "stripping": "b2LcMuXCharmFromBSemiLine",
        "tracks": ("K-", "pi+", "mu-")
    },
    "LcTo{0}WS".format(config.pKpi): {
        "stripping": "b2LcMuXCharmFromBSemiLine",
        "tracks": ("K-", "pi+", "mu+")
    },
    "LcTo{0}".format(config.pKK): {
        "stripping": "b2Lc2pKKMuXCharmFromBSemiLine",
        "tracks": ("K-", "K+", "mu-")
    },
    "LcTo{0}WS".format(config.pKK): {
        "stripping": "b2Lc2pKKMuXCharmFromBSemiLine",
        "tracks": ("K-", "K+", "mu+")
    },
    "LcTo{0}".format(config.ppipi): {
        "stripping": "b2Lc2pPiPiMuXCharmFromBSemiLine",
        "tracks": ("pi-", "pi+", "mu-")
    },
    "LcTo{0}WS".format(config.ppipi): {
        "stripping": "b2Lc2pPiPiMuXCharmFromBSemiLine",
        "tracks": ("pi-", "pi+", "mu+")
    }
}

# Lambda_c mass window of 75 MeV around the nominal PDG mass
filter_template = FilterDesktop(
    "FilterOfflineLc2phh",
    Code="(MINTREE(ABSID=='Lambda_c+', ADMASS('Lambda_c+')) < 75*MeV)"
)

inputs_template = "Phys/{0}/Particles"
decay_template = "[Lambda_b0 -> (^Lambda_c+ -> ^p+ ^{0} ^{1}) ^{2}]cc"
mother_templates = {
    "Lambdab": "[Lambda_b0]cc: [Lambda_b0 -> (Lambda_c+ -> p+ {0} {1}) {2}]cc",
    "Lambdac": "[Lambda_b0 -> (^Lambda_c+ -> p+ {0} {1}) {2}]cc",
}
daughter_templates = {
    "mu": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} {1}) ^{2}]cc",
    "h1": "[Lambda_b0 -> (Lambda_c+ -> p+ ^{0} {1}) {2}]cc",
    "h2": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} ^{1}) {2}]cc",
    "proton": "[Lambda_b0 -> (Lambda_c+ -> ^p+ {0} {1}) {2}]cc"
}

for line in lines:
    stripping = lines[line]["stripping"]
    tracks = lines[line]["tracks"]

    filter_name = "FilterOffline{0}".format(line)
    filter = filter_template.clone(filter_name)
    filter.Inputs = [inputs_template.format(stripping)]

    # Fill the branch templates with the appropriate particles
    mothers = {}
    daughters = {}
    for mother in mother_templates:
        mothers[mother] = mother_templates[mother].format(*tracks)
    for daughter in daughter_templates:
        daughters[daughter] = daughter_templates[daughter].format(*tracks)

    # Create a tuple for the mode
    tuple = tuple_templates.decay_tree_tuple(
        "Tuple{0}".format(line),
        decay_template.format(*tracks),
        mothers,
        daughters,
        # The input to the tuple is the output of the filter
        inputs_template.format(filter_name),
        mc
    )
    # Refit the decay tree, storing refitted daughter information
    dtf = tuple.Lambdab.addTupleTool("TupleToolDecayTreeFitter/Fit")
    dtf.Verbose = True

    # Sequence to hold a succession of algorithms
    sequence = GaudiSequencer("SequenceBook{0}".format(line))
    sequence.Members = [filter, tuple]

    DaVinci().UserAlgorithms.append(sequence)

