
import os
import time
import json
import argparse

import numpy as np
from lxml import etree

from shapely.geometry import Polygon
from shapely.geometry import Point

import openquake.hazardlib.geo as geo
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.geo.utils import get_orthographic_projection

import shakemap.grind.fault as fault
from shakemap.utils.ecef import latlon2ecef, ecef2latlon
from shakemap.utils.vector import Vector
from shakemap.utils.timeutils import ShakeDateTime


def get_extent(source):
    """
    Method to compute map extent from source.

    Note: currently written assuming source has a fault

    Args:
        source (Source): A Source instance. 

    Returns:
        tuple: lonmin, lonmax, latmin, latmax.

    """
    # 
    flt = source.getFault()
    lats = flt.getLats()
    lons = flt.getLons()
    clat = 0.5 * (np.nanmax(lats) + np.nanmin(lats))
    clon = 0.5 * (np.nanmax(lons) + np.nanmin(lons))
    mag = source.getEventParam('mag')

    # Is this a stable or active tectonic event?
    # (this could be made an attribute of the ShakeMap Source class)
    hypo = source.getHypo()
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

    # Apply an upper limit on extent. This should only matter for large magnitudes
    # (> ~8.25) in stable tectonic environments. 
    if mindist_km > 1000.:
        mindist_km = 1000.

    # Projection
    proj = get_orthographic_projection(clon - 4, clon + 4, clat + 4, clat - 4)
    fltx, flty = proj(lons, lats)
    xmin = np.nanmin(fltx) - mindist_km
    ymin = np.nanmin(flty) - mindist_km
    xmax = np.nanmax(fltx) + mindist_km
    ymax = np.nanmax(flty) + mindist_km

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
    tmp = [(float(x),float(y)) for x, y in zip(coords['lon'], coords['lat'])]
    poly = Polygon(tmp)
    p = Point((lon, lat))
    return p.within(poly)


def filter_gmpe_list(gmpes, wts, imt):
    """
    Method to remove GMPEs from the GMPE list that are not applicable
    to a specific IMT. Rescales the weights to sum to one. 

    Args:
        gmpes (list): List of GMPE instances. 
        wts (list): List of floats indicating the weight of the GMPEs. 

    Returns:
        tuple: List of GMPE instances and list of weights. 

    """
    per_max = [np.max(get_gmpe_sa_periods(g)) for g in gmpes]
    per_min = [np.min(get_gmpe_sa_periods(g)) for g in gmpes]
    if imt == PGA():
        sgmpe = [g for g in gmpes if imt in g.COEFFS.non_sa_coeffs]
        swts = [w for g, w in zip(gmpes, wts) if imt in g.COEFFS.non_sa_coeffs]
    elif(imt == PGV()):
        sgmpe = []
        swts = []
        for i in range(len(gmpes)):
            if (imt in gmpes[i].COEFFS.non_sa_coeffs) or\
               (per_max[i] >= 1.0 and per_min[i] <= 1.0):
               sgmpe.append(gmpes[i])
               swts.append(wts[i])
    else:
        per = imt.period
        sgmpe = []
        swts = []
        for i in range(len(gmpes)):
            if (per_max[i] >= per and per_min[i] <= per):
               sgmpe.append(gmpes[i])
               swts.append(wts[i])

    if len(sgmpe) == 0:
        raise Exception('No applicable GMPEs from GMPE list for %s' %val)

    # Scale weights to sum to one
    swts = np.array(swts)
    swts = swts/np.sum(swts)

    return sgmpe, swts



def get_gmpe_sa_periods(gmpe):
    """
    Method to extract the SA periods defined by a GMPE. 

    Args: 
        gmpe (GMPE): A GMPE instance. 

    Retunrs:
        list: List of periods. 

    """

    ctab = gmpe.COEFFS.sa_coeffs
    ilist = list(ctab.keys())
    per = [i.period for i in ilist]
    return per



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
       (rake >= -30  and rake <= 30) or \
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

def get_event_id(event_name, mag, directivity, i_dir, quads, id = None):
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
    mag_str = str(mag).strip("0")
    # PDL requrement: no ".", so replace with "p"
    mag_str = mag_str.replace('.', 'p')

    # Get an 'average strike' from first quad to mean of trace
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

    nq = len(quads)
    if (i_dir == 0) and (directivity):
        # Put hypo in center of first quad
        selquad = quads[0]
        if squadrant == 1:
            ddes = "Northern directivity"
        if squadrant == 2:
            ddes = "Eastern directivity"
        if squadrant == 3:
            ddes = "Southern directivity"
        if squadrant == 4:
            ddes = "Western directivity"
    elif (i_dir == 1) or (not directivity):
        # Put hypo in center of middle quad
        selquad = quads[int(np.round(nq / 2, 0)) - 1]
        ddes = "Bilateral directivity"
    elif (i_dir == 2) and (directivity):
        # Put hypo in center of last quad
        selquad = quads[nq - 1]
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
            id_str = "%s_M%s_se~%s" % (id[:20], mag_str, dirtag)
        id_str = id_str.lower()
        real_desc = ddes
    else:
        if id is None:
            id_str = "%s_M%s_se" % (event_legal[:20], mag_str)
        else:
            id_str = "%s_M%s_se" % (id[:20], mag_str)
        id_str = id_str.lower()
        real_desc = 'Median ground motions'

    eventsourcecode = "%s_M%s_se" % (event_legal[:20], mag_str)
    eventsourcecode = eventsourcecode.lower()
    return id_str, eventsourcecode, real_desc, selquad

def get_fault_edges(q, rev = None):
    """
    Return a list of the top and bottom edges of the fault. This is
    useful as a simplified visual representation of the fault but not
    used for calculaitons. 

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
        rev = np.zeros(nq, dtype = bool)
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
