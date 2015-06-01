import unittest
from pyramid.paster import get_app
from webtest import TestApp

class AllTests(unittest.TestCase):
    def test_login(self):
        app = get_app('testing.ini')
        test_app = TestApp(app)
        resp = test_app.get('/login')
        self.assertEqual(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()

"""
from pyramid import testing
from webtest import TestApp
from paste.deploy import loadapp
from paste.deploy.loadwsgi import appconfig
from pyramid.config import Configurator
import unittest, os, transaction, pyramid.registry, pyramid.request

ini = 'config:' + os.path.join(os.path.dirname(__file__), '../', 'development.ini')
settings = appconfig(ini, relative_to=".")

# ini = 'config:' + os.path.join('/', 'development.ini')
# settings = appconfig(ini, relative_to=".")

class AllTests(unittest.TestCase):

    def setup(self):
        reg = pyramid.registry.Registry('testing')
        wsgiapp = self._load_wsgiapp()
        self.config = Configurator(registry=wsgiapp.registry)
        self.config.setup_registry(settings=settings)
        self.app = TestApp(wsgiapp, extra_environ={})

    def tearDown(self):
        #self.config.end()
        pass

    def _load_wsgiapp(self):
        wsgiapp = loadapp(ini)
        return wsgiapp

    def _get_app_url(self):
        return 'http://localhost:5000'

    def test_login(self):
        res = self.app.get('/login', status=200)
        self.assertTrue(res.status_code==200)

if __name__ == '__main__':
    unittest.main()
"""

"""
import unittest

from pyramid import testing
from pyramid.paster import get_app


class ViewTests(unittest.TestCase):
    def setUp(self):
        app = get_app('development.ini')
        self.config = testing.setUp(registry=app)
        self.config.include('pyramid_mailer.testing')

    def tearDown(self):
        testing.tearDown()
    
    def test_login(self):
        from .views import login
        request = testing.DummyRequest()
        response = login(request)
        self.assertEqual(response.status, '200 OK')
"""    

