import unittest

import Image, ImageDraw

from nostaples.utils.graphics import *

class TestGraphics(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGB', (400, 400))
        draw = ImageDraw.Draw(self.image)
        
        draw.line((0, 0) + self.image.size, fill=128)
        draw.line((0, self.image.size[1], self.image.size[0], 0), fill=128)
        del draw
    
    def tearDown(self):
        self.image = None
    
    def test_conversion_sanity(self):
        pixbuf = convert_pil_image_to_pixbuf(self.image)
        image = convert_pixbuf_to_pil_image(pixbuf)
        
        self.assertEquals(self.image.tostring(), image.tostring())