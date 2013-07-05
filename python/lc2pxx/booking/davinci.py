from Gaudi.Configuration import *
from Configurables import DaVinci, LoKiSvc
from PhysConf.MicroDST import uDstConf

from lc2pxx import config

def configure(year, mc):
    """General configuration of DaVinci options.

    Keyword arguments:
    year -- One of lc2pxx.config.years
    mc -- True if booking MC ntuples, else false
    """
    # No enormous LoKi messages
    LoKiSvc().Welcome = False

    dv = DaVinci()
    # Output ntuple name
    dv.TupleFile = config.ntuple_name
    # Process all events
    dv.EvtMax = -1
    # Print status every 1000 events
    dv.PrintFreq = 1000
    # Number of events to skip at the beginning of each file
    dv.SkipEvents = 0
    dv.DataType = str(year)
    dv.Simulation = mc
    # Collision streams for Charm are on microDST, and there's no luminosity
    # in MC
    if not mc:
        dv.InputType = "MDST"
        # See http://cern.ch/go/B7mq
        uDstConf("/Event/Charm")
        # Add a GetIntegratedLuminosity/LumiTuple TTree to output
        dv.Lumi = True

