import os
import json

class FieldMaps():
    """ class to handle States abbreviation """

    cur_path = os.path.dirname(__file__)

    @staticmethod
    def map_key_value(map_type, key):
        """ maps state to state code """
        with open(FieldMaps.cur_path + '/data/' + FieldMaps.get_map_file(map_type), 'r') as file:
            map_object = json.loads(file.read())

        if key and key in map_object:
            return map_object[key]
        return None

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
