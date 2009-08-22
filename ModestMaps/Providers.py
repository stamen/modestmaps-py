from Core import Coordinate
from Geo import LinearProjection, MercatorProjection, Transformation

import math

ids = ('MICROSOFT_ROAD', 'MICROSOFT_AERIAL', 'MICROSOFT_HYBRID',
       'YAHOO_ROAD',     'YAHOO_AERIAL',     'YAHOO_HYBRID',
       'BLUE_MARBLE',
       'OPEN_STREET_MAP')

class IMapProvider:
    def __init__(self):
        raise NotImplementedError("Abstract method not implemented by subclass.")
        
    def getTileUrls(self, coordinate):
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
        raise NotImplementedError("Abstract method not implemented by subclass.")

    def sourceCoordinate(self, coordinate):
        wrappedColumn = coordinate.column % math.pow(2, coordinate.zoom)
        
        while wrappedColumn < 0:
            wrappedColumn += math.pow(2, coordinate.zoom)
            
        return Coordinate(coordinate.row, wrappedColumn, coordinate.zoom)

class TemplatedMercatorProvider(IMapProvider):
    def __init__(self, template):
        t = Transformation(1.068070779e7, 0, 3.355443185e7,
		                   0, -1.068070890e7, 3.355443057e7)

        self.projection = MercatorProjection(26, t)
        self.template = template

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

    def getTileUrls(self, coordinate):
        x, y, z = str(int(coordinate.column)), str(int(coordinate.row)), str(int(coordinate.zoom))
        return (self.template.replace('{X}', x).replace('{Y}', y).replace('{Z}', z),)
