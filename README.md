shakemap-scenarios
==================

**Disclaimer:**

>This software is preliminary or provisional and is subject to revision. It is 
being provided to meet the need for timely best science. The software has not 
received final approval by the U.S. Geological Survey (USGS). No warranty, 
expressed or implied, is made by the USGS or the U.S. Government as to the 
functionality of the software and related material nor shall the fact of release 
constitute any such warranty. The software is provided on the condition that 
neither the USGS nor the U.S. Government shall be held liable for any damages 
resulting from the authorized or unauthorized use of the software.

Overview
--------

Running a scenario is very different than running real events for a few reasons:
    - There isn't any data to be concerned about
    - The date/time doesn't really matter unless required for a specific exercise
    - Transfering to COMCAT requires a different set
    - Scenarios are organized in COMCAT by scenario catalogs, and each catalog
      needs to have an associated "catalog page" on the earthquake website that
      describes how the scenarios are created

In the future, all of this will be run within Python in ShakeMap 4.0. However,
this code was created to address some issues that could not be handled in the
current version of ShakeMap, such as the use of multiple GMPEs, and the inclusion
of new GMPEs that are not available in ShakeMap 3.5. However, the code in this
repository only handles the generation of the ground motion grids. The generaiton
of products (e.g., maps, shapefiles, etc.) and transferring of the products to
COMCAT is still handled with ShakeMap 3.5.

Dependencies
------------
* ShakeMap 3.5: http://usgs.github.io/shakemap/manual_index.html
* The python dependencies are the same as ShakeMap 4.0, so use the setup_env.sh
  script from here: https://github.com/usgs/shakemap

Workflow
--------

### Rupture Set

Generally, we start with sceanrio sources defined in JSON files. The subdirectory
"rupture_sets" includes a few examples. Note that there is more than one accepable
format for the rupture sets because different sources of ruptures use different
representations. Here is an example rupture set JSON file with only a single simple
rupture (extracted from US_MT_2016.json):
```
{
    "name": "2016 Montanta Scenarios",
    "info": "Derived by expert opinion with input from Michael Stickney, Kathy Haller.",
    "events":
    [
	{
	    "id":"greatfalls_se",
	    "desc":"Great Falls",
	    "mag":6.01,
	    "width":12.3,
	    "dip":90,
	    "rake":0,
	    "ztor":1.0,
	    "lats":[47.542, 47.499],
	    "lons":[-111.435, -111.406]
	}
    ]
}
```
If you create a rupture set for scenarios, I would like to archive them in this
repository. So please send it in as a pull request or email the file to me. 

### Input Directories

The `mkinputdir` command line program will generate an input directory for
each of the events in a rupture set. The arguments are explained with the help
message:
```
$ mkinputdir -h
usage: mkinputdir [-h] [-f FILE] [-r REFERENCE] [-d {-1,0,1,2}]
                  [-i [INDEX [INDEX ...]]] [-s SHAKEHOME]

Create ShakeMap input directory. This is designed primarily to be used with an
input file that provides rupture information. Currently, this only supports
the BSSC2014 JSON format. TODO: * Add support for NSHM XML format * Add
support for Excel rupture template * prompt for minimal info if file is not
provided

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  File with rupture information.
  -r REFERENCE, --reference REFERENCE
                        Reference for rupture source.
  -d {-1,0,1,2}, --dirind {-1,0,1,2}
                        Directivity; -1 for no directivity (default); 0 and 2
                        are the two opposing unilateral directions, 1 is for
                        bilateral.
  -i [INDEX [INDEX ...]], --index [INDEX [INDEX ...]]
                        List of rupture indices to run. Useful if you do not
                        want to run all ruptures in the file.
  -s SHAKEHOME, --shakehome SHAKEHOME
                        the location of ShakeMap install; default is
                        ~/ShakeMap.
```
A few things to note:
- This is where directivity is seleccted if needed.
- The resulting input directories will use the current time/date as the
  time/date for the scenario by default. This can be edited in the resulting
  event.xml file if required by the scenario exercise.

### Grid Calculations

The `runscenarios` command line program will calculate the ground motion grids
for all of events in the current ShakeMap data directory, which is basically
just a wrapper around the `mkscenariogrids` program that runs on an individual
event directory. I usually use `runscenarios` because I don't keep old event
directories around in the data directory, and when I re-run things, I usually
do the full set all at once. Some key things that need to be set in either
of these programs are:
* Vs30 grid file
* What GMPE to use. Currently this only supports the NSHMP GMPE sets/weights,
  but it is easy to add new ones, or use a single GMPE.
* `runscenarios` has an additional argument for the number of processors to use.
  If you are running a large number of events, it will run them in parallel, but
  the the code is not written to parallelize the calculations within a single
  scenario.

### Run ShakeMap 3.5
The input directories now have all the required files, as well as the
*estimates.grd and *sd.grd files. So ShakeMap 3.5 is run to generate the various
products that are transferred to COMCAT.

Note that I have not written a command line argument for doing this, but there
is a helper method `run_one_old_shakemap` in this repository. Here is a python
script that uses this to run ShakeMap 3.5 on all of the events in the current
data directory:
```
import os
from scenarios.utils import run_one_old_shakemap
from impactutils.io.cmd import get_command_output
# Arguments
datadir = '/Users/emthompson/shake/data'
id_str = next(os.walk(datadir))[1]
n = len(id_str)
logs = [None]*n
for i in range(0, n):
    logs[i] = run_one_old_shakemap(id_str[i], shakehome = '/Users/emthompson/shake')

```
Note: just running shakemap without this helper function probably will not work.
Also, if anything goes wrong, the list of logs can be helpful for
troubleshooting.
