__package__    = "pwmarker/__init__.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/pwmarker"
__date__       = "$Date: 2008/07/24 05:52:38 $"
__copyright__  = "Copyright (c) 2008 Aaron Straup Cope. All rights reserved."
__license__    = "http://www.modestmaps.com/license.txt"

import types

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

        self.add_dot = True
        self.cartoon_shadows = True
        self.blurry_shadows = True
        self.add_cropmarks = False

        # the radius of the dot at
        # the bottom of the cone/anchor

        self.dot_r = 7.5
        self.dot_c = (1, 0, 1)

        # pwcairo-isms

        self.surface = None
        
        # various image objects/caches

        self.pinwin_cache = {}
        self.shadow_cache = {}
        self.cartoon_anchor_cache = {}
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

        self.render_engine = 'pil'
        
        # Sharing is good...
        
        try :
            import pwcommon
            MixIn(PinwinMarker, pwcommon.Common, 0)
        except Exception, e :
            raise e

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
            self.render_engine = 'cairo'
            self.using_cairo = True            
        except Exception, e :
            print "failed to load pycairo %s" % e
            self.using_cairo = False            
            pass
        
    
if __name__ == '__main__' :

    import random
    import optparse

    def draw () :

        # this is how is *actually* works if you're interested...
        
        w = max(150, int(random.random() * 500))
        h = max(200, int(random.random() * 500))
        c = max(50, int(random.random() * 200))

        m = PinwinMarker(w, h, c)
        
        # m.border_w = 3
        # m.cartoon_shadows = False
        # m.blurry_shadows = False
        # m.add_dot = False
        
        m.draw()
        
        return m

    #
    
    def profile () :

        # http://python.active-venture.com/lib/profile-instant.html
        
        import profile
        import pstats
        
        profile.run('draw()', 'pwprof')
        p = pstats.Stats('pwprof')

        p.sort_stats('cumulative').print_stats(10)
        p.print_stats()

    #
    
    def run () :

        import os.path
        import pwd
        import posix
        user = pwd.getpwuid(posix.geteuid())
        home = os.path.abspath(user[5])
        
        pl = os.path.join(home, "example.png")
        pw = os.path.join(home, "example-pw.png")
        sh = os.path.join(home, "example-sh.png")

        m = draw()
        
        # profit
        
        m.save(pl)
        print "wrote combined layers to %s" % pl
        
        m.save(pw, "pinwin")
        print "wrote pinwin layer to %s" % pw
        
        m.save(sh, "shadow")
        print "wrote shadow layer to %s" % sh

    # hey look, code to run!
    
    parser = optparse.OptionParser()
    parser.add_option("-p", "--profile", action="store_true", help="run profiling stats", default=False)
    
    (opts, args) = parser.parse_args()

    if opts.profile :
        profile()
    else :
        run()
