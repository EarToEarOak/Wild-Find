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

import sqlite3

from peregrine.constants import LOG_SIZE


VERSION = 1


def create_database(connection):
    with connection:
        cmd = 'pragma foreign_keys = 1;'
        connection.execute(cmd)
        cmd = 'pragma auto_vacuum = incremental;'
        connection.execute(cmd)

        # Info table
        cmd = ('create table if not exists '
               'Info ('
               '    Key text primary key,'
               '    Value blob)')
        connection.execute(cmd)
        try:
            cmd = 'insert into info VALUES ("DbVersion", ?)'
            connection.execute(cmd, (VERSION,))
        except sqlite3.IntegrityError as error:
            pass
        except sqlite3.OperationalError as error:
            err = 'Database error: {}'.format(error.message)
            return err

        # Scans table
        cmd = ('create table if not exists '
               'Scans ('
               '    TimeStamp integer primary key,'
               '    Freq real)')
        connection.execute(cmd)

        # Signals table
        cmd = ('create table if not exists '
               'Signals ('
               '    Id integer primary key autoincrement,'
               '    TimeStamp integer,'
               '    Freq real,'
               '    Mod integer,'
               '    Rate real,'
               '    Level real,'
               '    Lon real,'
               '    Lat real,'
               '    foreign key (TimeStamp) REFERENCES Scans (TimeStamp)'
               '        on delete cascade)')
        connection.execute(cmd)

        # Log table
        cmd = ('create table if not exists '
               'Log ('
               '    Id integer primary key autoincrement,'
               '    TimeStamp text,'
               '    Message )')
        connection.execute(cmd)

        # Log pruning trigger
        cmd = ('create trigger if not exists LogPrune insert on Log when '
               '(select count(*) from log) > {} '
               'begin'
               '    delete from Log where Log.Id not in '
               '      (select Log.Id from Log order by'
               '          Id desc limit {});'
               'end;').format(LOG_SIZE, LOG_SIZE - 1)
        connection.execute(cmd)

        return None
