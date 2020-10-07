""" Custom field mapping building permit api """

import os
import json

# pylint: disable=too-few-public-methods
class FieldMaps():
    """ class to handle States abbreviation """

    cur_path = os.path.dirname(__file__)

    @staticmethod
    def map_key_value(map_type, key):
        """ maps state to state code """
        ret = None
        with open(FieldMaps.cur_path + '/data/' + FieldMaps.get_map_file(map_type), 'r') as file:
            map_object = json.loads(file.read())
        # mutli-select values that need to be mapped
        if key and ',' in key:
            list_values = key.split(',')
            r_values = []
            for value in list_values:
                r_values.append(map_object[value.strip()])
            ret = ','.join(r_values)
        elif key and key in map_object:
            ret = map_object[key]
        return ret

    @staticmethod
    def get_map_file(argument):
        """ python switch statement to get map file name """
        switcher = {
            'state_fields': 'states.json',
            'building_use':'building_use.json',
            'fire_rating':'fire_rating.json',
            'construction_type':'construction_type.json',
            'occupancy_code':'occupancy_code.json',
            'street_suffix_fields':'street_suffix.json'
        }
        return switcher.get(argument, "")
