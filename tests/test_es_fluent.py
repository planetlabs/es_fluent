#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_es_fluent
----------------------------------

Tests for `es_fluent` module.
"""

import unittest

from es_fluent.builder import QueryBuilder
from es_fluent.filters import Exists, Or, And


class TestEs_fluent(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fluent_constructor(self):
        query_builder = QueryBuilder()
        self.assertIsNotNone(query_builder)

    def test_empty_and_filter(self):
        and_filter = And()
        self.assertEquals({"and": []}, and_filter.to_query())

    def test_single_clause_and_filter(self):
        and_filter = And()
        and_filter.add_filter(Exists("field", "value"))
        self.assertEquals({"and": [
            {"exists": {"field": "value"}}
        ]}, and_filter.to_query())

    def test_empty_or_filter(self):
        or_filter = Or()
        self.assertEquals({"or": []}, or_filter.to_query())

    def test_single_clause_or_filter(self):
        or_filter = Or()
        or_filter.add_filter(Exists("field", "value"))
        self.assertEquals({"or": [
            {"exists": {"field": "value"}}
        ]}, or_filter.to_query())

    def test_query_builder_and_filter(self):
        query_builder = QueryBuilder()
        query_builder.and_filter(
            Exists('field', 'value')
        )
        self.assertEquals(
            query_builder.to_query()['filters'],
            {
                "and": [
                    {"exists": {"field": "value"}}
                ]
            }
        )

    def test_multi_and_filter(self):
        """
        When a given filter type already exists, we smartly append to it if
        possible rather than clobbering an existing filter.
        """
        query_builder = QueryBuilder()
        query_builder.and_filter(
            Exists('field', 'value')
        )
        query_builder.and_filter(
            Exists('field_two', 'value_two')
        )
        self.assertEquals(
            query_builder.to_query()['filters'],
            {
                "and": [
                    {"exists": {"field": "value"}},
                    {"exists": {"field_two": "value_two"}}
                ]
            }
        )

    def test_filter_clobber(self):
        query_builder = QueryBuilder()
        query_builder.add_filter(Exists('field', 'value'))
        self.assertEquals(
            query_builder.to_query()['filters'],
            {"exists": {"field": "value"}},
        )
        query_builder.add_filter(Exists('field_two', 'value_two'))
        self.assertEquals(
            query_builder.to_query()['filters'],
            {"exists": {"field_two": "value_two"}},
        )

    def test_nested_or_filter(self):
        """
        It should be possible to add another multi-clause filter inside
        of an existing multi-clause filter and have them nest correctly.
        """
        query_builder = QueryBuilder()
        query_builder.or_filter(
            Exists('field', 'value')
        )
        or_filter = query_builder.find_filter(Or)
        or_filter.or_filter(
            Exists('nested_field', 'nested_value')
        )
        self.assertEquals(
            query_builder.to_query()['filters'],
            {
                "or": [
                    {"exists": {"field": "value"}},
                    {
                        "or": [
                            {"exists": {
                                "nested_field": "nested_value"
                            }}
                        ]
                    }
                ]
            }
        )

    def test_nested_and_filter(self):
        """
        It should be possible to add another multi-clause filter inside
        of an existing multi-clause filter and have them nest correctly.
        """
        query_builder = QueryBuilder()
        query_builder.and_filter(
            Exists('field', 'value')
        )
        and_filter = query_builder.find_filter(And)
        and_filter.and_filter(
            Exists('nested_field', 'nested_value')
        )
        self.assertEquals(
            query_builder.to_query()['filters'],
            {
                "and": [
                    {"exists": {"field": "value"}},
                    {
                        "and": [
                            {"exists": {
                                "nested_field": "nested_value"
                            }}
                        ]
                    }
                ]
            }
        )

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
