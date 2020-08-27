import os
import ast

class FieldConfigs():
    """ Takes field configs from environment var as JSON.
        Could also pass in from POST, if do_post is implemented
        Determines which fields need custom formatting. 
     """

    field_configs = ast.literal_eval(os.getenv('FIELD_CONFIGS'))

    @staticmethod
    def check_phone_fields(key):
        """ check for phone number fields """
        for field in FieldConfigs.field_configs:
            if key in field['phone_fields']:
                return True
        return False

    @staticmethod
    def check_state_fields(key):
        """ check for State fields """
        for field in FieldConfigs.field_configs:
            if key in field['state_fields']:
                return True
        return False
