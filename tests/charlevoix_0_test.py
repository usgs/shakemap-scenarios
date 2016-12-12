# stdlib imports
import os
import sys
import filecmp
import shutil

# third party
import pytest
import tempfile

from impactutils.io.cmd import get_command_output
from impactutils.testing.grd import cmp

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..'))
sys.path.insert(0, shakedir)


def test_charlevoix_0(tmpdir):
    # make a temporary directory; read in rupture file
    p = os.path.join(str(tmpdir), "sub")
    if not os.path.exists(p):
        os.makedirs(p)
    jsonfile = 'rupture_sets/BSSC2014/bssc2014_ceus.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/charlevoix_0_m7p_se/input')
    targetinput = 'tests/output/charlevoix_0_m7p_se/input'

    #---------------------------------------------------------------------------
    # First test mkinputdir
    #---------------------------------------------------------------------------

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 0 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())


    # Check output files

    # Note: Not checking event.xml because the timestamp breaks cmp comparison.
    #       Would need to parse and to tag comaprisons. Not worth it. 

    target = os.path.join(targetinput, 'charlevoix_0_m7p_se_for-map_fault.txt')
    test = os.path.join(testinput, 'charlevoix_0_m7p_se_for-map_fault.txt')
    assert filecmp.cmp(test, target) is True


    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    #---------------------------------------------------------------------------
    datadir = os.path.join(p, 'data')
    v = 'tests/data/CharlevoixVs30.grd'
    cmd = 'mkscenariogrids -e %s -g nshmp14_scr_rlme -r 0.1 '\
          '-v %s -s %s' %('charlevoix_0_m7p_se', v, p)
    rc,so,se = get_command_output(cmd)


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

    shutil.rmtree(p)

def test_charlevoix_0_shallow(tmpdir):
    # make a temporary directory; read in rupture file
    p = os.path.join(str(tmpdir), "sub")
    if not os.path.exists(p):
        os.makedirs(p)
    jsonfile = 'rupture_sets/BSSC2014/bssc2014_ceus.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/charlevoix_0_m7p_se/input')
    targetinput = 'tests/output/charlevoix_0_m7p_se/input'

    #---------------------------------------------------------------------------
    # First test mkinputdir
    #---------------------------------------------------------------------------

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 0 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())


    # Check output files

    # Note: Not checking event.xml because the timestamp breaks cmp comparison.
    #       Would need to parse and to tag comaprisons. Not worth it. 

    target = os.path.join(targetinput, 'charlevoix_0_m7p_se_for-map_fault.txt')
    test = os.path.join(testinput, 'charlevoix_0_m7p_se_for-map_fault.txt')
    assert filecmp.cmp(test, target) is True


    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    #---------------------------------------------------------------------------
    datadir = os.path.join(p, 'data')
    v = 'tests/data/CharlevoixVs30.grd'
    cmd = 'mkscenariogrids -e %s -g nshmp14_shallow -r 0.1 '\
          '-v %s -s %s' %('charlevoix_0_m7p_se', v, p)
    rc,so,se = get_command_output(cmd)


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

    shutil.rmtree(p)


def test_charlevoix_0_no_rupture(tmpdir):
    # make a temporary directory; read in rupture file
    p = os.path.join(str(tmpdir), "sub")
    if not os.path.exists(p):
        os.makedirs(p)
    jsonfile = 'rupture_sets/BSSC2014/bssc2014_ceus.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/charlevoix_0_m7p_se/input')
    targetinput = 'tests/output/charlevoix_0_m7p_noflt_se/input'

    #---------------------------------------------------------------------------
    # First test mkinputdir
    #---------------------------------------------------------------------------

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 0 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())


    # Remove rupture file:
    os.remove(os.path.join(testinput, 'rupture.json'))

    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    datadir = os.path.join(p, 'data')
    v = 'tests/data/CharlevoixVs30.grd'
    cmd = 'mkscenariogrids -e %s -g nshmp14_shallow -r 0.1 '\
          '-v %s -s %s' %('charlevoix_0_m7p_se', v, p)
    rc,so,se = get_command_output(cmd)



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

    shutil.rmtree(p)


if __name__ == "__main__":
    td = tempfile.TemporaryDirectory()
    test_charlevoix_0(td.name)
    test_charlevoix_0_shallow(td.name)
    test_charlevoix_0_no_rupture(td.name)

