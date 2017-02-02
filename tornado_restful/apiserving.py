# standard library imports
import logging
import inspect
import re
import traceback

# third-party imports
import tornado.web
from tornado import gen
from tornado.escape import json_decode

# application-specific imports

logger = logging.getLogger(__name__)


class RestResource(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        """Get method."""
        yield self._handle('GET')

    @gen.coroutine
    def post(self):
        """Post method."""
        # try:
        #     self.request.body = tornado.escape.json_decode(self.request.body)
        # except ValueError:
        #     raise tornado.web.HTTPError(400, 'Invalid JSON')
        yield self._handle('POST')

    @gen.coroutine
    def put(self):
        """Put method."""
        # try:
        #     self.request.body = tornado.escape.json_decode(self.request.body)
        # except ValueError:
        #     raise tornado.web.HTTPError(400, 'Invalid JSON')
        yield self._handle('PUT')

    @gen.coroutine
    def delete(self):
        """Delete method."""
        yield self._handle('DELETE')

    def write_error(self, status_code, **kwargs):
        """See Tornado doc"""
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            self.set_header('Content-Type', 'application/json')
            error = {'code': status_code, 'reason': self._reason}
            if 'exc_info' in kwargs:
                exception = kwargs['exc_info'][1]
                if isinstance(exception, tornado.web.HTTPError) and exception.log_message:  # noqa
                    error['message'] = exception.log_message % exception.args
            self.finish(error)

    @gen.coroutine
    def _handle(self, method):
        """Handle the request.

        This function handle the request for executing the right Rest service
        function.
        Args:
            method: string, Http request verb.
        """
        path_parts = self.request.path.split('/')
        endpoints_and_params = list(filter(lambda x: x != '', path_parts))

        resources_functions = self.get_resources_functions()
        # Get all http methods configured in the class RestHandler
        http_methods = set([func.method_info.http_method for func in resources_functions])  # noqa

        if method not in http_methods:
            raise tornado.web.HTTPError(405)

        # Find the right function to execute
        for func in resources_functions:
            method_info = func.method_info

            if method_info.http_method != method:
                continue

            # List of service endpoints
            endpoint = re.findall(
                r"(?<=/)\w+", method_info.get_path(self.api_info))
            #
            endpoint_from_request = list(filter(
                lambda x: x in path_parts, endpoint))

            if endpoint != endpoint_from_request:
                continue
            endpoint_params = re.findall(
                r"(?<={)\w+", method_info.get_path(self.api_info))

            if len(endpoint_params) + len(endpoint) != len(endpoints_and_params):  # noqa
                continue

            if (method_info.http_method in ['POST', 'PUT'] and
                    method_info.content_type == 'application/json'):
                try:
                    self.request.body = json_decode(self.request.body)
                except ValueError:
                    raise tornado.web.HTTPError(400, 'Invalid JSON')
            # try:
            self.set_header("Content-Type", 'application/json')
            params_values = self._find_params_value_of_url(
                endpoint, self.request.path)
            # p_values = self._convert_params_values(params_values, params_types)
            response = yield func(self, *params_values)

            if isinstance(response, dict):
                self.write(response)
                self.finish()
            elif isinstance(response, list):
                self.write({'items': response})
                self.finish()
            else:
                raise tornado.web.HTTPError(500, 'Response is not a json document')
            # except Exception:
            #     raise tornado.web.HTTPError(500)

    @classmethod
    def get_resources_functions(self):
        # Get all funcion configured in the class RestResource
        rest_handler_functions = inspect.getmembers(
            self, predicate=inspect.isroutine)
        # Return only function decorated with the method decorator
        resources_functions = [finstance for fname, finstance in rest_handler_functions if hasattr(finstance, 'method_info')]  # noqa
        return resources_functions

    @classmethod
    def get_rest_resources_paths(self):
        resources_functions = self.get_resources_functions()
        paths = []
        for func in resources_functions:
            paths.append(func.method_info.get_path(self.api_info))
        return paths

    def _find_params_value_of_url(self, services, url):
        """Find the values of path params """
        url_split = url.split('/')
        values = [
            item for item in url_split if item not in services and item != '']
        return values

    def _find_params_value_of_arguments(self, operation):
        values = []
        if len(self.request.arguments) > 0:
            a = operation._service_params
            b = operation._func_params
            params = [item for item in b if item not in a]
            for p in params:
                if p in self.request.arguments.keys():
                    v = self.request.arguments[p]
                    values.append(v[0])
                else:
                    values.append(None)
        elif (len(self.request.arguments) == 0 and
              len(operation._query_params) > 0):
            values = [None]*(len(operation._func_params) - len(operation._service_params))  # noqa
        return values

# 	def _convert_params_values(self, values_list, params_types):
# 		""" Converts the values to the specifics types """
# 		values = list()
# 		i = 0
# 		for v in values_list:
# 			if v != None:
# 				values.append(types.convert(v,params_types[i]))
# 			else:
# 				values.append(v)
# 			i+=1
# 		return values


class RestService(tornado.web.Application):
    """ Class to create Rest services in tornado web server """
    resource = None

    def __init__(self, rest_handlers, resource=None, handlers=None,
                 default_host="", transforms=None, **settings):
        _handlers = []
        self.resource = resource
        for rest_handler in rest_handlers:
            _handlers += self._rest_handler_to_tornado_handler(rest_handler)
        if handlers:
            _handlers += handlers
        logger.info(_handlers)
        tornado.web.Application.__init__(self, _handlers, default_host,
                                         transforms, **settings)

    def _rest_handler_to_tornado_handler(self, rest_handler):
        tornado_handlers = []
        paths = rest_handler.get_rest_resources_paths()
        for path in paths:
            s = re.sub(r"(?<={)\w+}", ".*", path).replace("{", "")
            o = re.sub(r"(?<=<)\w+", "", s).replace("<", "").replace(">", "").replace("&", "").replace("?", "")  # noqa
            tornado_handlers.append((o, rest_handler, self.resource))

        return tornado_handlers
