"""A module that plots variables from ntuples."""

import logging as log
from array import array

import ROOT

from lc2pxx import config, utilities

def line_colour(index):
    """Return a line colour for the index."""
    colours = [
        ROOT.kBlue + 1,
        ROOT.kRed,
        ROOT.kMagenta,
        ROOT.kOrange
    ]
    return colours[index]


def line_style(index):
    """Return a line style for the index."""
    return index


def fill_colour(index):
    """Return a fill colour for the index."""
    colours = [
        38,
        2,
        ROOT.kMagenta,
        ROOT.kOrange,
        7,
        8,
        9,
        11
    ]
    return colours[index]


def fill_style(index):
    """Return a fill style for the index."""
    styles = [
        1001,
        3554,
        3003,
        3545,
        0
    ]
    return styles[index]


def plot_variable(variable, data_stores):
    """Return a TCanvas containing the variable plotted for each data_store.

    Keyword arguments:
    variable -- HistoVar instance for the variable to be plotted
    data_stores -- List of DataStore instances to be superimposed
    """
    get_style().cd()

    # If the datasets are weighted, this ensures proper error calculation
    ROOT.TH1.SetDefaultSumw2(True)

    # Only matters what the aspect ratio is
    canvas = ROOT.TCanvas(variable.name, variable.title, 400, 400)
    stack = ROOT.THStack("stack", variable.title)
    # Legend height as a function of entry numbers
    legend = ROOT.TLegend(0.9, 0.9, 0.6, 0.9 - (0.1*len(data_stores)))
    legend.SetName(utilities.random_str())
    # TODO this will be silly with proportional fonts
    # TStyle has no method for setting this globally: aaarrrrggggghhh
    legend.SetTextSize(16)

    histograms = []

    # Used to find the tallest histogram
    total_max = -1

    for count, data_store in enumerate(data_stores):
        # Because this method may be called several times, we must make sure
        # not to create histograms with identical `name` attributes in the
        # global scope, so we generate random strings and assign these as
        # names
        uniq = utilities.random_str()
        data_store.Draw(
            "{0}>>h{1}({2},{3},{4})".format(
                variable.name,
                uniq,
                variable.bins,
                variable.min,
                variable.max
            ),
            data_store.cuts
        )

        histo = ROOT.gDirectory.Get("h{0}".format(uniq))
        # We scale to 100 so the y-axis units look nicer
        histo.Scale(100. / histo.GetSumOfWeights())
        max = histo.GetMaximum()
        if max > total_max:
            total_max = max
        histo.SetLineColor(line_colour(count))
        histo.SetFillColor(fill_colour(count))
        histo.SetFillStyle(fill_style(count))
        histo.SetMarkerColor(line_colour(count))
        histo.SetMarkerSize(0.5)
        histo.SetMarkerStyle(20)

        stack.Add(histo)
        legend.AddEntry(histo, data_store.name, "lep")

        histograms.append(histo)

    # count should be 1-indexed
    count += 1

    total_max *= 1.1
    for i in range(count):
        histograms[i].SetMaximum(total_max)

    # The stack needs to be drawn to get access to the axes
    stack.Draw()
    xaxis_title = variable.title
    if variable.units:
        xaxis_title += " [{0}]".format(variable.units)
    stack.GetXaxis().SetTitle(xaxis_title)
    stack.GetYaxis().SetTitle("Arbitrary units")
    stack.Draw("e1 nostack ")
    legend.Draw()

    # Adding properties to canvas means they won't get garbage collected
    # when canvas is returned
    # Wierdly, the histograms aren't GC'd, even though the THStack docs
    # says that the stack doesn't own the histos it contains
    canvas.s = stack
    canvas.l = legend

    return canvas


def plot_variable_2d(variables, data_store):
    """Return a TCanvas containing the variables plotted for the data_store.

    Keyword arguments:
    variables -- 2-tuple of HistoVars to be plotted as (x, y)
    data_store -- DataStore instance to plot from
    """
    get_style().cd()

    # If the datasets are weighted, this ensures proper error calculation
    ROOT.TH1.SetDefaultSumw2(True)
    ROOT.TGaxis.SetMaxDigits(3)

    x = variables[0]
    y = variables[1]
    # Only matters what the aspect ratio is
    canvas = ROOT.TCanvas("{0}v{1}".format(
        x.name, y.name
    ), "{0} vs. {1}".format(
        x.title, y.title
    ), 400, 400)
    uniq = utilities.random_str()
    data_store.Draw(
        "{0}:{1}>>h{2}({3},{4},{5},{6},{7},{8})".format(
            # Yeah, it's flipped
            y.name, x.name,
            uniq,
            x.bins, x.min, x.max,
            y.bins, y.min, y.max
        ),
        data_store.cuts
    )
    histo = ROOT.gDirectory.Get("h{0}".format(uniq))
    # TODO styling goes here
    # The histo needs to be drawn to get access to the axes
    histo.Draw("colz")
    canvas.SetRightMargin(0.13)
    xaxis_title = x.title
    yaxis_title = y.title
    if x.units:
        xaxis_title += " [{0}]".format(x.units)
    if y.units:
        yaxis_title += " [{0}]".format(y.units)
    histo.GetXaxis().SetTitle(xaxis_title)
    histo.GetYaxis().SetTitle(yaxis_title)
    histo.Draw("colz")
    canvas.Update()

    # Adding properties to canvas means they won't get garbage collected
    # when canvas is returned
    canvas.h = histo

    return canvas


