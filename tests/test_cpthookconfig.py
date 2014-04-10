import os.path
import sys
import tempfile
import unittest2 as unittest

from cpthook import CptHookConfig
import cpthook


def cfgfile():
    """Return name of config file corresponding with calling function name"""
    fun_name = sys._getframe(1).f_code.co_name
    return '/'.join((
        os.path.dirname(os.path.realpath(__name__)),
        'tests',
        'configs',
        fun_name + '.cfg'))


class UnitTests(unittest.TestCase):

    def test_nonexistent_config(self):
        def f():
            h = CptHookConfig('doesnotexist.cfg')
        self.assertRaises(IOError, f)

    def test_empty_repo_block(self):
        h = CptHookConfig(cfgfile())

    def test_cyclical_dependency(self):
        config = cfgfile()
        def f():
            h = CptHookConfig(config)
        self.assertRaises(cpthook.CyclicalDependencyException, f)
