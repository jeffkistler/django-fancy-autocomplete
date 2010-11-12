.. _views:

=====
Views
=====

Django Fancy Autocomplete provides two basic types for use as views
within Django projects.

The Autocomplete Classes
========================

.. highlight:: python

The autocomplete classes are used to define autocomplete resources and
handle autocomplete query requests against those resources. To define
an autocomplete resource, you may subclass one of the two provided
autocomplete classes and set attributes on your class::

    from django.contrib.auth.models import User
    from fancy_autocomplete.views import LabeledAutocomplete

    class UserAutocomplete(LabeledAutocomplete):
        model = User

You may then use this autocomplete resource directly as a view by
calling the ``as_view`` class method::

    urlpatterns = patterns('',
        url(r'^users/autocomplete/$', UserAutocomplete.as_view()),
    )

It is also possible to define an autocomplete resource by passing
configuration values as keyword args to the ``as_view`` class method to set
these configuration attributes on your autocomplete resource::

    urlpatterns = patterns('',
        url(r'^users/autocomplete/$', LabeledAutocomplete.as_view(model=User)),
    )

``BaseAutocomplete``
--------------------

The two autocomplete classes, ``LabeledAutocomplete`` and
``ObjectAutocomplete`` accept a number of common configuration values that
are processed by the ``BaseAutocomplete`` class.

Attributes
~~~~~~~~~~

.. attribute:: BaseAutocomplete.queryset

    The queryset to search for autocomplete results within.    

.. attribute:: BaseAutocomplete.model

    A model class to search for autocomplete results within.

.. attribute:: BaseAutocomplete.search_fields

    The fields to search on to filter results.

.. attribute:: BaseAutocomplete.limit

    The maximum number of results to return. If its value is ``None``, all
    results will be returned.

.. attribute:: BaseAutocomplete.query_param

    The querystring parameter to retrieve the search term from. Defaults
    to ``'q'``.

.. attribute:: BaseAutocomplete.lookup

    The lookup type to perform when searching. This must be a Django field
    lookup type. Defaults to ``'startswith'``.

.. attribute:: BaseAutocomplete.mimetype

    A MIME type for the response. Defaults to ``application/javascript``.

.. attribute:: BaseAutocomplete.allowed_methods

    An iterable of allowed HTTP methods. Defaults to ``('GET',)``.

Methods
~~~~~~~

Additionally the ``BaseAutocomplete`` class defines a number of methods that
may be overridden to customize behavior. When called as a view the
``HttpRequest`` is stored on the instance in the ``request`` attribute so
these methods may access ``self.request`` in order to generate their return
values.

.. method:: BaseAutocomplete.get_queryset

    Returns the ``QuerySet`` object to perform the search on.

.. method:: BaseAutocomplete.get_result_queryset(queryset)

    Performs the search within ``queryset``, using the results of
    ``get_queryset``, ``get_query_param``, ``get_search_fields`` and
    ``get_lookup``.

.. method:: BaseAutocomplete.is_authorized

    Determines whether the client making the request is authorized to use
    this autocomplete.

.. method:: BaseAutocomplete.get_query_param

    Returns the retrieved search term. By default, this returns the value of
    the ``'q'`` parameter in the request querystring.

.. method:: BaseAutocomplete.get_search_fields

    Returns an iterable of fields to use in the search.

.. method:: BaseAutocomplete.get_limit

    Returns the maximum numer of results to include in the returned response.

.. method:: BaseAutocomplete.get_mimetype

    Returns a MIME type for the response.

.. method:: BaseAutocomplete.prepare_results(results)

    Returns an object that is ready to be serialized into the response.

.. method:: BaseAutocomplete.serialize_results(results)

    Serializes the results object to be used as the response body. By default
    the results will be serialized as JSON.

.. method:: BaseAutocomplete.get_response(results)

    Creates the ``HttpResponse`` object with the correct MIME type and
    serializes the result object into the body.

.. method:: BaseAutocomplete.as_view(**initkwargs)

    Returns a function that will build an instance of the current autocomplete
    class suitable for use as a view.

.. method:: BaseAutocomplete._load_config_value(initkwargs, **defaults)

    Set on self some config values possibly taken from __init__, or
    attributes on self.__class__, or some default.

``LabeledAutocomplete``
-----------------------

The ``LabeledAutocomplete`` class is used to generate responses as
``(key, value)`` pairs.

.. attribute:: LabeledAutocomplete.key_field

    Specifies a field to use as the ``key`` in the response. If not specified,
    the ``pk`` value of the model will be used.

.. attribute:: LabeledAutocomplete.label

    Specifies a field or callable for use as the label in the response.
    If a callable is given, it must accept a single model instance argument
    and return a string. If not specified, the models's ``__unicode__`` method
    will be used.

.. method:: LabeledAutocomplete.get_key_field(results)

    Returns the key field name. By default it returns the ``pk`` field name.

.. method:: LabeledAutocomplete.get_label(results)

    Returns the label field name or a callable to generate the label.

``ObjectAutocomplete``
----------------------

The ``ObjectAutocomplete`` class is used to generate responses as a list
of JSON objects whose properties are the specified ``response_fields``.

.. attribute:: ObjectAutocomplete.response_fields

    An iterable of field names to include in the response objects.

.. method:: ObjectAutocomplete.get_response_fields

    Returns the list of field names to include in the response objects.

The ``AutocompleteSite`` Class
==============================

The ``AutocompleteSite`` class acts as a registry of autocomplete handlers
that in the simplest case can be used as a view to dispatch requests to one
or more ``Autocomplete`` classes. ``AutocompleteSite`` objects also have
the ability to provide global authorization for and provide global
configuration values to any registered autocompletes.

.. method:: AutocompleteSite.__init__(**defaults)

    Sets up the ``AutocompleteSite`` and stores any given keyword arguments
    for use as default configuration values for all autocomplete classes
    registered with the site. These values will override those on the
    autocomplete classes.

.. method:: AutocompleteSite.register(key, autocomplete=None, **options)

    Register an autocomplete handler with the site to be dispatched to by
    the given ``key``. If given, the autocomplete keyword argument should
    specify an autocomplete class to use for this key. If this is left
    unspecified the ``LabeledAutocomplete`` class will be used. If given,
    any additional keyword arguments will be used as constructor parameters
    for the autocomplete object. Note that any site-wide defaults will
    take precedence.

.. method:: AutocompleteSite.unregister(key)

    Removes the autocomplete with the given ``key`` from the registry.

.. method:: AutocompleteSite.is_authorized(request)

    Returns a boolean value whether or not the requesting client is
    authorized to make a request to the current site object.
