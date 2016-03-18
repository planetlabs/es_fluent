# A dictionary of filter classes, keyed by their name attributes.
FILTER_REGISTRY = {}


class FilterRegistry(type):
    """
    Metaclass used to automatically register new filter classes in our filter
    registry. Enables shorthand filter notation.

        >>> from es_fluent.builder import QueryBuilder
        >>> query_builder = QueryBuilder()
        >>> query_builder.add_filter('missing', 'boop').to_query()['filter']
        {'missing': {'field': 'field_name'}}
    """
    def __new__(cls, clsname, bases, attrs):
        newclass = super(FilterRegistry, cls).__new__(
            cls, clsname, bases, attrs)
        register_filter(newclass)
        return newclass


def register_filter(filter_cls):
    """
    Adds the ``filter_cls`` to our registry.
    """
    if filter_cls.name is None:
        return
    elif filter_cls.name in FILTER_REGISTRY:
        raise RuntimeError(
            "Filter class already registered: {}".format(filter_cls.name))
    else:
        FILTER_REGISTRY[filter_cls.name] = filter_cls


def build_filter(filter_or_string, *args, **kwargs):
    """
    Overloaded filter construction. If ``filter_or_string`` is a string
    we look up it's corresponding class in the filter registry and return it.
    Otherwise, assume ``filter_or_string`` is an instance of a filter.

    :return: :class:`~es_fluent.filters.Filter`
    """
    if isinstance(filter_or_string, basestring):
        # Names that start with `~` indicate a negated filter.
        if filter_or_string.startswith('~'):
            filter_name = filter_or_string[1:]
            return ~FILTER_REGISTRY[filter_name](*args, **kwargs)
        else:
            filter_name = filter_or_string
            return FILTER_REGISTRY[filter_name](*args, **kwargs)
    else:
        return filter_or_string


class Filter(object):
    """
    The base filter. Subclasses of this Filter will automatically register
    themselves on import.
    """

    #: The shorthand name of the filter.
    name = None

    #: Auto-register any Filter subclass with our registry.
    __metaclass__ = FilterRegistry

    def __invert__(self):
        """
        Returns this filter wrapped in a :class:`es_fluent.filters.Not` filter.
        :
        """
        not_filter = Not()
        not_filter.add_filter(self)
        return not_filter

    def to_query(self):
        """
        Serializes this ``Filter`` and any descendants into a json-serializable
        dictionary suitable for use with the elasticsearch api.
        """
        raise NotImplementedError()


from .core import (
    Age,
    And,
    Custom,
    Dict,
    Exists,
    Generic,
    Missing,
    Not,
    Or,
    Range,
    RegExp,
    Script,
    ScriptID,
    Term,
    Terminal,
    Terms,
)

from .geometry import (
    GeoJSON,
    IndexedShape,
)
