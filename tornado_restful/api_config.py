# standard library imports
import re

# third-party imports

# application-specific imports


class _ApiInfo(object):
    """Configurable attributes of an API.

    A structured data object used to store API information associated with each
    remote.Service-derived class that implements an API.  This stores
    properties that could be different for each class (such as the path or
    collection/resource name), as well as properties common to all classes in
    the API (such as API name and version).
    """
    def __init__(self, common_info, resource_name=None, path=None,
                 auth_level=None):
        """Constructor for _ApiInfo.

        Args:
            common_info: _ApiDecorator.__ApiCommonInfo, Information
              that's common for all classes that implement an API.
            resource_name: string, The collection that the annotated class will
              implement in the API. (Default: None)
            path: string, Base request path for all methods in this API.
              (Default: None)
            auth_level: enum from AUTH_LEVEL, Frontend authentication level.
              (Default: None)
        """
        # _CheckType(resource_name, basestring, 'resource_name')
        # _CheckType(path, basestring, 'path')
        # _CheckEnum(auth_level, AUTH_LEVEL, 'auth_level')

        self.__common_info = common_info
        self.__resource_name = resource_name
        self.__path = path
        self.__auth_level = auth_level

    def is_same_api(self, other):
        """Check if this implements the same API as another
        _ApiInfo instance.
        """
        if not isinstance(other, _ApiInfo):
            return False

        return self.__common_info is other.__common_info

    @property
    def name(self):
        """Name of the API."""
        return self.__common_info.name

    @property
    def version(self):
        """Version of the API."""
        return self.__common_info.version

    @property
    def auth_level(self):
        """Enum from AUTH_LEVEL specifying the frontend authentication
        level.
        """
        if self.__auth_level is not None:
            return self.__auth_level
        return self.__common_info.auth_level

    @property
    def resource_name(self):
        """Resource name for the class this decorates."""
        return self.__resource_name

    @property
    def path(self):
        """Base path prepended to any method paths in the class this
        decorates.
        """
        return self.__path


class _ApiDecorator(object):
    """Decorator for single- or multi-class APIs.

    An instance of this class can be used directly as a decorator for a
    single-class API.  Or call the api_class() method to decorate a multi-class
    API.
    """
    def __init__(self, name, version, auth_level=None):
        """Constructor for _ApiDecorator.

        Args:
          name: string, Name of the API.
          version: string, Version of the API.
          auth_level: enum from AUTH_LEVEL, Frontend authentication level.
        """
        self.__common_info = self.__ApiCommonInfo(
            name, version, auth_level=auth_level)
        self.__classes = []

    class __ApiCommonInfo(object):
        """API information that's common among all classes that implement an API.

        When a remote.Service-derived class implements part of an API, there is
        some common information that remains constant across all such classes
        that implement the same API.  This includes things like name, version,
        hostname, and so on.  __ApiComminInfo stores that common information,
        and a single __ApiCommonInfo instance is shared among all classes that
        implement the same API, guaranteeing that they share the same common
        information.
        """
        def __init__(self, name, version, auth_level=None):
            """Constructor for _ApiCommonInfo.

            Args:
              name: string, Name of the API.
              version: string, Version of the API.
              auth_level: enum from AUTH_LEVEL, Frontend authentication level.
            """
            # _CheckType(name, basestring, 'name', allow_none=False)
            # _CheckType(version, basestring, 'version', allow_none=False)
            # _CheckEnum(auth_level, AUTH_LEVEL, 'auth_level')
            self.__name = name
            self.__version = version
            self.__auth_level = auth_level

        @property
        def name(self):
            """Name of the API."""
            return self.__name

        @property
        def version(self):
            """Version of the API."""
            return self.__version

        @property
        def auth_level(self):
            """Enum from AUTH_LEVEL specifying default frontend auth level."""
            return self.__auth_level

    def __call__(self, service_class):
        """Decorator for service class that configures server.

        Args:
            service_class: remote.Service class, ProtoRPC service
                class being wrapped.

        Returns:
            Same class with API attributes assigned in api_info.
        """
        return self.api_class()(service_class)

    def api_class(self, resource_name=None, path=None, auth_level=None):
        """Get a decorator for a class that implements an API.

        This can be used for single-class or multi-class implementations.
        It's used implicitly in simple single-class APIs that only
        use @api directly.

        Args:
            resource_name: string, Resource name for the class this
                decorates. (Default: None)
            path: string, Base path prepended to any method paths in the
                class this decorates. (Default: None)
            auth_level: enum from AUTH_LEVEL, Frontend authentication
                level. (Default: None)

            Returns:
                A decorator function to decorate a class that implements
                an API.
        """
        def apiserving_api_decorator(api_class):
            """Decorator for service class that configures server.

            Args:
                api_class: remote.Service class, ProtoRPC service class
                    being wrapped.
            Returns:
                Same class with API attributes assigned in api_info.
            """
            self.__classes.append(api_class)
            api_class.api_info = _ApiInfo(
                self.__common_info, resource_name=resource_name,
                path=path, auth_level=auth_level)
            return api_class

        return apiserving_api_decorator

        def get_api_classes(self):
            """Get the list of remote.Service classes that implement
            this API.
            """
            return self.__classes


