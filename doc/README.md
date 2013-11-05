Lc2pXX
======

The [Urania](http://lhcb-release-area.web.cern.ch/LHCb-release-area/DOC/urania/) package `Lc2pXX` is the main code repository for the [Lambda_c DeltaACP analysis](https://twiki.cern.ch/twiki/bin/viewauth/LHCbPhysics/LcTophhDACP).
It consists primarily of a Python module, also called `Lc2pXX`, and a set of Python scripts.
The module allows easy manipulation of the appropriate ntuples, such as fitting and plotting, which the scripts exploit.

Installation
------------

To use the Python module, just `SetupUrania` and then `import Lc2pXX` anywhere in Python.
To edit the package:

    SetupUrania --build-env
    getpack Lc2pXX
    cd Phys/Lc2pXX/cmt
    cmt make

Then you can run anything in `scripts/python`, or create new ones.

After modifying the `Lc2pXX` *module*, you need to tell CMT to "recompile" it with `cmt make`.

Purpose
-------

The Lc2pXX Python module is *not* intended as the be-all and end-all of the analysis.
The incomplete list of features, both current and planned, includes:

* Fitting to any variables deemed necessary (so far only the Lambda_c invariant mass);
* Production of publication-ready plots of fits and variables, including comparisons across different datasets;
* Retrieval and manipulation of data (ROOT ntuples) required for the analysis; and
* Calculation of interesting quantities, such as efficiencies and branching fractions.

In general, the analyst will link together such features in a script dependent on this module which performs a single task, or a series of closely related tasks.
A set of examples is given in `scripts/python`.

Again, the module is not intended to contain a monolithic `do_analysis` method.

Contributing
------------

If you are contributing to the Lc2pXX package, the style guide is approximate to the [PEP8 guide](http://www.python.org/dev/peps/pep-0008/).
The most important points are:

* Lines of code are a maximum of 80 characters long, and should not have any trailing whitespace;
* Variables, functions, and modules are `lower_case`, but classes are `CamelCase`;
* Indentation is four spaces;
* Two blank lines between function and class definitions (except inside class definitions where it is one blank line), and one blank line terminating every script;
* Concise and comprehensive comments, particularly for [function docstrings]((http://www.python.org/dev/peps/pep-0257/);
* There's no need to align assignments, `=`, or dictionaries, `:`.

This all seems pedantic, but consistency is key to readable, maintainable code.

Once you've made your contribution, create a commit with a descriptive log message (e.g. "Fixed a bug where ClassName.method_name would add two arguments rather than divide.", not "Fixed addition bug.").
You don't need to add too many details like the date and the author; that's what the version control is for.

Authors
-------

* Alex Pearce `<alex.pearce@cern.ch>`

