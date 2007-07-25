import sys, math, optparse, ModestMaps

def parseWidthHeight(option, opt, values, parser):
    if values[0] > 0 and values[1] > 0:
        parser.width = values[0]
        parser.height = values[1]
        
    else:
        raise optparse.OptionValueError('Image dimensions must be positive (got: width %d, height %d)' % values)

def assertWidthHeight(parser):
    try:
        parser.width, parser.height
    except AttributeError:
        raise optparse.OptionValueError('Image dimensions must be provided, e.g.: --dimensions <width> <height>')

def parseProvider(option, opt, value, parser):
    if value == 'MICROSOFT_ROAD':
        parser.provider = ModestMaps.Microsoft.RoadProvider()
        
    elif value == 'MICROSOFT_AERIAL':
        parser.provider = ModestMaps.Microsoft.AerialProvider()
        
    elif value == 'MICROSOFT_HYBRID':
        parser.provider = ModestMaps.Microsoft.HybridProvider()
        
    elif value == 'GOOGLE_ROAD':
        parser.provider = ModestMaps.Google.RoadProvider()
        
    elif value == 'GOOGLE_AERIAL':
        parser.provider = ModestMaps.Google.AerialProvider()
        
    elif value == 'GOOGLE_HYBRID':
        parser.provider = ModestMaps.Google.HybridProvider()
        
    elif value == 'YAHOO_ROAD':
        parser.provider = ModestMaps.Yahoo.RoadProvider()
        
    elif value == 'YAHOO_AERIAL':
        parser.provider = ModestMaps.Yahoo.AerialProvider()
        
    elif value == 'YAHOO_HYBRID':
        parser.provider = ModestMaps.Yahoo.HybridProvider()
        
    else:
        raise optparse.OptionValueError('Provider must be in eligible list (got: "%s")' % value)

def assertProvider(parser):
    try:
        parser.provider
    except AttributeError:
        raise optparse.OptionValueError('Provider must be provided, e.g.: --provider <name>')

def parseCenterZoom(option, opt, values, parser):
    assertProvider(parser)

    coordinate = parser.provider.locationCoordinate(ModestMaps.Geo.Location(values[0], values[1])).zoomTo(values[2])
    coordPoint = ModestMaps.calculateMapCenter(parser.provider, coordinate)
    parser.coord, parser.offset = coordPoint

def parseExtent(option, opt, values, parser):
    assertWidthHeight(parser)
    assertProvider(parser)

    coordPoint = ModestMaps.calculateMapExtent(parser.provider,
                                               parser.width, parser.height,
                                               ModestMaps.Geo.Location(values[0], values[1]),
                                               ModestMaps.Geo.Location(values[2], values[3]))
    parser.coord, parser.offset = coordPoint

parser = optparse.OptionParser(usage="""compose.py [options]

Map provider and output image dimensions MUST be specified before extent
or center/zoom. Multiple extents and center/zooms may be specified, but
only the last will be used.""")

parser.add_option('-v', '--verbose', dest='verbose',
                  help='Make a bunch of noise',
                  action='store_true')

parser.add_option('-o', '--out', dest='outfile',
                  help='Write to output file')

parser.add_option('-c', '--center', dest='centerzoom', nargs=3,
                  help='Center (lat, lon) and zoom level', type='float',
                  action='callback', callback=parseCenterZoom)

parser.add_option('-e', '--extent', dest='extent', nargs=4,
                  help='Geographical extent (lat, lon pair)', type='float',
                  action='callback', callback=parseExtent)

parser.add_option('-p', '--provider', dest='provider',
                  type='string', help='Map Provider, one of: MICROSOFT_ROAD, MICROSOFT_AERIAL, MICROSOFT_HYBRID, GOOGLE_ROAD, GOOGLE_AERIAL, GOOGLE_HYBRID, YAHOO_ROAD, YAHOO_AERIAL, YAHOO_HYBRID',
                  action='callback', callback=parseProvider)

parser.add_option('-d', '--dimensions', dest='dimensions', nargs=2,
                  help='Pixel dimensions (width, height) of resulting image', type='int',
                  action='callback', callback=parseWidthHeight)

if __name__ == '__main__':

    (options, args) = parser.parse_args()

    if options.verbose:
        print parser.coord, parser.offset, '->', options.outfile, (parser.width, parser.height)

    dim = ModestMaps.Core.Point(parser.width, parser.height)
    map = ModestMaps.Map(parser.provider, dim, parser.coord, parser.offset)

    map.draw(options.verbose).save(options.outfile or sys.stdout)
