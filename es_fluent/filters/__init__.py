import re
import datetime

# A dictionary of filter classes, keyed by their name attributes.
FILTER_REGISTRY = {}


def _now():
    """
    Mockable proxy to ``datetime.datetime.now()``
    """
    return datetime.datetime.now()


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
    The base filter.
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


class Generic(Filter):
    """
    Contains a generic list of filters. Serialized as a dictionary.
    """
    def __init__(self):
        self.filters = []

    def is_empty(self):
        """
        :return: ``True`` if this filter has nested clauses ``False``.
        """
        return len(self.filters) == 0

    def add_filter(self, filter_or_string, *args, **kwargs):
        """
        Appends a filter.
        """
        self.filters.append(build_filter(filter_or_string, *args, **kwargs))

        return self

    def and_filter(self, filter_or_string, *args, **kwargs):
        """
        Adds a list of :class:`~es_fluent.filters.And` clauses, automatically
        generating :class:`~es_fluent.filters.And` filter if it does not
        exist.
        """
        and_filter = self.find_filter(And)

        if and_filter is None:
            and_filter = And()
            self.filters.append(and_filter)

        and_filter.add_filter(build_filter(
            filter_or_string, *args, **kwargs))

        return and_filter

    def or_filter(self, filter_or_string, *args, **kwargs):
        """
        Adds a list of :class:`~es_fluent.filters.Or` clauses, automatically
        generating the an :class:`~es_fluent.filters.Or` filter if it does not
        exist.
        """
        or_filter = self.find_filter(Or)

        if or_filter is None:
            or_filter = Or()
            self.filters.append(or_filter)

        or_filter.add_filter(build_filter(
            filter_or_string, *args, **kwargs
        ))

        return or_filter

    def find_filter(self, filter_cls):
        """
        Find or create a filter instance of the provided ``filter_cls``. If it
        is found, use remaining arguments to augment the filter otherwise
        create a new instance of the desired type and add it to the
        current :class:`~es_fluent.builder.QueryBuilder` accordingly.
        """
        for filter_instance in self.filters:
            if isinstance(filter_instance, filter_cls):
                return filter_instance

        return None


class Dict(Generic):
    """
    Contains a generic dictionary of filters e.g. in a top level ES Query
    we may have::

        { "filtered": {"filter": {"and": {...}, "or": {...}, "exists": {...} }

    The Dict filter may represent the dictionary inside of "filtered.filter".
    """
    def to_query(self):
        """
        Iterates over all filters and converts them to an Elastic HTTP API
        suitable query.

        Note: each :class:`~es_fluent.filters.Filter` is free to set it's own
        filter dictionary. ESFluent does not attempt to guard against filters
        that may clobber one another.  If you wish to ensure that filters are
        isolated, nest them inside of a boolean filter such as
        :class:`~es_fluent.filters.And` or :class:`~es_fluent.filters.Or`.
       """
        query = {}
        for filter_instance in self.filters:
            filter_query = filter_instance.to_query()
            query.update(filter_query)

        return query


class And(Generic):
    """
    A multi-clause filter that ands's all sub-filters added to it.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-and-filter.html>`_.
    """
    name = 'and'

    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            clauses.append(filter_instance.to_query())
        return {
            "and": clauses
        }


class Or(Generic):
    """
    A multi-clause filter that ``ors`` all sub-filters added to it.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-or-filter.html>`_.
    """
    name = 'or'

    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            clauses.append(filter_instance.to_query())
        return {
            "or": clauses
        }


class Not(Dict):
    """
    A filter that inverts it's clauses.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-not-filter.html>`_.
    """
    name = 'not'

    def to_query(self):
        query = super(Not, self).to_query()
        return {
            "not": query
        }


class Terminal(Filter):
    """
    A filter that cannot contain nested filters. Merge behavior is to clobber
    existing clauses rather than appending additional clauses.
    """
    def add_filter(self, filter_instance):
        """
        As a :class:`~es_fluent.filters.Terminal` filter, adding nested filters
        is not allowed.
        """
        raise RuntimeError("Terminal filters do not support sub-filters")

    def find_filter(self, filter_cls):
        """
        As a :class:`~es_fluent.filters.Terminal` filter, adding nested filters
        is not allowed and therefore, finding sub-filters is not supported.
        """
        raise RuntimeError("Terminal filters do not support sub-filters")


