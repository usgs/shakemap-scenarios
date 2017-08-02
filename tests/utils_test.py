
import sys
import os
from scenarios.utils import find_rupture

import numpy as np

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)


def test_find_rupture():
    rfile = os.path.join('rupture_sets', 'BSSC2014', 'bssc2014_wus.json')
    ind, result = find_rupture('Grand Valley', rfile)
    assert ind == np.array([250])
    assert result == np.array(['Grand Valley fault'])
