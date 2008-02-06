"""
>>> p = Provider()
>>> p.getTileUrls(Coordinate(10, 13, 7))
('http://tile.openstreetmap.org/7/13/10.png',)
>>> p.getTileUrls(Coordinate(13, 10, 7))
('http://tile.openstreetmap.org/7/10/13.png',)
"""

from Core import Coordinate
from Geo import MercatorProjection, Transformation
from Providers import IMapProvider

import Tiles

class Provider(IMapProvider):
    def __init__(self):
        t = Transformation(1.068070779e7, 0, 3.355443185e7,
		                   0, -1.068070890e7, 3.355443057e7)

        self.projection = MercatorProjection(26, t)

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

    def getTileUrls(self, coordinate):
        return ('http://tile.openstreetmap.org/%d/%d/%d.png' % (coordinate.zoom, coordinate.column, coordinate.row),)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
