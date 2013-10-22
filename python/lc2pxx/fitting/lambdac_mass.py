"""
fitting
Set of methods for fitting.
"""

import logging as log

import ROOT
from uncertainties import ufloat

from lc2pxx import config, utilities

# String constants
consts = {
    "data": "data",
    "var_name": "Lambdac_M",
    "pdf_sig": "signal_pdf",
    "pdf_bkg": "background_pdf",
    "pdf_tot": "total_pdf",
    "yield_sig": "yield_signal",
    "yield_bkg": "yield_background",
    "fit_result": "fit_result",
    "sWeights": "sWeights"
}

def fit(ntuple, workspace, shapes, bins=0):
    """Fits an ntuple to the Lambda_c mass spectrum.

    Adds all PDF and variables to the workspace, along with the fit result.
    Logs a WARNING if the fit does not fully converge.
    Keyword arguments:
    ntuple -- Lc2pXX instance containing data to be fitted
    workspace -- RooWorkspace to hold the data, PDFs, and fit result
    shapes -- 2-tuple of PDF shapes to fit with. Indexes are
        0 -- Signal, one of (SGS, DGS, SCB, DCB)
        1 -- Background, one of (FOP, EXP)
    bins -- Performs a binned fit, if bins != 0, to that number of bins
        (default 0)
    """
    log.info("Fitting Lc mass")

    shape_sig = shapes[0]
    shape_bkg = shapes[1]
    entries = ntuple.GetEntries()

    # Add the mass variable and data to the workspace
    workspace.factory("{0}[{1}, {2}]".format(
        consts["var_name"], config.lc_m_low, config.lc_m_high
    ))
    workspace.var(consts["var_name"]).SetTitle("m({0})".format(
        utilities.latex_mode(ntuple.mode)
    ))
    workspace.var(consts["var_name"]).setUnit("MeV/#font[12]{c}^{2}")
    if bins:
        ntuple.Draw("{0}>>h1({1}, {2}, {3})".format(
            consts["var_name"],
            bins,
            config.lc_m_low,
            config.lc_m_high
        ))
        h1 = ROOT.gDirectory.Get("h1")
        data = ROOT.RooDataHist(consts["data"], consts["data"],
            ROOT.RooArgList(workspace.var(consts["var_name"])), h1)
    else:
        data = ROOT.RooDataSet(consts["data"], consts["data"], ntuple,
            ROOT.RooArgSet(workspace.var(consts["var_name"])))
    # Workaround for `import` being a Python keyword
    workspace_import = getattr(workspace, "import")
    workspace_import(data)

    # Add variables to hold the yields
    workspace.factory("{0}[{1}, 0, {2}]".format(
        consts["yield_sig"], entries / 2, entries)
    )
    workspace.factory("{0}[{1}, 0, {2}]".format(
        consts["yield_bkg"], entries / 2, entries)
    )

    # Add the shapes to the workspace
    add_pdf(shape_sig, workspace)
    add_pdf(shape_bkg, workspace)

    # Total PDF as the weighted sum of the signal and background
    workspace.factory("SUM::{0}({1}*{2}, {3}*{4})".format(
        consts["pdf_tot"],
        consts["yield_sig"],
        consts["pdf_sig"],
        consts["yield_bkg"],
        consts["pdf_bkg"],
    ))

    # Perform the fit, adding the RooFitResult to the workspace
    fit_result = workspace.pdf(consts["pdf_tot"]).fitTo(
        workspace.data(consts["data"]), ROOT.RooFit.Save(True)
    )
    workspace_import(fit_result, consts["fit_result"])

    # Check for poor fit quality using the error matrix status
    # http://cern.ch/go/6PwR
    fit_quality = fit_result.covQual()
    if fit_quality < 3:
        log.warning("Poor fit quality: {0}".format(fit_quality))

    # sWeights requires an unbinned fit
    if not bins:
        log.info("Generating sWeights")
        # sPlot requires all non-yields parameters of the model be constant
        vars = workspace.allVars()
        it = vars.createIterator()
        yield_vars = (consts["yield_sig"], consts["yield_bkg"])
        while it.Next():
            if it.GetName() not in yield_vars:
                it.setConstant()
        sweights = ROOT.RooStats.SPlot(
            "sData",
            "sData",
            workspace.data(consts["data"]),
            workspace.pdf(consts["pdf_tot"]),
            ROOT.RooArgList(
                workspace.var(yield_vars[0]),
                workspace.var(yield_vars[1])
            )
        )
        workspace_import(sweights, consts["sWeights"])


