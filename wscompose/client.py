# -*-python-*-

__package__    = "wscompose/client.py"
__version__    = "1.0"
__author__     = "Aaron Straup Cope"
__url__        = "http://www.aaronland.info/python/wscompose"
__date__       = "$Date: 2008/01/04 06:23:46 $"
__copyright__  = "Copyright (c) 2007-2008 Aaron Straup Cope. BSD license : http://www.modestmaps.com/license.txt"

import urllib
import httplib
import Image
import StringIO
import string
import re

class httpclient :

    def __init__ (self, host='127.0.0.1', port=9999) :
        self.__host__  = host
        self.__port__ = port

    # ##########################################################
    
    def fetch (self, args) :

        img = None
        meta = {}

        params = urllib.urlencode(args)
        url = "%s:%s" % (self.__host__, self.__port__)
        endpoint = "/?%s" % params

        # maybe always POST or at least add it as an option...
        
        try :
            conn = httplib.HTTPConnection(url)
            conn.request("GET", endpoint)
            res = conn.getresponse()
        except Exception, e :
            raise e

        if res.status != 200 :

            if res.status == 500 :
                errmsg = "(%s) %s" % (res.getheader('x-errorcode'), res.getheader('x-errormessage'))
                raise Exception, errmsg
            else :
                raise Exception, res.message   

        # fu.PYTHON ...
        re_xheader = re.compile(r"^x-wscompose-", re.IGNORECASE)
        
        for key, value in res.getheaders() :

            if re_xheader.match(key) :

                parts = key.split("-")
                parts = map(string.lower, parts)

                major = parts[2]
                minor = parts[3]
                
                if not meta.has_key(major) :
                    meta[major] = {}

                meta[major][minor] = value
                                    
        data = res.read()
        conn.close()

        try : 
            img = Image.open(StringIO.StringIO(data))
        except Exception, e :
            raise e
        
        return (img, meta)

    # ##########################################################
