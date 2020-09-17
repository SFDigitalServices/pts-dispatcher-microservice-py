""" Export Submissions Transform module """
#pylint: disable=too-few-public-methods
import json
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
        output = self.normalize(output)
        output = self.to_csv(output, sep)
        return output

    def get_data(self, submission):
        """
        Get data from submission object
        """
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
                multi_selects = []
                for multi_key, multi_value in data[key].items():
                    if multi_value:
                        multi_selects.append(multi_key)
                output[key] = ', '.join(multi_selects)
            else:
                output[key] = data[key]

        return output

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
        for key in data:
            if self.datetime_valid(data[key]):
                output[key] = self.pretty_time(data[key])
            else:
                field_key = FieldConfigs.get_field_key(key)
                phone_appnum_key = FieldConfigs.get_phone_appnum_field(key)
                if field_key is not None:
                    output[key] = FieldMaps.map_key_value(field_key, data[key])
                # format phone numbers and building application number
                elif phone_appnum_key is not None:
                    if phone_appnum_key == 'phone_fields':
                        output[key] = self.pretty_phonenumber(data[key])
                    elif phone_appnum_key == 'appnum_fields':
                        output[key] = self.pretty_app_num(data[key])
                # replace \n with \t, \n messes up to_csv()
                elif isinstance(data[key], (str, bytes)):
                    output[key] = data[key].replace('\n', '\t')
                else:
                    output[key] = data[key]
        return output
