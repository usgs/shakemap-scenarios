
import os
import json
import copy
import shutil
import ast

import numpy as np
import xml.etree.ElementTree as ET
from configobj import ConfigObj

from shapely.geometry import Polygon
from shapely.geometry import Point

import openquake.hazardlib.geo as geo
from openquake.hazardlib.geo.utils import get_orthographic_projection

from mapio.gmt import GMTGrid
from impactutils.io.cmd import get_command_output
from impactutils.vectorutils.ecef import ecef2latlon
from impactutils.vectorutils.vector import Vector
from impactutils.time.ancient_time import HistoricTime as ShakeDateTime

from shakelib.rupture.origin import read_event_file
from shakelib.rupture.edge_rupture import EdgeRupture
from shakelib.rupture.quad_rupture import QuadRupture


def set_shakehome(path):
    """
    Helper function for managing shakehome in the scenario conf file.

    Args:
        path (str): Path to shakehome.

    Returns:
        str: Previous shakehome, which can be used to restor to previous
             config.
    """
    conf_file = os.path.join(os.path.expanduser('~'), 'scenarios.conf')
    config = ConfigObj(conf_file)
    old_shakehome = config['system']['shakehome']
    config['system']['shakehome'] = path
    config.write()
    return old_shakehome


def set_vs30file(path):
    """
    Helper function for managing vs30file in the scenario conf file.

    Args:
        path (str): Path to vs30file.

    Returns:
        str: Previous vs30file, which can be used to restor to previous
             config.
    """
    conf_file = os.path.join(os.path.expanduser('~'), 'scenarios.conf')
    config = ConfigObj(conf_file)
    old_vs30file = config['data']['vs30file']
    config['data']['vs30file'] = path
    config.write()
    return old_vs30file


def set_gmpe(gmpe):
    """
    Helper function for managing gmpe in the scenario conf file.

    Args:
        gmpe (str): The designed OQ GMPE or name of GMPE set.

    Returns:
        str: Previous GMPE, which can be used to restor to previous
             config.
    """
    conf_file = os.path.join(os.path.expanduser('~'), 'scenarios.conf')
    config = ConfigObj(conf_file)
    old_gmpe = config['modeling']['gmpe']
    config['modeling']['gmpe'] = gmpe
    config.write()
    return old_gmpe


def find_rupture(pattern, file):
    """
    Convenience method for finding name and index of a rupture based on pattern
    matching the description.

    Args:
        pattern (str): Pattern to search for.
        file (str): JSON rupture file to look in.

    Return:
        tuple: List of descriptions and list of indices.

    """
    with open(file) as f:
        rupts = json.load(f)

    # The key for the search is different for UCERF3 than other
    # files:
    if rupts['name'] == '2014 NSHMP Determinisitc Event Set':
        skey = 'name'
    else:
        skey = 'desc'

    desc = [r[skey] for r in rupts['events']]

    ind = np.where(list(map(lambda x: pattern in str(x), desc)))[0]
    result = np.array(desc)[ind]

    for i in range(len(ind)):
        print('%i: %s' % (ind[i], result[i]))

    return ind, result


