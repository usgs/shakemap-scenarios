#!/usr/bin/env python

import os
import pkg_resources

import numpy as np

from openquake.hazardlib import imt, const
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.gsim.base import DistancesContext
from openquake.hazardlib.gsim.base import SitesContext

from configobj import ConfigObj

from shakemap.utils.config import get_custom_validator
from shakemap.utils.config import config_error

from shakelib.grind.multigmpe import MultiGMPE

from scenarios.utils import set_gmpe


def test_scr_rlme():
    old_gmpe = set_gmpe('stable_continental_nshmp2014_rlme')
    spec_file = pkg_resources.resource_filename(
        'scenarios', os.path.join('data', 'configspec.conf'))
    validator = get_custom_validator()
    config = ConfigObj(os.path.join(os.path.expanduser('~'), 'scenarios.conf'),
                       configspec=spec_file)
    tmp = pkg_resources.resource_filename(
        'scenarios', os.path.join('..', 'data', 'gmpe_sets.conf'))
    config.merge(ConfigObj(tmp, configspec=spec_file))
    tmp = pkg_resources.resource_filename(
        'scenarios', os.path.join('..', 'data', 'modules.conf'))
    config.merge(ConfigObj(tmp, configspec=spec_file))
    results = config.validate(validator)
    if results != True:
        config_error(config, results)

    # MultiGMPE from config
    config = config.dict()
    gmpe = MultiGMPE.from_config(config)

    # Input stuff
    IMT = imt.SA(1.0)
    rctx = RuptureContext()
    dctx = DistancesContext()
    sctx = SitesContext()

    rctx.rake = 0.0
    rctx.dip = 90.0
    rctx.ztor = 0.0
    rctx.mag = 8.0
    rctx.width = 10.0
    rctx.hypo_depth = 8.0

    dctx.rjb = np.logspace(1, np.log10(800), 100)
    dctx.rrup = dctx.rjb
    dctx.rhypo = dctx.rjb
    dctx.rx = dctx.rjb
    dctx.ry0 = dctx.rjb

    sctx.vs30 = np.ones_like(dctx.rjb) * 275.0
    sctx.vs30measured = np.full_like(dctx.rjb, False, dtype='bool')
    sctx = MultiGMPE.set_sites_depth_parameters(sctx, gmpe)

    # Evaluate
    conf_lmean, dummy = gmpe.get_mean_and_stddevs(
        sctx, rctx, dctx, IMT, [const.StdDev.TOTAL])

    target_lmean = np.array(
        [0.10556736,  0.0839267,  0.06189444,  0.03945984,  0.01661264,
         -0.006657, -0.03035844, -0.05450058, -0.07909179, -0.10413995,
         -0.1296524, -0.15563655, -0.1821091, -0.20909381, -0.23661405,
         -0.26469259, -0.29335086, -0.32257956, -0.35232905, -0.38254639,
         -0.41317807, -0.44417017, -0.47549552, -0.5071888, -0.53929293,
         -0.57185042, -0.60490345, -0.63848027, -0.67255251, -0.70707712,
         -0.74201096, -0.77731091, -0.81293906, -0.84889737, -0.88520644,
         -0.92188724, -0.95899471, -0.99699613, -1.03583184, -1.07530664,
         -1.11531737, -1.15576129, -1.19653696, -1.23757689, -1.2772327,
         -1.2915098, -1.30576498, -1.32001713, -1.33429606, -1.3486727,
         -1.36322545, -1.37803346, -1.39317668, -1.40677752, -1.42081409,
         -1.43538898, -1.45056417, -1.46640223, -1.48327111, -1.50656497,
         -1.53368548, -1.56645985, -1.59991327, -1.63399401, -1.66867278,
         -1.7039438, -1.73980246, -1.77624473, -1.81326727, -1.85087166,
         -1.889066, -1.92784814, -1.96721442, -2.0071855, -2.04779304,
         -2.08909259, -2.13114448, -2.17401045, -2.21775376, -2.26243406,
         -2.30808979, -2.35475487, -2.40246494, -2.4512575, -2.50117075,
         -2.55223495, -2.60447754, -2.65792811, -2.71261851, -2.61732716,
         -2.67007323, -2.72399057, -2.77918054, -2.83574666, -2.89379416,
         -2.95340501, -3.01462691, -3.07750731, -3.14209631, -3.20844679])

    np.testing.assert_allclose(conf_lmean, target_lmean, atol=1e-6)

    # Redo for 3 sec so some GMPEs are filtered out
    IMT = imt.SA(3.0)
    gmpe = MultiGMPE.from_config(config, filter_imt=IMT)
    conf_lmean, dummy = gmpe.get_mean_and_stddevs(
        sctx, rctx, dctx, IMT, [const.StdDev.TOTAL])

    target_lmean = np.array(
        [-1.26636973, -1.289514, -1.31300386, -1.33683936, -1.36102084,
         -1.38554902, -1.41042497, -1.43565015, -1.46122642, -1.48715602,
         -1.51344154, -1.54008586, -1.56709215, -1.59446375, -1.62220409,
         -1.65031664, -1.6788048, -1.70767178, -1.7369205, -1.76655351,
         -1.79657287, -1.82698005, -1.85777587, -1.88896039, -1.92053288,
         -1.95249175, -1.98483453, -2.01755788, -2.05065755, -2.08412844,
         -2.11796463, -2.15215943, -2.18670547, -2.22159473, -2.25681869,
         -2.29236835, -2.32823441, -2.36453464, -2.40140834, -2.43883442,
         -2.47679132, -2.51525752, -2.55421156, -2.59363211, -2.63112832,
         -2.63336521, -2.63582817, -2.6385319, -2.64147962, -2.64466761,
         -2.64809268, -2.65175214, -2.6556438, -2.65976592, -2.66411721,
         -2.66869673, -2.67350386, -2.67853821, -2.68413311, -2.69604497,
         -2.7124745, -2.73590549, -2.75964098, -2.78367044, -2.80798539,
         -2.8325853, -2.85746998, -2.88263948, -2.90809408, -2.93383429,
         -2.95986073, -2.98617306, -3.01275705, -3.03961495, -3.06675608,
         -3.09419043, -3.12192861, -3.14998191, -3.17836228, -3.20708239,
         -3.23615561, -3.26559604, -3.29541858, -3.32563888, -3.35627343,
         -3.38733956, -3.41885548, -3.4508403, -3.48331409, -3.56476842,
         -3.59987076, -3.63573296, -3.67238872, -3.70987332, -3.74822369,
         -3.78747847, -3.82767809, -3.86886488, -3.91108308, -3.95437899])

    np.testing.assert_allclose(conf_lmean, target_lmean, atol=1e-6)

    # Clean up
    set_gmpe(old_gmpe)
