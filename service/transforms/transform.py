""" TransformBase module """
#pylint: disable=too-few-public-methods,no-self-use
import re
import dateutil.parser
import pytz

class TransformBase():
    """ Base module for Transforms """

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
