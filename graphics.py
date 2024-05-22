import gc
import displayio
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.bitmap_label import Label
from adafruit_display_text import wrap_text_to_lines

import adafruit_imageload

# Adapted from https://github.com/adafruit/Adafruit_CircuitPython_PortalBase

class Graphics:
    def __init__(self, display, default_bg=0x000000, scale=1, debug=False):

        self._debug = debug
        self.display = display

        # Font Cache
        self._fonts = {}
        self._text = []

        if self._debug:
            print("Init display")
        self.splash = displayio.Group(scale=scale)
        self._qr_group = None
        if self._debug:
            print("Init background")
        self._bg_group = displayio.Group()
        self.splash.append(self._bg_group)

        # set the default background
        if default_bg is not None:
            # self.display.show(self.splash)
            self.display.root_group = self.splash
            self.set_background(default_bg)

        gc.collect()

    def set_background(self, file_or_color, position=None):
        while self._bg_group:
            self._bg_group.pop()

        if not position:
            position = (0, 0)  # default in top corner

        if not file_or_color:
            return  # we're done, no background desired
        if isinstance(file_or_color, str):  # its a filenme:
            bitmap, palette = adafruit_imageload.load(file_or_color, bitmap=displayio.Bitmap, palette=displayio.Palette)
            self._bg_sprite = displayio.TileGrid(
                bitmap,
                pixel_shader=palette,
                x=position[0],
                y=position[1],
            )
        elif isinstance(file_or_color, int):
            # Make a background color fill
            color_bitmap = displayio.Bitmap(self.display.width, self.display.height, 1)
            color_palette = displayio.Palette(1)
            color_palette[0] = file_or_color
            self._bg_sprite = displayio.TileGrid(
                color_bitmap,
                pixel_shader=color_palette,
                x=position[0],
                y=position[1],
            )
        else:
            raise RuntimeError("Unknown type of background")
        self._bg_group.append(self._bg_sprite)
        gc.collect()

    def add_qrcode(
        self, qrcode, *, qr_size=1, x=0, y=0, qr_color=0x000000, qr_anchor_point=(0.0, 0.0)
    ):
        # monochrome (2 color) palette
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = qr_color

        # bitmap the size of the matrix, plus border, monochrome (2 colors)
        qr_bitmap = displayio.Bitmap(
            qrcode.matrix.width + 2, qrcode.matrix.height + 2, 2
        )
        for i in range(qr_bitmap.width * qr_bitmap.height):
            qr_bitmap[i] = 0

        # transcribe QR code into bitmap
        for xx in range(qrcode.matrix.width):
            for yy in range(qrcode.matrix.height):
                qr_bitmap[xx + 1, yy + 1] = 1 if qrcode.matrix[xx, yy] else 0

        # display the QR code
        qr_sprite = displayio.TileGrid(qr_bitmap, pixel_shader=palette)

        # Adjust group position based on anchor point
        qr_width_with_scale = qr_bitmap.width * qr_size
        qr_height_with_scale = qr_bitmap.height * qr_size
        anchor_x = x - qr_width_with_scale * qr_anchor_point[0]
        anchor_y = y - qr_height_with_scale * qr_anchor_point[1]

        if self._qr_group:
            try:
                self._qr_group.pop()
            except IndexError:  # if group is empty
                pass
        else:
            self._qr_group = displayio.Group()
            self.splash.append(self._qr_group)
        self._qr_group.scale = qr_size
        self._qr_group.x = int(anchor_x)
        self._qr_group.y = int(anchor_y)
        self._qr_group.append(qr_sprite)
    
    def _load_font(self, font):
        if font is terminalio.FONT:
            if "terminal" not in self._fonts:
                self._fonts["terminal"] = terminalio.FONT
            return "terminal"
        if font not in self._fonts:
            self._fonts[font] = bitmap_font.load_font(font)
        return font

    @staticmethod
    def wrap_nicely(string, max_chars):
        return wrap_text_to_lines(string, max_chars)
        
    def add_text(
        self,
        text_position=(0, 0),
        text_font=terminalio.FONT,
        text_color=0x000000,
        text_wrap=0,
        text_maxlen=0,
        text_transform=None,
        text_scale=1,
        line_spacing=1.25,
        text_anchor_point=(0, 0.5),
        is_data=True,
        text=None,
    ):
        if not text_wrap:
            text_wrap = 0
        if not text_maxlen:
            text_maxlen = 0
        if not text_transform:
            text_transform = None
        if not isinstance(text_scale, (int, float)) or text_scale < 1:
            text_scale = 1
        if not isinstance(text_anchor_point, (tuple, list)):
            text_anchor_point = (0, 0.5)
        if not 0 <= text_anchor_point[0] <= 1 or not 0 <= text_anchor_point[1] <= 1:
            raise ValueError("Text anchor point values should be between 0 and 1.")
        text_scale = round(text_scale)
        gc.collect()

        if self._debug:
            print("Init text area")
        text_field = {
            "label": None,
            "font": self._load_font(text_font),
            "color": text_color,
            "position": text_position,
            "wrap": text_wrap,
            "maxlen": text_maxlen,
            "transform": text_transform,
            "scale": text_scale,
            "line_spacing": line_spacing,
            "anchor_point": text_anchor_point,
            "is_data": bool(is_data),
        }
        self._text.append(text_field)

        text_index = len(self._text) - 1
        if text is not None:
            self.set_text(text, text_index)

        return text_index

    def remove_all_text(self, clear_font_cache=False):
        # Remove the labels
        for i in range(len(self._text)):
            self.set_text("", i)
        # Remove the data
        self._text = []
        if clear_font_cache:
            self._fonts = {}
        gc.collect()

    def remove_all_qr(self):
        if self._qr_group and self._qr_group in self.splash:
            self.splash.remove(self._qr_group)
        self._qr_group = None
        gc.collect()
        return

    def set_text(self, val, index=0):
        # Make sure at least a single label exists
        if not self._text:
            self.add_text()
        string = str(val)
        if self._text[index]["maxlen"] and len(string) > self._text[index]["maxlen"]:
            # too long! shorten it
            if len(string) >= 3:
                string = string[: self._text[index]["maxlen"] - 3] + "..."
            else:
                string = string[: self._text[index]["maxlen"]]
        index_in_splash = None

        if len(string) > 0 and self._text[index]["wrap"]:
            if self._debug:
                print("Wrapping text with length of", self._text[index]["wrap"])
            lines = self.wrap_nicely(string, self._text[index]["wrap"])
            string = "\n".join(lines)

        if self._text[index]["label"] is not None:
            if self._debug:
                print("Replacing text area with :", string)
            index_in_splash = self.splash.index(self._text[index]["label"])
        elif self._debug:
            print("Creating text area with :", string)
        if len(string) > 0:
            if self._text[index]["label"] is None:
                self._text[index]["label"] = Label(
                    self._fonts[self._text[index]["font"]],
                    text=string,
                    scale=self._text[index]["scale"],
                )
                if index_in_splash is not None:
                    self.splash[index_in_splash] = self._text[index]["label"]
                else:
                    self.splash.append(self._text[index]["label"])
            else:
                self._text[index]["label"].text = string
            self._text[index]["label"].color = self._text[index]["color"]
            self._text[index]["label"].anchor_point = self._text[index]["anchor_point"]
            self._text[index]["label"].anchored_position = self._text[index]["position"]
            self._text[index]["label"].line_spacing = self._text[index]["line_spacing"]
        elif index_in_splash is not None:
            self._text[index]["label"] = None

        # Remove the label from splash
        if index_in_splash is not None and self._text[index]["label"] is None:
            del self.splash[index_in_splash]
        gc.collect()

    def preload_font(self, glyphs=None, index=0):
        if not glyphs:
            glyphs = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-!,. \"'?!"
        print("Preloading font glyphs:", glyphs)
        if self._fonts[self._text[index]["font"]] is not terminalio.FONT:
            self._fonts[self._text[index]["font"]].load_glyphs(glyphs)

    def set_text_color(self, color, index=0):
        if self._text[index]:
            color = self.html_color_convert(color)
            self._text[index]["color"] = color
            if self._text[index]["label"] is not None:
                self._text[index]["label"].color = color