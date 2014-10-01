"""
containers
Classes representing containers, holding something and some metadata.
"""

import logging as log
import array

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
    def __init__(self, name, title, min, max, units="", bins=20, binning=None):
        """Initialise an instance of the HistoVar class.

        Keyword arguments:
        name -- String assigned to HistoVar.name, represents the variable
            the instance represents.
        title -- Pretty version of name, assigned to HistoVar.title
        min -- Min range of variable assigned to HistoVar.min
        max -- Max range of variable assigned to HistoVar.max
        units -- String of the units of this variable (default: "")
        bins -- Number of bins to plot with (default: 20)
        binning -- An *array* of bin boundaries. If None (default), create a
            fixed-width binning using min, max, and num_bins, assigned to
            HistoVar.binning
        """
        self.name = name
        self.title = title
        self.min = min
        self.max = max
        self.units = units
        self.bins = bins
        self.binning = binning

    def bins_array(self, t='f'):
        """Return an array, of type t, defining the variable's bin boundaries.

        The first boundary is self.min, the last is self.max.
        If the user has not defined self.binning, create a fixed-width binning
        of num_bins bins.
        Keyword arguments:
        t -- Type of the array (default: 'f', for floats). See
            http://docs.python.org/2/library/array.html
        """
        binning = self.binning
        if not binning:
            step = (self.max - self.min)/(1.*self.bins)
            boundaries = [self.min + i*step for i in range(self.bins)]
            # We need to specify the upper edge of the last bin
            boundaries += [self.max]
            binning = array.array(t, boundaries)
        return binning
