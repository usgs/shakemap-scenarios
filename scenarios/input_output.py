import os
import time
import xml.etree.ElementTree as ET
import ast

import numpy as np
from lxml import etree

import openquake.hazardlib.geo as geo

from shakemap.grind.rupture import QuadRupture
from shakemap.grind.origin import Origin
from shakemap.utils.timeutils import ShakeDateTime

from scenarios.utils import get_event_id
from scenarios.utils import get_rupture_edges
from scenarios.utils import get_hypo
from scenarios.utils import rake_to_type


def read_event_xml(file):
    """
    Read event.xml. 

    Args:
        file (str): Path to event.xml file.

    Returns:
        dict: Dictionary with event info.

    """
    eventtree = ET.parse(file)
    eventroot = eventtree.getroot()
    for eq in eventroot.iter('earthquake'):
        id_str = eq.attrib['id']
        magnitude = float(eq.attrib['mag'])
        hlat = float(eq.attrib['lat'])
        hlon = float(eq.attrib['lon'])
        hdepth = float(eq.attrib['depth'])
        if 'rake' in eq.attrib.keys():
            rake = float(eq.attrib['rake'])
        else:
            rake = None
        lstring = eq.attrib['locstring']
        if 'description' in eq.attrib.keys():
            description = eq.attrib['description']
        else:
            description = ""
        if 'type' in eq.attrib.keys():
            mech = eq.attrib['type']
        else:
            mech = "ALL"
        year = int(eq.attrib['year'])
        month = int(eq.attrib['month'])
        day = int(eq.attrib['day'])
        hour = int(eq.attrib['hour'])
        minute = int(eq.attrib['minute'])
        second = int(eq.attrib['second'])
        if 'directivity' in eq.attrib.keys():
            directivity = ast.literal_eval(eq.attrib['directivity'])
        else:
            directivity = False
        if 'eventsourcecode' in eq.attrib.keys():
            eventsourcecode = eq.attrib['eventsourcecode']
        else:
            eventsourcecode = None

    sdt = ShakeDateTime(year, month, day, hour, minute, second, int(0))

    event = {'lat': hlat,
             'lon': hlon,
             'depth': hdepth,
             'mag': magnitude,
             'rake': rake,
             'id': id_str,
             'locstring': lstring,
             'type': mech,
             'mech': mech,
             'time': sdt.strftime('%Y-%m-%dT%H:%M:%SZ'),
             'timezone': 'UTC',
             'directivity':directivity,
             'description':description,
             'eventsourcecode':eventsourcecode,
             'sdt':sdt}

    return event



def write_event_xml(input_dir, rdict, directivity):
    """
    Write the event.xml file. 

    Args:
        input_dir (str): Path of input directory.
        rdict (dict): Rupture dictionary.
        directivity (bool): Include directivity?

    """
    event = rdict['event']

    # Need to parse 'time' for event.xml
    evtime = time.strptime(str(event['time']), "%Y-%m-%d %H:%M:%S")

    # Write event.xml file
    xml_file = os.path.join(input_dir, 'event.xml')
    root = etree.Element('earthquake')
    root.set('id', rdict['id_str'])
    root.set('lat', str(event['lat']))
    root.set('lon', str(event['lon']))
    root.set('mag', str(event['mag']))
    root.set('year', time.strftime('%Y', evtime))
    root.set('month', time.strftime('%m', evtime))
    root.set('day', time.strftime('%d', evtime))
    root.set('hour', time.strftime('%H', evtime))
    root.set('minute', time.strftime('%M', evtime))
    root.set('second', time.strftime('%S', evtime))
    root.set('timezone', 'UTC')
    root.set('depth', str(event['depth']))
    root.set('locstring', rdict['short_name'])
    root.set('description', rdict['real_desc'])
    root.set('created', '')
    root.set('otime', '')
    root.set('network', '')
    if rdict['rupture'] is not None:
        root.set('reference', rdict['rupture'].getReference())
    if event['rake'] is not None:
        root.set('rake', str(event['rake']))
        root.set('type', rake_to_type(event['rake']))
    else:
        root.set('type', 'ALL')
    root.set('directivity', str(directivity))
    root.set('eventsourcecode', rdict['eventsourcecode'])

    et = etree.ElementTree(root)
    et.write(xml_file, pretty_print=True, xml_declaration=True,
             encoding="us-ascii")


