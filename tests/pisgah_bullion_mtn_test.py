# stdlib imports
import os
import sys
import io

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

    # make a temporary directory
    p = str(tmpdir.mkdir("sub"))
    jsonfile = 'rupture_sets/BSSC2014/UCERF3_EventSet_All.json'

    # Run mkinputdir
    cmd = 'mkinputdir -f %s -i 46 -s %s' % (jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())

    # Check for errors
    assert se == b''

    # Run mkscenariogrids
    datadir = os.path.join(p, 'data')
    id_str = next(os.walk(datadir))[1]
    v = 'tests/data/SCalVs30.grd'
    cmd = 'mkscenariogrids -e %s -g NSHMP14acr -r 0.1 '\
          '-v %s -s %s' %(id_str[0], v, p)
    rc,so,se = get_command_output(cmd)

    # Check for errors
    assert se == b''

    
