from Configurables import StrippingReport, AlgorithmCorrelationsAlg
from StrippingConf.Configuration import StrippingConf, StrippingStream

from lc2pxx.booking.StrippingB2DMuNuX import (
    B2DMuNuXAllLinesConf,
    confdict
)

def stripping_sequence_nopids():
    """Return a list of sequences to run and monitor NoPIDs stripping.

    The list contains three sequences:
      1. StreamB2DMuNuXNoPIDs StrippingConf, which runs all the
         semileptonic Lambda_c -> X stripping lines, but without PID cuts
      2. Stripping report on the above
      3. Algorithm that reports correlations in the above stripping lines
    Sequences 2 and 3 aren't strictly necessary, but are nice to have.
    The list can be run by DaVinci with
        DaVinci().appendToMainSequence(stripping_sequence_nopids())
    """
    stream = StrippingStream("StreamB2DMuNuX")
    stream.appendLines(
        B2DMuNuXAllLinesConf("B2DMuNuX", confdict).lines()
    )

    # Create stripping configuration from my stream
    conf = StrippingConf(
        Streams=[stream],
        MaxCandidates=2000,
        AcceptBadEvents=True,
        # Stripping reports already exist in the DST,
        # so put these ones somewhere fake
        HDRLocation="NowhereIsNowHere"
    )

    # Extra reporting
    reporting = StrippingReport(Selections=conf.selections())
    correlations = AlgorithmCorrelationsAlg(Algorithms=conf.selections())

    return [conf.sequence(), reporting, correlations]
