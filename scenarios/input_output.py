import os
import time
import json
import argparse

import numpy as np
from lxml import etree

import openquake.hazardlib.geo as geo

import shakemap.grind.fault as fault
from shakemap.utils.ecef import latlon2ecef, ecef2latlon
from shakemap.utils.vector import Vector
from shakemap.utils.timeutils import ShakeDateTime

from scenarios.utils import get_event_id
from scenarios.utils import get_fault_edges


def parse_bssc2014_ucerf(rupts, args):
    """
    This function is to parse the UCERF3 json file format. The ruptures in 
    UCERF3 are very complex and so we don't exepct to get other rupture lists
    in this format. 
    :param rupts:
        Python translation of json using json.load. 
    :param args:
        argparse object. 
    :returns:
        Dictionary of rupture information.
    """
    rlist = []
    nrup = len(rupts['events'])

    if args.index:
        iter = args.index
        iter = map(int, iter)
    else:
        iter = range(nrup)

    for i in iter:
        event_name = rupts['events'][i]['name']
        short_name = event_name.split('EllB')[0].split(
            'Shaw09')[0].split('2011')[0].split('HB08')[0].rstrip()
        magnitude = rupts['events'][i]['magnitude']
        dip = rupts['events'][i]['dip']
        rake = rupts['events'][i]['rake']
        width = rupts['events'][i]['width']

        sections = np.array(rupts['events'][i]['sections'])
        nsections = len(sections)

        secind = 0
        new_seg_ind = []
        rev = np.array([[]])
        xp0 = np.array([[]])
        xp1 = np.array([[]])
        yp0 = np.array([[]])
        yp1 = np.array([[]])
        zp = np.array([[]])
        dip_sec = np.array([[]])
        strike_sec = np.array([[]])
        width_sec = np.array([[]])
        for j in range(0, nsections):
            trace_sec = np.array(sections[j]['resampledTrace'])
            top_sec_lon = trace_sec[:, 0]
            top_sec_lat = trace_sec[:, 1]
            top_sec_z = trace_sec[:, 2]
            n_sec_trace = len(trace_sec) - 1
            dip_sec = np.append(dip_sec, np.repeat(
                sections[j]['dip'], n_sec_trace))
            dipDir_sec = np.repeat(sections[j]['dipDir'], n_sec_trace)
            strike_sec = np.append(strike_sec, dipDir_sec - 90)
            width_sec = np.append(width_sec, np.repeat(
                sections[j]['width'], n_sec_trace))
            rev_sec = sections[j]['reversed']
            rev = np.append(rev, np.repeat(rev_sec, n_sec_trace))
            xp0_sec = top_sec_lon[range(0, n_sec_trace)]
            xp1_sec = top_sec_lon[range(1, n_sec_trace + 1)]
            yp0_sec = top_sec_lat[range(0, n_sec_trace)]
            yp1_sec = top_sec_lat[range(1, n_sec_trace + 1)]
            zp_sec = top_sec_z[range(0, n_sec_trace)]
            if rev_sec == False:
                xp0 = np.append(xp0, xp0_sec)
                xp1 = np.append(xp1, xp1_sec)
                yp0 = np.append(yp0, yp0_sec)
                yp1 = np.append(yp1, yp1_sec)
                zp = np.append(zp, zp_sec)
            else:
                xp0 = np.append(xp0, xp0_sec[::-1])
                xp1 = np.append(xp1, xp1_sec[::-1])
                yp0 = np.append(yp0, yp0_sec[::-1])
                yp1 = np.append(yp1, yp1_sec[::-1])
                zp = np.append(zp, zp_sec[::-1])
            new_seg_ind.extend([secind] * n_sec_trace)
            secind = secind + 1

        flt = fault.Fault.fromTrace(xp0, yp0, xp1, yp1, zp,
                                    width_sec, dip_sec, strike=strike_sec,
                                    reference=args.reference)
        flt._segment_index = new_seg_ind

        quads = flt.getQuadrilaterals()

        id_str, eventsourcecode, real_desc, selquad = get_event_id(
            event_name, magnitude, args.directivity, args.dirind, quads)

        event = {'lat': 0,
                 'lon': 0,
                 'depth': 0,
                 'mag': magnitude,
                 'rake':rake,
                 'id': id_str,
                 'locstring': event_name,
                 'type': 'U',  # overwrite later
                 'timezone': 'UTC'}
        event['time'] = ShakeDateTime.utcfromtimestamp(int(time.time()))
        event['created'] = ShakeDateTime.utcfromtimestamp(int(time.time()))

        #-----------------------------------------------------------------------
        # Hypocenter placement
        #-----------------------------------------------------------------------
        # top left
        pp0 = Vector.fromPoint(geo.point.Point(
            selquad[0].longitude, selquad[0].latitude, selquad[0].depth))
        # top right
        pp1 = Vector.fromPoint(geo.point.Point(
            selquad[1].longitude, selquad[1].latitude, selquad[1].depth))
        # bottom right
        pp2 = Vector.fromPoint(geo.point.Point(
            selquad[2].longitude, selquad[2].latitude, selquad[2].depth))
        # bottom left
        pp3 = Vector.fromPoint(geo.point.Point(
            selquad[3].longitude, selquad[3].latitude, selquad[3].depth))
        dxp = 0.5
        dyp = 0.5
        mp0 = pp0 + (pp1 - pp0) * dxp
        mp1 = pp3 + (pp2 - pp3) * dxp
        rp = mp0 + (mp1 - mp0) * dyp
        hlat, hlon, hdepth = ecef2latlon(rp.x, rp.y, rp.z)

        event['lat'] = hlat
        event['lon'] = hlon
        event['depth'] = hdepth

        #-----------------------------------------------------------------------
        # For map display get trace of top/bottom edges and
        # put them in order.
        #-----------------------------------------------------------------------

        edges = get_fault_edges(quads, rev)

        rdict = {'fault':flt,
                 'event':event,
                 'edges':edges,
                 'id_str':id_str,
                 'short_name':short_name,
                 'real_desc':real_desc,
                 'eventsourcecode':eventsourcecode
                }
        rlist.append(rdict)

    return rlist
    
