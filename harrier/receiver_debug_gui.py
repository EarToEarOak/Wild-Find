#!/usr/bin/env python
#
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

import argparse
import os

import wx

from harrier import receiver_debug


def parse_arguments():
    parser = argparse.ArgumentParser(description='GUI for receiver testmode')

    parser.add_argument('dir', help='Capture directory',
                        nargs='?', default=os.getcwd())
    parser.add_argument('args',
                        help='Arguments to pass through',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = parse_arguments()

    app = wx.App(False)

    while True:
        dlg = wx.FileDialog(None, "Choose a capture", args.dir, '',
                            'WAVE File (*.wav)|*.wav', wx.OPEN)
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_OK:
            argList = ['wav', '{}'.format(dlg.GetPath())]
            argList.extend(args.args)
            receiver_debug.main(argList)
        else:
            break
