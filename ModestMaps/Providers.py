import re
from math import pi, pow

from .Core import Coordinate
from .Geo import LinearProjection, MercatorProjection, deriveTransformation

ids = ('MICROSOFT_ROAD', 'MICROSOFT_AERIAL', 'MICROSOFT_HYBRID',
       'YAHOO_ROAD',     'YAHOO_AERIAL',     'YAHOO_HYBRID',
       'BLUE_MARBLE',
       'OPEN_STREET_MAP')

class IMapProvider:
    def __init__(self):
        raise NotImplementedError("Abstract method not implemented by subclass.")
        
    def getTileUrls(self, coordinate):
        raise NotImplementedError("Abstract method not implemented by subclass.")

    def tileWidth(self):
        raise NotImplementedError("Abstract method not implemented by subclass.")
    
    def tileHeight(self):
        raise NotImplementedError("Abstract method not implemented by subclass.")
    
    def locationCoordinate(self, location):
        return self.projection.locationCoordinate(location)

    def coordinateLocation(self, location):
        return self.projection.coordinateLocation(location)

    def sourceCoordinate(self, coordinate):
        wrappedColumn = coordinate.column % pow(2, coordinate.zoom)
        
        while wrappedColumn < 0:
            wrappedColumn += pow(2, coordinate.zoom)
            
        return Coordinate(coordinate.row, wrappedColumn, coordinate.zoom)

class TemplatedMercatorProvider(IMapProvider):
    """ Convert URI templates into tile URLs, using a tileUrlTemplate identical to:
        http://code.google.com/apis/maps/documentation/overlays.html#Custom_Map_Types
    """
    def __init__(self, template):
        # the spherical mercator world tile covers (-π, -π) to (π, π)
        t = deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
        self.projection = MercatorProjection(0, t)
        
        self.templates = []
        
        while template:
            match = re.match(r'^((http|https|file)://\S+?)(,(http|https|file)://\S+)?$', template)
            first = match.group(1)
            
            if match:
                self.templates.append(first)
                template = template[len(first):].lstrip(',')
            else:
                break

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

    def getTileUrls(self, coordinate):
        x, y, z = str(int(coordinate.column)), str(int(coordinate.row)), str(int(coordinate.zoom))
        return [t.replace('{X}', x).replace('{Y}', y).replace('{Z}', z) for t in self.templates]
