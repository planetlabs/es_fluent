===============================
ESFluent
===============================

.. image:: https://travis-ci.org/planetlabs/es_fluent.svg
        :target: https://travis-ci.org/planetlabs/es_fluent

.. image:: https://img.shields.io/pypi/v/es_fluent.svg
        :target: https://pypi.python.org/pypi/es_fluent


A user-friendly module for managing and composing elasticsearch queries.

.. doctest::

  >>> from es_fluent.builder import QueryBuilder
  >>> query_builder = QueryBuilder()
  >>> query_builder.and_filter('term', 'planet', 'earth')
  >>> query_builder.enable_source()
  >>> query_builder.to_query()
  {'filter': {'and': [{'term': {'planet': 'earth'}}]}, 'fields': [], '_source': True}

Supported Servers
-----------------

This version of ESFluent only supports elasticsearch 6.x.

Features
--------

* A Fluent API for generating and composing queries.
* Support for many elasticsearch filter types.
* Pluggable filter definitions, currently we simply model existing
  elasticsearch filters.


Concepts and Walkthrough
------------------------

We'll walk through some examples of getting started with ESFluent. If you're
the type that likes to shoot first and ask questions later, the tests will
exercise all of the API concepts.

The QueryBuilder
~~~~~~~~~~~~~~~~

The QueryBuilder encapsulates the entire query. It features
a :func:`~es_fluent.filters.core.Filter.to_query` method which generates a JSON
payload suitable for POST'ing to elasticsearch.

For the most part, you'll be adding chains of filters. The QueryBuilder offers
additional support for:

* Enabling or disabling the _source document. By default this is not returned,
  but many use cases demand it. See
  :func:`~es_fluent.builder.QueryBuilder.enable_source` and
  :func:`~es_fluent.builder.QueryBuilder.disable_source`.
* Limiting returned fields. See :func:`~es_fluent.builder.QueryBuilder.add_field`.
* Configuring sorting. See :func:`~es_fluent.builder.QueryBuilder.sort`.

To create a :class:`~es_fluent.builder.QueryBuilder` instance:

.. code-block:: python

  from es_fluent.builder import QueryBuilder
  query = QueryBuilder()

Filter Basics
~~~~~~~~~~~~~

Having created a QueryBuilder instance, you're likely going to want
to add filter criteria. There are two ways of doing this: importing the filter
class directly and creating an instance of a filter by hand then augmenting
your QueryBuilder instance:

.. code-block:: python

  from es_fluent.builder import QueryBuilder
  from es_fluent.filters import Term

  query = QueryBuilder()
  query.and_filter(Term('field_name', 'field_value'))

The alternative approach is to use a shorthand notation:

.. code-block:: python

  from es_fluent.builder import QueryBuilder

  query = QueryBuilder()
  # Args and kwargs are forwarded to appropriate constructors.
  query.and_filter('range', 'field_name', lte=0.5)


Each Filter class has a registered name - see the `name` class attribute - that
is used as it's shorthand identifier.

Not filter
~~~~~~~~

.. code-block:: python

  from es_fluent.builder import QueryBuilder
  from es_fluent.filters import Term

  query = QueryBuilder()
  query.not_filter(Term('field_name', 'field_value'))


This is equivalent to:

.. code-block:: python

  from es_fluent.builder import QueryBuilder
  query = QueryBuilder()
  query.not_filter('term', 'field_name', 'field_value')

Boolean Filters
~~~~~~~~~~~~~~~

Boolean filters contain a list of sub-filters. The API provides conveniences
for creating nested and / or clauses:

.. code-block:: python

  from es_fluent.builder import QueryBuilder
  query = QueryBuilder()
  query.or_filter('term', 'field_name', 'field_value')
  query.or_filter('term', 'another_field', 'another_value')

