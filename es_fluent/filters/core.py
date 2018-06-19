import re
import datetime

from . import Filter, build_filter


def _now():
    """
    Mockable proxy to ``datetime.datetime.now()``
    """
    return datetime.datetime.now()


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
        return all(_filter.is_empty() for _filter in self.filters)

    def add_filter(self, filter_or_string, *args, **kwargs):
        """
        Appends a filter.
        """
        self.filters.append(build_filter(filter_or_string, *args, **kwargs))

        return self

    def and_filter(self, filter_or_string, *args, **kwargs):
        """
        Adds a list of :class:`~es_fluent.filters.core.And` clauses, automatically
        generating :class:`~es_fluent.filters.core.And` filter if it does not
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
        Adds a list of :class:`~es_fluent.filters.core.Or` clauses, automatically
        generating the an :class:`~es_fluent.filters.core.Or` filter if it does not
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

    def not_filter(self, filter_or_string, *args, **kwargs):
        """
        Adds a list of :class:`~es_fluent.filters.core.Not` clauses, automatically
        generating :class:`~es_fluent.filters.core.Not` filter if it does not
        exist.
        """
        not_filter = self.find_filter(Not)

        if not_filter is None:
            not_filter = Not()
            self.filters.append(not_filter)

        not_filter.add_filter(build_filter(
            filter_or_string, *args, **kwargs))

        return not_filter

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
        :class:`~es_fluent.filters.core.And` or
        :class:`~es_fluent.filters.core.Or`.
       """
        query = {}
        for filter_instance in self.filters:
            if filter_instance.is_empty():
                continue
            filter_query = filter_instance.to_query()
            query.update(filter_query)

        return query

    def is_empty(self):
        """
        :return:
            ``True`` if this filter has nested clauses, otherwise ``False``.
        """
        return len(self.filters) == 0


class Bool(Generic):
    """
    A multi-clause filter that bool's all sub-filters added to it.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-and-filter.html>`_.
    """
    name = 'bool'

    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            if filter_instance.is_empty():
                continue
            clauses.append(filter_instance.to_query())
        return {
            "bool": clauses
        }


class And(Generic):
    """
    A multi-clause filter that ands's all sub-filters added to it.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-and-filter.html>`_.
    """
    name = 'and'

    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            if filter_instance.is_empty():
                continue
            clauses.append(filter_instance.to_query())
        return {
            "filter": clauses
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
            if filter_instance.is_empty():
                continue
            clauses.append(filter_instance.to_query())
        return {
            "should": clauses
        }


class Not(Dict):
    """
    A filter that inverts it's clauses.

    `Elastic docs <https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-not-filter.html>`_.
    """
    name = 'not'

    def to_query(self):
        clauses = []
        for filter_instance in self.filters:
            if filter_instance.is_empty():
                continue
            clauses.append(filter_instance.to_query())
        return {
            "must_not": clauses
        }

class Terminal(Filter):
    """
    A filter that cannot contain nested filters. Merge behavior is to clobber
    existing clauses rather than appending additional clauses.
    """
    def add_filter(self, filter_instance):
        """
        As a :class:`~es_fluent.filters.core.Terminal` filter, adding nested filters
        is not allowed.
        """
        raise RuntimeError("Terminal filters do not support sub-filters")

    def find_filter(self, filter_cls):
        """
        As a :class:`~es_fluent.filters.core.Terminal` filter, adding nested filters
        is not allowed and therefore, finding sub-filters is not supported.
        """
        raise RuntimeError("Terminal filters do not support sub-filters")

    def is_empty(self):
        """
        :return:
            ``False`` as Terminal filters are never empty.
        """
        return False


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


class Range(Terminal):
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


class Age(Terminal):
    """
    Similar to a range filter. Operates on times. When querified, we convert
    the age in seconds into a datetime relative to the current
    ``datetime.datetime.now()``.
    """
    name = 'age'

    def __init__(self, name, gte=None, lte=None, lt=None, gt=None):
        """
        :param string name:
            The datetime indexed field we'll be making age comparisons against.
        """
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
        """
        :param string name:
            The name of the field that will be checked for the provided
            ``value``.
        :param string value:
            The value that we expect to find in the provided field name
            ``name``.
        """
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
        """
        :param string name:
            The name of the field whose presence in the document will be
            checked.
        """
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
        """
        :param string name: The name of the field to filter for ``values``.
        :param list values:
            A list of values to filter on.
        """
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
        """
        :param string name: The name of the field to filter on.
        :param string expression: The regular expression to filter with.
        """
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
        """
        :param string name: The name of the script's generated field.
        :param string script_id:
            The identifier within your cluster's indexed scripts.
        :param dict script_params:
            Additional script parameters to pass to the script.
        :param string lang:
            The script language. Defaults to ``groovy``.
        """
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
