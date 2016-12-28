"""
>>> toBinaryString(1)
'1'
>>> toBinaryString(2)
'10'
>>> toBinaryString(3)
'11'
>>> toBinaryString(4)
'100'

>>> fromBinaryString('1')
1
>>> fromBinaryString('11')
3
>>> fromBinaryString('101')
5
>>> fromBinaryString('1001')
9

>>> fromYahooRoad(0, 0, 17)
(0, 0, 1)
>>> fromYahooRoad(10507, 7445, 2)
(10507, 25322, 16)
>>> fromYahooRoad(10482, 7434, 2)
(10482, 25333, 16)

>>> toYahooRoad(0, 0, 1)
(0, 0, 17)
>>> toYahooRoad(10507, 25322, 16)
(10507, 7445, 2)
>>> toYahooRoad(10482, 25333, 16)
(10482, 7434, 2)

>>> fromYahooAerial(0, 0, 17)
(0, 0, 1)
>>> fromYahooAerial(10507, 7445, 2)
(10507, 25322, 16)
>>> fromYahooAerial(10482, 7434, 2)
(10482, 25333, 16)

>>> toYahooAerial(0, 0, 1)
(0, 0, 17)
>>> toYahooAerial(10507, 25322, 16)
(10507, 7445, 2)
>>> toYahooAerial(10482, 25333, 16)
(10482, 7434, 2)

>>> fromMicrosoftRoad('0')
(0, 0, 1)
>>> fromMicrosoftRoad('0230102122203031')
(10507, 25322, 16)
>>> fromMicrosoftRoad('0230102033330212')
(10482, 25333, 16)

>>> toMicrosoftRoad(0, 0, 1)
'0'
>>> toMicrosoftRoad(10507, 25322, 16)
'0230102122203031'
>>> toMicrosoftRoad(10482, 25333, 16)
'0230102033330212'

>>> fromMicrosoftAerial('0')
(0, 0, 1)
>>> fromMicrosoftAerial('0230102122203031')
(10507, 25322, 16)
>>> fromMicrosoftAerial('0230102033330212')
(10482, 25333, 16)

>>> toMicrosoftAerial(0, 0, 1)
'0'
>>> toMicrosoftAerial(10507, 25322, 16)
'0230102122203031'
>>> toMicrosoftAerial(10482, 25333, 16)
'0230102033330212'
"""

import math

octalStrings = ('000', '001', '010', '011', '100', '101', '110', '111')

def toBinaryString(i):
    """ Return a binary string for an integer.
    """
    return ''.join([octalStrings[int(c)]
                    for c
                    in oct(i).lstrip('0o')]).lstrip('0')

def fromBinaryString(s):
    """ Return an integer for a binary string.
    """
    s = list(s)
    e = 0
    i = 0
    while(len(s)):
        if(s[-1]) == '1':
            i += int(math.pow(2, e))
        e += 1
        s.pop()
    return i

def fromYahoo(x, y, z):
    """ Return column, row, zoom for Yahoo x, y, z.
    """
    zoom = 18 - z
    row = int(math.pow(2, zoom - 1) - y - 1)
    col = x
    return col, row, zoom

def toYahoo(col, row, zoom):
    """ Return x, y, z for Yahoo tile column, row, zoom.
    """
    x = col
    y = int(math.pow(2, zoom - 1) - row - 1)
    z = 18 - zoom
    return x, y, z

def fromYahooRoad(x, y, z):
    """ Return column, row, zoom for Yahoo Road tile x, y, z.
    """
    return fromYahoo(x, y, z)

def toYahooRoad(col, row, zoom):
    """ Return x, y, z for Yahoo Road tile column, row, zoom.
    """
    return toYahoo(col, row, zoom)

def fromYahooAerial(x, y, z):
    """ Return column, row, zoom for Yahoo Aerial tile x, y, z.
    """
    return fromYahoo(x, y, z)

def toYahooAerial(col, row, zoom):
    """ Return x, y, z for Yahoo Aerial tile column, row, zoom.
    """
    return toYahoo(col, row, zoom)

microsoftFromCorners = {'0': '00', '1': '01', '2': '10', '3': '11'}
microsoftToCorners = {'00': '0', '01': '1', '10': '2', '11': '3'}

def fromMicrosoft(s):
    """ Return column, row, zoom for Microsoft tile string.
    """
    row, col = map(fromBinaryString, zip(*[list(microsoftFromCorners[c]) for c in s]))
    zoom = len(s)
    return col, row, zoom

def toMicrosoft(col, row, zoom):
    """ Return string for Microsoft tile column, row, zoom.
    """
    x = col
    y = row
    y, x = toBinaryString(y).rjust(zoom, '0'), toBinaryString(x).rjust(zoom, '0')
    string = ''.join([microsoftToCorners[y[c]+x[c]] for c in range(zoom)])
    return string

def fromMicrosoftRoad(s):
    """ Return column, row, zoom for Microsoft Road tile string.
    """
    return fromMicrosoft(s)

def toMicrosoftRoad(col, row, zoom):
    """ Return x, y, z for Microsoft Road tile column, row, zoom.
    """
    return toMicrosoft(col, row, zoom)

def fromMicrosoftAerial(s):
    """ Return column, row, zoom for Microsoft Aerial tile string.
    """
    return fromMicrosoft(s)

def toMicrosoftAerial(col, row, zoom):
    """ Return x, y, z for Microsoft Aerial tile column, row, zoom.
    """
    return toMicrosoft(col, row, zoom)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
