""" Export Submissions Transform module """
#pylint: disable=too-few-public-methods
import os
import sys
import logging
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
        output = [i for i in output if i != {}]
        output = self.normalize(output)
        output = self.to_csv(output, sep)
        # set encoding to windows-cp1252
        encoded_output = bytes(output, 'cp1252').decode('cp1252', 'ignore')
        return encoded_output

    # pylint: disable=R0201, disable=too-many-nested-blocks
    def get_data(self, submission):
        """
        Get data from submission object
        """
        output = {}
        # exclude permit type = existingPermitApplication submissions and bluebeam fails
        if not self.exclude_submissions(submission):
            data = submission['data']
            # support old submissions
            if data.get('permitType', '') == 'revisionToAnIssuedPermit':
                data['permitType'] = 'permitRevision'

            output['id'] = submission['_id']
            output['created'] = submission['created']
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
                    elif key == 'workersCompSelectboxes':
                        output[key] = self.convert_workmencomp(data[key])
                    else:
                        multi_selects = []
                        for multi_key, multi_value in data[key].items():
                            if multi_value:
                                multi_selects.append(multi_key)
                        output[key] = ', '.join(multi_selects)
                else:
                    output[key] = data[key]
            #if output['id'] == '6027006df6281e2cae70dd1b':
                #raw_string = r"{}".format(output['projectDescription'])
                #print(raw_string)
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
                        output[key] = " ".join(data[key].split()).replace('|', '').strip("\r\n")
                # relabel field, if necessary
                relabel_field = FieldConfigs.get_relabel_fields(key)
                if relabel_field:
                    output[relabel_field] = output.pop(key)
            # reorder fields specific to MIS
            output = self.reorder_fields(output)
        return output

    def exclude_submissions(self, submission):
        """ exclude submissions that meet conditions """
        if submission['data'].get('bluebeamStatus', '') == 'Error':
            self.bb_upload_fail_records(submission)
            return False
        if submission['data'].get('permitType', '') != 'existingPermitApplication':
            return False
        return True

    def bb_upload_fail_records(self, submission):
        """ handles failed bluebeam upload failures """
        # log fails to a file for process_result to pick up
        failed = {
            "formio_id": submission.get('_id'),
            "status": "Error",
            "bluebeamStatus": submission['data'].get('bluebeamStatus', '')
        }
        data_file_path = os.path.dirname(__file__) + '/../resources/data/exported_data/'
        # write failed bluebeam for process_result, need to delete the file after it has been processed.
        with open(data_file_path + 'bb_failed_records.txt', "a") as bb_failed_records_file:
            try:
                bb_failed_records_file.write(failed['formio_id'] + '|' + failed['status'] + '|' + failed['bluebeamStatus'])
                bb_failed_records_file.write('\n')
            except IOError as err:
                logging.exception("I/O error(%s): %s", err.errno, err.strerror)
            except Exception: #pylint: disable=broad-except
                logging.exception("Unexpected error: %s", format(sys.exc_info()[0]))

            bb_failed_records_file.close()
