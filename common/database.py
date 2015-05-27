#!/usr/bin/env python
#
# Wild Find
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

from common.constants import LOG_SIZE


VERSION = 3


def __create_table_info(cursor):
    cmd = ('create table if not exists '
           'Info ('
           '    Key text primary key,'
           '    Value integer)')
    cursor.execute(cmd)

    cmd = 'insert into info VALUES ("DbVersion", ?)'
    cursor.execute(cmd, (VERSION,))


def __create_table_scans(cursor):
    cmd = ('create table if not exists '
           'Scans ('
           '    TimeStamp integer primary key,'
           '    Freq real,'
           '    Survey text)')
    cursor.execute(cmd)


def __create_table_signals(cursor):
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
    cursor.execute(cmd)


def __create_table_log(cursor):
    cmd = ('create table if not exists '
           'Log ('
           '    Id integer primary key autoincrement,'
           '    TimeStamp integer,'
           '    Message )')
    cursor.execute(cmd)


def __create_tables(cursor):
    __create_table_info(cursor)
    __create_table_scans(cursor)
    __create_table_signals(cursor)
    __create_table_log(cursor)

    # Log pruning trigger
    cmd = ('create trigger if not exists LogPrune insert on Log when '
           '(select count(*) from log) > {} '
           'begin'
           '    delete from Log where Log.Id not in '
           '      (select Log.Id from Log order by'
           '          Id desc limit {});'
           'end;').format(LOG_SIZE, LOG_SIZE - 1)
    cursor.execute(cmd)


def __upgrade(cursor):
    cmd = 'select value from Info where key = "DbVersion"'
    cursor.execute(cmd)
    result = cursor.fetchone()
    version = int(result['Value'])
    if version == VERSION:
        return None

    if version == 1:
        __upgrade_1_to_2(cursor)
        __upgrade_2_to_3(cursor)

    if version == 2:
        return __upgrade_2_to_3(cursor)


def __upgrade_1_to_2(cursor):
    cmd = 'alter table Scans add column Survey text'
    cursor.execute(cmd)

    cmd = 'update Scans set Survey="Unspecified" where Survey is null'
    cursor.execute(cmd)

    cmd = 'update Info set Value = ? where Key = "DbVersion"'
    cursor.execute(cmd, (2,))


def __upgrade_2_to_3(cursor):
    cmd = 'alter table Log rename to Temp'
    cursor.execute(cmd)
    __create_table_log(cursor)

    cmd = ('insert into Log (Id, TimeStamp, Message) '
           'select Id, TimeStamp, Message from Temp')
    cursor.execute(cmd)

    cmd = 'update Info set Value = ? where Key = "DbVersion"'
    cursor.execute(cmd, (3,))


def create_database(connection):
    err = None

    with connection:
        try:
            cmd = 'pragma foreign_keys = 1;'
            connection.execute(cmd)
            cmd = 'pragma auto_vacuum = incremental;'
            connection.execute(cmd)

            cursor = connection.cursor()

            cmd = ('select name from sqlite_master where '
                   'type = "table" and name = "Info"')
            cursor.execute(cmd)
            table = cursor.fetchall()
            if len(table):
                __upgrade(cursor)
                cmd = 'drop table if exists temp'
                cursor.execute(cmd)
            else:
                __create_tables(cursor)
        except sqlite3.IntegrityError as error:
            err = 'Database error: {}'.format(error.message)
        except sqlite3.OperationalError as error:
            err = 'Database error: {}'.format(error.message)

    return err


def name_factory(cursor, row):
    names = {}
    for i, column in enumerate(cursor.description):
        names[column[0]] = row[i]

    return names
