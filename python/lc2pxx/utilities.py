"""
utilities
Useful functions.
"""

import os
import sys
import logging as log
import tempfile
import random
import re
from math import sqrt

import ROOT
from uncertainties import ufloat

import lc2pxx

def quiet_mode():
    """Enables ROOT batch mode (no X windows) and sets no INFO logging."""
    # Enable batch mode -> no X windows
    ROOT.gROOT.SetBatch(True)
    # Disable INFO level logging, i.e. WARNING and up
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    log.info("Quiet mode enabled")

def progress_bar(fraction):
    """Prints a progress bar filled proportionally to fraction.

    Keyword arguments:
    fraction -- Float between 0 and 1.
    """
    width = 20
    percent = int(100*fraction)
    if percent % 5 != 0: return
    filled = percent/5
    sys.stdout.write("\r")
    sys.stdout.write("[{0}{1}] {2}%".format(
        "#"*filled,
        " "*(width - filled),
        percent
    ))
    sys.stdout.flush()


def create_temp_file():
    """Return a temporary TFile, to be deleted by the user."""
    dir = tempfile.mkdtemp()
    # TODO not particular useful if we have more than one temp file...
    filename = dir + "/tmp.root"
    log.info("Creating temporary TFile `{0}`".format(filename))
    return ROOT.TFile(filename, "recreate")


def delete_temp_file(file):
    """Deletes files created by `create_temp_file`."""
    filename = file.GetEndpointUrl().GetFile()
    # Prevent accidental deletion of non-temporary files
    if filename.startswith(("/var", "/tmp")):
        log.info("Deleting temporary TFile `{0}`".format(filename))
        try:
            os.remove(filename)
        except OSError:
            log.error("Could not remove file at `{0}`".format(filename))
    else:
        log.error("Refusing to delete 'temporary' file `{0}`".format(
            filename
        ))


def save_to_file(filename, objects):
    """Creates a TFile called filename, then writes each object to the file.

    Keyword arguments:
    filename -- Name of the filename the objects will be saved in to.
        If filename already exists, it is overwritten.
    objects -- List of objects implementing TObject.Write.
    """
    file = ROOT.TFile(filename, "recreate")
    for object in objects: object.Write()
    file.Write()
    file.Close()


def file_exists(path):
    """Returns True if anything exists at the given path."""
    # http://cern.ch/go/9rxQ
    return os.path.exists(path)


def latex_mode(mode):
    """Return the LaTeX string corresponding to the mode."""
    try:
        latex = lc2pxx.config.modes_latex[mode]
    except KeyError:
        latex = "MODENOTFOUND"
    return latex


def significance(signal, background):
    """Return the significance of the signal yield wrt to the background.

    The significance is defined as
       S / sqrt(S + B)
    where S and B are the signal and background yields respectively.
    """
    return (signal/(signal + background)**0.5)


def random_str():
    """Generates a 30 character string of random letters and numbers."""
    return "%030x" % random.randrange(256**15)


def sanitise(dirty):
    """Substitutes all characters outside [A-za-z0-9_] with _."""
    return re.sub(r"\W+", "", dirty.lower().replace(" ", "_"))


def binomial_error(k, n):
    """Return the binomial error when selecting k events out of a n.

    The error, or standard deviation, is the square root of the variance.
    Assuming a cut has a predicted efficiency of k/n when selecting k
    events out of n, the variance is given as
        k*(n - k)/n^3.
    """
    # Arguments may be given as ints, so prevent against integer division
    a = float(k)
    b = float(n)
    try:
        variance = a*(b - a)/(b*b*b)
    except ValueError:
        log.error("ValueError (binomial_error): a={0}, b={0}".format(a, b))
        variance = 0.0
    return sqrt(variance)


def efficiency_from_yields(after, before):
    """Return a ufloat of the efficiency and error.

    The efficiency returned is simply after/before, and the error is the
    binomial error on the efficiency (see `binomial_error`).
    """
    eff = float(after)/float(before)
    err = binomial_error(after, before)
    return ufloat(eff, err)
