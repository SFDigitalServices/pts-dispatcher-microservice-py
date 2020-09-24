""" Export Submissions Transform module """
#pylint: disable=too-few-public-methods
import dateutil.parser
import pytz
import pandas as pd
from .transform import TransformBase

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

    @staticmethod
    def get_data(submission):
        """
        Get data from submission object
        """
        output = {}
        data = submission['data']

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
            else:
                output[key] = data[key]

        # append id and created field to data
        output['id'] = submission['_id']
        output['created'] = submission['created']
        return output

    def normalize(self, data):
        """
        Normalize data into a flat structure into DataFrame
        """
        dataframe = pd.json_normalize(data)

        # move id and created to front
        col = dataframe.pop("created")
        dataframe.insert(0, col.name, col)
        col = dataframe.pop("id")
        dataframe.insert(0, col.name, col)

        # update column names
        dataframe.rename(columns=self.pretty_string, inplace=True)

        return dataframe

    @staticmethod
    def to_csv(dataframe, sep=','):
        """
        Return CSV from DataFrame
        """
        return dataframe.to_csv(index=False, sep=sep, line_terminator='\r\n')

    def pretty_format(self, data):
        """ Pretty format data fields """
        output = {}
        for key in data:
            output[key] = self.pretty_time(data[key])
        return output

    def pretty_time(self, value, zone='America/Los_Angeles'):
        """
        If valid date, return a better human readable time string
        """
        new_value = value
        if self.datetime_valid(value):
            time = dateutil.parser.parse(value)
            timezone = pytz.timezone(zone)
            localtime = time.astimezone(timezone).strftime('%Y-%m-%d %I:%M:%S %p')
            return localtime
        return new_value

    @staticmethod
    def datetime_valid(dt_str):
        """ Check if string is valid datetime """
        try:
            time = dateutil.parser.parse(dt_str)
            time_str = time.isoformat("T", "milliseconds").replace("+00:00", "Z")
            return time_str == dt_str
        #pylint: disable=bare-except
        except:
            pass
        return False
