"""
Exercises the RegExp filter.
"""
import unittest
import re

from es_fluent.filters import RegExp


class TestEs_fluent_filters(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_invalid_regexp(self):
        with self.assertRaises(re.error):
            RegExp("field", r"[$")

    def test_regexp(self):
        re = RegExp(
            "field", r".*test_Exp$"
        )
        self.assertEquals(
            re.to_query(),
            {
                "regexp": {"field": ".*test_Exp$"}
            }
        )
