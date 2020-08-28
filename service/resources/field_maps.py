import os
import json

class FieldMaps():
    """ class to handle States abbreviation """

    cur_path = os.path.dirname(__file__)

    @staticmethod
    def map_state_code(key):
        """ maps state to state code """
        with open(FieldMaps.cur_path + '/data/states.json', 'r') as file:
            state_map = json.loads(file.read())

        if key and key in state_map:
            return state_map[key]
        return None

    @staticmethod
    def map_construction_type(key):
        """ maps construction type """

    @staticmethod
    def map_fire_rating(key):
        """ maps fire rating """

    @staticmethod
    def map_occupancy(key):
        """ maps occupancy code """

    @staticmethod
    def map_building_use(key):
        """ maps building use code """