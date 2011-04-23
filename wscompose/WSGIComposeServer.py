import urlparse
import wscompose

def application(environ, start_response):

    # path_info = environ.get('PATH_INFO', None)

    query_string = environ.get('QUERY_STRING', None)
    params = urlparse.parse_qs(query_string)

    ws = wscompose.wscompose()

    try:

        if len(params.keys()) == 0:

            status = '200 OK'
            content_type = 'text/plain'
            data = ws.help()

        else:

            ws.load_ctx(params)

            status = '200 OK'
            content_type = 'text/plain'
            data = str(params)

    except Exception, e:

        print >> environ['wsgi.errors'], "[gunistache] failed to handle request:" + str(e)
        status = '500 SERVER ERROR'
        content_type = 'text/plain'
        data = str(e)

    # mod_wsgi hates unicode apparently
    # so make sure everything is a str.

    response_headers = [
        ('Content-type', str(content_type)),
        ('Content-Length', str(len(data)))
        ]

    start_response(status, response_headers)
    return iter([data])
