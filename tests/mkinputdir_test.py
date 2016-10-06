# stdlib imports
import os
import os.path
import sys
import io

# third party
import numpy as np
import pytest

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)

from shakemap.grind.fault import Fault
from shakemap.utils.exception import ShakeMapException
from impactutils.io.cmd import get_command_output
from shakemap.grind.fault import get_local_unit_slip_vector
from shakemap.grind.fault import get_quad_slip

def test_pisgah_bullion_mtn(tmpdir):
    # a segment of this fault causes a division by zero error that
    # we trap for and are testing here.

    # make a temporary directory
    p = tmpdir.mkdir("sub")
    jsonfile = os.path.join(shakedir, 'tests/data/eventdata/UCERF3_EventSet_All.json')
    script = os.path.join(shakedir,'mkinputdir')
    cmd = '%s -f %s -i 46 -s %s' % (script,jsonfile, p)
    rc,so,se = get_command_output(cmd)
    if se != b'':
        print(so.decode())
        print(se.decode())
    assert se == b''
