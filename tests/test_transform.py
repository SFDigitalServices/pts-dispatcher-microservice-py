""" TEST Transform class and methods """

from service.transforms.transform import TransformBase

def test_transform_base():
    """ Test TransformBase transform method """
    data = "test"
    sep = '|'
    assert TransformBase().transform(data, sep) == data


def test_pretty_app_num():
    """ test stripping dash from application number  """
    assert '123456789' == TransformBase.pretty_app_num('123-456-789')

def test_pretty_string():
    """ test camelCase to words """
    assert 'Hello World' == TransformBase.pretty_string('HelloWorld')

def test_pretty_time():
    """ test human readable time string """
    value = '2020-08-17T16:54:48.000Z'
    expected = '2020-08-17 09:54:48 AM'
    assert expected == TransformBase.pretty_time(value)

def test_pretty_phonenumber():
    """ test phone format """
    assert '4155084155' == TransformBase.pretty_phonenumber('415-508-4155')

def test_datetime_valid():
    """ test string is valid datetime """
    assert TransformBase.datetime_valid('2020-08-17T16:56:09.191Z')
    assert not TransformBase.datetime_valid('2020-09-12')
