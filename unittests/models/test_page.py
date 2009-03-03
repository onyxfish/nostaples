import os
import unittest

from mock import Mock

import Image, ImageDraw

from nostaples.models.page import PageModel

class TestPageModel(unittest.TestCase):
    TEST_PAGE_WIDTH = 93
    TEST_PAGE_HEIGHT = 266
    
    def setUp(self):    
        self.mock_application = Mock(spec=Application)
        
        image = Image.new('RGB', (self.TEST_PAGE_WIDTH, self.TEST_PAGE_HEIGHT))
        draw = ImageDraw.Draw(image)
        
        draw.line((0, 0) + image.size, fill=128)
        draw.line((0, image.size[1], image.size[0], 0), fill=128)
        del draw
        
        image.save('TestPageModel.png')
        
        self.page_model = PageModel(self.mock_application, 'TestPageModel.png')
        
    def tearDown(self):
        os.remove('TestPageModel.png')
    
    def test_width(self):
        self.assertEquals(self.page_model.width, self.TEST_PAGE_WIDTH)
        
    def test_height(self):
        self.assertEquals(self.page_model.height, self.TEST_PAGE_HEIGHT)