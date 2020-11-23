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
        if key == 'existingBuildingConstructionType':
            output['existingFireRating'] = FieldMaps.map_key_value('fire_rating', value)
        elif key == 'typeOfConstruction':
            output['proposedFireRating'] = FieldMaps.map_key_value('fire_rating', value)

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
                if FieldConfigs.is_missing_field(key):
                    data.pop(key, None)
                    data = TransformBase.add_missing_fields(key, data)

            # set site permit field
            data['sitePermit'] = data['sitePermitForm38'] if data['sitePermitForm38'] else data['sitePermitForm12']
            data.pop('sitePermitForm12', None)
            data.pop('sitePermitForm38', None)

            #convert bool values
            data = TransformBase.convert_bool_fields(data)

        return data

    @staticmethod
    def map_new_proposed(data):
        """ maps new to proposed """
        data['projectDescription'] = data['newProjectDescription']
        data['typeOfConstruction'] = data['newTypeOfConstruction']
        data['occupancyClass'] = data['newOccupancyClass']
        data['proposedDwellingUnits'] = data['newDwellingUnits']
        data['proposedOccupancyStories'] = data['newOccupancyStories']
        data['proposedBasementsAndCellars'] = data['newBasements']

        return data

    @staticmethod
    def add_missing_fields(key, output):
        """ add missing MIS fields """
        address_prefix = ''
        if key == 'ownerName':
            address_prefix = 'owner'
        elif key == 'contractorName':
            address_prefix = 'contractor'
        elif key == 'engineerName':
            address_prefix = 'engineer'
        elif key == 'architectName':
            address_prefix = 'architect'
        elif key == 'agentName':
            address_prefix = 'contractor'
        elif key == 'attorneyName':
            address_prefix = 'attorney'

        if address_prefix != '':
            output[address_prefix + 'FirstName'] = ''
            output[address_prefix + 'LastName'] = ''
            if address_prefix != 'owner':
                output[address_prefix + 'PhoneNumber'] = ''
                output[address_prefix + 'Address1'] = ''
                output[address_prefix + 'Address2'] = ''
                output[address_prefix + 'City'] = ''
                output[address_prefix + 'State'] = ''
                output[address_prefix + 'ZipCode'] = ''

        return output

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
