""" Export Submissions Transform module """
#pylint: disable=too-few-public-methods
import pandas as pd
from .transform import TransformBase
from ..resources.field_configs import FieldConfigs
from ..resources.field_maps import FieldMaps

class ExportSubmissionsTransform(TransformBase):
    """ Transform for Export Submissions """
    def transform(self, data, sep):
        """
        transform submissions from export
        """
        output = list(map(self.get_data, data))
        output = list(map(self.pretty_format, output))
        output = [i for i in output if i is not None]
        output = self.normalize(output)
        output = self.to_csv(output, sep)
        return output

    # pylint: disable=R0201
    def get_data(self, submission):
        """
        Get data from submission object
        """
        # skip permit type = existingPermitApplication submissions
        #pylint: disable=too-many-nested-blocks
        if submission['data']['permitType'] and submission['data']['permitType'] != 'existingPermitApplication':
            output = {}
            data = submission['data']

            output['id'] = submission['_id']
            output['created'] = submission['created']
            #pylint: disable=too-many-nested-blocks
            for key in data:
                # flatten list values
                if isinstance(data[key], list):
                    if len(data[key]) > 0:
                        if isinstance(data[key][0], (int, str)):
                            output[key] = ', '.join(map(str, data[key]))
                        else:
                            file_names = []
                            for index, val in enumerate(data[key]):
                                # if storage, concat filename
                                if 'storage' in val and 'originalName' in val:
                                    file_names.append(val['originalName'])
                                else:
                                    output[key+str(index+1)] = val

                            if len(file_names) > 0:
                                output[key] = ', '.join(file_names)
                # flatten multi select values
                elif isinstance(data[key], dict):
                    # building use code needs manual process
                    if FieldConfigs.is_building_use(key):
                        output[key] = self.convert_building_use(key, data[key], data)
                    # flatten nested address fields
                    elif FieldConfigs.is_nested_address_field(key):
                        output = self.convert_address_fields(key, data[key], output)
                    else:
                        multi_selects = []
                        for multi_key, multi_value in data[key].items():
                            if multi_value:
                                multi_selects.append(multi_key)
                        output[key] = ', '.join(multi_selects)
                else:
                    output[key] = data[key]
            return output
        return None

    def normalize(self, data):
        """
        Normalize data into a flat structure into DataFrame
        """
        dataframe = pd.json_normalize(data)
        # update column names
        dataframe.rename(columns=self.pretty_string, inplace=True)

        return dataframe

    def to_csv(self, dataframe, sep=','):
        """
        Return CSV from DataFrame
        """
        return dataframe.to_csv(index=False, sep=sep, line_terminator='\r\n')

    def pretty_format(self, data):
        """ Pretty format data fields """
        output = {}

        if data:
            data = self.set_pts_fields(data)
            for key in data:
                if self.datetime_valid(data[key]):
                    output[key] = self.pretty_time(data[key])
                else:
                    field_key = FieldConfigs.get_field_key(key, 'map')
                    phone_appnum_key = FieldConfigs.get_field_key(key, 'pretty')
                    if field_key is not None:
                        output[key] = FieldMaps.map_key_value(field_key, data[key])
                        # manually add Fire Rating and proposed Fire Rating
                        if field_key == 'construction_type' and data[key] != '':
                            output = self.add_fire_rating(key, data[key], output)
                    # format phone numbers and building application number
                    elif phone_appnum_key is not None:
                        if phone_appnum_key == 'phone_fields':
                            output[key] = self.pretty_phonenumber(data[key])
                    # cleanse characters that break the csv
                    elif isinstance(data[key], (str, bytes)):
                        output[key] = data[key].replace('\n', '\t').replace('|', '')
                # relabel field, if necessary
                relabel_field = FieldConfigs.get_relabel_fields(key)
                if relabel_field:
                    output[relabel_field] = output.pop(key)
            output = self.reorder_fields(output)
<<<<<<< HEAD
        return output
=======
            return output

>>>>>>> 047ea9c02ade19dc0e686f3244f6238552da93a7
