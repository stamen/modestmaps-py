# -*-python-*-

__package__    = "wscompose/dithering.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wscompose"
__date__       = "$Date: 2008/01/04 06:23:46 $"
__copyright__  = "Copyright (c) 2007-2008 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license."

import wscompose
import Image

# DEPRECATED
# TO BE REBLESSED AS A PROPER PROVIDER

class handler (wscompose.handler) :

    def draw_map (self) :

        img = wscompose.handler.draw_map(self)
        return self.atkinson_dithering(img)
    
    #
    # http://mike.teczno.com/notes/atkinson.html
    #
    
    def atkinson_dithering(self, img) :

        img = img.convert('L')

        threshold = 128*[0] + 128*[255]

        for y in range(img.size[1]):
            for x in range(img.size[0]):

                old = img.getpixel((x, y))
                new = threshold[old]
                err = (old - new) >> 3 # divide by 8
            
                img.putpixel((x, y), new)
        
                for nxy in [(x+1, y), (x+2, y), (x-1, y+1), (x, y+1), (x+1, y+1), (x, y+2)]:
                    try:
                        img.putpixel(nxy, img.getpixel(nxy) + err)
                    except IndexError:
                        pass

        return img.convert('RGBA')
