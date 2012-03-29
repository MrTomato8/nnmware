from functools import wraps

from django.shortcuts import render_to_response, render
from django.template import RequestContext

from nnmware.core.http import JSONResponse


def stream(func):
    """
    Stream decorator to be applied to methods of an ``ActionManager`` subclass

    Syntax::

        from nnmware.core.decorators import stream
        from nnmware.core.managers import ActionManager

        class MyManager(ActionManager):
            @stream
            def foobar(self, ...):
                ...

    """
    @wraps(func)
    def wrapped(manager, *args, **kwargs):
        offset, limit = kwargs.pop('_offset', None), kwargs.pop('_limit', None)
        try:
            return func(manager, *args, **kwargs)[offset:limit]\
                .fetch_generic_relations()
        except AttributeError:
            return func(manager, *args, **kwargs).fetch_generic_relations()
    return wrapped


def ajax_request(func):
    """
    Checks request.method is POST. Return error in JSON in other case.

    If view returned dict, returns JSONResponse with this dict as content.
    """

    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            response = func(request, *args, **kwargs)
        else:
            response = {'error': {'type': 403,
                        'message': 'Accepts only POST request'}}
        if isinstance(response, dict):
            return JSONResponse(response)
        else:
            return response

    return wrapper