from distutils.core import setup
import os.path
import versioneer

setup(name='scenarios',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Shakemap scenarios',
      author='Eric Thompson',
      author_email='emthompson@usgs.gov',
      url='http://github.com/usgs/shakemap',
      packages=['scenarios'],
      package_data={'scenarios': [os.path.join('rupture_sets', '*'),
                                  os.path.join('tests', 'data', '*') ]},
      scripts=['runscenarios', 'mkinputdir', 'mkscenariogrids'],
      )
