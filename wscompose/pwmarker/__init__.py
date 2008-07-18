__package__    = "pwmarker/__init__.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/18 05:55:28 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import types
import math

import Image
import ImageDraw

# notes :
# 
# this package uses "mixins" to add or change functionality
# based on the rendering engine (pycairo, if present, or PIL)
# the layout of the various methods may change and there is
# a measure of duplication in the wrapper methods if only
# just to make it easier to see who's on first.
#
# the part where you see 'anchor=bottom' all over the place
# is stub code for a time when you will be able to place the
# anchor on any one of the canvas' four sides. that did not
# make the first cut; just ignore it for now.

class PinwinMarker :

    def __init__ (self, w, h, c=0) :

        # image dimensions
        
        self.img_w = w
        self.img_h = h

        # the cone-y bit ensure that
        # it's at least 20px tall
        
        if c == 0 :
            c = max(20, int(h * .3))
        
        self.anchor_h = c
        self.anchor_w = 20

        if self.img_w > (self.anchor_w * 5) and self.img_h > (self.anchor_w * 5):
            self.anchor_w = 30
            
        # the space between the outer
        # edge of the pinwin and the
        # image
        
        self.padding = None

        # the radius of the rounded corners
        # on a pinwin (used by pycairo)
        
        self.corner_r = None

        # the line width of the border
        # around a pinwin
        
        self.border_w  = None

        # the colour used for the border
        # around a pinwin
        
        self.border_c = None
        
        # the amount to offset the edge
        # of the pinwin from (0,0) to
        # prevent the aliasing on the
        # border from being cropped
        
        self.offset = None

        # the actual height and width
        # of the pinwin canvas factoring
        # in padding and border width
        # and stuff
        
        self.canvas_w = None
        self.canvas_h = None

        self.offset_x = None
        self.offset_y = None

        # the x, y coordinates of the
        # bottom of the anchor/cone
        # (relative to the pinwin's
        # 0,0 position)
        
        self.pt_x = None
        self.pt_y = None

        self.cartoon_shadows = True
        self.add_cropmarks = False
        
        self.add_dot = True

        # the radius of the dot at
        # the bottom of the cone/anchor

        self.dot_r = 7.5
        self.dot_c = (1, 0, 1)

        # pwcairo-isms

        self.surface = None
        
        # various image objects/caches

        self.pinwin_cache = {}
        self.shadow_cache = {}
        self.rendered = {'all' : None, 'pinwin' : None, 'shadow' : None}
        
        # legacy crap to account for the wscompose/markers.py
        # code in modestmaps. it will probably never go away
        # but should be considered as deprecated...
        
        self.x_padding = None
        self.y_padding = None 
        self.x_offset = None
        self.y_offset = None

        # to be perfectly honest, hacking the symbol table
        # in perl is both easier and makes more sense...
        # 
        # http://www.linuxjournal.com/article/4540

        def MixIn(pyClass, mixInClass, makeAncestor=0):
            if makeAncestor:
                if mixInClass not in pyClass.__bases__:
                    pyClass.__bases__ = (mixInClass,) + pyClass.__bases__
            else:
                # Recursively traverse the mix-in ancestor
                # classes in order to support inheritance
                baseClasses = list(mixInClass.__bases__)
                baseClasses.reverse()
                for baseClass in baseClasses:
                    MixIn(pyClass, baseClass)
                # Install the mix-in methods into the class
                for name in dir(mixInClass):
                    if not name.startswith('__'):
                        # skip private members
                        member = getattr(mixInClass, name)
                        if type(member) is types.MethodType:
                            member = member.im_func
                        setattr(pyClass, name, member)

        # Assume PIL, or cry
        
        try :
            import pwpil
            MixIn(PinwinMarker, pwpil.PILMarker, 0)
        except Exception, e :
            raise e

        # Add the Cairo love, if possible
        
        try : 
            import pwcairo    
            MixIn(PinwinMarker, pwcairo.CairoMarker, 0)
            self.using_cairo = True
        except Exception, e :
            self.using_cairo = False            
            pass
        
    #

    def calculate_dimensions (self, anchor='bottom') :

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
        
        if self.add_dot :
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
    
    def position_shadow(self, pw, sh) :

        (pww, pwh) = pw.size
        (shw, shh) = sh.size

        w = max(pww, shw)
        h = max(pwh, shh)

        im = Image.new('RGBA', (w, h))
        dr = ImageDraw.Draw(im)

        shx = 3
        shy = h - shh

        # add the shadow        
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

        im = Image.new('RGBA', (w, h))
        dr = ImageDraw.Draw(im)

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

    # 
    
    def fh (self, ctx='all') :
        if not self.rendered.has_key(ctx) :
            return None
        
        return self.rendered[ctx]

    # stubs (re) defined in an engine-specific class
    
    def draw (self, anchor='bottom') :
        pass

    def pinwin (self, *args) :
        pass

    def shadow (self, *args) :
        pass

    def mask (self, *args) :
        pass

    def compose (self, *args) :
        pass

    def tilt (self, *args) :
        pass

    def blur (self, *args) :
        pass    

    def dot (self, *args) :
        pass

    def crop_marks (self, *args) :
        pass
    
if __name__ == '__main__' :

    import random
    import os.path
    import pwd
    import posix

    # files we will write to
    
    user = pwd.getpwuid(posix.geteuid())
    home = os.path.abspath(user[5])

    pl = os.path.join(home, "example.png")
    pw = os.path.join(home, "example-pw.png")
    sh = os.path.join(home, "example-sh.png")

    # size of the pinwin marker
    
    w = max(150, int(random.random() * 500))
    h = max(200, int(random.random() * 500))
    c = max(50, int(random.random() * 200))

    # go!
    
    m = PinwinMarker(w, h, c)

    # m.border_w = 3
    # m.add_cropmarks = True
    m.cartoon_shadows = False
    
    m.draw()

    # profit
    
    m.save(pl)
    print "wrote combined layers to %s" % pl
    
    m.save(pw, "pinwin")
    print "wrote pinwin layer to %s" % pw
    
    m.save(sh, "shadow")
    print "wrote shadow layer to %s" % sh
