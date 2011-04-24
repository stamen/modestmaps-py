import sys
sys.path.insert(0, '/home/asc/ext/python/modestmaps-py/')

from urlparse import parse_qs
from wscompose import wscompose

def application(environ, start_response):

    # path_info = environ.get('PATH_INFO', None)

    query_string = environ.get('QUERY_STRING', None)
    params = parse_qs(query_string)

    ws = wscompose()

    x_headers = None

    try:

        if len(params.keys()) == 0:

            status = '200 OK'
            content_type = 'text/plain'
            data = ws.help()

        else:

            ctx = ws.load_ctx(params)
            format = ws.ctx.get('output', 'png')

            img = ws.draw_map()

            if format == 'json':

                content_type = 'application/js'
                data = self.generate_javascript_output(img)

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
            response_headers.append(k, str(v))

    # go!

    start_response(status, response_headers)
    return iter([data])
