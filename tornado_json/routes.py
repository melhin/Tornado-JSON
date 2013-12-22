import pyclbr
import pkgutil
import importlib
from itertools import chain


def get_routes(package):
    """
    This will walk `package` and generates routes from any and all
    `APIHandler` and `ViewHandler` subclasses it finds. If you need to
    customize or remove any routes, you can do so to the list of
    returned routes that this generates.

    :type  package: package
    :param package: The package containing RequestHandlers to generate
        routes from
    :returns: List of routes for all submodules of `package`
    :rtype: [(url, RequestHandler), ... ]
    """
    return list(chain(*[get_module_routes(modname) for modname in
                        gen_submodule_names(package)]))


def gen_submodule_names(package):
    """Walk package and yield names of all submodules

    :type  package: package
    :param package: The package to get submodule names of
    :returns: Iterator that yields names of all submodules of `package`
    :rtype: Iterator that yields `str`
    """
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=package.__path__,
        prefix=package.__name__ + '.',
            onerror=lambda x: None):
        yield modname


def get_module_routes(
        module_name, custom_routes=None, exclusions=None
):
    """Create and return routes for module_name

    Routes are (url, RequestHandler) tuples

    :returns: list of routes for `module_name` with respect to `exclusions`
        and `custom_routes`. Returned routes are with URLs formatted such
        that they are forward-slash-separated by module/class level
        and end with the lowercase name of the RequestHandler (it will also
        remove 'handler' from the end of the name of the handler).
        For example, a requesthandler with the name
        `helloworld.api.HelloWorldHandler` would be assigned the url
        `/api/helloworld`
    :rtype: [(url, RequestHandler), ... ]
    :type  module_name: str
    :param module_name: Name of the module to get routes for
    :type  custom_routes: [(str, RequestHandler), ... ]
    :param custom_routes: List of routes that have custom URLs and therefore
        should be automagically generated
    :type  exclusions: [str, str, ...]
    :param exclusions: List of RequestHandler names that routes should not be
        generated for
    """
    if not custom_routes:
        custom_routes = []
    if not exclusions:
        exclusions = []

    # Import module so we can get its request handlers
    module = importlib.import_module(module_name)

    # Generate list of RequestHandler names in custom_routes
    custom_routes_s = [c.__name__ for r, c in custom_routes]

    # rhs is a dict of {classname: pyclbr.Class} key, value pairs
    rhs = pyclbr.readmodule(module_name)

    # You better believe this is a list comprehension
    auto_routes = [
        # URL, requesthandler tuple
        (
            "/{}/{}".format("/".join(module_name.split(".")[1:]),
                            k.lower().replace('handler', '', 1) if
                            k.lower().endswith('handler') else k.lower()),
            getattr(module, k)
        )
        # foreach classname, pyclbr.Class in rhs
        for k, v in rhs.iteritems()
        # Only add the pair to auto_routes if:
        #    * the superclass is in the list of supers we want
        #    * the requesthandler isn't already paired in custom_routes
        #    * the requesthandler isn't manually excluded
        if any(
            True for s in v.super if s in ["ViewHandler", "APIHandler"]
        )
        and k not in (custom_routes_s + exclusions)
    ]

    routes = auto_routes + custom_routes
    return routes
