#
# Project Peregrine
#
#
# Copyright 2014 - 2015 Al Brown
#
# Wildlife tracking and mapping
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import ConfigParser
import sys

from comm import Comm


class Settings(object):
    def __init__(self, args):

        self.db = args.file

        self.delay = None

        self.freq = args.frequency
        self.recvIndex = None
        self.recvGain = None
        self.gps = Comm()

        self.__load_conf(args.conf)

    def __load_conf(self, confFile):

        config = ConfigParser.SafeConfigParser()

        try:
            config.read(confFile)

            if config.has_option('scan', 'delay'):
                self.delay = config.getint('scan', 'delay')

            if config.has_option('receiver', 'index'):
                self.recvIndex = config.getint('receiver', 'index')

            if config.has_option('receiver', 'gain'):
                self.recvGain = config.getfloat('receiver', 'gain')

            self.gps.port = config.get('gps', 'port')

            if config.has_option('gps', 'baud'):
                bauds = self.gps.get_bauds()
                baud = config.getint('gps', 'baud')
                if baud in bauds:
                    self.gps.baud = baud
                else:
                    raise ValueError('Baud "{}" is not one of:\n  {}'.format(baud,
                                                                             bauds))

            if config.has_option('gps', 'bits'):
                bits = config.getint('gps', 'bits')
                if bits in Comm.BITS:
                    self.gps.bits = bits
                else:
                    raise ValueError('Bits "{}" is note one of:\n  {}'.format(bits,
                                                                              Comm.BITS))

            if config.has_option('gps', 'parity'):
                parity = config.get('gps', 'parity')
                if parity in Comm.PARITIES:
                    self.gps.parity = parity
                else:
                    raise ValueError('Parity "{}" is not one of:\n  {}'.format(parity,
                                                                               Comm.PARITIES))

            if config.has_option('gps', 'stops'):
                stops = config.getfloat('gps', 'stops')
                if stops in Comm.STOPS:
                    self.gps.stops = stops
                else:
                    raise ValueError('Stops "{}" is not one of:\n  {}'.format(stops,
                                                                              Comm.STOPS))

            if config.has_option('gps', 'soft'):
                self.gps.soft = config.getboolean('gps', 'soft')

        except ConfigParser.Error as e:
            sys.stderr.write('Configuration error: {}\n'.format(e))
            exit(2)
        except ValueError as e:
            sys.stderr.write('Configuration error: {}\n'.format(e))
            exit(2)
