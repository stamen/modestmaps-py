# -*-python-*-

__package__    = "wscompose/markers.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wscompose"
__date__       = "$Date: 2008/01/04 06:23:46 $"
__copyright__  = "Copyright (c) 2007-2008 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license."

import Image
import ImageDraw
import ImageFilter
import StringIO
import base64

# DANGER WILL ROBINSON : YOU ARE ABOUT TO
# ENCOUNTER CODE THAT WILL MAKE YOU WEEP.
# I KNOW. I CRY EVERY TIME I LOOK AT IT.
#
# TO DO (patches are welcome) :
#
# - clean up variable names and exposed object
#   properties - 'marker' objects defined here
#   and 'marker data' are different beasts but
#   it's really easy to get the two mixed up
#
# - add support for pycairo, if present
#
# - learn the necessary maths to generate real
#   shadows - or at least improve the cartoon
#   versions
#
# - allow the cone to be positioned on any side
#   of the canvas

class  pinwin :

    def __init__ (self, imgw=100, imgh=100, adjust_cone=0, dotr=18) :

        self.__mrk__ = None

        m = max(imgh, imgw)
        padding = m / 8

        if m <= 100 :
            padding = m / 5
            
        self.dot_radius = dotr
        self.padding = padding

        self.adjust_cone_height = adjust_cone

        # do not base cone width on cone height
        # makes for weirdness if we reposition
        # overlapping markers
        
        self.cone_height = int(imgh / 6)
        self.cone_width = int(self.cone_height / 1.4)
        
        if self.cone_width < 20 :
            self.cone_width = int(imgh * .55)

        # no big honking cones. no!
        
        if self.cone_width > (imgw * .2) :
            self.cone_width = max(int((imgw * .2)), 20)
            
        #
        
        self.cone_height = int(imgh / 6) + self.adjust_cone_height
        
        self.start_cone = int(imgw / 3)

        if self.start_cone < padding :
            self.start_cone = padding        
        
        self.mid_cone = self.start_cone + int(self.cone_width / 2)
        self.end_cone = self.start_cone + self.cone_width
        
        self.width = imgw + int(padding * 2)
        self.height = imgh + int(padding * 2) + self.cone_height + self.dot_radius
        
        self.bottom_cone = self.height - int(self.dot_radius / 2) - 5

        #
        
        self.x_offset = self.mid_cone
        self.y_offset = self.bottom_cone

        self.x_canvas = imgw
        self.y_canvas = imgh

        self.x_padding = int(self.padding / 2)
        self.y_padding = int(self.padding / 2)

        self.img_width = imgw
        self.img_height = imgh        
                                       
    # ##########################################################
    
    def fh (self) :
        return self.draw()

    # ##########################################################
    
    def draw (self, guides=False) :

        if not self.__mrk__ :

            pw = self.mk_pinwin()
            sh = self.mk_cartoon_shadow()
            al = self.mk_alpha()
            
            im = self.add_shadow(pw, sh, al)
            im = self.antialias(im)

            if guides :
                self.add_guides(im)
                
            self.__mrk__ = im
            
        return self.__mrk__

    # ##########################################################
    
    def mk_pinwin (self, fill='white') :

        coords = self.pinwin_coords()
        
        # define no bgcolour for the
        # transparency lurve
        
        im = Image.new('RGBA', (self.width, self.height))
        dr = ImageDraw.Draw(im)        
        dr.polygon(coords['frame'], fill=fill)
    
        # assume a padding of 50
        # im = Image.new('RGBA', (400, 300))
        # dr = ImageDraw.Draw(im)
        # 
        # top left
        # dr.pieslice((0, 0, 75, 75), 180, 270, outline=255)
        # 
        # bottom left
        # dr.pieslice((0, 225, 75, 300), 90, 180, outline=255)        
        # 
        # top right
        # dr.pieslice((325, 0, 400, 75), 270, 0, outline='red')
        # 
        # bottom right
        # dr.pieslice((325, 225, 400, 300), 0, 90, outline=255)        
        
        x1 = 0
        y1 = 0
        x2 = self.padding + (self.padding / 2)
        y2 = self.padding + (self.padding / 2)
        
        dr.pieslice((x1, y1, x2, y2), 180, 270, fill=fill)

        x1 = 0
        y1 = coords['endy'] - (self.padding + (self.padding / 2))
        x2 = self.padding + (self.padding / 2)
        y2 = coords['endy']
        
        dr.pieslice((x1, y1, x2, y2), 90, 180, fill=fill)

        x1 = coords['endx'] - (self.padding + (self.padding / 2))
        y1 = 0
        x2 = coords['endx']
        y2 = self.padding + (self.padding / 2)

        dr.pieslice((x1, y1, x2, y2), 270, 0, fill=fill)

        x1 = coords['endx'] - (self.padding + (self.padding / 2))
        y1 = coords['endy'] - (self.padding + (self.padding / 2))
        x2 = coords['endx']
        y2 = coords['endy']

        dr.pieslice((x1, y1, x2, y2), 0, 90, fill=fill)

        return im

    # ##########################################################

    def pinwin_coords (self) :

        #
        #    startx, starty
        #
        #      nwa ------------- nea
        #      /                   \ 
        #    nwb                   neb   
        #    |                       |
        #    |                       |
        #    swb                   seb
        #      \   cna   cnc       /
        #      swa --/ | /------ sea
        #             |
        #            |
        #           |
        #          |
        #         cnb
        #
        #                  endx, endy
        #
        # The rounded corners get bolted on after the
        # fact - this is dumb and if I can ever find
        # docs/examples for PIL's ImagePath stuff then
        # I will use that instead...
        
        startx = self.padding - (self.padding / 4)
        starty = 0

        endx = self.img_width + self.padding
        endy = self.img_height + self.padding
        
        nwa_x = startx
        nwa_y = starty

        nea_x = endx - startx
        nea_y = starty
        neb_x = endx
        neb_y = startx

        seb_x = endx
        seb_y = endy - startx
        sea_x = endx - startx
        sea_y = endy

        cnc_x = self.start_cone
        cnc_y = endy
        cnb_x = self.mid_cone
        cnb_y = self.bottom_cone
        cna_x = self.end_cone
        cna_y = endy
        
        swa_x = startx
        swa_y = endy
        swb_x = 0
        swb_y = endy - startx

        nwb_x = 0
        nwb_y = startx

        frame = [(nwa_x, nwa_y),
                  (nea_x, nea_y), (neb_x, neb_y),
                  (seb_x, seb_y), (sea_x, sea_y),
                  (cnc_x, cnc_y), (cnb_x, cnb_y),
                  (cna_x, cna_y), (swa_x, swa_y),
                  (swb_x, swb_y), (nwb_x, nwb_y),
                  (nwa_x, nwa_y)]
        
        coords = {
            'startx' : startx,
            'starty' : starty,
            'endx' : endx,
            'endy' : endy,
            'frame' : frame
            }

        return coords
    
    # ##########################################################

    def cartoon_shadow_coords (self) :
        
        startx = self.padding  - (self.padding / 4)
        starty = 0
        
        endx = startx + self.img_width - (self.padding / 4)
        endy = starty + self.img_height + (self.padding / 2)

        # All of these numbers could use some
        # loving and thought - I just eyeballed
        # it really ... and the part where there
        # are some arbitrary offsets thrown in is
        # just that
        
        w = endx - startx
        h = endy
        
        xoff_top = int(w * .3)
        yoff_top = int(h * .75)

        xoff_bottom = int(w * .1)
        yoff_bottom = int(h * .2)

        yoff_bleed = .8
        
        # see the diagram in pinwin_coords if you're curious...
        
        nwa_x = startx + int(xoff_top * 1.05)
        nwa_y = starty + yoff_top

        nea_x = endx + xoff_top - int(startx / 1.5)
        nea_y = starty + yoff_top
        neb_x = endx + xoff_top
        neb_y = starty + int(yoff_top * 1.05)

        seb_x = endx + int(xoff_bottom * 2.25)
        seb_y = endy + int(yoff_bottom * .6)
        sea_x = endx + xoff_bottom - 15
        sea_y = endy + yoff_bottom

        cnc_x = self.end_cone + xoff_bottom + int(self.cone_width / 2.25)
        cnc_y = endy + yoff_bottom
        cnb_x = self.mid_cone
        cnb_y = self.bottom_cone
        cna_x = self.start_cone + xoff_bottom + int(self.cone_width / 2.25)
        cna_y = endy + yoff_bottom
        
        swa_x = startx + int(xoff_bottom * 2)
        swa_y = endy + yoff_bottom
        swb_x = startx + int(xoff_bottom * 1.25)
        swb_y = endy + (yoff_bottom * yoff_bleed)

        nwb_x = startx + int(xoff_top * .95)
        nwb_y = starty + int(yoff_top * 1.05)

        #
        
        frame = [(nwa_x, nwa_y),
                  (nea_x, nea_y), (neb_x, neb_y),
                  (seb_x, seb_y), (sea_x, sea_y),
                  (cnc_x, cnc_y), (cnb_x, cnb_y),
                  (cna_x, cna_y), (swa_x, swa_y),
                  (swb_x, swb_y), (nwb_x, nwb_y),
                  (nwa_x, nwa_y)]
        
        coords = {
            'startx' : startx,
            'starty' : starty,
            'endx' : endx,
            'endy' : endy,
            'xoff_top' : xoff_top,
            'xoff_bottom' : xoff_bottom,  
            'yoff_top' : yoff_top,
            'yoff_bottom' : yoff_bottom,
            'yoff_bleed' : yoff_bleed,
            'frame' : frame
            }

        return coords

    # ##########################################################
    
    def mk_cartoon_shadow (self, fill='black', blurry=True) :

        coords = self.cartoon_shadow_coords()

        #

        w = coords['endx'] + coords['xoff_top'] + 3
        h = self.height
        
        im = Image.new('RGBA', (w, h))
        dr = ImageDraw.Draw(im)

        dr.polygon(coords['frame'], fill=fill)

        # bottom left - this one has gaps but we don't
        # care and rely on the blurring to make them vanish!
        
        x1 = (coords['startx'] + int(coords['xoff_bottom'] * 1.25))
        y1 = (coords['endy'] + int(coords['yoff_bottom'] * coords['yoff_bleed']))
        x2 = (coords['startx'] + int(coords['xoff_bottom'] * 2))
        y2 = (coords['endy'] + coords['yoff_bottom'])
        c = (x1, y1, x2, y2)

        center_x = x2
        center_y = y1
        x_diff = x2 - x1
        y_diff = y2 - y1
        
        x1 = center_x - x_diff
        y1 = center_y - int(y_diff/3)
        x2 = center_x + int(x_diff * 2)
        y2 = center_y + y_diff

        dr.pieslice((x1, y1, x2, y2), 90, 180, fill=fill)                

        # bottom right - this one has gaps but we don't
        # care and rely on the blurring to make them vanish!

        x1 = (coords['endx'] + coords['xoff_bottom'])
        y1 = (coords['endy'] + coords['yoff_bottom'])
        x2 = (coords['endx'] + int(coords['xoff_bottom'] * 2.25))
        y2 = (coords['endy'] + int(coords['yoff_bottom'] * .6))

        c = (x1, y1, x2, y2)
        
        center_x = x1
        center_y = y2
        x_diff = x2 - x1
        y_diff = y1 - y2

        x1 = center_x - int(x_diff * 2.5)
        y1 = center_y - int(y_diff * 1.4)
        x2 = center_x + x_diff
        y2 = center_y + y_diff

        dr.pieslice((x1, y1, x2, y2), 0, 90, fill=fill)                

        # top right

        x1 = ((coords['endx'] + coords['xoff_top'] - int(coords['startx'] / 2)))
        y1 = (coords['starty'] + coords['yoff_top'])
        x2 = (coords['endx'] + coords['xoff_top'])
        y2 = (coords['starty'] + int(coords['yoff_top'] * 1.05))

        c = (x1, y1, x2, y2)
        
        center_x = x1
        center_y = y2
        x_diff = x2 - x1
        y_diff = y2 - y1

        x1 = center_x - int(x_diff * 2.75)
        y1 = center_y - y_diff
        x2 = center_x + x_diff
        y2 = center_y + y_diff

        dr.pieslice((x1, y1, x2, y2), 270, 0, fill=fill)

        if not blurry :
            return im
        
        return self.mk_shadow_blurry(im)

    # ##########################################################
    
    def mk_shadow_blurry (self, sh, iterations=10) :

        for i in range(1, iterations) :
            sh = sh.filter(ImageFilter.BLUR)

        return sh
    
    # ##########################################################
    
    def mk_perspective_shadow (self, img, corners) :

        #
        # I R DUHM ... why won't someone explain to me the math behind : 
        #
        # http://www.cycloloco.com/shadowmaker/
        # http://www.css.taylor.edu/~btoll/s99/424/res/mtu/Notes/geometry/geo-tran.htm
        # inkscape's extensions/perspective.py
        #
        # so that I can do this :
        #
        # im.transform(size, PERSPECTIVE, data)
        #

        """
            
        Returns a new surface containing the image reshaped to fit inside the quadrilateral defined by the given vertices (top-left, top-right, bottom-right, bottom-left).
        
        For the sake of my sanity, we're assuming that the left and right sides, post-transform, will be straight vertical lines. If you intend them to be otherwise, I shall punch you in the cock. Also assumed is that the smaller end doesn't extend above or below the longer end (though I'm not sure that it doing so would actually be a problem).
        """
        
        tl, tr, br, bl = corners
        sourceSize = img.size
        newSize = (max(tr[0], br[0]), max(bl[1], br[1]))
        
        a = float(sourceSize[0] * (br[1] - tr[1])) / \
            (newSize[0] * (bl[1] - tl[1]))
        b = 0
        c = 0
        d = float(sourceSize[1] * (tl[1] - tr[1])) / \
            (newSize[0] * (bl[1] - tl[1]))
        e = float(sourceSize[1]) / \
            (bl[1] - tl[1])
        f = float(-(sourceSize[1] * tl[1])) / \
            (bl[1] - tl[1])
        g = float(tl[1] - tr[1] + br[1] - bl[1]) / \
            (newSize[0] * (bl[1] - tl[1]))
        h = 0
        vals = [a, b, c, d, e, f, g, h]
        
        return img.transform (newSize, Image.PERSPECTIVE, vals, Image.BILINEAR)
           

    # ##########################################################

    def mk_alpha (self) :

        pw = self.mk_pinwin('white')
        sh = self.mk_cartoon_shadow('grey')

        h = pw.size[1]
        w = max(pw.size[0], sh.size[0])
        
        im = Image.new('L', (w, h))
        dr = ImageDraw.Draw(im)

        # add the shadow
        
        im.paste(sh, (0, 0), sh)
        
        #  add the dot
        
        offset = self.dot_radius / 2
        x = self.start_cone + ((self.end_cone - self.start_cone) / 2)
        y = self.height - offset

        x1 = x - offset
        y1 = y - offset - 5
        x2 = x + offset
        y2 = y + offset - 5
        
        dr.ellipse((x1 + 1 , y1 + 2, x2 + 1, y2 + 2), fill='white')        
        dr.ellipse((x1, y1, x2, y2), fill='white')

        # add the pinwin

        # note the offset; required so that the top and left
        # side outlines of the pinwin don't obscured by the
        # alpha channel; this also affects the values of dx
        # and dy in plotting.draw_marker
        
        im.paste(pw, (1,1), pw)

        return im

    # ##########################################################
    
    def add_shadow (self, pw, sh, al) :

        h = pw.size[1]
        w = max(pw.size[0], sh.size[0])

        im = Image.new('RGBA', (w, h))
        dr = ImageDraw.Draw(im)

        # add the shadow

        im.paste(sh, (0,0), sh)
        
        #  add the dot
        
        offset = self.dot_radius / 2
        x = self.start_cone + ((self.end_cone - self.start_cone) / 2)
        y = self.height - offset

        x1 = x - offset
        y1 = y - offset - 5
        x2 = x + offset
        y2 = y + offset - 5

        # flickr pink
        pink = (255, 0, 132)
        grey = (42, 42, 42)
        
        dr.ellipse((x1 + 1 , y1 + 2, x2 + 1, y2 + 2), fill=grey)        
        dr.ellipse((x1, y1, x2, y2), fill=pink)

        # add the pinwin

        # note the offset; required so that the top and left
        # side outlines of the pinwin don't obscured by the
        # alpha channel; this also affects the values of dx
        # and dy in plotting.draw_marker
        
        im.paste(pw, (1,1), pw) 

        im.putalpha(al)
        return im

    # ##########################################################
    
    def add_guides (self, im) :

        dr = ImageDraw.Draw(im)
        
        startx = self.padding - (self.padding / 2)
        starty = self.padding - (self.padding / 2)
        
        dr.line((startx, starty, startx, int(starty + self.img_height)), fill='red')

        startx = self.padding - (self.padding / 2)
        starty = self.padding - (self.padding / 2)
        
        dr.line((startx, starty, int(startx + self.img_width), starty), fill='red')
        # return im

    # ##########################################################

    def antialias (self, im, scale=4) :
        sz = im.size
        im = im.resize((sz[0] * scale, im.size[1] * scale),  Image.NEAREST)
        return im.resize(sz, Image.ANTIALIAS)

    # ##########################################################

if __name__ == '__main__' :

    w = 400
    h = 100
    
    pw = pinwin(w, h, 15)
    im = pw.mk_pinwin()
    im = pw.mk_perspective_shadow(im, ((10,100), (10,10), (500,500), (500,200)))
    # im.save("/home/asc/Desktop/mrk.png")
    im.show()
