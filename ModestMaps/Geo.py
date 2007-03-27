"""
>>> t = Transformation(1, 0, 0, 0, 1, 0)
>>> p = Point(1, 1)
>>> p
(1.000, 1.000)
>>> p_ = t.transform(p)
>>> p_
(1.000, 1.000)
>>> p__ = t.untransform(p_)
>>> p__
(1.000, 1.000)

>>> t = Transformation(0, 1, 0, 1, 0, 0)
>>> p = Point(0, 1)
>>> p
(0.000, 1.000)
>>> p_ = t.transform(p)
>>> p_
(1.000, 0.000)
>>> p__ = t.untransform(p_)
>>> p__
(0.000, 1.000)

>>> t = Transformation(1, 0, 1, 0, 1, 1)
>>> p = Point(0, 0)
>>> p
(0.000, 0.000)
>>> p_ = t.transform(p)
>>> p_
(1.000, 1.000)
>>> p__ = t.untransform(p_)
>>> p__
(0.000, 0.000)

>>> m = MercatorProjection(10)
>>> m.locationCoordinate(Location(0, 0))
(-0.000, 0.000 @10.000)
>>> m.locationCoordinate(Location(37, -122))
(0.696, -2.129 @10.000)
"""

import math
from Core import Point, Coordinate

class Location:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        
    def __repr__(self):
        return '(%(lat).3f, %(lon).3f)' % self.__dict__

class Transformation:
    def __init__(self, ax, bx, cx, ay, by, cy):
        self.ax = ax
        self.bx = bx
        self.cx = cx
        self.ay = ay
        self.by = by
        self.cy = cy
    
    def transform(self, point):
        return Point(self.ax*point.x + self.bx*point.y + self.cx,
                     self.ay*point.x + self.by*point.y + self.cy)
                         
    def untransform(self, point):
        return Point((point.x*self.by - point.y*self.bx - self.cx*self.by + self.cy*self.bx) / (self.ax*self.by - self.ay*self.bx),
                     (point.x*self.ay - point.y*self.ax - self.cx*self.ay + self.cy*self.ax) / (self.bx*self.ay - self.by*self.ax))

class IProjection:
    def __init__(self, zoom, transformation=Transformation(1, 0, 0, 0, 1, 0)):
        self.zoom = zoom
        self.transformation = transformation
        
    def rawProject(self, point):
        raise NotImplementedError("Abstract method not implemented by subclass.")
        
    def rawUnproject(self, point):
        raise NotImplementedError("Abstract method not implemented by subclass.")

    def project(self, point):
        point = self.rawProject(point)
        if(self.transformation):
            point = self.transformation.transform(point)
        return point
    
    def unproject(self, point):
        if(self.transformation):
            point = self.transform.untransformation(point)
        point = self.rawUnproject(point)
        return point
        
    def locationCoordinate(self, location):
        point = Point(math.pi * location.lon / 180.0, math.pi * location.lat / 180.0)
        point = self.project(point)
        return Coordinate(point.y, point.x, self.zoom)

    def coordinateLocation(self, coordinate):
        coordinate = coordinate.zoomTo(self.zoom)
        point = Point(coordinate.column, coordinate.row)
        point = self.unproject(point)
        return Location(180.0 * point.y / math.pi, 180.0 * point.x / math.pi)

class LinearProjection(IProjection):
    def rawProject(self, point):
        return Point(point.x, point.y)

    def rawUnproject(self, point):
        return Point(point.x, point.y)

class MercatorProjection(IProjection):
    def rawProject(self, point):
        return Point(point.x,
                     math.log(math.tan(0.25 * math.pi + 0.5 * point.y)))

    def rawUnproject(self, point):
        return Point(point.x,
                     2 * math.atan(math.pow(math.e, point.y)) - 0.5 + math.pi)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
