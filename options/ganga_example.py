"""
An example of creating an Lc2pXX ntuple creation job with Ganga.
"""
# This will use the latest DaVinci release
# When submitting multiple jobs for the same analysis, make sure to use the same version!
j = Job(application="DaVinci")
# The order here is important: first load the helpers, then our options
j.application.optsfile = [
    "/path/to/Lc2pXX/options/add_helpers.py",
    "/path/to/Lc2pXX/options/davinci_collision_2011.py",
    "/path/to/Lc2pXX/options/collision_S20.py"
]
# Choose some data, e.g.
# /LHCb/Collision11/Bea,3500GeV-VeloClosed-MagDown/Real Data/Reco14/Stripping20r1/90000000/CHARM.MDST
j.inputdata = browseBK()
# Run DaVinci and place the output on The Grid
j.backend = Dirac()
j.outputfiles = [DiracFile("DVntuple.root")]
j.splitter = SplitByFiles(filesPerJob=15)
# Get emails when subjobs fail, and when the job is complete
j.postprocessors = [Notifier(address="my.name@cern.ch")]
# Good to know what the job was for
j.comments = "..."

# Away we go!
j.submit()
