from copy import copy
import operator

from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, Http404
)
from django.utils import simplejson
from django.utils.functional import update_wrapper
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q

class classonlymethod(classmethod):
    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError("This method is available only on the autocomplete class.")
        return super(classonlymethod, self).__get__(instance, owner)


class BaseAutocomplete(object):
    """
    Encapsulates the basic options for doing an autocomplete search for a ``Model``.
    """
    def __init__(self, **kwargs):
        self._load_config_values(kwargs,
            lookup='startswith',
            mimetype='text/javascript',
            query_param='q',
            model=None,
            queryset=None,
            limit=None,
            search_fields=None,
            allowed_methods=('GET',)
        )
        if kwargs:
            raise TypeError("__init__() got an unexpected keyword argument '%s'" % iter(kwargs).next())

    def get_query_param(self):
        """
        Get the query from the request.
        """
        return self.request.REQUEST.get(self.query_param)

    def get_lookup(self, field):
        """
        Get the query lookup.
        """
        return self.lookup

    def get_search_fields(self):
        """
        Get the model fields to search.
        """
        if not self.search_fields:
            raise ImproperlyConfigured("A list of search fields must be specified")
        return self.search_fields

    def get_queryset(self):
        """
        Get a ``QuerySet`` to perform the search query on.
        """
        if self.queryset is not None:
            return self.queryset
        if self.model is None:
            raise ImproperlyConfigured("A queryset or model must be specified.")
        return self.model._default_manager.all()

    def get_limit(self):
        """
        Get the number of results to include in the response.
        """
        return self.limit

    def get_result_queryset(self):
        """
        Get the ``QuerySet`` of results for the current query.
        """
        query_param = self.get_query_param()
        queryset = self.get_queryset()
        if not query_param:
            return queryset.none()
        search_fields = self.get_search_fields()
        query_parts = [Q(**{"%s__%s" % (field, self.get_lookup(field)): query_param}) for field in search_fields]
        query = reduce(operator.or_, query_parts)
        results = queryset.filter(query)
        limit = self.get_limit()
        if limit is not None:
            results = results[:limit]
        return results

    def is_authorized(self):
        """
        Is the requesting user authorized to use this autocomplete?
        """
        return True

    def get_mimetype(self):
        """
        Get the response MIME type.
        """
        return self.mimetype

    def prepare_results(self, results):
        """
        Format the results for serialization.
        """
        raise NotImplementedError

    def serialize_results(self, results):
        """
        Serialize the result ``QuerySet`` for use in the response.
        """
        results = self.prepare_results(results)
        return simplejson.dumps(results, cls=DjangoJSONEncoder)

    def get_response(self, results):
        """
        Get the response object for the query.
        """
        response = HttpResponse(mimetype=self.get_mimetype())
        response.write(self.serialize_results(results))
        return response

    def __call__(self, request):
        """
        Handle an autocomplete request.
        """
        self.request = request
        if request.method not in self.allowed_methods:
            return HttpResponseNotAllowed(self.allowed_methods)
        if not self.is_authorized():
            return HttpResponseForbidden()
        results = self.get_result_queryset()
        return self.get_response(results)

    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        def view(request):
            self = cls(**initkwargs)
            return self(request)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls, assigned=())
        return view

    def _load_config_values(self, initkwargs, **defaults):
        """
        Set on self some config values possibly taken from __init__, or
        attributes on self.__class__, or some default.
        """
        for k in defaults:
            default = getattr(self.__class__, k, defaults[k])
            value = initkwargs.pop(k, default)
            setattr(self, k, value)


class ObjectAutocomplete(BaseAutocomplete):
    """
    Serializes the search results into a list of dictionaries
    containing the specified ``response_fields``.
    """
    def __init__(self, **kwargs):
        self._load_config_values(kwargs,
            response_fields=None
        )
        super(ObjectAutocomplete, self).__init__(**kwargs)

    def get_response_fields(self):
        """
        Get the model fields to serialize into the response.
        """
        return self.response_fields

    def prepare_results(self, results):
        """
        Get a list of dictionaries for the results.
        """
        response_fields = self.get_response_fields()
        if not response_fields:
            raise ImproperlyConfigured("A list of response fields must be specified")
        return list(results.values(*response_fields))


class LabeledAutocomplete(BaseAutocomplete):
    """
    Serializes the search results into a list of (key, label) pairs.
    """
    def __init__(self, **kwargs):
        self._load_config_values(kwargs,
            key_field=None,
            label=lambda o: unicode(o)
        )
        super(LabeledAutocomplete, self).__init__(**kwargs)
    
    def get_key_field(self, results):
        """
        Get the key field name.
        """
        if self.key_field is None:
            return  results.model._meta.pk.attname
        return self.key_field

    def get_label(self, results):
        """
        Get the label field name or callable to generate a label
        for a given model instance.
        """
        return self.label

    def prepare_results(self, results):
        """
        Return the list of (key, label) pairs.
        """
        key_field = self.get_key_field(results)
        label = self.get_label(results)
        if isinstance(label, basestring):
            results = list(results.values_list(key_field, label))
        elif callable(label):
            results = [(getattr(result, key_field), label(result)) for result in results]
        else:
            raise ImproperlyConfigured(
                "'label' must be either a string or a callable accepting one parameter"
            )
        return results


class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class AutocompleteSite(object):
    """
    An autocomplete site is a registry of autocomplete handlers that dispatches
    requests to their designated handlers.
    """
    def __init__(self, **defaults):
        self._registry = {}
        self.defaults = defaults

    def register(self, key, autocomplete=None, **options):
        """
        Register an autocomplete with the current site.
        """
        if autocomplete is None:
            autocomplete = LabeledAutocomplete
        if key in self._registry:
            raise AlreadyRegistered("The key '%s' is already registered" % key)
        opts = copy(options)
        opts.update(self.defaults)
        self._registry[key] = (autocomplete,  opts)

    def unregister(self, key):
        """
        Remove an autocomplete from the current site's registry.
        """
        if not key in self._registry:
            raise NotRegistered("The key '%s' is not registered" % key)
        del self._registry[key]

    def is_authorized(self, request):
        """
        Is the requesting user allowed to get autocomplete results from
        this site?
        """
        return True

    def __call__(self, request, key=None):
        """
        Dispatch an autocomplete request to the appropriate autocomplete
        handler.
        """
        if key not in self._registry:
            raise Http404
        # Apply site auth
        if not self.is_authorized(request):
            return HttpResponseForbidden()
        autocomplete_class, options = self._registry[key]
        autocomplete = autocomplete_class(**options)
        return autocomplete(request)