class Custom(Terminal):
    """
    Allows for an entirely custom dictionary to be used and passed verbatim
    when `to_query` is invoked.
    """
    name = 'custom'

    def __init__(self, query):
        self.query = query

    def to_query(self):
        return self.query


class Exists(Terminal):
    """
    Checks whether a field exists in the source document.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-exists-filter.html>`_.
    """
    name = 'exists'

    def __init__(self, value):
        self.value = value

    def to_query(self):
        return {
            "exists": {
                "field": self.value
            }
        }


class Range(Dict):
    """
    A Filter for ranges of values, supporting ``lt``, ``lte``, ``gt``, ``gte``
    comparisons.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-range-filter.html>`_.
    """
    name = 'range'

    def __init__(self, name, gte=None, lte=None, lt=None, gt=None):
        self.name = name
        self.gte = gte
        self.lte = lte
        self.lt = lt
        self.gt = gt

    def to_query(self):
        criteria = {}
        for comparator in ['lte', 'lt', 'gt', 'gte']:
            if getattr(self, comparator) is not None:
                criteria[comparator] = getattr(self, comparator)

        return {
            "range": {
                self.name: criteria
            }
        }


class Age(Dict):
    """
    Similar to a range filter. Operates on times. When querified, we convert
    the age in seconds into a datetime relative to the current
    ``datetime.datetime.now()``.
    """
    name = 'age'

    def __init__(self, name, gte=None, lte=None, lt=None, gt=None):
        self.name = name
        # Yes, this flipping of gt/lt is deliberate. Saying something is
        # less than 3600 seconds old is equivalent to saying it's timestamp
        # is greater that `now` - 3600.
        self.lte = float(gte) if gte is not None else None
        self.gte = float(lte) if lte is not None else None
        self.gt = float(lt) if lt is not None else None
        self.lt = float(gt) if gt is not None else None

    def to_query(self):
        criteria = {}
        now = _now()
        for comparator in ['lte', 'lt', 'gt', 'gte']:
            if getattr(self, comparator) is not None:
                seconds = getattr(self, comparator)
                age = datetime.timedelta(seconds=seconds)
                value = (now - age).isoformat()
                criteria[comparator] = value
        return {
            "range": {
                self.name: criteria
            }
        }


class Term(Terminal):
    """
    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-term-filter.html>`_.
    """
    name = 'term'

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_query(self):
        return {
            "term": {
                self.name: self.value
            }
        }


class Missing(Terminal):
    """
    Filters documents that to do not contain a given field.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-term-filter.html>`_.
    """
    name = 'missing'

    def __init__(self, name):
        self.name = name

    def to_query(self):
        return {
            "missing": {
                "field": self.name
            }
        }


class Terms(Terminal):
    """
    Matches documents that contain multiple exact values.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-terms-filter.html>`_.
    """
    name = 'terms'

    def __init__(self, name, values):
        self.name = name
        self.values = values

    def to_query(self):
        return {
            "terms": {
                self.name: self.values
            }
        }


class RegExp(Terminal):
    """
    Matches documents whose given field matches a provided regular expression.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-terms-filter.html>`_.
    """
    name = 'regexp'

    def __init__(self, name, expression):
        # Immediately try to compile the expression to check it's validity.
        re.compile(expression)
        self.name = name
        self.expression = expression

    def to_query(self):
        return {
            "regexp": {
                self.name: self.expression
            }
        }


class Script(Generic):
    """
    Represents script criteria.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-script-filter.html>`_.
    """
    name = 'script'

    def to_query(self):
        query = {}

        for filter_instance in self.filters:
            filter_query = filter_instance.to_query()
            query.update(filter_query)

        return query


class ScriptID(Terminal):
    """
    Represents a pre-indexed script filter.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-script-filter.html>`_.
    """
    name = 'script_id'

    def __init__(self, name, script_id, script_params, lang='groovy'):
        self.name = name
        self.script_id = script_id
        self.script_params = script_params
        self.lang = lang

    def to_query(self):
        return {
            self.name: {
                'lang': self.lang,
                'script_id': self.script_id,
                'params': self.script_params
            }
        }
