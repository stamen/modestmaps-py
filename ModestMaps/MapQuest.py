"""
>>> p = RoadProvider()
>>> p.getTileUrls(Coordinate(10, 13, 7)) #doctest: +ELLIPSIS
('http://otile....mqcdn.com/tiles/1.0.0/7/13/10.png',)
>>> p.getTileUrls(Coordinate(13, 10, 7)) #doctest: +ELLIPSIS
('http://otile....mqcdn.com/tiles/1.0.0/7/10/13.png',)

>>> p = AerialProvider()
>>> p.getTileUrls(Coordinate(10, 13, 7)) #doctest: +ELLIPSIS
('http://oatile....mqcdn.com/naip/7/13/10.png',)
>>> p.getTileUrls(Coordinate(13, 10, 7)) #doctest: +ELLIPSIS
('http://oatile....mqcdn.com/naip/7/10/13.png',)
"""

from math import pi

from .Core import Coordinate
from .Geo import MercatorProjection, deriveTransformation
from .Providers import IMapProvider

import random
from . import Tiles

class AbstractProvider(IMapProvider):
    def __init__(self):
        # the spherical mercator world tile covers (-π, -π) to (π, π)
        t = deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
        self.projection = MercatorProjection(0, t)

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

class RoadProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://otile%d.mqcdn.com/tiles/1.0.0/%d/%d/%d.png' % (random.randint(1, 4), coordinate.zoom, coordinate.column, coordinate.row),)

class AerialProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://oatile%d.mqcdn.com/naip/%d/%d/%d.png' % (random.randint(1, 4), coordinate.zoom, coordinate.column, coordinate.row),)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
