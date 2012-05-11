import unittest

# Python versions earlier then 2.7 doesn't have OrderedDict
try:
    from collections import OrderedDict_
except ImportError:
    ## {{{ http://code.activestate.com/recipes/576693/ (r9)
    # Backport of OrderedDict() class that runs on Python 2.4, 2.5, 2.6, 2.7 and pypy.
    # Passes Python2.7's test suite and incorporates all the latest updates.
    
    try:
        from thread import get_ident as _get_ident
    except ImportError:
        from dummy_thread import get_ident as _get_ident
    
    try:
        from _abcoll import KeysView, ValuesView, ItemsView
    except ImportError:
        pass
    
    
    class OrderedDict(dict):
        'Dictionary that remembers insertion order'
        # An inherited dict maps keys to values.
        # The inherited dict provides __getitem__, __len__, __contains__, and get.
        # The remaining methods are order-aware.
        # Big-O running times for all methods are the same as for regular dictionaries.
    
        # The internal self.__map dictionary maps keys to links in a doubly linked list.
        # The circular doubly linked list starts and ends with a sentinel element.
        # The sentinel element never gets deleted (this simplifies the algorithm).
        # Each link is stored as a list of length three:  [PREV, NEXT, KEY].
    
        def __init__(self, *args, **kwds):
            '''Initialize an ordered dictionary.  Signature is the same as for
            regular dictionaries, but keyword arguments are not recommended
            because their insertion order is arbitrary.
    
            '''
            if len(args) > 1:
                raise TypeError('expected at most 1 arguments, got %d' % len(args))
            try:
                self.__root
            except AttributeError:
                self.__root = root = []                     # sentinel node
                root[:] = [root, root, None]
                self.__map = {}
            self.__update(*args, **kwds)
    
        def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
            'od.__setitem__(i, y) <==> od[i]=y'
            # Setting a new item creates a new link which goes at the end of the linked
            # list, and the inherited dictionary is updated with the new key/value pair.
            if key not in self:
                root = self.__root
                last = root[0]
                last[1] = root[0] = self.__map[key] = [last, root, key]
            dict_setitem(self, key, value)
    
        def __delitem__(self, key, dict_delitem=dict.__delitem__):
            'od.__delitem__(y) <==> del od[y]'
            # Deleting an existing item uses self.__map to find the link which is
            # then removed by updating the links in the predecessor and successor nodes.
            dict_delitem(self, key)
            link_prev, link_next, key = self.__map.pop(key)
            link_prev[1] = link_next
            link_next[0] = link_prev
    
        def __iter__(self):
            'od.__iter__() <==> iter(od)'
            root = self.__root
            curr = root[1]
            while curr is not root:
                yield curr[2]
                curr = curr[1]
    
        def __reversed__(self):
            'od.__reversed__() <==> reversed(od)'
            root = self.__root
            curr = root[0]
            while curr is not root:
                yield curr[2]
                curr = curr[0]
    
        def clear(self):
            'od.clear() -> None.  Remove all items from od.'
            try:
                for node in self.__map.itervalues():
                    del node[:]
                root = self.__root
                root[:] = [root, root, None]
                self.__map.clear()
            except AttributeError:
                pass
            dict.clear(self)
    
        def popitem(self, last=True):
            '''od.popitem() -> (k, v), return and remove a (key, value) pair.
            Pairs are returned in LIFO order if last is true or FIFO order if false.
    
            '''
            if not self:
                raise KeyError('dictionary is empty')
            root = self.__root
            if last:
                link = root[0]
                link_prev = link[0]
                link_prev[1] = root
                root[0] = link_prev
            else:
                link = root[1]
                link_next = link[1]
                root[1] = link_next
                link_next[0] = root
            key = link[2]
            del self.__map[key]
            value = dict.pop(self, key)
            return key, value
    
        # -- the following methods do not depend on the internal structure --
    
        def keys(self):
            'od.keys() -> list of keys in od'
            return list(self)
    
        def values(self):
            'od.values() -> list of values in od'
            return [self[key] for key in self]
    
        def items(self):
            'od.items() -> list of (key, value) pairs in od'
            return [(key, self[key]) for key in self]
    
        def iterkeys(self):
            'od.iterkeys() -> an iterator over the keys in od'
            return iter(self)
    
        def itervalues(self):
            'od.itervalues -> an iterator over the values in od'
            for k in self:
                yield self[k]
    
        def iteritems(self):
            'od.iteritems -> an iterator over the (key, value) items in od'
            for k in self:
                yield (k, self[k])
    
        def update(*args, **kwds):
            '''od.update(E, **F) -> None.  Update od from dict/iterable E and F.
    
            If E is a dict instance, does:           for k in E: od[k] = E[k]
            If E has a .keys() method, does:         for k in E.keys(): od[k] = E[k]
            Or if E is an iterable of items, does:   for k, v in E: od[k] = v
            In either case, this is followed by:     for k, v in F.items(): od[k] = v
    
            '''
            if len(args) > 2:
                raise TypeError('update() takes at most 2 positional '
                                'arguments (%d given)' % (len(args),))
            elif not args:
                raise TypeError('update() takes at least 1 argument (0 given)')
            self = args[0]
            # Make progressively weaker assumptions about "other"
            other = ()
            if len(args) == 2:
                other = args[1]
            if isinstance(other, dict):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, 'keys'):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
            for key, value in kwds.items():
                self[key] = value
    
        __update = update  # let subclasses override update without breaking __init__
    
        __marker = object()
    
        def pop(self, key, default=__marker):
            '''od.pop(k[,d]) -> v, remove specified key and return the corresponding value.
            If key is not found, d is returned if given, otherwise KeyError is raised.
    
            '''
            if key in self:
                result = self[key]
                del self[key]
                return result
            if default is self.__marker:
                raise KeyError(key)
            return default
    
        def setdefault(self, key, default=None):
            'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
            if key in self:
                return self[key]
            self[key] = default
            return default
    
        def __repr__(self, _repr_running={}):
            'od.__repr__() <==> repr(od)'
            call_key = id(self), _get_ident()
            if call_key in _repr_running:
                return '...'
            _repr_running[call_key] = 1
            try:
                if not self:
                    return '%s()' % (self.__class__.__name__,)
                return '%s(%r)' % (self.__class__.__name__, self.items())
            finally:
                del _repr_running[call_key]
    
        def __reduce__(self):
            'Return state information for pickling'
            items = [[k, self[k]] for k in self]
            inst_dict = vars(self).copy()
            for k in vars(OrderedDict()):
                inst_dict.pop(k, None)
            if inst_dict:
                return (self.__class__, (items,), inst_dict)
            return self.__class__, (items,)
    
        def copy(self):
            'od.copy() -> a shallow copy of od'
            return self.__class__(self)
    
        @classmethod
        def fromkeys(cls, iterable, value=None):
            '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S
            and values equal to v (which defaults to None).
    
            '''
            d = cls()
            for key in iterable:
                d[key] = value
            return d
    
        def __eq__(self, other):
            '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
            while comparison to a regular mapping is order-insensitive.
    
            '''
            if isinstance(other, OrderedDict):
                return len(self)==len(other) and self.items() == other.items()
            return dict.__eq__(self, other)
    
        def __ne__(self, other):
            return not self == other
    
        # -- the following methods are only used in Python 2.7 --
    
        def viewkeys(self):
            "od.viewkeys() -> a set-like object providing a view on od's keys"
            return KeysView(self)
    
        def viewvalues(self):
            "od.viewvalues() -> an object providing a view on od's values"
            return ValuesView(self)
    
        def viewitems(self):
            "od.viewitems() -> a set-like object providing a view on od's items"
            return ItemsView(self)
    ## end of http://code.activestate.com/recipes/576693/ }}}


