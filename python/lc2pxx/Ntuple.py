import logging as log

import ROOT
import numpy as np

from lc2pxx import config, utilities

class Ntuple(ROOT.TChain):
    """Wrapper class for TChain.

    Makes TChains faster to loop through and a little more Pythonesque.
    Use exactly as you would a TChain, except use set_entry for GetEntry,
    add for Add, and val for retrieving branch values.
    To loop, simply use
        for entry in my_ntuple:
            # entry is the current entry number
            ...
    Looping can be speeded up with the use of activate_branches.
    """
    # ROOT TBranch types corresponding the numpy types
    types_map = {
        # int-like
        "B": "int8",
        "b": "uint8",
        "S": "int16",
        "s": "uint16",
        "I": "int32",
        "i": "uint32",
        "L": "int64",
        "l": "uint64",
        "O": "bool",
        # float-like
        "F": "float32",
        "D": "float64"
    }
    def __init__(self, name):
        """Initialise an Ntuple object.

        Keyword arguments:
        name -- Name of the TTree this object represents
        """
        log.info("Initialising Ntuple")
        super(Ntuple, self).__init__(name)
        # Current entry number
        self.entry = -1
        # Total number of entries
        self.entries = 0
        # Dictionary of branch names to array pointers
        # Shorthand access to this is provided by the val method
        self.vars = {}
        # True to show a progress bar when iterating over self
        self.show_progress = True

    def __iter__(self):
        """Ntuple is iterable."""
        # Reset the current entry
        self.entry = -1
        return self

    def next(self):
        """Set current entry to the next, returning the entry number."""
        self.entry += 1
        if self.show_progress:
            utilities.progress_bar(1.*self.entry/self.entries)
        if self.set_entry(self.entry) <= 0:
            if self.show_progress:
                # Newline after the progress bar
                print ""
            raise StopIteration
        return self.entry

    @classmethod
    def from_ntuple(cls, ntuple):
        """Instantiate a new Ntuple from an existing one."""
        return cls(ntuple.GetName())

    @classmethod
    def from_tree(cls, tree):
        """Instantiate a new Ntuple from a TTree instance."""
        ntuple = cls(tree.GetName())
        # ROOT gymnastics
        ntuple.add(tree.GetCurrentFile().GetEndpointUrl().GetFile())
        return ntuple

    def add(self, path):
        """Add a TTree to the chain. Superseeds TChain.Add."""
        log.info("Adding {0} to Ntuple".format(path))
        ret = self.Add(path)
        self.entries = self.GetEntries()
        self.setup_branches()
        return ret

    def add_friend(self, tree_name, path):
        """Add a friend tree. Superseeds TChain.AddFriend."""
        log.info("Adding friend tree {0} to Ntuple".format(path))
        ret = self.AddFriend(tree_name, path)
        self.setup_branches()
        return ret

    def val(self, var, reference=False):
        """Return the value of var for the current entry.

        Keyword arguments:
        var -- String of the variable value to be retrieved
        reference -- If True, the array pointer is returned, else the value
        of the first array element (i.e. the value itself)
        """
        return self.vars[var] if reference else self.vars[var][0]

    def set_entry(self, entry):
        """Set the current entry to entry. Superseeds TChain.GetEntry."""
        self.entry = entry
        return self.GetEntry(entry)

    def activate_branches(self, branches, append=False):
        """Activate branches, deactivating all others if not append.

        Keyword arguments:
        branches -- List of strings of branches to activate
        append -- Do not deactivate all other branches if True
        (default: False)
        """
        if not append:
            self.SetBranchStatus("*", 0)
        for branch in branches:
            self.SetBranchStatus(branch, 1)

    def setup_branches(self):
        """Populate the vars dict with appropriate-type numpy arrays."""
        # This is subtle. GetListOfBranches returns a TObjArray pointer,
        # and so modifying this, by appending friend branches for instance,
        # changes the original TTree instance. The friend tree concept is
        # supposed to prevent this. So, copy the list and modify that.
        branches = list(self.GetListOfBranches())
        # GetListOfBranches does not include branches of friends,
        # so we must append them manually.
        # If GetListOfFriends is called before any friends are added,
        # the TList pointer is the null pointer. Helpful!
        # We use `or []` here, but checking for None would be equally valid
        # to avoid a "iteration over non-sequence" TypeError.
        friends = self.GetListOfFriends() or []
        for friend in friends:
            branches += friend.GetTree().GetListOfBranches()
        for branch in branches:
            name = branch.GetName()
            title = branch.GetTitle()
            # Don't bind to branches containing arrays
            if title.find("[") >= 0: continue
            btype = title.split("/")[-1]
            dtype = Ntuple.types_map[btype]
            # Use the key value if it exists, else create one
            try:
                z = self.vars[name]
            except KeyError:
                z = np.zeros(1, dtype=dtype)
                self.vars[name] = z
            self.SetBranchAddress(name, z)

    def copy_selected(self, cuts):
        """Return a new Ntuple instance containing only the entries
        passing the requirements in cuts.

        Creates a temporary file in which the copied tree resides,
        containing only branches which are activated in `self`.
        """
        temp_file = utilities.create_temp_file()
        temp_file_path = temp_file.GetEndpointUrl().GetFile()
        # Copied tree exists in temp_file
        sel_tree = self.CopyTree(cuts)
        sel_tree.Write()
        # Create a new instance of the class of the current object.
        # If the caller is a child class of Ntuple, this will
        # create a new instance of that child class
        sel_ntuple = self.__class__.from_ntuple(self)
        sel_ntuple.SetName(sel_tree.GetName())
        sel_ntuple.SetTitle(sel_tree.GetTitle())
        # If we closed this earlier, sel_tree would've been deleted
        temp_file.Close()
        sel_ntuple.add(temp_file_path)
        return sel_ntuple

    def __enter__(self):
        """Use with e.g. `with ntuple.copy_selected(...) as nt:`"""
        return self

    def __exit__(self, type, value, traceback):
        """Deletes the file on disk belonging to this ntuple."""
        utilities.delete_temp_file(self.GetFile())

