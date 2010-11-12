.. _overview:

Django Fancy Autocomplete Overview
==================================

This document gives a brief overview of using Django Fancy Autocomplete
in a Django project.

Installing Django Fancy Autocomplete
------------------------------------

.. highlight:: bash

To install Django Fancy Autocomplete, run the following command inside the
extracted package directory::

    $ python setup.py install

Once this is done, you should be able to import and use the
``fancy_autocomplete`` package.

Quickstart
----------

.. highlight:: python

Suppose you want to write a user messaging app for your site with thousands
of users tracked by ``auth.User`` models. Your message sending form allows
the user to type in a username, but to ensure that they are sending their
message to a valid user you want to present them with choices as they type.
Enter the ``AutocompleteSite`` class to help you out.

To provide a quick JSON data source for your JavaScript widget, you can
simply create an ``AutocompleteSite`` in your ``urls.py`` and register the
user model against it like so::

    from django.conf.urls.defaults import *
    from django.contrib.auth.models import User
    
    from fancy_autocomplete.views import AutocompleteSite

    autocompletes = AutocompleteSite()
    
    autocompletes.register(
        'user',
        queryset = User.objects.filter(is_active=True, is_superuser=False),
        search_fields = ('username', 'email', 'first_name', 'last_name'),
        limit = 5
    )

    urlpatterns = patterns('',
        url(r'^autocomplete/(.*)/$', autocompletes, name='autocomplete'),
    )

This creates an autocomplete class that will search for active, non-superuser
users whose ``username``, ``email``, ``first_name`` or ``last_name`` starts
with the string the user types in the username field, and returns the first
five results in a JSON list of ``(id, username)`` pairs.

.. highlight:: html

So in our message sending template we have a text input for usernames::

    <input type="text" name="username" id="id_username">

.. highlight:: javascript

Now let's wire up our username input field to the autocomplete view using
jQuery UI to handle the AJAX magic::


    $("#id_username").autocomplete({
        source: function(request, response){
            $.ajax({
                url: "{% url autocomplete 'user'%}",
                data: {q: request.term},
                success: function(data) {
                    response($.map(data, function(item) {
                        return {
                            label: item[1],
                            value: item[1]
                        };
                    }));
                },
                dataType: "json"
            });
        },
        minLength: 2
    });

When we visit the form now, after typing two characters into the ``username``
form field we are presented with a shiny list of users we can choose from.

Further Information
-------------------

For information on how to customize the behavior of autocomplete classes and
sites please see the `views <views>`_ documentation.