from pyramid import testing
from pyramid_mailer import get_mailer

from voteit.core.testing_helpers import bootstrap_and_fixture


class UsersViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.users import UsersView
        return UsersView
    
    def _fixture(self):
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root.users['u1'] = User(title='Dummy 1')
        root.users['u2'] = User(title='Dummy 2')
        root.users['u3'] = User(title='Dummy 3')
        return root.users
        
    def test_list_users(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.list_users()
        self.assertIn('users', response)
        
    def test_view_user(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['u1'] 
        request = testing.DummyRequest(is_xhr=True)
        obj = self._cut(context, request)
        response = obj.view_user()
        self.assertIn('user_info', response)
        
class UsersFormViewTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.users import UsersFormView
        return UsersFormView
    
    def _fixture(self):
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root.users['dummy1'] = User(title='Dummy 1')
        root.users['dummy2'] = User(title='Dummy 2')
        root.users['dummy3'] = User(title='Dummy 3', email='dummy3@test.com')
        root.users['dummy3'].set_password('dummy1234')
        return root.users
    
    def test_add_form(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)
        
    def test_add_form_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertEqual(response.location, 'http://example.com/users/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Canceled',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_add_form_post(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', '/'), 
                                                           ('add', 'add')]))
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('dummy4', context)
        self.assertEqual(response.location, 'http://example.com/users/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Successfully added',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_add_form_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy3'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', '/'), 
                                                           ('add', 'add')]))
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)
        
    def test_password_form(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertIn('form', response)
        
    def test_password_form_admin(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertIn('form', response)
        
    def test_password_form_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertEqual(response.location, 'http://example.com/users/dummy3/')
        
    def test_password_form_post(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = OrderedDict([('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('update', 'update')]))
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertEqual(response.location, 'http://example.com/users/dummy3/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Password changed',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_password_form_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = OrderedDict([('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234_'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('update', 'update')]))
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertIn('form', response)
        
    def test_token_password_change(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertEqual(response.location, 'http://example.com/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Invalid security token. Did you click the link in your email?',
                                  'close_button': True,
                                  'type': 'error'}])
    
    def test_token_password_change_get(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest(params={'token': 'dummy_token'})
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertIn('form', response)
        
    def test_token_password_change_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_token_password_change_post(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        from voteit.core.models.user import RequestPasswordToken
        context.__token__ = RequestPasswordToken()
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = OrderedDict([('token', context.__token__()),
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('change', 'change')]))
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertEqual(response.location, 'http://example.com/@@login')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Password set. You may login now.',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_token_password_change_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        from voteit.core.models.user import RequestPasswordToken
        context.__token__ = RequestPasswordToken()
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = OrderedDict([('token', context.__token__()),
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234_'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('change', 'change')]))
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertIn('form', response)
        
    def test_login_or_register(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(user_agent='Dummy agent', params={'came_from': '/'})
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('login_form', response)
        self.assertIn('reg_form', response)
        
    def test_login_or_register_unsupported_browser(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(user_agent='Mozilla/4.0 (compatible; MSIE 7.0;)')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/unsupported_browser')
        
    def test_login_or_register_login_userid(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy3'),
                                                           ('password', 'dummy1234'), 
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_login_or_register_login_email(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy3@test.com'),
                                                           ('password', 'dummy1234'), 
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_login_or_register_login_came_from(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy3@test.com'),
                                                           ('password', 'dummy1234'),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'dummy_url')
        
    def test_login_or_register_login_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy3@test.com'),
                                                           ('password', ''),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('login_form', response)
        
    def test_login_or_register_login_failed(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy3@test.com'),
                                                           ('password', 'dummy1234_'),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('login_form', response)
        self.assertIn('reg_form', response)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Login failed.',
                                  'close_button': True,
                                  'type': 'error'}])
        
    def test_login_or_register_register(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/login')
        
    def test_login_or_register_register_came_from(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', 'dummy_url'), 
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'dummy_url')
        
    def test_login_or_register_register_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = OrderedDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234_'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', 'dummy_url'), 
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('reg_form', response)
        
    def test_request_password(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertIn('form', response)
        
    def test_request_password_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_request_password_userid(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('voteit.core.models.flash_messages')
        self.config.include('pyramid_mailer.testing')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': 'dummy3'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Email sent.',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_request_password_email(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('voteit.core.models.flash_messages')
        self.config.include('pyramid_mailer.testing')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': 'dummy3@test.com'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Email sent.',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_request_password_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': ''})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertIn('form', response)
        
    def test_request_password_not_found(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': 'dummy4'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertIn('form', response)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Username or email not found.',
                                  'close_button': True,
                                  'type': 'error'}])
        
    def test_logout(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.logout()
        self.assertEqual(response.location, 'http://example.com/')