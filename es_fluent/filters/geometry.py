"""
Geometry related filters require additional dependencies.  Hence they're broken
out into their own module.
"""
from copy import deepcopy
from . import Terminal


def prepare_geojson(geojson):
    """
    Modifies incoming GeoJSON to make it Elastic friendly. This means:

        1. CW orientation of polygons.
        2. Re-casting of Features and FeatureCollections to Geometry and
           GeometryCollections.
    """
    # TODO CW orientation.
    geojson = deepcopy(geojson)

    if geojson["type"] == "Feature":
        geojson = geojson["geometry"]
        if hasattr(geojson, 'properties'):
            del geojson['properties']

    if geojson["type"] == "FeatureCollection":
        geojson["type"] = "GeometryCollection"
        geojson["geometries"] = [
            feature["geometry"] for feature in geojson["features"]
        ]
        del geojson["features"]

    return geojson


class GeoJSON(Terminal):
    """
    Manages querying by GeoJSON. Automatically converts incoming GeoJSON
    to elasticsearch friendly geometry. This generally means::

    #. CW orientation of polygons.
    #. Re-casting of Features and FeatureCollections to Geometry and
       GeometryCollections.
    """
    name = 'geometry'

    def __init__(self, name, geojson):
        self.name = name
        self.geojson = prepare_geojson(geojson)

    def to_query(self):
        """
        Returns a json-serializable representation.
        """
        return {
            "geo_shape": {
                self.name: {
                    "shape": self.geojson
                }
            }
        }


class IndexedShape(Terminal):
    """
    Searches by a previously indexed Geometry.
    """
    name = "indexed_geometry"

    def __init__(self, name, shape_id, index_name, doc_type, path):
        """
        :param string name: The field to match against the target shape.
        :param string shape_id: The id of the indexed shape within the index.
        :param string index_name: The name of the index containing our shape.
        :param string doc_type: The type of document within index_name.
        :param string path:
            The location of geometry field within the indexed doc.
        """
        self.name = name
        self.shape_id = shape_id
        self.index_name = index_name
        self.doc_type = doc_type
        self.path = path

    def to_query(self):
        """
        Returns a json-serializable representation.
        """
        return {
            "geo_shape": {
                self.name: {
                    "indexed_shape":  {
                        "index": self.index_name,
                        "type": self.doc_type,
                        "id": self.shape_id,
                        "path": self.path
                    }
                }
            }
        }
