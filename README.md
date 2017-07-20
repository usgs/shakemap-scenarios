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
* Shakemap 3.5: http://usgs.github.io/shakemap/manual_index.html
* The python dependencies are the same as ShakeMap 4.0, so use the setup_env.sh
  script from here: https://github.com/usgs/shakemap

Workflow
--------

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

