# pylint: disable=redefined-outer-name
"""Tests for field configs and mappings """
import pytest
from falcon import testing
from service.resources.field_maps import FieldMaps

@pytest.mark.parametrize('name, expected', [('state_fields', 'states.json'), ('building_use', 'building_use.json'), ('fire_rating', 'fire_rating.json'),
('construction_type', 'construction_type.json'),('occupancy_code', 'occupancy_code.json'), ('street_suffix_fields', 'street_suffix.json')])
def test_get_map_file(name, expected):
    """ test get map files """
    assert expected == FieldMaps.get_map_file(name)

@pytest.mark.parametrize('name, expected', [('california', 'CA'), ('colorado', 'CO')])
def test_map_key_value_states(name, expected):
    """ test mapping values to key from map_type """
    assert expected == FieldMaps.map_key_value('state_fields', name)

@pytest.mark.parametrize('name, expected', [('Avenue', 'AV'), ('Court', 'CT')])
def test_map_key_value_street_suffix(name, expected):
    """ test mapping values to key from map_type """
    assert expected == FieldMaps.map_key_value('street_suffix_fields', name)

@pytest.mark.parametrize('name, expected', [('TEST', 'AV')])
def test_map_key_value_none(name, expected):
    """ test mapping values to key from map_type """
    assert FieldMaps.map_key_value('street_suffix_fields', name) is None
