"""
>>> p = RoadProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://mt....google.com/mt?n=404&v=...&x=10507&y=25322&zoom=1',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://mt....google.com/mt?n=404&v=...&x=10482&y=25333&zoom=1',)

>>> p = AerialProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://kh....google.com/kh?n=404&v=...&t=tqtsqrqtrtttqsqsr',)
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://kh....google.com/kh?n=404&v=...&t=tqtsqrqtqssssqtrt',)

>>> p = HybridProvider()
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://kh....google.com/kh?n=404&v=...&t=tqtsqrqtrtttqsqsr', 'http://mt....google.com/mt?n=404&v=...&x=10507&y=25322&zoom=1')
>>> p.getTileUrls(Coordinate(25333, 10482, 16)) #doctest: +ELLIPSIS
('http://kh....google.com/kh?n=404&v=...&t=tqtsqrqtqssssqtrt', 'http://mt....google.com/mt?n=404&v=...&x=10482&y=25333&zoom=1')
"""

from Core import Coordinate
from Geo import MercatorProjection, Transformation
from Providers import IMapProvider

import random, Tiles

ROAD_VERSION = 'w2.60'
AERIAL_VERSION = '20'
HYBRID_VERSION = 'w2t.60'

class AbstractProvider(IMapProvider):
    def __init__(self):
        t = Transformation(1.068070779e7, 0, 3.355443185e7,
		                   0, -1.068070890e7, 3.355443057e7)

        self.projection = MercatorProjection(26, t)

    def getZoomString(self, coordinate):
        raise NotImplementedError()

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

class RoadProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://mt%d.google.com/mt?n=404&v=%s&%s' % (random.randint(0, 3), ROAD_VERSION, self.getZoomString(self.sourceCoordinate(coordinate))),)
        
    def getZoomString(self, coordinate):
        return 'x=%d&y=%d&zoom=%d' % Tiles.toGoogleRoad(int(coordinate.column), int(coordinate.row), int(coordinate.zoom))

class AerialProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        return ('http://kh%d.google.com/kh?n=404&v=%s&t=%s' % (random.randint(0, 3), AERIAL_VERSION, self.getZoomString(self.sourceCoordinate(coordinate))),)

    def getZoomString(self, coordinate):
        return Tiles.toGoogleAerial(int(coordinate.column), int(coordinate.row), int(coordinate.zoom))

class HybridProvider(AbstractProvider):
    def getTileUrls(self, coordinate):
        under = AerialProvider().getTileUrls(coordinate)[0]
        over = 'http://mt%d.google.com/mt?n=404&v=%s&%s' % (random.randint(0, 3), HYBRID_VERSION, RoadProvider().getZoomString(self.sourceCoordinate(coordinate)))
        return (under, over)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
