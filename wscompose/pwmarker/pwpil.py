__package__    = "pwmarker/pwpil.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/24 05:52:38 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import math

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

class PILMarker :

    #
    
    def p__dot (self, ctx='pinwin', dr=None) :
    
        # dr should never be None, it's just a
        # hack to make python stop whinging...
        
        x = self.pt_x + 1
        y = self.pt_y + 1
        
        x1 = x - self.dot_r
        y1 = y - self.dot_r
        x2 = x + self.dot_r
        y2 = y + self.dot_r

        if ctx.startswith('mask-') :
            sh_c = (255, 255, 255)
            dot_c = (255, 255, 255)
        else :
            sh_c = (42, 42, 42)            
            dot_c = (255, 0, 132)

	# mock shadow
        dr.ellipse((x1 + 1 , y1 + 2, x2 + 1, y2 + 2), fill=sh_c)        

	# the dot
        dr.ellipse((x1, y1, x2, y2), fill=dot_c)

        # no donut hole for PIL

    # 
    
    def p__pinwin(self, anchor='bottom', dot_ctx='pinwin', fill='white') :

        (w, h) = self.calculate_dimensions(anchor)

        # to prevent the de-facto border (artifacting)
        # from being cropped when a pinwin is rendered
        # without its shadow
        
        w += 1
        
        im = PIL.Image.new('RGBA', (w, h))
        
        coords = self.p__coords()
        return self.p__draw_pinwin(im, coords, dot_ctx, fill)
        
    #

    def p__draw_pinwin (self, im, coords, dot_ctx='pinwin', fill='white') :

        dr = PIL.ImageDraw.Draw(im)
        
        if self.add_dot and (dot_ctx != 'shadow' and dot_ctx != 'mask-shadow') :
            self.dot(dot_ctx, dr)

        dr.polygon(coords, fill=fill)

        # top left
        
        x1 = self.offset
        y1 = self.offset
        x2 = self.offset + self.padding * 2
        y2 = self.offset + self.padding * 2
        
        dr.pieslice((x1, y1, x2, y2), 180, 270, fill=fill)

        # bottom left
        
        x1 = self.offset
        y1 = self.offset + self.img_h 
        x2 = self.offset + self.padding * 2
        y2 = self.offset + (self.padding * 2) + self.img_h 
        
        dr.pieslice((x1, y1, x2, y2), 90, 180, fill=fill)

        # top right
        
        x1 = self.offset + self.img_w
        y1 = self.offset
        x2 = self.offset + self.img_w + (self.padding * 2)
        y2 = self.offset + (self.padding * 2)

        dr.pieslice((x1, y1, x2, y2), 270, 0, fill=fill)

        # bottom right
        
        x1 = self.offset + self.img_w
        y1 = self.offset + self.img_h
        x2 = self.offset + self.img_w + (self.padding * 2)
        y2 = self.offset + self.img_h + (self.padding * 2)

        dr.pieslice((x1, y1, x2, y2), 0, 90, fill=fill)
        return im
        
    #
    
    def p__shadow (self, anchor, dot_ctx, fill='black') :
        sh = self.p__pinwin(anchor, dot_ctx, fill)
        return self.tilt(sh, self.blurry_shadows)

    #
    
    def p__cartoon_shadow (self, anchor, dot_ctx, fill='black') :

        # make the canvas

        w = self.offset + self.img_w + (self.padding * 2)
        h = self.offset + self.img_h + (self.padding * 2)
        
        cnv = PIL.Image.new('RGBA', (w, h))
        coords = self.p__cartoon_shadow_coords()

        blur = False
        
        cnv = self.p__draw_pinwin(cnv, coords, dot_ctx, fill)
        cnv = self.tilt(cnv, blur)    
        
        coords = self.calculate_cartoon_anchor_coords(cnv)

        (w, h, sh_offset) = coords[0]
        (sha_left, cnv_h) = coords[1]
        (bottom_x, bottom_y) = coords[2]
        (sha_right, cnv_h) = coords[3]
                
        sh = PIL.Image.new('RGBA', (w, h))
        sh.paste(cnv, (sh_offset, 0), cnv)
        
        dr = PIL.ImageDraw.Draw(sh)
                
        anchor = [
            (sha_left, cnv_h),
            (bottom_x, bottom_y),        
            (sha_right, cnv_h),
            (sha_left, cnv_h),            
            ]

        dr.polygon(anchor, fill=fill)
        
        # dot

        self.dot('shadow', dr)
    
        # blur!

        if not self.blurry_shadows :
            return sh
        
        return self.p__blur(sh)
    
    #

    def p__coords (self) :

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
        
        nwa_x = self.offset + self.padding
        nwa_y = self.offset

        nea_x = self.offset + self.padding + self.img_w
        nea_y = self.offset

        neb_x = self.offset + self.img_w + (self.padding * 2)
        neb_y = self.offset + self.padding

        seb_x = self.offset + self.img_w + (self.padding * 2)
        seb_y = self.offset + self.img_h + self.padding

        sea_x = self.offset + self.img_w + self.padding
        sea_y = self.offset + self.img_h + (self.padding * 2)

        cnc_x = self.offset + self.offset_cone + int(self.anchor_w * .5)
        cnc_y = self.offset + self.img_h + (self.padding * 2)

        cnb_x = self.offset + self.offset_cone
        cnb_y = self.offset + self.canvas_h

        cna_x = self.offset + self.offset_cone - int(self.anchor_w * .5)
        cna_y = self.offset + self.img_h + (self.padding * 2)
        
        swa_x = self.offset + self.padding
        swa_y = self.offset + self.img_h + (self.padding * 2)

        swb_x = self.offset
        swb_y = self.offset + self.img_h + self.padding

        nwb_x = self.offset
        nwb_y = self.offset + self.padding

        frame = [(nwa_x, nwa_y),
                  (nea_x, nea_y), (neb_x, neb_y),
                  (seb_x, seb_y), (sea_x, sea_y),
                  (cnc_x, cnc_y), (cnb_x, cnb_y),
                  (cna_x, cna_y), (swa_x, swa_y),
                  (swb_x, swb_y), (nwb_x, nwb_y),
                  (nwa_x, nwa_y)]

        return frame

    #
    
    def p__cartoon_shadow_coords (self) :
        
        nwa_x = self.offset + self.padding
        nwa_y = self.offset

        nea_x = self.offset + self.padding + self.img_w
        nea_y = self.offset

        neb_x = self.offset + self.img_w + (self.padding * 2)
        neb_y = self.offset + self.padding

        seb_x = self.offset + self.img_w + (self.padding * 2)
        seb_y = self.offset + self.img_h + self.padding

        sea_x = self.offset + self.img_w + self.padding
        sea_y = self.offset + self.img_h + (self.padding * 2)
        
        swa_x = self.offset + self.padding
        swa_y = self.offset + self.img_h + (self.padding * 2)

        swb_x = self.offset
        swb_y = self.offset + self.img_h + self.padding

        nwb_x = self.offset
        nwb_y = self.offset + self.padding

        frame = [(nwa_x, nwa_y),
                 (nea_x, nea_y),
                 (neb_x, neb_y),
                 (seb_x, seb_y),
                 (sea_x, sea_y),
                 (swa_x, swa_y),                 
                 (swb_x, swb_y),
                 (nwb_x, nwb_y),
                 (nwa_x, nwa_y)]

        return frame
    
    #
    
    def p__tilt(self, pil_im, blur=True) :

        # foo is to remind me that math is hard...
        
        foo = 3.75
        
        (iw, ih) = pil_im.size

        iw2 = int(float(ih) * .45) + iw
        ih2 = int(ih / foo)

        bar = int(float(ih2) * 1.6)

        a = 1
        b = math.tan(45)
        c = -bar
        d = 0
        e = foo
        f = 0
        g = 0
        h = 0
        
        data = (a, b, c, d, e, f, g, h)

        return pil_im.transform ((iw2,ih2), PIL.Image.PERSPECTIVE, data, PIL.Image.BILINEAR)

    #
    
    def p__blur(self, pil_im, iterations=5) :

        (w, h) = pil_im.size

        # ensure some empty padding so the blurring
        # doesn't create butt ugly lines at the top
        # and bottom
        
        h+= 20
        
        im = PIL.Image.new('RGBA', (w, h))
        dr = PIL.ImageDraw.Draw(im)

        im.paste(pil_im, (0, 10), pil_im)
        
        for i in range(1, iterations) :
            im = im.filter(PIL.ImageFilter.BLUR)

        return im    

    #

    def p__antialias(self, im) :

        scale = 4
        sz = im.size
        im = im.resize((sz[0] * scale, sz[1] * scale),  PIL.Image.NEAREST)
        im = im.resize(sz, PIL.Image.ANTIALIAS)

        return im
