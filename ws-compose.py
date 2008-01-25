import wscompose

if __name__ == "__main__" :        
    app = wscompose.server(wscompose.handler)
    app.loop()
