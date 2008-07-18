__package__    = "pwmarker/pwcairo.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/18 05:54:33 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import array
import math
import cairo
import Image
import ImageDraw

# http://www.cairographics.org/pycairo/tutorial/
# http://www.tortall.net/mu/wiki/CairoTutorial
# http://www.cairographics.org/manual/cairo-Paths.html#cairo-arc
# http://www.cairographics.org/matrix_transform/

class CairoMarker :

    def draw (self, anchor='bottom') :

        pw = self.generate_pinwin(anchor)
        sh = self.generate_shadow(anchor)
        sh = self.position_shadow(pw, sh)
        
        for ctx in self.rendered.keys() :
            mask = self.generate_mask(anchor, ctx)
        
            if ctx == 'pinwin' :
                self.rendered[ctx] = self.render_pinwin(pw, mask)
            elif ctx == 'shadow' :
                self.rendered[ctx] = self.render_shadow(pw, sh, mask)        
            else :
                self.rendered[ctx] = self.render_all(pw, sh, mask)   

    #
    
    def generate_pinwin (self, anchor='bottom', c=(0, 0, 0), dot_ctx='pinwin') :

        key = "%s-%s-%s" % (anchor, c, dot_ctx)

        if self.pinwin_cache.has_key(key) :
            return self.pinwin_cache[key]
        
        pw = self.__c_pinwin(anchor, c, dot_ctx)                
        pw = self.__cairo2pil(pw)        

        self.pinwin_cache[key] = pw
        return pw
        
    #
    
    def generate_shadow (self, anchor='bottom', c=(0, 0, 0), dot_ctx='shadow') :

        key = "%s-%s-%s" % (anchor, c, dot_ctx)

        if self.cartoon_shadows :
            key += "-cartoon"

        if self.shadow_cache.has_key(key) :
            return self.shadow_cache[key]
            
        if self.cartoon_shadows :
            sh = self.__c_cartoon_shadow(anchor, c, dot_ctx)
	else :
            sh = self.__c_shadow(anchor, c, dot_ctx)
            sh = self.__cairo2pil(sh)

        self.shadow_cache[key] = sh
	return sh

    #

    def generate_mask (self, anchor, ctx) :
        return self.__c_mask(anchor, ctx)
            
    #
        
    def dot (self, ctx='pinwin', *args) :

            cr = cairo.Context(self.surface)
        
            cx = self.pt_x
            cy = self.pt_y

            if ctx == 'shadow' :
                sh_c = (0, 0, 0)
                dot_c = (0, 0, 0)
            
            elif ctx == 'mask' :
                sh_c = (255, 255, 255)
                dot_c = (255, 255, 255)
                
            else :
                sh_c = (.3, .3, .3)
                dot_c = self.dot_c

            # mock shadow
                
            cr.arc (cx + 1, cy + 1, self.dot_r, 0, 360)            
            cr.set_source_rgb(sh_c[0], sh_c[1], sh_c[2])
            cr.fill()

            # dot proper
            
            cr.arc (cx, cy, self.dot_r, 0, 360)                
            cr.set_source_rgb(dot_c[0], dot_c[1], dot_c[2])
            cr.fill()

            # donut hole
                
            if ctx == 'pinwin' :                
                cr.arc (cx, cy, 2, 0, 360)
                cr.set_source_rgb(255, 255, 255)
                cr.fill()                

    #
    
    def crop_marks (self) :

        cr = cairo.Context(self.surface)

        nw_x = self.offset_x
        nw_y = self.offset_y

        ne_x = self.offset_x + self.img_w
        ne_y = self.offset_y

        se_x = self.offset_x + self.img_w
        se_y = self.offset_y + self.img_h

        sw_x = self.offset_x
        sw_y = self.offset_y + self.img_h

        guide = self.padding
        lead = int(guide / 2)
        
        cr.move_to(nw_x - lead, nw_y)
        cr.line_to((nw_x + guide), nw_y)

        cr.move_to(nw_x, (nw_y - lead))
        cr.line_to(nw_x, (nw_y + guide))

        cr.move_to((ne_x + lead), ne_y)
        cr.line_to((ne_x - guide), ne_y)

        cr.move_to(ne_x, (ne_y - lead))
        cr.line_to(ne_x, (ne_y + guide))

        cr.move_to((se_x + lead), se_y)
        cr.line_to((se_x - guide), se_y)

        cr.move_to(se_x, (se_y + lead))
        cr.line_to(se_x, (se_y - guide))

        cr.move_to((sw_x - lead), sw_y)
        cr.line_to((sw_x + guide), sw_y)

        cr.move_to(sw_x, (sw_y + lead))
        cr.line_to(sw_x, (sw_y - guide))

        #

        cr.move_to((self.pt_x - self.dot_r), (self.pt_y - self.dot_r))
        cr.line_to((self.pt_x + self.dot_r), (self.pt_y + self.dot_r))

        cr.move_to((self.pt_x - self.dot_r), (self.pt_y + self.dot_r))
        cr.line_to((self.pt_x + self.dot_r), (self.pt_y - self.dot_r))
        
        #
        
        cr.set_source_rgb(0, 0, 1)
        cr.set_line_width(1)   
        cr.stroke()   
        
    #
    # 
    #
    
    def __c_pinwin (self, anchor='bottom', c=(0, 0, 0), ctx='pinwin') :
        
        self.__c_setup(anchor)
        
        if self.add_dot :                
            dot = self.dot(ctx)
                            
        background = self.__c_draw(anchor)
        background.set_source_rgb(255, 255, 255)
        background.fill()

        border = self.__c_draw(anchor)    
        border.set_source_rgb(c[0], c[1], c[2])
        border.set_line_width(self.border_w)

        # to prevent thick borders from exceeding
        # the center of a dot or just spilling off
        # it altogether...
        # http://www.cairographics.org/manual/cairo-cairo-t.html#cairo-set-miter-limit

        border.set_miter_limit(2);
        
        border.stroke()

        if ctx == 'pinwin' and self.add_cropmarks :
            self.crop_marks()

        #

        return self.surface

    #

    def __c_shadow (self, anchor='bottom', c=(0, 0, 0), dot_ctx='shadow') :
        
        self.__c_setup(anchor)

        if self.add_dot :
            self.dot(dot_ctx)            

        background = self.__c_draw(anchor)
        background.set_source_rgba(c[0], c[1], c[2])    
        background.fill()

        plain = self.__cairo2pil(self.surface)
        tilted = self.tilt(plain)

        return self.__pil2cairo(tilted)

    	# fix me : anchors

    #

    def __c_cartoon_shadow (self, anchor='bottom', c=(0, 0, 0), dot_ctx='shadow') :

        w = self.offset + self.img_w + (self.padding * 2)
        h = self.offset + self.img_h + (self.padding * 2)

        mode = cairo.FORMAT_ARGB32
        self.surface = cairo.ImageSurface (mode, w, h)

        background = self.__c_draw_canvas()
        background.set_source_rgba(c[0], c[1], c[2])    
        background.fill()

        cnv = self.__cairo2pil(self.surface)

        blur = False
        cnv = self.tilt(cnv, False)
    
        # draw the anchor

        (cnv_w,cnv_h) = cnv.size

        sh_offset = int(w * .1)
        sh_bleed = int(self.anchor_h * .90)

        if (self.anchor_h - sh_bleed) > int(cnv_h / 2) :
            sh_bleed= self.anchor_h - int(cnv_h / 2)

        elif (self.anchor_h - sh_bleed) < int(cnv_h / 4) :
            sh_bleed = self.anchor_h - int(cnv_h / 4)
        else :
            pass
        
        w = cnv_w + sh_offset
        h = cnv_h + sh_bleed

        left = (self.offset + self.offset_cone - int(self.anchor_w * .5)) + int(sh_offset / 2)
        bottom = self.offset + self.offset_cone
        right = (self.offset + self.offset_cone + int(self.anchor_w * .5)) + int(sh_offset / 2)

        mode = cairo.FORMAT_ARGB32
        self.surface = cairo.ImageSurface (mode, w, h)
        cr = cairo.Context(self.surface)

        # don't bother - you'll never see it anyway
            
        if self.add_dot :
            pass
            
        cr.move_to(left, cnv_h)
        cr.line_to(bottom, h)
        cr.line_to(right, cnv_h)
        cr.line_to(left, cnv_h)

        cr.set_source_rgba(c[0], c[1], c[2])    
        cr.fill()

        # combine the canvas and the anchor
        
        sh = self.__cairo2pil(self.surface)
        sh.paste(cnv, (sh_offset, 0), cnv)

        # blur
        
        return self.blur(sh)
    
    #

    def __c_mask(self, anchor='bottom', ctx='all') :

        dot_ctx = 'mask'

    	pw_c = (255, 255, 255)
    	sh_c = (.7, .7, .7)

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
        
    def __c_apply_matrix(self, surface, matrix) :
        
        data = array.array ("c", surface.get_data())
        mode = cairo.FORMAT_ARGB32
        
        tmp = cairo.ImageSurface.create_for_data (data, mode, self.canvas_w, self.canvas_h)
        surface = cairo.ImageSurface (mode, self.canvas_w, self.canvas_h)

        cr = cairo.Context(surface)
        
        cr.transform(matrix)
        cr.set_source_surface(tmp)
        cr.paint ()

        return surface

    #

    def __c_setup (self, anchor) :

        (w, h) = self.calculate_dimensions(anchor)
        
        mode = cairo.FORMAT_ARGB32
        self.surface = cairo.ImageSurface (mode, w, h)

    #

    def __c_draw (self, anchor):
        return self.__c_draw_vertical()

    #
    
    def __c_draw_vertical(self) :

        # to do : investigate the 'curve_to' method...

        cr = cairo.Context(self.surface)
            
        # top right arc
        # 
        #   *------------------------
        #  *                         \
        # *                           \
        
        x = (self.offset + self.padding)
        y = (self.offset + 0)
        cx = (self.offset + self.img_w + self.padding)
        cy = (self.offset + self.padding)

        cr.move_to(x, y)
        cr.arc(cx, cy, self.corner_r, -math.pi/2, 0)

        # bottom right arc
        # 
        #                                |
        #                                |
        #                               /
        #                              /

        x = (self.offset + self.img_w + (self.padding * 2))
        y = (self.offset + self.img_h + self.padding)
        cx = (self.offset + self.img_w + self.padding)
        cy = (self.offset + self.img_h + self.padding)

        cr.line_to(x, y)
        cr.arc (cx, cy, self.corner_r, 0, math.pi/2)

        # cone
        #
        #                -----------------------------
        #               
        #             
        
        x = (self.offset + self.offset_cone + int(self.anchor_w * .5))
        y = (self.offset + self.img_h + (self.padding * 2))
        cr.line_to(x, y)

        # cone
        #
        #           ==== 
        #          /
        #         /
        
        x = (self.offset + self.offset_cone)
        y = (self.offset + self.canvas_h)
        cr.line_to(x, y)

        # cone
        #
        #  ***\
        #      \
        
        x = (self.offset + self.offset_cone - int(self.anchor_w * .5))
        y = (self.offset + self.img_h + (self.padding * 2))
        cr.line_to(x, y)
        
        # bottom left arc
        #
        # \
        #  \
        #   -----
        
        x = (self.offset + self.padding)
        y = (self.offset + self.img_h + (self.padding * 2))
        cx = (self.offset + self.padding)
        cy = (self.offset + self.img_h + self.padding)

        cr.line_to(x, y)
        cr.arc (cx, cy, self.corner_r, math.pi/2, math.pi)
    
        # top left arc
        #
        #    /
        #   /
        #   |
        #   |
        
        x = (self.offset + 0)
        y = (self.offset + self.padding)
        cx = (self.offset + self.padding)
        cy = (self.offset + self.padding)

        cr.line_to(x, y)
        cr.arc (cx, cy, self.corner_r, math.pi, -math.pi/2)

        #

        return cr

    #

    def __c_draw_canvas(self) :

        cr = cairo.Context(self.surface)
            
        # top right arc
        # 
        #   *------------------------
        #  *                         \
        # *                           \
        
        x = (self.offset + self.padding)
        y = (self.offset + 0)
        cx = (self.offset + self.img_w + self.padding)
        cy = (self.offset + self.padding)

        cr.move_to(x, y)
        cr.arc(cx, cy, self.corner_r, -math.pi/2, 0)

        # bottom right arc
        # 
        #                                |
        #                                |
        #                               /
        #                              /

        x = (self.offset + self.img_w + (self.padding * 2))
        y = (self.offset + self.img_h + self.padding)
        cx = (self.offset + self.img_w + self.padding)
        cy = (self.offset + self.img_h + self.padding)

        cr.line_to(x, y)
        cr.arc (cx, cy, self.corner_r, 0, math.pi/2)

        # bottom
        #
        #  -----------------------------
        
        x = (self.offset + self.padding)
        y = (self.offset + self.img_h + (self.padding * 2))        
        cr.line_to(x, y)
        
        # bottom left arc
        #
        # \
        #  \
        #   -----
        
        x = (self.offset + self.padding)
        y = (self.offset + self.img_h + (self.padding * 2))
        cx = (self.offset + self.padding)
        cy = (self.offset + self.img_h + self.padding)

        cr.line_to(x, y)
        cr.arc (cx, cy, self.corner_r, math.pi/2, math.pi)
    
        # top left arc
        #
        #    /
        #   /
        #   |
        #   |
        
        x = (self.offset + 0)
        y = (self.offset + self.padding)
        cx = (self.offset + self.padding)
        cy = (self.offset + self.padding)

        cr.line_to(x, y)
        cr.arc (cx, cy, self.corner_r, math.pi, -math.pi/2)

        #

        return cr

    #        
    
    def __pil2cairo(self, im, mode=None) :

        if not mode :
            mode = cairo.FORMAT_ARGB32
            
        data = im.tostring()
        a = array.array('B', data)

        (w,h) = im.size
        return cairo.ImageSurface.create_for_data (a, mode, w, h)

    #
    
    def __cairo2pil(self, surface, mode='RGBA') :

        width = surface.get_width()
        height = surface.get_height()
        
        return Image.frombuffer(mode, (width, height), surface.get_data(), "raw", mode, 0, 1)
