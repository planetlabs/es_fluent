class Filter(object):
    pass


class Generic(Filter):
    """
    Contains a generic list of filters.
    """
    def __init__(self):
        self.filters = []

    def add_filter(self, filter_instance):
        """
        Appends a filter.
        """
        self.filters.append(filter_instance)

        return self

    def and_filter(self, *args):
        """
        Adds a list of `and` clauses, automatically generating the `and` filter
        if it does not already exist.
        """
        and_filter = self.find_filter(And)

        if and_filter is None:
            and_filter = And()
            self.filters.append(and_filter)

        for arg in args:
            and_filter.add_filter(arg)

        return and_filter

    def or_filter(self, *args):
        """
        Adds a list of `or` clauses, automatically generating the `or` filter
        if it does not already exist.
        """
        or_filter = self.find_filter(Or)

        if or_filter is None:
            or_filter = Or()
            self.filters.append(or_filter)

        for arg in args:
            or_filter.add_filter(arg)

        return or_filter

    def find_filter(self, filter_cls):
        """
        Find or create a filter instance of the provided filter_cls. If it is
        found, use remaining arguments to augment the filter otherwise create
        a new instance of the desired type and add it to the query_builder
        accordingly.
        """
        for filter_instance in self.filters:
            if isinstance(filter_instance, filter_cls):
                return filter_instance

        return None


class Dict(Generic):
    """
    Contains a generic dictionary of filters e.g. in a top level ES Query
    we may have:
        { "filtered": {"filter": {"and": {...}, "or": {...}, "exists": {...} }
    The Dict filter may represent the dictionary inside of "filtered.filter".
    """
    def to_query(self):
        """
        Iterates over all filters and converts them to an Elastic HTTP API
        suitable query.

        Note: each Filter is free to set it's own filter dictionary. ES Fluent
        does not attempt to guard against filters that may clobber one another.
        If you wish to ensure that filters are isolated, nested them inside
        of a boolean filter such as And or Or.
        """
        query = {}
        for filter_instance in self.filters:
            filter_query = filter_instance.to_query()
            query.update(filter_query)

        return query


class And(Generic):
    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            clauses.append(filter_instance.to_query())
        return {
            "and": clauses
        }


class Or(Generic):
    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            clauses.append(filter_instance.to_query())
        return {
            "or": clauses
        }


class Terminal(Filter):
    """
    A filter that cannot contain nested filters. Merge behavior is to clobber
    existing clauses rather than appending additional clauses.
    """
    def add_filter(self, filter_instance):
        raise RuntimeError("Terminal filters do not support sub-filters")

    def find_filter(self, filter_cls):
        raise RuntimeError("Terminal filters do not support sub-filters")


class Exists(Terminal):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_query(self):
        return {
            "exists": {
                self.name: self.value
            }
        }
