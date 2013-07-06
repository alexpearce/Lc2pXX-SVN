from Configurables import (
    DaVinci,
    GaudiSequencer,
    FilterDesktop,
    FilterEventByMCDecay,
    MCDecayFinder,
    CombineParticles
)

from lc2pxx import config
from lc2pxx.booking import davinci, tuple_templates

year = 2011
mc = True

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

mc_decay_template = "[Lambda_b0 => (^Lambda_c+ => ^p+ ^{0} ^{1}) ^{2} nu_mu~ ...]cc"
mc_mother_templates = {
    "Lambdab": "[Lambda_b0]cc: [Lambda_b0 => (Lambda_c+ => p+ {0} {1}) {2} nu_mu~ ...]cc",
    "Lambdac": "[Lambda_b0 => (^Lambda_c+ => p+ {0} {1}) {2} nu_mu~ ...]cc"
}
mc_daughter_templates = {
    "mu": "[Lambda_b0 => (Lambda_c+ => p+ {0} {1}) ^{2} nu_mu~ ...]cc",
    "h1": "[Lambda_b0 => (Lambda_c+ => p+ ^{0} {1}) {2} nu_mu~ ...]cc",
    "h2": "[Lambda_b0 => (Lambda_c+ => p+ {0} ^{1}) {2} nu_mu~ ...]cc",
    "proton": "[Lambda_b0 => (Lambda_c+ => ^p+ {0} {1}) {2} nu_mu~ ...]cc"
}

# Build CombineParticles for Lambda_c decay, then Lambda_b decay
lc_decay_template = "[Lambda_c+ -> p+ {0} {1}]cc"
lc_mother_template = "(mcMatch('[Lambda_c+ ==> p+ {0} {1}]CC'))"
lc_daughters_template = {
    "p+": "mcMatch('[Lambda_c+ ==> ^p+ {0} {1}]CC')",
    "h1": "mcMatch('[Lambda_c+ ==> p+ ^{0} {1}]CC')",
    "h2": "mcMatch('[Lambda_c+ ==> p+ {0} ^{1}]CC')"
}
lc_combine_template = CombineParticles(
    "CombineCheatedLcpTophh",
    Preambulo=[
      "from LoKiPhysMC.decorators import *" ,
      "from LoKiPhysMC.functions import mcMatch"
    ],
    DecayDescriptor=lc_decay_template,
    Inputs=[
      "Phys/StdAllNoPIDsPions",
      "Phys/StdAllNoPIDsKaons",
      "Phys/StdAllNoPIDsProtons"
    ],
    DaughtersCuts=lc_daughters_template,
    CombinationCut="AALL",
    MotherCut=lc_mother_template
)
# Lambda_b templates
lb_decay_template = "[Lambda_b0 -> Lambda_c+ {0}]cc"
lb_mother_template = "(mcMatch('[Lambda_b0 --> Lambda_c+ {0} ...]CC'))"
lb_daughters_template = {
    "mu+": "(mcMatch('[Lambda_b0 --> Lambda_c+ ^{0} ...]CC'))"
}
lb_combine_template = CombineParticles(
    "CombineCheatedLb0ToLcpmu",
    Preambulo=[
      "from LoKiPhysMC.decorators import *",
      "from LoKiPhysMC.functions import mcMatch"
    ],
    DecayDescriptor=lb_decay_template,
    Inputs=[
      "Phys/StdAllNoPIDsMuons",
      "Phys/CombineCheatedLcpTophh"
    ],
    DaughtersCuts=lb_daughters_template,
    CombinationCut="AALL",
    MotherCut=lb_mother_template,
)

# Lambda_c mass window of 75 MeV around the nominal PDG mass
filter_template = FilterDesktop(
    "FilterOfflineLc2phh",
    Code="(MINTREE(ABSID=='Lambda_c+', ADMASS('Lambda_c+')) < 75*MeV)"
)

mc_filter_template = FilterEventByMCDecay("FilterMCLc2phh")
mc_filter_template.addTool(MCDecayFinder)
mc_filter_template.MCDecayFinder.Decay = mc_decay_template
mc_filter_template.MCDecayFinder.ResonanceThreshold = 5e-10

