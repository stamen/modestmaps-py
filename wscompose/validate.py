# -*-python-*-

__version__    = "1.1"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wscompose"
__date__       = "$Date: 2008/01/04 06:23:46 $"
__copyright__  = "Copyright (c) 2007-2008 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license."

import re
import urlparse

_re = {
    'coord' : re.compile(r"^-?\d+(?:\.\d+)?$"),
    'adjust' : re.compile(r"^(\d+(?:\.\d*)?|\d*?\.\d+)$"),
    'num' : re.compile(r"^\d+$"),
    'provider' : re.compile(r"^(\w+)$"),
    'label' : re.compile(r"^(?:[a-z0-9-_\.]+)$"),
    'hull' : re.compile(r"^(marker|dot|plot)$")
    }

# ##########################################################

def validate_regexp (label, string) :

    if not _re.has_key(label) :
        return False

    return _re[label].match(string)

# ##########################################################

def validate_ensure_args (args, required) :

    for i in required :

        if not args.has_key(i) :
            raise Exception, "Required argument %s missing" % i

    return True

# ##########################################################

def validate_bbox (input) :

    bbox = input.split(",")

    if len(bbox) != 4 :
        raise Exception, "Missing or incomplete %s parameter" % 'bbox'

    bbox = map(string.strip, bbox)

    for pt in bbox :
        if not validate_regexp('coord', pt) :
            raise Exception, "Not a valid lat/long : %s" % pt

    return map(float, bbox)

# ##########################################################

def validate_bbox_adjustment (input) :

    if not validate_regexp('adjust', str(input)) :
        raise Exception, "Not a valid adjustment %s " % input

    return float(input)

# ##########################################################

def validate_latlon (input) :

    if not validate_regexp('coord', input) :
        raise Exception, "Not a valid lat/long : %s" % input

    return float(input)

# ##########################################################

def validate_zoom (input) :
    return validate_number(input)

# ##########################################################

def validate_dimension (input) :
    return validate_number(input)

# ##########################################################

def validate_radius (input) :
    return validate_number(input)

# ##########################################################

def validate_provider (input):

    if input.startswith('http://'):
        # probably a URI template thing, let it slide
        return input

    input = input.upper()

    if not validate_regexp('provider', input) :
        raise Exception, "Not a valid provider : %s" % input

    return input

# ###########################################################

def validate_marker_label (input) :

    if not validate_regexp('label', input) :
        raise Exception, "Not a valid marker label"

    return unicode(input)

# ##########################################################

def validate_markers (markers) :

    valid = []

    for pos in markers :

        marker_data = {'width':75, 'height':75, 'adjust_cone_height' : 0}

        details = pos.split(",")
        details = map(string.strip, details)

        if len(details) < 3 :
            raise Exception, "Missing or incomplete %s parameter : %s" % ('marker', pos)

        # Magic center/zoom markers

        if details[0] == 'center' :

            marker_data['fill'] = 'center'
            marker_data['label'] = 'center'

            marker_data['provider'] = validate_provider(details[1])
            marker_data['zoom'] = self.zoom(details[2])

        # Pinwin name/label

        else :

            marker_data['label'] = validate_marker_label(details[0])

            # Pinwin location

            marker_data['latitude'] = validate_latlon(details[1])
            marker_data['longitude'] = validate_latlon(details[2])

        # Pinwin size

        if len(details) > 3 :

            if len(details) < 4 :
                raise Exception, "Missing height parameter"

            marker_data['width'] = validate_dimension(details[3])
            marker_data['height'] = validate_dimension(details[4])

        # URI for content to fill the pinwin with

        if len(details) > 5 :

            parts = urlparse.urlparse(details[5])

            if parts[1] == '' and parts[0] != 'file' :
                raise Exception, "Unknown URL"

            marker_data['fill'] = details[5]

        # Done

        valid.append(marker_data)

    return valid

    # ##########################################################

def validate_plots (plots) :

    valid = []

    for pos in plots :

        details = pos.split(",")
        details = map(string.strip, details)

        if len(details) < 3 :
            raise Exception, "Missing or incomplete %s parameter : %s" % ('plot', pos)

        data = {}

        data['label'] = validate_marker_label(details[0])

        # Pinwin location

        data['latitude'] = validate_latlon(details[1])
        data['longitude'] = validate_latlon(details[2])

        valid.append(data)

    return valid

# ##########################################################

def validate_dots (self, dots) :

    valid = []

    for pos in dots :

        details = pos.split(",")
        details = map(string.strip, details)
        cnt = len(details)

        if cnt < 3 :
            raise Exception, "Missing or incomplete %s parameter : %s" % ('dot', pos)

        data = {}

        data['label'] = validate_marker_label(details[0])
        data['latitude'] = validate_latlon(details[1])
        data['longitude'] = validate_latlon(details[2])

        if cnt > 3 :
                data['radius'] = validate_radius(details[3])
        else :
            data['radius'] = 18

        if cnt > 4 :
            pass
        else :
            data['colour'] = 'red'

        valid.append(data)

    return valid

# ##########################################################

def validate_polylines (lines) :

    valid = []

    for poly in lines :

        points = []

        for pt in poly.split(" ") :

            coord = pt.split(",")

            if len(coord) != 2 :
                raise Exception, "Polyline coordinate missing data"

            (lat, lon) = map(string.strip, coord)

            lat = validate_latlon(lat)
            lon = validate_latlon(lon)

            points.append({'latitude':lat, 'longitude':lon})

        valid.append(points)

    return valid

# ##########################################################

def validate_convex (hulls) :

    valid = []

    for label in hulls :

        if not validate_regexp('hull', label)  :
            raise Exception, "Unknown marker type for convex hulls"

        valid.append(label)

    return valid

# ##########################################################

def validate_json_callback(func) :

    if not self.re['label'].match(func) :
        raise Exception, "Invalid JSON callback name"

    return func

# ##########################################################

def validate_number(input) :

    if not validate_regexp('num', input) :
        raise Exception, "Not a valid number : %s" % p

    return int(input)

# ##########################################################
