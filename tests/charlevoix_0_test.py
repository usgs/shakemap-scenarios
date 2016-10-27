# stdlib imports
import os
import sys
import io
import filecmp

# third party
import numpy as np
import pytest

from shakemap.grind.fault import Fault
from shakemap.utils.exception import ShakeMapException
from shakemap.grind.fault import get_local_unit_slip_vector
from shakemap.grind.fault import get_quad_slip

from impactutils.io.cmd import get_command_output
from impactutils.testing.grd import cmp


def test_charlevoix_0(tmpdir):
    # a segment of this fault causes a division by zero error that
    # we trap for and are testing here.

    # make a temporary directory; read in rupture file
    p = str(tmpdir.mkdir("sub"))
    jsonfile = 'rupture_sets/BSSC2014/bssc2014_ceus.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/charlevoix_0_m7p_se/input')
    targetinput = 'tests/output/charlevoix_0_m7p_se'

    #---------------------------------------------------------------------------
    # First test mkinputdir
    #---------------------------------------------------------------------------

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 0 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())

    # Check for errors/warnings
    assert se == b''

    # Check output files

    # Note: Not checking event.xml because the timestamp breaks cmp comparison.
    #       Would need to parse and to tag comaprisons. Not worth it. 

    target = os.path.join(targetinput, 'charlevoix_0_m7p_se_for-map_fault.txt')
    test = os.path.join(testinput, 'charlevoix_0_m7p_se_for-map_fault.txt')
    assert filecmp.cmp(test, target) is True

    target = os.path.join(targetinput, 'charlevoix_0_m7p_se-fault-for-calc.txt')
    test = os.path.join(testinput, 'charlevoix_0_m7p_se-fault-for-calc.txt')
    assert filecmp.cmp(test, target) is True

    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    #---------------------------------------------------------------------------
    datadir = os.path.join(p, 'data')
    v = 'tests/data/CharlevoixVs30.grd'
    cmd = 'mkscenariogrids -e %s -g NSHMP14scr_rlme -r 0.1 '\
          '-v %s -s %s' %('charlevoix_0_m7p_se', v, p)
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

