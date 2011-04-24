#!/usr/bin/env python

from urlparse import parse_qs
from wscompose import wscompose
import StringIO

def application(environ, start_response):

    query_string = environ.get('QUERY_STRING', None)
    params = parse_qs(query_string)

    x_headers = None

    try:

        ws = wscompose()

        if len(params.keys()) == 0:

            content_type = 'text/plain'
            data = ws.help()

        else:

            ctx = ws.load_ctx(params)
            format = ctx.get('output', 'png')

            img = ws.draw_map()
            x_headers = ws.generate_x_headers(img)

            if format == 'json':

                content_type = 'application/js'
                data = ws.generate_javascript_output(img)

            else:

                fh = StringIO.StringIO()
                img.save(fh, format.upper())

                content_type = 'image/%s' % format.lower()
                data = fh.getvalue()

        status = '200 OK'

    except Exception, e:

        status = '500 SERVER ERROR'
        content_type = 'text/plain'
        data = str(e)

    # headers

    response_headers = [
        ('Content-type', str(content_type)),
        ('Content-Length', str(len(data)))
        ]

    if x_headers:
        for k, v in x_headers.items():
            response_headers.append((k, str(v)))

    # go!

    start_response(status, response_headers)
    return iter([data])

if __name__ == '__main__' :

    from wsgiref.simple_server import make_server
    server = make_server('localhost', 9999, application)
    server.serve_forever()
