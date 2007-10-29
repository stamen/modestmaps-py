"""
>>> m = Map(Microsoft.RoadProvider(), Core.Point(600, 600), Core.Coordinate(3165, 1313, 13), Core.Point(-144, -94))
>>> p = m.locationPoint(Geo.Location(37.804274, -122.262940))
>>> p
(370.724, 342.549)
>>> m.pointLocation(p)
(37.804, -122.263)
"""

import PIL.Image, urllib, StringIO, math, thread, time

import Tiles
import Providers
import Core
import Geo
import Google, Yahoo, Microsoft

def calculateMapCenter(provider, centerCoord):
    """ Based on a center coordinate, returns the coordinate
        of an initial tile and it's point placement, relative to
        the map center.
    """

    # initial tile coordinate
    initTileCoord = Core.Coordinate(math.floor(centerCoord.row), math.floor(centerCoord.column), math.floor(centerCoord.zoom))

    # initial tile position, assuming centered tile well in grid
    initX = (initTileCoord.column - centerCoord.column) * provider.tileWidth()
    initY = (initTileCoord.row - centerCoord.row) * provider.tileHeight()
    initPoint = Core.Point(round(initX), round(initY))
    
    return initTileCoord, initPoint

def calculateMapExtent(provider, width, height, *args):

    coordinates = map(provider.locationCoordinate, args)
    
    TL = Core.Coordinate(min([c.row for c in coordinates]),
                         min([c.column for c in coordinates]),
                         min([c.zoom for c in coordinates]))

    BR = Core.Coordinate(max([c.row for c in coordinates]),
                         max([c.column for c in coordinates]),
                         max([c.zoom for c in coordinates]))
                    
    # multiplication factor between horizontal span and map width
    hFactor = (BR.column - TL.column) / (float(width) / provider.tileWidth())

    # multiplication factor expressed as base-2 logarithm, for zoom difference
    hZoomDiff = math.log(hFactor) / math.log(2)
        
    # possible horizontal zoom to fit geographical extent in map width
    hPossibleZoom = TL.zoom - math.ceil(hZoomDiff)
        
    # multiplication factor between vertical span and map height
    vFactor = (BR.row - TL.row) / (float(height) / provider.tileHeight())
        
    # multiplication factor expressed as base-2 logarithm, for zoom difference
    vZoomDiff = math.log(vFactor) / math.log(2)
        
    # possible vertical zoom to fit geographical extent in map height
    vPossibleZoom = TL.zoom - math.ceil(vZoomDiff)
        
    # initial zoom to fit extent vertically and horizontally
    initZoom = min(hPossibleZoom, vPossibleZoom)

    ## additionally, make sure it's not outside the boundaries set by provider limits
    #initZoom = min(initZoom, provider.outerLimits()[1].zoom)
    #initZoom = max(initZoom, provider.outerLimits()[0].zoom)

    # coordinate of extent center
    centerRow = (TL.row + BR.row) / 2
    centerColumn = (TL.column + BR.column) / 2
    centerZoom = (TL.zoom + BR.zoom) / 2
    centerCoord = Core.Coordinate(centerRow, centerColumn, centerZoom).zoomTo(initZoom)
    
    return calculateMapCenter(provider, centerCoord)
    
class TileRequest:
    
    # how many times to retry a failing tile
    MAX_ATTEMPTS = 5

    def __init__(self, provider, coord, offset):
        self.done = False
        self.provider = provider
        self.coord = coord
        self.offset = offset
        
    def loaded(self):
        return self.done
    
    def images(self):
        return self.imgs
    
    def load(self, lock, verbose, attempt=1):
        if self.done:
            # don't bother?
            return

        urls = self.provider.getTileUrls(self.coord)
        
        if verbose:
            print 'Requesting', urls, '- attempt no.', attempt, 'in thread', thread.get_ident()

        # this is the time-consuming part
        try:
            imgs = [PIL.Image.open(StringIO.StringIO(urllib.urlopen(url).read())).convert('RGBA')
                    for url in urls]

        except:
            if verbose:
                print 'Failed', urls, '- attempt no.', attempt, 'in thread', thread.get_ident()

            if attempt < TileRequest.MAX_ATTEMPTS:
                return self.load(lock, verbose, attempt+1)
            else:
                imgs = [None for url in urls]

        else:
            if verbose:
                print 'Received', urls, '- attempt no.', attempt, 'in thread', thread.get_ident()

        if lock.acquire():
            self.imgs = imgs
            self.done = True
            lock.release()

