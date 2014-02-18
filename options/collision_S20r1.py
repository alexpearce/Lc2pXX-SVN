"""
2011 collision DaVinci options file for creating ntuples for the decay chain
    [Lambda_b0 -> (Lambda_c+ -> f) mu-]CC
where the Lambda_c+ decay mode f is one of
    p+ K- pi+
    p+ K- K+
    p+ pi- pi+
The first is Cabibbo-favoured, the others are singly Cabibbo-suppressed.
"""
from Configurables import DaVinci
from DecayTreeTuple.Configuration import *

from helpers import davinci, tuple_templates

year = 2011
mc = False

davinci.configure(2011, False)

lines = {
    "LcTopKpi": {
        "stripping": "b2LcMuXCharmFromBSemiLine",
        "tracks": ("K-", "pi+", "mu-")
    },
    "LcTopKK": {
        "stripping": "b2Lc2pKKMuXCharmFromBSemiLine",
        "tracks": ("K-", "K+", "mu-")
    },
    "LcToppipi": {
        "stripping": "b2Lc2pPiPiMuXCharmFromBSemiLine",
        "tracks": ("pi-", "pi+", "mu-")
    }
}

inputs_template = "Phys/{0}/Particles"
decay_template = "[Lambda_b0 -> ^(Lambda_c+ -> ^p+ ^{0} ^{1}) ^{2}]CC"
mothers_templates = {
    "Lambdab": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} {1}) {2}]CC",
    "Lambdac": "[Lambda_b0 -> ^(Lambda_c+ -> p+ {0} {1}) {2}]CC",
}
daughters_templates = {
    "mu": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} {1}) ^{2}]CC",
    "h1": "[Lambda_b0 -> (Lambda_c+ -> p+ ^{0} {1}) {2}]CC",
    "h2": "[Lambda_b0 -> (Lambda_c+ -> p+ {0} ^{1}) {2}]CC",
    "proton": "[Lambda_b0 -> (Lambda_c+ -> ^p+ {0} {1}) {2}]CC"
}

for line in lines:
    stripping = lines[line]["stripping"]
    tracks = lines[line]["tracks"]

    # Fill the branch templates with the appropriate particles
    mothers = {}
    daughters = {}
    for mother in mothers_templates:
        mothers[mother] = mothers_templates[mother].format(*tracks)
    for daughter in daughters_templates:
        daughters[daughter] = daughters_templates[daughter].format(*tracks)

    # Create a tuple for the mode
    t = tuple_templates.lc2pxx_tuple(
        "Tuple{0}".format(line),
        decay_template.format(*tracks),
        mothers,
        daughters,
        inputs_template.format(stripping),
        mc
    )

    DaVinci().UserAlgorithms.append(t)

