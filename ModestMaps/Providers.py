import random, Tiles

ids = ('MICROSOFT_ROAD', 'MICROSOFT_AERIAL', 'MICROSOFT_HYBRID',
       'GOOGLE_ROAD',    'GOOGLE_AERIAL',    'GOOGLE_HYBRID',
       'YAHOO_ROAD',     'YAHOO_AERIAL',     'YAHOO_HYBRID',
       'BLUE_MARBLE',
       'OPEN_STREET_MAP')

class Provider:
    """
    """

    def __init__(self, id):
        if id not in ids:
            raise KeyError("Unknown provider: '%s'" % id)
            
        self.id = id
        
    def url(self, column, row, zoom):
        """ Retrieve a tile URL for a given column, row, zoom.
        """
        if self.id == 'MICROSOFT_ROAD':
            return 'http://r%d.ortho.tiles.virtualearth.net/tiles/r%s.png?g=45' % (random.randint(0,3), Tiles.toMicrosoft(column, row, zoom))

        if self.id == 'MICROSOFT_HYBRID':
            return 'http://h%d.ortho.tiles.virtualearth.net/tiles/h%s.jpeg?g=45' % (random.randint(0,3), Tiles.toMicrosoft(column, row, zoom))

        if self.id == 'MICROSOFT_AERIAL':
            return 'http://a%d.ortho.tiles.virtualearth.net/tiles/a%s.jpeg?g=45' % (random.randint(0,3), Tiles.toMicrosoft(column, row, zoom))
            
        else:
            raise NotImplementedError("Unimplemented provider: '%s'" % self.id)