for line in lines:
    stripping = lines[line]["stripping"]
    tracks = lines[line]["tracks"]

    filter_name = "FilterOffline{0}".format(line)
    filter = filter_template.clone(filter_name)
    filter.Inputs = [inputs_template.format(stripping)]

    mc_filter_name = "MCFilter{0}".format(line)
    mc_filter = mc_filter_template.clone(mc_filter_name)
    mc_filter.MCDecayFinder.Decay = mc_decay_template.format(*tracks)

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
        inputs_template.format(filter_name)
    )

    # MCDecayTreeTuple
    mc_tuple = tuple_templates.mc_decay_tree_tuple(
        "MCGenTuple{0}".format(line),
        mc_decay_template.format(*tracks),
        mc_mothers,
        mc_daughters
    )

    # Cheated DecayTreeTuple
    # TODO explain
    h1, h2, mu = tracks
    # Construct Lambda_c daughters dictionary
    lc_daughters = {
        "p+": lc_daughters_template["p+"].format(h1, h2)
    }
    # The sign of h1 changes in idx0, remains equal for h2 in idx1
    # (str.replace returns str if no substitution is made)
    idx0 = h1.replace("-", "+")
    idx1 = h2.replace("-", "+")
    # This condition will be satisfied by the CF and DCS modes, not the SCS
    if (idx0 != idx1):
        lc_daughters[idx0] = lc_daughters_template["h1"].format(h1, h2)
        lc_daughters[idx1] = lc_daughters_template["h2"].format(h1, h2)
    else:
        lc_daughters[idx0] = lc_daughters_template["h1"].format(
            h1, '^{0}'.format(h2)
        )
    lb_daughters = {
        "Lambda_c+": "ALL",
        "mu+": lb_daughters_template["mu+"].format(mu)
    }
    # Combine Lambda_c daughters to form mother
    lc_combine_name = "CombineCheated{0}".format(line)
    lc_decay = lc_decay_template.format(h1, h2)
    lc_mother = lc_mother_template.format(h1, h2)
    lc_combine = lc_combine_template.clone(lc_combine_name)
    lc_combine.DecayDescriptor = lc_decay
    lc_combine.DaughtersCuts = lc_daughters
    lc_combine.MotherCut = lc_mother
    # Combine Lambda_b daughters to form mother
    lb_combine_name = "CombineCheatedLbTomu{0}".format(line)
    lb_decay = lb_decay_template.format(mu)
    lb_mother = lb_mother_template.format(mu)
    lb_combine = lb_combine_template.clone(lb_combine_name)
    lb_combine.DecayDescriptor = lb_decay
    lb_combine.DaughtersCuts = lb_daughters
    lb_combine.MotherCut = lb_mother
    # Output of combining Lc daughters is input to combining Lb daughters
    lb_combine.Inputs = [
        "Phys/StdAllNoPIDsMuons",
        "Phys/{0}".format(lc_combine_name)
    ]
    # Clone the DecayTreeTuple created above
    cheat_tuple = tuple.clone("Tuple{0}".format(lb_combine_name))
    cheat_tuple.Inputs = ["Phys/{0}".format(lb_combine_name)]

    # Sequences for ntuple creation
    dec_sequence = GaudiSequencer("SeqBook{0}".format(line))
    dec_sequence.Members = [filter, tuple]
    mc_sequence = GaudiSequencer("SeqMCGenBook{0}".format(line))
    mc_sequence.Members = [mc_tuple]
    cheat_sequence = GaudiSequencer("SeqMCCheatBook{0}".format(line))
    cheat_sequence.Members = [lc_combine, lb_combine, cheat_tuple]

    # Sequence for ntuple sequences
    tuples_sequence = GaudiSequencer("SeqTuples{0}".format(line))
    tuples_sequence.IgnoreFilterPassed = True
    tuples_sequence.Members = [dec_sequence, mc_sequence, cheat_sequence]

    # Sequence for MC filter then ntuple sequences
    master_sequence = GaudiSequencer("SeqMaster{0}".format(line))
    master_sequence.Members = [mc_filter, tuples_sequence]

    DaVinci().UserAlgorithms.append(master_sequence)