def get_hypo(edges, args):
    """
    Args:
        edges (list): A list of two lists of points; the first list corresponds
            to the top edge and the second is the bottom edge.
        args (ArgumentParser): argparse object.

    Returns:
        tuple: Hypocenter (lat, lon depth).

    """
    top = copy.deepcopy(edges[0])
    bot = copy.deepcopy(edges[1])

    # Along strike and along dip distance (0-1)
    # NOTE: This could also be made a function of mechanism
    if args.dirind == -1:
        # no directivity
        dxp = 0.5  # strike
        dyp = 0.6  # dip
    elif args.dirind == 0:
        # first unilateral
        dxp = 0.05  # strike
        dyp = 0.6  # dip
    elif args.dirind == 2:
        # second unilateral
        dxp = 0.95  # strike
        dyp = 0.6  # dip
    elif args.dirind == 1:
        # bilateral
        dxp = 0.5  # strike
        dyp = 0.6  # dip

    # Convert to ECEF
    topxy = [Vector.fromPoint(geo.point.Point(p.longitude,
                                              p.latitude,
                                              p.depth))
             for p in top]
    botxy = [Vector.fromPoint(geo.point.Point(p.longitude,
                                              p.latitude,
                                              p.depth))
             for p in bot]

    # Compute distances along edges for each vertex
    t0 = topxy[0]
    b0 = botxy[0]
    topdist = np.array([t0.distance(p) for p in topxy])
    botdist = np.array([b0.distance(p) for p in botxy])

    # Normalize distance from 0 to 1
    topdist = topdist / np.max(topdist)
    botdist = botdist / np.max(botdist)

    #---------------------------------------------------------------------------
    # Find points of surrounding quad
    #---------------------------------------------------------------------------
    tix0 = np.amax(np.where(topdist < dxp))
    tix1 = np.amin(np.where(topdist > dxp))
    bix0 = np.amax(np.where(botdist < dxp))
    bix1 = np.amin(np.where(botdist > dxp))

    # top left
    pp0 = topxy[tix0]

    # top right
    pp1 = topxy[tix1]

    # bottom right
    pp2 = botxy[bix0]

    # bottom left
    pp3 = botxy[bix1]

    # How far from pp0 to pp1, and pp2 to pp3?
    dxt = (dxp - topdist[tix0]) / (topdist[tix1] - topdist[tix0])
    dxb = (dxp - botdist[bix0]) / (botdist[bix1] - botdist[bix0])

    mp0 = pp0 + (pp1 - pp0) * dxt
    mp1 = pp3 + (pp2 - pp3) * dxb
    rp = mp0 + (mp1 - mp0) * dyp
    hlat, hlon, hdepth = ecef2latlon(rp.x, rp.y, rp.z)

    return hlat, hlon, hdepth


def get_extent(origin, rupture=None):
    """
    Method to compute map extent from rupture.

    Args:
        origin (Origin): A ShakeMap Origin instance.
        rupture (Rupture): A ShakeMap Rupture instance (optional).

    Returns:
        tuple: lonmin, lonmax, latmin, latmax.

    """

    # Is there a rupture?
    if isinstance(rupture, (QuadRupture, EdgeRupture)):
        lats = rupture.lats
        lons = rupture.lons

        # Remove nans
        lons = lons[~np.isnan(lons)]
        lats = lats[~np.isnan(lats)]

        clat = 0.5 * (np.nanmax(lats) + np.nanmin(lats))
        clon = 0.5 * (np.nanmax(lons) + np.nanmin(lons))
    else:
        clat = origin.lat
        clon = origin.lon

    mag = origin.mag

    # Is this a stable or active tectonic event?
    # (this could be made an attribute of the ShakeMap Origin class)
    hypo = origin.getHypo()
    stable = is_stable(hypo.longitude, hypo.latitude)

    if stable is False:
        if mag < 6.48:
            mindist_km = 100.
        else:
            mindist_km = 27.24 * mag**2 - 250.4 * mag + 579.1
    else:
        if mag < 6.10:
            mindist_km = 100.
        else:
            mindist_km = 63.4 * mag**2 - 465.4 * mag + 581.3

    # Apply an upper limit on extent. This should only matter for large
    # magnitudes (> ~8.25) in stable tectonic environments.
    if mindist_km > 1000.:
        mindist_km = 1000.

    # Projection
    proj = get_orthographic_projection(clon - 4, clon + 4, clat + 4, clat - 4)
    if isinstance(rupture, (QuadRupture, EdgeRupture)):
        ruptx, rupty = proj(lons, lats)
    else:
        ruptx, rupty = proj(clon, clat)

    xmin = np.nanmin(ruptx) - mindist_km
    ymin = np.nanmin(rupty) - mindist_km
    xmax = np.nanmax(ruptx) + mindist_km
    ymax = np.nanmax(rupty) + mindist_km

    # Put a limit on range of aspect ratio
    dx = xmax - xmin
    dy = ymax - ymin
    ar = dy / dx
    if ar > 1.25:
        # Inflate x
        dx_target = dy / 1.25
        ddx = dx_target - dx
        xmax = xmax + ddx / 2
        xmin = xmin - ddx / 2
    if ar < 0.6:
        # inflate y
        dy_target = dx * 0.6
        ddy = dy_target - dy
        ymax = ymax + ddy / 2
        ymin = ymin - ddy / 2

    lonmin, latmin = proj(np.array([xmin]), np.array([ymin]), reverse=True)
    lonmax, latmax = proj(np.array([xmax]), np.array([ymax]), reverse=True)

    return lonmin, lonmax, latmin, latmax


