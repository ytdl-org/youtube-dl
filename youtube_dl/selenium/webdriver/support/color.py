# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

RGB_PATTERN = r"^\s*rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)\s*$"
RGB_PCT_PATTERN = r"^\s*rgb\(\s*(\d{1,3}|\d{1,2}\.\d+)%\s*,\s*(\d{1,3}|\d{1,2}\.\d+)%\s*,\s*(\d{1,3}|\d{1,2}\.\d+)%\s*\)\s*$"
RGBA_PATTERN = r"^\s*rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(0|1|0\.\d+)\s*\)\s*$"
RGBA_PCT_PATTERN = r"^\s*rgba\(\s*(\d{1,3}|\d{1,2}\.\d+)%\s*,\s*(\d{1,3}|\d{1,2}\.\d+)%\s*,\s*(\d{1,3}|\d{1,2}\.\d+)%\s*,\s*(0|1|0\.\d+)\s*\)\s*$"
HEX_PATTERN = r"#([A-Fa-f0-9]{2})([A-Fa-f0-9]{2})([A-Fa-f0-9]{2})"
HEX3_PATTERN = r"#([A-Fa-f0-9])([A-Fa-f0-9])([A-Fa-f0-9])"
HSL_PATTERN = r"^\s*hsl\(\s*(\d{1,3})\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*\)\s*$"
HSLA_PATTERN = r"^\s*hsla\(\s*(\d{1,3})\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*,\s*(0|1|0\.\d+)\s*\)\s*$"


class Color(object):
    """
    Color conversion support class

    Example:

    .. code-block:: python

        from selenium.webdriver.support.color import Color

        print(Color.from_string('#00ff33').rgba)
        print(Color.from_string('rgb(1, 255, 3)').hex)
        print(Color.from_string('blue').rgba)
    """

    @staticmethod
    def from_string(str_):
        import re

        class Matcher(object):
            def __init__(self):
                self.match_obj = None

            def match(self, pattern, str_):
                self.match_obj = re.match(pattern, str_)
                return self.match_obj

            @property
            def groups(self):
                return () if self.match_obj is None else self.match_obj.groups()

        m = Matcher()

        if m.match(RGB_PATTERN, str_):
            return Color(*m.groups)
        elif m.match(RGB_PCT_PATTERN, str_):
            rgb = tuple([float(each) / 100 * 255 for each in m.groups])
            return Color(*rgb)
        elif m.match(RGBA_PATTERN, str_):
            return Color(*m.groups)
        elif m.match(RGBA_PCT_PATTERN, str_):
            rgba = tuple([float(each) / 100 * 255 for each in m.groups[:3]] + [m.groups[3]])
            return Color(*rgba)
        elif m.match(HEX_PATTERN, str_):
            rgb = tuple([int(each, 16) for each in m.groups])
            return Color(*rgb)
        elif m.match(HEX3_PATTERN, str_):
            rgb = tuple([int(each * 2, 16) for each in m.groups])
            return Color(*rgb)
        elif m.match(HSL_PATTERN, str_) or m.match(HSLA_PATTERN, str_):
            return Color._from_hsl(*m.groups)
        elif str_.upper() in Colors.keys():
            return Colors[str_.upper()]
        else:
            raise ValueError("Could not convert %s into color" % str_)

    @staticmethod
    def _from_hsl(h, s, l, a=1):
        h = float(h) / 360
        s = float(s) / 100
        l = float(l) / 100

        if s == 0:
            r = l
            g = r
            b = r
        else:
            luminocity2 = l * (1 + s) if l < 0.5 else l + s - l * s
            luminocity1 = 2 * l - luminocity2

            def hue_to_rgb(lum1, lum2, hue):
                if hue < 0.0:
                    hue += 1
                if hue > 1.0:
                    hue -= 1

                if hue < 1.0 / 6.0:
                    return (lum1 + (lum2 - lum1) * 6.0 * hue)
                elif hue < 1.0 / 2.0:
                    return lum2
                elif hue < 2.0 / 3.0:
                    return lum1 + (lum2 - lum1) * ((2.0 / 3.0) - hue) * 6.0
                else:
                    return lum1

            r = hue_to_rgb(luminocity1, luminocity2, h + 1.0 / 3.0)
            g = hue_to_rgb(luminocity1, luminocity2, h)
            b = hue_to_rgb(luminocity1, luminocity2, h - 1.0 / 3.0)

        return Color(round(r * 255), round(g * 255), round(b * 255), a)

    def __init__(self, red, green, blue, alpha=1):
        self.red = int(red)
        self.green = int(green)
        self.blue = int(blue)
        self.alpha = "1" if float(alpha) == 1 else str(float(alpha) or 0)

    @property
    def rgb(self):
        return "rgb(%d, %d, %d)" % (self.red, self.green, self.blue)

    @property
    def rgba(self):
        return "rgba(%d, %d, %d, %s)" % (self.red, self.green, self.blue, self.alpha)

    @property
    def hex(self):
        return "#%02x%02x%02x" % (self.red, self.green, self.blue)

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.rgba == other.rgba
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash((self.red, self.green, self.blue, self.alpha))

    def __repr__(self):
        return "Color(red=%d, green=%d, blue=%d, alpha=%s)" % (self.red, self.green, self.blue, self.alpha)

    def __str__(self):
        return "Color: %s" % self.rgba


