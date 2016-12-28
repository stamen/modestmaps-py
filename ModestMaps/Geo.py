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
>>> m.coordinateLocation(Coordinate(0, 0, 10))
(0.000, 0.000)
>>> m.locationCoordinate(Location(37, -122))
(0.696, -2.129 @10.000)
>>> m.coordinateLocation(Coordinate(0.696, -2.129, 10.000))
(37.001, -121.983)
"""

import math
from .Core import Point, Coordinate

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

def deriveTransformation(a1x, a1y, a2x, a2y, b1x, b1y, b2x, b2y, c1x, c1y, c2x, c2y):
    """ Generates a transform based on three pairs of points, a1 -> a2, b1 -> b2, c1 -> c2.
    """
    ax, bx, cx = linearSolution(a1x, a1y, a2x, b1x, b1y, b2x, c1x, c1y, c2x)
    ay, by, cy = linearSolution(a1x, a1y, a2y, b1x, b1y, b2y, c1x, c1y, c2y)
    
    return Transformation(ax, bx, cx, ay, by, cy)

def linearSolution(r1, s1, t1, r2, s2, t2, r3, s3, t3):
    """ Solves a system of linear equations.

          t1 = (a * r1) + (b + s1) + c
          t2 = (a * r2) + (b + s2) + c
          t3 = (a * r3) + (b + s3) + c

        r1 - t3 are the known values.
        a, b, c are the unknowns to be solved.
        returns the a, b, c coefficients.
    """

    # make them all floats
    r1, s1, t1, r2, s2, t2, r3, s3, t3 = map(float, (r1, s1, t1, r2, s2, t2, r3, s3, t3))

    a = (((t2 - t3) * (s1 - s2)) - ((t1 - t2) * (s2 - s3))) \
      / (((r2 - r3) * (s1 - s2)) - ((r1 - r2) * (s2 - s3)))

    b = (((t2 - t3) * (r1 - r2)) - ((t1 - t2) * (r2 - r3))) \
      / (((s2 - s3) * (r1 - r2)) - ((s1 - s2) * (r2 - r3)))

    c = t1 - (r1 * a) - (s1 * b)
    
    return a, b, c

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
            point = self.transformation.untransform(point)
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
                     2 * math.atan(math.pow(math.e, point.y)) - 0.5 * math.pi)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
