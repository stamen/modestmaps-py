# -*-python-*-

__package__    = "wscompose/pinwin.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wscompose"
__date__       = "$Date: 2008/01/04 06:23:46 $"
__copyright__  = "Copyright (c) 2007-2008 Aaron Straup Cope. Perl Artistic License."

import wscompose

import wscompose.plotting
import wscompose.dithering

import re
import urllib
import Image
import ImageDraw
import StringIO
import ModestMaps
import validate

# TO DO (patches are welcome) :
#
# - figure out whether/what code here should be merged
#   with plotting.py

class handler (wscompose.plotting.handler, wscompose.dithering.handler) :

    def draw_map (self) :

        img = wscompose.handler.draw_map(self)

        if self.ctx.has_key('filter') and self.ctx['filter'] == 'atkinson' :
            img = self.atkinson_dithering(img)
            
        if self.ctx.has_key('markers') :

            self.reposition_markers()
            
            if self.ctx.has_key('bleed') :
                img = self.draw_markers_with_bleed(img)                
            else :
                img = self.draw_markers(img)            

        return img

    # ##########################################################

    def send_x_headers (self, img) :

        wscompose.handler.send_x_headers(self, img)
        
        if self.ctx.has_key('markers') :
            
            for mrk_data in self.ctx['markers'] :
            
                # The first two numbers are the x/y coordinates for the lat/lon.
                # The second two are the x/y coordinates of the top left corner
                # where the actual pinwin content should be pasted. The last pair
                # are the dimensions of the pinwin content which is sort of redundant
                # unless you are opting for defaults and don't know what to expect.

                details = (mrk_data['x'], mrk_data['y'],
                           mrk_data['x_fill'], mrk_data['y_fill'],
                           mrk_data['width'], mrk_data['height'])
                
                details = map(str, details)
                header = "X-wscompose-Marker-%s" % mrk_data['label']
                sep = ","
                
                self.send_header(header, sep.join(details))
        
    # ##########################################################

    # only works for method='bbox' ... WTF?

    # To do : move this code in to methods that can be run
    # easily from unit tests and/or CLI tools...
    
    def draw_markers_with_bleed (self, img) :
            
        bleed_top = 0
        bleed_right = 0
        bleed_bottom = 0
        bleed_left = 0
        bleed = 0

        for data in self.ctx['markers'] :
            (top, right, bottom, left) = self.calculate_bleed(img, data)

            bleed_top = min(bleed_top, top)
            bleed_right = max(bleed_right, right)
            bleed_bottom = max(bleed_bottom, bottom)
            bleed_left = min(bleed_left, left)
            
            # print "%s : top: %s, right: %s, bottom: %s, left: %s" % (data['label'], bleed_top, bleed_right, bleed_bottom, bleed_left)
            
        #
        
        if bleed_top : 
            bleed_top -= bleed_top * 2
            
        if bleed_left :
            bleed_left -= bleed_left * 2
            
        #
        
        bleed_x = bleed_left
        bleed_y = bleed_top
        
        if bleed_top or bleed_right :

            old = img.copy()
            sz = old.size

            x = sz[0] + bleed_left + bleed_right
            y = sz[1] + bleed_top + bleed_bottom

            # print "new x: %s y: %s" % (x, y)
            # print "paste x: %s y: %s" % (bleed_x, bleed_y)
            
            img = Image.new('RGB', (x, y), 'white')
            img.paste(old, (bleed_x, bleed_y))
            
        #
        
        for data in self.ctx['markers'] :
            self.draw_marker(img, data, bleed_x, bleed_y)

        return img

    # ##########################################################

    def calculate_bleed (self, img, mrk_data) :

        w = mrk_data['width']
        h = mrk_data['height']
        a = mrk_data['adjust_cone_height']
        
        mrk = self.load_marker(w, h, a)
        mrk_sz = mrk.fh().size
        
        loc = ModestMaps.Geo.Location(mrk_data['latitude'], mrk_data['longitude'])
        pt = self.ctx['map'].locationPoint(loc)            

        #
        
        mrk_data['x'] = int(pt.x)
        mrk_data['y'] = int(pt.y)

        mx = mrk_data['x'] - int(mrk.x_offset)
        my = mrk_data['y'] - int(mrk.y_offset)

        dx = mx + mrk.x_padding
        dy = my + mrk.y_padding

        #

        top = my
        right = (mx + mrk_sz[0]) - img.size[0]        
        
        left = mx
        bottom = my + mrk_sz[1] - img.size[1]

        # print "calc bleed %s, %s, %s, %s" % (top, right, bottom, left)
        return (top, right, bottom, left)

    # ##########################################################

    def draw_marker (self, img, mrk_data, bleed_x=0, bleed_y=0) :
        
        #
        # Dirty... hack to account for magic
        # center/zoom markers...
        #
        
        if mrk_data.has_key('fill') and mrk_data['fill'] == 'center' :
            if self.ctx['method'] == 'center' :
                mrk_data['latitude'] = self.ctx['latitude']
                mrk_data['longitude'] = self.ctx['longitude']
            else :
                offset_lat = (self.ctx['bbox'][2] - self.ctx['bbox'][0]) / 2
                offset_lon = (self.ctx['bbox'][3] - self.ctx['bbox'][1]) / 2
            
                mrk_data['latitude'] = self.ctx['bbox'][0] + offset_lat
                mrk_data['longitude'] = self.ctx['bbox'][1] + offset_lon

        wscompose.plotting.handler.draw_marker(self, img, mrk_data, bleed_x, bleed_y)

        #
        # Magic global fill in with a map hack
        #
        
        if self.ctx.has_key('fill') :
            mrk_data['fill'] = 'center'
            mrk_data['provider'] = self.ctx['fill']
            mrk_data['zoom'] = self.ctx['fill_zoom']

        try :
            fill = self.fetch_marker_fill(mrk_data)
        except Exception, e :
            return False

        #
        # Magic global fill in with a map hack
        #

        if self.ctx.has_key('fill') :
            # add centering dot
            # (flickr pink)
        
            pink = (255, 0, 132)

            (w, h) = fill.size
        
            h = h / 2
            w = w / 2
            
            x1 = int(w - 5)
            x2 = int(w + 5)
            y1 = int(h - 5)
            y2 = int(h + 5)
            
            dr = ImageDraw.Draw(fill)        
            dr.ellipse((x1, y1, x2, y2), outline=pink)
            
        # the offset to paste the filler content
        
        dx = mrk_data['x_fill']
        dy = mrk_data['y_fill']

        img.paste(fill, (dx, dy))
        return True
    
    # ##########################################################
    
    def fetch_marker_fill (self, mrk_data) :
        
        if mrk_data.has_key('fill') and mrk_data['fill'] == 'center' :
                
            args = {'height': mrk_data['height'],
                    'width' : mrk_data['width'],
                    'latitude' : mrk_data['latitude'],
                    'longitude' : mrk_data['longitude'],
                    'zoom' : mrk_data['zoom'],
                    'provider' : mrk_data['provider'],
                    }

            (host, port) = self.server.server_address

            if host == '' :
                host = "127.0.0.1"
                
            params = urllib.urlencode(args)
            
            url = "http://%s:%s?%s" % (host, port, params)
            
        else :
            url = mrk_data['fill']
            
        #
        
        data = urllib.urlopen(url).read()
        return Image.open(StringIO.StringIO(data)).convert('RGBA')        
    
    # ##########################################################

    def validate_params (self, params) :

        valid = wscompose.handler.validate_params(self, params)
        
        if not valid :
            return False

        #

        validator = validate.validate()

        #
        # markers
        #

        if params.has_key('marker') :

            try :
                valid['markers'] = validator.markers(params['marker'])
            except Exception, e :
                self.error(141, e)
                return False

        #
        # magic!
        #
        
        if params.has_key('fill') :

            re_provider = re.compile(r"^(GOOGLE|YAHOO|MICROSOFT)_(ROAD|HYBRID|AERIAL)$")
            re_num = re.compile(r"^\d+$")
                
            if not re_provider.match(params['fill'][0].upper()) :
                self.error(102, "Not a valid marker provider")
                return False

            valid['fill'] = unicode(params['fill'][0].upper())

            if params.has_key('fill_accuracy') :
                
                if not re_num.match(params['fill_accuracy'][0]) :
                    self.error(102, "Not a valid number %s" % 'accuracy')
                    return False

                valid['fill_zoom'] = float(params['fill_accuracy'])
                
            else :
                valid['fill_zoom'] = 15

        #

        if params.has_key('bleed') :
            valid['bleed'] = True
            
        #

        if params.has_key('filter') :

            valid_filters = ('atkinson')
            
            if not params['filter'][0] in valid_filters :
                self.error(104, "Not a valid marker filter")
                return False

            valid['filter'] = params['filter'][0]
            
        #
        
        return valid

    # ##########################################################
    
    def help_synopsis (self) :
        self.help_para("ws-pinwin.py - an HTTP interface to the ModestMaps map tile composer with support for rendering and plotting markers.\n\n")

    # ##########################################################

    def help_example (self) :
        self.help_header("Example")
        self.help_para("http://127.0.0.1:9999/?provider=MICROSOFT_ROAD&method=extent&bbox=45.482882,%20-73.619899,%2045.532687,%20-73.547801&height=1024&width=1024&marker=roy,45.521375561025756,%20-73.57049345970154&marker=mileend,45.525825499457,%20-73.5989034175872,600,180&marker=cherrier,45.51978191639917,-73.56947422027588&bleed=1")
        self.help_para("Returns a PNG file of a map of Montreal at the appropriate zoom level to display the bounding box in a image 1024 pixels square, with (3) empty pinwin markers.")

    # ##########################################################

    def help_parameters (self) :
        wscompose.handler.help_parameters(self)

        self.help_option('marker', 'Draw a pinwin-style marker at a given point. You may pass multiple marker arguments, each of which should contain the following comma separated values :', False)
        self.help_option('label', 'A unique string to identify the marker by', True, 1)
        self.help_option('point', 'A comma-separated string containing the latitude and longitude indicating the point where the marker should be placed', True, 1)
        self.help_option('dimensions', 'A comma-separated string containing the height and width of the marker canvas - the default is 75 x 75', False, 1)   

        self.help_option('fill', 'A helper argument which if present will cause each marker specified to be filled with the contents of map for the marker\'s coordinates at zoom level 15. The value should be a valid ModestMaps map tile provider.', False)
        
        self.help_option('adjust', 'Adjust the size of the bounding box argument by (n) kilometers; you may want to do this if you have markers positioned close to the sides of your bounding box', False)
        self.help_option('bleed', 'If true, the final image will be enlarged to ensure that all marker canvases are not clipped', False)

        self.help_option('filter', 'Filter the map image before any markers are applied. Valid options are :', False)
        self.help_option('atkinson', 'Apply the Atkinson dithering algorithm to the map image', False, 1)        

    # ##########################################################

    def help_notes (self) :
        self.help_header("Notes")        
        self.help_para("The shadows for the markers are stylized by design; especially when they have been repositioned and have very long stems. Not only do they look funny, I've decided I like that they look funny.")
        self.help_para("\"Proper\" shadows rendered in correct perspective are on the list and if you want to help me with the math then they be added sooner still.")

    # ##########################################################

    def help_metadata (self) :
        self.help_header("Metadata")

        self.help_para("Metadata about an image is returned in HTTP headers prefixed with 'X-wscompose-'.")
        self.help_para("For example : ")
        
        self.help_pre("""	HTTP/1.x 200 OK
        Server: BaseHTTP/0.3 Python/2.5
        Date: Sun, 13 Jan 2008 01:08:37 GMT
        Content-Type: image/png
        Content-Length: 1946576
        X-wscompose-Image-Height: 1024
        X-wscompose-Image-Width: 1024
        X-wscompose-Map-Zoom: 14.0
        X-wscompose-Marker-mileend: 336,211,157,-131,600,180
        X-wscompose-Marker-roy: 667,285,629,165,75,75
        X-wscompose-Marker-cherrier: 679,312,641,192,75,75""")

        self.help_para("Most headers are self-explanatory. Markers are a little more complicated.")

        self.help_para("The string after 'X-wscompose-Marker-' is the label assigned to the marker when the API call was made. The value is a comma separated list interpreted as follows :")

        self.help_para("The first two numbers are the x/y coordinates for the lat/lon.")
        self.help_para("The second two are the x/y coordinates of the top left corner where the actual pinwin content should be pasted.")
        self.help_para("The last pair  are the dimensions of the pinwin content which is sort of redundant unless you are opting for defaults and don't know what to expect.")

    # ##########################################################
