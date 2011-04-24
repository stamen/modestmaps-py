#!/usr/bin/env python

import optparse
from wsgiref.simple_server import make_server
from wscompose.WSGIComposeServer import application

if __name__ == "__main__" :

    parser = optparse.OptionParser()
    parser.add_option("-p", "--port", dest="port", help="port number that the ws-pinwin HTTP server will listen on", default=9999)

    (opts, args) = parser.parse_args()

    server = make_server('localhost', int(opts.port), application)
    server.serve_forever()
