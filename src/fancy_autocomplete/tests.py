from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, Http404
from django.test import Client
from django.core.handlers.wsgi import WSGIRequest
from django.utils import simplejson

from fancy_autocomplete.views import (
    BaseAutocomplete, LabeledAutocomplete, ObjectAutocomplete, AutocompleteSite,
    AlreadyRegistered, NotRegistered
)


class RequestFactory(Client):
    """
    Class that lets you create mock Request objects for use in testing.
    
    Usage:
    
    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})
    
    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client
    
    Once you have a request object you can pass it to any view function, 
    just as if that view had been hooked up using a URLconf.
    
    """
    def request(self, **request):
        """
        Similar to parent class, but returns the request object as soon as it
        has created it.
        """
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)

request_factory = RequestFactory()

class BaseAutocompleteTest(TestCase):
    def test_init_kwargs(self):
        autocomplete = BaseAutocomplete(model=User)
        self.assertEquals(User, autocomplete.model)
        self.assertEquals('q', autocomplete.query_param)
        self.assertEquals('startswith', autocomplete.lookup)
        self.assertEquals('application/javascript', autocomplete.mimetype)
        self.assertEquals(None, autocomplete.limit)
        self.assertEquals(('GET',), autocomplete.allowed_methods)

    def test_init_no_kwargs(self):
        autocomplete = BaseAutocomplete(model=User)
        self.assertEquals('q', autocomplete.query_param)
        self.assertEquals('startswith', autocomplete.lookup)
        self.assertEquals('application/javascript', autocomplete.mimetype)
        self.assertEquals(None, autocomplete.limit)
        self.assertEquals(('GET',), autocomplete.allowed_methods)

    def test_init_declarative(self):
        class TestAutocomplete(BaseAutocomplete):
            model = User
        autocomplete = TestAutocomplete()
        self.assertEquals(User, autocomplete.model)

    def test_get_lookup(self):
        autocomplete = BaseAutocomplete()
        self.assertEquals('startswith', autocomplete.get_lookup(None))
        autocomplete = BaseAutocomplete(lookup='istartswith')
        self.assertEquals('istartswith', autocomplete.get_lookup(None))
        class TestAutocomplete(BaseAutocomplete):
            def get_lookup(self, field):
                if field == 'username':
                    return 'icontains'
                return self.lookup
        autocomplete = TestAutocomplete()
        self.assertEquals('icontains', autocomplete.get_lookup('username'))
        self.assertEquals('startswith', autocomplete.get_lookup('email'))
            
    def test_get_queryset(self):
        autocomplete = BaseAutocomplete()
        self.assertRaises(ImproperlyConfigured, autocomplete.get_queryset)
        autocomplete = BaseAutocomplete(model=User)
        self.assertEquals(
            unicode(User.objects.all().query),
            unicode(autocomplete.get_queryset().query)
        )
        autocomplete = BaseAutocomplete(queryset=User.objects.filter(is_active=True))
        self.assertEquals(
            unicode(User.objects.filter(is_active=True).query),
            unicode(autocomplete.get_queryset().query)
        )

    def test_get_limit(self):
        autocomplete = BaseAutocomplete()
        self.assertEquals(None, autocomplete.get_limit())
        autocomplete = BaseAutocomplete(limit=100)
        self.assertEquals(100, autocomplete.get_limit())
        class TestAutocomplete(BaseAutocomplete):
            limit = 130
        autocomplete = TestAutocomplete()
        self.assertEquals(130, autocomplete.get_limit())

    def test_get_search_fields(self):
        autocomplete = BaseAutocomplete()
        self.assertRaises(ImproperlyConfigured, autocomplete.get_search_fields)
        autocomplete = BaseAutocomplete(search_fields=['username'])
        self.assertEquals(['username'], autocomplete.get_search_fields())

    def test_is_authorized(self):
        autocomplete = BaseAutocomplete()
        self.assertEquals(True, autocomplete.is_authorized())

    def test_get_result_queryset(self):
        autocomplete = BaseAutocomplete(model=User, search_fields=['username'])
        request = request_factory.get('/')
        autocomplete.request = request
        self.assertEquals(
            unicode(User.objects.none().query),
            unicode(autocomplete.get_result_queryset().query)
        )

        autocomplete = BaseAutocomplete(model=User, search_fields=['username'])
        request = request_factory.get('/', {'q': 'foo'})
        autocomplete.request = request
        qs = User.objects.filter(username__startswith='foo')
        self.assertEquals(
            unicode(qs.query),
            unicode(autocomplete.get_result_queryset().query)
        )

        autocomplete = BaseAutocomplete(model=User, search_fields=['username'], limit=10)
        request = request_factory.get('/', {'q': 'foo'})
        autocomplete.request = request
        qs = User.objects.filter(username__startswith='foo')[:10]
        self.assertEquals(
            unicode(qs.query),
            unicode(autocomplete.get_result_queryset().query)
        )
    
    def test_get_mimetype(self):
        autocomplete = BaseAutocomplete()
        self.assertEquals('application/javascript', autocomplete.get_mimetype())
        autocomplete = BaseAutocomplete(mimetype='application/json')
        self.assertEquals('application/json', autocomplete.get_mimetype())
        class TestAutocomplete(BaseAutocomplete):
            mimetype = 'application/json'
        autocomplete = TestAutocomplete()
        self.assertEquals('application/json', autocomplete.get_mimetype())

    def test_prepare_results(self):
        autocomplete = BaseAutocomplete()
        self.assertRaises(NotImplementedError, autocomplete.prepare_results, None)

    def test_serialize_results(self):
        autocomplete = BaseAutocomplete()
        self.assertRaises(NotImplementedError, autocomplete.serialize_results, None)

    def test_get_response(self):
        autocomplete = BaseAutocomplete()
        self.assertRaises(NotImplementedError, autocomplete.get_response, None)

    def test_get_response_invalid_method(self):
        autocomplete = BaseAutocomplete()
        request = request_factory.post("q=foo")
        response = autocomplete(request)
        self.assertEquals(405, response.status_code)
        self.assertEquals('GET', response['Allow'])
        autocomplete = BaseAutocomplete(allowed_methods=['POST'])
        self.assertEquals(['POST'], autocomplete.allowed_methods)
        
    def test_forbidden_response(self):
        class TestAutocomplete(BaseAutocomplete):
            def is_authorized(self):
                return self.request.user.is_authenticated()
        request = request_factory.get("/")
        request.user = AnonymousUser()
        autocomplete = TestAutocomplete()
        response = autocomplete(request)
        self.assertEquals(403, response.status_code)
    
    def test_as_view(self):
        autocomplete = BaseAutocomplete()
        self.assertRaises(AttributeError, getattr, autocomplete, "as_view")
        view = BaseAutocomplete.as_view()


