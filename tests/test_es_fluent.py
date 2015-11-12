#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_es_fluent
----------------------------------

Tests for `es_fluent` module.
"""

import unittest
import datetime
from mock import patch

from es_fluent.builder import QueryBuilder
from es_fluent.filters import Exists, Or, And, Range, Term, Terms, ScriptID, \
    Age, Missing
from es_fluent.script_fields import ScriptField, ScriptIDField


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
        and_filter.add_filter(Exists("value"))
        self.assertEquals({"and": [
            {"exists": {"field": "value"}}
        ]}, and_filter.to_query())

    def test_empty_or_filter(self):
        or_filter = Or()
        self.assertEquals({"or": []}, or_filter.to_query())

    def test_single_clause_or_filter(self):
        or_filter = Or()
        or_filter.add_filter(Exists("value"))
        self.assertEquals({"or": [
            {"exists": {"field": "value"}}
        ]}, or_filter.to_query())

    def test_query_builder_and_filter(self):
        query_builder = QueryBuilder()
        query_builder.and_filter(
            Exists('value')
        )
        self.assertEquals(
            query_builder.to_query()['filter'],
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
            Exists('field_one')
        )
        query_builder.and_filter(
            Exists('field_two')
        )
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "and": [
                    {"exists": {"field": "field_one"}},
                    {"exists": {"field": "field_two"}}
                ]
            }
        )

    def test_filter_clobber(self):
        query_builder = QueryBuilder()
        query_builder.add_filter(Exists('value'))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {"exists": {"field": "value"}},
        )
        query_builder.add_filter(Exists('value_two'))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {"exists": {"field": "value_two"}},
        )

    def test_nested_or_filter(self):
        """
        It should be possible to add another multi-clause filter inside
        of an existing multi-clause filter and have them nest correctly.
        """
        query_builder = QueryBuilder()
        query_builder.or_filter(
            Exists('value')
        )
        or_filter = query_builder.find_filter(Or)
        or_filter.or_filter(
            Exists('nested_value')
        )
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "or": [
                    {"exists": {"field": "value"}},
                    {
                        "or": [
                            {"exists": {
                                "field": "nested_value"
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
            Exists('value')
        )
        and_filter = query_builder.find_filter(And)
        and_filter.and_filter(
            Exists('nested_value')
        )
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "and": [
                    {"exists": {"field": "value"}},
                    {
                        "and": [
                            {"exists": {
                                "field": "nested_value"
                            }}
                        ]
                    }
                ]
            }
        )

    def test_inversion_and(self):
        """
        Filters can return an inverted version of themselve using the `~`
        operator.
        """
        query_builder = QueryBuilder()
        query_builder.and_filter(
            ~Exists('and_not_value')
        )
        query_builder.and_filter(
            Exists('exists_value')
        )
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "and": [
                    {"not": {"exists": {"field": "and_not_value"}}},
                    {"exists": {"field": "exists_value"}}
                ]
            }
        )

    def test_inversion_or(self):
        """
        Filters can return an inverted version of themselve using the `~`
        operator.
        """
        query_builder = QueryBuilder()
        query_builder.or_filter(
            ~Exists('and_not_value')
        )
        query_builder.or_filter(
            Exists('exists_value')
        )
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "or": [
                    {"not": {"exists": {"field": "and_not_value"}}},
                    {"exists": {"field": "exists_value"}}
                ]
            }
        )

    def test_range_full(self):
        """
        All valid range comparators should be represented in the final query.
        """
        query_builder = QueryBuilder()
        query_builder.add_filter(Range(
            'field', lte=0.5, lt=0.6, gt=0.7, gte=0.8
        ))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "range": {
                    "field": {
                        "lte": 0.5,
                        "lt": 0.6,
                        "gt": 0.7,
                        "gte": 0.8
                    }
                }
            }
        )

    def test_range_partial(self):
        """
        If only a specific range criteria is provided, only it should appear
        in the final query.
        """
        query_builder = QueryBuilder()
        query_builder.add_filter(Range(
            'field', lte=0.5
        ))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "range": {
                    "field": {
                        "lte": 0.5,
                    }
                }
            }
        )

    def test_term(self):
        query_builder = QueryBuilder()
        query_builder.add_filter(Term(
            'field', 0.5
        ))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "term": {"field": 0.5}
            }
        )

    def test_terms(self):
        query_builder = QueryBuilder()
        query_builder.add_filter(Terms(
            'field', 0.5
        ))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                "terms": {"field": 0.5}
            }
        )

    def test_script_id(self):
        query_builder = QueryBuilder()
        query_builder.add_filter(ScriptID(
            'name', 'script_id', {"key": 0.5}
        ))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                'name': {
                    "script_id": "script_id",
                    "lang": "groovy",
                    "params": {
                        "key": 0.5
                    }
                }
            }
        )

    def test_multi_script_id(self):
        query_builder = QueryBuilder()
        query_builder.add_filter(ScriptID(
            'name', 'script_id', {"key": 0.5}
        ))
        query_builder.add_filter(ScriptID(
            'name_two', 'script_id_two', {"key_two": 0.4}
        ))
        self.assertEquals(
            query_builder.to_query()['filter'],
            {
                'name': {
                    "script_id": "script_id",
                    "lang": "groovy",
                    "params": {
                        "key": 0.5
                    }
                },
                'name_two': {
                    "script_id": "script_id_two",
                    "lang": "groovy",
                    "params": {
                        "key_two": 0.4
                    }
                }
            }
        )

    def test_script_field(self):
        query_builder = QueryBuilder()
        query_builder.add_script_field(ScriptField(
            'my_script',
            '_source.field * factor',
            factor=2
        ))
        self.assertEquals(query_builder.to_query()['script_fields'], {
            'my_script': {
                'lang': 'groovy',
                'script': '_source.field * factor',
                'params': {
                    'factor': 2
                }
            }
        })

    def test_script_id_field(self):
        query_builder = QueryBuilder()
        query_builder.add_script_field(ScriptIDField(
            'my_script',
            'my_script_id',
            factor=2
        ))
        self.assertEquals(query_builder.to_query()['script_fields'], {
            'my_script': {
                'lang': 'groovy',
                'script_id': 'my_script_id',
                'params': {
                    'factor': 2
                }
            }
        })

    def test_add_and_shorthand(self):
        query_builder = QueryBuilder()
        query_builder.and_filter('exists', 'some_field')
        query_builder.and_filter('range', 'range_field', lte=5)
        self.assertEquals(query_builder.to_query()['filter'], {
            'and': [
                {'exists': {'field': 'some_field'}},
                {'range': {'range_field': {'lte': 5}}}
            ]
        })

    def test_add_or_shorthand(self):
        query_builder = QueryBuilder()
        query_builder.or_filter('range', 'range_field', gte=5)
        self.assertEquals(query_builder.to_query()['filter'], {
            'or': [
                {'range': {'range_field': {'gte': 5}}}
            ]
        })

    def test_add_shorthand_negation(self):
        query_builder = QueryBuilder()
        query_builder.and_filter('~exists', 'some_field')
        self.assertEquals(query_builder.to_query()['filter'], {
            'and': [
                {'not': {'exists': {'field': 'some_field'}}},
            ]
        })

    def test_source_default(self):
        query_builder = QueryBuilder()
        self.assertEqual(query_builder.to_query()['_source'], True)

    def test_source_enable_disable(self):
        query_builder = QueryBuilder()

        query_builder.disable_source()
        self.assertEqual(query_builder.to_query()['_source'], False)

        query_builder.enable_source()
        self.assertEqual(query_builder.to_query()['_source'], True)

    def test_sort_default(self):
        query_builder = QueryBuilder()
        query_builder.sort('test')
        self.assertEqual(query_builder.to_query()['sort'], [
            {'test': 'asc'}
        ])

    def test_sort_desc(self):
        query_builder = QueryBuilder()
        query_builder.sort('test', 'desc')
        self.assertEqual(query_builder.to_query()['sort'], [
            {'test': 'desc'}
        ])

    def test_sort_asc(self):
        query_builder = QueryBuilder()
        query_builder.sort('test', 'asc')
        self.assertEqual(query_builder.to_query()['sort'], [
            {'test': 'asc'}
        ])

    def test_sort_reset(self):
        query_builder = QueryBuilder()
        query_builder.sort('test', 'asc')
        self.assertEqual(query_builder.to_query()['sort'], [
            {'test': 'asc'}
        ])
        query_builder.sort_reset()
        self.assertFalse('sort' in query_builder.to_query())

    @patch('es_fluent.filters._now')
    def test_age_filter(self, mock_now):
        mock_now.return_value = datetime.datetime(2015, 1, 1, 2, 0, 0)
        age = Age('some_field', lte=3600, gte=1800, gt=1860, lt=1920)
        self.assertEqual(age.to_query(), {
            'range': {
                'some_field': {
                    'gte': '2015-01-01T01:00:00',
                    'lte': '2015-01-01T01:30:00',
                    'lt': '2015-01-01T01:29:00',
                    'gt': '2015-01-01T01:28:00',
                }
            }
        })

    def test_missing_filter(self):
        missing = Missing('field_name')
        self.assertEqual(missing.to_query(), {
            "missing": {
                "field": "field_name"
            }
        })

    def test_size(self):
        query_builder = QueryBuilder()
        self.assertNotIn('size', query_builder.to_query())
        query_builder.size = 50
        self.assertIn('size', query_builder.to_query())
        self.assertEqual(query_builder.to_query()['size'], 50)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
