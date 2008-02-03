# -*-python-*-

__package__    = "wscompose/plotting.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wscompose"
__date__       = "$Date: 2008/01/04 06:23:46 $"
__copyright__  = "Copyright (c) 2007-2008 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license."

import wscompose
import wscompose.markers
import string
import random
import re

import ModestMaps
import Image
import ImageDraw

# SEE COMMENTS IN markers.py ABOUT VARIABLE NAMES
#
# TO DO (patches are welcome) :
#
# - figure out whether/what code here should be merged
#   with pinwin.py
#
# - make the background for an image with bleeds transparent
#
# - adjust randomly (for overlaps) on the x-axis
#
# - allow for the marker canvas (and cone) to be rotated
#   360 degrees around a point (also to do in marker.py)

class handler (wscompose.handler) :

    def __init__ (self, request, client_address, server) :
        self.__markers__ = {}

        wscompose.handler.__init__(self, request, client_address, server)

    # ##########################################################
    
    def draw_map (self) :

        img = wscompose.handler.draw_map(self)
        img = self.draw_markers(img)

        return img
    
    # ##########################################################

    def sort_markers (self):

        def mysort (x, y) :
            return cmp (y['latitude'], x['latitude'])

        self.ctx['markers'].sort(mysort)
        
    # ##########################################################

    def reload_markers (self) :

        # it's called reload marker because it simply
        # calculates all the coordinates for a marker
        # but does not draw it
        
        for mrk_data in self.ctx['markers'] :

            # please reconcile me with the code
            # in __init__/draw_marker

            w = mrk_data['width']
            h = mrk_data['height']
            a = mrk_data['adjust_cone_height']
            
            mrk = self.load_marker(w, h, a)
            
            loc = ModestMaps.Geo.Location(mrk_data['latitude'], mrk_data['longitude'])
            pt = self.ctx['map'].locationPoint(loc)            
            
            # argh...fix me!

            bleed_x = 0
            bleed_y = 0
            
            mrk_data['x'] = int(pt.x) + bleed_x
            mrk_data['y'] = int(pt.y) + bleed_y

            x1 = mrk_data['x'] - int(mrk.x_offset)
            y1 = mrk_data['y'] - int(mrk.y_offset)
            
            x2 = x1 + (w + mrk.padding)
            y2 = y1 + (h + mrk.padding)
            
            mrk_data['canvas'] = (x1, y1, x2, y2)
            
    # ##########################################################

    def reposition_markers (self) :
        self.sort_markers()
        return self.__reposition_markers()

    # ##########################################################
    
    def __reposition_markers (self, iterations=1, max_iterations=25) :

        # get some context
        self.reload_markers()
        
        # the number of markers
        count = len(self.ctx['markers'])

        # markers, accounting for 0-based index
        indexes = range(0, count)

        # start from the bottom
        indexes.reverse()

        # happy happy
        try_again = False

        for offset_mrk in range(0, count) : 

            mrk_idx = indexes[offset_mrk]
            current = self.ctx['markers'][mrk_idx]

            next = offset_mrk + 1

            for offset_test in range(next, count) :

                test_idx = indexes[offset_test]
                other = self.ctx['markers'][test_idx]

                overlap = self.does_marker_overlap_marker(current, other)
                
                if overlap != 0 :

                    self.ctx['markers'][test_idx]['adjust_cone_height'] += (overlap + random.randint(10, 100))
                    try_again = True
                    break
            
            if try_again :
                break

        if try_again :
            
            iterations += 1

            # if iterations == max_iterations :
            #     return False
            
            return self.__reposition_markers(iterations)

        return True
    
    # ##########################################################

    def does_marker_overlap_marker(self, current, test) :

        cur_label = current['label']
        test_label = test['label']

        # print "does %s overlap %s" % (cur_label, test_label)
        
        # first, ensure that some part of 'current'
        # overlaps 'test' on the x axis

        cur_x1 = current['canvas'][0]
        cur_x2 = current['canvas'][2]
        test_x1 = test['canvas'][0]
        test_x2 = test['canvas'][2]

        # print "\t%s (X) : %s, %s" % (cur_label, cur_x1, cur_x2)
        # print "\t%s (X) : %s, %s" % (test_label, test_x1, test_x2)

        if test_x1 > cur_x2 :
            return 0
        
        if test_x2 < cur_x1 :
            return 0

        cur_y = current['y']
        test_y = test['y']

        cur_cy1 = current['canvas'][1]
        cur_cy2 = current['canvas'][3]

        test_cy1 = test['canvas'][1]
        test_cy2 = test['canvas'][3]

        # do both markers occupy the same space?

        if cur_cy1 == test_cy1 and test_cy2 == cur_cy2 : 
            return cur_cy2 - cur_cy1
        
        # print "%s\t%s\t%s\t%s" % (cur_cy1, cur_cy2, cur_y, cur_label)
        # print "%s\t%s\t%s\t%s" % (test_cy1, test_cy2, test_y, test_label)

        # is the y (lat) position of 'test' somewhere
        # in the space between the y position of 'current'
        # and the bottom of its pinwin canvas?
        
        if cur_cy2 >= test_y :            
            if cur_cy1 <= test_cy2 :

                return test_cy2 - cur_cy1

        # the y (or lat) position for 'test' falls between
        # the canvas of 'current'
        
        if test_y > cur_cy1 :
            if test_cy2 >= cur_cy1 : 
                return test_cy2 - cur_cy1

        # ensure at least a certain amount of
        # space between markers
        
        space = cur_cy1 - test_cy2
        
        if space <= 10 :
            return random.randint(10, 25)
        
        return 0
    
    # ##########################################################
    
    def draw_markers (self, img) :

        self.sort_markers()
            
        for data in self.ctx['markers'] :
            self.draw_marker(img, data)

        return img
    
    # ##########################################################
        
    def draw_marker (self, img, mrk_data, bleed_x=0, bleed_y=0) :

        w = mrk_data['width']
        h = mrk_data['height']
        a = mrk_data['adjust_cone_height']
        
        mrk = self.load_marker(w, h, a)
                                        
        loc = ModestMaps.Geo.Location(mrk_data['latitude'], mrk_data['longitude'])
        pt = self.ctx['map'].locationPoint(loc)            

        #
        
        mrk_data['x'] = int(pt.x) + bleed_x
        mrk_data['y'] = int(pt.y) + bleed_y

        mx = mrk_data['x'] - int(mrk.x_offset)
        my = mrk_data['y'] - int(mrk.y_offset)

        dx = mx + mrk.x_padding
        dy = my + mrk.y_padding

        #

        img.paste(mrk.fh(), (mx, my), mrk.fh())
        
        mrk_data['x_fill'] = dx
        mrk_data['y_fill'] = dy        
           
    # ##########################################################
    
    def validate_params (self, params) :
        
        valid  = wscompose.handler.validate_params(self, params)
        
        if not valid :
            return False

        if not params.has_key('marker') :
            self.error(101, "Missing or incomplete parameter : %s" % 'marker')
            return False
            
        return valid

    # ##########################################################
    
    def load_marker (self, w, h, a) :

        key = "%s-%s-%s" % (w, h, a)

        if not self.__markers__.has_key(key) :
            self.__markers__[key] = wscompose.markers.pinwin(w, h, a)

        return self.__markers__[key]

    # ##########################################################
