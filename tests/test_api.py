from unittest import main, TestCase
from flask.ext.webtest import TestApp
import json
from api import app

class ApiTests(TestCase):

    def setUp(self):
        self.app = app
        self.w = TestApp(self.app)

    def test_cassini(self):
        r = self.w.get('/Cassini')
        self.assertFalse(r.flashes)

    def test_cassini_mass(self):
        r = self.w.get('/Cassini/mass')
        self.assertFalse(r.flashes)
