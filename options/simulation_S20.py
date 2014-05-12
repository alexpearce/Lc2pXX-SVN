"""
DaVinci options file for creating Monte Carlo ntuples for the decay chain
    [Lambda_b0 -> (Lambda_c+ -> f) mu-]CC
where the Lambda_c+ decay mode f (with event type number) is one of
    p+ K- pi+  (15874000)
    p+ K- K+   (15674000)
    p+ pi- pi+ (15674010)
The first is Cabibbo-favoured, the others are singly Cabibbo-suppressed.
Two ntuples are created
    1. Generator level Monte Carlo events
    2. Stripped and reconstructed events
The first ntuple contains one row per generated event.
The second contains one row per reconstructed decay, which has passed a modified
version of the stripping, identical to the usual but with out PID applied.
"""
from Configurables import DaVinci, GaudiSequencer

from helpers import tuple_templates, b2lc_stream

# Add the CharmFromBSemiNoPIDs lines
DaVinci().appendToMainSequence(b2lc_stream.stripping_sequence_nopids())

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

# Use ==> arrow to capture all intermediate resonances and ignore photons
mc_decay_template = "[Lambda_b0 ==> ^(Lambda_c+ ==> ^p+ ^{0} ^{1}) ^{2} nu_mu~]CC"
mc_mothers_templates = {
    "Lambdab": "[Lambda_b0 ==> (Lambda_c+ ==> p+ {0} {1}) {2} nu_mu~]CC",
    "Lambdac": "[Lambda_b0 ==> ^(Lambda_c+ ==> p+ {0} {1}) {2} nu_mu~]CC",
}
mc_daughters_templates = {
    "mu": "[Lambda_b0 ==> (Lambda_c+ ==> p+ {0} {1}) ^{2} nu_mu~]CC",
    "h1": "[Lambda_b0 ==> (Lambda_c+ ==> p+ ^{0} {1}) {2} nu_mu~]CC",
    "h2": "[Lambda_b0 ==> (Lambda_c+ ==> p+ {0} ^{1}) {2} nu_mu~]CC",
    "proton": "[Lambda_b0 ==> (Lambda_c+ ==> ^p+ {0} {1}) {2} nu_mu~]CC"
}

for line in lines:
    stripping = lines[line]["stripping"]
    tracks = lines[line]["tracks"]

    # Fill the branch templates with the appropriate particles
    mothers = {}
    daughters = {}
    mc_mothers = {}
    mc_daughters = {}
    for mother in mothers_templates:
        mothers[mother] = mothers_templates[mother].format(*tracks)
    for daughter in daughters_templates:
        daughters[daughter] = daughters_templates[daughter].format(*tracks)
    for mother in mc_mothers_templates:
        mc_mothers[mother] = mc_mothers_templates[mother].format(*tracks)
    for daughter in mc_daughters_templates:
        mc_daughters[daughter] = mc_daughters_templates[daughter].format(*tracks)

    # Tuple for stripped and reconstructed events
    t = tuple_templates.lc2pxx_tuple(
        "Tuple{0}".format(line),
        decay_template.format(*tracks),
        mothers,
        daughters,
        inputs_template.format(stripping),
        True
    )
    # Tuple for generated events
    mc_t = tuple_templates.mc_decay_tree_tuple(
        "MCGenTuple{0}".format(line),
        mc_decay_template.format(*tracks),
        mc_mothers,
        mc_daughters
    )

    # Stripped tuple will only be filled if MC tuple is
    sequence = GaudiSequencer("SeqBook{0}".format(line))
    sequence.Members = [mc_t, t]

    DaVinci().UserAlgorithms.append(sequence)
