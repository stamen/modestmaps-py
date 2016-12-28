from __future__ import print_function
"""
>>> m = Map(Microsoft.RoadProvider(), Core.Point(600, 600), Core.Coordinate(3165, 1313, 13), Core.Point(-144, -94))
>>> p = m.locationPoint(Geo.Location(37.804274, -122.262940))
>>> p
(370.752, 342.626)
>>> m.pointLocation(p)
(37.804, -122.263)

>>> c = Geo.Location(37.804274, -122.262940)
>>> z = 12
>>> d = Core.Point(800, 600)
>>> m = mapByCenterZoom(Microsoft.RoadProvider(), c, z, d)
>>> m.dimensions
(800.000, 600.000)
>>> m.coordinate
(1582.000, 656.000 @12.000)
>>> m.offset
(-235.000, -196.000)

>>> sw = Geo.Location(36.893326, -123.533554)
>>> ne = Geo.Location(38.864246, -121.208153)
>>> d = Core.Point(800, 600)
>>> m = mapByExtent(Microsoft.RoadProvider(), sw, ne, d)
>>> m.dimensions
(800.000, 600.000)
>>> m.coordinate
(98.000, 40.000 @8.000)
>>> m.offset
(-251.000, -218.000)

>>> se = Geo.Location(36.893326, -121.208153)
>>> nw = Geo.Location(38.864246, -123.533554)
>>> d = Core.Point(1600, 1200)
>>> m = mapByExtent(Microsoft.RoadProvider(), se, nw, d)
>>> m.dimensions
(1600.000, 1200.000)
>>> m.coordinate
(197.000, 81.000 @9.000)
>>> m.offset
(-246.000, -179.000)

>>> sw = Geo.Location(36.893326, -123.533554)
>>> ne = Geo.Location(38.864246, -121.208153)
>>> z = 10
>>> m = mapByExtentZoom(Microsoft.RoadProvider(), sw, ne, z)
>>> m.dimensions
(1693.000, 1818.000)
>>> m.coordinate
(395.000, 163.000 @10.000)
>>> m.offset
(-236.000, -102.000)

>>> se = Geo.Location(36.893326, -121.208153)
>>> nw = Geo.Location(38.864246, -123.533554)
>>> z = 9
>>> m = mapByExtentZoom(Microsoft.RoadProvider(), se, nw, z)
>>> m.dimensions
(846.000, 909.000)
>>> m.coordinate
(197.000, 81.000 @9.000)
>>> m.offset
(-246.000, -179.000)
"""

import os.path

__version__ = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read().strip()

import sys
import urllib
import math
import time

try:
    import httplib
    import urlparse
    import StringIO
    import thread
except ImportError:
    # Python 3
    import http.client as httplib
    import urllib.parse as urlparse
    from io import StringIO
    import _thread as thread

try:
    import Image
except ImportError:
    try:
        import PIL.Image as Image
    except ImportError:
        # you need PIL to do any actual drawing, but
        # maybe that's not what you're using MMaps for?
        Image = None

from . import Tiles
from . import Providers
from . import Core
from . import Geo
from . import Yahoo, Microsoft, BlueMarble, OpenStreetMap, CloudMade, MapQuest, Stamen
import time

# a handy list of possible providers, which isn't
# to say that you can't go writing your own.
builtinProviders = {
    'OPENSTREETMAP':    OpenStreetMap.Provider,
    'OPEN_STREET_MAP':  OpenStreetMap.Provider,
    'BLUE_MARBLE':      BlueMarble.Provider,
    'MAPQUEST_ROAD':   MapQuest.RoadProvider,
    'MAPQUEST_AERIAL':   MapQuest.AerialProvider,
    'MICROSOFT_ROAD':   Microsoft.RoadProvider,
    'MICROSOFT_AERIAL': Microsoft.AerialProvider,
    'MICROSOFT_HYBRID': Microsoft.HybridProvider,
    'YAHOO_ROAD':       Yahoo.RoadProvider,
    'YAHOO_AERIAL':     Yahoo.AerialProvider,
    'YAHOO_HYBRID':     Yahoo.HybridProvider,
    'CLOUDMADE_ORIGINAL': CloudMade.OriginalProvider,
    'CLOUDMADE_FINELINE': CloudMade.FineLineProvider,
    'CLOUDMADE_TOURIST': CloudMade.TouristProvider,
    'CLOUDMADE_FRESH':  CloudMade.FreshProvider,
    'CLOUDMADE_PALEDAWN': CloudMade.PaleDawnProvider,
    'CLOUDMADE_MIDNIGHTCOMMANDER': CloudMade.MidnightCommanderProvider,
    'STAMEN_TONER': Stamen.TonerProvider,
    'STAMEN_TERRAIN': Stamen.TerrainProvider,
    'STAMEN_WATERCOLOR': Stamen.WatercolorProvider,
    }