class TileQueue(list):
    """ List of TileRequest objects, that's sensitive to when they're loaded.
    """

    def pending(self):
        """ True if any contained tile is still loading.
        """
        remaining = [tile for tile in self if not tile.loaded()]
        return len(remaining) > 0

class Map:

    def __init__(self, provider, dimensions, coordinate, offset):
        """ Instance of a map intended for drawing to an image.
        
            provider
                Instance of IMapProvider
                
            dimensions
                Size of output image, instance of Point
                
            coordinate
                Base tile, instance of Coordinate
                
            offset
                Position of base tile relative to map center, instance of Point
        """
        self.provider = provider
        self.dimensions = dimensions
        self.coordinate = coordinate
        self.offset = offset
        
    def __str__(self):
        return 'Map(%(provider)s, %(dimensions)s, %(coordinate)s, %(offset)s)' % self.__dict__

    def locationPoint(self, location):
        """ Return an x, y point on the map image for a given geographical location.
        """
        point = Core.Point(self.offset.x, self.offset.y)
        coord = self.provider.locationCoordinate(location).zoomTo(self.coordinate.zoom)
        
        # distance from the known coordinate offset
        point.x += self.provider.tileWidth() * (coord.column - self.coordinate.column)
        point.y += self.provider.tileHeight() * (coord.row - self.coordinate.row)
        
        # because of the center/corner business
        point.x += self.dimensions.x/2
        point.y += self.dimensions.y/2
        
        return point
        
    def pointLocation(self, point):
        """ Return a geographical location on the map image for a given x, y point.
        """
        hizoomCoord = self.coordinate.zoomTo(Core.Coordinate.MAX_ZOOM)
        
        # because of the center/corner business
        point = Core.Point(point.x - self.dimensions.x/2,
                           point.y - self.dimensions.y/2)
        
        # distance in tile widths from reference tile to point
        xTiles = (point.x - self.offset.x) / self.provider.tileWidth();
        yTiles = (point.y - self.offset.y) / self.provider.tileHeight();
        
        # distance in rows & columns at maximum zoom
        xDistance = xTiles * math.pow(2, (Core.Coordinate.MAX_ZOOM - self.coordinate.zoom));
        yDistance = yTiles * math.pow(2, (Core.Coordinate.MAX_ZOOM - self.coordinate.zoom));
        
        # new point coordinate reflecting that distance
        coord = Core.Coordinate(round(hizoomCoord.row + yDistance),
                                round(hizoomCoord.column + xDistance),
                                hizoomCoord.zoom)

        coord = coord.zoomTo(self.coordinate.zoom)
        
        location = self.provider.coordinateLocation(coord)
        
        return location

    def draw(self, verbose=False):
        """ Draw map out to a PIL.Image and return it.
        """
        corner = Core.Point(int(self.offset.x + self.dimensions.x/2), int(self.offset.y + self.dimensions.y/2))
        
        while corner.x > 0:
            corner.x -= self.provider.tileWidth()
            self.coordinate = self.coordinate.left()
        
        while corner.y > 0:
            corner.y -= self.provider.tileHeight()
            self.coordinate = self.coordinate.up()
            
        tiles = TileQueue()
        
        rowCoord = self.coordinate.copy()
        for y in range(corner.y, self.dimensions.y, self.provider.tileHeight()):
            tileCoord = rowCoord.copy()
            for x in range(corner.x, self.dimensions.x, self.provider.tileWidth()):
                tiles.append(TileRequest(self.provider, tileCoord, Core.Point(x, y)))
                tileCoord = tileCoord.right()
            rowCoord = rowCoord.down()
        
        lock = thread.allocate_lock()
    
        for tile in tiles:
            # request all needed images
            thread.start_new_thread(tile.load, (lock, verbose))
            
        # if it takes any longer than 20 sec overhead + 10 sec per tile, give up
        due = time.time() + 20 + len(tiles) * 10
        
        while time.time() < due and tiles.pending():
            # hang around until they are loaded or we run out of time...
            time.sleep(1)
    
        mapImg = PIL.Image.new('RGB', (self.dimensions.x, self.dimensions.y))
        
        for tile in tiles:
            try:
                for img in tile.images():
                    mapImg.paste(img, (tile.offset.x, tile.offset.y), img)
            except:
                # something failed to paste, so we ignore it
                pass
        
        return mapImg

if __name__ == '__main__':
    import doctest
    doctest.testmod()
