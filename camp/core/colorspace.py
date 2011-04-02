# -*- coding: utf-8 -*-
import math


class Convert(object):
    """Set of functions to convert from one colorspace to another.
    :meth:`rgb2lab` and :meth:`lab2rgb` thanks to the following article:
    http://cookbooks.adobe.com/post_Useful_color_equations__RGB_to_LAB_converter-14227.html"""

    @classmethod
    def rgb2xyz(cls, rgb):
        """Convert from ``RGB`` colorspace into ``XYZ`` colorspace.
	
        :param rgb: RGB color tuple"""
        r = rgb[0] / 255.0
        g = rgb[1] / 255.0
        b = rgb[2] / 255.0
        
        if r > 0.04045:
            r = ((r + 0.055) / 1.055) ** 2.4
        else:
            r = r / 12.92
        if g > 0.04045:
            g = ((g + 0.055) / 1.055) ** 2.4
        else:
            g = g / 12.92
        if b > 0.04045:
            b = ((b + 0.055) / 1.055) ** 2.4
        else:
            b = b / 12.92

        r = r * 100.0
        g = g * 100.0
        b = b * 100.0
        
        # Observer = 2°, Illuminant = D65
        x = r * 0.4124 + g * 0.3576 + b * 0.1805
        y = r * 0.2126 + g * 0.7152 + b * 0.0722
        z = r * 0.0193 + g * 0.1192 + b * 0.9505

        return x, y, z

    @classmethod
    def xyz2lab(cls, xyz):
        """Convert from ``XYZ`` colorspace into ``Lab`` colorspace.
        
        :param xyz: XYZ color tuple"""
        # Observer = 2°, Illuminant = D65
        x = xyz[0] / 95.047
        y = xyz[1] / 100.0
        z = xyz[2] / 108.883

        if x > 0.008856:
            x = x ** (1.0 / 3.0)
        else:
            x = (7.787 * x) + (16.0 / 116.0)
        if y > 0.008856:
            y = y ** (1.0 / 3.0)
        else:
            y = (7.787 * y) + (16.0 / 116.0)
        if z > 0.008856:
            z = z ** (1.0 / 3.0)
        else:
            z = (7.787 * z) + (16.0 / 116.0)

        l = ( 116.0 * y ) - 16.0;
        a = 500.0 * ( x - y );
        b = 200.0 * ( y - z );

        return l, a, b

    @classmethod
    def rgb2lab(cls, rgb):
        """Convert from ``RGB`` colorspace into ``Lab`` colorspace.
        
        :param rgb: RGB color tuple"""
        return cls.xyz2lab(cls.rgb2xyz(rgb))

    @classmethod
    def lab2xyz(cls, lab):
        """Convert from ``Lab`` colorspace into ``XYZ`` colorspace.
        
        :param lab: Lab colorspace tuple"""
        y = (lab[0] + 16.0) / 116.0
        x = lab[1] / 500.0 + y
        z = y - lab[2] / 200.0

        if y ** 3 > 0.008856:
            y = y ** 3
        else:
            y = (y - 16.0 / 116.0) / 7.787
        if x ** 3 > 0.008856:
            x = x ** 3
        else:
            x = (x - 16.0 / 116.0) / 7.787
        if z ** 3 > 0.008856:
            z = z ** 3
        else:
            z = (z - 16.0 / 116.0) / 7.787

        x = 95.047 * x
        y = 100.0 * y
        z = 108.883 * z

        return x, y, z

    @classmethod
    def xyz2rgb(cls, xyz):
        """Convert from ``XYZ`` colorspace into ``RGB`` colorspace.

        :param xyz: XYZ colorspace tuple"""
        x = xyz[0] / 100.0
        y = xyz[1] / 100.0
        z = xyz[2] / 100.0

        r = x * 3.2406 + y * -1.5372 + z * -0.4986
        g = x * -0.9689 + y * 1.8758 + z * 0.0415
        b = x * 0.0557 + y * -0.2040 + z * 1.0570

        if r > 0.0031308:
            r = 1.055 * (r ** (1.0 / 2.4)) - 0.055
        else:
            r = 12.92 * r
        if g > 0.0031308:
            g = 1.055 * (g ** (1.0 / 2.4)) - 0.055
        else:
            g = 12.92 * g
        if b > 0.0031308:
            b = 1.055 * (b ** (1.0 / 2.4)) - 0.055
        else:
            b = 12.92 * b

        r = int(round(r * 255.0))
        g = int(round(g * 255.0))
        b = int(round(b * 255.0))

        return r, g, b

    @classmethod
    def lab2rgb(cls, lab):
        """Convert from ``Lab`` colorspace into ``RGB`` colorspace.
        
        :param lab: Lab colorspace tuple"""
        return cls.xyz2rgb(cls.lab2xyz(lab))

    @classmethod
    def rgb2hsv(cls, rgb):
        """Convert from ``RGB`` colorspace into ``HSV`` colorspace. Each
        channel of source ``RGB`` vector is in range 0..255. Ranges of
        resulting ``HSV`` vector channels are following:
        * 0..359 for H
        * 0..100 for S
        * 0..100 for V
        
        :param rgb: RGB colorspace tuple"""
        rgb = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        v = max(rgb)
        x = min(rgb)
        if x == v:
            h = s = 0.0
        else:
            if rgb[0] == x:
                f = rgb[1] - rgb[2]
                i = 3.0
            elif rgb[1] == x:
                f = rgb[2] - rgb[0]
                i = 5.0
            else:
                f = rgb[0] - rgb[1]
                i = 1.0
            h = (i - f / (v - x)) * 60.0
            h = h - math.floor(h/359.9) * 359.9 / 359.9   # h mod 359.9
            s = (v - x) / v
        return int(h), int(s*100.0), int(v*100.0)
        
    @classmethod
    def hsv2rgb(cls, hsv):
        """Convert from ``HSV`` colorspace into ``RGB`` colorspace. Both
        ``RGB`` and ``HSV`` channels are in ranges specified in
        :meth:`rgb2hsv`.
        
        :param hsv: HSV color tuple"""
        h, s, v = hsv[0]/359.9, hsv[1]/100.0, hsv[2]/100.0
        if h < 0.0:
            h = 0.0
        elif h > 359.9:
            h = 359.9
        if s < 0.0:
            s = 0.0
        elif s > 100.0:
            s = 100.0
        if v < 0.0:
            v = 0.0
        elif v > 100.0:
            v = 100.0
        if v == 0.0:
            return 0.0, 0.0, 0.0
        else:
            h = h * 5.998
            i = math.floor(h)
            f = h - i
            p = v * (1.0 - s)
            q = v * (1.0 - (s * f))
            t = v * (1.0 - (s * (1.0 - f)))
            if i == 0.0:
                r, g, b = v, t, p
            elif i == 1.0:
                r, g, b = q, v, p
            elif i == 2.0:
                r, g, b = p, v, t
            elif i == 3.0:
                r, g, b = p, q, v
            elif i == 4.0:
                r, g, b = t, p, v
            else:  # i == 5.0:
                r, g, b = v, p, q
            return int(r*255.0), int(g*255.0), int(b*255.0)