def mapByCenterZoom(provider, center, zoom, dimensions):
    """ Return map instance given a provider, center location, zoom value, and dimensions point.
    """
    centerCoord = provider.locationCoordinate(center).zoomTo(zoom)
    mapCoord, mapOffset = calculateMapCenter(provider, centerCoord)

    return Map(provider, dimensions, mapCoord, mapOffset)

def mapByExtent(provider, locationA, locationB, dimensions):
    """ Return map instance given a provider, two corner locations, and dimensions point.
    """
    mapCoord, mapOffset = calculateMapExtent(provider, dimensions.x, dimensions.y, locationA, locationB)

    return Map(provider, dimensions, mapCoord, mapOffset)
    
def mapByExtentZoom(provider, locationA, locationB, zoom):
    """ Return map instance given a provider, two corner locations, and zoom value.
    """
    # a coordinate per corner
    coordA = provider.locationCoordinate(locationA).zoomTo(zoom)
    coordB = provider.locationCoordinate(locationB).zoomTo(zoom)

    # precise width and height in pixels
    width = abs(coordA.column - coordB.column) * provider.tileWidth()
    height = abs(coordA.row - coordB.row) * provider.tileHeight()
    
    # nearest pixel actually
    dimensions = Core.Point(int(width), int(height))
    
    # projected center of the map
    centerCoord = Core.Coordinate((coordA.row + coordB.row) / 2,
                                  (coordA.column + coordB.column) / 2,
                                  zoom)
    
    mapCoord, mapOffset = calculateMapCenter(provider, centerCoord)

    return Map(provider, dimensions, mapCoord, mapOffset)

def calculateMapCenter(provider, centerCoord):
    """ Based on a provider and center coordinate, returns the coordinate
        of an initial tile and its point placement, relative to the map center.
    """
    # initial tile coordinate
    initTileCoord = centerCoord.container()

    # initial tile position, assuming centered tile well in grid
    initX = (initTileCoord.column - centerCoord.column) * provider.tileWidth()
    initY = (initTileCoord.row - centerCoord.row) * provider.tileHeight()
    initPoint = Core.Point(round(initX), round(initY))
    
    return initTileCoord, initPoint

def calculateMapExtent(provider, width, height, *args):
    """ Based on a provider, width & height values, and a list of locations,
        returns the coordinate of an initial tile and its point placement,
        relative to the map center.
    """
    coordinates = list(map(provider.locationCoordinate, args))
    
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
    
def printlocked(lock, *stuff):
    """
    """
    if lock.acquire():
        print(' '.join([str(thing) for thing in stuff]), file=sys.stderr)
        lock.release()

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
    
    def load(self, lock, verbose, cache, fatbits_ok, attempt=1, scale=1):
        if self.done:
            # don't bother?
            return

        urls = self.provider.getTileUrls(self.coord)
        
        if verbose:
            printlocked(lock, 'Requesting', urls, '- attempt no.', attempt, 'in thread', hex(thread.get_ident()))

        # this is the time-consuming part
        try:
            imgs = []
        
            for (scheme, netloc, path, params, query, fragment) in map(urlparse.urlparse, urls):
                if (netloc, path, query) in cache:
                    if lock.acquire():
                        img = cache[(netloc, path, query)].copy()
                        lock.release()

                    if verbose:
                        printlocked(lock, 'Found', urlparse.urlunparse(('http', netloc, path, '', query, '')), 'in cache')
            
                elif scheme in ('file', ''):
                    img = Image.open(path).convert('RGBA')
                    imgs.append(img)

                    if lock.acquire():
                        cache[(netloc, path, query)] = img
                        lock.release()
                
                elif scheme in ('http', 'https'):
                    conn = httplib.HTTPConnection(netloc)
                    conn.request('GET', path + ('?' + query).rstrip('?'), headers={'User-Agent': 'Modest Maps python branch (http://modestmaps.com)'})
                    response = conn.getresponse()
                    status = str(response.status)
                    
                    if status.startswith('2'):
                        img = Image.open(StringIO.StringIO(response.read())).convert('RGBA')
                        imgs.append(img)
    
                        if lock.acquire():
                            cache[(netloc, path, query)] = img
                            lock.release()
                    
                    elif status == '404' and fatbits_ok:
                        #
                        # We're probably never going to see this tile.
                        # Try the next lower zoom level for a pixellated output?
                        #
                        neighbor = self.coord.zoomBy(-1)
                        parent = neighbor.container()
                        
                        col_shift = 2 * (neighbor.column - parent.column)
                        row_shift = 2 * (neighbor.row - parent.row)
                        
                        # sleep for a second or two, helps prime the image cache
                        time.sleep(col_shift + row_shift/2)
                        
                        x_shift = scale * self.provider.tileWidth() * col_shift
                        y_shift = scale * self.provider.tileHeight() * row_shift
                        
                        self.offset.x -= int(x_shift)
                        self.offset.y -= int(y_shift)
                        self.coord = parent
    
                        return self.load(lock, verbose, cache, fatbits_ok, attempt+1, scale*2)

            if scale > 1:
                imgs = [img.resize((img.size[0] * scale, img.size[1] * scale)) for img in imgs]
                
        except:
            if verbose:
                printlocked(lock, 'Failed', urls, '- attempt no.', attempt, 'in thread', hex(thread.get_ident()))

            if attempt < TileRequest.MAX_ATTEMPTS:
                time.sleep(1 * attempt)
                return self.load(lock, verbose, cache, fatbits_ok, attempt+1, scale)
            else:
                imgs = [None for url in urls]

        else:
            if verbose:
                printlocked(lock, 'Received', urls, '- attempt no.', attempt, 'in thread', hex(thread.get_ident()))

        if lock.acquire():
            self.imgs = imgs
            self.done = True
            lock.release()

