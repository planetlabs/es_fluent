from es_fluent.filters import And, Dict


class QueryBuilder(object):
    def __init__(self):
        self.root_filter = Dict()

    def and_filter(self, *args):
        """
        Convenience method to delegate to the root_filter to generate an `and`
        clause.
        """
        self.root_filter.and_filter(*args)
        return self

    def or_filter(self, *args):
        """
        Convenience method to delegate to the root_filter to generate an `or`
        clause.
        """
        self.root_filter.or_filter(*args)
        return self

    def add_filter(self, filter_instance):
        self.root_filter.add_filter(filter_instance)
        return self

    def find_filter(self, filter_cls):
        return self.root_filter.find_filter(filter_cls)

    def to_query(self):
        return {
            "filters": self.root_filter.to_query()
        }

