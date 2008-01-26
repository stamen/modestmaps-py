import wscompose
import wscompose.pinwin

if __name__ == "__main__" :        
    app = wscompose.server(wscompose.pinwin.handler)
    app.loop()
