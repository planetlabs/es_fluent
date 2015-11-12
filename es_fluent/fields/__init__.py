"""
Utilized by the :class:`~es_fluent.builder.QueryBuilder` to optionally
restrict the fields returned by an Elastic query.
"""


class Fields(object):
    """
    Represents a collection of fields to be requested at query time.
    """
    def __init__(self):
        self.fields = []

    def add_field(self, field_instance_or_string):
        """
        Appends a field, can be a :class:`~es_fluent.fields.Field` or string.
        """
        if isinstance(field_instance_or_string, basestring):
            field_instance = Field(field_instance_or_string)
        elif isinstance(field_instance_or_string, Field):
            field_instance_or_string = field_instance
        else:
            raise ValueError('Expected a basetring or Field instance')

        self.fields.append(field_instance)

        return self

    def to_query(self):
        """
        Serializes this into a json-serializable dictionary suitable for use
        with the elasticsearch api.
        """
        return [field.name for field in self.fields]

    def is_empty(self):
        """
        Returns ``False`` if no fields have been added, ``True`` otherwise.
        """
        return len(self.fields) == 0


class Field(object):
    """
    Manages a basic field. These occur inside of an elasticsearch fields array.
    """
    def __init__(self, name):
        self.name = name
