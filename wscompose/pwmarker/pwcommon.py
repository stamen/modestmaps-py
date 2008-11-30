__package__    = "pwmarker/pwcommon.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/23 16:28:26 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import math

import PIL.Image
import PIL.ImageDraw

class Common :

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

            if self.render_engine == 'pil' :
                im = self.p__antialias(im)
                
            self.rendered[ctx] = im

    # 
    
    def generate_pinwin (self, anchor='bottom', dot_ctx='pinwin', *args) :

        key = "%s-%s-%s" % (anchor, dot_ctx, str(args))

        if self.pinwin_cache.has_key(key) :
            return self.pinwin_cache[key]

        #
        
        if self.render_engine == 'cairo' :

            pw = self.c__pinwin(anchor, dot_ctx, *args)       
            pw = self.c__cairo2pil(pw)        
        else :
            pw = self.p__pinwin(anchor, dot_ctx, *args)

        #
        
        self.pinwin_cache[key] = pw
        return pw
        
    #
    
    def generate_shadow (self, anchor='bottom', dot_ctx='shadow', *args) :

        # not clear whether caching is actually
        # necessary or useful here ...
        
        key = "%s-%s-%s" % (anchor, dot_ctx, str(args))

        if self.cartoon_shadows :
            key += "-cartoon"

        if self.shadow_cache.has_key(key) :
            return self.shadow_cache[key]

        #
        
        if self.render_engine == 'cairo' :

            if self.cartoon_shadows :
                sh = self.c__cartoon_shadow(anchor, dot_ctx, *args)
            else :
                sh = self.c__shadow(anchor, dot_ctx, *args)
                sh = self.c__cairo2pil(sh)

        else :
            if self.cartoon_shadows :
                sh = self.p__cartoon_shadow(anchor, dot_ctx, *args)
            else :
                sh = self.p__shadow(anchor, dot_ctx, *args)            

        #
        
        self.shadow_cache[key] = sh
	return sh

    #

    def generate_mask (self, anchor='bottom', ctx='all') :

        dot_ctx = "mask-%s" % ctx

        pw_c = (255, 255, 255)

        if self.render_engine == 'cairo' :
            sh_c = (.65, .65, .65)
        else :
            sh_c = (130, 130, 130)
        
        pw = self.generate_pinwin(anchor, dot_ctx, pw_c)
        sh = self.generate_shadow(anchor, dot_ctx, sh_c)
        
        (pww, pwh) = pw.size
        (shw, shh) = sh.size
        
        w = max(pww, shw)
        h = max(pwh, shh)

        if ctx == 'pinwin' :
            w = pww
            h = pwh

        im = PIL.Image.new('L', (w, h))
        dr = PIL.ImageDraw.Draw(im)

        if ctx != 'pinwin' : 
            shx = 3
            shy = h - shh

            # ugly ugly hack...please to track down
            # how not to need to do this...
            
            if self.add_dot :
                if self.cartoon_shadows :
                    shy -= int(self.dot_r * 1)
                else :
                    shy -= int(self.dot_r * 1.5)
                    shx -= int(self.dot_r * .5)
                    
            im.paste(sh, (shx, shy), sh)
            
        if ctx != 'shadow' :
            im.paste(pw, (1, 1), pw)
                
        return im

    #

    def tilt(self, pil_im, blur=True):

        sh = self.p__tilt(pil_im, blur)

        if blur == True :
            sh = self.blur(sh)

        return sh

    #
    
    def blur(self, pil_im) :
        return self.p__blur(pil_im)
    
    #

    def dot (self, ctx='pinwin', *args) :

        if self.render_engine == 'cairo' :
            return self.c__dot(ctx, args)
        else :
            return self.p__dot(ctx, *args)
        
    #
    
    def calculate_dimensions (self, anchor='bottom', ctx='pinwin') :

        if not self.border_c :
            self.border_c = (0, 0, 0)
            
        if not self.border_w :
            self.border_w = 2

        self.offset = int(math.ceil(self.border_w / 2))
        
        self.padding = int(min(self.img_w, self.img_h) * .1)

        if self.padding < 15 :
            self.padding = 15
        elif self.padding > 25 : 
            self.padding = 20
        else :
            pass

        self.corner_r = self.padding
        
        self.canvas_w = self.offset + self.border_w + self.img_w + (self.padding * 2)
        self.canvas_h = self.offset + self.img_h + (self.padding * 2) + self.anchor_h

        self.offset_x = self.offset + self.padding
        self.offset_y = self.offset + self.padding
            
        self.offset_cone = int(self.canvas_w * .35)

        if self.anchor_w > int(self.canvas_w / 2) :
            self.anchor_w = int(self.canvas_w / 3)

        h = self.canvas_h

        if ctx == 'pinwin' and self.add_dot :
            h += int(self.dot_r * 2)
            
        self.pt_x = self.offset + self.offset_cone
        self.pt_y = self.offset + self.img_h + (self.padding * 2) + self.anchor_h

        # legacy crap (see above)
        # note the +1 ... not sure, but it's necessary
        
        self.x_padding = self.offset + self.padding + 1
        self.y_padding = self.offset + self.padding + 1
        self.x_offset = self.pt_x
        self.y_offset = self.pt_y

        return (self.canvas_w, h)

    #

    def calculate_cartoon_anchor_coords (self, tilted_cnv) :

        (cnv_w,cnv_h) = tilted_cnv.size

        key = "%s-%s" % (cnv_w, cnv_h)

        if self.cartoon_anchor_cache.has_key(key) :
            return self.cartoon_anchor_cache[key]
        
        #
        
        w = self.offset + self.img_w + (self.padding * 2)
        h = self.offset + self.img_h + (self.padding * 2)

        sh_offset = int(w * .2)
        sh_anchor_h = int(self.anchor_h * .9)

        sh_anchor_w = int(self.anchor_w * .9)
        
        diff = self.anchor_h - sh_anchor_h
        cnv_half = int(cnv_h / 2)

        # for pinwins with insanely tall anchors
        # 90% may be larger than the canvas' height
        # which just looks weird

        if sh_anchor_h > cnv_h :
            sh_anchor_h = self.anchor_h - cnv_half

        # but we also want to make sure that shadows
        # for pinwins with short stubby anchors don't
        # start flush with the bottom of the canvas...
        # these are "cartoon" shadows after all so a
        # certain amount of artistic license is allowed
        
        elif diff < int(cnv_h / 4) :

            pw_cnv_h = (self.img_h + (self.padding * 2))
            
            if self.anchor_h < int(pw_cnv_h / 2) :
                sh_anchor_h = int(self.anchor_h / 2)
            else :
                sh_anchor_h = self.anchor_h - int(cnv_h / 4)
            
        else :
            pass
            
        # set up the dimensions for the image we're going to
        # combine the tilted canvas and anchor on
        
        tmp_w = cnv_w + sh_offset
        tmp_h = cnv_h + sh_anchor_h

        # figure out the coordinates for the anchor
        
        pwa_left = (self.offset + self.offset_cone - int(self.anchor_w * .5))
        pwa_right = pwa_left + self.anchor_w
        
        sha_left = pwa_left + sh_offset
        sha_right = sha_left + sh_anchor_w
        
        bottom_x = self.offset + self.offset_cone - self.border_w
        bottom_y = tmp_h

        # we don't draw the do because we'll never see it
        # but we do need to consider it

        if self.add_dot :
            bottom_y = bottom_y - self.dot_r

        if self.blurry_shadows :
            bottom_y += int(self.dot_r * 2.5)
            
        coords = ((tmp_w, tmp_h, sh_offset),
                  (sha_left, cnv_h),
                  (bottom_x, bottom_y),
                  (sha_right, cnv_h))
        
        self.cartoon_anchor_cache[key] = coords
        return coords
    
    #
    
    def position_shadow (self, pw, sh) :

        (pww, pwh) = pw.size
        (shw, shh) = sh.size

        w = max(pww, shw)
        h = max(pwh, shh)

        im = PIL.Image.new('RGBA', (w, h))
        dr = PIL.ImageDraw.Draw(im)

        shx = 3
        shy = h - shh

        if self.add_dot :
            shy -= int(self.dot_r)
        
        im.paste(sh, (shx, shy), sh)
        return im
    
    #

    def render_all (self, pw, sh, mask) :

        im = self.position_shadow(pw, sh)
        im.paste(pw, (1, 1), pw)
        
        im.putalpha(mask)
    	return im

    #
    
    def render_pinwin (self, pw, mask) :

	(w, h) = pw.size
        
        im = PIL.Image.new('RGBA', (w, h))
        dr = PIL.ImageDraw.Draw(im)

        im.paste(pw, (1, 1), pw)
        im.putalpha(mask)
    	return im

    #

    def render_shadow (self, pw, sh, mask) :

        im = self.position_shadow(pw, sh)
        im.putalpha(mask)
    	return im
            
    #

    def save (self, path, ctx='all') :
        if not self.rendered.has_key(ctx) :
            return None
        
        self.rendered[ctx].save(path)

    # backwards compatibility with (ws-modestmaps/markers.py)
    
    def fh (self, ctx='all') :
        if not self.rendered.has_key(ctx) :
            return None
        
        return self.rendered[ctx]

    # 
