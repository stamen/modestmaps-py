# -*-python-*-

import ModestMaps

from math import sin, cos, acos, radians, degrees

import base64

import StringIO
import types

try:
    import json
except Exception, e:
    import simplejson as json

from wscompose.help import *
from wscompose.validate import *

class wserror(Exception):

    def __init__ (self, code=999, msg='OH NOES'):
        self.code = 999
        self.msg = msg

    def __str__ (self):
        return repr(self.msg)

class wscompose:

    def __init__ (self, environ={}) :

        self.environ = environ
        self.ctx = {}
        self.points = {}

    def load_ctx (self, params) :
        self.ctx = self.validate_params(params)
        return self.ctx

    def draw_map (self) :

        try :

            if self.ctx['method'] == 'extent' :
                return self.draw_map_extentified()
            elif self.ctx['method'] == 'bbox' :
                return self.draw_map_bbox()
            else :
                return self.draw_map_centered()

        except Exception, e :
            raise wserror(200, "composer error : %s" % e)

    def draw_map_extentified (self) :

        if self.ctx.has_key('adjust') :
            self.ctx['bbox'] = self.__adjust_bbox(self.ctx['bbox'], self.ctx['adjust'])

        provider = self.load_provider(self.ctx['provider'])

        sw = ModestMaps.Geo.Location(self.ctx['bbox'][0], self.ctx['bbox'][1])
        ne = ModestMaps.Geo.Location(self.ctx['bbox'][2], self.ctx['bbox'][3])
        dims = ModestMaps.Core.Point(self.ctx['width'], self.ctx['height']);

        self.ctx['map'] = ModestMaps.mapByExtent(provider, sw, ne, dims)

        coord, offset = ModestMaps.calculateMapExtent(provider,
                                                      self.ctx['width'], self.ctx['height'],
                                                      ModestMaps.Geo.Location(self.ctx['bbox'][0], self.ctx['bbox'][1]),
                                                      ModestMaps.Geo.Location(self.ctx['bbox'][2], self.ctx['bbox'][3]))

        self.ctx['zoom'] = coord.zoom

        return self.ctx['map'].draw()

    # ##########################################################

    def draw_map_centered (self) :

        provider = self.load_provider(self.ctx['provider'])

        loc = ModestMaps.Geo.Location(self.ctx['latitude'], self.ctx['longitude'])
        dim = ModestMaps.Core.Point(self.ctx['width'], self.ctx['height'])
        zoom = self.ctx['zoom']

        self.ctx['map'] = ModestMaps.mapByCenterZoom(provider, loc, zoom, dim)
        return self.ctx['map'].draw()

    # ##########################################################

    def draw_map_bbox (self) :

        if self.ctx.has_key('adjust') :
            self.ctx['bbox'] = self.__adjust_bbox(self.ctx['bbox'], self.ctx['adjust'])

        #

        provider = self.load_provider(self.ctx['provider'])

        sw = ModestMaps.Geo.Location(self.ctx['bbox'][0], self.ctx['bbox'][1])
        ne = ModestMaps.Geo.Location(self.ctx['bbox'][2], self.ctx['bbox'][3])
        zoom = self.ctx['zoom']

        self.ctx['map'] = ModestMaps.mapByExtentZoom(provider, sw, ne, zoom)
        return self.ctx['map'].draw()

    # ##########################################################

    def __adjust_bbox (self, bbox, adjust) :

        swlat = bbox[0]
        swlon = bbox[1]
        nelat = bbox[2]
        nelon = bbox[3]

        adjust_ne = 1
        adjust_sw = 1

        if nelon < 0 :
            adjust_ne = - adjust_ne

        if swlon < 0 :
            adjust_sw = - adjust_sw

        dist_n = self.__dist(nelat, nelon, nelat, (nelon + adjust_ne))
        dist_s = self.__dist(swlat, swlon, swlat, (swlon + adjust_sw))

        swlat = swlat - (float(adjust) / float(dist_s))
        swlon = swlon - (float(adjust) / float(dist_s))
        nelat = nelat + (float(adjust) / float(dist_n))
        nelon = nelon + (float(adjust) / float(dist_n))

        return [swlat, swlon, nelat, nelon]

    # ##########################################################

    def __dist(self, lat1, lon1, lat2, lon2) :

        theta = lon1 - lon2
        dist = sin(radians(lat1)) * sin(radians(lat2)) +  cos(radians(lat1)) * cos(radians(lat2)) * cos(radians(theta));
        dist = acos(dist);
        dist = degrees(dist);

        return dist * 60

    # ##########################################################

    def generate_javascript_output(self, img) :

        fh = StringIO.StringIO()
        img.save(fh, "PNG")

        _json = self.generate_x_headers(img)
        _json['data'] = base64.b64encode(fh.getvalue())

        if self.ctx.get('json_callback', None) :
            callback = "%s(%s)" % (self.ctx['json_callback'], js)
            _json['json_callback'] = callback

        return json.dumps(_json)

    # ##########################################################

    def generate_x_headers (self, img) :

        headers = {
                "X-wscompose-Image-Height" : img.size[1],
                "X-wscompose-Image-Width" : img.size[0],
                "X-wscompose-Map-Zoom" : self.ctx['zoom']
                }

        for data in self.ctx.get('plots', []) :

            pt = self.latlon_to_point(data['latitude'], data['longitude'])

            key = "X-wscompose-Plot-%s" % data['label']
            coords = "%s,%s" % (int(pt.x), int(pt.y))
            headers[key] = coords

        return headers

    # ##########################################################

    def latlon_to_point (self, lat, lon) :

        key = "%s-%s" % (lat, lon)

        if not self.points.has_key(key) :
            loc = ModestMaps.Geo.Location(lat, lon)
            pt = self.ctx['map'].locationPoint(loc)
            self.points[key] = pt

        return self.points[key]

    # ##########################################################

    def load_provider (self, value) :

	if value.startswith('http://') or value.startswith('https://'):
	    return ModestMaps.Providers.TemplatedMercatorProvider(value, self.ctx['tilestache_cached'])
        elif value in ModestMaps.builtinProviders:
	    return ModestMaps.builtinProviders[value]()
        else :
            return None

    # ##########################################################

    def validate_params (self, params) :

        valid = {'output' : 'png'}

        #
        # La la la - I can't hear you
        #

        if not params.has_key('method') :
            params['method'] = ['center']

        #
        # Everyone needs a provider...
        #

        try :
            validate_ensure_args(params, ('provider',))
        except Exception, e :
            raise wserror(101, e)

        try :
            valid['provider'] = validate_provider(params['provider'][0])
        except Exception, e :
            raise wserror(101, e)

        if params.has_key('tilestache_cached'):
            valid['tilestache_cached'] = True
        else:
            valid['tilestache_cached'] = False

        #
        # Method specific requirements
        #

        if params['method'][0] == 'extent' :

            try :
                validate_ensure_args(params, ('bbox', 'height', 'width'))
            except Exception, e :
                raise wserror(111, e)

            try :
                valid['bbox'] = validate_bbox(params['bbox'][0])
            except Exception, e :
                raise wserror(112, e)

            for p in ('height', 'width') :

                try :
                    valid[p] = validate_dimension(params[p][0])
                except Exception, e :
                    raise wserror(113, e)

            if params.has_key('adjust') :

                try :
                    valid['adjust'] = validate_bbox_adjustment(params['adjust'][0])
                except Exception, e :
                    raise wserror(124, e)

            # you can blame migurski for this

            if params.has_key('zoom') :
                raise wserror(125, "'zoom' is not a valid argument when method is 'extent'")

        elif params['method'][0] == 'bbox' :

            try :
                validate_ensure_args(params, ('bbox', 'zoom'))
            except Exception, e :
                raise wserror(121, e)

            try :
                valid['bbox'] = validate_bbox(params['bbox'][0])
            except Exception, e :
                raise wserror(122, e)

            try :
                valid['zoom'] = validate_zoom(params['zoom'][0])
            except Exception, e :
                raise wserror(123, e)

            if params.has_key('adjust') :

                try :
                    valid['adjust'] = validate_bbox_adjustment(params['adjust'][0])
                except Exception, e :
                    raise wserror(124, e)

            # you can blame migurski for this

            for p in ('height', 'width') :
                if params.has_key(p) :
                    raise wserror(125, "'%s' is not a valid argument when method is 'bbox'" % p)

        # center

        else :

            try :
                validate_ensure_args(params, ('latitude', 'longitude', 'zoom', 'height', 'width'))
            except Exception, e :
                raise wserror(131, e)

            for p in ('latitude', 'longitude') :

                try :
                    valid[p] = validate_latlon(params[p][0])
                except Exception, e :
                    raise wserror(132, e)

            try :
                valid['zoom'] = validate_zoom(params['zoom'][0])
            except Exception, e :
                raise wserror(133, e)

            for p in ('height', 'width') :

                try :
                    valid[p] = validate_dimension(params[p][0])
                except Exception, e :
                    raise wserror(134, e)

        #
        # plotting or "headless" markers
        #

        if params.has_key('plot') :

            try :
                valid['plots'] = validate_plots(params['plot'])
            except Exception, e :
                raise wserror(141, e)

        #
        # json ?
        #

        if params.has_key('output') :

            out = params['output'][0].lower()

            if out == 'json' :
                valid['output'] = 'json'

            elif out == 'javascript' :
                if not params.has_key('callback') :
                    raise wserror(142, 'Missing JSON callback')

                try :
                    valid['json_callback'] = validate_json_callback(params['callback'][0])
                except Exception, e:
                    raise wserror(143, e)

                valid['output'] = 'json'

            elif out in ('png', 'jpeg') :
                valid['output'] = out

            else :
                raise wserror(144, 'Not a valid output format')

        #
        # whoooosh
        #

        valid['method'] = params['method'][0]

        return valid

    # ##########################################################

    def help (self) :

        return "\n\n".join([
                self.help_synopsis(),
                self.help_example(),
                self.help_parameters(),
                self.help_metadata(),
                self.help_errors(),
                self.help_questions(),
                self.help_license()
                ])

    # ##########################################################

    def help_synopsis (self) :
        return help_para("ws-compose.py - a bare bone HTTP interface to the ModestMaps map tile composer.")

    # ##########################################################

    def help_example (self) :

        host = self.environ.get('HTTP_HOST', '127.0.0.1:9999')

        return "\n\n".join([
                help_header("Example"),
                help_para("http://%s/?provider=MICROSOFT_ROAD&latitude=41.904688&longitude=12.494308&zoom=17&height=500&width=500" % host),
                help_para("Returns a PNG file of a map centered on the Santa Maria della Vittoria, in Rome.")
                ])



    # ##########################################################

    def help_parameters (self) :

        return "\n\n".join([
                help_header("Parameters"),

                help_option('provider', 'A valid ModestMaps map tile provider.', True),

                help_option('method', 'One of the following options :', True),

                help_option('center', 'Render map tiles centered around a specific coordinate. If defined, the following parameters must also be present : ', False, 1),
                help_option('latitude','A valid decimal latitude.', True, 2),

                help_option('longitude', 'A valid decimal longitude.', True, 2),

                help_option('accuracy', 'The zoom level / accuracy (as defined by ModestMaps rather than any individual tile provider) of the final image.', True, 2),

                help_option('height', 'The height of the final image', True, 2),

                help_option('width', 'The width of the final image', True, 2),

                help_option('extent', 'Render map tiles at a suitable zoom level in order to fit a bounding box in an image with specific dimensions. If defined, the following parameters must also be present : ', False, 1),

                help_option('bbox', 'A bounding box comprised of comma-separated decimal coordinates in the following order : SW latitude, SW longitude, NE latitude, NE longitude', True, 2),

                help_option('height', 'The height of the final image', True, 2),

                help_option('width', 'The width of the final image', True, 2),

                help_option('bbox', 'Render all the map tiles necessary to display a bounding box at a specific zoom level. If defined, the following parameters must also be present : ', False, 1),

                help_option('bbox', 'A bounding box comprised of comma-separated decimal coordinates in the following order : SW latitude, SW longitude, NE latitude, NE longitude', True, 2),

                help_option('accuracy', 'The zoom level / accuracy (as defined by ModestMaps rather than any individual tile provider) of the final image.', True, 2)     ,

                help_option('output', 'Although the default output format for maps is \'png\' (you know, like a PNG image file) you may also specify the following alternatives: ', False),

                help_option('json', 'Return a Base64 encoded version of a PNG image, as well as any extra X-wscompose headers, as JSON data structure.', False, 1),
                help_option('javascript', 'Return a Base64 encoded version of a PNG image, as well as any extra X-wscompose headers, as JSON data structure wrapped in a function whose name is defined by the \'callback\' parameter.', False, 1),

                help_option('callback', 'Required if the output format is \'javascript\'; this is the name of the callback function that your JSON data structure will be wrapped in.', False),

                help_option('plot', 'Plot -- but do not render -- the x and y coordinates for a given point. Coordinate data will be returned HTTP header(s) named \'X-wscompose-plot-\' followed by the label you choose when passing latitude and longitude information. You may pass multiple plot arguments, each of which should contain the following comma separated values :', False),

                help_option('label', 'A unique string to identify the plotting by', True, 1),

                help_option('point', 'A comma-separated string containing the latitude and longitude indicating the point to be plotted', True, 1)
                ])

    # ##########################################################

    def help_metadata (self) :

        return "\n\n".join([
                help_header("Metadata"),

                help_para("Metadata about an image is returned in HTTP headers prefixed with 'X-wscompose-'."),

                help_para("For example : "),

                help_pre("""	HTTP/1.x 200 OK
        Server: BaseHTTP/0.3 Python/2.5
        Date: Sun, 13 Jan 2008 01:08:37 GMT
        Content-Type: image/png
        Content-Length: 1946576
        X-wscompose-Image-Height: 1024
        X-wscompose-Image-Width: 1024
        X-wscompose-Map-Zoom: 14.0
        X-wscompose-plot-roy: 667,285"""),

                help_para("Most headers are self-explanatory. Plotted coordinates are a little more complicated."),

                help_para("The string after 'X-wscompose-plot' is the label assigned to the marker when the API call was made. The value is a comma separated list containing the x and y coordinates for (label's) corresponding latitude and longitude.")
                ])

    # ##########################################################

    def help_errors (self) :

        return "\n\n".join([
                help_header("Errors"),

                help_para("Errors are returned with the HTTP status code 500. Specific error codes and messages are returned both in the message body as XML and in the 'X-ErrorCode' and 'X-ErrorMessage' headers.")
                ])

    # ##########################################################

    def help_notes (self) :
        pass

    # ##########################################################

    def help_questions (self) :

        return "\n\n".join([
                help_header("Questions"),
                help_qa("Is it fast?", "Not really. It is designed, primarily, to be run on the same machine that is calling the interface."),
                help_qa("Will it ever be fast?", "Sure. The ws-compose.py script is just a thin wrapper around a WSGI compliant server which means you can run it with zippy web frameworks like gunicorn(.org). For example:"),
                help_pre("\t$> /usr/local/bin/gunicorn --options wscompose.WSGIComposeServer:application"),
                help_qa("Can I request map images asynchronously?", "Not yet."),
                help_qa("Can I get a pony?", "No.")
                ])

    # ##########################################################

    def help_license (self) :

        return "\n\n".join([
                help_header("License"),
                help_para("Copyright (c) 2007-2011 Aaron Straup Cope. All Rights Reserved. This is free software. You may redistribute it and/or modify it under the same terms the BSD license : http://www.modestmaps.com/license.txt")
                ])
