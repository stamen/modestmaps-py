import sys
import wscompose

if __name__ == "__main__" :        
    try:
        port = int(sys.argv[1])
    except:
        port = None
    app = wscompose.server(wscompose.handler, port)
    app.loop()
