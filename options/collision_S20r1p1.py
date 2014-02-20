"""
2011 collision DaVinci options file for creating ntuples for the decay chain
    [Lambda_b0 -> (Lambda_c+ -> p+ (KS0 -> pi- pi+)) mu-]CC
Ntuples for both long-long (LL) and down-down (DD) KS are produced.
DecayTreeFitter is run on the Lambda_b0, constraining the KS mass, as this
improves the Lambda_c+ mass resolution.
"""
from Configurables import DaVinci
from DecayTreeTuple.Configuration import *

from helpers import davinci, tuple_templates

year = 2011
mc = False

davinci.configure(2011, False)

lines = {
    "LcTopKSLL": {
        "stripping": "b2MuXLc2pKsLLCharmFromBSemiLine",
        "tracks": ("mu-",)
    },
    "LcTopKSDD": {
        "stripping": "b2MuXLc2pKsDDCharmFromBSemiLine",
        "tracks": ("mu-",)
    }
}

inputs_template = "Phys/{0}/Particles"
decay_template = "[Lambda_b0 -> ^(Lambda_c+ -> ^p+ ^(KS0 -> ^pi- ^pi+)) ^{0}]CC"
mothers_templates = {
    "Lambdab": "[Lambda_b0 -> (Lambda_c+ -> p+ (KS0 -> pi- pi+)) {0}]CC",
    "Lambdac": "[Lambda_b0 -> ^(Lambda_c+ -> p+ (KS0 -> pi- pi+)) {0}]CC",
    "KS": "[Lambda_b0 -> (Lambda_c+ -> p+ ^(KS0 -> pi- pi+)) {0}]CC",
}
daughters_templates = {
    "mu": "[Lambda_b0 -> (Lambda_c+ -> p+ (KS0 -> pi- pi+)) ^{0}]CC",
    "h1": "[Lambda_b0 -> (Lambda_c+ -> p+ (KS0 -> ^pi- pi+)) {0}]CC",
    "h2": "[Lambda_b0 -> (Lambda_c+ -> p+ (KS0 -> pi- ^pi+)) {0}]CC",
    "proton": "[Lambda_b0 -> (Lambda_c+ -> ^p+ (KS0 -> pi- pi+)) {0}]CC"
}

# DecayTreeFitter variables to add
dtf_particles = {
    "Lambdac": "CHILD({}, 1)",
    "proton": "CHILD({}, 1, 1)",
    "KS": "CHILD({}, 2, 1)",
    "h1": "CHILD({}, 1, 2, 1)",
    "h2": "CHILD({}, 2, 2, 1)",
}
dtf_variables = ["ID", "M", "P", "E", "PT", "PX", "PY", "PZ"]
dtf_loki_vars = {
    "DTF_CHI2": "DTF_CHI2(False, 'KS0')",
    "DTF_NDOF": "DTF_NDOF(False, 'KS0')"
}
for p in dtf_particles:
    for v in dtf_variables:
        key = "DTF_{0}_{1}".format(p, v)
        func = "DTF_FUN({}, False, 'KS0')".format(dtf_particles[p]).format(v)
        dtf_loki_vars[key] = func

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
    dtf = t.Lambdab.addTupleTool("LoKi::Hybrid::TupleTool/LoKiDTFTool")
    dtf.Variables = dtf_loki_vars

    DaVinci().UserAlgorithms.append(t)