class TileQueue(list):
    """ List of TileRequest objects, that's sensitive to when they're loaded.
    """

    def __getslice__(self, i, j):
        """ Return a TileQueue when a list slice is called-for.
        
            Python docs say that __getslice__ is deprecated, but its
            replacement __getitem__ doesn't seem to be doing anything.
        """
        other = TileQueue()
        
        for t in range(i, j):
            if t < len(self):
                other.append(self[t])

        return other

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

    #
    
    def draw_bbox(self, bbox, zoom=16, verbose=False) :

        sw = Geo.Location(bbox[0], bbox[1])
        ne = Geo.Location(bbox[2], bbox[3])
        nw = Geo.Location(ne.lat, sw.lon)
        se = Geo.Location(sw.lat, ne.lon)
        
        TL = self.provider.locationCoordinate(nw).zoomTo(zoom)

        #

        tiles = TileQueue()

        cur_lon = sw.lon
        cur_lat = ne.lat        
        max_lon = ne.lon
        max_lat = sw.lat
        
        x_off = 0
        y_off = 0
        tile_x = 0
        tile_y = 0
        
        tileCoord = TL.copy()

        while cur_lon < max_lon :

            y_off = 0
            tile_y = 0
            
            while cur_lat > max_lat :
                
                tiles.append(TileRequest(self.provider, tileCoord, Core.Point(x_off, y_off)))
                y_off += self.provider.tileHeight()
                
                tileCoord = tileCoord.down()
                loc = self.provider.coordinateLocation(tileCoord)
                cur_lat = loc.lat

                tile_y += 1
                
            x_off += self.provider.tileWidth()            
            cur_lat = ne.lat
            
            tile_x += 1
            tileCoord = TL.copy().right(tile_x)

            loc = self.provider.coordinateLocation(tileCoord)
            cur_lon = loc.lon

        width = int(self.provider.tileWidth() * tile_x)
        height = int(self.provider.tileHeight() * tile_y)

        # Quick, look over there!

        coord, offset = calculateMapExtent(self.provider,
                                           width, height,
                                           Geo.Location(bbox[0], bbox[1]),
                                           Geo.Location(bbox[2], bbox[3]))

        self.offset = offset
        self.coordinates = coord
        self.dimensions = Core.Point(width, height)

        return self.draw()
    
    #
    
    def draw(self, verbose=False, fatbits_ok=False):
        """ Draw map out to a PIL.Image and return it.
        """
        coord = self.coordinate.copy()
        corner = Core.Point(int(self.offset.x + self.dimensions.x/2), int(self.offset.y + self.dimensions.y/2))

        while corner.x > 0:
            corner.x -= self.provider.tileWidth()
            coord = coord.left()
        
        while corner.y > 0:
            corner.y -= self.provider.tileHeight()
            coord = coord.up()
        
        tiles = TileQueue()
        
        rowCoord = coord.copy()
        for y in range(corner.y, self.dimensions.y, self.provider.tileHeight()):
            tileCoord = rowCoord.copy()
            for x in range(corner.x, self.dimensions.x, self.provider.tileWidth()):
                tiles.append(TileRequest(self.provider, tileCoord, Core.Point(x, y)))
                tileCoord = tileCoord.right()
            rowCoord = rowCoord.down()

        return self.render_tiles(tiles, self.dimensions.x, self.dimensions.y, verbose, fatbits_ok)

    #
    
    def render_tiles(self, tiles, img_width, img_height, verbose=False, fatbits_ok=False):
        
        lock = thread.allocate_lock()
        threads = 32
        cache = {}
        
        for off in range(0, len(tiles), threads):
            pool = tiles[off:(off + threads)]
            
            for tile in pool:
                # request all needed images
                thread.start_new_thread(tile.load, (lock, verbose, cache, fatbits_ok))
                
            # if it takes any longer than 20 sec overhead + 10 sec per tile, give up
            due = time.time() + 20 + len(pool) * 10
            
            while time.time() < due and pool.pending():
                # hang around until they are loaded or we run out of time...
                time.sleep(1)

        mapImg = Image.new('RGB', (img_width, img_height))
        
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