def yields(workspace):
    """Return the signal and background yields in the signal region.

    The signal region is defined as +/- 3 sigma around the mean of the
    signal PDF, or the narrowest of the group for composite signal PDFs.
    The returned yields are ufloats.
    Keyword arguments:
    workspace -- RooWorkspace containing the fit result, PDFs and variables
    """
    if workspace.obj(consts["fit_result"]) == None:
        log.error("Cannot calculate yields, PDFs have not been fitted")
        return

    x = workspace.var(consts["var_name"])
    x_set = ROOT.RooArgSet(x)
    mean = workspace.var("mu").getVal()
    width_var = workspace.var("sigma")
    try:
        width = width_var.getVal()
    except TypeError:
        width_one = workspace.var("sigma_one").getVal()
        width_two = workspace.var("sigma_two").getVal()
        width = min(width_one, width_two)
    limit_lo = mean - 3*width
    limit_hi = mean + 3*width
    log.info("Calculating yields in range [{0}, {1}] MeV/c^2".format(
        limit_lo,
        limit_hi
    ))
    range = "signalRegion"
    x.setRange(range, limit_lo, limit_hi)
    int_sig = workspace.pdf(consts["pdf_sig"]).createIntegral(
        x_set, x_set, range
    ).getVal()
    int_bkg = workspace.pdf(consts["pdf_bkg"]).createIntegral(
        x_set, x_set, range
    ).getVal()

    yield_sig_var = workspace.var(consts["yield_sig"])
    yield_bkg_var = workspace.var(consts["yield_bkg"])
    yield_sig_num = int_sig*yield_sig_var.getVal()
    yield_sig_err = int_sig*yield_sig_var.getError()
    yield_bkg_num = int_bkg*yield_bkg_var.getVal()
    yield_bkg_err = int_bkg*yield_bkg_var.getError()

    yield_sig = ufloat(yield_sig_num, yield_sig_err)
    yield_bkg = ufloat(yield_bkg_num, yield_bkg_err)

    return (yield_sig, yield_bkg)


def sweights(workspace):
    """Return sWeights dataset from the fit."""
    sweights = workspace.obj(consts["sWeights"])
    if sweights == None:
        log.error("Could not retrieve sWeights, fit not performed")
    return sweights


def add_pdf(key, workspace):
    """Add a PDF to the workspace, of type specified by the key."""
    if key in shapes_sig:
        shapes_sig[key](workspace)
    elif key in shapes_bkg:
        shapes_bkg[key](workspace)
    else:
        log.error("PDF not found for key `{0}`".format(key))


def _double_crystal_ball(workspace):
    """Add double Crystal Ball signal PDF to the workspace.

    Each CB shares a common mean, decay rate, and normalization
    factor, but can have different widths.
    """
    log.info("Adding double Crystal Ball PDF to workspace")
    workspace.factory("mu[2290, 2285, 2295]")
    workspace.factory("sigma_one[4, 0, 8]")
    workspace.factory("sigma_two[7, 4, 15]")
    workspace.factory("alpha[1.5, -5, 5]")
    workspace.factory("n[2, 1, 10]")
    workspace.factory("RooCBShape::pdf_cb_one("
        "{0}, mu, sigma_one, alpha, n"
    ")".format(consts["var_name"]))
    workspace.factory("RooCBShape::pdf_cb_two("
        "{0}, mu, sigma_two, alpha, n"
    ")".format(consts["var_name"]))
    workspace.factory("SUM::{0}("
        "pdf_cb_one, num_cb[0.5, 0, 1]*pdf_cb_two"
    ")".format(consts["pdf_sig"]))


