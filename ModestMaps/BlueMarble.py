"""
>>> p = Provider()
>>> p.getTileUrls(Coordinate(10, 13, 7))
('http://s3.amazonaws.com/com.modestmaps.bluemarble/7-r10-c13.jpg',)
>>> p.getTileUrls(Coordinate(13, 10, 7))
('http://s3.amazonaws.com/com.modestmaps.bluemarble/7-r13-c10.jpg',)
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
        return ('http://s3.amazonaws.com/com.modestmaps.bluemarble/%d-r%d-c%d.jpg' % (coordinate.zoom, coordinate.row, coordinate.column),)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
