"""
>>> p = Provider()
>>> p.getTileUrls(Coordinate(10, 13, 7))
('http://tile.openstreetmap.org/7/13/10.png',)
>>> p.getTileUrls(Coordinate(13, 10, 7))
('http://tile.openstreetmap.org/7/10/13.png',)
"""

from math import pi

from .Core import Coordinate
from .Geo import MercatorProjection, deriveTransformation
from .Providers import IMapProvider

from . import Tiles

class Provider(IMapProvider):
    def __init__(self):
        # the spherical mercator world tile covers (-π, -π) to (π, π)
        t = deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
        self.projection = MercatorProjection(0, t)

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

    def getTileUrls(self, coordinate):
        return ('http://tile.openstreetmap.org/%d/%d/%d.png' % (coordinate.zoom, coordinate.column, coordinate.row),)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
