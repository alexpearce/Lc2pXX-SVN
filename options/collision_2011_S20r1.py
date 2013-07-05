from Configurables import DaVinci, FilterDesktop

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

for line in lines:
    stripping = lines[line]["stripping"]
    tracks = lines[line]["tracks"]

    filter_name = "FilterOffline{0}".format(line)
    filter = filter_template.clone(filter_name)
    filter.Inputs = [inputs_template.format(stripping)]

    # Create a tuple for the mode
    tuple = tuple_templates.decay_tree_tuple("Tuple{0}".format(line))
    tuple.Decay = tuple.Decay.format(hads)
    tuple.Inputs = [inputs_template.format(filter_name)]
    for b in tuple.Branches:
        # The star unpacks the tuple, neat!
        tuple.Branches[b] = tuple.Branches[b].format(*tracks)

    # Sequence to hold a succession of algorithms
    sequence = GaudiSequencer("SequenceBook{0}".format(line))
    sequence.Members = [filter, tuple]

    DaVinci().UserAlgorithms.append(sequence)

