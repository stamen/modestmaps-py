"""
>>> p = OriginalProvider('example')
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/1/256/16/10507/25322.png',)

>>> p = FineLineProvider('example')
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/2/256/16/10507/25322.png',)

>>> p = TouristProvider('example')
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/7/256/16/10507/25322.png',)

>>> p = FreshProvider('example')
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/997/256/16/10507/25322.png',)

>>> p = PaleDawnProvider('example')
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/998/256/16/10507/25322.png',)

>>> p = MidnightCommanderProvider('example')
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/999/256/16/10507/25322.png',)
"""

from Core import Coordinate
from Geo import MercatorProjection, Transformation
from Providers import IMapProvider

import random, Tiles

class AbstractProvider(IMapProvider):
    def __init__(self, apikey):
        t = Transformation(1.068070779e7, 0, 3.355443185e7,
		                   0, -1.068070890e7, 3.355443057e7)

        self.projection = MercatorProjection(26, t)
        
        self.key = apikey

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

    def getTileUrls(self, coordinate):
        zoom, column, row = coordinate.zoom, coordinate.column, coordinate.row
        return ('http://tile.cloudmade.com/%s/%d/256/%d/%d/%d.png' % (self.key, self.style, zoom, column, row),)

class OriginalProvider(AbstractProvider):
    style = 1

class FineLineProvider(AbstractProvider):
    style = 2

class TouristProvider(AbstractProvider):
    style = 7

class FreshProvider(AbstractProvider):
    style = 997

class PaleDawnProvider(AbstractProvider):
    style = 998

class MidnightCommanderProvider(AbstractProvider):
    style = 999

if __name__ == '__main__':
    import doctest
    doctest.testmod()
