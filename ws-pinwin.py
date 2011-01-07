import optparse
import wscompose
import wscompose.pinwin

if __name__ == "__main__" :

    parser = optparse.OptionParser()
    parser.add_option("-p", "--port", dest="port", help="port number that the ws-pinwin HTTP server will listen on", default=9999)

    (opts, args) = parser.parse_args()

    app = wscompose.server(wscompose.pinwin.handler, int(opts.port))
    app.loop()
