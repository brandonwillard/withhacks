
from __future__ import with_statement

import os
import sys
import unittest
import doctest

import withhacks
from withhacks import *


class TestXArgs(unittest.TestCase):

    def test_xargs(self):
        def func(a, b, c=42):
            return a * b * c
        with xargs(func) as v:
            a = 1
            b = 2
            c = 3
        self.assertEquals(v, 1 * 2 * 3)
        with xargs(func, 7) as v:
            x = 8
            y = 9
        self.assertEquals(v, 7 * 8 * 9)
        with xargs(func, 7) as v:
            b = 8
        self.assertEquals(v, 7 * 8 * 42)

    def test_xkwargs(self):
        def func(a, b, c=42):
            return a * a - b + c
        with xkwargs(func) as v:
            a = 1
            b = 2
            c = 3
        self.assertEquals(v, 1 * 1 - 2 + 3)
        with xkwargs(func, b=2) as v:
            c = 4
            a = -1
        self.assertEquals(v, 1 * 1 - 2 + 4)
        with xkwargs(func, b=2) as v:
            c = 3
            a = 1
            c = 5
        self.assertEquals(v, 1 * 1 - 2 + 5)


class TestNamespace(unittest.TestCase):

    def test_namespace(self):
        a = 42
        with namespace() as ns:
            a = 2 * a
        self.assertEquals(ns.a, 42 * 2)
        with namespace() as ns:
            a = 7
            b = a * 4
            v = ValueError
        self.assertEquals(ns.b, 7 * 4)
        self.assertEquals(ns.v, ValueError)
        b = withhacks._Bucket()
        with namespace(b):
            def hello():
                return "hi there"

            def howzitgoin():
                return "fine thanks"
        self.assertEquals(b.hello(), "hi there")
        self.assertEquals(b.howzitgoin(), "fine thanks")
        with namespace(b):
            del hello
        self.assertRaises(AttributeError, getattr, b, "hello")
        self.assertEquals(b.howzitgoin(), "fine thanks")

    def test_keyspace(self):
        a = 42
        with keyspace() as d:
            a = 2 * a
        self.assertEquals(d["a"], 42 * 2)
        with keyspace() as d:
            a = 7
            b = a * 4
            v = ValueError
        self.assertEquals(d["b"], 7 * 4)
        self.assertEquals(d["v"], ValueError)
        d = {}
        with keyspace(d):
            def hello():
                return "hi there"

            def howzitgoin():
                return "fine thanks"
        self.assertEquals(d["hello"](), "hi there")
        self.assertEquals(d["howzitgoin"](), "fine thanks")
        with keyspace(d):
            del hello
        self.assertRaises(KeyError, d.__getitem__, "hello")
        self.assertEquals(d["howzitgoin"](), "fine thanks")

    def test_keyspace_save_name(self):
        d = {'a': [1]}
        with keyspace() as d['a'][0]:
            x = 1
        self.assertEquals(d['a'][0]['x'], 1)

    def test_keyspace_save_global(self):
        global d
        with keyspace() as d:
            x = 1
        self.assertEquals(d['x'], 1)


class TestCaptureFunction(unittest.TestCase):

    def test_capture(self):
        with CaptureFunction() as c:
            return 42
        self.assertEquals(c.function(), 42)
        with CaptureFunction(("flag",)) as c:
            if not flag:
                raise ValueError
            return True
        self.assertRaises(TypeError, c.function)
        self.assertRaises(ValueError, c.function, False)
        self.assertTrue(c.function(True))
        with CaptureFunction() as c:
            TestCaptureFunction("test_capture").run()
        c.function()

    def test_capture_varargs(self):
        with CaptureFunction(("kwargs",), varkwargs=True) as c:
            return kwargs
        self.assertEquals(c.function(a=1), {'a': 1})
        with CaptureFunction(("args",), varargs=True) as c:
            return args
        self.assertEquals(c.function(1, 2, 3), (1, 2, 3))


class TestCaptureLocals(unittest.TestCase):

    def test_capture(self):

        cache_file = tempfile.mktemp(suffix='.db', dir='/tmp')
        times = 10
        message = "blagh"

        # Initial run executes the `with`'s code and caches the local variables.
        # The `for` loop should output `message`; (naively) demonstrating that the
        # code was actually run.
        with CacheLocals(cache_file) as cache_obj:
            for i in range(times):
                print(message)
            test_var = "blah"
            print("ran with block!")

        # Make sure cache wasn't used.
        self.assertTrue(cache_obj.last_cache_invalid)

        self.assertEquals(test_var, "blah")

        self.assertTrue("test_var" in cache_obj.assigned_locals)
        self.assertTrue("i" in cache_obj.assigned_locals)

        # Remove a `with`-local variable.
        del test_var, cache_obj

        self.assertTrue('i' not in locals())
        self.assertTrue('test_var' not in locals())

        # This time, the `for` loop should *not* print, but the `with`-local
        # variable `test_var` (and `i`) are [re]set.
        with CacheLocals(cache_file) as cache_obj:
            for i in range(times):
                print(message)
            test_var = "blah"
            print("ran with block!")

        # Make sure cache was used.
        self.assertTrue(not cache_obj.last_cache_invalid)

        self.assertEquals(test_var, "blah")
        self.assertTrue("test_var" in cache_obj.assigned_locals)
        self.assertTrue("i" in cache_obj.assigned_locals)




class TestMisc(unittest.TestCase):

    def test_docstrings(self):
        """Test withhacks docstrings."""
        assert doctest.testmod(withhacks)[0] == 0

    def test_README(self):
        """Ensure that the README is in sync with the docstring.

        This test should always pass; if the README is out of sync it just
        updates it with the contents of withhacks.__doc__.
        """
        dirname = os.path.dirname
        readme = os.path.join(dirname(dirname(dirname(__file__))), "README.txt")
        if not os.path.isfile(readme):
            f = open(readme, "wb")
            f.write(withhacks.__doc__.encode('utf8'))
            f.close()
        else:
            f = open(readme, "rb")
            if f.read() != withhacks.__doc__:
                f.close()
                f = open(readme, "wb")
                f.write(withhacks.__doc__.encode('utf8'))
                f.close()