def is_stable(lon, lat):
    """
    Determine if point is located in the US stable tectonic region. Uses the
    same boundary as the US NSHMP and so this function needs to be modified to
    work outside of the US.

    Args:
        lon (float): Lognitude.
        lat (float): Latitude.

    Returns:
        bool: Is the point classified as tectonically stable.

    """
    here = os.path.dirname(os.path.abspath(__file__))
    pfile = os.path.join(here, 'data', 'nshmp_stable.json')
    with open(pfile) as f:
        coords = json.load(f)
    tmp = [(float(x), float(y)) for x, y in zip(coords['lon'], coords['lat'])]
    poly = Polygon(tmp)
    p = Point((lon, lat))
    return p.within(poly)


def rake_to_type(rake):
    """
    Convert rake to mechansim (using the Shakemap convention for mechanism
    strings).

    Args:
        rake (float): Rake angle in degress.

    Returns:
        str: String indicating mechanism.

    """

    type = 'ALL'
    if (rake >= -180 and rake <= -150) or \
       (rake >= -30 and rake <= 30) or \
       (rake >= 150 and rake <= 180):
        type = 'SS'
    if rake >= -120 and rake <= -60:
        type = 'NM'
    if rake >= 60 and rake <= 120:
        type = 'RS'
    return type


def strike_to_quadrant(strike):
    """
    Convert strike angle to quadrant. Used for constructing a string describing
    the directivity direction.

    Args:
        strike (float): Strike angle in degrees.

    Returns:
        int: An integer indicating which quadrant the strike is pointing.

    """
    # assuming strike is between -180 and 180 (since it is
    # computed from numpy.arctan2
    #  \ 1 /
    #   \ /
    # 4  X  2
    #   / \
    #  / 3 \
    if strike > 180:
        strike = strike - 360
    if strike < -180:
        strike = strike + 360
    if (strike > -45 and strike <= 45):
        q = 1
    if strike > 45 and strike <= 135:
        q = 2
    if (strike > 135 and strike <= 180) or \
       (strike <= -135 and strike >= -180):
        q = 3
    if strike > -135 and strike <= -45:
        q = 4
    return q