class LabeledAutocompleteBasicTest(TestCase):
    def test_init(self):
        pass

    def test_get_key_field(self):
        autocomplete = LabeledAutocomplete(model=User)
        self.assertEquals('id', autocomplete.get_key_field(User.objects.all()))
        autocomplete = LabeledAutocomplete(key_field='id')
        self.assertEquals('id', autocomplete.get_key_field(None))

    def test_get_label(self):
        autocomplete = LabeledAutocomplete()
        label = autocomplete.get_label(None)
        self.assertTrue(callable(label))
        self.assertEquals(u'test', label(u'test'))
        autocomplete = LabeledAutocomplete(label='test')
        label = autocomplete.get_label(None)
        self.assertEquals(u'test', label)

    def test_prepare_results(self):
        autocomplete = LabeledAutocomplete(label=2)
        self.assertEquals(2, autocomplete.get_label(None))
        self.assertRaises(
            ImproperlyConfigured,
            autocomplete.prepare_results,
            User.objects.all()
        )

    def test_get_response(self):
        pass

    def test_as_view(self):
        pass

class LabeledAutcompleteResponseTest(TransactionTestCase):
    fixtures = ['fancy_autocomplete_test_data.json']

    def test_prepare_results(self):
        request = request_factory.get("/", {'q': 'an'})
        autocomplete = LabeledAutocomplete(model=User, search_fields=['username'])
        autocomplete.request = request
        results = autocomplete.get_result_queryset()
        prepared = autocomplete.prepare_results(results)
        qs = User.objects.filter(username__startswith='an')
        self.assertEquals([(u.id, unicode(u)) for u in qs], prepared)

        autocomplete = LabeledAutocomplete(
            model=User,
            search_fields=['username'],
            label='username'
        )
        autocomplete.request = request
        results = autocomplete.get_result_queryset()
        prepared = autocomplete.prepare_results(results)
        qs = User.objects.filter(username__startswith='an')
        self.assertEquals([(u.id, u.username) for u in qs], prepared)

        autocomplete = LabeledAutocomplete(
            model=User,
            search_fields=['username'],
            label='username',
            key_field='username'
        )
        autocomplete.request = request
        results = autocomplete.get_result_queryset()
        prepared = autocomplete.prepare_results(results)
        qs = User.objects.filter(username__startswith='an')
        self.assertEquals([(u.username, u.username) for u in qs], prepared)

    def test_get_response(self):
        request = request_factory.get("/", {'q': 'an'})
        autocomplete = LabeledAutocomplete(model=User, search_fields=['username'])
        autocomplete.request = request
        results = autocomplete.get_result_queryset()
        response = autocomplete.get_response(results)

        qs = User.objects.filter(username__startswith='an')
        compare = simplejson.dumps(list((u.id, unicode(u)) for u in qs))
        self.assertEquals('application/javascript', response['Content-Type'])
        self.assertEquals(compare, response.content)

        request = request_factory.get("/", {'q': 'an'})
        autocomplete = LabeledAutocomplete(
            model=User,
            search_fields=['username'],
            limit=1
        )
        autocomplete.request = request
        results = autocomplete.get_result_queryset()
        response = autocomplete.get_response(results)

        qs = User.objects.filter(username__startswith='an')[:1]
        compare = simplejson.dumps(list((u.id, unicode(u)) for u in qs))
        self.assertEquals('application/javascript', response['Content-Type'])
        self.assertEquals(compare, response.content)

    def test_as_view(self):
        class UserAutocomplete(LabeledAutocomplete):
            model = User
            search_fields = ['username']
            limit = 1
        view = UserAutocomplete.as_view(limit=None)
        request = request_factory.get("/", {'q': 'an'})
        response = view(request)

        qs = User.objects.filter(username__startswith='an')
        compare = simplejson.dumps(list((u.id, unicode(u)) for u in qs))
        self.assertEquals('application/javascript', response['Content-Type'])
        self.assertEquals(compare, response.content)

