"""
containers
Classes representing containers, holding something and some metadata.
"""

import logging as log

from lc2pxx import config

class DataStore:
    """Container class for ntuple metadata for plotting."""
    def __init__(self, name, ntuple, cuts=""):
        """Initialise an instance of the DataStore class.

        Keyword arguments:
        name -- String assigned to DataStore.name
        ntuple -- Lc2pXX object assigned to DataStore.ntuple
        cuts -- String of requirements on ntuple entries assigned to
            DataStore.cuts (default "")
        """
        self.name = name
        self.ntuple = ntuple
        self.cuts = cuts

    def __getattr__(self, attr):
        """Pass the method call to DataStore.ntuple, if it exists on it.

        This allows all methods and properties on Lc2pXX, such as
        GetEntries and mode, to be called on the DataStore instance.
        """
        try:
            method = getattr(self.ntuple, attr)
        except AttributeError:
            log.error("Attribute `{0}` not found on DataStore".format(attr))
        else:
            return method


class HistoVar:
    """Container class for variable metadata for plotting."""
    def __init__(self, name, title, min, max, units="", bins=0):
        """Initialise an instance of the HistoVar class.

        Keyword arguments:
        name -- String assigned to HistoVar.name, represents the variable
            the instance represents.
        title -- Pretty version of name, assigned to HistoVar.title
        min -- Min range of variable assigned to HistoVar.min
        max -- Min range of variable assigned to HistoVar.max
        units -- String of the units of this variable
        bins -- Number of bins to plot with. If 0, object uses
            config.num_bins
        """
        self.name = name
        self.title = title
        self.min = min
        self.max = max
        self.units = units
        self.bins = bins or config.num_bins