def write_rupture_files(input_dir, rdict):
    """
    Write rupture files for scenarios. This includes one for distance
    calculations, which is the full representation of the rupture, and
    also a simplified version for plotting on a map that is just the
    trace of the top and bottom edges. 

    Args:
        input_dir (str): Path of event input directory. 
        rdict (dict): Rupture dictionary.

    """
    rupture = rdict['rupture']
    rupture.writeTextFile(os.path.join(
        input_dir, rdict['id_str'] + '-fault-for-calc.txt'))

    ff = open(os.path.join(
        input_dir, rdict['id_str'] + '_for-map_fault.txt'), 'wt')

    top = rdict['edges'][0]
    bot = rdict['edges'][1]
    top_lat = [p.latitude for p in top]
    top_lon = [p.longitude for p in top]
    top_dep = [p.depth for p in top]
    bot_lat = [p.latitude for p in bot]
    bot_lon = [p.longitude for p in bot]
    bot_dep = [p.depth for p in bot]

    nl = len(top_lon)
    for i in range(0, nl):  # top edge
        ff.write('%.4f %.4f %.4f\n' % (top_lat[i], top_lon[i], top_dep[i]))
    for i in list(reversed(range(0, nl))):  # bottom edge
        ff.write('%.4f %.4f %.4f\n' % (bot_lat[i], bot_lon[i], bot_dep[i]))
    # Close the polygon loop
    ff.write('%.4f %.4f %.4f\n' % (top_lat[0], top_lon[0], top_dep[0]))

    ff.close()


