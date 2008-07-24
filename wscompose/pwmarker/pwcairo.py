__package__    = "pwmarker/pwcairo.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/24 05:52:38 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import array
import math
import random
import cairo
import Image
import ImageDraw

# http://www.cairographics.org/pycairo/tutorial/
# http://www.tortall.net/mu/wiki/CairoTutorial
# http://www.cairographics.org/manual/cairo-Paths.html#cairo-arc
# http://www.cairographics.org/matrix_transform/

class CairoMarker :

    #
    
    def c__dot (self, ctx='pinwin', *args) :
    
        cr = cairo.Context(self.surface)
        
        cx = self.pt_x
        cy = self.pt_y

        if ctx == 'pinwin' :
            sh_c = (.3, .3, .3)
            dot_c = self.dot_c
        else :
            sh_c = (255, 255, 255)
            dot_c = (255, 255, 255)

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
    
    def c__pinwin (self, anchor='bottom', dot_ctx='pinwin', c=(0, 0, 0)) :
        
        self.c__setup(anchor, 'pinwin')
        
        if self.add_dot :
            dot = self.dot(dot_ctx)
                            
        background = self.c__draw(anchor, 'pinwin')
        background.set_source_rgb(255, 255, 255)
        background.fill()

        border = self.c__draw(anchor, 'pinwin')    
        border.set_source_rgb(c[0], c[1], c[2])
        border.set_line_width(self.border_w)

        # to prevent thick borders from exceeding
        # the center of a dot or just spilling off
        # it altogether...
        # http://www.cairographics.org/manual/cairo-cairo-t.html#cairo-set-miter-limit

        border.set_miter_limit(2);
        
        border.stroke()

        if dot_ctx == 'pinwin' and self.add_cropmarks :
            self.crop_marks()

        #

        return self.surface

    #

    def c__shadow (self, anchor='bottom', ctx='shadow', c=(0, 0, 0)) :

        self.c__setup(anchor, ctx)
        
        background = self.c__draw(anchor, ctx)
        background.set_source_rgba(c[0], c[1], c[2])    
        background.fill()

        plain = self.c__cairo2pil(self.surface)
        
        tilted = self.tilt(plain, self.blurry_shadows)
        return self.c__pil2cairo(tilted)

    #

    def c__cartoon_shadow (self, anchor='bottom', dot_ctx='shadow', c=(0, 0, 0)) :

        w = self.offset + self.img_w + (self.padding * 2)
        h = self.offset + self.img_h + (self.padding * 2)
        
        mode = cairo.FORMAT_ARGB32
        self.surface = cairo.ImageSurface (mode, w, h)

        # first draw the canvas and tilt it
        
        background = self.c__draw_canvas()
        background.set_source_rgba(c[0], c[1], c[2])    
        background.fill()

        blur = False

        #
        
        cnv = self.c__cairo2pil(self.surface)
        cnv = self.tilt(cnv, False)
        
        coords = self.calculate_cartoon_anchor_coords(cnv)

        (tmp_w, tmp_h, sh_offset) = coords[0]
        (sha_left, cnv_h) = coords[1]
        (bottom_x, bottom_y) = coords[2]
        (sha_right, cnv_h) = coords[3]
        
        mode = cairo.FORMAT_ARGB32
        self.surface = cairo.ImageSurface (mode, tmp_w, tmp_h)
        cr = cairo.Context(self.surface)
            
        # draw the anchor

        cr.move_to(sha_left, cnv_h)

        cr.line_to(bottom_x, bottom_y)            
        cr.line_to(sha_right, cnv_h)
        cr.line_to(sha_left, cnv_h)

        cr.set_source_rgba(c[0], c[1], c[2])    
        cr.fill()

        # combine the canvas and the anchor
        
        sh = self.c__cairo2pil(self.surface)
        sh.paste(cnv, (sh_offset, 0), cnv)

        # blur

        if not self.blurry_shadows :
            return sh
        
        sh = self.blur(sh)
        return sh
    
    #

    def c__setup (self, anchor, ctx='pinwin') :

        (w, h) = self.calculate_dimensions(anchor, ctx)
        
        mode = cairo.FORMAT_ARGB32
        self.surface = cairo.ImageSurface (mode, w, h)

    #

    def c__draw (self, anchor, ctx):
        return self.c__draw_vertical(ctx)

    #
    
    def c__draw_vertical(self, ctx) :

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

    def c__draw_canvas(self) :

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
    
    def c__pil2cairo(self, im, mode=None) :

        if not mode :
            mode = cairo.FORMAT_ARGB32
            
        data = im.tostring()
        a = array.array('B', data)

        (w,h) = im.size
        return cairo.ImageSurface.create_for_data (a, mode, w, h)

    #
    
    def c__cairo2pil(self, surface, mode='RGBA') :

        width = surface.get_width()
        height = surface.get_height()
        
        return Image.frombuffer(mode, (width, height), surface.get_data(), "raw", mode, 0, 1)