# Signal PDFs
def _double_gaussian(workspace):
    """Add double gaussian signal PDF to the workspace.

    Each Gaussian shares a common mean, but can have different
    widths.
    """
    log.info("Adding double Gaussian signal PDF to workspace")
    workspace.factory("mu[2290, 2285, 2295]")
    workspace.factory("sigma_one[4, 0, 8]")
    workspace.factory("sigma_two[7, 4, 15]")
    workspace.factory("RooGaussian::pdf_gauss_one("
        "{0}, mu, sigma_one"
    ")".format(consts["var_name"]))
    workspace.factory("RooGaussian::pdf_gauss_two("
        "{0}, mu, sigma_two"
    ")".format(consts["var_name"]))
    workspace.factory("SUM::{0}("
        "pdf_gauss_one, num_gauss[0.5, 0, 1]*pdf_gauss_two"
    ")".format(consts["pdf_sig"]))


def _single_gaussian(workspace):
    """Add single gaussian signal PDF to the workspace."""
    log.info("Adding single Gaussian signal PDF to workspace")
    workspace.factory("mu[2290, 2285, 2295]")
    workspace.factory("sigma[4, 0, 8]")
    workspace.factory("RooGaussian::{0}("
        "{1}, mu, sigma"
    ")".format(consts["pdf_sig"], consts["var_name"]))


def _single_crystal_ball(workspace):
    """Add single Crystal Ball signal PDF to the workspace."""
    log.info("Adding single Crystal Ball signal PDF to workspace")
    workspace.factory("mu[2290, 2285, 2295]")
    workspace.factory("sigma[4, 0, 8]")
    workspace.factory("alpha[1.5, -5, 5]")
    workspace.factory("n[2, 1, 10]")
    workspace.factory("RooCBShape::{0}("
        "{1}, mu, sigma, alpha, n"
    ")".format(consts["pdf_sig"], consts["var_name"]))


def _gaussian_crystal_ball(workspace):
    """Add a Gaussian + Crystal Ball signal PDF to the workspace."""
    log.info("Adding Gaussian Crystal Ball signal PDF to workspace.")
    workspace.factory("mu[2290, 2285, 2295]")
    workspace.factory("sigma_one[7, 0, 15]")
    workspace.factory("sigma_two[4, 0, 15]")
    workspace.factory("alpha[2, -6, 6]")
    workspace.factory("n[2, -10, 10]")
    workspace.factory("RooGaussian::pdf_gauss_one("
        "{0}, mu, sigma_one"
    ")".format(consts["var_name"]))
    workspace.factory("RooCBShape::pdf_cb_two("
        "{0}, mu, sigma_two, alpha, n"
    ")".format(consts["var_name"]))
    workspace.factory("SUM::{0}("
        "pdf_gauss_one, num_gauss[0.5, 0, 1]*pdf_cb_two"
    ")".format(consts["pdf_sig"]))

# Background PDFs
def _exponential(workspace):
    """Add exponential background PDF to the workspace."""
    log.info("Adding exponential background PDF to workspace")
    workspace.factory("lambda[-0.1, -0.5, 0.5]")
    workspace.factory("RooExponential::{0}("
        "{1}, lambda"
    ")".format(consts["pdf_bkg"], consts["var_name"]))


def _first_order_polynomial(workspace):
    """Add 1st order polynomial background PDF to workspace."""
    log.info("Adding O(1) polynomial background PDF to workspace")
    workspace.factory("RooChebychev::{0}("
        "{1}, {{a0[-1, 1]}}"
    ")".format(consts["pdf_bkg"], consts["var_name"]))


shapes_sig = {
    "DGS": _double_gaussian,
    "SGS": _single_gaussian,
    "DCB": _double_crystal_ball,
    "SCB": _single_crystal_ball,
    "GCB": _gaussian_crystal_ball
}

shapes_bkg = {
    "EXP": _exponential,
    "FOP": _first_order_polynomial
}

