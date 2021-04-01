""" TransformBase module """
#pylint: disable=too-few-public-methods,no-self-use
import re
import dateutil.parser
import pytz
from ..resources.field_configs import FieldConfigs
from ..resources.field_maps import FieldMaps

class TransformBase():
    """ Base module for Transforms """

    #pylint: disable=unused-argument
    def transform(self, data, sep):
        """
        abstract transform function
        given input, does some transformation and return output
        """
        output = data
        return output

    @staticmethod
    def pretty_app_num(appnum):
        """ strip dash(-) from the application number  """
        return appnum.replace('-', '')

    @staticmethod
    def pretty_string(name):
        """ Change name from camelCase to words """
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', name).title()

    @staticmethod
    def pretty_time(value, zone='America/Los_Angeles'):
        """
        return a better human readable time string
        """
        time = dateutil.parser.parse(value)
        timezone = pytz.timezone(zone)
        localtime = time.astimezone(timezone).strftime('%Y-%m-%d %I:%M:%S %p')
        return localtime

    @staticmethod
    def pretty_phonenumber(value):
        """ strip non-digit characters """
        return re.sub('[^0-9]', '', value)

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

    @staticmethod
    def add_fire_rating(key, value, output):
        """ set mapping key for Fire Rating and proposed Fire Rating """
        # fire rating only allow 1 character
        if key == 'existingBuildingConstructionType':
            output['existingFireRating'] = FieldMaps.map_key_value('fire_rating', value)[:1]
            output['existingBuildingConstructionType'] = output['existingBuildingConstructionType'][:1]
        elif key == 'typeOfConstruction':
            output['proposedFireRating'] = FieldMaps.map_key_value('fire_rating', value)[:1]
            output['typeOfConstruction'] = output['typeOfConstruction'][:1]

        return output

    @staticmethod
    def convert_address_fields(key, value, output):
        """ flatten nested json address fields """
        if key == 'ownerAddress':
            address_prefix = 'owner'
        else:
            address_prefix = 'applicant'
        if value:
            output[address_prefix + 'Address1'] = value['line1'] if value['line1'] else ''
            output[address_prefix + 'Address2'] = value['line2'] if value['line2'] else ''
            output[address_prefix + 'City'] = value['city'] if value['city'] else ''
            output[address_prefix + 'State'] = value['state'] if value['state'] else ''
            output[address_prefix + 'ZipCode'] = value['zip'] if value['zip'] else ''

        return output

    @staticmethod
    def convert_building_use(key, value, data):
        """ flatten building use code """
        ret = []
        if value:
            for _k, _v in value.items():
                if _v == 'TRUE': # value is a string, not a bool
                    if _k == 'other':
                        other_key = key + 'Other'
                        if isinstance(data[other_key], list):
                            ret += data[other_key]
                        else:
                            ret.append(data[other_key])
                    else:
                        ret.append(_k)
        return ', '.join(ret)

    @staticmethod
    def set_pts_fields(data):
        """ remove non pts integration fields """
        if data:
            # map new building fields to proposed building fields
            if data['newTypeOfConstruction'] and data['newTypeOfConstruction'] != '':
                data = TransformBase.map_new_proposed(data)

            copy_data = []
            copy_data.extend(data)
            for key in copy_data:
                if not FieldConfigs.is_pts_fields(key):
                    data.pop(key, None)

            # set site permit field
            data['sitePermit'] = data['sitePermitForm38'] if data['sitePermitForm38'] else data['sitePermitForm12']
            data.pop('sitePermitForm12', None)
            data.pop('sitePermitForm38', None)

            # append Rev # to project description
            bpa = TransformBase.pretty_app_num(data['buildingPermitApplicationNumber'])
            data['projectDescription'] = 'Revision to ' + bpa + data['projectDescription']
            data.pop('buildingPermitApplicationNumber', None)

            # convert 'agent' to 'AUTHORIZED AGENT'
            if data.get('applicantType', '') == 'agent':
                data['applicantType'] = 'AUTHORIZED AGENT-OTHERS'

            #convert bool values
            data = TransformBase.convert_bool_fields(data)
        return data

    @staticmethod
    def map_new_proposed(data):
        """ maps new to proposed """
        data['projectDescription'] = data.get('newProjectDescription', '')
        data['typeOfConstruction'] = data.get('newTypeOfConstruction', '')
        data['occupancyClass'] = data.get('newOccupancyClass', '')
        data['proposedDwellingUnits'] = data.get('newDwellingUnits', '')
        data['proposedOccupancyStories'] = data.get('newOccupancyStories', '')
        data['proposedBasementsAndCellars'] = data.get('newBasements', '')
        data['proposedUseOther'] = data.get('newBuildingUseOther', '')

        return data

    @staticmethod
    def reorder_fields(data):
        """ reorder fields into MIS expected order """
        ret = {}
        for key in FieldConfigs.ordered_fields:
            if key in data:
                ret[key] = data[key]
            else:
                ret[key] = ''
        return ret

    @staticmethod
    def convert_bool_fields(data):
        """ reorder fields into MIS expected order """
        for key in FieldConfigs.convert_bool_fields:
            if key in data:
                if data[key].lower() == 'yes':
                    data[key] = 'Y'
                elif data[key].lower() == 'no':
                    data[key] = 'N'
                else:
                    data[key] = ''
        return data

    @staticmethod
    def convert_workmencomp(value):
        """ convert worker's comp data to a string of 0 and 1 """
        ret = ''
        if value:
            ret = '1' if value['Have_certificate_of_consent'] == 'TRUE' else '0'
            ret += '1' if value['Have_workers_comp_insurance'] == 'TRUE' else '0'
            ret += '1' if value['Not_subject_to_workers_comp'] == 'TRUE' else '0'
            ret += '1' if value['Will_comply_with_all_laws/ordinances'] == 'TRUE' else '0'
            ret += '1' if value['Work_less_than_$100'] == 'TRUE' else '0'

        return ret