def parse_bssc2014_ucerf(rupts, args):
    """
    This function is to parse the UCERF3 json file format. The ruptures in 
    UCERF3 are very complex and so we don't exepct to get other rupture lists
    in this format. 

    Args:
        rupts (dict): Python translation of rupture json file using json.load 
            method. 
        args (ArgumentParser): argparse object. 

    Returns:
        dict: Dictionary of rupture information.

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
        rake = rupts['events'][i]['rake']

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

        # Origin
        origin = Origin({'mag':0, 'id':'', 'lat':0, 'lon':0, 'depth':0})
        rupt = QuadRupture.fromTrace(xp0, yp0, xp1, yp1, zp,
                                     width_sec, dip_sec, origin, strike=strike_sec,
                                     reference=args.reference)

        rupt._segment_index = new_seg_ind

        quads = rupt.getQuadrilaterals()
        edges = get_rupture_edges(quads, rev)
        hlat, hlon, hdepth = get_hypo(edges, args)

        id_str, eventsourcecode, real_desc = get_event_id(
            event_name, magnitude, args.directivity, args.dirind, quads)

        event = {'lat': hlat,
                 'lon': hlon,
                 'depth': hdepth,
                 'mag': magnitude,
                 'rake':rake,
                 'id': id_str,
                 'locstring': event_name,
                 'type': 'ALL',
                 'timezone': 'UTC',
                 'time':ShakeDateTime.utcfromtimestamp(int(time.time())),
                 'created':ShakeDateTime.utcfromtimestamp(int(time.time()))
                     }

        # Update rupture with new origin info
        origin = Origin(event)
        rupt = QuadRupture.fromTrace(xp0, yp0, xp1, yp1, zp,
                                     width_sec, dip_sec, origin, strike=strike_sec,
                                     reference=args.reference)


        rdict = {'rupture':rupt,
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

    Args:
        rupts (dict): Python translation of rupture json file using json.load 
            method.
        args (ArgumentParser): argparse object. 

    Returns:
        dict: Dictionary of rupture information.

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
        short_name = event_name.split('.xls')[0]
        id = rupts['events'][i]['id']
        magnitude = rupts['events'][i]['mag']
        if 'rake' in rupts['events'][i].keys():
            rake = rupts['events'][i]['rake']
        else:
            rake = None

        # Does the file include a rupture model?
        if len(rupts['events'][i]['lats']) > 1:

            dip = rupts['events'][i]['dip']

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

            # Dummy origin
            origin = Origin({'mag':0, 'id':'', 'lat':0, 'lon':0, 'depth':0})
            rupt = QuadRupture.fromTrace(xp0, yp0, xp1, yp1, zp,
                                         widths, dips, origin, strike=strike,
                                         reference=args.reference)



            quads = rupt.getQuadrilaterals()
            edges = get_rupture_edges(quads) # for map and hypo placement
            hlat, hlon, hdepth = get_hypo(edges, args)
        else:
            rupt = None
            edges = None
            hlat = float(rupts['events'][i]['lats'][0])
            hlon = float(rupts['events'][i]['lons'][0])

        id_str, eventsourcecode, real_desc = get_event_id(
            event_name, magnitude, args.directivity, args.dirind,
            quads, id = id)

        event = {'lat': hlat,
                 'lon': hlon,
                 'depth': hdepth,
                 'mag': magnitude,
                 'rake':rake,
                 'id': id_str,
                 'locstring': event_name,
                 'type': 'ALL',
                 'timezone': 'UTC',
                 'time':ShakeDateTime.utcfromtimestamp(int(time.time())),
                 'created':ShakeDateTime.utcfromtimestamp(int(time.time()))
                     }

        # Update rupture with new origin info
        if rupt is not None:
            origin = Origin(event)
            rupt = QuadRupture.fromTrace(xp0, yp0, xp1, yp1, zp,
                                         widths, dips, origin, strike=strike,
                                         reference=args.reference)

        rdict = {'rupture':rupt,
                 'event':event,
                 'edges':edges,
                 'id_str':id_str,
                 'short_name':short_name,
                 'real_desc':real_desc,
                 'eventsourcecode':eventsourcecode
                }
        rlist.append(rdict)

    return rlist

def parse_json_sub(rupts, args):
    """
    This is an alternative version of parse_json to use with the Cascadia
    subduction zone JSON rupture file. 

    Args:
        rupts (dict): Python translation of rupture json file using json.load 
            method.
        args (ArgumentParser): argparse object. 

    Returns:
        dict: Dictionary of rupture information.

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
        short_name = event_name.split('.xls')[0]
        id = rupts['events'][i]['id']
        magnitude = rupts['events'][i]['mag']
        if 'rake' in rupts['events'][i].keys():
            rake = rupts['events'][i]['rake']
        else:
            rake = None

        toplons = np.array(rupts['events'][i]['toplons'])
        toplats = np.array(rupts['events'][i]['toplats'])
        topdeps = np.array(rupts['events'][i]['topdeps'])
        botlons = np.array(rupts['events'][i]['botlons'])
        botlats = np.array(rupts['events'][i]['botlats'])
        botdeps = np.array(rupts['events'][i]['botdeps'])

        lats = np.append(toplats, botlats[::-1])
        lons = np.append(toplons, botlons[::-1])
        deps = np.append(topdeps, botdeps[::-1])

        rupt = QuadRupture(lon = lons,
                          lat = lats,
                          depth = deps,
                          reference=args.reference)
        rupt._segment_index = np.zeros_like(xp0)

        quads = rupt.getQuadrilaterals()
        edges = get_rupture_edges(quads) # for map and hypo placement
        hlat, hlon, hdepth = get_hypo(edges, args)

        id_str, eventsourcecode, real_desc = get_event_id(
            event_name, magnitude, args.directivity, args.dirind,
            quads, id = id)

        event = {'lat': hlat,
                 'lon': hlon,
                 'depth': hdepth,
                 'mag': magnitude,
                 'rake':rake,
                 'id': id_str,
                 'locstring': event_name,
                 'type': 'U',  # overwrite later
                 'timezone': 'UTC'}
        event['time'] = ShakeDateTime.utcfromtimestamp(int(time.time()))
        event['created'] = ShakeDateTime.utcfromtimestamp(int(time.time()))

        rdict = {'rupture':rupt,
                 'event':event,
                 'edges':edges,
                 'id_str':id_str,
                 'short_name':short_name,
                 'real_desc':real_desc,
                 'eventsourcecode':eventsourcecode
                }
        rlist.append(rdict)

    return rlist

