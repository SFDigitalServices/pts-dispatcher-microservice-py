""" Custom field mapping building permit api """

import os
import json

# pylint: disable=too-few-public-methods
class FieldMaps():
    """ class to handle States abbreviation """

    cur_path = os.path.dirname(__file__)

    @staticmethod
    def map_key_value(key, key_value):
        """ converts field values defined in field_configs.py: map_field_configs
            to MIS accepted values using mapping data in data/*.json
        """
        ret = key_value
        with open(FieldMaps.cur_path + '/data/mappings/' + FieldMaps.get_map_file(key), 'r') as file:
            map_object = json.loads(file.read())
        # mutli-select values that need to be mapped
        if key_value and ',' in key_value:
            list_values = key_value.strip('"').split(',')
            r_values = []
            for value in list_values:
                if value.strip() in map_object:
                    r_values.append(map_object[value.strip()])
            ret = ','.join(r_values)
            ret = ret[:10] # 10 characters
        elif key_value and key_value in map_object:
            ret = map_object[key_value]
        else:
            ret = ''
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
