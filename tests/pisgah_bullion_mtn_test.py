# stdlib imports
import os
import sys
import io
from filecmp import cmp

# third party
import numpy as np
import pytest

from shakemap.grind.fault import Fault
from shakemap.utils.exception import ShakeMapException
from impactutils.io.cmd import get_command_output
from shakemap.grind.fault import get_local_unit_slip_vector
from shakemap.grind.fault import get_quad_slip

def test_pisgah_bullion_mtn(tmpdir):
    # a segment of this fault causes a division by zero error that
    # we trap for and are testing here.

    # make a temporary directory; read in rupture file
    p = str(tmpdir.mkdir("sub"))
    jsonfile = 'rupture_sets/BSSC2014/UCERF3_EventSet_All.json'

    # directory holding test and target data for this event
    testinput = os.path.join(p, 'data/pisgahbullionmtnmesq_m7p27_se/input')
    targetinput = 'tests/output/pisgah_bullion_mtn'

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
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'pisgahbullionmtnmesq_m7p27_se-fault-for-calc.txt')
    test = os.path.join(testinput, 'pisgahbullionmtnmesq_m7p27_se-fault-for-calc.txt')
    assert cmp(test, target) is True

    #---------------------------------------------------------------------------
    # Test mkscenariogrids
    #---------------------------------------------------------------------------
    datadir = os.path.join(p, 'data')
    id_str = next(os.walk(datadir))[1]
    v = 'tests/data/SCalVs30.grd'
    cmd = 'mkscenariogrids -e %s -g NSHMP14acr -r 0.1 '\
          '-v %s -s %s' %(id_str[0], v, p)
    rc,so,se = get_command_output(cmd)

    # Check for errors/warnings
    assert se == b''

    # Check output files
    target = os.path.join(targetinput, 'mi_estimates.grd')
    test = os.path.join(testinput, 'mi_estimates.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'mi_sd.grd')
    test = os.path.join(testinput, 'mi_sd.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'pga_estimates.grd')
    test = os.path.join(testinput, 'pga_estimates.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'pga_sd.grd')
    test = os.path.join(testinput, 'pga_sd.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'pgv_estimates.grd')
    test = os.path.join(testinput, 'pgv_estimates.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'pgv_sd.grd')
    test = os.path.join(testinput, 'pgv_sd.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'psa03_estimates.grd')
    test = os.path.join(testinput, 'psa03_estimates.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'psa03_sd.grd')
    test = os.path.join(testinput, 'psa03_sd.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'psa10_estimates.grd')
    test = os.path.join(testinput, 'psa10_estimates.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'psa10_sd.grd')
    test = os.path.join(testinput, 'psa10_sd.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'psa30_estimates.grd')
    test = os.path.join(testinput, 'psa30_estimates.grd')
    assert cmp(test, target) is True

    target = os.path.join(targetinput, 'psa30_sd.grd')
    test = os.path.join(testinput, 'psa30_sd.grd')
    assert cmp(test, target) is True







