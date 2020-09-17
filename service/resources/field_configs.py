import os
import ast

class FieldConfigs():
    """ Takes field configs from environment var as JSON.
        Could also pass in from POST, if do_post is implemented
        Determines which fields need custom formatting.
     """

    # will move this to client side in the POST body when we implement do_post()
    field_configs = ast.literal_eval(os.getenv('FIELD_CONFIGS'))

    @staticmethod
    def get_field_key(value):
        """ get the key from field_config based on value """
        for index in range(len(FieldConfigs.field_configs)):
            for field_key in FieldConfigs.field_configs[index]:
                # exclude fields that don't need mapping file
                if field_key == 'appnum_fields' or field_key == 'phone_fields':
                    return None
                if value in FieldConfigs.field_configs[index][field_key]:
                    return field_key
        return None

    @staticmethod
    def get_phone_appnum_field(key):
        """ check for phone number fields """
        for field in FieldConfigs.field_configs:
            if key in field['phone_fields']:
                return 'phone_fields'
            elif key in field['appnum_fields']:
                return 'appnum_fields'
        return None