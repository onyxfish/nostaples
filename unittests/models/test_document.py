import unittest

from mock import Mock

from application import Application
from models.document import DocumentModel
from models.page import PageModel

class TestDocumentModel(unittest.TestCase):
    def setUp(self):
        self.mock_application = Mock(spec=Application)
        self.document_model = DocumentModel(self.mock_application)
    
    def tearDown(self):
        self.mock_application = None
        self.document_model = None
    
    def test_append(self):
        self.assertEqual(self.document_model.count, 0)
        
        self.document_model.append(PageModel())
        self.document_model.append(PageModel())
        p = PageModel()
        self.document_model.append(p)
        
        self.assertEqual(self.document_model.count, 3)
        self.assertEqual(self.document_model[2][0], p)
        
    def test_prepend(self):
        self.assertEqual(self.document_model.count, 0)
        
        self.document_model.prepend(PageModel())
        self.document_model.prepend(PageModel())
        p = PageModel()
        self.document_model.prepend(p)
        
        self.assertEqual(self.document_model.count, 3)
        self.assertEqual(self.document_model[0][0], p)
        
    def test_insert(self):
        self.assertEqual(self.document_model.count, 0)
        
        p0 = PageModel()
        p1 = PageModel()
        p2 = PageModel()
        
        self.document_model.insert(0, p2)
        self.document_model.insert(0, p0)
        self.document_model.insert(1, p1)
        
        self.assertEqual(self.document_model.count, 3)
        self.assertEqual(self.document_model[0][0], p0)
        self.assertEqual(self.document_model[1][0], p1)
        self.assertEqual(self.document_model[2][0], p2)
        
    def test_insert_before(self):
        self.assertEqual(self.document_model.count, 0)
        
        p0 = PageModel()
        p1 = PageModel()
        p2 = PageModel()
                
        iter = self.document_model.get_iter_root()
        self.document_model.insert_before(iter, p2)
        iter = self.document_model.get_iter(0)
        self.document_model.insert_before(iter, p0)
        iter = self.document_model.get_iter(1)
        self.document_model.insert_before(iter, p1)
        
        self.assertEqual(self.document_model.count, 3)
        self.assertEqual(self.document_model[0][0], p0)
        self.assertEqual(self.document_model[1][0], p1)
        self.assertEqual(self.document_model[2][0], p2)
        
    def test_insert_after(self):
        self.assertEqual(self.document_model.count, 0)
        
        p0 = PageModel()
        p1 = PageModel()
        p2 = PageModel()
                
        iter = self.document_model.get_iter_root()
        self.document_model.insert_after(iter, p0)
        iter = self.document_model.get_iter(0)
        self.document_model.insert_after(iter, p2)
        iter = self.document_model.get_iter(0)
        self.document_model.insert_after(iter, p1)
        
        self.assertEqual(self.document_model.count, 3)
        self.assertEqual(self.document_model[0][0], p0)
        self.assertEqual(self.document_model[1][0], p1)
        self.assertEqual(self.document_model[2][0], p2)
        
    def test_remove(self):
        self.assertEqual(self.document_model.count, 0)
        
        p0 = PageModel()
        p1 = PageModel()
        p2 = PageModel()
                
        self.document_model.append(p0)
        self.document_model.append(p1)
        self.document_model.append(p2)
        
        iter = self.document_model.get_iter(1)
        self.document_model.remove(iter)
        
        self.assertEqual(self.document_model.count, 2)
        self.assertEqual(self.document_model[0][0], p0)
        self.assertEqual(self.document_model[1][0], p2)
        
    def test_clear(self):
        self.assertEqual(self.document_model.count, 0)
        
        p0 = PageModel()
        p1 = PageModel()
        p2 = PageModel()
                
        self.document_model.append(p0)
        self.document_model.append(p1)
        self.document_model.append(p2)
        
        self.document_model.clear()
        
        self.assertEqual(self.document_model.count, 0)
        self.assertRaises(ValueError, self.document_model.get_iter, 0)