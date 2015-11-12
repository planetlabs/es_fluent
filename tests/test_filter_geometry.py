#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_filters
----------------------------------

Tests for `filters` module.
"""

import unittest

from es_fluent.filters.geometry import GeoJSON, IndexedShape


class TestEs_fluent_filters(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_geoshape_point(self):
        geojson = {
            "type": "Point",
            "coordinates": [0, 0]
        }
        geoshape = GeoJSON("geom", geojson)
        self.assertEquals(geoshape.to_query(), {
            "geo_shape": {
                "geom": {
                    "shape": {
                        "type": "Point",
                        "coordinates": [0, 0]
                    }
                }
            }
        })

    def test_geoshape_feature(self):
        geojson = {
            "type": "Feature",
            "properties": {
                "hello": "I should be removed"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [0, 0]
            }
        }
        geoshape = GeoJSON("geom", geojson)
        self.assertEquals(geoshape.to_query(), {
            "geo_shape": {
                "geom": {
                    "shape": {
                        "type": "Point",
                        "coordinates": [0, 0]
                    }
                }
            }
        })

    def test_geoshape_feature_collection(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "hello": "I should be removed"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [0, 0]
                }
            }]
        }
        geoshape = GeoJSON("geom", geojson)
        self.assertEquals(geoshape.to_query(), {
            "geo_shape": {
                "geom": {
                    "shape": {
                        "type": "GeometryCollection",
                        "geometries": [{
                            "type": "Point",
                            "coordinates": [0, 0]
                        }]
                    }
                }
            }
        })

    def test_indexed_shape(self):
        indexedshape = IndexedShape('geom', 'shape_id', 'index_name',
                                    'doc_type', 'path')
        self.assertEquals(indexedshape.to_query(), {
            "geo_shape": {
                "geom": {
                    "indexed_shape": {
                        "id": "shape_id",
                        "index": "index_name",
                        "type": "doc_type",
                        "path": "path"
                    }
                }
            }
        })


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
