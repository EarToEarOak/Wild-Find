#! /usr/bin/env python

import argparse
import os

import wx

import receiver_test


def parse_arguments():
    parser = argparse.ArgumentParser(description='GUI for receiver test')

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
            argList = [dlg.GetPath()]
            argList.extend(args.args)
            receiver_test.main(argList)
        else:
            break
