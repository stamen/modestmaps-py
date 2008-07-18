__package__    = "pwmarker/pwpil.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/18 05:54:33 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import math

import Image
import ImageDraw
import ImageFilter

class PILMarker :

    def draw (self, anchor='bottom') :

        pw = self.generate_pinwin(anchor)
        sh = self.generate_shadow(anchor)
        sh = self.position_shadow(pw, sh)
        
        for ctx in self.rendered.keys() :
            mask = self.generate_mask(anchor, ctx)
        
            if ctx == 'pinwin' :
                im = self.render_pinwin(pw, mask)
            elif ctx == 'shadow' :
                im = self.render_shadow(pw, sh, mask)        
            else :
                im = self.render_all(pw, sh, mask)   

            self.rendered[ctx] = self.__p_antialias(im)
            
    #
    
    def generate_pinwin (self, anchor='bottom', c='white', dot_ctx='pinwin') :

        key = "%s-%s-%s" % (anchor, c, dot_ctx)

        if self.pinwin_cache.has_key(key) :
            return self.pinwin_cache[key]
    
        pw = self.__p_pinwin(anchor, c, dot_ctx)

        self.pinwin_cache[key] = pw        
        return pw 
    #
    
    def generate_shadow (self, anchor='bottom', c='black', dot_ctx='shadow') :

        key = "%s-%s-%s" % (anchor, c, dot_ctx)

        if self.cartoon_shadows :
            key += "-cartoon"

        if self.shadow_cache.has_key(key) :
            return self.shadow_cache[key]

        if self.cartoon_shadows :
            sh = self.__p_cartoon_shadow(anchor, c, dot_ctx)
        else :
            sh = self.__p_shadow(anchor, c, dot_ctx)            

        self.shadow_cache[key] = sh        
        return sh

    #

    def generate_mask (self, anchor, ctx='all') :
        return self.__p_mask(anchor, ctx)
        
    #

    def tilt(self, pil_im, blur=True):

        sh = self.__p_tilt(pil_im, blur)

        if blur == True :
            sh = self.blur(sh)

        return sh

    #
    
    def blur(self, pil_im) :
        return self.__p_blur(pil_im)

    #

    def dot (self, ctx='pinwin', dr=None) :

        # dr should never be None, it's just a
        # hack to make python stop whinging...
        
        x = self.pt_x
        y = self.pt_y
        
        x1 = x - self.dot_r
        y1 = y - self.dot_r
        x2 = x + self.dot_r
        y2 = y + self.dot_r

        if ctx == 'mask' :
            sh_c = (255, 255, 255)
            dot_c = (255, 255, 255)
        elif ctx == 'shadow' :
            sh_c = (0, 0, 0)
            dot_c = (0, 0, 0)
        else :
            sh_c = (42, 42, 42)            
            dot_c = (255, 0, 132)

        dr.ellipse((x1 + 1 , y1 + 2, x2 + 1, y2 + 2), fill=sh_c)        
        dr.ellipse((x1, y1, x2, y2), fill=dot_c)

        if ctx=='pinwin' :

            x1 = x - 1
            y1 = y - 1
            x2 = x + 1
            y2 = y + 1
            
            dr.ellipse((x1, y1, x2, y2), fill='white')   
            
    # 
    
    def __p_pinwin(self, anchor='bottom', fill='white', dot_ctx='pinwin') :

        (w, h) = self.calculate_dimensions(anchor)

        # to prevent the de-facto border (artifacting)
        # from being cropped when a pinwin is rendered
        # without its shadow
        
        w += 1
        
        im = Image.new('RGBA', (w, h))
        
        coords = self.__p_coords()
        return self.__p_draw_pinwin(im, coords, fill, dot_ctx)
        
    #

    def __p_draw_pinwin (self, im, coords, fill='white', dot_ctx='pinwin') :

        dr = ImageDraw.Draw(im)
        
        if self.add_dot :
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
    
    def __p_shadow (self, anchor, fill, dot_ctx) :
        sh = self.__p_pinwin(anchor, fill, dot_ctx)
        return self.tilt(sh)

    #
    
    def __p_cartoon_shadow (self, anchor, fill, dot_ctx) :

        # make the canvas

        w = self.offset + self.img_w + (self.padding * 2)
        h = self.offset + self.img_h + (self.padding * 2)
        
        cnv = Image.new('RGBA', (w, h))
        coords = self.__p_cartoon_shadow_coords()

        cnv = self.__p_draw_pinwin(cnv, coords, fill, dot_ctx)
    
        # tilt it
        blur = False
        cnv = self.tilt(cnv, blur)

        (cnv_w,cnv_h) = cnv.size

        sh_offset = int(w * .1)
        
        w = cnv_w + sh_offset
        h = cnv_h + int(self.anchor_h * .95)
        
        sh = Image.new('RGBA', (w, h))
        sh.paste(cnv, (sh_offset, 0), cnv)
        
        dr = ImageDraw.Draw(sh)
        
        # tack on the cone

        left = (self.offset + self.offset_cone - int(self.anchor_w * .5)) + int(sh_offset / 2)
        bottom = self.offset + self.offset_cone
        right = (self.offset + self.offset_cone + int(self.anchor_w * .5)) + int(sh_offset / 2)
        
        coords = [
            (left, cnv_h),
            (bottom, h),        
            (right, cnv_h),
            (left, cnv_h),            
            ]

        dr.polygon(coords, fill=fill)
        
        # dot

        self.dot('shadow', dr)
    
        # blur!
        
        return self.__p_blur(sh)
    
    #

    def __p_coords (self) :

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
    
    def __p_cartoon_shadow_coords (self) :
        
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

    def __p_mask (self, anchor, ctx='all') :

        dot_ctx = 'mask'

        pw_c = (255, 255, 255)
        sh_c = (130, 130, 130)

        pil_pw = self.generate_pinwin(anchor, pw_c, dot_ctx)
        pil_sh = self.generate_shadow(anchor, sh_c, dot_ctx)
        
        (pww, pwh) = pil_pw.size
        (shw, shh) = pil_sh.size
        
        w = max(pww, shw)
        h = max(pwh, shh)

        if ctx == 'pinwin' :
            w = pww
            h = pwh

        pil_im = Image.new('L', (w, h))
        dr = ImageDraw.Draw(pil_im)
        
        if ctx != 'pinwin' : 
            shx = 3	# not sure...
            shy = h - shh
            
            pil_im.paste(pil_sh, (shx, shy), pil_sh)
            
        if ctx != 'shadow' :
            pil_im.paste(pil_pw, (1, 1), pil_pw)
                
        return pil_im

    #
    
    def __p_tilt(self, pil_im, blur=True) :

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

        return pil_im.transform ((iw2,ih2), Image.PERSPECTIVE, data, Image.BILINEAR)

    #
    
    def __p_blur(self, pil_im, iterations=5) :

        (w, h) = pil_im.size

        # ensure some empty padding so the blurring
        # doesn't create butt ugly lines at the top
        # and bottom
        
        h+= 20
        
        im = Image.new('RGBA', (w, h))
        dr = ImageDraw.Draw(im)

        im.paste(pil_im, (0, 10), pil_im)
        
        for i in range(1, iterations) :
            im = im.filter(ImageFilter.BLUR)

        return im    

    #

    def __p_antialias(self, im) :

        scale = 4
        sz = im.size
        im = im.resize((sz[0] * scale, sz[1] * scale),  Image.NEAREST)
        im = im.resize(sz, Image.ANTIALIAS)

        return im