class ObjectAutocompleteBasicTest(TestCase):
    def test_get_response_fields(self):
        autocomplete = ObjectAutocomplete(model=User)
        self.assertEquals(None, autocomplete.get_response_fields())
        autocomplete = ObjectAutocomplete(model=User, response_fields=['username'])
        self.assertEquals(['username'], autocomplete.get_response_fields())
        class TestAutocomplete(ObjectAutocomplete):
            model = User
            response_fields = ['id']
        autocomplete = TestAutocomplete()
        self.assertEquals(['id'], autocomplete.get_response_fields())

    def test_prepare_results(self):
        autocomplete = ObjectAutocomplete()
        self.assertRaises(ImproperlyConfigured, autocomplete.prepare_results, None)


class ObjectAutocompleteResponseTest(TransactionTestCase):
    fixtures = ['fancy_autocomplete_test_data.json']

    def test_get_response(self):
        request = request_factory.get("/", {'q': 'c'})
        autocomplete = ObjectAutocomplete(
            model=User, search_fields=['username'],
            response_fields=['username']
        )
        autocomplete.request = request
        results = autocomplete.get_result_queryset()
        response = autocomplete.get_response(results)

        qs = User.objects.filter(username__startswith='c').values('username')
        compare = simplejson.dumps(list(qs))
        self.assertEquals('application/javascript', response['Content-Type'])
        self.assertEquals(compare, response.content)


    def test_as_view(self):
        class UserAutocomplete(ObjectAutocomplete):
            model = User
            search_fields = ['username']
            response_fields = ['username']
            limit = 1
        view = UserAutocomplete.as_view(limit=None)
        request = request_factory.get("/", {'q': 'd'})
        response = view(request)

        qs = User.objects.filter(username__startswith='d').values('username')
        compare = simplejson.dumps(list(qs))
        self.assertEquals('application/javascript', response['Content-Type'])
        self.assertEquals(compare, response.content)


class AutocompleteSiteTest(TestCase):
    def test_register(self):
        site = AutocompleteSite()
        site.register('user', model=User)
        self.assertTrue('user' in site._registry)
        self.assertEquals('LabeledAutocomplete', site._registry['user'][0].__name__)
        self.assertEquals({'model': User}, site._registry['user'][1])
        self.assertRaises(AlreadyRegistered, site.register, 'user', model=User)

    def test_unregister(self):
        site = AutocompleteSite()
        site.register('user', model=User)
        self.assertEquals(1, len(site._registry))
        site.unregister('user')
        self.assertEquals(0, len(site._registry))
        self.assertRaises(NotRegistered, site.unregister, 'user')

    def test_unregistered_view(self):
        site = AutocompleteSite()
        self.assertRaises(Http404, site, None, 'user')

class AutocompleteSiteResponseTest(TransactionTestCase):
    fixtures = ['fancy_autocomplete_test_data.json']

    def test_authorization(self):
        class TestSite(AutocompleteSite):
            def is_authorized(self, request):
                return request.user.is_authenticated()
        request = request_factory.get("/")
        request.user = AnonymousUser()
        site = TestSite()
        site.register(
            'user',
            model=User,
            search_fields=['username']
        )
        response = site(request, 'user')
        self.assertEquals(403, response.status_code)
        request = request_factory.get("/", {"q": "a"})
        request.user = User.objects.filter(is_active=True)[0]
        response = site(request, 'user')
        self.assertEquals(200, response.status_code)

    def test_overrides(self):
        site = AutocompleteSite(limit=1)
        site.register('user', model=User, search_fields=['username'])
        request = request_factory.get("/", {"q": "a"})
        
        response = site(request, 'user')
        self.assertEquals(1, len(simplejson.loads(response.content)))

