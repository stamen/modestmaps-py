# -*-python-*-

#
# $Id$
#

import ModestMaps
import StringIO
import sys

from urlparse import urlparse
from cgi import parse_qs, escape
import signal, thread, threading, time, sys
import BaseHTTPServer, SocketServer, mimetypes
import re
import tempfile
import textwrap
import string
import base64
import Image

# ##############################################################

global done, server

done = False
server = None

# ##############################################################

class WebServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

# ##############################################################

class WebRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    # ##########################################################
    
    def __init__ (self, request, client_address, server) :
        self.__mrk = None
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
         
    # ##########################################################
    
    def do_GET(self):

        scheme, host, path, params, query, hash = urlparse(self.path)
        params = parse_qs(query)

        args = self.validate_params(params)

        if not args :
            return

        img = self.draw_map(args)

        if not img :
            return

        self.send_map(img)
        return

    # ##########################################################
    
    def draw_map (self, args) :
        try :

            if args.has_key('bbox') :
                return self.draw_map_extentified(args)
            else :
                return self.draw_map_centered(args)
            
        except Exception, e :
            self.error(200, "composer error : %s" % e)
            return False

    # ##########################################################

    def draw_map_extentified (self, args) :

        provider = self.load_provider(args['provider'])
        
        coord, offset = ModestMaps.calculateMapExtent(provider,
                                                      args['width'], args['height'],
                                                      ModestMaps.Geo.Location(args['bbox'][0], args['bbox'][1]),
                                                      ModestMaps.Geo.Location(args['bbox'][2], args['bbox'][3]))

        dim = ModestMaps.Core.Point(args['width'], args['height'])
        map = ModestMaps.Map(provider, dim, coord, offset)            
        img = map.draw()

        if args.has_key('filter') :
            img = self.apply_filtering(img, args['filter'])

        return img
    
    # ##########################################################
    
    def draw_map_centered (self, args) :
        
        provider = self.load_provider(args['provider'])
        loc = ModestMaps.Geo.Location(args['latitude'], args['longitude'])
        
        # Migurski : "coordinate.zoomTo() returns a copy,
        # rather than modifying the coordinate in-place."
        
        coordinate = provider.locationCoordinate(loc)            
        coordinate = coordinate.zoomTo(args['zoom'])
        
        coord, offset = ModestMaps.calculateMapCenter(provider, coordinate)
        dim = ModestMaps.Core.Point(args['width'], args['height'])
        
        map = ModestMaps.Map(provider, dim, coord, offset)            
        img = map.draw()

        if args.has_key('filter') :
            img = self.apply_filtering(img, args['filter'])

        if args.has_key('marker') :            
            self.add_marker(img, args)
                
        return img
            
    # ##########################################################

    def pinwin(self) :

        return """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
RU5ErkJggg=="""

    	return pw

    # ##########################################################
    
    def get_marker (self) :

        # sort of pointless in a CGI-context
        # but think of the ponies...
        
        if not self.__mrk :
            pw = self.pinwin()
            self.__mrk = Image.open(StringIO.StringIO(base64.decodestring(pw)))
            
        return self.__mrk

    # ##########################################################

    def apply_filtering (self, img, filter) :

        return self.apply_atkinson_dithering(img)
    
    # ##########################################################
    
    #
    # http://mike.teczno.com/notes/atkinson.html
    #
    
    def apply_atkinson_dithering(self, img) :

        img = img.convert('L')

        threshold = 128*[0] + 128*[255]

        for y in range(img.size[1]):
            for x in range(img.size[0]):

                old = img.getpixel((x, y))
                new = threshold[old]
                err = (old - new) >> 3 # divide by 8
            
                img.putpixel((x, y), new)
        
                for nxy in [(x+1, y), (x+2, y), (x-1, y+1), (x, y+1), (x+1, y+1), (x, y+2)]:
                    try:
                        img.putpixel(nxy, img.getpixel(nxy) + err)
                    except IndexError:
                        pass

        return img.convert('RGBA')
    
    # ##########################################################
    
    def add_marker(self, img, args) :

        (x, y) = img.size
        marker = self.get_marker()
            
        if args['provider'] == args['marker'] :
            offset = 75 / 2
            nw = (x / 2) - offset
            se = (y / 2) + offset
            thumb = img.crop((nw, nw, se, se))
            
        else :
            args['height'] = 75
            args['width'] = 75
            args['provider'] = args['marker']
            args['marker'] = ''
            args['dither'] = 0            
            thumb = self.draw_map(args)

        #
        
        marker.paste(thumb, (11, 10))
        
        x = (x / 2) - 28
        y = (y / 2) - 134

        img.paste(marker, (x, y), marker)
    
    # ##########################################################
    
    def send_map (self, img) :

        # Oh PIL, why don't you have a 'tostringDWIM' method?

        fh = StringIO.StringIO()
        img.save(fh, "PNG")
        
        self.send_response(200, "OK")
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", fh.len)         
        self.send_header("X-ImageHeight", img.size[1])
        self.send_header("X-ImageWidth", img.size[0])        
        self.end_headers()

        self.wfile.write(fh.getvalue())
        return
        

    # ##########################################################
    
    def load_provider (self, value) :

        # Please for this method to be in MM itself...
        
        if value == 'MICROSOFT_ROAD':
            return ModestMaps.Microsoft.RoadProvider()
        
        elif value == 'MICROSOFT_AERIAL':
            return ModestMaps.Microsoft.AerialProvider()
        
        elif value == 'MICROSOFT_HYBRID':
            return ModestMaps.Microsoft.HybridProvider()
        
        elif value == 'GOOGLE_ROAD':
            return ModestMaps.Google.RoadProvider()
        
        elif value == 'GOOGLE_AERIAL':
            return ModestMaps.Google.AerialProvider()
        
        elif value == 'GOOGLE_HYBRID':
            return ModestMaps.Google.HybridProvider()
        
        elif value == 'YAHOO_ROAD':
            return ModestMaps.Yahoo.RoadProvider()
        
        elif value == 'YAHOO_AERIAL':
            return ModestMaps.Yahoo.AerialProvider()
        
        elif value == 'YAHOO_HYBRID':
            return ModestMaps.Yahoo.HybridProvider()
        
        else :
            return None
            
    # ##########################################################
    
    def validate_params (self, params) :

        if len(params.keys()) == 0 :
            self.help()
            return False

        #

        valid = {}
        
        re_coord    = re.compile(r"^-?\d+(?:\.\d+)?$")
        re_num      = re.compile(r"^\d+$")
        re_provider = re.compile(r"^(GOOGLE|YAHOO|MICROSOFT)_(ROAD|HYBRID|AERIAL)$")

        #
        # where am i?
        # 
        
        if params.has_key('bbox') :

            bbox = params['bbox'][0].split(",")

            if len(bbox) != 4 :
                self.error(101, "Missing or incomplete %s parameter" % 'bbox')
                return False

            bbox = map(string.strip, bbox)
            
            for pt in bbox :
                if not re_coord.match(pt) :
                    self.error(102, "Not a valid lat/long : %s" % pt)
                    return False

            valid['bbox'] = map(float, bbox)
            
        else :
        
            for p in ('latitude', 'longitude') :

                if not params.has_key(p) :
                    self.error(101, "Missing %s parameter" % p)
                    return False
            
                if not re_coord.match(params[p][0]) :
                    self.error(102, "Not a valid lat/long : %s" % p)
                    return False

                valid[p] = float(params[p][0])

            #
            
            if not params.has_key('accuracy') :
                self.error(101, "Missing %s parameter" % 'accuracy')
                return False

            if not re_num.match(params['accuracy'][0]) :
                self.error(102, "Not a valid number %s" % 'accuracy')
                return False

            valid['zoom'] = float(params['accuracy'][0])            
            
        #
        # dimensions
        #
        
        for p in ('height', 'width') :

            if not params.has_key(p) :
                self.error(101, "Missing %s parameter" % p)
                return False

            if not re_num.match(params[p][0]) :
                self.error(102, "Not a valid number %s" % p)
                return False

            valid[p] = int(params[p][0])
            
        #
        # map provider
        #
        
        if not params.has_key('provider') :
            self.error(101, "Missing %s parameter" % p)
            return False
        
        if not re_provider.match(params['provider'][0].upper()) :
            self.error(102, "Not a valid provider")
            return False

        valid['provider'] = params['provider'][0].upper()
        
        #
        # markers?
        #
        
        if params.has_key('marker') :
            if not re_provider.match(params['marker'][0].upper()) :
                self.error(102, "Not a valid marker provider")
                return False

            valid['marker'] = params['marker'][0]
        
        #
        # filters
        #

        if params.has_key('filter') and params['filter'][0]:
            valid['filter'] = params['filter'][0]

        #
        # whoooosh
        #
        
        return valid

    # ##########################################################

    def help (self) :
        
        self.send_response(200, "OK")
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        
        self.wfile.write("ws-compose.py - a bare bone HTTP interface to the ModestMaps map tile composer.\n\n")

        self.help_header("Example")
        self.help_para("http://127.0.0.1:9999/?provider=GOOGLE_ROAD&marker=YAHOO_AERIAL&latitude=41.904688&longitude=12.494308&accuracy=17&height=500&width=500")
        self.help_para("Returns a PNG file of a map centered on the Santa Maria della Vittoria, in Rome.")
        
        self.help_header("Parameters")
        self.help_option('provider', 'A valid ModestMaps map tile provider.', True)
        self.help_option('marker', 'A valid ModestMaps map tile provider. Used to overlay a "pinwin" marker over the chosen lat/lon point', False)
        self.help_option('latitude','A valid decimal latitude.', True)
        self.help_option('longitude', 'A valid decimal longitude.', True)
        self.help_option('accuracy', 'The zoom level / accuracy (as defined by ModestMaps rather than any individual tile provider) of the final image.', True)
        self.help_option('height', 'The height of the final image', True)
        self.help_option('width', 'The width of the final image', True)
        
        self.help_header("Errors")
        self.help_para("Errors are returned with the HTTP status code 500. Specific error codes and messages are returned both in the message body as XML and in the 'X-ErrorCode' and 'X-ErrorMessage' headers.")

        self.help_header("Notes")
        self.help_para("Currently, ws-compose only supports 'centered' maps; map images based on their geographic extent (bounding box) are not available at this time")

        self.help_header("Questions")
        self.help_qa("Is it fast?", "Not really. It is designed, primarily, to be run on the same machine that is calling the interface.") 
        self.help_qa("Will it ever be fast?", "Sure. It is on The List (tm) to create a mod_python and/or wsgi version. Patches are welcome.")
        self.help_qa("Can I request map images asynchronously?", "Not yet.")
        self.help_qa("Can I get a pony?", "No.")

        self.help_header("License")
        self.help_para("Copyright (c) 2007 Aaron Straup Cope. All Rights Reserved. This is free software. You may redistribute it and/or modify it under the same terms the Perl Artistic License.")

    # ##########################################################

    def help_para(self, text) :

        self.wfile.write(textwrap.fill(text, 72))
        self.wfile.write("\n\n")
        
    def help_header(self, title) :
        ln = "-" * 72
        self.wfile.write("%s\n" % ln);
        self.wfile.write("%s\n" % title.upper())
        self.wfile.write("%s\n\n" % ln);
        
    def help_option(self, opt, desc, required) :

        present = "required"

        if not required :
            present = "optional"
            
        self.wfile.write("* %s (%s)\n\n%s\n\n" % (opt, present, textwrap.fill(desc, 72, initial_indent="\t", subsequent_indent="\t")))
        
    def help_qa(self, question, answer) :
        self.wfile.write("%s\n\n" % question)
        self.wfile.write("%s\n\n" % textwrap.fill(answer, 72, initial_indent="\t", subsequent_indent="\t"))

    # ##########################################################
    
    def error (self, err_code=999, err_msg="OH NOES!!! INVISIBLE ERRORZ!!!") :

        err_code = self.sanitize(err_code)
        err_msg  = self.sanitize(err_msg)
        
        self.send_response(500, "Server Error")
        self.send_header("Content-Type", "application/xml") 
        self.send_header("X-ErrorCode", err_code)
        self.send_header("X-ErrorMessage", err_msg)         
        self.end_headers()
        self.wfile.write("<?xml version=\"1.0\" ?><error code=\"%s\">%s</error>" % (err_code, err_msg))

    # ##########################################################
    
    def sanitize (self, str) :
        return escape(unicode(str))
    
# ##############################################################

def serve(port):    
    signal.signal(signal.SIGINT, terminate)
    thread.start_new_thread(runServer, (port,))
    
    global done
    while not done:
        try:
            time.sleep(0.3)
        except IOError:
            pass
   
    global server
    server.server_close()
    
def runServer(port):

    url = "http://127.0.0.1:%s" % port    
    print "ws-compose server running on port %s" % port
    print "documentation and usage is available at %s/\n\n" % url

    global server
    server = WebServer(("", port), WebRequestHandler)
    server.allow_reuse_address = True
    server.serve_forever()

def terminate(sig_num, frame):
    global done
    done = True    

# ##############################################################

if __name__ == "__main__":

    if len(sys.argv) >= 2 :
        port = int(sys.argv[1])
    else :
        port = 9999
        
    serve(port)