def parse_json(rupts, args):
    """
    This will hopefully be the most general json format for rutpures.
    Assumes top of ruputure is horizontal and continuous, and that
    there is only one segment per rupture (but multiple quads).
    Users first and last point to get average strike, which is used
    for all quads. 

    :param rupts:
        Python translation of json using json.load. 
    :param args:
        argparse object. 
    :returns:
        Dictionary of rupture information.
    """
    rlist = []
    nrup = len(rupts['events'])

    if args.index:
        iter = args.index
        iter = map(int, iter)
    else:
        iter = range(nrup)

    for i in iter:
        event_name = rupts['events'][i]['desc']
        short_name = event_name
        id = rupts['events'][i]['id']
        magnitude = rupts['events'][i]['mag']
        dip = rupts['events'][i]['dip']
        rake = rupts['events'][i]['rake']
        width = rupts['events'][i]['width']
        ztor = rupts['events'][i]['ztor']

        lons = rupts['events'][i]['lons']
        lats = rupts['events'][i]['lats']
        xp0 = np.array(lons[:-1])
        xp1 = np.array(lons[1:])
        yp0 = np.array(lats[:-1])
        yp1 = np.array(lats[1:])
        zp = np.ones_like(xp0) * ztor
        dips = np.ones_like(xp0) * dip
        widths = np.ones_like(xp0) * width

        P1 = geo.point.Point(lons[0], lats[0])
        P2 = geo.point.Point(lons[-1], lats[-1])
        strike = np.array([P1.azimuth(P2)])

        flt = fault.Fault.fromTrace(xp0, yp0, xp1, yp1, zp,
                                    widths, dips, strike=strike,
                                    reference=args.reference)
        flt._segment_index = np.zeros_like(xp0)

        quads = flt.getQuadrilaterals()

        id_str, eventsourcecode, real_desc, selquad = get_event_id(
            event_name, magnitude, args.directivity, args.dirind,
            quads, id = id)

        event = {'lat': 0,
                 'lon': 0,
                 'depth': 0,
                 'mag': magnitude,
                 'rake':rake,
                 'id': id_str,
                 'locstring': event_name,
                 'type': 'U',  # overwrite later
                 'timezone': 'UTC'}
        event['time'] = ShakeDateTime.utcfromtimestamp(int(time.time()))
        event['created'] = ShakeDateTime.utcfromtimestamp(int(time.time()))

        #-----------------------------------------------------------------------
        # Hypocenter placement
        #-----------------------------------------------------------------------
        # top left
        pp0 = Vector.fromPoint(geo.point.Point(
            selquad[0].longitude, selquad[0].latitude, selquad[0].depth))
        # top right
        pp1 = Vector.fromPoint(geo.point.Point(
            selquad[1].longitude, selquad[1].latitude, selquad[1].depth))
        # bottom right
        pp2 = Vector.fromPoint(geo.point.Point(
            selquad[2].longitude, selquad[2].latitude, selquad[2].depth))
        # bottom left
        pp3 = Vector.fromPoint(geo.point.Point(
            selquad[3].longitude, selquad[3].latitude, selquad[3].depth))
        dxp = 0.5
        dyp = 0.5
        mp0 = pp0 + (pp1 - pp0) * dxp
        mp1 = pp3 + (pp2 - pp3) * dxp
        rp = mp0 + (mp1 - mp0) * dyp
        hlat, hlon, hdepth = ecef2latlon(rp.x, rp.y, rp.z)

        event['lat'] = hlat
        event['lon'] = hlon
        event['depth'] = hdepth

        #-----------------------------------------------------------------------
        # For map display get trace of top/bottom edges and
        # put them in order.
        #-----------------------------------------------------------------------
        edges = get_fault_edges(quads)

        rdict = {'fault':flt,
                 'event':event,
                 'edges':edges,
                 'id_str':id_str,
                 'short_name':short_name,
                 'real_desc':real_desc,
                 'eventsourcecode':eventsourcecode
                }
        rlist.append(rdict)

    return rlist

