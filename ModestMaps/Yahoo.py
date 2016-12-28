"""
>>> p = RoadProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://us.maps2.yimg.com/us.png.maps.yimg.com/png?v=...&t=m&x=10507&y=7445&z=2',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://us.maps2.yimg.com/us.png.maps.yimg.com/png?v=...&t=m&x=10482&y=7434&z=2',)

>>> p = AerialProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://us.maps3.yimg.com/aerial.maps.yimg.com/tile?v=...&t=a&x=10507&y=7445&z=2',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://us.maps3.yimg.com/aerial.maps.yimg.com/tile?v=...&t=a&x=10482&y=7434&z=2',)

>>> p = HybridProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://us.maps3.yimg.com/aerial.maps.yimg.com/tile?v=...&t=a&x=10507&y=7445&z=2', 'http://us.maps3.yimg.com/aerial.maps.yimg.com/png?v=...&t=h&x=10507&y=7445&z=2')
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://us.maps3.yimg.com/aerial.maps.yimg.com/tile?v=...&t=a&x=10482&y=7434&z=2', 'http://us.maps3.yimg.com/aerial.maps.yimg.com/png?v=...&t=h&x=10482&y=7434&z=2')
"""

from math import pi

from .Core import Coordinate
from .Geo import MercatorProjection, deriveTransformation
from .Providers import IMapProvider

from . import Tiles

ROAD_VERSION = '3.52'
AERIAL_VERSION = '1.7'
HYBRID_VERSION = '2.2'

class AbstractProvider(IMapProvider):
    def __init__(self):
        # the spherical mercator world tile covers (-π, -π) to (π, π)
        t = deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
        self.projection = MercatorProjection(0, t)

    def getZoomString(self, coordinate):
        return 'x=%d&y=%d&z=%d' % Tiles.toYahoo(int(coordinate.column), int(coordinate.row), int(coordinate.zoom))

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

class RoadProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://us.maps2.yimg.com/us.png.maps.yimg.com/png?v=%s&t=m&%s' % (ROAD_VERSION, self.getZoomString(self.sourceCoordinate(coordinate))),)

class AerialProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://us.maps3.yimg.com/aerial.maps.yimg.com/tile?v=%s&t=a&%s' % (AERIAL_VERSION, self.getZoomString(self.sourceCoordinate(coordinate))),)

class HybridProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        under = AerialProvider().getTileUrls(coordinate)[0]
        over = 'http://us.maps3.yimg.com/aerial.maps.yimg.com/png?v=%s&t=h&%s' % (HYBRID_VERSION, self.getZoomString(self.sourceCoordinate(coordinate)))
        return (under, over)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
