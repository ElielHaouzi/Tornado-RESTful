# standard library imports
# from concurrent.futures import ThreadPoolExecutor
# import time
# import logging

# third-party imports
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
# from tornado import gen
from tornado.options import define, options
import tornado.web

# application-specific imports
import tornado_extensions
import api_config

# from token_service import Token as TokenService

define("port", default=5555, help="run on the given port", type=int)


class Application(tornado_extensions.RestService):
    def __init__(self):
        an_api = api_config.api(name='atl', version='v1')
        check = an_api.api_class(resource_name='test', path='epg')(CheckHandler)
        handlers = [check]
        settings = dict(
            debug=True
        )
        super(Application, self).__init__(handlers, **settings)


class CheckHandler(tornado_extensions.RestResource):
    @api_config.method(name='list', path='check/{check_id}/app/{id}', http_method='GET')
    def test(self, a, b):
        # print check_id
        # print id
        return {'hello': a, 'world': b}

if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = HTTPServer(Application())
    http_server.listen(options.port)
    IOLoop.current().start()
