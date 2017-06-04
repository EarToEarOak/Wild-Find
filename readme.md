# Wild Find #

## Wildlife tracking and mapping ##

Copyright 2014-2017 Al Brown

al [at] eartoearoak.com



A software suite designed to track and map the locations of VHF transmitters which are typically used to locate wildlife in ecological studies.

It uses RTLSDR compatible USB dongles to receive the transmissions and any GPS unit which provides NMEA data.

Please note this software is at the Beta stage and currently undergoing testing.

More information can be found on the [website](https://eartoearoak.com/software/wild-find)

## Usage ##
Wild Find consists of two components: Harrier and Falconer.

**Harrier** is used to survey for transmissions and can be run on single board computers such as the Raspberry Pi 2.

**Falconer** is a desktop application which uses the data from Harrier to statistically map the locations of the transmitters. 

## Harrier ##
Harrier is a command line application, most of the set up is contained in a configuration file (and example is included the the `conf` directory).  The configuration file should be updated and copied to your home directory unless you explicitly specify it's location.

Harrier can be started by specifying a centre frequency to scan around. For example to scan for collars near 150MHz:

    python harrier.py -f 150

This will write to a file called `harrier.wfh` which can be opened with the Falconer application.  If this file already exists survey data will be appended to it.

Pressing [CTRL][C] will exit the application.


## Falconer ##
Falconer is used to map the data from Harrier.

From Falconer one or more surveys can be selected (a survey is generated each time Harrier is run), as well as individual scans (a scan is a sweep of frequencies at a particular time).  Finally the detected signals can be filtered (to include particular collars or exclude erroneous transmissions).

Start Falconer by using the command:

    python falconer.py


## License ##

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation version 2.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
