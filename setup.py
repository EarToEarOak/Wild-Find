#!/usr/bin/env python
#
#
# Wild Find
#
#
# Copyright 2014 - 2017 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from setuptools import setup, find_packages

from wildfind.common.version import VERSION


setup(name='wild-find',
      version='.'.join([str(x) for x in VERSION]),
      description='A software suite designed to track and map the locations of VHF transmitters which are typically used to locate wildlife in ecological studies.',
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Scientific/Engineering :: Bio-Informatics'
                   'Topic :: Scientific/Engineering :: Visualization'],
      keywords='wildlife tracking ecology',
      url='https://github.com/EarToEarOak/Wild-Find',
      author='Al Brown',
      author_email='al [at] eartoearok.com',
      license='GPLv2',
      packages=find_packages(),
      package_data={'wildfind.falconer.gui': ['*'],
                    'wildfind.falconer.htdocs': ['*'],
                    'wildfind.falconer.htdocs.ol': ['*']},
      scripts=['falconer.py', 'harrier.py'],
      install_requires=['matplotlib', 'natgrid', 'numpy', 'pyrtlsdr', 'pyserial', 'PySide', 'scipy'])
