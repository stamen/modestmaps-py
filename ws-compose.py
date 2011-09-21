#!/usr/bin/python

import optparse
import wscompose

if __name__ == "__main__" :

    parser = optparse.OptionParser()
    parser.add_option("-p", "--port", dest="port", help="port number that the ws-compose HTTP server will listen on", default=9999)
    
    (opts, args) = parser.parse_args()
    
    app = wscompose.server(wscompose.handler, int(opts.port))
    app.loop()
