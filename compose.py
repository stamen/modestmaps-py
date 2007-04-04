import sys, math, PIL.Image, urllib, StringIO, optparse, thread, ModestMaps, time

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
    coordPoint = ModestMaps.calculateMapCenter(coordinate)
    parser.coord, parser.point = coordPoint

def parseExtent(option, opt, values, parser):
    assertWidthHeight(parser)
    assertProvider(parser)

    coordPoint = ModestMaps.calculateMapExtent(parser.provider,
                                               parser.width, parser.height,
                                               ModestMaps.Geo.Location(values[0], values[1]),
                                               ModestMaps.Geo.Location(values[2], values[3]))
    parser.coord, parser.point = coordPoint
    
class RequestJob:
    def __init__(self, provider, coord, point):
        self.done = False
        self.provider = provider
        self.coord = coord
        self.point = point
        
    def do(self, lock, verbose):
        if self.done:
            # don't bother?
            return

        url = self.provider.getTileUrl(self.coord)

        if verbose:
            print 'Requesting', url, 'in thread', thread.get_ident()

        # this is the time-consuming part
        try:
            img = PIL.Image.open(StringIO.StringIO(urllib.urlopen(url).read()))

        except:
            print 'Failed', url, 'in thread', thread.get_ident()
            
        else:
            if lock.acquire():
                if verbose:
                    print 'Received', url, 'in thread', thread.get_ident()
    
                self.img = img
                self.done = True
                lock.release()

class RequestQueue(list):
    """ List of RequestJob objects, that's sensitive to when they're done.
    """

    def pending(self):
        """ True if any contained job is still pending.
        """
        remaining = [job for job in self if not job.done]
        return len(remaining) > 0

parser = optparse.OptionParser()

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
                  help='Map Provider', type='string',
                  action='callback', callback=parseProvider)

parser.add_option('-d', '--dimensions', dest='dimensions', nargs=2,
                  help='Pixel dimensions (width, height) of resulting image', type='int',
                  action='callback', callback=parseWidthHeight)

(options, args) = parser.parse_args()

if __name__ == '__main__':
    if options.verbose:
        print parser.coord, parser.point, '->', options.outfile, (parser.width, parser.height)
    
    corner = ModestMaps.Core.Point(int(parser.point.x + parser.width / 2), int(parser.point.y + parser.height / 2))
    
    while corner.x > 0:
        corner.x -= ModestMaps.TILE_WIDTH
        parser.coord = parser.coord.left()
    
    while corner.y > 0:
        corner.y -= ModestMaps.TILE_HEIGHT
        parser.coord = parser.coord.up()
        
    jobs = RequestQueue()
    
    rowCoord = parser.coord.copy()
    for y in range(corner.y, parser.height, ModestMaps.TILE_HEIGHT):
        tileCoord = rowCoord.copy()
        for x in range(corner.x, parser.width, ModestMaps.TILE_WIDTH):
            jobs.append(RequestJob(parser.provider, tileCoord, ModestMaps.Core.Point(x, y)))
            tileCoord = tileCoord.right()
        rowCoord = rowCoord.down()
    
    lock = thread.allocate_lock()

    for job in jobs:
        # request all needed images
        thread.start_new_thread(job.do, (lock, options.verbose))
        
    # if it takes any longer than 20 sec overhead + 10 sec per job, give up
    due = time.time() + 20 + len(jobs) * 10
    
    while time.time() < due and jobs.pending():
        # hang around until they are done or we run out of time...
        time.sleep(1)

    mapImg = PIL.Image.new('RGB', (parser.width, parser.height))
    
    for job in jobs:
        try:
            mapImg.paste(job.img, (job.point.x, job.point.y))
        except:
            # something failed to paste, so we ignore it
            pass
    
    mapImg.save(options.outfile)
