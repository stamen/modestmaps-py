import math

import Tiles
import Providers
import Core
import Geo
import Microsoft

TILE_WIDTH = 256
TILE_HEIGHT = 256

def calculateMapCenter(centerCoord):
    """ Based on a center coordinate, returns the coordinate
        of an initial tile and it's point placement, relative to
        the map center.
    """

    # initial tile coordinate
    initTileCoord = Core.Coordinate(math.floor(centerCoord.row), math.floor(centerCoord.column), math.floor(centerCoord.zoom))

    # initial tile position, assuming centered tile well in grid
    initX = (initTileCoord.column - centerCoord.column) * TILE_WIDTH
    initY = (initTileCoord.row - centerCoord.row) * TILE_HEIGHT
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
    hFactor = (BR.column - TL.column) / (width / TILE_WIDTH)

    # multiplication factor expressed as base-2 logarithm, for zoom difference
    hZoomDiff = math.log(hFactor) / math.log(2)
        
    # possible horizontal zoom to fit geographical extent in map width
    hPossibleZoom = TL.zoom - math.ceil(hZoomDiff)
        
    # multiplication factor between vertical span and map height
    vFactor = (BR.row - TL.row) / (height / TILE_HEIGHT)
        
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
    
    return calculateMapCenter(centerCoord)
