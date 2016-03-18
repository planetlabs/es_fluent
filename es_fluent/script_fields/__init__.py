class ScriptFields(object):
    """
    Represents a collection of requested script fields.
    """
    def __init__(self):
        self.fields = []

    def add_field(self, field_instance):
        """
        Appends a field.
        """
        if isinstance(field_instance, BaseScriptField):
            field_instance = field_instance
        else:
            raise ValueError('Expected a basetring or Field instance')

        self.fields.append(field_instance)

        return self

    def is_empty(self):
        """
        Returns True if there are no script fields, False otherwise.
        """
        return len(self.fields) == 0

    def to_query(self):
        """
        Returns a json-serializable representation.
        """
        query = {}

        for field_instance in self.fields:
            query.update(field_instance.to_query())

        return query


class BaseScriptField(object):
    """
    Manages a basic field. The intention here is to give script_fields
    and non script fields a similar taxonomy.
    """


class ScriptField(BaseScriptField):
    """
    Represents a script field.
    """
    def __init__(self, name, script, lang='groovy', **kwargs):
        """
        :param string name: The resulting name of the field.
        :param dict script: The script for the script field.
        :param string lang: The language of the script.
        :param dict kwargs: Additional keyword arguments become the params for
            the script.
        """
        self.name = name
        self.script = script
        self.lang = lang
        self.script_params = kwargs

    def to_query(self):
        """
        Returns a json-serializable representation.
        """
        return {
            self.name: {
                'lang': self.lang,
                'script': self.script,
                'params': self.script_params
            }
        }


class ScriptIDField(BaseScriptField):
    """
    Represents a pre-indexed script field.
    """
    def __init__(self, name, script_id, lang='groovy', **kwargs):
        """
        :param string name: The resulting name of the field.
        :param string script_id: The id of the pre-indexed script field.
        :param string lang: The language of the script.
        :param dict kwargs:
            Additional keyword arguments become args for the script.
        """
        self.name = name
        self.script_id = script_id
        self.lang = lang
        self.script_params = kwargs

    def to_query(self):
        """
        Returns a json-serializable representation.
        """
        return {
            self.name: {
                'lang': self.lang,
                'script_id': self.script_id,
                'params': self.script_params
            }
        }
