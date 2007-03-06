import sys, math, PIL.Image, urllib, StringIO, time, optparse
from ModestMaps import Providers

def deg2rad(deg):
    return deg * math.pi / 180

def project(lat, lon):
    x = lon
    y = math.log((1 + math.sin(lat)) / (1 - math.sin(lat))) / 2
    return x / math.pi, y / math.pi
    
def locationCoord(lat, lon, zoom=0):
    x, y = project(deg2rad(lat), deg2rad(lon))
    
    row = math.pow(2, zoom) * ((1 - y) / 2)
    col = math.pow(2, zoom) * ((x + 1) / 2)
    
    return row, col, zoom
    
parser = optparse.OptionParser()

parser.add_option('-o', '--out', dest='outfile',
                  help='Write to output file')

parser.add_option('-z', '--zoom', dest='zoomlevel',
                  help='Zoom level', type='int')

parser.add_option('-b', '--bounds', dest='bounds',
                  help='Lat/long bounding box', type='float', nargs=4)

parser.add_option('-p', '--provider', dest='provider',
                  help='Map Provider', choices=Providers.ids)

(options, args) = parser.parse_args()

if __name__ == '__main__':

    provider = Providers.Provider(options.provider)
    
    #print locationCoord(85, -180, 0)
    #print locationCoord(0, 0, 0)
    #print locationCoord(-85, 180, 0)
    #sys.exit()

    zoom = options.zoomlevel
    
    #print math.pow(2, zoom)

    minRow, minCol, minZoom = map(int, map(math.floor, locationCoord(options.bounds[0], options.bounds[1], zoom)))
    maxRow, maxCol, maxZoom = map(int, map(math.ceil,  locationCoord(options.bounds[2], options.bounds[3], zoom)))
    
    rows = (maxRow - minRow)
    cols = (maxCol - minCol)
    
    print 'Allocating...', rows, 'x', cols
    destImg = PIL.Image.new('RGB', (256 * cols, 256 * rows))
    
    for row in range(minRow, maxRow):
        for col in range(minCol, maxCol):
            destY = (row - minRow) * 256
            destX = (col - minCol) * 256
        
            try:
                url = provider.url(col, row, zoom)

                print row, col, zoom, '->', url, '->', destX, destY
                
                img = PIL.Image.open(StringIO.StringIO(urllib.urlopen(url).read()))
                destImg.paste(img, (destX, destY))
                
            except Exception, e:
                print e
            
            #time.sleep(10)
            
    print 'Saving...'
    destImg.save(options.outfile)
    print options.outfile