def get_event_id(event_name, mag, directivity, i_dir, quads, id=None):
    """
    This is to sort out the event id, event source code, realization
    description, and the quadrilateral that was selected for placing
    the hypocenter on.

    Args:
        event_name (str): Event name/description.
        mag (float): Earthquake magnitude.
        directivity (bool): Is directivity applied?
        i_dir (int): Directivity orientation indicator. Valid values are 0, 1, 2.
        quads (list): List of quadrilaterals describing the rupture.
        id (str): Optional event id. If None, then event id is constructed from
            event_name.

    Returns:
        tuple: id_str, eventsourcecode, real_desc, selquad.
    """

    event_legal = "".join(x for x in event_name if x.isalnum())
    if id is not None:
        id = id.replace('.', 'p')
        id = "".join(x for x in id if x.isalnum() or x == "_")
    mag_str = str(mag).strip("0")
    # PDL requrement: no ".", so replace with "p"
    mag_str = mag_str.replace('.', 'p')

    # Get an 'average strike' from first quad to mean of trace
    if quads is not None:
        lat0 = [q[0].latitude for q in quads]
        lon0 = [q[0].longitude for q in quads]
        lat1 = [q[1].latitude for q in quads]
        lon1 = [q[1].longitude for q in quads]
        lat2 = [q[2].latitude for q in quads]
        lon2 = [q[2].longitude for q in quads]
        lat3 = [q[3].latitude for q in quads]
        lon3 = [q[3].longitude for q in quads]
        clat = np.mean(np.array([lat0, lat1, lat2, lat3]))
        clon = np.mean(np.array([lon0, lon1, lon2, lon3]))
        strike = geo.geodetic.azimuth(lon0[0], lat0[0], clon, clat)
        squadrant = strike_to_quadrant(strike)

        if directivity:
            dirtag = 'dir' + str(i_dir)
        else:
            dirtag = ''

        if (i_dir == 0) and (directivity):
            if squadrant == 1:
                ddes = "Northern directivity"
            if squadrant == 2:
                ddes = "Eastern directivity"
            if squadrant == 3:
                ddes = "Southern directivity"
            if squadrant == 4:
                ddes = "Western directivity"
        elif (i_dir == 1) or (not directivity):
            ddes = "Bilateral directivity"
        elif (i_dir == 2) and (directivity):
            if squadrant == 1:
                ddes = "Southern directivity"
            if squadrant == 2:
                ddes = "Western directivity"
            if squadrant == 3:
                ddes = "Northern directivity"
            if squadrant == 4:
                ddes = "Eastern directivity"

    if directivity:
        if id is None:
            id_str = "%s_M%s_se~%s" % (event_legal[:20], mag_str, dirtag)
        else:
            if id[-3:] == '_se':
                id_str = id
            else:
                id_str = "%s_M%s_se~%s" % (id[:20], mag_str, dirtag)
        id_str = id_str.lower()
        real_desc = ddes
    else:
        if id is None:
            id_str = "%s_M%s_se" % (event_legal[:20], mag_str)
        else:
            if id[-3:] == '_se':
                id_str = id
            else:
                id_str = "%s_M%s_se" % (id[:20], mag_str)
        id_str = id_str.lower()
        real_desc = 'Median ground motions'

    if id is None:
        eventsourcecode = "%s_M%s_se" % (event_legal[:20], mag_str)
    else:
        if id[-3:] == '_se':
            eventsourcecode = id
        else:
            eventsourcecode = "%s_M%s_se" % (id[:20], mag_str)

    eventsourcecode = eventsourcecode.lower()
    return id_str, eventsourcecode, real_desc


def get_rupture_edges(q, rev=None):
    """
    Return a list of the top and bottom edges of the rupture. This is
    useful as a simplified visual representation of the rupture and placing
    the hypocenter but not used for distance calculaitons.

    Args:
        q (list): List of quads.
        rev (list): Optional list of booleans indicating whether or not
        the quad is reversed.

    Returns:
        list: A list of two lists of points; the first list corresponds to
        the top edge and the second is the bottom edge.
    """
    nq = len(q)

    if rev is None:
        rev = np.zeros(nq, dtype=bool)
    else:
        rev = rev.astype('bool')

    top_lat = np.array([[]])
    top_lon = np.array([[]])
    top_dep = np.array([[]])
    bot_lat = np.array([[]])
    bot_lon = np.array([[]])
    bot_dep = np.array([[]])

    for j in range(0, nq):
        if rev[j] == True:
            top_lat = np.append(top_lat, q[j][1].latitude)
            top_lat = np.append(top_lat, q[j][0].latitude)
            top_lon = np.append(top_lon, q[j][1].longitude)
            top_lon = np.append(top_lon, q[j][0].longitude)
            top_dep = np.append(top_dep, q[j][1].depth)
            top_dep = np.append(top_dep, q[j][0].depth)
            bot_lat = np.append(bot_lat, q[j][2].latitude)
            bot_lat = np.append(bot_lat, q[j][3].latitude)
            bot_lon = np.append(bot_lon, q[j][2].longitude)
            bot_lon = np.append(bot_lon, q[j][3].longitude)
            bot_dep = np.append(bot_dep, q[j][2].depth)
            bot_dep = np.append(bot_dep, q[j][3].depth)
        else:
            top_lat = np.append(top_lat, q[j][0].latitude)
            top_lat = np.append(top_lat, q[j][1].latitude)
            top_lon = np.append(top_lon, q[j][0].longitude)
            top_lon = np.append(top_lon, q[j][1].longitude)
            top_dep = np.append(top_dep, q[j][0].depth)
            top_dep = np.append(top_dep, q[j][1].depth)
            bot_lat = np.append(bot_lat, q[j][3].latitude)
            bot_lat = np.append(bot_lat, q[j][2].latitude)
            bot_lon = np.append(bot_lon, q[j][3].longitude)
            bot_lon = np.append(bot_lon, q[j][2].longitude)
            bot_dep = np.append(bot_dep, q[j][3].depth)
            bot_dep = np.append(bot_dep, q[j][2].depth)

    nl = len(top_lon)
    topp = [None] * nl
    botp = [None] * nl
    for i in range(0, nl):
        topp[i] = geo.point.Point(top_lon[i], top_lat[i], top_dep[i])
        botp[i] = geo.point.Point(bot_lon[i], bot_lat[i], bot_dep[i])

    edges = [topp, botp]
    return edges


