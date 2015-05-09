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

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import os
import threading

from falconer.utils import add_program_path


PORT = 12015


class Server(object):
    def __init__(self):
        self._server = ThreadedServer(('localhost', PORT), Handler)

        thread = threading.Thread(target=self._server.serve_forever)
        thread.start()

    def close(self):
        self._server.shutdown()


class ThreadedServer(ThreadingMixIn, HTTPServer):
    pass


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = add_program_path('falconer', 'htdocs', self.path.lstrip('/'))

        if os.path.exists(path):
            self.send_response(200)
            self.__send_content_type(path)
            self.end_headers()

            f = open(path, 'r')
            self.wfile.write(f.read())
            f.close()
        else:
            self.send_response(404)

    def __send_content_type(self, path):
        content = 'text/plain'
        _root, ext = os.path.splitext(path)
        if ext == '.css':
            content = 'text/css'
        elif ext == '.html':
            content = 'text/html'
        elif ext == '.js':
            content = 'text/javascript'

        self.send_header('Content-type', content)


if __name__ == '__main__':
    print 'Please run falconer.py'
    exit(1)