# Basic, extended and transparent colour keywords as defined by the W3C HTML4 spec
# See http://www.w3.org/TR/css3-color/#html4
Colors = {
    "TRANSPARENT": Color(0, 0, 0, 0),
    "ALICEBLUE": Color(240, 248, 255),
    "ANTIQUEWHITE": Color(250, 235, 215),
    "AQUA": Color(0, 255, 255),
    "AQUAMARINE": Color(127, 255, 212),
    "AZURE": Color(240, 255, 255),
    "BEIGE": Color(245, 245, 220),
    "BISQUE": Color(255, 228, 196),
    "BLACK": Color(0, 0, 0),
    "BLANCHEDALMOND": Color(255, 235, 205),
    "BLUE": Color(0, 0, 255),
    "BLUEVIOLET": Color(138, 43, 226),
    "BROWN": Color(165, 42, 42),
    "BURLYWOOD": Color(222, 184, 135),
    "CADETBLUE": Color(95, 158, 160),
    "CHARTREUSE": Color(127, 255, 0),
    "CHOCOLATE": Color(210, 105, 30),
    "CORAL": Color(255, 127, 80),
    "CORNFLOWERBLUE": Color(100, 149, 237),
    "CORNSILK": Color(255, 248, 220),
    "CRIMSON": Color(220, 20, 60),
    "CYAN": Color(0, 255, 255),
    "DARKBLUE": Color(0, 0, 139),
    "DARKCYAN": Color(0, 139, 139),
    "DARKGOLDENROD": Color(184, 134, 11),
    "DARKGRAY": Color(169, 169, 169),
    "DARKGREEN": Color(0, 100, 0),
    "DARKGREY": Color(169, 169, 169),
    "DARKKHAKI": Color(189, 183, 107),
    "DARKMAGENTA": Color(139, 0, 139),
    "DARKOLIVEGREEN": Color(85, 107, 47),
    "DARKORANGE": Color(255, 140, 0),
    "DARKORCHID": Color(153, 50, 204),
    "DARKRED": Color(139, 0, 0),
    "DARKSALMON": Color(233, 150, 122),
    "DARKSEAGREEN": Color(143, 188, 143),
    "DARKSLATEBLUE": Color(72, 61, 139),
    "DARKSLATEGRAY": Color(47, 79, 79),
    "DARKSLATEGREY": Color(47, 79, 79),
    "DARKTURQUOISE": Color(0, 206, 209),
    "DARKVIOLET": Color(148, 0, 211),
    "DEEPPINK": Color(255, 20, 147),
    "DEEPSKYBLUE": Color(0, 191, 255),
    "DIMGRAY": Color(105, 105, 105),
    "DIMGREY": Color(105, 105, 105),
    "DODGERBLUE": Color(30, 144, 255),
    "FIREBRICK": Color(178, 34, 34),
    "FLORALWHITE": Color(255, 250, 240),
    "FORESTGREEN": Color(34, 139, 34),
    "FUCHSIA": Color(255, 0, 255),
    "GAINSBORO": Color(220, 220, 220),
    "GHOSTWHITE": Color(248, 248, 255),
    "GOLD": Color(255, 215, 0),
    "GOLDENROD": Color(218, 165, 32),
    "GRAY": Color(128, 128, 128),
    "GREY": Color(128, 128, 128),
    "GREEN": Color(0, 128, 0),
    "GREENYELLOW": Color(173, 255, 47),
    "HONEYDEW": Color(240, 255, 240),
    "HOTPINK": Color(255, 105, 180),
    "INDIANRED": Color(205, 92, 92),
    "INDIGO": Color(75, 0, 130),
    "IVORY": Color(255, 255, 240),
    "KHAKI": Color(240, 230, 140),
    "LAVENDER": Color(230, 230, 250),
    "LAVENDERBLUSH": Color(255, 240, 245),
    "LAWNGREEN": Color(124, 252, 0),
    "LEMONCHIFFON": Color(255, 250, 205),
    "LIGHTBLUE": Color(173, 216, 230),
    "LIGHTCORAL": Color(240, 128, 128),
    "LIGHTCYAN": Color(224, 255, 255),
    "LIGHTGOLDENRODYELLOW": Color(250, 250, 210),
    "LIGHTGRAY": Color(211, 211, 211),
    "LIGHTGREEN": Color(144, 238, 144),
    "LIGHTGREY": Color(211, 211, 211),
    "LIGHTPINK": Color(255, 182, 193),
    "LIGHTSALMON": Color(255, 160, 122),
    "LIGHTSEAGREEN": Color(32, 178, 170),
    "LIGHTSKYBLUE": Color(135, 206, 250),
    "LIGHTSLATEGRAY": Color(119, 136, 153),
    "LIGHTSLATEGREY": Color(119, 136, 153),
    "LIGHTSTEELBLUE": Color(176, 196, 222),
    "LIGHTYELLOW": Color(255, 255, 224),
    "LIME": Color(0, 255, 0),
    "LIMEGREEN": Color(50, 205, 50),
    "LINEN": Color(250, 240, 230),
    "MAGENTA": Color(255, 0, 255),
    "MAROON": Color(128, 0, 0),
    "MEDIUMAQUAMARINE": Color(102, 205, 170),
    "MEDIUMBLUE": Color(0, 0, 205),
    "MEDIUMORCHID": Color(186, 85, 211),
    "MEDIUMPURPLE": Color(147, 112, 219),
    "MEDIUMSEAGREEN": Color(60, 179, 113),
    "MEDIUMSLATEBLUE": Color(123, 104, 238),
    "MEDIUMSPRINGGREEN": Color(0, 250, 154),
    "MEDIUMTURQUOISE": Color(72, 209, 204),
    "MEDIUMVIOLETRED": Color(199, 21, 133),
    "MIDNIGHTBLUE": Color(25, 25, 112),
    "MINTCREAM": Color(245, 255, 250),
    "MISTYROSE": Color(255, 228, 225),
    "MOCCASIN": Color(255, 228, 181),
    "NAVAJOWHITE": Color(255, 222, 173),
    "NAVY": Color(0, 0, 128),
    "OLDLACE": Color(253, 245, 230),
    "OLIVE": Color(128, 128, 0),
    "OLIVEDRAB": Color(107, 142, 35),
    "ORANGE": Color(255, 165, 0),
    "ORANGERED": Color(255, 69, 0),
    "ORCHID": Color(218, 112, 214),
    "PALEGOLDENROD": Color(238, 232, 170),
    "PALEGREEN": Color(152, 251, 152),
    "PALETURQUOISE": Color(175, 238, 238),
    "PALEVIOLETRED": Color(219, 112, 147),
    "PAPAYAWHIP": Color(255, 239, 213),
    "PEACHPUFF": Color(255, 218, 185),
    "PERU": Color(205, 133, 63),
    "PINK": Color(255, 192, 203),
    "PLUM": Color(221, 160, 221),
    "POWDERBLUE": Color(176, 224, 230),
    "PURPLE": Color(128, 0, 128),
    "REBECCAPURPLE": Color(128, 51, 153),
    "RED": Color(255, 0, 0),
    "ROSYBROWN": Color(188, 143, 143),
    "ROYALBLUE": Color(65, 105, 225),
    "SADDLEBROWN": Color(139, 69, 19),
    "SALMON": Color(250, 128, 114),
    "SANDYBROWN": Color(244, 164, 96),
    "SEAGREEN": Color(46, 139, 87),
    "SEASHELL": Color(255, 245, 238),
    "SIENNA": Color(160, 82, 45),
    "SILVER": Color(192, 192, 192),
    "SKYBLUE": Color(135, 206, 235),
    "SLATEBLUE": Color(106, 90, 205),
    "SLATEGRAY": Color(112, 128, 144),
    "SLATEGREY": Color(112, 128, 144),
    "SNOW": Color(255, 250, 250),
    "SPRINGGREEN": Color(0, 255, 127),
    "STEELBLUE": Color(70, 130, 180),
    "TAN": Color(210, 180, 140),
    "TEAL": Color(0, 128, 128),
    "THISTLE": Color(216, 191, 216),
    "TOMATO": Color(255, 99, 71),
    "TURQUOISE": Color(64, 224, 208),
    "VIOLET": Color(238, 130, 238),
    "WHEAT": Color(245, 222, 179),
    "WHITE": Color(255, 255, 255),
    "WHITESMOKE": Color(245, 245, 245),
    "YELLOW": Color(255, 255, 0),
    "YELLOWGREEN": Color(154, 205, 50)
}