def api(name, version, auth_level=None):
    """Decorate a Service class for use by the framework above.

    This decorator can be used to specify an API name and version for your API.

    Sample usage (python 2.7):
      @endpoints.api(name='guestbook', version='v0.2',
                     description='Guestbook API')
      class PostService(remote.Service):
        ...

    Sample usage if multiple classes implement one API:
      api_root = endpoints.api(name='library', version='v1.0')

      @api_root.api_class(resource_name='shelves')
      class Shelves(remote.Service):
        ...

      @api_root.api_class(resource_name='books', path='books')
      class Books(remote.Service):
        ...

    Args:
      name: string, Name of the API.
      version: string, Version of the API.
      auth_level: enum from AUTH_LEVEL, frontend authentication level.

    Returns:
      Class decorated with api_info attribute, an instance of ApiInfo.
    """
    return _ApiDecorator(name, version, auth_level=auth_level)


class _MethodInfo(object):
    """Configurable attributes of an API method.

    Consolidates settings from @method decorator and/or any settings that were
    calculating from the ProtoRPC method name, so they only need to be
    calculated once.
    """
    def __init__(self, name=None, path=None, http_method=None,
                 auth_level=None, content_type=None):
        """Constructor.

        Args:
          name: string, Name of the method, prepended with <apiname>. to make
            it unique.
          path: string, Path portion of the URL to the method, for RESTful
          methods. http_method: string, HTTP method supported by the method.
          auth_level: enum from AUTH_LEVEL, Frontend auth level for the method.
        """
        self.__name = name
        self.__path = path
        self.__http_method = http_method
        self.__auth_level = auth_level
        self.__content_type = content_type

    def __safe_name(self, method_name):
        """Restrict method name to a-zA-Z0-9_, first char lowercase."""
        safe_name = re.sub('[^\.a-zA-Z0-9_]', '', method_name)
        safe_name = safe_name.lstrip('_')
        return safe_name[0:1].lower() + safe_name[1:]

    @property
    def name(self):
        """Method name as specified in decorator or derived."""
        return self.__name

    def get_path(self, api_info):
        """Get the path portion of the URL to the method (for RESTful methods).

        Request path can be specified in the method, and it could have a base
        path prepended to it.

        Args:
          api_info: API information for this API, possibly including a base
            path. This is the api_info property on the class that's been
            annotated for this API.

        Returns:
          This method's request path (not including the http://.../_ah/api/
           prefix).

        Raises:
          ApiConfigurationError: If the path isn't properly formatted.
        """
        path = self.__path or ''
        if path and path[0] == '/':
            path = path[1:]

        path_dict = {
            'api_name': api_info.name,
            'api_version': api_info.version
        }

        if not api_info.path:
            path_dict['api_path'] = ''
        else:
            path_dict['api_path'] = api_info.path if api_info.path[-1] == '/' else '%s/' % (api_info.path)  # noqa

        path_dict['path'] = path
        path = '/{api_name}/{api_version}/{api_path}{path}'.format(**path_dict)

        for part in path.split('/'):
            if part and '{' in part and '}' in part:
                if re.match('^{[^{}]+}$', part) is None:
                    raise ApiConfigurationError(
                        'Invalid path segment: %s (part of %s)' % (part, path))
        return path

    @property
    def http_method(self):
        """HTTP method supported by the method (e.g. GET, POST)."""
        return self.__http_method

    @property
    def auth_level(self):
        """Enum from AUTH_LEVEL specifying default frontend auth level."""
        return self.__auth_level

    @property
    def content_type(self):
        return self.__content_type

    def method_id(self, api_info):
        """Computed method name."""
        if api_info.resource_name:
            resource_part = '.%s' % self.__safe_name(api_info.resource_name)
        else:
            resource_part = ''
        return '%s%s.%s' % (self.__safe_name(api_info.name), resource_part,
                            self.__safe_name(self.name))


def method(
        name=None, path=None, http_method='POST', auth_level=None,
        content_type='application/json'):
    """Decorate a Method for use by the framework above.

    This decorator can be used to specify a method name, path, http method,
    cache control, scopes, audiences, client ids and auth_level.

    Sample usage:
    @api_config.method(RequestMessage, ResponseMessage,
                       name='insert', http_method='PUT')
    def greeting_insert(request):
      ...
      return response

    Args:
    name: string, Name of the method, prepended with <apiname>. to make it
      unique. (Default: python method name)
    path: string, Path portion of the URL to the method, for RESTful methods.
    http_method: string, HTTP method supported by the method. (Default: POST)
    auth_level: enum from AUTH_LEVEL, Frontend auth level for the method.

    Returns:
    'apiserving_method_wrapper' function.

    """

    DEFAULT_HTTP_METHOD = 'POST'
    DEFAULT_CONTENT_TYPE = 'application/json'

    def apiserving_method_decorator(api_method):
        """Decorator for ProtoRPC method that configures Google's API server.

        Args:
          api_method: Original method being wrapped.

        Returns:
          Function responsible for actual invocation.
          Assigns the following attributes to invocation function:
            remote: Instance of RemoteInfo, contains remote method information.
            method_info: Instance of _MethodInfo, api method configuration.
          It is also assigned attributes corresponding to the aforementioned
          kwargs.
        """
        def invoke_remote(*args, **kwargs):
            return api_method(*args, **kwargs)

        invoke_remote.method_info = _MethodInfo(
            name=name or api_method.__name__, path=path or api_method.__name__,
            http_method=http_method or DEFAULT_HTTP_METHOD,
            auth_level=auth_level,
            content_type=content_type or DEFAULT_CONTENT_TYPE)
        invoke_remote.__name__ = invoke_remote.method_info.name

        return invoke_remote

    # _CheckEnum(auth_level, AUTH_LEVEL, 'auth_level')
    return apiserving_method_decorator
