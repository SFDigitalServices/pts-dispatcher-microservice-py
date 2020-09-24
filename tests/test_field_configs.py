# pylint: disable=redefined-outer-name
"""Tests for field configs and mappings """
import pytest

from service.resources.field_configs import FieldConfigs

@pytest.mark.parametrize('name, expected', [('projectAddressStreetType', 'street_suffix_fields'), ('ownerState', 'state_fields')])
def test_get_field_key(name, expected):
    """ test get map files """
    assert expected == FieldConfigs.get_field_key(name, 'map')
