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

>>> p = BaseProvider('example', 510)
>>> p.getTileUrls(Coordinate(25322, 10507, 16)) #doctest: +ELLIPSIS
('http://tile.cloudmade.com/example/510/256/16/10507/25322.png',)
"""

from math import pi

from .Core import Coordinate
from .Geo import MercatorProjection, deriveTransformation
from .Providers import IMapProvider

import random
from . import Tiles

class BaseProvider(IMapProvider):
    def __init__(self, apikey, style=None):
        # the spherical mercator world tile covers (-π, -π) to (π, π)
        t = deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
        self.projection = MercatorProjection(0, t)
        
        self.key = apikey
        
        if style:
            self.style = style

    def tileWidth(self):
        return 256

    def tileHeight(self):
        return 256

    def getTileUrls(self, coordinate):
        zoom, column, row = coordinate.zoom, coordinate.column, coordinate.row
        return ('http://tile.cloudmade.com/%s/%d/256/%d/%d/%d.png' % (self.key, self.style, zoom, column, row),)

class OriginalProvider(BaseProvider):
    style = 1

class FineLineProvider(BaseProvider):
    style = 2

class TouristProvider(BaseProvider):
    style = 7

class FreshProvider(BaseProvider):
    style = 997

class PaleDawnProvider(BaseProvider):
    style = 998

class MidnightCommanderProvider(BaseProvider):
    style = 999

if __name__ == '__main__':
    import doctest
    doctest.testmod()