def run_one_old_shakemap(eventid, topo=True, genex=True):
    """
    Convenience method for running old (v 3.5) shakemap with new estimates. This
    allows for us to generate all the products with the old code since the new
    code cannot do this yet, but use the new code for computing the ground
    motions.

    Args:
        eventid (srt): Specifies the id of the event to process.
        topo (bool): Include topography shading?
        genex (bool): Should genex be run?

    Returns:
        dictionary: Each entry is the log file for the different ShakeMap3.5
            calls.

    """
    config = ConfigObj(os.path.join(os.path.expanduser('~'), 'scenarios.conf'))
    shakehome = config['system']['shakehome']
    log = {}
    shakebin = os.path.join(shakehome, 'bin')
    datadir = os.path.join(shakehome, 'data')
    # Read event.xml
    eventdir = os.path.join(datadir, eventid)
    inputdir = os.path.join(eventdir, 'input')
    xml_file = os.path.join(inputdir, 'event.xml')
    # Read in event.xml
    event = read_event_file(xml_file)

    # Read in gmpe set name
    gmpefile = open(os.path.join(inputdir, "gmpe_set_name.txt"), "r")
    set_name = gmpefile.read()
    gmpefile.close()

    # Add scenario-specific fields:
    eventtree = ET.parse(xml_file)
    eventroot = eventtree.getroot()
    for eq in eventroot.iter('earthquake'):
        description = eq.attrib['description']
        directivity = eq.attrib['directivity']
        if 'reference' in eq.attrib.keys():
            reference = eq.attrib['reference']
        else:
            reference = ''

    event['description'] = description
    event['directivity'] = directivity
    event['reference'] = reference


    grd = os.path.join(inputdir, 'pgv_estimates.grd')
    gdict = GMTGrid.getFileGeoDict(grd)[0]

    # Tolerance is a bit hacky but necessary to prevent GMT
    # from barfing becasue it thinks that the estimates files
    # do not cover the desired area sampled by grind's call
    # with grdsample.
    tol = gdict.dx
    W = gdict.xmin + tol
    E = gdict.xmax - tol
    S = gdict.ymin + tol
    N = gdict.ymax - tol

    # Put into grind.conf (W S E N)
    confdir = os.path.join(eventdir, 'config')
    if os.path.isdir(confdir) == False:
        os.mkdir(confdir)

    # need to copy default grind.conf
    default_grind_conf = os.path.join(shakehome, 'config', 'grind.conf')
    grind_conf = os.path.join(confdir, 'grind.conf')
    shutil.copyfile(default_grind_conf, grind_conf)

    # Set strictbound and resolution to match estiamtes.grd files
    with open(grind_conf, 'a') as f:
        f.write('x_grid_interval : %.16f\n' % gdict.dx)
        f.write('y_grid_interval : %.16f\n' % gdict.dy)
        f.write('strictbound : %.9f %.9f %.9f %.9f\n' % (W, S, E, N))

    # Grind
    callgrind = os.path.join(shakebin, 'grind') + \
        ' -event ' + eventid + ' -psa'
    rc, so, se = get_command_output(callgrind)
    log['grind'] = {'rc': rc, 'so': so, 'se': se}

    # Add GMPE set name to info.json
    cmd = os.path.join(shakebin, 'edit_info') + ' -event ' + eventid + \
        ' -tag gmpe_reference' + ' -value ' + set_name
    rc, so, se = get_command_output(cmd)
    log['edit_info'] = {'rc': rc, 'so': so, 'se': se}

    # Tag
    calltag = os.path.join(shakebin, 'tag') + \
        ' -event ' + eventid + ' -name \"' + event['locstring'] + ' - ' + \
        event['description'] + '\"'
    rc, so, se = get_command_output(calltag)
    log['tag'] = {'rc': rc, 'so': so, 'se': se}

    # Copy rock_grid.xml from input to output directory
    rg_scr = os.path.join(inputdir, 'rock_grid.xml')
    rg_dst = os.path.join(eventdir, 'output', 'rock_grid.xml')
    cmd = shutil.copy(rg_scr, rg_dst)

    # Mapping
    if topo is True:
        topostr = '-itopo'
    else:
        topostr = ''
    callmapping = os.path.join(shakebin, 'mapping') + ' -event ' + \
        eventid + ' -timestamp -nohinges ' + topostr
    rc, so, se = get_command_output(callmapping)
    log['mapping'] = {'rc': rc, 'so': so, 'se': se}

    # Genex
    if genex is True:
        callgenex = os.path.join(shakebin, 'genex') + ' -event ' + \
            eventid + ' -metadata -zip -verbose -shape shape -shape hazus'
        rc, so, se = get_command_output(callgenex)
        log['genex'] = {'rc': rc, 'so': so, 'se': se}

    return log


