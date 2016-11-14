# stdlib imports
import os
import sys
import filecmp

# third party
import pytest
import tempfile

from impactutils.io.cmd import get_command_output
from impactutils.testing.grd import cmp

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..'))
sys.path.insert(0, shakedir)


def test_pisgah_bullion_mtn(tmpdir):
    # a segment of this rupture causes a division by zero error that
    # we trap for and are testing here.

    # make a temporary directory; read in rupture file
    p = os.path.join(str(tmpdir), "sub")
    if not os.path.exists(p):
        os.makedirs(p)
    jsonfile = 'rupture_sets/BSSC2014/UCERF3_EventSet_All.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/pisgahbullionmtnmesq_m7p27_se/input')
    targetinput = 'tests/output/pisgah_bullion_mtn/input'

    #---------------------------------------------------------------------------
    # First test mkinputdir
    #---------------------------------------------------------------------------

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 46 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())

    # Check for errors/warnings
    assert se == b''

    # Check output files

    # Note: Not checking event.xml because the timestamp breaks cmp comparison.
    #       Would need to parse and to tag comaprisons. Not worth it. 

    target = os.path.join(targetinput, 'pisgahbullionmtnmesq_m7p27_se_for-map_fault.txt')
    test = os.path.join(testinput, 'pisgahbullionmtnmesq_m7p27_se_for-map_fault.txt')
    assert filecmp.cmp(test, target) is True

    target = os.path.join(targetinput, 'pisgahbullionmtnmesq_m7p27_se-fault-for-calc.txt')
    test = os.path.join(testinput, 'pisgahbullionmtnmesq_m7p27_se-fault-for-calc.txt')
    assert filecmp.cmp(test, target) is True

    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    #---------------------------------------------------------------------------
    datadir = os.path.join(p, 'data')
    v = 'tests/data/SCalVs30.grd'
    cmd = 'mkscenariogrids -e %s -g nshmp14_acr -r 0.1 '\
          '-v %s -s %s' %('pisgahbullionmtnmesq_m7p27_se', v, p)
    rc,so,se = get_command_output(cmd)

    # Check for errors/warnings
    assert se == b''

    # Check output files
    target = os.path.join(targetinput, 'mi_estimates.grd')
    test = os.path.join(testinput, 'mi_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'mi_sd.grd')
    test = os.path.join(testinput, 'mi_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pga_estimates.grd')
    test = os.path.join(testinput, 'pga_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pga_sd.grd')
    test = os.path.join(testinput, 'pga_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pgv_estimates.grd')
    test = os.path.join(testinput, 'pgv_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pgv_sd.grd')
    test = os.path.join(testinput, 'pgv_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa03_estimates.grd')
    test = os.path.join(testinput, 'psa03_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa03_sd.grd')
    test = os.path.join(testinput, 'psa03_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa10_estimates.grd')
    test = os.path.join(testinput, 'psa10_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa10_sd.grd')
    test = os.path.join(testinput, 'psa10_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa30_estimates.grd')
    test = os.path.join(testinput, 'psa30_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa30_sd.grd')
    test = os.path.join(testinput, 'psa30_sd.grd')
    cmp(test, target)

def test_pisgah_bullion_mtn_shallow(tmpdir):
    # Same as before but this time check that NSHMPshallow option also
    # gives the same results. 

    # make a temporary directory; read in rupture file
    p = os.path.join(str(tmpdir), "sub")
    if not os.path.exists(p):
        os.makedirs(p)
    jsonfile = 'rupture_sets/BSSC2014/UCERF3_EventSet_All.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/pisgahbullionmtnmesq_m7p27_se/input')
    targetinput = 'tests/output/pisgah_bullion_mtn/input'

    #---------------------------------------------------------------------------
    # First test mkinputdir
    #---------------------------------------------------------------------------

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 46 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())

    # Check for errors/warnings
    assert se == b''

    # Check output files

    # Note: Not checking event.xml because the timestamp breaks cmp comparison.
    #       Would need to parse and to tag comaprisons. Not worth it. 

    target = os.path.join(targetinput, 'pisgahbullionmtnmesq_m7p27_se_for-map_fault.txt')
    test = os.path.join(testinput, 'pisgahbullionmtnmesq_m7p27_se_for-map_fault.txt')
    assert filecmp.cmp(test, target) is True

    target = os.path.join(targetinput, 'pisgahbullionmtnmesq_m7p27_se-fault-for-calc.txt')
    test = os.path.join(testinput, 'pisgahbullionmtnmesq_m7p27_se-fault-for-calc.txt')
    assert filecmp.cmp(test, target) is True

    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    #---------------------------------------------------------------------------
    datadir = os.path.join(p, 'data')
    v = 'tests/data/SCalVs30.grd'
    cmd = 'mkscenariogrids -e %s -g nshmp14_shallow -r 0.1 '\
          '-v %s -s %s' %('pisgahbullionmtnmesq_m7p27_se', v, p)
    rc,so,se = get_command_output(cmd)

    # Check for errors/warnings
    assert se == b''

    # Check output files
    target = os.path.join(targetinput, 'mi_estimates.grd')
    test = os.path.join(testinput, 'mi_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'mi_sd.grd')
    test = os.path.join(testinput, 'mi_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pga_estimates.grd')
    test = os.path.join(testinput, 'pga_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pga_sd.grd')
    test = os.path.join(testinput, 'pga_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pgv_estimates.grd')
    test = os.path.join(testinput, 'pgv_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'pgv_sd.grd')
    test = os.path.join(testinput, 'pgv_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa03_estimates.grd')
    test = os.path.join(testinput, 'psa03_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa03_sd.grd')
    test = os.path.join(testinput, 'psa03_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa10_estimates.grd')
    test = os.path.join(testinput, 'psa10_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa10_sd.grd')
    test = os.path.join(testinput, 'psa10_sd.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa30_estimates.grd')
    test = os.path.join(testinput, 'psa30_estimates.grd')
    cmp(test, target)

    target = os.path.join(targetinput, 'psa30_sd.grd')
    test = os.path.join(testinput, 'psa30_sd.grd')
    cmp(test, target)


if __name__ == "__main__":
    td = tempfile.TemporaryDirectory()
    test_pisgah_bullion_mtn(td.name)
    test_pisgah_bullion_mtn_shallow(td.name)
