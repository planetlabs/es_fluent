Filters
=======

Filters typically have corresponding elasticsearch filters. ESFluent helps
intelligently compose them and provides a common interface, via
:func:`~es_fluent.filters.Filter.to_query` whose responsibility is to
generate the corresponding elasticsearch filter dictionary.

A Filter can :class:`~es_fluent.filters.geometry.Geometry` clean up data and
also generate novel queries.

Basic Filters
-------------

.. automodule:: es_fluent.filters.core
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:

Geometry Filters
----------------

.. automodule:: es_fluent.filters.geometry
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:

Utilities
---------

.. autoclass:: es_fluent.filters.FilterRegistry
.. autoclass:: es_fluent.filters.Filter
.. autofunction:: es_fluent.filters.build_filter
