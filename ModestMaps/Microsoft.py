"""
>>> p = RoadProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://r....ortho.tiles.virtualearth.net/tiles/r0230102122203031.png?g=45',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://r....ortho.tiles.virtualearth.net/tiles/r0230102033330212.png?g=45',)

>>> p = AerialProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://a....ortho.tiles.virtualearth.net/tiles/a0230102122203031.jpeg?g=45',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://a....ortho.tiles.virtualearth.net/tiles/a0230102033330212.jpeg?g=45',)

>>> p = HybridProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://h....ortho.tiles.virtualearth.net/tiles/h0230102122203031.jpeg?g=45',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://h....ortho.tiles.virtualearth.net/tiles/h0230102033330212.jpeg?g=45',)
"""

from Core import Coordinate
from Geo import MercatorProjection, Transformation
from Providers import IMapProvider

import random, Tiles

class AbstractProvider(IMapProvider):
    def __init__(self):
        t = Transformation(1.068070779e7, 0, 3.355443185e7,
		                   0, -1.068070890e7, 3.355443057e7)

        self.projection = MercatorProjection(26, t)

    def getZoomString(self, coordinate):
        return Tiles.toMicrosoft(int(coordinate.column), int(coordinate.row), int(coordinate.zoom))

class RoadProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://r%d.ortho.tiles.virtualearth.net/tiles/r%s.png?g=45' % (random.randint(0, 3), self.getZoomString(self.sourceCoordinate(coordinate))),)

class AerialProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://a%d.ortho.tiles.virtualearth.net/tiles/a%s.jpeg?g=45' % (random.randint(0, 3), self.getZoomString(self.sourceCoordinate(coordinate))),)

class HybridProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://h%d.ortho.tiles.virtualearth.net/tiles/h%s.jpeg?g=45' % (random.randint(0, 3), self.getZoomString(self.sourceCoordinate(coordinate))),)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
