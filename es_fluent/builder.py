from es_fluent.filters import Dict
from es_fluent.script_fields import ScriptFields
from es_fluent.fields import Fields


class QueryBuilder(object):
    def __init__(self):
        self.root_filter = Dict()
        self.script_fields = ScriptFields()
        self.fields = Fields()

        self.sorts = []
        self.source = True
        self._size = None

    @property
    def size(self):
        """
        Sets current size limit of the ES response, which limits the number of
        documents returned. By default this is unset and the number of
        documents returned is up to ES.

        :return:
            The current size limit.
        """
        return self._size

    @size.setter
    def size(self, size):
        """
        Sets the size of the ES response.

        :param size: The number of documents to limit the response to.
        """
        self._size = size

    def add_filter(self, filter_or_string, *args, **kwargs):
        """
        Convenience method to append to root_filter

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.root_filter.add_filter(filter_or_string, *args, **kwargs)
        return self

    def and_filter(self, filter_or_string, *args, **kwargs):
        """
        Convenience method to delegate to the root_filter to generate an
        :class:`~es_fluent.filters.core.And` clause.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.root_filter.and_filter(filter_or_string, *args, **kwargs)
        return self

    def or_filter(self, filter_or_string, *args, **kwargs):
        """
        Convenience method to delegate to the root_filter to generate an `or`
        clause.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.root_filter.or_filter(filter_or_string, *args, **kwargs)
        return self

    def not_filter(self, filter_or_string, *args, **kwargs):
        """
        Convenience method to delegate to the root_filter to generate an `not`
        clause.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.root_filter.not_filter(filter_or_string, *args, **kwargs)
        return self

    def add_field(self, field_instance):
        """
        Adds a field to the query builder. The default behavior is
        to return all fields. Explicitly adding a single field will
        result in only that source field being returned.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.fields.add_field(field_instance)
        return self

    def add_script_field(self, field_instance):
        """
        Add a script field to the query. The `field_instance` should be
        an instance of `es_fluent.script_fields`.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.script_fields.add_field(field_instance)
        return self

    def find_filter(self, filter_cls):
        """
        Finds an existing filter using a filter class `filter_cls`. If not
        found, None is returned.

        This method is useful in cases where one wants to modify and extend
        and existing clause, a common example might be an
        :class:`~es_fluent.filters.core.And` filter. The method only looks in the
        query's top-level filter and does not recurse.

        :param: ``filter_cls``
            The the :class:`~es_fluent.filters.Filter` class
            to find.
        """
        return self.root_filter.find_filter(filter_cls)

    def to_query(self):
        result = {}

        if not self.root_filter.is_empty():
            result['query'] = self.root_filter.to_query()

        if not self.script_fields.is_empty():
            result['script_fields'] = self.script_fields.to_query()

        if self.fields.to_query():
            result['_source'] = self.fields.to_query()
        else:
            result['_source'] = self.source

        # We don't bother with representing sort as an object.
        if len(self.sorts):
            result['sort'] = self.sorts

        if self._size is not None:
            result['size'] = self._size

        return result

    def disable_source(self):
        """
        Don't include ``_source`` document in results.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.source = False

        return self

    def enable_source(self):
        """
        Include ``_source`` document in results.

        :return: :class:`~es_fluent.builder.QueryBuilder`
        """
        self.source = True

    def sort(self, field, direction="asc"):
        """
        Adds sort criteria.
        """
        if not isinstance(field, basestring):
            raise ValueError("Field should be a string")
        if direction not in ["asc", "desc"]:
            raise ValueError("Sort direction should be `asc` or `desc`")

        self.sorts.append({field: direction})

    def remove_sort(self, field_name):
        """
        Clears sorting criteria affecting ``field_name``.
        """
        self.sorts = [dict(field=value) for field, value in self.sorts if field
                      is not field_name]

    def sort_reset(self):
        """
        Resets sorting criteria.
        """
        self.sorts = []