def plot_fit(workspace, pdfs, bins=70, pull=True):
    """Return a TCanvas of the data and pdfs in workspace.

    Assumes that the first value in pdfs is the total fit PDF.
    Keyword arguments:
    workspace -- RooWorkspace containing the data, variables, fit, and PDFs
    pdfs -- List of tuples of the form
        `[("pdf_name_in_workspace", "Pretty Legend Name")...]`
    var -- String of the variable to to plotted, as named in the workspace
    """
    fit_var = workspace.obj("fit_var").GetString().Data()
    log.info("Plotting variable {0}".format(fit_var))

    get_style().cd()

    # Force exponents
    ROOT.TGaxis.SetMaxDigits(3)

    x = workspace.var(fit_var)
    total_pdf = workspace.pdf(pdfs[0][0])
    frame = x.frame()

    # TODO magic string
    workspace.data("data").plotOn(
        frame,
        ROOT.RooFit.Name("theData"),
        ROOT.RooFit.Binning(bins or config.num_bins),
        ROOT.RooFit.MarkerSize(0.5)
    )
    for idx, pdf in enumerate(pdfs[1:]):
        total_pdf.plotOn(
            frame,
            ROOT.RooFit.Name("component_{0}".format(idx)),
            ROOT.RooFit.Components(pdf[0]),
            ROOT.RooFit.LineColor(line_colour(idx)),
            ROOT.RooFit.LineStyle(line_style(idx + 2)),
            ROOT.RooFit.FillColor(fill_colour(idx)),
            ROOT.RooFit.FillStyle(fill_style(idx)),
            ROOT.RooFit.DrawOption("l")
        )
    total_pdf.plotOn(
        frame,
        ROOT.RooFit.Name("theFit"),
        ROOT.RooFit.LineColor(ROOT.kBlue + 1)
    )

    legend = ROOT.TLegend(0.5, 0.9, 0.175, 0.8 - (0.1*idx))
    legend.SetTextSize(16)
    legend.AddEntry(frame.findObject("theData"), "Data", "ep")
    legend.AddEntry(frame.findObject("theFit"), "Fit", "l")
    for i in range(idx + 1):
        pdf = frame.findObject("component_{0}".format(i))
        pdf_name = pdfs[1 + i][1]
        legend.AddEntry(pdf, pdf_name, "l")

    # Create a canvas of two pads, drawing the distribution and fit(s)
    # on a larger canvas above the pull plot
    c_name = "canvas_{0}".format(utilities.random_str())
    canvas = ROOT.TCanvas(c_name, c_name, 400, 500)
    if pull:
        # The pull plot is the difference between the total PDF and the
        # data, divided by the the error on that difference.
        # The y-axis values can be interpreted as sigmas.
        pull_frame = x.frame(ROOT.RooFit.Title("Pull Plot"))
        pull_frame.addPlotable(frame.pullHist(), "BX0")
        pull_frame.GetXaxis().SetTitle("")
        # Show +/- 5 sigma labels
        pull_frame.SetMaximum(5)
        pull_frame.SetMinimum(-5)
        pull_frame.GetYaxis().SetNdivisions(503)
        pull_frame.GetYaxis().SetTitle("#Delta/#sigma")
        # Hide x-axis labels
        pull_frame.GetXaxis().SetLabelOffset(99)
        canvas.Divide(1, 2)
        canvas.cd(1)
        ROOT.gPad.SetPad(0, 0.25, 1, 1)
        canvas.cd(2)
        ROOT.gPad.SetPad(0, 0, 1, 0.25)
        pull_frame.Draw()
        x_min = pull_frame.GetXaxis().GetXmin()
        x_max = pull_frame.GetXaxis().GetXmax()
        l1 = ROOT.TLine(
            x_min, 2,
            x_max, 2
        )
        l2 = ROOT.TLine(
            x_min, -2,
            x_max, -2
        )
        l1.SetLineColor(ROOT.kRed)
        l2.SetLineColor(ROOT.kRed)
        l1.Draw()
        l2.Draw()
        canvas.l1 = l1
        canvas.l2 = l2
        canvas.cd(1)
    frame.Draw("L")
    legend.Draw()

    # Change the y-axis label "Events" to "Candidates"
    y_axis = frame.GetYaxis()
    y_axis.SetTitle(y_axis.GetTitle().replace("Events", "Candidates"))
    if x.getUnit() != "":
        # For consistency, change unit braces from () to []
        x_axis = frame.GetXaxis()
        # Title components split by spaces, the last in the units
        x_title = x_axis.GetTitle().split(" ")
        x_units = x_title[-1].replace("(", "[").replace(")", "]")
        x_axis.SetTitle(" ".join(x_title[0:-1] + [x_units]))

    canvas.l = legend

    return canvas


