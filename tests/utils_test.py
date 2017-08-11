
import sys
import os
import json

import numpy as np

from shakelib.grind.rupture.origin import Origin

from scenarios.utils import find_rupture
from scenarios.utils import get_extent
from scenarios.utils import get_event_id
from scenarios.input_output import parse_bssc2014_ucerf

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..'))
sys.path.insert(0, shakedir)



def test_get_extent_no_rup():
    origin = Origin({'id': 'test', 'lat': 37.1, 'lon': -122.1,
                     'depth': 5.0, 'mag': 8.5})
    extent = np.array(get_extent(origin))
    np.testing.assert_allclose(extent,
        np.array([[-126.5981497 ],
                  [-117.13214326],
                  [  33.23305437],
                  [  40.77859864]]))
    origin = Origin({'id': 'test', 'lat': 37.1, 'lon': -122.1,
                     'depth': 5.0, 'mag': 6})
    extent = np.array(get_extent(origin))
    np.testing.assert_allclose(extent,
        np.array([[-123.21199895],
                  [-120.9613286 ],
                  [  36.19336348],
                  [  37.99597076]]))

def test_get_hypo_and_event_id():
    jsonfile = os.path.join(
        shakedir, 'rupture_sets/BSSC2014/UCERF3_EventSet_All.json')
    with open(jsonfile) as f:
        rupts = json.load(f)

    args = type('', (), {})()
    args.index = [2]
    args.reference = ''
    args.directivity = True
    args.dirind = 0

    rup = parse_bssc2014_ucerf(rupts, args)[0]
    np.testing.assert_allclose(rup['event']['lat'], 36.376584141401686)
    np.testing.assert_allclose(rup['event']['lon'], -121.54438439782552)
    np.testing.assert_allclose(rup['event']['depth'], 8.96001742487494)

    id_str, eventsourcecode, real_desc = get_event_id(
            'test', rup['event']['mag'], args.directivity, args.dirind,
            rup['rupture'].getQuadrilaterals())
    assert id_str == 'test_m7p26_se~dir0'
    assert eventsourcecode == 'test_m7p26_se'
    assert real_desc == 'Western directivity'

    args.dirind = 1
    rup = parse_bssc2014_ucerf(rupts, args)[0]
    np.testing.assert_allclose(rup['event']['lat'], 36.595051893199994)
    np.testing.assert_allclose(rup['event']['lon'], -121.87197147595805)
    np.testing.assert_allclose(rup['event']['depth'], 8.96001742487494)

    id_str, eventsourcecode, real_desc = get_event_id(
            'test', rup['event']['mag'], args.directivity, args.dirind,
            rup['rupture'].getQuadrilaterals())
    assert id_str == 'test_m7p26_se~dir1'
    assert eventsourcecode == 'test_m7p26_se'
    assert real_desc == 'Bilateral directivity'

    args.dirind = 2
    rup = parse_bssc2014_ucerf(rupts, args)[0]
    np.testing.assert_allclose(rup['event']['lat'], 36.89182649285367)
    np.testing.assert_allclose(rup['event']['lon'], -122.09157302812258)
    np.testing.assert_allclose(rup['event']['depth'], 8.96001742487494)

    id_str, eventsourcecode, real_desc = get_event_id(
            'test', rup['event']['mag'], args.directivity, args.dirind,
            rup['rupture'].getQuadrilaterals())
    assert id_str == 'test_m7p26_se~dir2'
    assert eventsourcecode == 'test_m7p26_se'
    assert real_desc == 'Eastern directivity'



def test_find_rupture():
    rfile = os.path.join('rupture_sets', 'BSSC2014', 'bssc2014_wus.json')
    ind, result = find_rupture('Grand Valley', rfile)
    assert ind == np.array([250])
    assert result == np.array(['Grand Valley fault'])
