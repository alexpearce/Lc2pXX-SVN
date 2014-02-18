"""
In order to normalise options files between modes, and between collision
and simulation, we use a helper module.
In order to use this module, we need to add its parent directory to the
PYTHONPATH.
This script does exactly that, and so must be called before any true option file,
e.g. in Ganga
    j = Job(application='DaVinci')
    j.application.optsfile= [
        '/path/to/Lc2pXX/options/add_helpers.py',
        '/path/to/Lc2pXX/options/my_options.py'
    ]
The path `/path/to/Lc2pXX/options` is then added to PYTHONPATH, and `my_options`
can call `import helpers` and the like.
If you want to use the options files, you should change the path below to reflect
your environment.
"""
import sys
sys.path.append("/afs/cern.ch/user/a/apearce/cmtuser/Urania_v2r1/Phys/Lc2pXX/options")
