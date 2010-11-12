from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin
from django.contrib.auth.models import User

from fancy_autocomplete.views import AutocompleteSite, LabeledAutocomplete, ObjectAutocomplete

# Define a vanilla site

autocompletes = AutocompleteSite()

# Register a simple autocomplete with the site

autocompletes.register(
    'user',
    queryset = User.objects.filter(is_active=True, is_superuser=False),
    search_fields = ('username', 'email', 'first_name', 'last_name'),
    limit = 5,
)

# Define an autocomplete site that may only be used by authenticated users
class LoginSite(AutocompleteSite):
    def is_authorized(self, request):
        return request.user.is_authenticated()

authenticated_autocompletes = LoginSite()

# Create a dict autocomplete that returns first and last names for use
# in a client-side label

class UserDictAutocomplete(ObjectAutocomplete):
    queryset = User.objects.filter(is_active=True, is_superuser=False)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    response_fields = ('username', 'first_name', 'last_name', 'email')
    limit = 10

authenticated_autocompletes.register('user', autocomplete=UserDictAutocomplete)

# Define a simple standalone autocomplete

class UserAutocomplete(LabeledAutocomplete):
    """
    User autocomplete action!
    """
    queryset = User.objects.filter(is_active=True, is_superuser=False)
    search_fields = ('username', 'email', 'first_name', 'last_name')

urlpatterns = patterns('',
    url(
        r'^admin/',
        include(admin.site.urls)
    ),
    url(
        r'^$',
        direct_to_template,
        {'template': 'index.html'}
    ),
    url(
        r'^autocomplete/([\w-]+)/$',
        autocompletes,
        name='autocomplete'
    ),
    url(
        r'^authenticatedautocomplete/([\w-]+)/$',
        authenticated_autocompletes,
        name='authenticated_autocomplete'
    ),
    url(
        r'^standalone/$',
        UserAutocomplete.as_view(),
        name='standalone_autocomplete'
    ),
)