def get_style(proportional=False, serif=True):
    """Return a TStyle mimicing the official LHCb style.

    Stolen from rootpy/plotting/style/lhcb/style.py
    Keyword arguments:
    proportional -- If True, draw text proportional to canvas size it
        resides in, else draw it with an absolute size in px (default False)
    serif -- If True, draw text with Times New Roman, else with Helvetica
    """
    # See docs for font information
    # http://root.cern.ch/root/htmldoc/TAttText
    precision = [3, 2][proportional]
    typeface = [4, 13][serif]

    font = 10*typeface + precision
    line_width = 2
    if proportional:
        text_size = 0.05
    else:
        text_size = 16

    style = ROOT.TStyle("myStyle",  "myStyle")

    # Colours
    style.SetCanvasBorderMode(0)
    style.SetCanvasColor(0)
    style.SetFillColor(0)
    style.SetLegendFillColor(0)
    style.SetFillStyle(1001)
    style.SetFrameBorderMode(0)
    style.SetFrameFillColor(0)
    style.SetLegendBorderSize(0)
    style.SetPadBorderMode(0)
    style.SetPadColor(0)
    style.SetPalette(1)
    style.SetStatColor(0)

    # Paper and margin sizes
    style.SetPadBottomMargin(0.16)
    style.SetPadLeftMargin(0.14)
    style.SetPadRightMargin(0.05)
    style.SetPadTopMargin(0.05)

    # Font
    style.SetLabelFont(font, "xyz")
    style.SetLabelSize(text_size, "xyz")
    style.SetTextFont(font)
    style.SetTextSize(text_size)
    style.SetLegendFont(font)
    style.SetTitleFont(font)
    style.SetTitleFont(font, "xyz")
    if proportional:
        style.SetTitleSize(1.1*text_size, "xyz")
    else:
        style.SetTitleSize(1.1*text_size, "xyz")

    # Lines and markers
    style.SetFrameLineWidth(line_width)
    style.SetFuncWidth(line_width)
    style.SetGridWidth(line_width)
    style.SetHistLineWidth(line_width)
    style.SetLineStyleString(2, "[12 12]")
    style.SetLineWidth(line_width)
    style.SetMarkerSize(1.0)
    style.SetMarkerStyle(20)

    # Label offsets
    style.SetLabelOffset(0.010, "xy")

    # Decorations.
    style.SetOptFit(0)
    style.SetOptStat(0)
    style.SetOptTitle(0)
    style.SetStatFormat("6.3g")

    # Titles
    style.SetTitleBorderSize(0)
    style.SetTitleFillColor(0)
    style.SetTitleFont(font, "title")
    style.SetTitleH(0.05)
    if proportional:
        style.SetTitleOffset(1, "xy")
        style.SetTitleOffset(1.2, "z")
    else:
        style.SetTitleOffset(1.5, "x")
        style.SetTitleOffset(1.5, "yz")
    style.SetTitleStyle(0)
    style.SetTitleW(1.0)
    style.SetTitleX(0.0)
    style.SetTitleY(1.0)

    # Statistics box
    style.SetStatBorderSize(0)
    style.SetStatFont(font)
    style.SetStatFontSize(0.05)
    style.SetStatH(0.15)
    style.SetStatW(0.25)
    style.SetStatX(0.9)
    style.SetStatY(0.9)

    # Tick marks
    style.SetPadTickX(1)
    style.SetPadTickY(1)

    # Divisions: only 5 in x to avoid label overlaps
    style.SetNdivisions(505, "xy")

    # Smoother colour palette
    contours = 100
    stops = array("d", [0.00, 0.34, 0.61, 0.84, 1.00])
    red   = array("d", [0.00, 0.00, 0.87, 1.00, 0.51])
    green = array("d", [0.00, 0.81, 1.00, 0.20, 0.00])
    blue  = array("d", [0.51, 1.00, 0.12, 0.00, 0.00])
    style.SetNumberContours(contours)
    ROOT.TColor.CreateGradientColorTable(
        len(stops), stops, red, green, blue, contours
    )

    return style
