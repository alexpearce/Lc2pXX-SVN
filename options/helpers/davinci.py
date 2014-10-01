from Configurables import DaVinci

def configure(year, mc):
    """General configuration of DaVinci options.

    Keyword arguments:
    year -- One of lc2pxx.config.years
    mc -- True if booking MC ntuples, else false
    """
    dv = DaVinci()
    # Output ntuple name
    dv.TupleFile = "DVntuple.root"
    # Process all events
    dv.EvtMax = -1
    # Print status every 1000 events
    dv.PrintFreq = 1000
    # Number of events to skip at the beginning of each file
    dv.SkipEvents = 0
    dv.DataType = str(year)
    dv.Simulation = mc
    # Collision streams for Charm are on microDST, and  in MC
    if not mc:
        dv.InputType = "MDST"
        # See "Question about microDST and RootInTES" in lhcb-davinci
        dv.RootInTES = "/Event/Charm"
    # Add a GetIntegratedLuminosity/LumiTuple TTree to output, but not in MC
    dv.Lumi = not mc
