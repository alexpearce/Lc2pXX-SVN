from Configurables import (
    DaVinci,
    GaudiSequencer
)

from lc2pxx import config
from lc2pxx.booking import davinci, tuple_templates, b2lc_stream

year = 2011
mc = True

davinci.configure(year, mc)

# Add the CharmFromBSemiNoPIDs lines
DaVinci().appendToMainSequence(b2lc_stream.stripping_sequence_nopids())

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

inputs_template = "Phys/{0}/Particles"
decay_template = "[Lambda_b0 --> ^(Lambda_c+ --> ^p+ ^{0} ^{1}) ^{2}]CC"
mother_templates = {
    "Lambdab": "[^(Lambda_b0 --> (Lambda_c+ --> p+ {0} {1}) {2})]CC",
    "Lambdac": "[Lambda_b0 --> ^(Lambda_c+ --> p+ {0} {1}) {2}]CC"
}
daughter_templates = {
    "mu": "[Lambda_b0 --> (Lambda_c+ --> p+ {0} {1}) ^{2}]CC",
    "proton": "[Lambda_b0 --> (Lambda_c+ --> ^p+ {0} {1}) {2}]CC",
    "h1": "[Lambda_b0 --> (Lambda_c+ --> p+ ^{0} {1}) {2}]CC",
    "h2": "[Lambda_b0 --> (Lambda_c+ --> p+ {0} ^{1}) {2}]CC"
}

mc_decay_template = "[Lambda_b0 => ^(Lambda_c+ ==> ^p+ ^{0} ^{1} ) ^{2} nu_mu~]CC"
mc_mother_templates = {
    "Lambdab": "[^(Lambda_b0 => (Lambda_c+ ==> p+ {0} {1}) {2} nu_mu~)]CC",
    "Lambdac": "[Lambda_b0 => ^(Lambda_c+ ==> p+ {0} {1}) {2} nu_mu~]CC"
}
mc_daughter_templates = {
    "mu": "[Lambda_b0 => (Lambda_c+ ==> p+ {0} {1}) ^{2} nu_mu~]CC",
    "proton": "[Lambda_b0 => (Lambda_c+ ==> ^p+ {0} {1}) {2} nu_mu~]CC",
    "h1": "[Lambda_b0 => (Lambda_c+ ==> p+ ^{0} {1}) {2} nu_mu~]CC",
    "h2": "[Lambda_b0 => (Lambda_c+ ==> p+ {0} ^{1}) {2} nu_mu~]CC"
}

for line in lines:
    stripping = lines[line]["stripping"]
    tracks = lines[line]["tracks"]

    # Fill the branch templates with the appropriate particles
    mothers = {}
    daughters = {}
    mc_mothers = {}
    mc_daughters = {}
    for m in mother_templates:
        mothers[m] = mother_templates[m].format(*tracks)
    for d in daughter_templates:
        daughters[d] = daughter_templates[d].format(*tracks)
    for m in mc_mother_templates:
        mc_mothers[m] = mc_mother_templates[m].format(*tracks)
    for d in mc_daughter_templates:
        mc_daughters[m] = mc_daughter_templates[d].format(*tracks)

    # Create a tuple for the mode
    tuple = tuple_templates.decay_tree_tuple(
        "Tuple{0}".format(line),
        decay_template.format(*tracks),
        mothers,
        daughters,
        # The input to the tuple is the output of the filter
        inputs_template.format(stripping),
        mc
    )

    # MCDecayTreeTuple
    mc_tuple = tuple_templates.mc_decay_tree_tuple(
        "MCGenTuple{0}".format(line),
        mc_decay_template.format(*tracks),
        mc_mothers,
        mc_daughters
    )

    # Sequences for ntuple creation
    dec_sequence = GaudiSequencer("SeqBook{0}".format(line))
    dec_sequence.Members = [tuple]
    mc_sequence = GaudiSequencer("SeqMCGenBook{0}".format(line))
    mc_sequence.Members = [mc_tuple]

    # Sequence for ntuple sequences
    tuples_sequence = GaudiSequencer("SeqTuples{0}".format(line))
    tuples_sequence.IgnoreFilterPassed = True
    tuples_sequence.Members = [dec_sequence, mc_sequence]

    DaVinci().UserAlgorithms.append(tuples_sequence)

