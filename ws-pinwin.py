import sys
import wscompose
import wscompose.pinwin

if __name__ == "__main__" :        
    try:
        port = int(sys.argv[1])
    except:
        port = None
    app = wscompose.server(wscompose.pinwin.handler, port)
    app.loop()