def send_origin(eventid):
    """
    Args:
        eventid (str): Event id.

    Returns:
        dict: transfer logs.

    """
    config = ConfigObj(os.path.join(os.path.expanduser('~'), 'scenarios.conf'))
    shakehome = config['system']['shakehome']
    pdlbin = config['system']['pdlbin']
    key = config['system']['key']
    pdlconf = config['system']['pdlconf']
    catalog = config['system']['catalog']

    datadir = os.path.join(shakehome, 'data')
    xmlfile = os.path.join(datadir, eventid, 'input', 'event.xml')
    eventdict = read_event_xml(xmlfile)
    short_name = eventdict['locstring']  # locstring in event.xml
    if eventdict['eventsourcecode'] is None:
        eventsourcecode = eventid
    else:
        eventsourcecode = eventdict['eventsourcecode']
    lat = eventdict['lat']
    lon = eventdict['lon']
    depth = eventdict['depth']
    magnitude = eventdict['mag']
    sdt = eventdict['sdt']

    send_origin = \
        'java -jar ' + pdlbin + ' --send ' + \
        '--configFile=' + pdlconf + ' ' + \
        '--privateKey=' + key + ' ' + \
        '\"--property-title=' + short_name + '\" ' + \
        '--source=us ' + \
        '--eventsource=' + catalog + ' ' + \
        '--code=' + catalog + eventid + ' ' + \
        '--eventsourcecode=' + eventsourcecode + ' ' + \
        '--type=origin-scenario ' + \
        '--latitude=' + str(lat) + ' ' + \
        '--longitude=' + str(lon) + ' ' + \
        '--magnitude=' + str(magnitude) + ' ' + \
        '--depth=' + str(depth) + ' ' + \
        '--eventtime=' + sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
    rc, so, se = get_command_output(send_origin)
    return {'rc': rc, 'so': so, 'se': se}


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
             'directivity': directivity,
             'description': description,
             'eventsourcecode': eventsourcecode,
             'sdt': sdt}

    return event
